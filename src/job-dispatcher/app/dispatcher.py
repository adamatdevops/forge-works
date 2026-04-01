"""
Job Dispatcher — consumes insights from Kafka and dispatches jobs via adapters.

Pipeline:
  forge.learning.outcomes (insights) → Dispatcher → Adapter → K8s Job
                                                                  ↓
  forge.jobs.results ← Result Collector ← K8s Job completion
  forge.learning.feedback ← Feedback loop

The dispatcher decides WHAT action to take based on the insight's pattern_id
and severity, then delegates HOW to the adapter.
"""

import asyncio
import json
import logging
import time

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from prometheus_client import Counter, Histogram

from app.adapters import registry
from app.config import settings
from app.schemas import Insight, JobResult, JobSpec, JobStatus

logger = logging.getLogger(__name__)

# Prometheus metrics
JOBS_DISPATCHED = Counter(
    "forgeworks_jobs_dispatched_total", "Total jobs dispatched", ["pattern_id", "adapter"]
)
JOBS_COMPLETED = Counter(
    "forgeworks_jobs_completed_total", "Total jobs completed", ["status", "adapter"]
)
JOBS_E2E_LATENCY = Histogram(
    "forgeworks_job_e2e_latency_seconds", "Job E2E latency (dispatch → result)",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
INSIGHTS_PROCESSED = Counter(
    "forgeworks_insights_processed_total", "Total insights consumed", ["pattern_id"]
)
FEEDBACK_PUBLISHED = Counter(
    "forgeworks_feedback_published_total", "Total feedback events published"
)

# Pattern → task type mapping
PATTERN_TASK_MAP = {
    "PAT-CI-001": {
        "task_type": "create-github-issue",
        "description": "Create GitHub issue for CI gap",
        "min_severity": "medium",
    },
    "PAT-DEPLOY-001": {
        "task_type": "send-slack-alert",
        "description": "Alert on rapid deployments",
        "min_severity": "high",
    },
    "PAT-K8S-001": {
        "task_type": "send-slack-alert",
        "description": "Alert on pod crash loop",
        "min_severity": "critical",
    },
}


class JobDispatcher:
    """Consumes insights from Kafka and dispatches jobs."""

    def __init__(self):
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None
        self._running = False

    async def start(self) -> None:
        """Initialize Kafka consumer/producer and connect adapters."""
        self._consumer = AIOKafkaConsumer(
            settings.kafka_input_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=False,  # Manual commit after processing
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._consumer.start()
        await self._producer.start()

        # Connect all registered adapters — fail startup if none connect
        connected = 0
        for name, adapter in registry._adapters.items():
            try:
                await adapter.connect()
                connected += 1
                logger.info("Adapter %s connected", name)
            except Exception:
                logger.exception("Failed to connect adapter %s", name)

        if connected == 0:
            raise RuntimeError("No adapters connected — cannot start dispatcher")

        self._running = True
        logger.info("Job Dispatcher started — consuming from %s", settings.kafka_input_topic)

    async def stop(self) -> None:
        """Shutdown consumer, producer, and adapters."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        for name, adapter in registry._adapters.items():
            await adapter.disconnect()
        logger.info("Job Dispatcher stopped")

    def is_healthy(self) -> dict:
        """Check dispatcher health: Kafka consumer/producer + running state."""
        consumer_ok = self._consumer is not None and not self._consumer._closed
        producer_ok = self._producer is not None and not self._producer._closed
        return {
            "running": self._running,
            "kafka_consumer": consumer_ok,
            "kafka_producer": producer_ok,
            "healthy": self._running and consumer_ok and producer_ok,
        }

    async def run(self) -> None:
        """Main dispatch loop — at-least-once with bounded concurrency.

        Commits offsets only after processing completes.
        On crash, uncommitted messages are redelivered (at-least-once).
        """
        async for msg in self._consumer:
            if not self._running:
                break

            try:
                insight = Insight(**msg.value)
                # Process and wait — ensures offset is only committed after completion
                await self._process_insight(insight)
                await self._consumer.commit()
            except Exception:
                logger.exception("Error processing insight (offset not committed): %s", msg.value)
                # Don't commit — message will be redelivered on restart

    async def _process_insight(self, insight: Insight) -> None:
        """Evaluate an insight and dispatch a job if actionable."""
        INSIGHTS_PROCESSED.labels(pattern_id=insight.pattern_id).inc()

        task_config = PATTERN_TASK_MAP.get(insight.pattern_id)
        if not task_config:
            logger.debug("No task mapping for pattern %s, skipping", insight.pattern_id)
            return

        # Enforce minimum severity
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_sev = severity_order.get(task_config.get("min_severity", "low"), 0)
        actual_sev = severity_order.get(insight.severity, 0)
        if actual_sev < min_sev:
            logger.debug(
                "Insight severity %s below threshold %s for %s, skipping",
                insight.severity, task_config["min_severity"], insight.pattern_id,
            )
            return

        # Build job spec
        spec = JobSpec(
            correlation_id=insight.trigger_event_ids[0] if insight.trigger_event_ids else "",
            insight_id=insight.insight_id,
            pattern_id=insight.pattern_id,
            pattern_name=insight.pattern_name,
            severity=insight.severity,
            group_key=insight.group_key,
            adapter=settings.default_adapter,
            task_type=task_config["task_type"],
            input_data={
                "severity": insight.severity,
                "message": insight.message,
                "group_key": insight.group_key,
                "recommendations": insight.recommendations,
                "model_score": insight.model_score,
            },
            labels={
                "pattern_id": insight.pattern_id,
                "source": insight.source,
            },
        )

        # Get adapter
        adapter = registry.get(spec.adapter) or registry.get_default()
        if not adapter:
            logger.error("No adapter available for %s", spec.adapter)
            return

        # Submit job
        try:
            native_id = await adapter.submit(spec)
            JOBS_DISPATCHED.labels(pattern_id=spec.pattern_id, adapter=adapter.name).inc()
            logger.info(
                "Job dispatched: %s → %s (pattern: %s, group: %s)",
                spec.job_id, native_id, spec.pattern_id, spec.group_key,
            )
        except Exception:
            logger.exception("Failed to submit job %s", spec.job_id)
            await self._publish_result(
                JobResult(
                    job_id=spec.job_id,
                    correlation_id=spec.correlation_id,
                    status=JobStatus.FAILED,
                    adapter=adapter.name,
                    error="Job submission failed",
                )
            )
            return

        # Wait for completion (async, with timeout)
        result = await self._wait_for_result(adapter, native_id, spec)
        await self._publish_result(result)
        await self._publish_feedback(insight, result)

    async def _wait_for_result(
        self, adapter, native_id: str, spec: JobSpec
    ) -> JobResult:
        """Poll for job completion."""
        start = time.monotonic()
        timeout = spec.timeout_seconds

        while True:
            status = await adapter.get_status(native_id)

            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                result = await adapter.get_result(native_id)
                result.duration_ms = int((time.monotonic() - start) * 1000)
                result.correlation_id = spec.correlation_id
                return result

            elapsed = time.monotonic() - start
            if elapsed > timeout:
                await adapter.cancel(native_id)
                return JobResult(
                    job_id=spec.job_id,
                    correlation_id=spec.correlation_id,
                    status=JobStatus.TIMEOUT,
                    adapter=adapter.name,
                    duration_ms=int(elapsed * 1000),
                    error=f"Timeout after {timeout}s",
                )

            await asyncio.sleep(5)

    async def _publish_result(self, result: JobResult) -> None:
        """Publish job result to Kafka."""
        await self._producer.send_and_wait(
            settings.kafka_results_topic,
            value=result.model_dump(),
        )
        JOBS_COMPLETED.labels(status=result.status.value, adapter=result.adapter).inc()
        JOBS_E2E_LATENCY.observe(result.duration_ms / 1000)
        logger.info("Result published: %s — %s (%dms)", result.job_id, result.status, result.duration_ms)

    async def _publish_feedback(self, insight: Insight, result: JobResult) -> None:
        """Publish feedback for ML training loop."""
        feedback = {
            "type": "job_outcome",
            "insight_id": insight.insight_id,
            "pattern_id": insight.pattern_id,
            "job_id": result.job_id,
            "job_status": result.status.value,
            "duration_ms": result.duration_ms,
            "model_score": insight.model_score,
            "group_key": insight.group_key,
        }
        await self._producer.send_and_wait(
            settings.kafka_feedback_topic,
            value=feedback,
        )
        FEEDBACK_PUBLISHED.inc()
