import asyncio
import json
import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI
from prometheus_client import Counter

from app import store
from app.config import settings
from app.dlq import (
    FW_NL_NORM_001,
    FW_NL_PARSE_001,
    FW_NL_REDIS_001,
    FW_NL_S3_001,
    FW_NL_SRC_001,
    DLQEvent,
    RedisWriteError,
    S3WriteError,
)
from app.normalizers.github_actions import GitHubActionsNormalizer
from app.normalizers.kubernetes import KubernetesNormalizer
from app.normalizers.terraform import TerraformNormalizer
from app.routes import health, query

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Metrics
EVENTS_CONSUMED = Counter("forgeworks_normalizer_events_consumed_total", "Events consumed", ["source"])
CONFIGS_PRODUCED = Counter("forgeworks_normalizer_configs_produced_total", "Configs produced", ["source", "type"])
EVENTS_SKIPPED = Counter("forgeworks_normalizer_events_skipped_total", "Events skipped (not normalizable)")
DLQ_PUBLISHED = Counter(
    "forgeworks_normalizer_dlq_published_total",
    "Events published to DLQ",
    ["error_code"],
)

# Normalizers
normalizers = [
    KubernetesNormalizer(),
    TerraformNormalizer(),
    GitHubActionsNormalizer(),
]


async def _publish_dlq(
    dlq_producer: AIOKafkaProducer,
    *,
    source: str,
    error_code: str,
    error_message: str,
    original_payload: dict,
    correlation_id: str,
) -> None:
    """Publish a DLQ envelope and increment the DLQ metric.

    Caller is responsible for committing the consumer offset *after* this returns
    successfully — never before.
    """
    envelope = DLQEvent(
        correlation_id=correlation_id,
        source=source,
        error_code=error_code,
        error_message=error_message,
        original_payload=original_payload,
    )
    await dlq_producer.send_and_wait(
        settings.kafka_dlq_topic,
        value=envelope.model_dump(),
    )
    DLQ_PUBLISHED.labels(error_code=error_code).inc()
    logger.warning(
        "DLQ published: source=%s code=%s msg=%s", source, error_code, error_message,
    )


async def process_message(
    raw_value: bytes,
    *,
    dlq_producer: AIOKafkaProducer,
    output_producer: AIOKafkaProducer,
) -> None:
    """Pipeline for a single Kafka message.

    Returns normally on success or DLQ-routed-failure (caller commits offset).
    Raises only when DLQ publish itself failed — caller must NOT commit and
    let Kafka redeliver on next poll.
    """
    event: dict = {}
    source = "unknown"
    correlation_id = ""

    # ---- 1. Decode --------------------------------------------------------
    try:
        event = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
        await _publish_dlq(
            dlq_producer,
            source="unknown",
            error_code=FW_NL_PARSE_001,
            error_message=f"JSON decode failed: {e}",
            original_payload={"raw_bytes_hex": raw_value.hex() if raw_value else ""},
            correlation_id="",
        )
        return

    source = event.get("source", "unknown")
    correlation_id = event.get("correlation_id", "")
    EVENTS_CONSUMED.labels(source=source).inc()
    logger.info("Consumed event: %s from %s", event.get("event_id", "?"), source)

    # ---- 2. Per-source isolation guard ------------------------------------
    if settings.expected_source and source != settings.expected_source:
        await _publish_dlq(
            dlq_producer,
            source=source,
            error_code=FW_NL_SRC_001,
            error_message=(
                f"Source mismatch: got {source!r}, expected "
                f"{settings.expected_source!r}"
            ),
            original_payload=event,
            correlation_id=correlation_id,
        )
        return

    # ---- 3. Normalize -----------------------------------------------------
    try:
        normalized = None
        for normalizer in normalizers:
            if normalizer.source == source:
                normalized = normalizer.normalize(event)
                break
    except Exception as e:
        await _publish_dlq(
            dlq_producer,
            source=source,
            error_code=FW_NL_NORM_001,
            error_message=f"Normalizer raised: {e}",
            original_payload=event,
            correlation_id=correlation_id,
        )
        return

    if normalized is None:
        EVENTS_SKIPPED.inc()
        logger.info("Skipped event (no normalizer for source=%s)", source)
        return

    # ---- 4. Store (Redis hot + S3 cold) -----------------------------------
    try:
        await store.put(normalized)
    except RedisWriteError as e:
        await _publish_dlq(
            dlq_producer,
            source=source,
            error_code=FW_NL_REDIS_001,
            error_message=str(e),
            original_payload=event,
            correlation_id=correlation_id,
        )
        return
    except S3WriteError as e:
        await _publish_dlq(
            dlq_producer,
            source=source,
            error_code=FW_NL_S3_001,
            error_message=str(e),
            original_payload=event,
            correlation_id=correlation_id,
        )
        return

    # ---- 5. Publish normalized config -------------------------------------
    await output_producer.send_and_wait(
        settings.kafka_output_topic,
        value=normalized.model_dump(exclude_none=True),
    )

    CONFIGS_PRODUCED.labels(source=source, type=normalized.resource_type).inc()
    logger.info(
        "Normalized: %s → %s (%s)",
        source, normalized.resource_ref, normalized.resource_type,
    )


async def consume_loop():
    """Consume events from Kafka. Any failure → structured DLQ, never silent loss."""
    consumer = AIOKafkaConsumer(
        settings.kafka_input_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        # Decode is intentionally manual so JSON parse failures route to DLQ
        # instead of crashing the consumer iterator.
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    dlq_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await consumer.start()
    await producer.start()
    await dlq_producer.start()

    logger.info(
        "Normalizer consuming from %s (expected_source=%r)",
        settings.kafka_input_topic, settings.expected_source or "<any>",
    )

    try:
        async for msg in consumer:
            try:
                await process_message(
                    msg.value, dlq_producer=dlq_producer, output_producer=producer,
                )
                await consumer.commit()
            except Exception:
                # process_message handles DLQ for known failures internally;
                # reaching this branch means DLQ publish itself failed. Do NOT
                # commit — let Kafka redeliver on the next poll.
                logger.exception("DLQ publish failed — message will be retried")
    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception:
        logger.exception("Consumer loop crashed")
    finally:
        await consumer.stop()
        await producer.stop()
        await dlq_producer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    await store.init_store()

    consume_task = asyncio.create_task(consume_loop())

    yield

    consume_task.cancel()
    await store.close_store()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(query.router)
