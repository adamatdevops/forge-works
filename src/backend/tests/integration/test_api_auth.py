"""Integration tests for authentication API endpoints.

Tests the auth endpoints using mocked database operations due to
PostgreSQL UUID type incompatibility with SQLite test database.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.main import app

# =============================================================================
# Test Fixtures
# =============================================================================


def create_mock_user(
    user_id: str | None = None,
    email: str = "test@example.com",
    password: str = "SecurePass123",
    full_name: str = "Test User",
    role: str = "user",
    is_active: bool = True,
    is_verified: bool = False,
):
    """Create a mock user object."""
    user = MagicMock()
    user.id = user_id or str(uuid4())
    user.email = email
    user.hashed_password = get_password_hash(password)
    user.full_name = full_name
    user.role = role
    user.is_active = is_active
    user.is_verified = is_verified
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    user.last_login = None
    return user


def create_mock_refresh_token(
    user_id: str,
    token_hash: str,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
):
    """Create a mock refresh token object."""
    token = MagicMock()
    token.id = str(uuid4())
    token.user_id = user_id
    token.token_hash = token_hash
    token.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=7))
    token.revoked_at = revoked_at
    token.created_at = datetime.now(UTC)
    return token


@pytest.fixture
def mock_user():
    """Create a default mock user for testing."""
    return create_mock_user()


@pytest.fixture
def auth_headers(mock_user):
    """Create authorization headers with a valid token."""
    token = create_access_token(
        subject=mock_user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": mock_user.role},
    )
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Registration Tests
# =============================================================================


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful user registration."""
        new_user = create_mock_user(
            email="newuser@example.com",
            full_name="New User",
        )

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_user_by_email = AsyncMock(return_value=None)
            mock_crud.create_user = AsyncMock(return_value=new_user)
            mock_crud.create_refresh_token = AsyncMock()
            mock_crud.update_user_login = AsyncMock(return_value=new_user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "newuser@example.com",
                        "password": "SecurePass123",
                        "full_name": "New User",
                    },
                )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        assert data["expires_in"] == ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registration with existing email fails."""
        existing_user = create_mock_user()

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_user_by_email = AsyncMock(return_value=existing_user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": existing_user.email,
                        "password": "SecurePass123",
                        "full_name": "Another User",
                    },
                )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self):
        """Test registration with weak password fails validation."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "weak",  # Too short, no uppercase, no number
                    "full_name": "Test User",
                },
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_invalid_email(self):
        """Test registration with invalid email fails validation."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "not-an-email",
                    "password": "SecurePass123",
                    "full_name": "Test User",
                },
            )

        assert response.status_code == 422


# =============================================================================
# Login Tests
# =============================================================================


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        password = "SecurePass123"
        user = create_mock_user(password=password)

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.authenticate_user = AsyncMock(return_value=user)
            mock_crud.create_refresh_token = AsyncMock()
            mock_crud.update_user_login = AsyncMock(return_value=user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": user.email,
                        "password": password,
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == user.email

        # Check refresh token cookie is set
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.authenticate_user = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "WrongPassword123",
                    },
                )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """Test login with non-existent email fails."""
        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.authenticate_user = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "nonexistent@example.com",
                        "password": "SecurePass123",
                    },
                )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_disabled_user(self):
        """Test login with disabled account fails."""
        user = create_mock_user(is_active=False)

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.authenticate_user = AsyncMock(return_value=user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": user.email,
                        "password": "SecurePass123",
                    },
                )

        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]


# =============================================================================
# Refresh Token Tests
# =============================================================================


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_with_body_token(self):
        """Test token refresh using token in request body."""
        user = create_mock_user()
        raw_token, token_hash = create_refresh_token()
        stored_token = create_mock_refresh_token(user.id, token_hash)

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
            mock_crud.get_user_by_id = AsyncMock(return_value=user)
            mock_crud.create_refresh_token = AsyncMock()
            mock_crud.revoke_refresh_token = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": raw_token},
                )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    @pytest.mark.asyncio
    async def test_refresh_with_cookie(self):
        """Test token refresh using cookie."""
        user = create_mock_user()
        raw_token, token_hash = create_refresh_token()
        stored_token = create_mock_refresh_token(user.id, token_hash)

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
            mock_crud.get_user_by_id = AsyncMock(return_value=user)
            mock_crud.create_refresh_token = AsyncMock()
            mock_crud.revoke_refresh_token = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    cookies={"refresh_token": raw_token},
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_no_token(self):
        """Test refresh without token fails."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self):
        """Test refresh with invalid token fails."""
        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_refresh_token_by_hash = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "invalid-token"},
                )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_revoked_token(self):
        """Test refresh with revoked token fails and triggers security response."""
        user = create_mock_user()
        raw_token, token_hash = create_refresh_token()
        stored_token = create_mock_refresh_token(
            user.id,
            token_hash,
            revoked_at=datetime.now(UTC),  # Revoked
        )

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
            mock_crud.revoke_all_user_tokens = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": raw_token},
                )

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"]
        # Should revoke all tokens for security
        mock_crud.revoke_all_user_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self):
        """Test refresh with expired token fails."""
        user = create_mock_user()
        raw_token, token_hash = create_refresh_token()
        stored_token = create_mock_refresh_token(
            user.id,
            token_hash,
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
        )

        with patch("app.api.routes.auth.user_crud") as mock_crud:
            mock_crud.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": raw_token},
                )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"]


