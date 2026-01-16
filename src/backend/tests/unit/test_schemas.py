"""Unit tests for Pydantic schemas.

Tests schema validation, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError

from app.db.models.service import ServiceStatus, ServiceTier
from app.schemas.auth import (
    PasswordChange,
    TokenPayload,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.ml import (
    DatabaseType,
    ProgrammingLanguage,
    RecommendationResponse,
    TemplateRecommendation,
    TemplateType,
    TrainingExample,
    WorkloadFeatures,
    WorkloadType,
)
from app.schemas.service import ServiceBase, ServiceCreate, ServiceUpdate


# =============================================================================
# Auth Schema Tests
# =============================================================================


class TestUserRegister:
    """Tests for UserRegister schema."""

    def test_valid_registration(self):
        """Test valid user registration data."""
        data = UserRegister(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test User",
        )
        assert data.email == "test@example.com"
        assert data.password == "SecurePass123"
        assert data.full_name == "Test User"

    def test_invalid_email(self):
        """Test validation fails for invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="not-an-email",
                password="SecurePass123",
                full_name="Test User",
            )
        assert "email" in str(exc_info.value)

    def test_password_too_short(self):
        """Test validation fails for password under 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Short1",
                full_name="Test User",
            )
        assert "password" in str(exc_info.value).lower()

    def test_password_no_uppercase(self):
        """Test validation fails for password without uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="lowercase123",
                full_name="Test User",
            )
        assert "uppercase" in str(exc_info.value).lower()

    def test_password_no_lowercase(self):
        """Test validation fails for password without lowercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="UPPERCASE123",
                full_name="Test User",
            )
        assert "lowercase" in str(exc_info.value).lower()

    def test_password_no_number(self):
        """Test validation fails for password without number."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="NoNumbersHere",
                full_name="Test User",
            )
        assert "number" in str(exc_info.value).lower()

    def test_empty_full_name(self):
        """Test validation fails for empty full name."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="SecurePass123",
                full_name="",
            )
        assert "full_name" in str(exc_info.value)


class TestUserLogin:
    """Tests for UserLogin schema."""

    def test_valid_login(self):
        """Test valid login data."""
        data = UserLogin(
            email="test@example.com",
            password="anypassword",
        )
        assert data.email == "test@example.com"
        assert data.password == "anypassword"

    def test_invalid_email(self):
        """Test validation fails for invalid email."""
        with pytest.raises(ValidationError):
            UserLogin(email="invalid", password="password")


class TestPasswordChange:
    """Tests for PasswordChange schema."""

    def test_valid_password_change(self):
        """Test valid password change data."""
        data = PasswordChange(
            current_password="OldPass123",
            new_password="NewPass456",
        )
        assert data.current_password == "OldPass123"
        assert data.new_password == "NewPass456"

    def test_weak_new_password(self):
        """Test validation fails for weak new password."""
        with pytest.raises(ValidationError):
            PasswordChange(
                current_password="OldPass123",
                new_password="weak",
            )


# =============================================================================
# Service Schema Tests
# =============================================================================


class TestServiceBase:
    """Tests for ServiceBase schema."""

    def test_valid_service(self):
        """Test valid service data."""
        data = ServiceCreate(
            name="my-service",
            team_id="team-123",
            description="A test service",
        )
        assert data.name == "my-service"
        assert data.team_id == "team-123"
        assert data.tier == ServiceTier.STANDARD

    def test_minimal_service(self):
        """Test minimal required fields."""
        data = ServiceCreate(
            name="api",
            team_id="t1",
        )
        assert data.name == "api"
        assert data.tags == []
        assert data.metadata == {}

    def test_name_too_long(self):
        """Test validation fails for name over 100 chars."""
        with pytest.raises(ValidationError):
            ServiceCreate(
                name="a" * 101,
                team_id="team-123",
            )

    def test_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValidationError):
            ServiceCreate(
                name="",
                team_id="team-123",
            )

    def test_all_tiers(self):
        """Test all service tier values are accepted."""
        for tier in ServiceTier:
            data = ServiceCreate(
                name="service",
                team_id="team-123",
                tier=tier,
            )
            assert data.tier == tier


class TestServiceUpdate:
    """Tests for ServiceUpdate schema (partial updates)."""

    def test_empty_update(self):
        """Test empty update is valid (all fields optional)."""
        data = ServiceUpdate()
        assert data.name is None
        assert data.team_id is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        data = ServiceUpdate(
            name="new-name",
            status=ServiceStatus.HEALTHY,
        )
        assert data.name == "new-name"
        assert data.status == ServiceStatus.HEALTHY
        assert data.tier is None


# =============================================================================
# ML Schema Tests
# =============================================================================


class TestWorkloadFeatures:
    """Tests for ML WorkloadFeatures schema."""

    def test_valid_workload(self):
        """Test valid workload features."""
        data = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
            needs_queue=False,
            needs_cache=True,
            needs_gpu=False,
            expected_rps=500,
            expected_memory_mb=1024,
            team_size=8,
            compliance_required=True,
        )
        assert data.language == ProgrammingLanguage.PYTHON
        assert data.workload_type == WorkloadType.API
        assert data.expected_rps == 500

    def test_default_values(self):
        """Test default values are applied."""
        data = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        assert data.needs_database is False
        assert data.database_type == DatabaseType.NONE
        assert data.needs_queue is False
        assert data.needs_cache is False
        assert data.expected_rps == 100
        assert data.expected_memory_mb == 512
        assert data.team_size == 5

    def test_rps_bounds(self):
        """Test RPS validation bounds."""
        # Valid minimum
        data = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            expected_rps=0,
        )
        assert data.expected_rps == 0

        # Invalid negative
        with pytest.raises(ValidationError):
            WorkloadFeatures(
                language=ProgrammingLanguage.PYTHON,
                workload_type=WorkloadType.API,
                expected_rps=-1,
            )

    def test_memory_bounds(self):
        """Test memory validation bounds."""
        # Valid minimum
        data = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            expected_memory_mb=128,
        )
        assert data.expected_memory_mb == 128

        # Below minimum
        with pytest.raises(ValidationError):
            WorkloadFeatures(
                language=ProgrammingLanguage.PYTHON,
                workload_type=WorkloadType.API,
                expected_memory_mb=64,
            )

    def test_all_languages(self):
        """Test all programming languages are valid."""
        for lang in ProgrammingLanguage:
            data = WorkloadFeatures(
                language=lang,
                workload_type=WorkloadType.API,
            )
            assert data.language == lang

    def test_all_workload_types(self):
        """Test all workload types are valid."""
        for wt in WorkloadType:
            data = WorkloadFeatures(
                language=ProgrammingLanguage.PYTHON,
                workload_type=wt,
            )
            assert data.workload_type == wt


class TestTemplateRecommendation:
    """Tests for TemplateRecommendation schema."""

    def test_valid_recommendation(self):
        """Test valid recommendation structure."""
        data = TemplateRecommendation(
            template=TemplateType.MICROSERVICE_PYTHON,
            confidence=0.92,
            reasons=["Python language matches", "PostgreSQL support"],
        )
        assert data.template == TemplateType.MICROSERVICE_PYTHON
        assert data.confidence == 0.92
        assert len(data.reasons) == 2

    def test_confidence_bounds(self):
        """Test confidence score bounds."""
        # Valid bounds
        TemplateRecommendation(
            template=TemplateType.MICROSERVICE_PYTHON,
            confidence=0.0,
            reasons=[],
        )
        TemplateRecommendation(
            template=TemplateType.MICROSERVICE_PYTHON,
            confidence=1.0,
            reasons=[],
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            TemplateRecommendation(
                template=TemplateType.MICROSERVICE_PYTHON,
                confidence=-0.1,
                reasons=[],
            )
        with pytest.raises(ValidationError):
            TemplateRecommendation(
                template=TemplateType.MICROSERVICE_PYTHON,
                confidence=1.1,
                reasons=[],
            )


class TestRecommendationResponse:
    """Tests for RecommendationResponse schema."""

    def test_valid_response(self):
        """Test valid recommendation response."""
        primary = TemplateRecommendation(
            template=TemplateType.MICROSERVICE_PYTHON,
            confidence=0.92,
            reasons=["Python matches"],
        )
        alt = TemplateRecommendation(
            template=TemplateType.WORKER_SERVICE,
            confidence=0.45,
            reasons=["Could work for async"],
        )
        data = RecommendationResponse(
            primary=primary,
            alternatives=[alt],
            input_summary={"language": "python"},
        )
        assert data.primary.confidence == 0.92
        assert len(data.alternatives) == 1

    def test_empty_alternatives(self):
        """Test response with no alternatives."""
        primary = TemplateRecommendation(
            template=TemplateType.ML_PIPELINE,
            confidence=0.95,
            reasons=["Perfect match"],
        )
        data = RecommendationResponse(
            primary=primary,
            alternatives=[],
            input_summary={},
        )
        assert data.alternatives == []


class TestTrainingExample:
    """Tests for TrainingExample schema."""

    def test_valid_training_example(self):
        """Test valid training example."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        data = TrainingExample(
            features=features,
            label=TemplateType.MICROSERVICE_PYTHON,
            weight=1.0,
        )
        assert data.label == TemplateType.MICROSERVICE_PYTHON
        assert data.weight == 1.0

    def test_default_weight(self):
        """Test default weight is 1.0."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        data = TrainingExample(
            features=features,
            label=TemplateType.MICROSERVICE_PYTHON,
        )
        assert data.weight == 1.0

    def test_invalid_weight(self):
        """Test negative weight is rejected."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        with pytest.raises(ValidationError):
            TrainingExample(
                features=features,
                label=TemplateType.MICROSERVICE_PYTHON,
                weight=-0.5,
            )
