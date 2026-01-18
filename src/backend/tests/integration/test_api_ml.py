"""Integration tests for ML recommendation API endpoints.

Tests the ML recommendation endpoints including template suggestions,
template listing, and health checks.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.ml import TemplateType


# =============================================================================
# ML Health Endpoint Tests
# =============================================================================


class TestMLHealthEndpoint:
    """Tests for GET /api/v1/ml/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test ML health endpoint returns healthy status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/ml/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "model_loaded" in data
        assert "mode" in data
        assert data["mode"] in ["ml", "rule-based"]


# =============================================================================
# Template List Endpoint Tests
# =============================================================================


class TestListTemplatesEndpoint:
    """Tests for GET /api/v1/ml/templates endpoint."""

    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Test listing all templates."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/ml/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "count" in data
        assert data["count"] == 5  # 5 template types
        assert len(data["templates"]) == 5

    @pytest.mark.asyncio
    async def test_template_structure(self):
        """Test each template has required fields."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/ml/templates")

        data = response.json()
        for template in data["templates"]:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "best_for" in template
            assert "includes" in template
            assert isinstance(template["best_for"], list)
            assert isinstance(template["includes"], list)


# =============================================================================
# Get Template Endpoint Tests
# =============================================================================


class TestGetTemplateEndpoint:
    """Tests for GET /api/v1/ml/templates/{template_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_python_template(self):
        """Test getting Python microservice template."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/ml/templates/{TemplateType.MICROSERVICE_PYTHON.value}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "microservice-python"
        assert "name" in data
        assert "Python" in data["name"]

    @pytest.mark.asyncio
    async def test_get_node_template(self):
        """Test getting Node.js microservice template."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/ml/templates/{TemplateType.MICROSERVICE_NODE.value}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "microservice-node"
        assert "Node" in data["name"]

    @pytest.mark.asyncio
    async def test_get_ml_pipeline_template(self):
        """Test getting ML pipeline template."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/ml/templates/{TemplateType.ML_PIPELINE.value}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ml-pipeline"
        assert "ML" in data["name"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self):
        """Test getting non-existent template returns 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/ml/templates/nonexistent-template")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# Recommendation Endpoint Tests
# =============================================================================


class TestRecommendEndpoint:
    """Tests for POST /api/v1/ml/recommend endpoint."""

    @pytest.mark.asyncio
    async def test_recommend_python_api(self):
        """Test recommendation for Python API workload."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "primary" in data
        assert "alternatives" in data
        assert "input_summary" in data

        # Primary should have template, confidence, reasons
        primary = data["primary"]
        assert "template" in primary
        assert "confidence" in primary
        assert "reasons" in primary
        assert primary["template"] == TemplateType.MICROSERVICE_PYTHON.value
        assert 0.0 <= primary["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_recommend_nodejs_api(self):
        """Test recommendation for Node.js API workload."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "javascript",
                    "workload_type": "api",
                    "expected_rps": 1000,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 3,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["primary"]["template"] == TemplateType.MICROSERVICE_NODE.value

    @pytest.mark.asyncio
    async def test_recommend_ml_pipeline(self):
        """Test recommendation for ML workload."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "ml-pipeline",  # Correct enum value
                    "expected_rps": 10,
                    "needs_database": True,
                    "needs_cache": False,
                    "needs_queue": True,
                    "team_size": 4,
                    "needs_gpu": True,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["primary"]["template"] == TemplateType.ML_PIPELINE.value

    @pytest.mark.asyncio
    async def test_recommend_worker_service(self):
        """Test recommendation for background worker workload."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "worker",
                    "expected_rps": 50,
                    "needs_database": True,
                    "needs_cache": False,
                    "needs_queue": True,
                    "team_size": 3,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["primary"]["template"] == TemplateType.WORKER_SERVICE.value

    @pytest.mark.asyncio
    async def test_recommend_frontend_app(self):
        """Test recommendation for frontend workload returns valid response."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "typescript",
                    "workload_type": "frontend",
                    "expected_rps": 100,
                    "needs_database": False,
                    "needs_cache": False,
                    "needs_queue": False,
                    "team_size": 2,
                },
            )

        assert response.status_code == 200
        data = response.json()
        # Verify response structure; frontend-app should be in top recommendations
        assert "primary" in data
        assert data["primary"]["template"] in [t.value for t in TemplateType]
        # Frontend-app should be either primary or in alternatives
        all_templates = [data["primary"]["template"]] + [
            alt["template"] for alt in data["alternatives"]
        ]
        assert TemplateType.FRONTEND_APP.value in all_templates

    @pytest.mark.asyncio
    async def test_recommend_has_alternatives(self):
        """Test recommendation includes alternatives."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        data = response.json()
        assert isinstance(data["alternatives"], list)
        # Should have at least one alternative
        assert len(data["alternatives"]) >= 1

    @pytest.mark.asyncio
    async def test_recommend_includes_input_summary(self):
        """Test recommendation includes input summary."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        data = response.json()
        assert "input_summary" in data
        assert isinstance(data["input_summary"], dict)
        assert "language" in data["input_summary"]

    @pytest.mark.asyncio
    async def test_recommend_missing_required_field(self):
        """Test recommendation fails with missing required fields."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    # Missing workload_type and other required fields
                },
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_recommend_invalid_workload_type(self):
        """Test recommendation fails with invalid workload type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "invalid-type",
                    "expected_rps": 100,
                    "needs_database": False,
                    "team_size": 3,
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_recommend_invalid_language(self):
        """Test recommendation fails with invalid language."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "cobol",  # Invalid enum value
                    "workload_type": "api",
                    "expected_rps": 100,
                    "needs_database": True,
                    "team_size": 2,
                },
            )

        assert response.status_code == 422


