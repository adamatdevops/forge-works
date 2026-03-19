from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app import producer
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe — always returns healthy if the process is running."""
    return {"status": "healthy"}


@router.get("/ready")
async def ready():
    """Readiness probe — checks Kafka producer connectivity."""
    kafka_ok = producer.is_connected()
    if not kafka_ok:
        return Response(
            content='{"status":"not_ready","kafka":"disconnected"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ready", "kafka": "connected"}


@router.get("/status")
async def status():
    """Kafka cluster health — brokers, topics, connectivity."""
    metadata = await producer.get_cluster_metadata()
    if not metadata.get("connected"):
        import json
        return Response(
            content=json.dumps({"status": "unhealthy", "kafka": metadata}),
            status_code=503,
            media_type="application/json",
        )

    expected_topics = {
        settings.kafka_topic_github,
        settings.kafka_topic_argocd,
        settings.kafka_topic_kubernetes,
        settings.kafka_topic_dlq,
    }
    available_topics = set(metadata.get("topics", []))
    missing_topics = sorted(expected_topics - available_topics)

    return {
        "status": "healthy" if not missing_topics else "degraded",
        "kafka": {
            "cluster_id": metadata.get("cluster_id"),
            "controller_id": metadata.get("controller_id"),
            "brokers": metadata.get("brokers"),
            "broker_count": metadata.get("broker_count"),
            "topic_count": metadata.get("topic_count"),
            "topics": metadata.get("topics"),
            "missing_topics": missing_topics or None,
        },
    }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
