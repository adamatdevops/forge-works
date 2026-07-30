"""Feature computation pipeline for the AB-028 spike (RFC §4.3).

Strict as-of-T0 boundary: every feature is computed from events with `event_time < T0` only.
No look-ahead. The `assert_no_lookahead_for` helper is exposed for tests.

Feature families per RFC §4.3:
- Deployment metadata: resource types, count, plan_diff_size, author role, hour, day-of-week.
- Recent-history rolling counts: apply_failed / slo_burning at {1h, 6h, 24h, 7d}.
- Slice-state: current monitor state, active-incident count, days-since-slice-was-added.
- Deploy-content: sensitive-resource-touched flag, plan_diff_size, resource_count.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

import pandas as pd
from forge_works.dr.ab028_spike.events import (
    RESOURCE_TYPES,
    SENSITIVE_RESOURCE_TYPES,
)

if TYPE_CHECKING:
    from datetime import datetime

    from forge_works.dr.ab028_spike.events import (
        DeployRecord,
        MonitorStateChange,
        SyntheticEventStream,
    )
    from forge_works.dr.ab028_spike.labels import DerivedLabel


ROLLING_WINDOWS_HOURS = (1, 6, 24, 168)
MONITOR_STATES = ("ok", "warning", "alert", "muted", "unknown")
AUTHOR_ROLE_COLUMNS = ("engineer", "senior_engineer", "sre")
SLICE_START_ANCHOR_DAYS = 400


@dataclass(frozen=True)
class FeatureMatrix:
    X: pd.DataFrame
    y: pd.Series
    deploy_ids: list[str]
    deploy_times: list[datetime]
    severity_map: dict[str, str]

    @property
    def n_features(self) -> int:
        return self.X.shape[1]

    @property
    def n_rows(self) -> int:
        return self.X.shape[0]


def build_feature_matrix(
    stream: SyntheticEventStream,
    labels: list[DerivedLabel],
) -> FeatureMatrix:
    """Build the feature matrix + target for the *eligible* label cohort only.

    Censored + missing_data labels are excluded — they don't participate in the primary
    calibration cohort per RFC §4.2. Consumers who need those cohorts filter them separately.
    """
    eligible = [dl for dl in labels if dl.eligibility == "eligible"]
    if not eligible:
        return FeatureMatrix(
            X=pd.DataFrame(),
            y=pd.Series(dtype="int8"),
            deploy_ids=[],
            deploy_times=[],
            severity_map={},
        )

    apply_failure_times = [af.event_time for af in stream.apply_failures]
    breach_times = [b.event_time for b in stream.slo_breaches]
    incident_times = [inc.event_time for inc in stream.incidents]
    monitor_events = stream.monitor_events
    slice_start = stream.start

    rows: list[dict[str, float | int]] = []
    y: list[int] = []
    deploy_ids: list[str] = []
    deploy_times: list[datetime] = []
    severity_map: dict[str, str] = {}
    for dl in eligible:
        deploy = dl.deploy
        row = _row_for_deploy(
            deploy=deploy,
            apply_failure_times=apply_failure_times,
            breach_times=breach_times,
            incident_times=incident_times,
            monitor_events=monitor_events,
            slice_start=slice_start,
        )
        rows.append(row)
        y.append(1 if dl.outcome == "slo_breach_occurred" else 0)
        deploy_ids.append(deploy.deploy_id)
        deploy_times.append(deploy.deployed_at)
        severity_map[deploy.deploy_id] = _severity_for_deploy(dl, breach_times)

    X = pd.DataFrame(rows).reset_index(drop=True)
    return FeatureMatrix(
        X=X,
        y=pd.Series(y, dtype="int8"),
        deploy_ids=deploy_ids,
        deploy_times=deploy_times,
        severity_map=severity_map,
    )


def _row_for_deploy(
    *,
    deploy: DeployRecord,
    apply_failure_times: list[datetime],
    breach_times: list[datetime],
    incident_times: list[datetime],
    monitor_events: list[MonitorStateChange],
    slice_start: datetime,
) -> dict[str, float | int]:
    t0 = deploy.deployed_at
    row: dict[str, float | int] = {
        "plan_diff_size": deploy.plan_diff_size,
        "resource_count": deploy.resource_count,
        "hour_of_day": t0.hour,
        "day_of_week": t0.weekday(),
        "is_friday_pm": int(t0.weekday() == 4 and t0.hour >= 15),
        "sensitive_resource_touched": int(
            bool(SENSITIVE_RESOURCE_TYPES.intersection(deploy.resource_types_touched))
        ),
        "days_since_slice_added": max((t0 - slice_start).days, 0) + SLICE_START_ANCHOR_DAYS,
    }
    for rt in RESOURCE_TYPES:
        row[f"resource_type__{rt}"] = int(rt in deploy.resource_types_touched)
    for role in AUTHOR_ROLE_COLUMNS:
        row[f"author_role__{role}"] = int(deploy.author_role == role)
    for hours in ROLLING_WINDOWS_HOURS:
        lo = t0 - timedelta(hours=hours)
        row[f"apply_failed_last_{hours}h"] = _count_in(apply_failure_times, lo, t0)
        if hours <= 24:
            row[f"slo_burning_last_{hours}h"] = _count_in(breach_times, lo, t0)
    row["time_since_last_apply_failure_h"] = _hours_since_last(apply_failure_times, t0)
    row["time_since_last_breach_h"] = _hours_since_last(breach_times, t0)
    row["recent_incidents_24h"] = _count_in(incident_times, t0 - timedelta(hours=24), t0)
    monitor_state = _monitor_state_at(monitor_events, t0)
    for state in MONITOR_STATES:
        row[f"monitor_state__{state}"] = int(monitor_state == state)
    return row


def _count_in(sorted_times: list[datetime], lo: datetime, hi: datetime) -> int:
    left = bisect.bisect_left(sorted_times, lo)
    right = bisect.bisect_left(sorted_times, hi)
    return right - left


def _hours_since_last(sorted_times: list[datetime], t0: datetime) -> float:
    idx = bisect.bisect_left(sorted_times, t0)
    if idx == 0:
        return 24.0 * 365
    last = sorted_times[idx - 1]
    return (t0 - last).total_seconds() / 3600.0


def _monitor_state_at(monitor_events: list[MonitorStateChange], t0: datetime) -> str:
    state = "ok"
    for event in monitor_events:
        if event.event_time >= t0:
            break
        state = event.state
    return state


def _severity_for_deploy(dl: DerivedLabel, breach_times: list[datetime]) -> str:
    del breach_times
    if dl.outcome != "slo_breach_occurred":
        return "none"
    return "warning"


def assert_no_lookahead_for(stream: SyntheticEventStream, t0: datetime) -> None:
    """Sanity check used by tests: no synthetic-stream event with time >= t0 can be visible to the feature builder at T0."""
    for events in (
        stream.slo_breaches,
        stream.apply_failures,
        stream.monitor_events,
        stream.incidents,
    ):
        for e in events:
            if e.event_time >= t0:
                msg = f"as-of-T0 boundary violated at {t0.isoformat()} by event at {e.event_time.isoformat()}"
                raise AssertionError(msg)
