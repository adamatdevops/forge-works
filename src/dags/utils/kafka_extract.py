"""
Kafka data extraction utilities for Airflow tasks.

Extracts events from Kafka topics into JSON files on S3 for training.
Tracks watermarks (topic/partition/offset) per run for idempotent re-extraction.

Why watermarks matter:
- Without them, re-running the DAG re-extracts the same data → duplicate training rows
- Each run stores its high-watermark (last offset consumed per partition)
- Next run starts from the stored watermark → no duplicates, no gaps

NOTE: Heavy imports (kafka, boto3) are deferred to function calls to avoid
import errors during Airflow DAG processor scanning.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
S3_BUCKET = "fw-models-dev"


def extract_topic_to_s3(
    topic: str,
    s3_prefix: str,
    max_messages: int = 10000,
    timeout_ms: int = 10000,
) -> dict:
    """
    Extract messages from a Kafka topic and write to S3 as newline-delimited JSON.

    Returns metadata about the extraction (message count, offsets, S3 path).
    """
    from kafka import KafkaConsumer
    import boto3

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=timeout_ms,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id=f"airflow-extract-{topic}",
    )

    messages = []
    offsets = {}

    try:
        for msg in consumer:
            messages.append(msg.value)
            offsets[f"{msg.topic}-{msg.partition}"] = msg.offset

            if len(messages) >= max_messages:
                break

        # Commit offsets only after successful extraction
        consumer.commit()
    finally:
        consumer.close()

    if not messages:
        logger.info("No new messages in topic %s", topic)
        return {"count": 0, "s3_path": None, "offsets": offsets}

    # Write to S3 as newline-delimited JSON
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    s3_key = f"{s3_prefix}/{topic}/{timestamp}.jsonl"

    s3 = boto3.client("s3")
    body = "\n".join(json.dumps(m) for m in messages)
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=body.encode("utf-8"))

    logger.info("Extracted %d messages from %s → s3://%s/%s", len(messages), topic, S3_BUCKET, s3_key)

    return {
        "count": len(messages),
        "s3_path": f"s3://{S3_BUCKET}/{s3_key}",
        "offsets": offsets,
    }
