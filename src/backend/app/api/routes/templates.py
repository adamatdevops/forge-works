"""Golden Path template API endpoints."""

import time
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.template import TemplateCRUD
from app.db.base import get_db
from app.schemas.template import (
    TemplateResponse,
    TemplateListResponse,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationScore,
)

router = APIRouter()

# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    workload_type: str | None = Query(None, description="Filter by workload type"),
    language: str | None = Query(None, description="Filter by language"),
    is_active: bool = Query(True, description="Filter by active status"),
    is_recommended: bool | None = Query(None, description="Filter recommended only"),
) -> TemplateListResponse:
    """
    List all Golden Path templates.

    Supports pagination and filtering by workload type, language, and status.
    Templates are the production-ready blueprints for service creation.
    """
    skip = (page - 1) * page_size

    templates = await TemplateCRUD.get_all(
        db,
        skip=skip,
        limit=page_size,
        workload_type=workload_type,
        language=language,
        is_active=is_active,
        is_recommended=is_recommended,
    )

    total = await TemplateCRUD.count(
        db,
        workload_type=workload_type,
        language=language,
        is_active=is_active,
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(db: DbSession, template_id: str) -> TemplateResponse:
    """
    Get template details by ID.

    Returns full template information including stack details and capabilities.
    """
    template = await TemplateCRUD.get_by_id(db, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID '{template_id}' not found",
        )

    return TemplateResponse.model_validate(template)


@router.get("/slug/{slug}", response_model=TemplateResponse)
async def get_template_by_slug(db: DbSession, slug: str) -> TemplateResponse:
    """
    Get template by slug.

    Returns full template information including stack details and capabilities.
    """
    template = await TemplateCRUD.get_by_slug(db, slug)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with slug '{slug}' not found",
        )

    return TemplateResponse.model_validate(template)


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_template(
    db: DbSession,
    request: RecommendationRequest,
) -> RecommendationResponse:
    """
    Get ML-powered template recommendations based on requirements.

    This endpoint uses a simple scoring algorithm for Phase 1.
    Phase 2 will integrate a proper ML model (scikit-learn/XGBoost).

    The recommender analyzes:
    - Workload type match (api, batch, stream, ml)
    - Language preference (python, go, typescript)
    - Requirements alignment (low_latency, high_throughput, etc.)
    - Team patterns (future: what templates team has used successfully)
    """
    start_time = time.perf_counter()
    session_id = str(uuid4())

    # Get all active, recommended templates
    templates = await TemplateCRUD.get_all(
        db,
        is_active=True,
        is_recommended=True,
        limit=100,
    )

    if not templates:
        return RecommendationResponse(
            session_id=session_id,
            recommendations=[],
            top_recommendation=None,
            processing_time_ms=0,
            model_version="1.0.0-rule-based",
        )

    # Score each template (Phase 1: Rule-based scoring)
    scored_templates = []
    for template in templates:
        score, reasons, warnings = _calculate_template_score(template, request)

        if score > 0:
            scored_templates.append(
                RecommendationScore(
                    template=TemplateResponse.model_validate(template),
                    score=score,
                    match_reasons=reasons,
                    warnings=warnings,
                )
            )

    # Sort by score descending
    scored_templates.sort(key=lambda x: x.score, reverse=True)

    # Take top 5 recommendations
    top_recommendations = scored_templates[:5]

    processing_time = (time.perf_counter() - start_time) * 1000

    return RecommendationResponse(
        session_id=session_id,
        recommendations=top_recommendations,
        top_recommendation=(
            top_recommendations[0].template if top_recommendations else None
        ),
        processing_time_ms=round(processing_time, 2),
        model_version="1.0.0-rule-based",
    )


def _calculate_template_score(
    template,
    request: RecommendationRequest,
) -> tuple[float, list[str], list[str]]:
    """
    Calculate match score for a template (Phase 1: Rule-based).

    Returns (score, match_reasons, warnings)
    """
    score = 0.0
    reasons = []
    warnings = []

    # Workload type match (40% weight)
    if template.workload_type.lower() == request.workload_type.lower():
        score += 0.40
        reasons.append(f"Exact workload type match: {request.workload_type}")
    elif _is_compatible_workload(template.workload_type, request.workload_type):
        score += 0.20
        reasons.append(f"Compatible workload type: {template.workload_type}")

    # Language match (30% weight)
    if template.language.lower() == request.language.lower():
        score += 0.30
        reasons.append(f"Exact language match: {request.language}")
    else:
        warnings.append(
            f"Language mismatch: template uses {template.language}, "
            f"you requested {request.language}"
        )

    # Requirements/capabilities match (20% weight)
    if request.requirements:
        matching_capabilities = set(
            c.lower() for c in template.capabilities
        ) & set(r.lower() for r in request.requirements)

        matching_ideal = set(
            i.lower() for i in template.ideal_for
        ) & set(r.lower() for r in request.requirements)

        total_matches = len(matching_capabilities) + len(matching_ideal)
        if total_matches > 0:
            req_score = min(0.20, 0.05 * total_matches)
            score += req_score
            if matching_capabilities:
                reasons.append(
                    f"Matching capabilities: {', '.join(matching_capabilities)}"
                )
            if matching_ideal:
                reasons.append(f"Ideal for: {', '.join(matching_ideal)}")

    # Includes bonus (10% weight)
    includes_bonus = 0.0
    includes_list = []
    if template.includes_ci:
        includes_bonus += 0.025
        includes_list.append("CI")
    if template.includes_cd:
        includes_bonus += 0.025
        includes_list.append("CD")
    if template.includes_monitoring:
        includes_bonus += 0.025
        includes_list.append("monitoring")
    if template.includes_tests:
        includes_bonus += 0.025
        includes_list.append("tests")

    if includes_list:
        score += includes_bonus
        reasons.append(f"Includes: {', '.join(includes_list)}")

    # Usage popularity bonus (small boost for proven templates)
    if template.usage_count > 10:
        score = min(1.0, score + 0.05)
        reasons.append(f"Popular template ({template.usage_count} uses)")

    return round(score, 2), reasons, warnings


def _is_compatible_workload(template_type: str, requested_type: str) -> bool:
    """Check if workload types are compatible (not exact but usable)."""
    compatibility_map = {
        "api": ["batch"],  # API templates can be adapted for batch
        "batch": ["data-pipeline"],
        "stream": ["ml", "data-pipeline"],
        "ml": ["api", "batch"],
        "data-pipeline": ["batch", "stream"],
    }
    return requested_type.lower() in compatibility_map.get(template_type.lower(), [])