# =============================================================================
# Feedback Endpoint Tests
# =============================================================================


class TestFeedbackEndpoint:
    """Tests for POST /api/v1/ml/feedback endpoint."""

    @pytest.mark.asyncio
    async def test_submit_feedback_primary(self):
        """Test submitting feedback when primary was selected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/feedback",
                json={
                    "recommendation_id": "rec-123",
                    "selected_template": "microservice-python",
                    "was_primary": True,
                    "feedback_text": "Perfect fit for our use case",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "received"
        assert data["was_primary"] is True
        assert data["selected_template"] == "microservice-python"

    @pytest.mark.asyncio
    async def test_submit_feedback_alternative(self):
        """Test submitting feedback when alternative was selected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/feedback",
                json={
                    "recommendation_id": "rec-456",
                    "selected_template": "microservice-node",
                    "was_primary": False,
                    "feedback_text": "Team prefers Node.js",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["was_primary"] is False

    @pytest.mark.asyncio
    async def test_submit_feedback_minimal(self):
        """Test submitting feedback with minimal required fields."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/feedback",
                json={
                    "selected_template": "worker-service",
                    "was_primary": False,
                },
            )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_template(self):
        """Test feedback with invalid template fails."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/feedback",
                json={
                    "recommendation_id": "rec-789",
                    "selected_template": "invalid-template",
                    "was_primary": True,
                },
            )

        assert response.status_code == 422


# =============================================================================
# Response Structure Tests
# =============================================================================


class TestRecommendationResponseStructure:
    """Tests for recommendation response structure."""

    @pytest.mark.asyncio
    async def test_primary_structure(self):
        """Test primary recommendation has correct structure."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        data = response.json()
        primary = data["primary"]

        assert "template" in primary
        assert "confidence" in primary
        assert "reasons" in primary
        assert isinstance(primary["reasons"], list)

    @pytest.mark.asyncio
    async def test_alternative_structure(self):
        """Test alternatives have correct structure."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        data = response.json()
        alternatives = data["alternatives"]

        assert isinstance(alternatives, list)
        if alternatives:  # If there are alternatives
            for alt in alternatives:
                assert "template" in alt
                assert "confidence" in alt
                assert "reasons" in alt

    @pytest.mark.asyncio
    async def test_input_summary_structure(self):
        """Test input_summary has correct structure."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ml/recommend",
                json={
                    "language": "python",
                    "workload_type": "api",
                    "expected_rps": 500,
                    "needs_database": True,
                    "needs_cache": True,
                    "needs_queue": False,
                    "team_size": 5,
                },
            )

        data = response.json()
        input_summary = data["input_summary"]

        assert isinstance(input_summary, dict)
        # Should contain at least language and workload_type
        assert "language" in input_summary
        assert "workload_type" in input_summary
