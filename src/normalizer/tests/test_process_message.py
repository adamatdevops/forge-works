"""
Tests for the per-message pipeline (`main.process_message`).

Covers all five DLQ paths plus happy paths:
- FW-NL-PARSE-001  malformed JSON
- FW-NL-SRC-001    source mismatch (FW_EXPECTED_SOURCE enforcement)
- FW-NL-NORM-001   normalizer raised
- FW-NL-REDIS-001  Redis write failed
- FW-NL-S3-001     S3 write failed

Also verifies:
- Empty FW_EXPECTED_SOURCE → no enforcement (backward compat)
- Matched source → no DLQ; output_producer is called
- Unknown source → not DLQ'd, just skipped (existing behavior)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.dlq import (
    FW_NL_NORM_001,
    FW_NL_PARSE_001,
    FW_NL_REDIS_001,
    FW_NL_S3_001,
    FW_NL_SRC_001,
    RedisWriteError,
    S3WriteError,
)


def _terraform_event() -> dict:
    return {
        "event_id": "evt_t1",
        "source": "terraform",
        "correlation_id": "cid-1",
        "payload": {
            "type": "aws_ecs_task_definition",
            "values": {"family": "fw-api", "cpu": 1024, "memory": 2048},
        },
    }


def _kubernetes_event() -> dict:
    return {
        "event_id": "evt_k1",
        "source": "kubernetes",
        "correlation_id": "cid-2",
        "payload": {
            "kind": "Deployment",
            "metadata": {"name": "api", "namespace": "web"},
            "spec": {"template": {"spec": {"containers": [{"image": "nginx"}]}}},
        },
    }


@pytest.fixture
def dlq_producer():
    p = MagicMock()
    p.send_and_wait = AsyncMock(return_value=None)
    return p


@pytest.fixture
def output_producer():
    p = MagicMock()
    p.send_and_wait = AsyncMock(return_value=None)
    return p


# ---------------------------------------------------------------------------
# FW-NL-PARSE-001 — malformed input
# ---------------------------------------------------------------------------


class TestParseFailure:

    @pytest.mark.asyncio
    async def test_invalid_json_routes_to_dlq(self, dlq_producer, output_producer):
        from app import main

        await main.process_message(
            b"this is not json",
            dlq_producer=dlq_producer,
            output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_PARSE_001
        assert body["source"] == "unknown"
        # Output producer must NOT be called for a parse failure
        assert output_producer.send_and_wait.await_count == 0

    @pytest.mark.asyncio
    async def test_invalid_utf8_routes_to_dlq(self, dlq_producer, output_producer):
        from app import main

        await main.process_message(
            b"\xff\xfe\x00\x00",  # invalid UTF-8
            dlq_producer=dlq_producer,
            output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_PARSE_001


# ---------------------------------------------------------------------------
# FW-NL-SRC-001 — source isolation guard
# ---------------------------------------------------------------------------


class TestSourceIsolation:

    @pytest.mark.asyncio
    async def test_matched_source_passes_through(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "terraform")
        # Stub store so the message reaches the publish step
        monkeypatch.setattr("app.main.store.put", AsyncMock(return_value=None))

        await main.process_message(
            json.dumps(_terraform_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 0, "matched source must NOT DLQ"
        assert output_producer.send_and_wait.await_count == 1

    @pytest.mark.asyncio
    async def test_mismatched_source_routes_to_dlq(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "terraform")
        monkeypatch.setattr("app.main.store.put", AsyncMock(return_value=None))

        # kubernetes event arriving at a terraform-pinned pod
        await main.process_message(
            json.dumps(_kubernetes_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_SRC_001
        assert body["source"] == "kubernetes"
        assert "terraform" in body["error_message"]
        # The mismatched message must NEVER be normalized + published
        assert output_producer.send_and_wait.await_count == 0

    @pytest.mark.asyncio
    async def test_empty_expected_source_disables_enforcement(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "")
        monkeypatch.setattr("app.main.store.put", AsyncMock(return_value=None))

        # kubernetes event accepted with no enforcement
        await main.process_message(
            json.dumps(_kubernetes_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 0
        assert output_producer.send_and_wait.await_count == 1


# ---------------------------------------------------------------------------
# FW-NL-NORM-001 — normalizer raises
# ---------------------------------------------------------------------------


class TestNormalizerRaises:

    @pytest.mark.asyncio
    async def test_normalizer_exception_routes_to_dlq(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "")

        # Replace the kubernetes normalizer with one that raises
        broken = MagicMock()
        broken.source = "kubernetes"
        broken.normalize.side_effect = RuntimeError("synthetic crash")
        monkeypatch.setattr(main, "normalizers", [broken])

        await main.process_message(
            json.dumps(_kubernetes_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_NORM_001
        assert "synthetic crash" in body["error_message"]
        assert output_producer.send_and_wait.await_count == 0


# ---------------------------------------------------------------------------
# FW-NL-S3-001 / FW-NL-REDIS-001 — store failures
# ---------------------------------------------------------------------------


class TestStoreFailures:

    @pytest.mark.asyncio
    async def test_s3_failure_routes_to_dlq(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "")
        monkeypatch.setattr(
            "app.main.store.put",
            AsyncMock(side_effect=S3WriteError("simulated")),
        )

        await main.process_message(
            json.dumps(_terraform_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_S3_001
        assert output_producer.send_and_wait.await_count == 0

    @pytest.mark.asyncio
    async def test_redis_failure_routes_to_dlq(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "")
        monkeypatch.setattr(
            "app.main.store.put",
            AsyncMock(side_effect=RedisWriteError("simulated")),
        )

        await main.process_message(
            json.dumps(_terraform_event()).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        assert dlq_producer.send_and_wait.await_count == 1
        body = dlq_producer.send_and_wait.call_args.kwargs["value"]
        assert body["error_code"] == FW_NL_REDIS_001
        assert output_producer.send_and_wait.await_count == 0


# ---------------------------------------------------------------------------
# Unknown source — passes through (no normalizer, no DLQ; existing semantic)
# ---------------------------------------------------------------------------


class TestUnknownSource:

    @pytest.mark.asyncio
    async def test_unknown_source_skipped_without_dlq(
        self, monkeypatch, dlq_producer, output_producer,
    ):
        from app import main

        monkeypatch.setattr(settings, "expected_source", "")
        monkeypatch.setattr("app.main.store.put", AsyncMock(return_value=None))

        await main.process_message(
            json.dumps({"source": "argocd", "payload": {}}).encode(),
            dlq_producer=dlq_producer, output_producer=output_producer,
        )
        # Unknown / unsupported source → skipped, not DLQ'd
        assert dlq_producer.send_and_wait.await_count == 0
        assert output_producer.send_and_wait.await_count == 0
