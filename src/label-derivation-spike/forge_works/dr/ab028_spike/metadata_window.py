"""AB-028 pre-scoping metadata-window pass (RFC §A3 + §4.4).

Inspects the 30-day metadata window ONLY for aggregate counts — volume, base rate,
censoring rate, missing-data rate. **The modeling window is not touched.** Output
feeds the scoping-approval meeting's threshold-lock discussion.

Also produces a prospective power-analysis projection: given the metadata-window base
rate, extrapolate to the 60-day modeling window and check the per-split positive floors
(train=50, val=15, test=30 per RFC §4.4 v0.2 proposals). If the projection fails any
floor, the meeting knows to escalate before locking §B1-§B3 rather than after training.

Every threshold in the report is a **proposal** carried in `MetadataPassConfig`. The
scoping-approval meeting locks the real numbers by constructing a config at run time.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.adapters import EventLoader
    from forge_works.dr.ab028_spike.events import SyntheticEventStream


MUTED_STATES = frozenset({"muted", "unknown"})
HORIZON_MINUTES = 60
DEFAULT_TRAIN_FRACTION = 0.70
DEFAULT_VAL_FRACTION = 0.15
DEFAULT_TEST_FRACTION = 0.15


@dataclass(frozen=True)
class MetadataPassConfig:
    """Threshold config for the metadata pass. Placeholders match RFC §4.4 v0.2 proposals."""

    metadata_days: int = 30
    modeling_days: int = 60
    base_rate_lower: float = 0.01
    base_rate_upper: float = 0.20
    train_positive_floor: int = 50
    val_positive_floor: int = 15
    test_positive_floor: int = 30
    train_fraction: float = DEFAULT_TRAIN_FRACTION
    val_fraction: float = DEFAULT_VAL_FRACTION
    test_fraction: float = DEFAULT_TEST_FRACTION
    eligibility_yield_estimate: float | None = None


@dataclass(frozen=True)
class ProjectedModelingWindow:
    """Prospective projection: what would the modeling window look like at these rates?"""

    modeling_days: int
    projected_deploys: int
    projected_eligible: int
    projected_positives: int
    projected_train_positives: int
    projected_val_positives: int
    projected_test_positives: int
    train_floor_met: bool
    val_floor_met: bool
    test_floor_met: bool

    @property
    def all_floors_met(self) -> bool:
        return self.train_floor_met and self.val_floor_met and self.test_floor_met


@dataclass(frozen=True)
class MetadataPass:
    """Aggregate-only pre-scoping window report — no label / feature values inspected."""

    metadata_window_start: datetime
    metadata_window_end: datetime
    metadata_days: int

    deploys: int
    slo_breaches: int
    apply_failures: int
    incidents: int
    monitor_muted_events: int

    deploys_per_day: float
    base_rate: float
    censoring_rate: float
    missing_data_rate: float
    eligibility_rate: float

    projected_modeling_window: ProjectedModelingWindow

    base_rate_in_bounds: bool
    warnings: list[str] = field(default_factory=list)

    @property
    def ready_for_scoping_approval(self) -> bool:
        return (
            self.base_rate_in_bounds
            and self.projected_modeling_window.all_floors_met
            and not self.warnings
        )


def run_metadata_pass(
    stream: SyntheticEventStream,
    *,
    config: MetadataPassConfig | None = None,
) -> MetadataPass:
    """Run the pre-scoping metadata pass on the metadata portion of `stream`.

    Assumes the stream's first `config.metadata_days` days ARE the metadata window
    (matches `generate_stream(metadata_days=..., modeling_days=...)` layout). The
    remaining days are the modeling window — untouched here.
    """
    config = config or MetadataPassConfig()
    md_start = stream.start
    md_end = md_start + timedelta(days=config.metadata_days)
    return _compute(stream, md_start, md_end, config)


def run_metadata_pass_via_loader(
    loader: EventLoader,
    *,
    anchor: datetime,
    config: MetadataPassConfig | None = None,
) -> MetadataPass:
    """Adapter-facing entry point — real Terraform + DataDog loader drops in here."""
    config = config or MetadataPassConfig()
    md_start = anchor - timedelta(days=config.metadata_days)
    md_end = anchor
    stream = loader.load(md_start, md_end)
    return _compute(stream, md_start, md_end, config)


def _compute(
    stream: SyntheticEventStream,
    md_start: datetime,
    md_end: datetime,
    config: MetadataPassConfig,
) -> MetadataPass:
    days = max((md_end - md_start).days, 1)
    deploys = [d for d in stream.deploys if md_start <= d.deployed_at < md_end]
    breaches = [b for b in stream.slo_breaches if md_start <= b.event_time < md_end]
    apply_failures = [a for a in stream.apply_failures if md_start <= a.event_time < md_end]
    incidents = [i for i in stream.incidents if md_start <= i.event_time < md_end]
    muted_events = [
        m
        for m in stream.monitor_events
        if md_start <= m.event_time < md_end and m.state in MUTED_STATES
    ]

    n_deploys = len(deploys)
    n_breaches = len(breaches)
    censoring, missing = _count_eligibility_shapes(deploys, stream)

    base_rate = _rate(n_breaches, n_deploys)
    censoring_rate = _rate(censoring, n_deploys)
    missing_data_rate = _rate(missing, n_deploys)
    eligibility_rate = max(0.0, 1.0 - censoring_rate - missing_data_rate)
    deploys_per_day = n_deploys / days

    projection = _project_modeling_window(
        deploys_per_day=deploys_per_day,
        base_rate=base_rate,
        eligibility_rate=(
            config.eligibility_yield_estimate
            if config.eligibility_yield_estimate is not None
            else eligibility_rate
        ),
        config=config,
    )
    base_rate_in_bounds = config.base_rate_lower <= base_rate <= config.base_rate_upper
    warnings = _generate_warnings(
        base_rate=base_rate,
        base_rate_in_bounds=base_rate_in_bounds,
        projection=projection,
        eligibility_rate=eligibility_rate,
        missing_data_rate=missing_data_rate,
        config=config,
    )

    return MetadataPass(
        metadata_window_start=md_start,
        metadata_window_end=md_end,
        metadata_days=days,
        deploys=n_deploys,
        slo_breaches=n_breaches,
        apply_failures=len(apply_failures),
        incidents=len(incidents),
        monitor_muted_events=len(muted_events),
        deploys_per_day=deploys_per_day,
        base_rate=base_rate,
        censoring_rate=censoring_rate,
        missing_data_rate=missing_data_rate,
        eligibility_rate=eligibility_rate,
        projected_modeling_window=projection,
        base_rate_in_bounds=base_rate_in_bounds,
        warnings=warnings,
    )


def _count_eligibility_shapes(deploys: list, stream: SyntheticEventStream) -> tuple[int, int]:
    censoring = 0
    missing = 0
    for i, deploy in enumerate(deploys):
        window_end = deploy.deployed_at + timedelta(minutes=HORIZON_MINUTES)
        next_time = deploys[i + 1].deployed_at if i + 1 < len(deploys) else None
        if next_time is not None and next_time < window_end:
            censoring += 1
        elif _muted_during(stream.monitor_events, deploy.deployed_at, window_end):
            missing += 1
    return censoring, missing


def _muted_during(monitor_events: list, start: datetime, end: datetime) -> bool:
    state = "ok"
    for event in monitor_events:
        if event.event_time >= end:
            break
        if event.event_time <= start:
            state = event.state
        elif state in MUTED_STATES:
            return True
        else:
            state = event.state
    return state in MUTED_STATES


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _project_modeling_window(
    *,
    deploys_per_day: float,
    base_rate: float,
    eligibility_rate: float,
    config: MetadataPassConfig,
) -> ProjectedModelingWindow:
    projected_deploys = round(deploys_per_day * config.modeling_days)
    projected_eligible = round(projected_deploys * max(0.0, eligibility_rate))
    projected_positives = round(projected_eligible * base_rate)
    train_pos = round(projected_positives * config.train_fraction)
    val_pos = round(projected_positives * config.val_fraction)
    test_pos = round(projected_positives * config.test_fraction)
    return ProjectedModelingWindow(
        modeling_days=config.modeling_days,
        projected_deploys=projected_deploys,
        projected_eligible=projected_eligible,
        projected_positives=projected_positives,
        projected_train_positives=train_pos,
        projected_val_positives=val_pos,
        projected_test_positives=test_pos,
        train_floor_met=train_pos >= config.train_positive_floor,
        val_floor_met=val_pos >= config.val_positive_floor,
        test_floor_met=test_pos >= config.test_positive_floor,
    )


def _generate_warnings(
    *,
    base_rate: float,
    base_rate_in_bounds: bool,
    projection: ProjectedModelingWindow,
    eligibility_rate: float,
    missing_data_rate: float,
    config: MetadataPassConfig,
) -> list[str]:
    warnings: list[str] = []
    if not base_rate_in_bounds:
        warnings.append(
            f"base rate {base_rate:.3f} outside acceptable window "
            f"[{config.base_rate_lower}, {config.base_rate_upper}] — RFC §4.4 requires re-scoping"
        )
    if not projection.train_floor_met:
        warnings.append(
            f"projected train positives {projection.projected_train_positives} "
            f"< floor {config.train_positive_floor}"
        )
    if not projection.val_floor_met:
        warnings.append(
            f"projected val positives {projection.projected_val_positives} "
            f"< floor {config.val_positive_floor}"
        )
    if not projection.test_floor_met:
        warnings.append(
            f"projected test positives {projection.projected_test_positives} "
            f"< floor {config.test_positive_floor}"
        )
    if eligibility_rate < 0.5:
        warnings.append(
            f"eligibility rate {eligibility_rate:.3f} < 0.5 — most deploys censored or missing-data; "
            f"consider larger inter-deploy gap or slice re-scope"
        )
    if missing_data_rate > 0.20:
        warnings.append(
            f"missing-data rate {missing_data_rate:.3f} > 0.20 — monitor-mute policy needs review "
            f"before real spike execution"
        )
    return warnings


def default_anchor() -> datetime:
    return datetime(2026, 7, 1, tzinfo=UTC)


def with_locked_thresholds(config: MetadataPassConfig, **overrides) -> MetadataPassConfig:
    """Convenience for the scoping-approval meeting to inject locked numbers."""
    return replace(config, **overrides)
