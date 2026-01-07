"""Pydantic schemas for Template API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class TemplateResponse(BaseModel):
    """Full template response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str
    version: str
    workload_type: str
    language: str
    capabilities: list[str]
    ideal_for: list[str]
    stack: dict[str, Any]
    repository_url: str | None
    documentation_url: str | None
    includes_ci: bool
    includes_cd: bool
    includes_monitoring: bool
    includes_tests: bool
    usage_count: int
    is_active: bool
    is_recommended: bool
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    """Paginated list of templates."""

    templates: list[TemplateResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RecommendationRequest(BaseModel):
    """Request schema for template recommendation."""

    workload_type: str = Field(
        ...,
        description="Type of workload (api, batch, stream, ml, data-pipeline)",
    )
    language: str = Field(
        ...,
        description="Programming language (python, go, typescript, java)",
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="List of requirements (e.g., 'low_latency', 'high_throughput')",
    )
    team_id: str | None = Field(
        None,
        description="Team ID for context-aware recommendations",
    )
    additional_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for ML model",
    )


class RecommendationScore(BaseModel):
    """Individual recommendation with score."""

    template: TemplateResponse
    score: float = Field(..., ge=0, le=1, description="Match score (0-1)")
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for the match",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Potential concerns or considerations",
    )


class RecommendationResponse(BaseModel):
    """Template recommendation response."""

    session_id: str = Field(..., description="Unique session ID for tracking")
    recommendations: list[RecommendationScore]
    top_recommendation: TemplateResponse | None
    processing_time_ms: float = Field(
        ..., description="ML inference time in milliseconds"
    )
    model_version: str = Field(..., description="Recommender model version")
