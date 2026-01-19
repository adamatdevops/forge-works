"""Webhook Router - Routes incoming webhooks to appropriate Forges.

The webhook router is the central entry point for all external tool webhooks.
It handles:
1. Signature validation
2. Event parsing
3. Routing to registered Forges
4. Error handling and logging

Architecture:
    External Tool (GitHub, ArgoCD, K8s)
           │
           ▼ POST /api/v1/webhooks/{source}
    ┌──────────────────┐
    │  Webhook Router  │
    │  ├─ validate     │
    │  ├─ parse        │
    │  └─ route        │
    └────────┬─────────┘
             │
    ┌────────┼────────┬────────┐
    ▼        ▼        ▼        ▼
  GitHub  ArgoCD    K8s     Custom
  Forge   Forge    Forge    Forges
"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.forges.base import ForgeAdapter, WebhookPayload

# Registry of Forges that handle webhooks
_forge_registry: dict[str, list[ForgeAdapter]] = {}


def register_forge(source: str, forge: ForgeAdapter) -> None:
    """Register a Forge to receive webhooks from a specific source.

    Args:
        source: The webhook source (github, argocd, kubernetes, etc.)
        forge: The Forge adapter to register
    """
    if source not in _forge_registry:
        _forge_registry[source] = []
    _forge_registry[source].append(forge)


def unregister_forge(source: str, forge: ForgeAdapter) -> None:
    """Unregister a Forge from receiving webhooks."""
    if source in _forge_registry and forge in _forge_registry[source]:
        _forge_registry[source].remove(forge)


def get_registered_forges(source: str) -> list[ForgeAdapter]:
    """Get all Forges registered for a source."""
    return _forge_registry.get(source, [])


def list_webhook_sources() -> list[str]:
    """List all sources that have registered Forges."""
    return list(_forge_registry.keys())


# =============================================================================
# Webhook Validation
# =============================================================================


def validate_github_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Validate GitHub webhook signature (HMAC-SHA256)."""
    if not signature.startswith("sha256="):
        return False

    expected = signature[7:]  # Remove "sha256=" prefix
    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, computed)


