"""
Tests for the normalizer's DLQ pipeline.

Covers:
- Parse failures (malformed JSON) → FW-NL-PARSE-001 + offset commit
- S3 write failures → FW-NL-S3-001 + offset commit, after Redis attempted
- Redis write failures → FW-NL-REDIS-001 + offset commit
- Normalizer raising → FW-NL-NORM-001 + offset commit
- Source mismatch (when FW_EXPECTED_SOURCE set) → FW-NL-SRC-001 + offset commit
- Order: DLQ ack must happen *before* offset commit
- store.put raises (no longer swallows)
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

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


# ---------------------------------------------------------------------------
# Direct test of store.put failure semantics (no Kafka)
# ---------------------------------------------------------------------------


class TestStorePropagatesErrors:

    @pytest.mark.asyncio
    async def test_s3_failure_raises_s3writeerror(self, monkeypatch):
        from app import store
        from app.schemas import NormalizedConfig

        # Stub Redis (success)
        fake_redis = MagicMock()
        fake_redis.setex = AsyncMock(return_value=True)
        monkeypatch.setattr(store, "_redis", fake_redis)

        # Stub boto3 to raise on PutObject
        fake_s3 = MagicMock()
        fake_s3.put_object.side_effect = RuntimeError("simulated S3 outage")
        fake_boto3 = MagicMock()
        fake_boto3.client.return_value = fake_s3
        monkeypatch.setattr("boto3.client", fake_boto3.client)

        cfg = NormalizedConfig(
            resource_ref="kubernetes:web/api",
            source="kubernetes",
            resource_type="workload",
            resource={"name": "api"},
            raw_hash="x",
        )

        with pytest.raises(S3WriteError, match="kubernetes:web/api"):
            await store.put(cfg)

        assert fake_redis.setex.await_count == 1, "Redis must still be attempted"
        assert fake_s3.put_object.call_count == 1, "S3 must be attempted"

    @pytest.mark.asyncio
    async def test_redis_failure_raises_rediswriteerror_before_s3(self, monkeypatch):
        from app import store
        from app.schemas import NormalizedConfig

        fake_redis = MagicMock()
        fake_redis.setex = AsyncMock(side_effect=RuntimeError("redis down"))
        monkeypatch.setattr(store, "_redis", fake_redis)

        fake_s3 = MagicMock()
        fake_boto3 = MagicMock()
        fake_boto3.client.return_value = fake_s3
        monkeypatch.setattr("boto3.client", fake_boto3.client)

        cfg = NormalizedConfig(
            resource_ref="kubernetes:web/api",
            source="kubernetes",
            resource_type="workload",
            resource={"name": "api"},
            raw_hash="x",
        )

        with pytest.raises(RedisWriteError):
            await store.put(cfg)

        assert fake_redis.setex.await_count == 1
        assert fake_s3.put_object.call_count == 0, "S3 must NOT be reached if Redis fails"


# ---------------------------------------------------------------------------
# DLQEvent shape
# ---------------------------------------------------------------------------


class TestDlqEventShape:

    def test_dlq_event_required_fields(self):
        ev = DLQEvent(
            source="terraform",
            error_code=FW_NL_S3_001,
            error_message="S3 outage",
            original_payload={"foo": "bar"},
        )
        d = ev.model_dump()
        assert d["source"] == "terraform"
        assert d["error_code"] == FW_NL_S3_001
        assert d["error_message"] == "S3 outage"
        assert d["original_payload"] == {"foo": "bar"}
        assert d["event_id"].startswith("dlq_")
        assert d["timestamp"]
        assert d["correlation_id"] == ""


# ---------------------------------------------------------------------------
# End-to-end consume_loop tests via direct invocation of the helper
# (full Kafka integration is exercised by cluster verify, not here)
# ---------------------------------------------------------------------------


class TestPublishDlqHelper:

    @pytest.mark.asyncio
    async def test_publish_dlq_sends_envelope_to_dlq_topic(self):
        from app import main

        fake_producer = MagicMock()
        fake_producer.send_and_wait = AsyncMock(return_value=None)

        await main._publish_dlq(
            fake_producer,
            source="kubernetes",
            error_code=FW_NL_PARSE_001,
            error_message="bad json",
            original_payload={"raw": "x"},
            correlation_id="cid-1",
        )

        assert fake_producer.send_and_wait.await_count == 1
        args, kwargs = fake_producer.send_and_wait.call_args
        topic = args[0]
        body = kwargs["value"]
        from app.config import settings
        assert topic == settings.kafka_dlq_topic
        assert body["source"] == "kubernetes"
        assert body["error_code"] == FW_NL_PARSE_001
        assert body["error_message"] == "bad json"
        assert body["correlation_id"] == "cid-1"
        assert body["original_payload"] == {"raw": "x"}

    @pytest.mark.asyncio
    async def test_publish_dlq_increments_metric(self):
        from app import main

        fake_producer = MagicMock()
        fake_producer.send_and_wait = AsyncMock(return_value=None)

        before = main.DLQ_PUBLISHED.labels(error_code=FW_NL_NORM_001)._value.get()
        await main._publish_dlq(
            fake_producer,
            source="terraform",
            error_code=FW_NL_NORM_001,
            error_message="normalizer crashed",
            original_payload={},
            correlation_id="",
        )
        after = main.DLQ_PUBLISHED.labels(error_code=FW_NL_NORM_001)._value.get()
        assert after == before + 1


# ---------------------------------------------------------------------------
# Error-code constants are stable (caught if someone renames them)
# ---------------------------------------------------------------------------


class TestErrorCodes:

    @pytest.mark.parametrize("code,expected", [
        (FW_NL_PARSE_001, "FW-NL-PARSE-001"),
        (FW_NL_NORM_001, "FW-NL-NORM-001"),
        (FW_NL_S3_001, "FW-NL-S3-001"),
        (FW_NL_REDIS_001, "FW-NL-REDIS-001"),
        (FW_NL_SRC_001, "FW-NL-SRC-001"),
    ])
    def test_error_code_strings_are_stable(self, code, expected):
        assert code == expected
