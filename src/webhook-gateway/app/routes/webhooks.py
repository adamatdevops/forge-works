import json
import logging

from fastapi import APIRouter, Header, Request
from prometheus_client import Counter, Histogram
from starlette.responses import JSONResponse

from app import producer
from app.auth import (
    validate_argocd_signature,
    validate_github_signature,
    validate_kubernetes_token,
)
from app.config import settings
from app.schemas import DLQEvent, EventEnvelope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook")

# Prometheus metrics
WEBHOOKS_RECEIVED = Counter(
    "forgeworks_webhooks_received_total",
    "Total webhooks received",
    ["source", "type"],
)
WEBHOOKS_PROCESSED = Counter(
    "forgeworks_webhooks_processed_total",
    "Total webhooks successfully processed",
    ["source", "status"],
)
WEBHOOKS_FAILED = Counter(
    "forgeworks_webhooks_failed_total",
    "Total webhooks that failed",
    ["source", "error"],
)
KAFKA_PUBLISHED = Counter(
    "forgeworks_kafka_messages_published_total",
    "Total messages published to Kafka",
    ["topic"],
)
KAFKA_PUBLISH_LATENCY = Histogram(
    "forgeworks_kafka_publish_latency_seconds",
    "Kafka publish latency",
)


def _check_body_size(request: Request) -> JSONResponse | None:
    """Reject oversized payloads before reading the body."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_request_body_bytes:
                return JSONResponse(
                    {"error": "FW-IN-LIMIT-002", "message": "Payload too large"},
                    status_code=413,
                )
        except ValueError:
            return JSONResponse(
                {"error": "FW-IN-PARSE-001", "message": "Invalid Content-Length header"},
                status_code=400,
            )
    return None


async def _read_body_checked(request: Request) -> bytes | JSONResponse:
    """Read request body with post-read size validation (handles chunked transfer)."""
    raw_body = await request.body()
    if len(raw_body) > settings.max_request_body_bytes:
        return JSONResponse(
            {"error": "FW-IN-LIMIT-002", "message": "Payload too large"},
            status_code=413,
        )
    return raw_body


def _parse_github_event_type(headers: dict, body: dict) -> str:
    """Derive event type from GitHub webhook headers and payload."""
    event = headers.get("x-github-event", "unknown")
    action = body.get("action", "")
    return f"{event}.{action}" if action else event


def _parse_argocd_event_type(body: dict) -> str:
    """Derive event type from ArgoCD webhook payload."""
    return body.get("type", "unknown")


def _parse_kubernetes_event_type(body: dict) -> str:
    """Derive event type from Kubernetes admission/event payload."""
    kind = body.get("kind", "unknown").lower()
    reason = body.get("reason", "unknown").lower()
    return f"{kind}.{reason}"


async def _send_to_dlq(
    source: str,
    error_code: str,
    error_message: str,
    payload: dict,
    headers: dict,
    correlation_id: str,
) -> None:
    """Publish a failed event to the dead-letter queue."""
    dlq = DLQEvent(
        correlation_id=correlation_id,
        source=source,
        error_code=error_code,
        error_message=error_message,
        original_payload=payload,
        headers=headers,
    )
    await producer.publish(
        settings.kafka_topic_dlq,
        dlq.model_dump(),
        key=source,
    )


async def _process_webhook(
    source: str,
    event_type: str,
    body: dict,
    correlation_id: str,
    metadata: dict,
) -> JSONResponse:
    """Normalize event and publish to Kafka. DLQ on failure."""
    topic = settings.topic_for_source(source)
    if not topic:
        WEBHOOKS_FAILED.labels(source=source, error="unknown_source").inc()
        return JSONResponse(
            {"error": "FW-IN-PARSE-002", "message": f"Unknown source: {source}"},
            status_code=400,
        )

    envelope = EventEnvelope(
        correlation_id=correlation_id,
        source=source,
        type=event_type,
        metadata=metadata,
        payload=body,
    )

    with KAFKA_PUBLISH_LATENCY.time():
        ok = await producer.publish(topic, envelope.model_dump(), key=source)

    if ok:
        KAFKA_PUBLISHED.labels(topic=topic).inc()
        WEBHOOKS_PROCESSED.labels(source=source, status="success").inc()
        logger.info(
            "Published %s event %s to %s", source, envelope.event_id, topic
        )
        return JSONResponse(
            {"event_id": envelope.event_id, "status": "accepted"}, status_code=200
        )

    # Publish failed — send to DLQ
    WEBHOOKS_FAILED.labels(source=source, error="kafka_publish").inc()
    await _send_to_dlq(
        source=source,
        error_code="FW-KF-PROD-001",
        error_message="Failed to publish message to Kafka",
        payload=body,
        headers={"correlation_id": correlation_id},
        correlation_id=correlation_id,
    )
    return JSONResponse(
        {"error": "FW-KF-PROD-001", "message": "Failed to publish event"},
        status_code=502,
    )


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------


@router.post("/github")
async def webhook_github(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    """Receive GitHub webhook events."""
    size_error = _check_body_size(request)
    if size_error:
        return size_error
    result = await _read_body_checked(request)
    if isinstance(result, JSONResponse):
        return result
    raw_body = result
    correlation_id = getattr(request.state, "correlation_id", "")

    WEBHOOKS_RECEIVED.labels(source="github", type=x_github_event or "unknown").inc()

    # Signature validation (skip if no secret configured)
    if settings.github_webhook_secret:
        if not x_hub_signature_256 or not validate_github_signature(
            raw_body, x_hub_signature_256, settings.github_webhook_secret
        ):
            WEBHOOKS_FAILED.labels(source="github", error="auth").inc()
            return JSONResponse(
                {"error": "FW-IN-AUTH-002", "message": "Signature mismatch"},
                status_code=401,
            )

    try:
        body: dict = await request.json()
    except Exception:
        WEBHOOKS_FAILED.labels(source="github", error="parse").inc()
        return JSONResponse(
            {"error": "FW-IN-PARSE-001", "message": "Invalid JSON"}, status_code=400
        )

    headers_dict = dict(request.headers)
    event_type = _parse_github_event_type(headers_dict, body)
    metadata = {
        "repository": body.get("repository", {}).get("full_name", ""),
        "sender": body.get("sender", {}).get("login", ""),
    }

    # Route GitHub Actions events (workflow_run / workflow_job) to a separate
    # source so the per-source normalizer pod consumes them from its own topic.
    source = "github-actions" if x_github_event in ("workflow_run", "workflow_job") else "github"

    return await _process_webhook(source, event_type, body, correlation_id, metadata)


@router.post("/argocd")
async def webhook_argocd(
    request: Request,
    x_argocd_signature: str | None = Header(None),
):
    """Receive ArgoCD webhook events."""
    size_error = _check_body_size(request)
    if size_error:
        return size_error
    result = await _read_body_checked(request)
    if isinstance(result, JSONResponse):
        return result
    raw_body = result
    correlation_id = getattr(request.state, "correlation_id", "")

    WEBHOOKS_RECEIVED.labels(source="argocd", type="webhook").inc()

    if settings.argocd_webhook_secret:
        if not x_argocd_signature or not validate_argocd_signature(
            raw_body, x_argocd_signature, settings.argocd_webhook_secret
        ):
            WEBHOOKS_FAILED.labels(source="argocd", error="auth").inc()
            return JSONResponse(
                {"error": "FW-IN-AUTH-002", "message": "Signature mismatch"},
                status_code=401,
            )

    try:
        body: dict = await request.json()
    except Exception:
        WEBHOOKS_FAILED.labels(source="argocd", error="parse").inc()
        return JSONResponse(
            {"error": "FW-IN-PARSE-001", "message": "Invalid JSON"}, status_code=400
        )

    event_type = _parse_argocd_event_type(body)
    metadata = {
        "application": body.get("application", {}).get("metadata", {}).get("name", ""),
    }

    return await _process_webhook("argocd", event_type, body, correlation_id, metadata)


@router.post("/kubernetes")
async def webhook_kubernetes(
    request: Request,
    authorization: str | None = Header(None),
):
    """Receive Kubernetes admission/event webhooks."""
    size_error = _check_body_size(request)
    if size_error:
        return size_error
    result = await _read_body_checked(request)
    if isinstance(result, JSONResponse):
        return result
    raw_body = result
    correlation_id = getattr(request.state, "correlation_id", "")

    WEBHOOKS_RECEIVED.labels(source="kubernetes", type="webhook").inc()

    if settings.kubernetes_webhook_token:
        if not authorization or not validate_kubernetes_token(
            authorization, settings.kubernetes_webhook_token
        ):
            WEBHOOKS_FAILED.labels(source="kubernetes", error="auth").inc()
            return JSONResponse(
                {"error": "FW-IN-AUTH-001", "message": "Invalid token"},
                status_code=401,
            )

    try:
        body: dict = json.loads(raw_body)
    except Exception:
        WEBHOOKS_FAILED.labels(source="kubernetes", error="parse").inc()
        return JSONResponse(
            {"error": "FW-IN-PARSE-001", "message": "Invalid JSON"}, status_code=400
        )

    event_type = _parse_kubernetes_event_type(body)
    metadata = {
        "namespace": body.get("metadata", {}).get("namespace", ""),
        "name": body.get("metadata", {}).get("name", ""),
    }

    return await _process_webhook(
        "kubernetes", event_type, body, correlation_id, metadata
    )
