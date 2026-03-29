"""
ForgeWorks Model Training Pipeline DAG.

Schedule: Nightly at 02:00 UTC
Pipeline: Extract → Feature Engineering → Train → Validate → Register → Notify Flink

This DAG trains ML models that replace the static weighted scoring models
in the Pattern Matcher's Hot tier. The trained models learn from real
event patterns (forge.learning.outcomes) to score risks more accurately
than hand-tuned weights.

Data flow:
  Kafka (forge.learning.outcomes) → S3 (raw events)
  Kafka (forge.insights.realtime) → S3 (raw events)
  S3 (raw events) → Feature Engineering → S3 (feature vectors)
  S3 (features) → Model Training → MLflow (model registry)
  MLflow (new model) → Kafka (forge.mcp.updates) → Flink hot-reload
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task

TRAINING_S3_PREFIX = "training-data"
MODEL_NAME = "forgeworks-pattern-scorer"
EXPERIMENT_NAME = "forgeworks-training"


@dag(
    dag_id="model_training_pipeline",
    description="Nightly model training pipeline — extract, engineer, train, validate, deploy",
    schedule="0 2 * * *",  # 02:00 UTC daily
    start_date=datetime(2026, 3, 29),
    catchup=False,
    default_args={
        "owner": "forgeworks",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["ml", "training", "nightly"],
)
def model_training_pipeline():

    @task()
    def extract_learning_outcomes() -> dict:
        """Extract insight/alert data from Kafka for training labels."""
        from utils.kafka_extract import extract_topic_to_s3
        return extract_topic_to_s3(
            topic="forge.learning.outcomes",
            s3_prefix=TRAINING_S3_PREFIX,
            max_messages=10000,
        )

    @task()
    def extract_realtime_events() -> dict:
        """Extract raw events from Kafka for training features."""
        from utils.kafka_extract import extract_topic_to_s3
        return extract_topic_to_s3(
            topic="forge.insights.realtime",
            s3_prefix=TRAINING_S3_PREFIX,
            max_messages=50000,
        )

    @task()
    def engineer_features(outcomes_result: dict, events_result: dict) -> str:
        """Transform raw events + outcomes into feature vectors."""
        from utils.feature_engineering import (
            extract_features,
            load_events_from_s3,
            save_features_to_s3,
        )

        all_events = []

        if outcomes_result.get("s3_path"):
            outcomes = load_events_from_s3(outcomes_result["s3_path"])
            all_events.extend(outcomes)

        if events_result.get("s3_path"):
            events = load_events_from_s3(events_result["s3_path"])
            all_events.extend(events)

        if not all_events:
            return ""

        features = extract_features(all_events)
        return save_features_to_s3(features, TRAINING_S3_PREFIX)

    @task()
    def train_model(features_s3_path: str) -> dict:
        """Train a GradientBoosting model on extracted features."""
        if not features_s3_path:
            return {"status": "skipped", "reason": "no_features"}

        from utils.model_training import train_model as _train
        return _train(features_s3_path, MODEL_NAME, EXPERIMENT_NAME)

    @task()
    def validate_model(training_result: dict) -> dict:
        """Validate model quality against thresholds."""
        from utils.model_training import validate_model as _validate
        return _validate(training_result, min_accuracy=0.6)

    @task()
    def notify_flink(validation_result: dict, training_result: dict) -> bool:
        """Notify Flink to hot-reload the new model."""
        if not validation_result.get("passed"):
            return False

        from utils.flink_notify import notify_model_update
        return notify_model_update(
            model_name=training_result.get("model_name", MODEL_NAME),
            model_uri=training_result.get("model_uri", ""),
            metrics=training_result.get("metrics", {}),
            run_id=training_result.get("run_id", ""),
        )

    # DAG pipeline
    outcomes = extract_learning_outcomes()
    events = extract_realtime_events()
    features_path = engineer_features(outcomes, events)
    result = train_model(features_path)
    validation = validate_model(result)
    notify_flink(validation, result)


model_training_pipeline()