def validate_argocd_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Validate ArgoCD webhook signature."""
    # ArgoCD uses HMAC-SHA1 by default
    if signature.startswith("sha1="):
        expected = signature[5:]
        computed = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha1,
        ).hexdigest()
        return hmac.compare_digest(expected, computed)

    return False


def validate_kubernetes_token(token: str, expected_token: str) -> bool:
    """Validate Kubernetes webhook token (Bearer token)."""
    return hmac.compare_digest(token, expected_token)


# =============================================================================
# Webhook Parsers
# =============================================================================


def parse_github_event(request: Request, body: dict[str, Any]) -> WebhookPayload:
    """Parse a GitHub webhook into standardized payload."""
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    action = body.get("action", "")

    # Combine event type and action (e.g., "pull_request.opened")
    full_event_type = f"{event_type}.{action}" if action else event_type

    return WebhookPayload(
        source="github",
        event_type=full_event_type,
        timestamp=datetime.utcnow(),
        raw_payload=body,
        signature=request.headers.get("X-Hub-Signature-256"),
        headers=dict(request.headers),
    )


def parse_argocd_event(request: Request, body: dict[str, Any]) -> WebhookPayload:
    """Parse an ArgoCD webhook into standardized payload."""
    # ArgoCD webhooks have different event types
    event_type = body.get("type", "sync")

    return WebhookPayload(
        source="argocd",
        event_type=event_type,
        timestamp=datetime.utcnow(),
        raw_payload=body,
        signature=request.headers.get("X-Argocd-Signature"),
        headers=dict(request.headers),
    )


def parse_kubernetes_event(request: Request, body: dict[str, Any]) -> WebhookPayload:
    """Parse a Kubernetes webhook into standardized payload.

    Supports both:
    - ForgeWorks custom format: {"event_type": "deployment.available", "deployment": {...}}
    - K8s Admission Webhook format: {"kind": "AdmissionReview", "request": {...}}
    """
    # Check for ForgeWorks custom format first (simpler, used for testing/demos)
    if "event_type" in body:
        return WebhookPayload(
            source="kubernetes",
            event_type=body["event_type"],
            timestamp=datetime.utcnow(),
            raw_payload=body,
            signature=request.headers.get("Authorization"),
            headers=dict(request.headers),
        )

    # K8s admission webhooks have a specific structure
    kind = body.get("kind", "AdmissionReview")
    operation = body.get("request", {}).get("operation", "unknown")

    return WebhookPayload(
        source="kubernetes",
        event_type=f"{kind}.{operation}",
        timestamp=datetime.utcnow(),
        raw_payload=body,
        signature=request.headers.get("Authorization"),
        headers=dict(request.headers),
    )


# =============================================================================
# FastAPI Router
# =============================================================================

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(request: Request) -> dict[str, Any]:
    """Receive GitHub webhooks and route to registered Forges."""
    body_bytes = await request.body()
    body = json.loads(body_bytes)

    payload = parse_github_event(request, body)
    forges = get_registered_forges("github")

    if not forges:
        # No forges registered, but acknowledge receipt
        return {"status": "ok", "message": "No forges registered for github"}

    # Validate signature for each forge and dispatch
    processed = 0
    for forge in forges:
        try:
            # Validate if secret is configured
            if forge.config.webhook_secret:
                if not validate_github_signature(
                    body_bytes,
                    payload.signature or "",
                    forge.config.webhook_secret,
                ):
                    continue  # Skip this forge, invalid signature

            await forge.on_webhook(payload)
            processed += 1
        except Exception as e:
            # Log but don't fail - other forges may still process
            print(f"Error processing webhook in {forge.forge_name}: {e}")

    return {
        "status": "ok",
        "event_type": payload.event_type,
        "forges_processed": processed,
    }


@router.post("/argocd")
async def argocd_webhook(request: Request) -> dict[str, Any]:
    """Receive ArgoCD webhooks and route to registered Forges."""
    body_bytes = await request.body()
    body = json.loads(body_bytes)

    payload = parse_argocd_event(request, body)
    forges = get_registered_forges("argocd")

    if not forges:
        return {"status": "ok", "message": "No forges registered for argocd"}

    processed = 0
    for forge in forges:
        try:
            if forge.config.webhook_secret:
                if not validate_argocd_signature(
                    body_bytes,
                    payload.signature or "",
                    forge.config.webhook_secret,
                ):
                    continue

            await forge.on_webhook(payload)
            processed += 1
        except Exception as e:
            print(f"Error processing webhook in {forge.forge_name}: {e}")

    return {
        "status": "ok",
        "event_type": payload.event_type,
        "forges_processed": processed,
    }


@router.post("/kubernetes")
async def kubernetes_webhook(request: Request) -> dict[str, Any]:
    """Receive Kubernetes admission webhooks and route to registered Forges."""
    body_bytes = await request.body()
    body = json.loads(body_bytes)

    payload = parse_kubernetes_event(request, body)
    forges = get_registered_forges("kubernetes")

    if not forges:
        return {"status": "ok", "message": "No forges registered for kubernetes"}

    processed = 0
    for forge in forges:
        try:
            if forge.config.webhook_secret:
                auth_header = request.headers.get("Authorization", "")
                token = auth_header.replace("Bearer ", "")
                if not validate_kubernetes_token(token, forge.config.webhook_secret):
                    continue

            await forge.on_webhook(payload)
            processed += 1
        except Exception as e:
            print(f"Error processing webhook in {forge.forge_name}: {e}")

    return {
        "status": "ok",
        "event_type": payload.event_type,
        "forges_processed": processed,
    }


@router.post("/{source}")
async def generic_webhook(source: str, request: Request) -> dict[str, Any]:
    """Generic webhook endpoint for custom sources."""
    body_bytes = await request.body()
    body = json.loads(body_bytes)

    payload = WebhookPayload(
        source=source,
        event_type=body.get("event_type", body.get("type", "unknown")),
        timestamp=datetime.utcnow(),
        raw_payload=body,
        headers=dict(request.headers),
    )

    forges = get_registered_forges(source)

    if not forges:
        raise HTTPException(
            status_code=404,
            detail=f"No forges registered for source: {source}",
        )

    processed = 0
    for forge in forges:
        try:
            await forge.on_webhook(payload)
            processed += 1
        except Exception as e:
            print(f"Error processing webhook in {forge.forge_name}: {e}")

    return {
        "status": "ok",
        "source": source,
        "event_type": payload.event_type,
        "forges_processed": processed,
    }


@router.get("/")
async def list_webhooks() -> dict[str, Any]:
    """List all registered webhook sources and their forges."""
    return {
        "sources": {
            source: [f.forge_name for f in forges] for source, forges in _forge_registry.items()
        },
        "available_endpoints": [
            "/api/v1/webhooks/github",
            "/api/v1/webhooks/argocd",
            "/api/v1/webhooks/kubernetes",
            "/api/v1/webhooks/{custom_source}",
        ],
    }
