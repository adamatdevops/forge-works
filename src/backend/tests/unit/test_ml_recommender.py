"""Unit tests for ML template recommender.

Tests feature conversion, scoring logic, and recommendation generation.
"""

import numpy as np
import pytest

from app.ml.recommender import TemplateRecommender, get_recommender
from app.schemas.ml import (
    DatabaseType,
    ProgrammingLanguage,
    RecommendationResponse,
    TemplateType,
    WorkloadFeatures,
    WorkloadType,
)

# =============================================================================
# Feature Vector Conversion Tests
# =============================================================================


class TestFeatureVectorConversion:
    """Tests for _features_to_vector method."""

    @pytest.fixture
    def recommender(self):
        """Create recommender instance for testing."""
        return TemplateRecommender(model_path="/nonexistent/path")

    def test_basic_conversion(self, recommender):
        """Test basic feature vector conversion."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        vector = recommender._features_to_vector(features)

        assert isinstance(vector, np.ndarray)
        assert vector.shape == (1, 11)  # 11 features

    def test_language_encoding(self, recommender):
        """Test language is encoded correctly."""
        # Python = 0
        features_py = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        vector_py = recommender._features_to_vector(features_py)
        assert vector_py[0, 0] == 0  # Python

        # JavaScript = 1
        features_js = WorkloadFeatures(
            language=ProgrammingLanguage.JAVASCRIPT,
            workload_type=WorkloadType.API,
        )
        vector_js = recommender._features_to_vector(features_js)
        assert vector_js[0, 0] == 1  # JavaScript

    def test_workload_encoding(self, recommender):
        """Test workload type is encoded correctly."""
        # API = 0
        features_api = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        vector_api = recommender._features_to_vector(features_api)
        assert vector_api[0, 1] == 0  # API

        # Worker = 1
        features_worker = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.WORKER,
        )
        vector_worker = recommender._features_to_vector(features_worker)
        assert vector_worker[0, 1] == 1  # Worker

    def test_database_encoding(self, recommender):
        """Test database type is encoded correctly."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
        )
        vector = recommender._features_to_vector(features)
        assert vector[0, 2] == 1  # PostgreSQL

    def test_boolean_features(self, recommender):
        """Test boolean features are encoded as 0/1."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            needs_queue=True,
            needs_cache=True,
            needs_gpu=False,
        )
        vector = recommender._features_to_vector(features)

        assert vector[0, 3] == 1  # needs_database
        assert vector[0, 4] == 1  # needs_queue
        assert vector[0, 5] == 1  # needs_cache
        assert vector[0, 6] == 0  # needs_gpu

    def test_normalized_features(self, recommender):
        """Test numeric features are normalized."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            expected_rps=5000,  # Should normalize to 0.5
            expected_memory_mb=4096,  # Should normalize to 0.5
            team_size=50,  # Should normalize to 0.5
        )
        vector = recommender._features_to_vector(features)

        assert vector[0, 7] == pytest.approx(0.5, rel=0.01)  # RPS
        assert vector[0, 8] == pytest.approx(0.5, rel=0.01)  # Memory
        assert vector[0, 9] == pytest.approx(0.5, rel=0.01)  # Team size

    def test_normalized_capped_at_one(self, recommender):
        """Test normalized features cap at 1.0."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            expected_rps=20000,  # Above cap
            expected_memory_mb=16384,  # Above cap
            team_size=200,  # Above cap
        )
        vector = recommender._features_to_vector(features)

        assert vector[0, 7] == 1.0  # RPS capped
        assert vector[0, 8] == 1.0  # Memory capped
        assert vector[0, 9] == 1.0  # Team size capped


# =============================================================================
# Template Scoring Tests
# =============================================================================


class TestTemplateScoring:
    """Tests for _score_template method."""

    @pytest.fixture
    def recommender(self):
        """Create recommender instance for testing."""
        return TemplateRecommender(model_path="/nonexistent/path")

    def test_python_api_scores_microservice_python(self, recommender):
        """Test Python API workload scores high for microservice-python."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
            needs_cache=True,
        )
        score, reasons = recommender._score_template(TemplateType.MICROSERVICE_PYTHON, features)

        assert score >= 0.9  # Should be high
        assert "Python language matches" in reasons
        assert "API workload type" in reasons
        assert "PostgreSQL support included" in reasons

    def test_javascript_api_scores_microservice_node(self, recommender):
        """Test JavaScript API workload scores high for microservice-node."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.JAVASCRIPT,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.MONGODB,
            expected_rps=2000,
        )
        score, reasons = recommender._score_template(TemplateType.MICROSERVICE_NODE, features)

        assert score >= 0.9  # Should be high
        assert "JavaScript/TypeScript matches" in reasons
        assert "API workload type" in reasons
        assert "MongoDB support included" in reasons

    def test_worker_workload_scores_worker_service(self, recommender):
        """Test worker workload scores high for worker-service."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.WORKER,
            needs_queue=True,
            database_type=DatabaseType.REDIS,
        )
        score, reasons = recommender._score_template(TemplateType.WORKER_SERVICE, features)

        assert score >= 0.9  # Should be high
        assert "Worker/background job workload" in reasons
        assert "Queue processing support" in reasons

    def test_ml_pipeline_scores_ml_template(self, recommender):
        """Test ML pipeline workload scores high for ml-pipeline."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.ML_PIPELINE,
            needs_gpu=True,
        )
        score, reasons = recommender._score_template(TemplateType.ML_PIPELINE, features)

        assert score >= 0.9  # Should be high
        assert "ML pipeline workload type" in reasons
        assert "GPU support required" in reasons
        assert "Python ML ecosystem" in reasons

    def test_frontend_workload_scores_frontend_app(self, recommender):
        """Test frontend workload scores high for frontend-app."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.TYPESCRIPT,
            workload_type=WorkloadType.FRONTEND,
            needs_database=False,
        )
        score, reasons = recommender._score_template(TemplateType.FRONTEND_APP, features)

        assert score >= 0.9  # Should be high
        assert "Frontend workload type" in reasons
        assert "JavaScript/TypeScript frontend" in reasons

    def test_mismatched_features_low_score(self, recommender):
        """Test mismatched features result in low score."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,  # Frontend doesn't benefit from database
        )
        score, reasons = recommender._score_template(TemplateType.FRONTEND_APP, features)

        assert score < 0.3  # Should be low for frontend with database need


# =============================================================================
# Rule-Based Recommendation Tests
# =============================================================================


class TestRuleBasedRecommendation:
    """Tests for _rule_based_recommend method."""

    @pytest.fixture
    def recommender(self):
        """Create recommender instance for testing."""
        return TemplateRecommender(model_path="/nonexistent/path")

    def test_returns_sorted_list(self, recommender):
        """Test recommendations are returned sorted by score."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        recommendations = recommender._rule_based_recommend(features)

        assert len(recommendations) == 5  # All templates
        # Verify sorted descending
        scores = [r[1] for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_includes_reasons(self, recommender):
        """Test recommendations include reasons."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        recommendations = recommender._rule_based_recommend(features)

        # First recommendation should have reasons
        _, _, reasons = recommendations[0]
        assert isinstance(reasons, list)


# =============================================================================
# Main Recommendation Tests
# =============================================================================


class TestRecommendation:
    """Tests for recommend method (fallback mode)."""

    @pytest.fixture
    def recommender(self):
        """Create recommender without trained model (fallback mode)."""
        return TemplateRecommender(model_path="/nonexistent/path")

    def test_returns_recommendation_response(self, recommender):
        """Test recommend returns RecommendationResponse."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        assert isinstance(response, RecommendationResponse)
        assert response.primary is not None
        assert isinstance(response.alternatives, list)
        assert isinstance(response.input_summary, dict)

    def test_python_api_recommends_microservice_python(self, recommender):
        """Test Python API workload recommends microservice-python."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.MICROSERVICE_PYTHON

    def test_javascript_api_recommends_microservice_node(self, recommender):
        """Test JavaScript API workload recommends microservice-node."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.JAVASCRIPT,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.MONGODB,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.MICROSERVICE_NODE

    def test_worker_recommends_worker_service(self, recommender):
        """Test worker workload recommends worker-service."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.WORKER,
            needs_queue=True,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.WORKER_SERVICE

    def test_ml_pipeline_recommends_ml_template(self, recommender):
        """Test ML pipeline workload recommends ml-pipeline."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.ML_PIPELINE,
            needs_gpu=True,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.ML_PIPELINE

    def test_frontend_recommends_frontend_app(self, recommender):
        """Test frontend workload recommends frontend-app."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.TYPESCRIPT,
            workload_type=WorkloadType.FRONTEND,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.FRONTEND_APP

    def test_confidence_normalized(self, recommender):
        """Test confidence scores are normalized to [0, 1]."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        assert 0.0 <= response.primary.confidence <= 1.0
        for alt in response.alternatives:
            assert 0.0 <= alt.confidence <= 1.0

    def test_input_summary_included(self, recommender):
        """Test input summary is included in response."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            needs_gpu=False,
        )
        response = recommender.recommend(features)

        assert response.input_summary["language"] == "python"
        assert response.input_summary["workload_type"] == "api"
        assert response.input_summary["needs_database"] is True
        assert response.input_summary["needs_gpu"] is False

    def test_fallback_mode_indicator(self, recommender):
        """Test fallback mode is indicated in input summary."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        assert response.input_summary.get("mode") == "rule-based"


# =============================================================================
# Singleton Pattern Tests
# =============================================================================


class TestRecommenderSingleton:
    """Tests for get_recommender singleton pattern."""

    def test_returns_recommender_instance(self):
        """Test get_recommender returns TemplateRecommender."""
        recommender = get_recommender()
        assert isinstance(recommender, TemplateRecommender)

    def test_singleton_pattern(self):
        """Test get_recommender returns same instance."""
        recommender1 = get_recommender()
        recommender2 = get_recommender()
        assert recommender1 is recommender2


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def recommender(self):
        """Create recommender instance for testing."""
        return TemplateRecommender(model_path="/nonexistent/path")

    def test_all_defaults(self, recommender):
        """Test recommendation with all default values."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        assert response.primary is not None
        assert response.primary.template in list(TemplateType)

    def test_all_features_enabled(self, recommender):
        """Test recommendation with all features enabled."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
            needs_queue=True,
            needs_cache=True,
            needs_gpu=True,
            expected_rps=10000,
            expected_memory_mb=8192,
            team_size=100,
            compliance_required=True,
        )
        response = recommender.recommend(features)

        assert response.primary is not None

    def test_cron_workload(self, recommender):
        """Test cron workload gets worker-service recommendation."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.CRON,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.WORKER_SERVICE

    def test_batch_workload(self, recommender):
        """Test batch workload gets worker-service recommendation."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.BATCH,
        )
        response = recommender.recommend(features)

        assert response.primary.template == TemplateType.WORKER_SERVICE

    def test_go_language(self, recommender):
        """Test Go language with API workload."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.GO,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        # Should still return a valid recommendation
        assert response.primary is not None
        assert response.primary.template in list(TemplateType)

    def test_java_language(self, recommender):
        """Test Java language with API workload."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.JAVA,
            workload_type=WorkloadType.API,
        )
        response = recommender.recommend(features)

        # Should still return a valid recommendation
        assert response.primary is not None
        assert response.primary.template in list(TemplateType)

    def test_alternatives_filtered_by_score(self, recommender):
        """Test alternatives are filtered by minimum score threshold."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.ML_PIPELINE,
            needs_gpu=True,
        )
        response = recommender.recommend(features)

        # All alternatives should have >= 30% of max score
        for alt in response.alternatives:
            assert alt.confidence >= 0.3

    def test_reasons_are_populated(self, recommender):
        """Test recommendations have populated reasons."""
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            workload_type=WorkloadType.API,
            needs_database=True,
            database_type=DatabaseType.POSTGRESQL,
        )
        response = recommender.recommend(features)

        assert len(response.primary.reasons) > 0
