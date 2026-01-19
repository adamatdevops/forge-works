"""Unit tests for CRUD operations.

Tests pure functions and CRUD logic using mocks.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.crud.service import ServiceCRUD, slugify
from app.crud.template import TemplateCRUD
from app.db.models.service import Service, ServiceStatus, ServiceTier
from app.db.models.template import Template
from app.schemas.service import ServiceCreate, ServiceUpdate

# =============================================================================
# Slugify Function Tests
# =============================================================================


class TestSlugify:
    """Tests for slugify utility function."""

    def test_basic_slugify(self):
        """Test basic name to slug conversion."""
        assert slugify("My Service") == "my-service"

    def test_lowercase(self):
        """Test conversion to lowercase."""
        assert slugify("UPPERCASE") == "uppercase"
        assert slugify("MixedCase") == "mixedcase"

    def test_spaces_to_hyphens(self):
        """Test spaces are converted to hyphens."""
        assert slugify("hello world") == "hello-world"
        assert slugify("multiple   spaces") == "multiple-spaces"

    def test_special_characters_removed(self):
        """Test special characters are removed."""
        assert slugify("service!@#$%^&*()") == "service"
        assert slugify("test.service.name") == "testservicename"

    def test_hyphens_preserved(self):
        """Test hyphens are preserved and normalized."""
        assert slugify("already-slugified") == "already-slugified"
        assert slugify("multiple---hyphens") == "multiple-hyphens"

    def test_whitespace_stripped(self):
        """Test leading/trailing whitespace is stripped."""
        assert slugify("  padded  ") == "padded"
        assert slugify("\ttabbed\n") == "tabbed"

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert slugify("") == ""

    def test_unicode_characters(self):
        """Test unicode characters are preserved."""
        # Unicode word characters are preserved by the regex
        assert slugify("café") == "café"
        assert slugify("naïve") == "naïve"
        # Non-word unicode characters are removed
        assert slugify("test™") == "test"

    def test_numbers_preserved(self):
        """Test numbers are preserved."""
        assert slugify("service123") == "service123"
        assert slugify("v2 API") == "v2-api"

    def test_real_world_examples(self):
        """Test real-world service name examples."""
        assert slugify("User API") == "user-api"
        assert slugify("Payment Service v2") == "payment-service-v2"
        assert slugify("ML Pipeline (GPU)") == "ml-pipeline-gpu"
        assert slugify("auth-service") == "auth-service"


# =============================================================================
# ServiceCRUD Tests
# =============================================================================


class TestServiceCRUDGetById:
    """Tests for ServiceCRUD.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test getting a service by ID when it exists."""
        mock_db = AsyncMock()
        mock_service = MagicMock(spec=Service)
        mock_service.id = "test-id"
        mock_service.name = "test-service"

        # Mock the query execution
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_by_id(mock_db, "test-id")

        assert result is mock_service
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting a service by ID when it doesn't exist."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_by_id(mock_db, "nonexistent-id")

        assert result is None


class TestServiceCRUDGetBySlug:
    """Tests for ServiceCRUD.get_by_slug method."""

    @pytest.mark.asyncio
    async def test_get_by_slug_found(self):
        """Test getting a service by slug when it exists."""
        mock_db = AsyncMock()
        mock_service = MagicMock(spec=Service)
        mock_service.slug = "test-slug"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_by_slug(mock_db, "test-slug")

        assert result is mock_service

    @pytest.mark.asyncio
    async def test_get_by_slug_not_found(self):
        """Test getting a service by slug when it doesn't exist."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_by_slug(mock_db, "nonexistent-slug")

        assert result is None


