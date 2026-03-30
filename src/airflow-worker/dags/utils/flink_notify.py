"""
Flink hot-reload notification.

After a new model is trained, validated, and registered in MLflow,
this module publishes a notification to Kafka (forge.mcp.updates)
so Flink's Pattern Matcher can reload the model from the registry.

Why Kafka notification (not direct Flink API):
- Decoupled — Airflow doesn't need to know Flink's REST URL
- Durable — if Flink is restarting, the message waits in Kafka
- Auditable — every model update is a Kafka event
- Extensible — other consumers can react to model updates too
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
NOTIFY_TOPIC = "forge.mcp.updates"


def notify_model_update(
    model_name: str,
    model_uri: str,
    metrics: dict,
    run_id: str,
) -> bool:
    """
    Publish a model update notification to Kafka.

    The Pattern Matcher's ModelLoader (Phase 2) will consume this
    and hot-swap the model in the Hot tier.
    """
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    message = {
        "type": "model_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": model_name,
        "model_uri": model_uri,
        "run_id": run_id,
        "metrics": metrics,
        "action": "reload",
    }

    try:
        future = producer.send(NOTIFY_TOPIC, value=message)
        future.get(timeout=10)
        logger.info("Flink notified of model update: %s → %s", model_name, model_uri)
        return True
    except Exception:
        logger.exception("Failed to notify Flink of model update")
        return False
    finally:
        producer.close()
