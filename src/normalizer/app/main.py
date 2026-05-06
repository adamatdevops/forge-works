import asyncio
import json
import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI
from prometheus_client import Counter

from app import store
from app.config import settings
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

# Normalizers
normalizers = [
    KubernetesNormalizer(),
    TerraformNormalizer(),
    GitHubActionsNormalizer(),
]


async def consume_loop():
    """Consume events from Kafka, normalize, store, and publish."""
    consumer = AIOKafkaConsumer(
        settings.kafka_input_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await consumer.start()
    await producer.start()

    logger.info("Normalizer consuming from %s", settings.kafka_input_topic)

    try:
        async for msg in consumer:
            try:
                event = msg.value
                source = event.get("source", "unknown")
                EVENTS_CONSUMED.labels(source=source).inc()
                logger.info("Consumed event: %s from %s", event.get("event_id", "?"), source)

                normalized = None
                for normalizer in normalizers:
                    if normalizer.source == source:
                        normalized = normalizer.normalize(event)
                        break

                if normalized is None:
                    EVENTS_SKIPPED.inc()
                    logger.info("Skipped event (no normalizer for source=%s)", source)
                    await consumer.commit()
                    continue

                # Store (Redis hot + S3 cold)
                await store.put(normalized)

                # Publish to Kafka
                await producer.send_and_wait(
                    settings.kafka_output_topic,
                    value=normalized.model_dump(),
                )

                CONFIGS_PRODUCED.labels(source=source, type=normalized.resource_type).inc()
                logger.info("Normalized: %s → %s (%s)",
                            source, normalized.resource_ref, normalized.resource_type)

                await consumer.commit()
            except Exception:
                logger.exception("Error processing message")
                await consumer.commit()  # Skip bad message
    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception:
        logger.exception("Consumer loop crashed")
    finally:
        await consumer.stop()
        await producer.stop()


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
