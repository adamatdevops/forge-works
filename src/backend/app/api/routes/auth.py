"""Authentication API routes."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.crud import user as user_crud
from app.db.base import get_db
from app.schemas.auth import (
    MessageResponse,
    PasswordChange,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


# =============================================================================
# Request Models
# =============================================================================


class RefreshTokenRequest(BaseModel):
    """Request body for refresh token endpoint."""

    refresh_token: str | None = None


# =============================================================================
# Public Endpoints
# =============================================================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if email already exists
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await user_crud.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )

    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": user.role},
    )

    raw_refresh_token, token_hash = create_refresh_token()
    await user_crud.create_refresh_token(db, user.id, token_hash)

    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    # Update last login
    user = await user_crud.update_user_login(db, user)

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    # Authenticate user
    user = await user_crud.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": user.role},
    )

    raw_refresh_token, token_hash = create_refresh_token()
    await user_crud.create_refresh_token(db, user.id, token_hash)

    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    # Update last login
    user = await user_crud.update_user_login(db, user)

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    body: RefreshTokenRequest | None = None,
    refresh_token_cookie: str | None = Cookie(None, alias="refresh_token"),
):
    """Refresh access token using refresh token from cookie or body."""
    # Try to get token from body first, then from cookie
    token = None
    if body and body.refresh_token:
        token = body.refresh_token
    elif refresh_token_cookie:
        token = refresh_token_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required (provide in body or cookie)",
        )

    refresh_token = token  # Use consistent variable name

    # Hash the token to look it up
    token_hash = hash_refresh_token(refresh_token)

    # Find the refresh token
    stored_token = await user_crud.get_refresh_token_by_hash(db, token_hash)
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked
    if stored_token.revoked_at is not None:
        # Token reuse detected - revoke all user tokens for security
        await user_crud.revoke_all_user_tokens(db, stored_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked - possible token theft detected",
        )

    # Check if token is expired
    if stored_token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Get user
    user = await user_crud.get_user_by_id(db, stored_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Create new tokens (rotation)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": user.role},
    )

    new_raw_token, new_token_hash = create_refresh_token()
    await user_crud.create_refresh_token(db, user.id, new_token_hash)

    # Revoke old token with reference to new one
    await user_crud.revoke_refresh_token(db, stored_token, replaced_by=new_token_hash)

    # Set new refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_raw_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    db: DBSession,
    current_user: CurrentUser,
):
    """Logout user and revoke all refresh tokens."""
    # Revoke all refresh tokens for this user
    revoked_count = await user_crud.revoke_all_user_tokens(db, current_user.id)

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")

    return MessageResponse(message=f"Logged out successfully. {revoked_count} token(s) revoked.")


# =============================================================================
# Protected Endpoints
# =============================================================================


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update current user's profile."""
    updated_user = await user_crud.update_user_profile(
        db=db,
        user=current_user,
        full_name=user_update.full_name,
    )
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    db: DBSession,
    current_user: CurrentUser,
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    await user_crud.update_user_password(db, current_user, password_data.new_password)

    # Revoke all refresh tokens (force re-login on all devices)
    await user_crud.revoke_all_user_tokens(db, current_user.id)

    return MessageResponse(message="Password changed successfully. Please login again.")
