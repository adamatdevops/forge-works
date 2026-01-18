"""Unit tests for security module.

Tests password hashing, JWT tokens, and validation functions.
"""

from datetime import UTC, datetime, timedelta

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    get_refresh_token_expiry,
    hash_refresh_token,
    validate_password_strength,
    verify_password,
)

# =============================================================================
# Password Hashing Tests
# =============================================================================


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing produces a hash."""
        password = "SecurePass123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are ~60 chars
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test password verification with correct password."""
        password = "SecurePass123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test password verification with wrong password."""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test same password produces different hashes (salting)."""
        password = "SecurePass123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        # Both should still verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test hashing empty password (edge case)."""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "Пароль123"  # Russian + numbers
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_long_password(self):
        """Test password near bcrypt's 72-byte limit."""
        # bcrypt has a 72-byte limit, so test near that boundary
        password = "A" * 20 + "a" * 20 + "1" * 20 + "!@#"  # 63 chars, under limit
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


# =============================================================================
# JWT Access Token Tests
# =============================================================================


class TestAccessToken:
    """Tests for JWT access token functions."""

    def test_create_access_token(self):
        """Test creating a valid access token."""
        user_id = "user-123"
        token = create_access_token(subject=user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_decode_valid_token(self):
        """Test decoding a valid access token."""
        user_id = "user-456"
        token = create_access_token(subject=user_id)
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token(self):
        """Test decoding an expired token returns None."""
        user_id = "user-789"
        # Create token that expires immediately
        token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-1),
        )
        payload = decode_access_token(token)

        assert payload is None

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_decode_tampered_token(self):
        """Test decoding a tampered token returns None."""
        user_id = "user-abc"
        token = create_access_token(subject=user_id)
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1][:-5] + "xxxxx"  # Modify payload
        tampered = ".".join(parts)

        payload = decode_access_token(tampered)
        assert payload is None

    def test_custom_expiry(self):
        """Test token with custom expiry time."""
        user_id = "user-def"
        expires = timedelta(hours=2)
        token = create_access_token(subject=user_id, expires_delta=expires)
        payload = decode_access_token(token)

        assert payload is not None
        # Check expiry is roughly 2 hours from now
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected = datetime.now(UTC) + expires
        assert abs((exp - expected).total_seconds()) < 5  # Within 5 seconds

    def test_additional_claims(self):
        """Test token with additional claims."""
        user_id = "user-ghi"
        claims = {"role": "admin", "team": "platform"}
        token = create_access_token(
            subject=user_id,
            additional_claims=claims,
        )
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["role"] == "admin"
        assert payload["team"] == "platform"

    def test_default_expiry_time(self):
        """Test default expiry is ACCESS_TOKEN_EXPIRE_MINUTES."""
        user_id = "user-jkl"
        token = create_access_token(subject=user_id)
        payload = decode_access_token(token)

        assert payload is not None
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        assert abs((exp - expected).total_seconds()) < 5


class TestDecodeAccessTokenType:
    """Tests for token type validation in decode."""

    def test_wrong_token_type(self):
        """Test decoding a token with wrong type returns None."""
        from jose import jwt

        from app.core.config import settings

        # Create a token with wrong type
        payload = {
            "sub": "user-123",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "refresh",  # Wrong type
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

        result = decode_access_token(token)
        assert result is None


# =============================================================================
# Refresh Token Tests
# =============================================================================


class TestRefreshToken:
    """Tests for refresh token functions."""

    def test_create_refresh_token(self):
        """Test creating a refresh token pair."""
        raw_token, token_hash = create_refresh_token()

        assert isinstance(raw_token, str)
        assert isinstance(token_hash, str)
        assert len(raw_token) > 30  # URL-safe base64 of 32 bytes
        assert len(token_hash) == 64  # SHA-256 hex digest

    def test_refresh_token_uniqueness(self):
        """Test each refresh token is unique."""
        tokens = [create_refresh_token() for _ in range(10)]
        raw_tokens = [t[0] for t in tokens]
        hashes = [t[1] for t in tokens]

        # All should be unique
        assert len(set(raw_tokens)) == 10
        assert len(set(hashes)) == 10

    def test_hash_matches_created_hash(self):
        """Test hashing raw token produces same hash."""
        raw_token, original_hash = create_refresh_token()
        computed_hash = hash_refresh_token(raw_token)

        assert computed_hash == original_hash

    def test_hash_refresh_token(self):
        """Test hashing a refresh token."""
        token = "test-token-value"
        hashed = hash_refresh_token(token)

        assert len(hashed) == 64  # SHA-256 hex
        assert hashed != token

    def test_hash_is_deterministic(self):
        """Test same input produces same hash."""
        token = "consistent-token"
        hash1 = hash_refresh_token(token)
        hash2 = hash_refresh_token(token)

        assert hash1 == hash2

    def test_refresh_token_expiry(self):
        """Test refresh token expiry calculation."""
        expiry = get_refresh_token_expiry()
        expected = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        assert abs((expiry - expected).total_seconds()) < 5


# =============================================================================
# Password Strength Validation Tests
# =============================================================================


class TestPasswordStrength:
    """Tests for password strength validation."""

    def test_valid_password(self):
        """Test valid password passes validation."""
        is_valid, error = validate_password_strength("SecurePass123")
        assert is_valid is True
        assert error is None

    def test_too_short(self):
        """Test password under 8 characters fails."""
        is_valid, error = validate_password_strength("Short1A")
        assert is_valid is False
        assert "8 characters" in error

    def test_no_uppercase(self):
        """Test password without uppercase fails."""
        is_valid, error = validate_password_strength("lowercase123")
        assert is_valid is False
        assert "uppercase" in error

    def test_no_lowercase(self):
        """Test password without lowercase fails."""
        is_valid, error = validate_password_strength("UPPERCASE123")
        assert is_valid is False
        assert "lowercase" in error

    def test_no_number(self):
        """Test password without number fails."""
        is_valid, error = validate_password_strength("NoNumbers")
        assert is_valid is False
        assert "number" in error

    def test_exactly_8_chars(self):
        """Test password with exactly 8 characters is valid."""
        is_valid, error = validate_password_strength("Abcdefg1")
        assert is_valid is True
        assert error is None

    def test_special_characters_allowed(self):
        """Test password with special characters is valid."""
        is_valid, error = validate_password_strength("Pass@#$123")
        assert is_valid is True

    def test_unicode_characters(self):
        """Test password with unicode meets requirements."""
        is_valid, error = validate_password_strength("Пароль12")
        assert is_valid is True  # Has upper, lower (Cyrillic), number


# =============================================================================
# Constants Tests
# =============================================================================


class TestSecurityConstants:
    """Tests for security constants."""

    def test_algorithm_is_hs256(self):
        """Test JWT algorithm is HS256."""
        assert ALGORITHM == "HS256"

    def test_access_token_expire_minutes(self):
        """Test access token expiry is reasonable."""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert 5 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 60

    def test_refresh_token_expire_days(self):
        """Test refresh token expiry is reasonable."""
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert 1 <= REFRESH_TOKEN_EXPIRE_DAYS <= 30
