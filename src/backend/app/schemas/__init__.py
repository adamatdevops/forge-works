"""Pydantic schemas for API request/response models."""

from app.schemas.service import (
    ServiceBase,
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceStatsResponse,
    ServiceUpdate,
)
from app.schemas.template import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationScore,
    TemplateListResponse,
    TemplateResponse,
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
