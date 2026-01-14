"""ML components for template recommendation.

This module provides:
- Template recommendation based on workload features
- Training data generation for model improvement
- Model training and persistence utilities
"""

from app.ml.recommender import TemplateRecommender
from app.ml.training import generate_training_data, train_model

__all__ = [
    "TemplateRecommender",
    "generate_training_data",
    "train_model",
]
