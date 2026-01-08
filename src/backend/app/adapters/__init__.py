"""External service adapters (GitHub, ArgoCD, Prometheus, K8s).

Adapters provide a consistent interface for integrating with external
services used by the IDP. Each adapter supports both mock and live modes:

- Mock mode: Returns realistic data for development and demos
- Live mode: Connects to actual external services

Usage:
    from app.adapters import get_github_adapter, get_argocd_adapter, AdapterMode

    # Get mock adapters (default)
    github = get_github_adapter()
    argocd = get_argocd_adapter()

    # Get live adapters with credentials
    github = get_github_adapter(mode=AdapterMode.LIVE, token="...")
    argocd = get_argocd_adapter(mode=AdapterMode.LIVE, server_url="...", token="...")
"""

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter
from app.adapters.github import (
    Branch,
    Commit,
    GitHubAdapter,
    PRState,
    PullRequest,
    Repository,
    WorkflowConclusion,
    WorkflowRun,
    WorkflowStatus,
    get_github_adapter,
)
from app.adapters.argocd import (
    Application,
    ApplicationSummary,
    ArgoCDAdapter,
    HealthStatus,
    OperationPhase,
    ResourceStatus,
    SyncOperation,
    SyncResult,
    SyncStatus,
    get_argocd_adapter,
)

__all__ = [
    # Base
    "AdapterHealth",
    "AdapterMode",
    "BaseAdapter",
    # GitHub
    "Branch",
    "Commit",
    "GitHubAdapter",
    "PRState",
    "PullRequest",
    "Repository",
    "WorkflowConclusion",
    "WorkflowRun",
    "WorkflowStatus",
    "get_github_adapter",
    # ArgoCD
    "Application",
    "ApplicationSummary",
    "ArgoCDAdapter",
    "HealthStatus",
    "OperationPhase",
    "ResourceStatus",
    "SyncOperation",
    "SyncResult",
    "SyncStatus",
    "get_argocd_adapter",
]
