"""Pydantic schemas for API request/response models."""

from app.schemas.service import (
    ServiceBase,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceStatsResponse,
)
from app.schemas.template import (
    TemplateResponse,
    TemplateListResponse,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationScore,
)

__all__ = [
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceListResponse",
    "ServiceStatsResponse",
    "TemplateResponse",
    "TemplateListResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationScore",
]
