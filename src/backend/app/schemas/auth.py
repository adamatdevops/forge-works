"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# =============================================================================
# Request Schemas
# =============================================================================


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=100)]
    full_name: Annotated[str, Field(min_length=1, max_length=255)]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: Annotated[str, Field(min_length=8, max_length=100)]

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: Annotated[str | None, Field(min_length=1, max_length=255)] = None


# =============================================================================
# Response Schemas
# =============================================================================


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Schema for simple message response."""

    message: str


# =============================================================================
# Internal Schemas
# =============================================================================


class TokenPayload(BaseModel):
    """Schema for decoded JWT payload."""

    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str
    role: str | None = None


class UserInDB(UserResponse):
    """Schema for user with hashed password (internal use)."""

    hashed_password: str
