"""Event-loader protocol for the AB-028 metadata-window pass.

Real Terraform + DataDog adapters will implement `EventLoader` and drop in without
touching the pass logic. The synthetic loader is the reference implementation used by
tests and by CI runs pre-scoping-approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from forge_works.dr.ab028_spike.events import generate_stream

if TYPE_CHECKING:
    from datetime import datetime

    from forge_works.dr.ab028_spike.events import SyntheticEventStream


class EventLoader(Protocol):
    """Load events for a bounded time window. Contract-only — no state.

    Implementations MUST NOT emit events outside [start, end). The pass caller
    trusts the loader for its window bounds — the pass itself does no re-filtering.
    """

    def load(self, start: datetime, end: datetime) -> SyntheticEventStream: ...


@dataclass(frozen=True)
class SyntheticEventLoader:
    """Reference EventLoader — deterministic synthetic stream. Used by tests + CI.

    Ignores `start` / `end` params: the underlying generator produces a full 90-day
    window starting at a fixed anchor. The pass caller aligns its metadata / modeling
    windows within that.
    """

    seed: int = 20260728
    base_rate: float = 0.08
    deploys_per_day: float = 8.0
    modeling_days: int = 60
    metadata_days: int = 30

    def load(self, start: datetime, end: datetime) -> SyntheticEventStream:
        del start, end
        return generate_stream(
            modeling_days=self.modeling_days,
            metadata_days=self.metadata_days,
            seed=self.seed,
            base_rate=self.base_rate,
            deploys_per_day=self.deploys_per_day,
        )
