"""
Adapter Registry — discovers, registers, and serves control plane adapters.
"""

import logging

from app.adapters.base import ControlPlaneAdapter

logger = logging.getLogger(__name__)

_adapters: dict[str, ControlPlaneAdapter] = {}
_default: str | None = None


def register(adapter: ControlPlaneAdapter) -> None:
    """Register an adapter."""
    _adapters[adapter.name] = adapter
    logger.info("Registered adapter: %s v%s", adapter.name, adapter.version)


def get(name: str) -> ControlPlaneAdapter | None:
    """Get adapter by name."""
    return _adapters.get(name)


def get_default() -> ControlPlaneAdapter | None:
    """Get default adapter."""
    if _default:
        return _adapters.get(_default)
    if _adapters:
        return next(iter(_adapters.values()))
    return None


def set_default(name: str) -> None:
    """Set default adapter."""
    global _default
    if name in _adapters:
        _default = name


def list_all() -> dict[str, str]:
    """List all registered adapters with versions."""
    return {name: adapter.version for name, adapter in _adapters.items()}
