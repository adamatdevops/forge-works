"""ForgeWorks Forge System - Bidirectional Bridges Between DevOps Tools.

The Forge system is the core of ForgeWorks' philosophy:
- Tools can integrate, but they don't truly collaborate
- DevOps requires bidirectional feedback loops
- Forges fill the gaps that tools can't fill natively

A Forge:
1. Listens to external events (webhooks, watch APIs)
2. Reconciles state between ForgeWorks and external tools
3. Broadcasts changes to connected clients
4. Creates bridges between tools that couldn't communicate otherwise

Example: The GitHub ↔ Kubernetes Forge enables:
- Kubernetes to know build status from GitHub Actions
- GitHub to know deployment health from Kubernetes
- Automatic correlation between builds and deployments
"""

from app.forges.base import (
    ForgeAdapter,
    ForgeConfig,
    ForgeHealth,
    ForgeMode,
    ReconciliationStrategy,
    StateDiff,
    WebhookPayload,
)

__all__ = [
    "ForgeAdapter",
    "ForgeConfig",
    "ForgeHealth",
    "ForgeMode",
    "ReconciliationStrategy",
    "StateDiff",
    "WebhookPayload",
]
