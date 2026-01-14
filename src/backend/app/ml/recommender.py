"""Template recommendation engine.

Provides ML-based template recommendations based on workload features.
Supports both trained model inference and rule-based fallback.
"""

import pickle
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.schemas.ml import (
    RecommendationResponse,
    TemplateRecommendation,
    TemplateType,
    WorkloadFeatures,
)


class TemplateRecommender:
    """ML-powered template recommender.

    Uses a trained scikit-learn model when available,
    falls back to rule-based recommendations otherwise.
    """

    def __init__(self, model_path: str | None = None):
        """Initialize recommender.

        Args:
            model_path: Path to trained model file. Uses config default if None.
        """
        self.model_path = Path(model_path or settings.ml_model_path)
        self.model = None
        self.feature_names: list[str] = []
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model from disk if available."""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.model = data.get("model")
                    self.feature_names = data.get("feature_names", [])
            except Exception:
                # Fall back to rule-based if model load fails
                self.model = None

    def _features_to_vector(self, features: WorkloadFeatures) -> np.ndarray:
        """Convert WorkloadFeatures to numeric feature vector.

        Args:
            features: Input workload features

        Returns:
            Numpy array of numeric features
        """
        # Language encoding (one-hot style as numeric)
        lang_map = {
            "python": 0, "javascript": 1, "typescript": 2,
            "go": 3, "java": 4, "rust": 5,
        }
        lang_idx = lang_map.get(features.language.value, 0)

        # Workload type encoding
        workload_map = {
            "api": 0, "worker": 1, "cron": 2,
            "ml-pipeline": 3, "frontend": 4, "batch": 5,
        }
        workload_idx = workload_map.get(features.workload_type.value, 0)

        # Database type encoding
        db_map = {
            "none": 0, "postgresql": 1, "mongodb": 2,
            "redis": 3, "mysql": 4,
        }
        db_idx = db_map.get(features.database_type.value, 0)

        # Build feature vector
        vector = np.array([
            lang_idx,
            workload_idx,
            db_idx,
            1 if features.needs_database else 0,
            1 if features.needs_queue else 0,
            1 if features.needs_cache else 0,
            1 if features.needs_gpu else 0,
            min(features.expected_rps / 10000, 1.0),  # Normalize
            min(features.expected_memory_mb / 8192, 1.0),  # Normalize
            min(features.team_size / 100, 1.0),  # Normalize
            1 if features.compliance_required else 0,
        ])

        return vector.reshape(1, -1)

    def _rule_based_recommend(
        self, features: WorkloadFeatures
    ) -> list[tuple[TemplateType, float, list[str]]]:
        """Rule-based recommendation fallback.

        Args:
            features: Input workload features

        Returns:
            List of (template, confidence, reasons) tuples
        """
        scores: dict[TemplateType, tuple[float, list[str]]] = {}

        # Score each template based on rules
        for template in TemplateType:
            score, reasons = self._score_template(template, features)
            scores[template] = (score, reasons)

        # Sort by score descending
        sorted_templates = sorted(
            scores.items(),
            key=lambda x: x[1][0],
            reverse=True,
        )

        return [
            (template, score, reasons)
            for template, (score, reasons) in sorted_templates
        ]

    def _score_template(
        self, template: TemplateType, features: WorkloadFeatures
    ) -> tuple[float, list[str]]:
        """Score a template for given features.

        Args:
            template: Template to score
            features: Input features

        Returns:
            Tuple of (score, reasons)
        """
        score = 0.0
        reasons: list[str] = []

        if template == TemplateType.MICROSERVICE_PYTHON:
            if features.language.value == "python":
                score += 0.4
                reasons.append("Python language matches")
            if features.workload_type.value == "api":
                score += 0.3
                reasons.append("API workload type")
            if features.database_type.value == "postgresql":
                score += 0.2
                reasons.append("PostgreSQL support included")
            if features.needs_cache:
                score += 0.1
                reasons.append("Redis caching included")

        elif template == TemplateType.MICROSERVICE_NODE:
            if features.language.value in ("javascript", "typescript"):
                score += 0.4
                reasons.append("JavaScript/TypeScript matches")
            if features.workload_type.value == "api":
                score += 0.3
                reasons.append("API workload type")
            if features.database_type.value == "mongodb":
                score += 0.2
                reasons.append("MongoDB support included")
            if features.expected_rps > 1000:
                score += 0.1
                reasons.append("High throughput optimized")

        elif template == TemplateType.WORKER_SERVICE:
            if features.workload_type.value in ("worker", "cron", "batch"):
                score += 0.5
                reasons.append("Worker/background job workload")
            if features.needs_queue:
                score += 0.3
                reasons.append("Queue processing support")
            if not features.needs_database or features.database_type.value == "redis":
                score += 0.2
                reasons.append("Lightweight data storage")

        elif template == TemplateType.ML_PIPELINE:
            if features.workload_type.value == "ml-pipeline":
                score += 0.5
                reasons.append("ML pipeline workload type")
            if features.needs_gpu:
                score += 0.3
                reasons.append("GPU support required")
            if features.language.value == "python":
                score += 0.2
                reasons.append("Python ML ecosystem")

        elif template == TemplateType.FRONTEND_APP:
            if features.workload_type.value == "frontend":
                score += 0.5
                reasons.append("Frontend workload type")
            if features.language.value in ("javascript", "typescript"):
                score += 0.3
                reasons.append("JavaScript/TypeScript frontend")
            if not features.needs_database:
                score += 0.2
                reasons.append("Static/client-side focus")

        return score, reasons

    def recommend(self, features: WorkloadFeatures) -> RecommendationResponse:
        """Get template recommendation for workload features.

        Args:
            features: Input workload features

        Returns:
            RecommendationResponse with primary and alternative recommendations
        """
        if self.model is not None:
            return self._model_recommend(features)
        return self._fallback_recommend(features)

    def _model_recommend(self, features: WorkloadFeatures) -> RecommendationResponse:
        """Get recommendation using trained ML model.

        Args:
            features: Input workload features

        Returns:
            RecommendationResponse
        """
        vector = self._features_to_vector(features)

        # Get probability predictions
        probas = self.model.predict_proba(vector)[0]
        classes = self.model.classes_

        # Build recommendations from probabilities
        recommendations: list[tuple[TemplateType, float, list[str]]] = []
        for i, cls in enumerate(classes):
            template = TemplateType(cls)
            confidence = float(probas[i])
            _, reasons = self._score_template(template, features)
            recommendations.append((template, confidence, reasons))

        # Sort by confidence
        recommendations.sort(key=lambda x: x[1], reverse=True)

        # Build response
        primary = recommendations[0]
        alternatives = recommendations[1:4]  # Top 3 alternatives

        return RecommendationResponse(
            primary=TemplateRecommendation(
                template=primary[0],
                confidence=primary[1],
                reasons=primary[2],
            ),
            alternatives=[
                TemplateRecommendation(
                    template=t[0],
                    confidence=t[1],
                    reasons=t[2],
                )
                for t in alternatives
                if t[1] >= settings.ml_confidence_threshold * 0.3
            ],
            input_summary={
                "language": features.language.value,
                "workload_type": features.workload_type.value,
                "needs_database": features.needs_database,
                "needs_gpu": features.needs_gpu,
            },
        )

    def _fallback_recommend(self, features: WorkloadFeatures) -> RecommendationResponse:
        """Get recommendation using rule-based fallback.

        Args:
            features: Input workload features

        Returns:
            RecommendationResponse
        """
        recommendations = self._rule_based_recommend(features)

        # Normalize scores to [0, 1]
        max_score = max(r[1] for r in recommendations) if recommendations else 1.0
        if max_score == 0:
            max_score = 1.0

        normalized = [
            (r[0], r[1] / max_score, r[2])
            for r in recommendations
        ]

        primary = normalized[0]
        alternatives = [
            r for r in normalized[1:4]
            if r[1] >= 0.3  # At least 30% of max score
        ]

        return RecommendationResponse(
            primary=TemplateRecommendation(
                template=primary[0],
                confidence=primary[1],
                reasons=primary[2] if primary[2] else ["Best match based on rules"],
            ),
            alternatives=[
                TemplateRecommendation(
                    template=t[0],
                    confidence=t[1],
                    reasons=t[2] if t[2] else ["Alternative option"],
                )
                for t in alternatives
            ],
            input_summary={
                "language": features.language.value,
                "workload_type": features.workload_type.value,
                "needs_database": features.needs_database,
                "needs_gpu": features.needs_gpu,
                "mode": "rule-based",
            },
        )


# Global recommender instance (lazy loaded)
_recommender: TemplateRecommender | None = None


def get_recommender() -> TemplateRecommender:
    """Get or create the global recommender instance."""
    global _recommender
    if _recommender is None:
        _recommender = TemplateRecommender()
    return _recommender