# =============================================================================
# Logout Tests
# =============================================================================


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout."""
        user = create_mock_user()
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role},
        )

        with patch("app.api.deps.user_crud") as mock_deps_crud:
            mock_deps_crud.get_user_by_id = AsyncMock(return_value=user)

            with patch("app.api.routes.auth.user_crud") as mock_auth_crud:
                mock_auth_crud.revoke_all_user_tokens = AsyncMock(return_value=2)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {token}"},
                    )

        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]
        assert "2 token(s) revoked" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_logout_no_auth(self):
        """Test logout without authentication fails."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401


# =============================================================================
# Protected Endpoint Tests
# =============================================================================


class TestMeEndpoint:
    """Tests for GET/PATCH /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_success(self):
        """Test getting current user profile."""
        user = create_mock_user()
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role},
        )

        with patch("app.api.deps.user_crud") as mock_crud:
            mock_crud.get_user_by_id = AsyncMock(return_value=user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name

    @pytest.mark.asyncio
    async def test_get_me_no_auth(self):
        """Test getting profile without auth fails."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_expired_token(self):
        """Test getting profile with expired token fails."""
        user = create_mock_user()
        token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(seconds=-1),  # Expired
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_success(self):
        """Test updating current user profile."""
        user = create_mock_user()
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role},
        )

        updated_user = create_mock_user(full_name="Updated Name")
        updated_user.id = user.id

        with patch("app.api.deps.user_crud") as mock_deps_crud:
            mock_deps_crud.get_user_by_id = AsyncMock(return_value=user)

            with patch("app.api.routes.auth.user_crud") as mock_auth_crud:
                mock_auth_crud.update_user_profile = AsyncMock(return_value=updated_user)

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.patch(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"full_name": "Updated Name"},
                    )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"


# =============================================================================
# Change Password Tests
# =============================================================================


class TestChangePasswordEndpoint:
    """Tests for POST /api/v1/auth/change-password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        password = "SecurePass123"
        user = create_mock_user(password=password)
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role},
        )

        with patch("app.api.deps.user_crud") as mock_deps_crud:
            mock_deps_crud.get_user_by_id = AsyncMock(return_value=user)

            with patch("app.api.routes.auth.user_crud") as mock_auth_crud:
                mock_auth_crud.update_user_password = AsyncMock()
                mock_auth_crud.revoke_all_user_tokens = AsyncMock()

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/change-password",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "current_password": password,
                            "new_password": "NewSecurePass456",
                        },
                    )

        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
        mock_auth_crud.revoke_all_user_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self):
        """Test password change with wrong current password fails."""
        user = create_mock_user(password="SecurePass123")
        token = create_access_token(
            subject=user.id,
            additional_claims={"role": user.role},
        )

        with patch("app.api.deps.user_crud") as mock_crud:
            mock_crud.get_user_by_id = AsyncMock(return_value=user)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/change-password",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "current_password": "WrongPassword123",
                        "new_password": "NewSecurePass456",
                    },
                )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]