class TestServiceCRUDGetAll:
    """Tests for ServiceCRUD.get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """Test get_all returns a list of services."""
        mock_db = AsyncMock()
        mock_services = [
            MagicMock(spec=Service, name="service-1"),
            MagicMock(spec=Service, name="service-2"),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_services
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_all(mock_db)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_empty(self):
        """Test get_all returns empty list when no services."""
        mock_db = AsyncMock()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.get_all(mock_db)

        assert result == []


class TestServiceCRUDCount:
    """Tests for ServiceCRUD.count method."""

    @pytest.mark.asyncio
    async def test_count_returns_integer(self):
        """Test count returns an integer."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.count(mock_db)

        assert result == 5
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_count_zero(self):
        """Test count returns zero when no services."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        result = await ServiceCRUD.count(mock_db)

        assert result == 0


class TestServiceCRUDCreate:
    """Tests for ServiceCRUD.create method."""

    @pytest.mark.asyncio
    async def test_create_service(self):
        """Test creating a new service."""
        mock_db = AsyncMock()

        # Create a mock service that will be returned
        mock_service = MagicMock(spec=Service)
        mock_service.id = str(uuid4())
        mock_service.name = "new-service"
        mock_service.slug = "new-service"
        mock_service.status = ServiceStatus.PROVISIONING

        # Mock get_by_id to return the service after creation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        mock_db.execute.return_value = mock_result

        data = ServiceCreate(
            name="New Service",
            team_id=str(uuid4()),
            description="A new service",
        )

        with patch.object(ServiceCRUD, "get_by_id", return_value=mock_service):
            result = await ServiceCRUD.create(mock_db, data)

        assert result is mock_service
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestServiceCRUDUpdate:
    """Tests for ServiceCRUD.update method."""

    @pytest.mark.asyncio
    async def test_update_service(self):
        """Test updating a service."""
        mock_db = AsyncMock()
        mock_service = MagicMock(spec=Service)
        mock_service.id = str(uuid4())
        mock_service.name = "old-name"

        # Mock get_by_id for the return
        with patch.object(ServiceCRUD, "get_by_id", return_value=mock_service):
            data = ServiceUpdate(name="new-name", description="updated")
            await ServiceCRUD.update(mock_db, mock_service, data)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_service)


class TestServiceCRUDDelete:
    """Tests for ServiceCRUD.delete method."""

    @pytest.mark.asyncio
    async def test_delete_service(self):
        """Test deleting a service."""
        mock_db = AsyncMock()
        mock_service = MagicMock(spec=Service)

        await ServiceCRUD.delete(mock_db, mock_service)

        mock_db.delete.assert_called_once_with(mock_service)
        mock_db.commit.assert_called_once()


class TestServiceCRUDGetStats:
    """Tests for ServiceCRUD.get_stats method."""

    @pytest.mark.asyncio
    async def test_get_stats_structure(self):
        """Test get_stats returns expected structure."""
        mock_db = AsyncMock()

        # Mock multiple execute calls for different queries
        mock_results = [
            MagicMock(scalar_one=MagicMock(return_value=10)),  # total
            MagicMock(
                all=MagicMock(
                    return_value=[
                        (ServiceStatus.HEALTHY, 5),
                        (ServiceStatus.DEGRADED, 3),
                    ]
                )
            ),  # by_status
            MagicMock(
                all=MagicMock(
                    return_value=[
                        (ServiceTier.CRITICAL, 2),
                        (ServiceTier.STANDARD, 8),
                    ]
                )
            ),  # by_tier
            MagicMock(scalar_one=MagicMock(return_value=2)),  # active_anomalies
            MagicMock(scalar_one=MagicMock(return_value=15)),  # deploys_today
            MagicMock(scalar_one=MagicMock(return_value=3)),  # rollbacks
        ]
        mock_db.execute.side_effect = mock_results

        result = await ServiceCRUD.get_stats(mock_db)

        assert "total_services" in result
        assert "by_status" in result
        assert "by_tier" in result
        assert "active_anomalies" in result
        assert "deploys_today" in result
        assert "rollbacks_this_week" in result


# =============================================================================
# TemplateCRUD Tests
# =============================================================================


class TestTemplateCRUDGetById:
    """Tests for TemplateCRUD.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test getting a template by ID when it exists."""
        mock_db = AsyncMock()
        mock_template = MagicMock(spec=Template)
        mock_template.id = "template-id"
        mock_template.name = "test-template"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.get_by_id(mock_db, "template-id")

        assert result is mock_template

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting a template by ID when it doesn't exist."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.get_by_id(mock_db, "nonexistent-id")

        assert result is None


class TestTemplateCRUDGetBySlug:
    """Tests for TemplateCRUD.get_by_slug method."""

    @pytest.mark.asyncio
    async def test_get_by_slug_found(self):
        """Test getting a template by slug when it exists."""
        mock_db = AsyncMock()
        mock_template = MagicMock(spec=Template)
        mock_template.slug = "test-template"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.get_by_slug(mock_db, "test-template")

        assert result is mock_template


class TestTemplateCRUDGetAll:
    """Tests for TemplateCRUD.get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """Test get_all returns a list of templates."""
        mock_db = AsyncMock()
        mock_templates = [
            MagicMock(spec=Template),
            MagicMock(spec=Template),
            MagicMock(spec=Template),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_templates
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.get_all(mock_db)

        assert len(result) == 3


class TestTemplateCRUDCount:
    """Tests for TemplateCRUD.count method."""

    @pytest.mark.asyncio
    async def test_count_returns_integer(self):
        """Test count returns an integer."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.count(mock_db)

        assert result == 5


class TestTemplateCRUDExists:
    """Tests for TemplateCRUD.exists method."""

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """Test exists returns True when template exists."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.exists(mock_db, "existing-id")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """Test exists returns False when template doesn't exist."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        result = await TemplateCRUD.exists(mock_db, "nonexistent-id")

        assert result is False


class TestTemplateCRUDIncrementUsage:
    """Tests for TemplateCRUD.increment_usage method."""

    @pytest.mark.asyncio
    async def test_increment_usage(self):
        """Test incrementing template usage count."""
        mock_db = AsyncMock()
        mock_template = MagicMock(spec=Template)
        mock_template.usage_count = 5

        await TemplateCRUD.increment_usage(mock_db, mock_template)

        assert mock_template.usage_count == 6
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_template)
