"""Base adapter interface for external service integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class AdapterMode(str, Enum):
    """Adapter operation mode."""

    MOCK = "mock"
    LIVE = "live"


@dataclass
class AdapterHealth:
    """Health status for an adapter."""

    name: str
    healthy: bool
    mode: AdapterMode
    latency_ms: float | None = None
    last_check: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "healthy": self.healthy,
            "mode": self.mode.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error": self.error,
        }


class BaseAdapter(ABC):
    """Abstract base class for external service adapters.

    All adapters support both mock and live modes to enable:
    - Local development without external dependencies
    - Integration testing with predictable responses
    - Production deployment with real API connections
    """

    def __init__(self, mode: AdapterMode = AdapterMode.MOCK) -> None:
        """Initialize adapter with specified mode."""
        self.mode = mode
        self._last_health_check: datetime | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the adapter name for identification."""
        ...

    @abstractmethod
    async def health_check(self) -> AdapterHealth:
        """Check adapter connectivity and health."""
        ...

    def is_mock(self) -> bool:
        """Check if adapter is running in mock mode."""
        return self.mode == AdapterMode.MOCK
