"""Pydantic schemas for API request/response models."""

from app.schemas.auth import (
    MessageResponse,
    PasswordChange,
    TokenPayload,
    TokenResponse,
    UserInDB,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
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
    # Service schemas
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceListResponse",
    "ServiceStatsResponse",
    # Template schemas
    "TemplateResponse",
    "TemplateListResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationScore",
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenPayload",
    "UserInDB",
    "PasswordChange",
    "MessageResponse",
]
