"""Kubernetes API routes for cluster management and monitoring."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.adapters.kubernetes import (
    get_kubernetes_adapter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kubernetes", tags=["Kubernetes"])


@router.get("/cluster", response_model=dict)
async def get_cluster_info() -> dict:
    """Get Kubernetes cluster overview information.

    Returns cluster version, platform, and resource counts.
    """
    adapter = get_kubernetes_adapter()

    try:
        info = await adapter.get_cluster_info()
        return {
            **info.to_dict(),
            "adapter_mode": adapter.mode.value,
        }
    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/namespaces", response_model=list[dict])
async def list_namespaces() -> list[dict]:
    """List all namespaces in the Kubernetes cluster.

    Returns namespace details including pod and deployment counts.
    """
    adapter = get_kubernetes_adapter()

    try:
        namespaces = await adapter.list_namespaces()
        return [ns.to_dict() for ns in namespaces]
    except Exception as e:
        logger.error(f"Failed to list namespaces: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/nodes", response_model=list[dict])
async def list_nodes() -> list[dict]:
    """List all nodes in the Kubernetes cluster.

    Returns node status, capacity, and resource metrics.
    """
    adapter = get_kubernetes_adapter()

    try:
        nodes = await adapter.list_nodes()
        return [node.to_dict() for node in nodes]
    except Exception as e:
        logger.error(f"Failed to list nodes: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/deployments", response_model=list[dict])
async def list_deployments(
    namespace: Annotated[str | None, Query(description="Filter by namespace")] = None,
    label_selector: Annotated[
        str | None, Query(description="Label selector (e.g., app=forge-api)")
    ] = None,
) -> list[dict]:
    """List deployments in the cluster.

    Optionally filter by namespace or label selector.
    """
    adapter = get_kubernetes_adapter()

    try:
        deployments = await adapter.list_deployments(
            namespace=namespace,
            label_selector=label_selector,
        )
        return [dep.to_dict() for dep in deployments]
    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/deployments/{namespace}/{name}", response_model=dict)
async def get_deployment(namespace: str, name: str) -> dict:
    """Get a specific deployment by namespace and name.

    Returns detailed deployment status including replica counts and conditions.
    """
    adapter = get_kubernetes_adapter()

    try:
        deployment = await adapter.get_deployment(name=name, namespace=namespace)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {namespace}/{name} not found")
        return deployment.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment {namespace}/{name}: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/pods", response_model=list[dict])
async def list_pods(
    namespace: Annotated[str | None, Query(description="Filter by namespace")] = None,
    label_selector: Annotated[
        str | None, Query(description="Label selector (e.g., app=forge-api)")
    ] = None,
) -> list[dict]:
    """List pods in the cluster.

    Optionally filter by namespace or label selector.
    Returns pod status, container states, and resource metrics.
    """
    adapter = get_kubernetes_adapter()

    try:
        pods = await adapter.list_pods(
            namespace=namespace,
            label_selector=label_selector,
        )
        return [pod.to_dict() for pod in pods]
    except Exception as e:
        logger.error(f"Failed to list pods: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/pods/{namespace}/{name}/logs", response_model=dict)
async def get_pod_logs(
    namespace: str,
    name: str,
    container: Annotated[
        str | None, Query(description="Container name (required for multi-container pods)")
    ] = None,
    tail_lines: Annotated[int, Query(description="Number of lines to return", ge=1, le=1000)] = 100,
) -> dict:
    """Get logs from a specific pod.

    Returns the last N lines of logs from the pod's container.
    """
    adapter = get_kubernetes_adapter()

    try:
        logs = await adapter.get_pod_logs(
            name=name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
        )
        return {
            "namespace": namespace,
            "pod": name,
            "container": container,
            "lines": logs.split("\n") if logs else [],
            "line_count": len(logs.split("\n")) if logs else 0,
        }
    except Exception as e:
        logger.error(f"Failed to get logs for {namespace}/{name}: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_cluster_stats() -> dict:
    """Get aggregated cluster statistics.

    Returns counts and health status for nodes, namespaces, deployments, and pods.
    """
    adapter = get_kubernetes_adapter()

    try:
        cluster_info = await adapter.get_cluster_info()
        nodes = await adapter.list_nodes()
        deployments = await adapter.list_deployments()
        pods = await adapter.list_pods()

        # Calculate health stats
        healthy_nodes = sum(1 for n in nodes if n.status == "Ready")
        healthy_deployments = sum(
            1 for d in deployments if d.ready_replicas == d.replicas and d.unavailable_replicas == 0
        )
        running_pods = sum(1 for p in pods if p.phase.value == "Running")
        pending_pods = sum(1 for p in pods if p.phase.value == "Pending")
        failed_pods = sum(1 for p in pods if p.phase.value == "Failed")

        # Calculate total restarts
        total_restarts = sum(sum(c.restart_count for c in p.containers) for p in pods)

        return {
            "nodes": {
                "total": len(nodes),
                "healthy": healthy_nodes,
                "unhealthy": len(nodes) - healthy_nodes,
            },
            "namespaces": {
                "total": cluster_info.namespace_count,
            },
            "deployments": {
                "total": len(deployments),
                "healthy": healthy_deployments,
                "degraded": len(deployments) - healthy_deployments,
            },
            "pods": {
                "total": len(pods),
                "running": running_pods,
                "pending": pending_pods,
                "failed": failed_pods,
                "total_restarts": total_restarts,
            },
            "cluster_version": cluster_info.version,
            "adapter_mode": adapter.mode.value,
        }
    except Exception as e:
        logger.error(f"Failed to get cluster stats: {e}")
        raise HTTPException(status_code=503, detail=str(e))
