"""
Model training utilities.

Trains scikit-learn models on extracted features, validates quality,
and registers to MLflow.

Why scikit-learn (not deep learning):
- Our features are tabular (numeric columns per event window)
- Training data starts small (~hundreds of rows)
- Inference must be <50ms — sklearn models are sub-millisecond
- No GPU needed — runs on standard Airflow worker pods
- When data grows to millions of rows, we can switch to XGBoost/LightGBM
  (same scikit-learn API, same MLflow integration)
"""

import json
import json
import logging
import os

logger = logging.getLogger(__name__)

S3_BUCKET = "fw-models-dev"
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI", "http://mlflow.forge-ml.svc.cluster.local:5000"
)


def load_features_from_s3(s3_path: str) -> list[dict]:
    """Load feature vectors from S3."""
    import boto3
    s3 = boto3.client("s3")
    bucket = s3_path.split("/")[2]
    key = "/".join(s3_path.split("/")[3:])
    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return [json.loads(line) for line in body.strip().split("\n") if line]


def train_model(
    features_s3_path: str,
    model_name: str,
    experiment_name: str = "forgeworks-training",
) -> dict:
    """
    Train a GradientBoosting model on extracted features.

    Returns training metadata (metrics, model URI, run ID).
    """
    import mlflow
    import mlflow.sklearn
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    from sklearn.model_selection import train_test_split

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment_name)

    # Load features
    rows = load_features_from_s3(features_s3_path)
    if len(rows) < 10:
        logger.warning("Insufficient training data: %d rows (need 10+)", len(rows))
        return {"status": "skipped", "reason": "insufficient_data", "row_count": len(rows)}

    # Prepare training data
    feature_cols = [
        "event_count", "unique_types", "time_span_minutes", "unique_authors",
        "merge_count", "push_count", "sync_count", "crash_count", "test_count",
        "events_per_minute", "author_concentration",
    ]
    label_col = "has_alert"

    X = np.array([[row.get(col, 0) for col in feature_cols] for row in rows])
    y = np.array([row.get(label_col, 0) for row in rows])

    # Check label balance
    positive_ratio = y.sum() / len(y) if len(y) > 0 else 0
    if positive_ratio == 0 or positive_ratio == 1:
        logger.warning("All labels are the same (%s) — model won't learn", positive_ratio)
        return {"status": "skipped", "reason": "no_label_variance", "positive_ratio": positive_ratio}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with mlflow.start_run(run_name=f"{model_name}-{len(rows)}rows") as run:
        # Log parameters
        mlflow.log_param("model_type", "GradientBoostingClassifier")
        mlflow.log_param("feature_count", len(feature_cols))
        mlflow.log_param("training_rows", len(X_train))
        mlflow.log_param("test_rows", len(X_test))
        mlflow.log_param("positive_ratio", round(positive_ratio, 4))

        # Train
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
        }
        mlflow.log_metrics(metrics)

        # Log feature importance
        for col, importance in zip(feature_cols, model.feature_importances_):
            mlflow.log_metric(f"importance_{col}", round(importance, 4))

        # Log model
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name=model_name,
        )

        logger.info(
            "Model trained: %s — accuracy=%.3f, f1=%.3f, rows=%d",
            model_name, metrics["accuracy"], metrics["f1"], len(rows),
        )

        return {
            "status": "success",
            "run_id": run.info.run_id,
            "model_name": model_name,
            "model_uri": f"runs:/{run.info.run_id}/model",
            "metrics": metrics,
            "row_count": len(rows),
        }


def validate_model(training_result: dict, min_accuracy: float = 0.6) -> dict:
    """
    Validate a trained model against quality thresholds.

    Why 0.6 accuracy threshold (not 0.85):
    - Early training data is small and noisy
    - A model that's slightly better than random (0.5) is still useful
    - Threshold will increase as training data grows
    - We still have rule-based fallback for low-confidence predictions
    """
    if training_result.get("status") != "success":
        return {"passed": False, "reason": training_result.get("reason", "training_failed")}

    metrics = training_result.get("metrics", {})
    accuracy = metrics.get("accuracy", 0)

    if accuracy < min_accuracy:
        return {
            "passed": False,
            "reason": f"accuracy {accuracy:.3f} below threshold {min_accuracy}",
            "metrics": metrics,
        }

    return {
        "passed": True,
        "metrics": metrics,
        "model_uri": training_result.get("model_uri"),
        "model_name": training_result.get("model_name"),
    }
