"""Forge API routes - Expose bidirectional bridge functionality.

These routes provide:
1. Forge health and status monitoring
2. Correlation reports (the key value-add)
3. Manual forge triggering
4. Configuration management
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.forges.github_forge import get_github_forge
from app.forges.github_k8s_bridge import get_github_kubernetes_bridge
from app.forges.webhook_router import list_webhook_sources
from app.forges.webhook_router import router as webhook_router

router = APIRouter()


# =============================================================================
# Forge Status & Health
# =============================================================================


@router.get("/")
async def list_forges() -> dict[str, Any]:
    """List all available forges and their status."""
    github_forge = get_github_forge()
    bridge = get_github_kubernetes_bridge()

    return {
        "forges": [
            {
                "name": github_forge.forge_name,
                "type": "source",
                "description": "Bidirectional bridge to GitHub",
                "webhook_events": github_forge.supported_webhook_events,
                "status": "active" if not github_forge.is_mock() else "mock",
            },
            {
                "name": bridge.forge_name,
                "type": "bridge",
                "description": "Connects GitHub builds to Kubernetes deployments",
                "webhook_events": bridge.supported_webhook_events,
                "status": "active" if not bridge.is_mock() else "mock",
            },
        ],
        "webhook_sources": list_webhook_sources(),
    }


@router.get("/health")
async def forge_health() -> dict[str, Any]:
    """Get health status of all forges."""
    github_forge = get_github_forge()
    bridge = get_github_kubernetes_bridge()

    github_health = await github_forge.health_check()
    bridge_health = await bridge.health_check()

    return {
        "overall_status": "healthy"
        if github_health.healthy and bridge_health.healthy
        else "degraded",
        "forges": {
            github_forge.forge_name: github_health.to_dict(),
            bridge.forge_name: bridge_health.to_dict(),
        },
    }


# =============================================================================
# GitHub Forge
# =============================================================================


@router.get("/github/status")
async def github_forge_status() -> dict[str, Any]:
    """Get GitHub Forge status and cached data."""
    forge = get_github_forge()
    state = await forge.fetch_external_state()

    return {
        "forge": forge.forge_name,
        "mode": "mock" if forge.is_mock() else "live",
        "pull_requests_cached": len(state.get("pull_requests", {})),
        "workflows_cached": len(state.get("workflows", {})),
        "repos_monitored": state.get("repos", []),
    }


@router.post("/github/register-service")
async def register_github_service(
    service_id: str,
    repo_name: str,
) -> dict[str, Any]:
    """Register a ForgeWorks service to track a GitHub repository."""
    forge = get_github_forge()
    forge.register_service_repo(service_id, repo_name)

    return {
        "status": "registered",
        "service_id": service_id,
        "repo_name": repo_name,
        "message": f"Service {service_id} will now track GitHub events from {repo_name}",
    }


# =============================================================================
# GitHub ↔ Kubernetes Bridge (THE KEY VALUE)
# =============================================================================


@router.get("/bridge/correlations")
async def get_all_correlations() -> dict[str, Any]:
    """Get all build-to-deployment correlations.

    This is THE KEY ENDPOINT that provides the value Kubernetes can't
    generate on its own: a complete picture of build→deploy→health.
    """
    bridge = get_github_kubernetes_bridge()
    correlations = bridge.get_all_correlations()

    return {
        "total": len(correlations),
        "correlations": correlations,
    }


@router.get("/bridge/correlations/active")
async def get_active_correlations() -> dict[str, Any]:
    """Get correlations that are still in progress."""
    bridge = get_github_kubernetes_bridge()
    correlations = bridge.get_active_correlations()

    return {
        "active_count": len(correlations),
        "correlations": correlations,
    }


@router.get("/bridge/correlation/{correlation_id}")
async def get_correlation(correlation_id: str) -> dict[str, Any]:
    """Get a specific correlation by ID.

    Returns the complete build→deploy→health report.
    """
    bridge = get_github_kubernetes_bridge()
    correlation = bridge.get_correlation(correlation_id)

    if not correlation:
        raise HTTPException(
            status_code=404,
            detail=f"Correlation {correlation_id} not found",
        )

    return correlation.to_report()


@router.post("/bridge/register-mapping")
async def register_repo_deployment_mapping(
    repo_name: str,
    deployment_name: str,
    namespace: str = "default",
) -> dict[str, Any]:
    """Register a mapping between a GitHub repo and Kubernetes deployment.

    This is the configuration that enables the bridge to correlate
    builds with deployments.
    """
    bridge = get_github_kubernetes_bridge()
    bridge.register_repo_deployment_mapping(repo_name, deployment_name, namespace)

    return {
        "status": "registered",
        "mapping": {
            "repo": repo_name,
            "deployment": deployment_name,
            "namespace": namespace,
        },
        "message": f"Repo {repo_name} → Deployment {namespace}/{deployment_name}",
    }


@router.get("/bridge/mappings")
async def get_repo_deployment_mappings() -> dict[str, Any]:
    """Get all configured repo→deployment mappings."""
    bridge = get_github_kubernetes_bridge()
    state = await bridge.fetch_external_state()

    return {
        "mappings": state.get("mappings", {}),
    }


# =============================================================================
# Manual Forge Triggers (for testing/demos)
# =============================================================================


@router.post("/github/simulate")
async def simulate_github_events() -> dict[str, Any]:
    """Manually trigger mock GitHub events.

    Useful for demos and testing the bridge without real GitHub webhooks.
    """
    forge = get_github_forge()

    if not forge.is_mock():
        raise HTTPException(
            status_code=400,
            detail="Simulation only available in mock mode",
        )

    events = await forge.generate_mock_events()
    for event in events:
        await forge.on_webhook(event)

    return {
        "status": "simulated",
        "events_generated": len(events),
        "event_types": [e.event_type for e in events],
    }


@router.post("/bridge/simulate")
async def simulate_bridge_events() -> dict[str, Any]:
    """Manually trigger mock bridge events (build→deploy cycle).

    Useful for demos and testing the complete correlation flow.
    """
    bridge = get_github_kubernetes_bridge()

    if not bridge.is_mock():
        raise HTTPException(
            status_code=400,
            detail="Simulation only available in mock mode",
        )

    events = await bridge.generate_mock_events()
    for event in events:
        await bridge.on_webhook(event)

    return {
        "status": "simulated",
        "events_generated": len(events),
        "event_types": [e.event_type for e in events],
        "correlations_active": len(bridge.get_active_correlations()),
    }


@router.post("/reconcile")
async def trigger_reconciliation() -> dict[str, Any]:
    """Manually trigger state reconciliation for all forges."""
    github_forge = get_github_forge()
    bridge = get_github_kubernetes_bridge()

    github_diffs = await github_forge.reconcile()
    bridge_diffs = await bridge.reconcile()

    return {
        "status": "reconciled",
        "github_forge": {
            "diffs_found": len(github_diffs),
            "diffs_with_drift": len([d for d in github_diffs if d.has_drift]),
        },
        "bridge": {
            "diffs_found": len(bridge_diffs),
            "diffs_with_drift": len([d for d in bridge_diffs if d.has_drift]),
        },
    }


# Include the webhook router for receiving external events
# webhook_router already has prefix="/webhooks" so we don't add it again
router.include_router(webhook_router)
