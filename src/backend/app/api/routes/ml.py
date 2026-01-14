"""ML recommendation API routes."""

from fastapi import APIRouter, HTTPException, status

from app.ml.recommender import get_recommender
from app.schemas.ml import (
    RecommendationFeedback,
    RecommendationResponse,
    TemplateType,
    WorkloadFeatures,
)

router = APIRouter()


# =============================================================================
# Template Information
# =============================================================================


TEMPLATE_INFO = {
    TemplateType.MICROSERVICE_PYTHON: {
        "name": "Python Microservice",
        "description": "FastAPI-based microservice with PostgreSQL and Redis support",
        "best_for": ["Python APIs", "REST services", "Data-intensive backends"],
        "includes": ["FastAPI", "PostgreSQL", "Redis", "Docker", "pytest"],
    },
    TemplateType.MICROSERVICE_NODE: {
        "name": "Node.js Microservice",
        "description": "Express/Fastify-based microservice with MongoDB support",
        "best_for": ["JavaScript/TypeScript APIs", "Real-time services", "High-throughput APIs"],
        "includes": ["Express/Fastify", "MongoDB", "Redis", "Docker", "Jest"],
    },
    TemplateType.WORKER_SERVICE: {
        "name": "Worker Service",
        "description": "Background job processor with queue support",
        "best_for": ["Background jobs", "Queue consumers", "Scheduled tasks", "Batch processing"],
        "includes": ["Celery/RQ", "Redis", "Docker", "Monitoring"],
    },
    TemplateType.ML_PIPELINE: {
        "name": "ML Pipeline",
        "description": "Machine learning pipeline with GPU support and model serving",
        "best_for": ["ML model training", "Model serving", "Data pipelines", "GPU workloads"],
        "includes": ["PyTorch/TensorFlow", "MLflow", "GPU support", "Model registry"],
    },
    TemplateType.FRONTEND_APP: {
        "name": "Frontend Application",
        "description": "React/Next.js frontend with CDN and SSR support",
        "best_for": ["Web UIs", "SPAs", "Server-rendered apps", "Static sites"],
        "includes": ["Next.js/React", "Tailwind CSS", "CDN", "Vercel/Netlify ready"],
    },
}


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get template recommendation",
    description="Analyze workload features and recommend the best template",
)
async def get_recommendation(features: WorkloadFeatures) -> RecommendationResponse:
    """Get template recommendation based on workload features.

    Analyzes the provided workload characteristics and returns
    a ranked list of template recommendations with confidence scores.
    """
    try:
        recommender = get_recommender()
        return recommender.recommend(features)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}",
        )


@router.get(
    "/templates",
    summary="List available templates",
    description="Get information about all available golden path templates",
)
async def list_templates() -> dict:
    """List all available templates with their details."""
    return {
        "templates": [
            {
                "id": template.value,
                **info,
            }
            for template, info in TEMPLATE_INFO.items()
        ],
        "count": len(TEMPLATE_INFO),
    }


@router.get(
    "/templates/{template_id}",
    summary="Get template details",
    description="Get detailed information about a specific template",
)
async def get_template(template_id: str) -> dict:
    """Get details for a specific template."""
    try:
        template = TemplateType(template_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )

    info = TEMPLATE_INFO.get(template)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )

    return {
        "id": template.value,
        **info,
    }


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    summary="Submit recommendation feedback",
    description="Submit feedback on a template recommendation",
)
async def submit_feedback(feedback: RecommendationFeedback) -> dict:
    """Submit feedback on a recommendation.

    This helps improve the recommendation model over time.
    """
    # In production, this would save to database for model retraining
    # For now, just acknowledge receipt
    return {
        "status": "received",
        "message": "Thank you for your feedback",
        "selected_template": feedback.selected_template.value,
        "was_primary": feedback.was_primary,
    }


@router.get(
    "/health",
    summary="ML service health check",
    description="Check if the ML service is operational",
)
async def ml_health() -> dict:
    """Check ML service health and model status."""
    recommender = get_recommender()

    return {
        "status": "healthy",
        "model_loaded": recommender.model is not None,
        "mode": "ml" if recommender.model is not None else "rule-based",
    }
