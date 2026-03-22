import json
import logging

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def start_producer() -> AIOKafkaProducer:
    """Initialize and start the Kafka producer."""
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        acks=settings.kafka_acks,
        retry_backoff_ms=500,
        request_timeout_ms=settings.kafka_request_timeout_ms,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    await _producer.start()
    logger.info("Kafka producer connected to %s", settings.kafka_bootstrap_servers)
    return _producer


async def stop_producer() -> None:
    """Stop the Kafka producer."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


async def publish(topic: str, value: dict, key: str | None = None) -> bool:
    """Publish a message to a Kafka topic. Returns True on success."""
    if not _producer:
        logger.error("Kafka producer not initialized")
        return False
    try:
        await _producer.send_and_wait(topic, value=value, key=key)
        return True
    except Exception:
        logger.exception("Failed to publish to topic %s", topic)
        return False


def is_connected() -> bool:
    """Check if the Kafka producer is connected."""
    return _producer is not None and not _producer._closed


async def get_cluster_metadata() -> dict:
    """Fetch Kafka cluster metadata: brokers, topics, controller."""
    if not _producer or _producer._closed:
        return {"connected": False}
    try:
        client = _producer.client
        await client.force_metadata_update()
        cluster = client.cluster
        brokers = [
            {"node_id": b.nodeId, "host": b.host, "port": b.port}
            for b in cluster.brokers()
        ]
        topics = list(cluster.topics())
        return {
            "connected": True,
            "controller_id": getattr(cluster.controller, "nodeId", None),
            "brokers": brokers,
            "broker_count": len(brokers),
            "topics": sorted(topics),
            "topic_count": len(topics),
        }
    except Exception:
        logger.exception("Failed to fetch cluster metadata")
        return {"connected": False, "error": "Failed to fetch metadata"}
