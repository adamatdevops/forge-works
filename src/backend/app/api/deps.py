"""API dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.db.base import get_db
from app.db.models.user import User, UserRole

# Security scheme
security = HTTPBearer(auto_error=False)


# =============================================================================
# Database Dependencies
# =============================================================================


DBSession = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException: If not authenticated or token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_user_optional(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work differently for authenticated users
    but don't require authentication.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(db, credentials)
    except HTTPException:
        return None


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


# =============================================================================
# Authorization Dependencies (Role-Based)
# =============================================================================


def require_role(*allowed_roles: UserRole):
    """
    Create a dependency that requires user to have one of the allowed roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_only_endpoint():
            ...

        # Or with user access:
        @router.get("/admin-data")
        async def admin_data(user: Annotated[User, Depends(require_role(UserRole.ADMIN))]):
            ...
    """

    async def role_checker(
        current_user: CurrentUser,
    ) -> User:
        user_role = UserRole(current_user.role)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


# Pre-configured role dependencies
async def require_admin(current_user: CurrentUser) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_user_or_admin(current_user: CurrentUser) -> User:
    """Require user or admin role (not viewer)."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin access required",
        )
    return current_user


# Type aliases for role-based access
AdminUser = Annotated[User, Depends(require_admin)]
AuthorizedUser = Annotated[User, Depends(require_user_or_admin)]


# =============================================================================
# Verified User Dependency
# =============================================================================


async def require_verified_user(current_user: CurrentUser) -> User:
    """Require user to be verified."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user


VerifiedUser = Annotated[User, Depends(require_verified_user)]
