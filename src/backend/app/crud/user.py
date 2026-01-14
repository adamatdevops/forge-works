"""CRUD operations for User model."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    get_password_hash,
    get_refresh_token_expiry,
    verify_password,
)
from app.db.models.user import RefreshToken, User, UserRole


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role.value,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user_login(db: AsyncSession, user: User) -> User:
    """Update user's last login timestamp."""
    user.last_login = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_password(
    db: AsyncSession, user: User, new_password: str
) -> User:
    """Update user's password."""
    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession, user: User, full_name: str | None = None
) -> User:
    """Update user's profile."""
    if full_name is not None:
        user.full_name = full_name
    user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return user


# =============================================================================
# Refresh Token Operations
# =============================================================================


async def create_refresh_token(
    db: AsyncSession, user_id: str, token_hash: str
) -> RefreshToken:
    """Create a new refresh token."""
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)
    return refresh_token


async def get_refresh_token_by_hash(
    db: AsyncSession, token_hash: str
) -> RefreshToken | None:
    """Get a refresh token by its hash."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(
    db: AsyncSession, refresh_token: RefreshToken, replaced_by: str | None = None
) -> RefreshToken:
    """Revoke a refresh token."""
    refresh_token.revoked_at = datetime.now(UTC)
    refresh_token.replaced_by = replaced_by
    await db.commit()
    await db.refresh(refresh_token)
    return refresh_token


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> int:
    """Revoke all refresh tokens for a user."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()
    now = datetime.now(UTC)
    for token in tokens:
        token.revoked_at = now
    await db.commit()
    return len(tokens)


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Delete expired refresh tokens (cleanup task)."""
    now = datetime.now(UTC)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.expires_at < now)
    )
    tokens = result.scalars().all()
    for token in tokens:
        await db.delete(token)
    await db.commit()
    return len(tokens)
