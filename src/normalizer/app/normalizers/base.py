from abc import ABC, abstractmethod

from app.schemas import NormalizedConfig


class ConfigNormalizer(ABC):
    """Base class for config normalizers."""

    @property
    @abstractmethod
    def source(self) -> str:
        """Source system identifier."""

    @abstractmethod
    def normalize(self, event: dict) -> NormalizedConfig | None:
        """Transform a raw event into a NormalizedConfig. Returns None if not applicable."""
