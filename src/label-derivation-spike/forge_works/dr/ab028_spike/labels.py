"""Label derivation for the AB-028 spike.

Consumes a `SyntheticEventStream` and emits one label per deploy per GT §2 v0.2. Every
emitted label is validated via the AB-030 `label_schema_validator` library — halt-on-reject
per RFC §4.2 / AB-030 §7.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from forge_works.dr.ab028_spike.events import SERVICE
from forge_works.dr.label_schema_validator import (
    validate_label_event,
)

if TYPE_CHECKING:
    from datetime import datetime

    from forge_works.dr.ab028_spike.events import (
        DeployRecord,
        MonitorStateChange,
        SLOBreach,
        SyntheticEventStream,
    )
    from forge_works.dr.label_schema_validator import EstimandCatalog, ValidationResult

ESTIMAND_ID = "deploy_slo_breach_60m_association_v0"
HORIZON = timedelta(minutes=60)
PRODUCING_SYSTEM = "ab028_spike_label_deriver"
PRODUCING_VERSION = "0.1.0"
LOGIC_REF = f"mlflow://experiments/ab-028/{ESTIMAND_ID}/derivation.py"
MUTED_STATES = frozenset({"muted", "unknown"})


@dataclass(frozen=True)
class DerivedLabel:
    deploy: DeployRecord
    label: dict[str, Any]
    result: ValidationResult

    @property
    def eligibility(self) -> str:
        return self.label["eligibility"]

    @property
    def outcome(self) -> str | None:
        return self.label.get("outcome")


class LabelDerivationError(RuntimeError):
    def __init__(self, deploy: DeployRecord, result: ValidationResult) -> None:
        super().__init__(
            f"label rejected for deploy {deploy.deploy_id!r}: {[e.code for e in result.errors]}"
        )
        self.deploy = deploy
        self.result = result


def derive_labels(
    stream: SyntheticEventStream,
    *,
    catalog: EstimandCatalog,
    modeling_window_start: datetime,
    modeling_window_end: datetime,
) -> list[DerivedLabel]:
    """Derive one label per deploy inside [modeling_window_start, modeling_window_end).

    Deploys outside the modeling window are ignored (the metadata window uses aggregate
    counts only, not label emission — RFC §4.4).
    """
    deploys_in_window = [
        d for d in stream.deploys if modeling_window_start <= d.deployed_at < modeling_window_end
    ]
    labels: list[DerivedLabel] = []
    for i, deploy in enumerate(deploys_in_window):
        next_deploy_time = _next_deploy_time(deploys_in_window, i)
        label = _build_label(
            deploy=deploy,
            slice_id=stream.slice_id(),
            breaches=stream.slo_breaches,
            monitor_events=stream.monitor_events,
            next_deploy_time=next_deploy_time,
        )
        result = validate_label_event(label, estimand_catalog=catalog)
        if not result.is_valid:
            raise LabelDerivationError(deploy, result)
        labels.append(DerivedLabel(deploy=deploy, label=label, result=result))
    return labels


def _next_deploy_time(deploys: list[DeployRecord], i: int) -> datetime | None:
    if i + 1 < len(deploys):
        return deploys[i + 1].deployed_at
    return None


def _build_label(
    *,
    deploy: DeployRecord,
    slice_id: str,
    breaches: list[SLOBreach],
    monitor_events: list[MonitorStateChange],
    next_deploy_time: datetime | None,
) -> dict[str, Any]:
    horizon_end = deploy.deployed_at + HORIZON
    base = _label_skeleton(deploy=deploy, slice_id=slice_id, window_end=horizon_end)

    if next_deploy_time is not None and next_deploy_time < horizon_end:
        base["eligibility"] = "censored"
        base["observation_window"]["end"] = _iso(next_deploy_time)
        base["original_horizon_end"] = _iso(horizon_end)
        base["outcome_source"] = "derived"
        return base

    if _monitor_muted_during(monitor_events, deploy.deployed_at, horizon_end):
        base["eligibility"] = "missing_data"
        base["outcome_source"] = "derived"
        return base

    breach = _breach_in_window(breaches, deploy.deployed_at, horizon_end)
    base["eligibility"] = "eligible"
    if breach is not None:
        base["outcome"] = "slo_breach_occurred"
        base["outcome_source"] = "direct_observation"
    else:
        base["outcome"] = "slo_breach_absent"
        base["outcome_source"] = "derived"
    return base


def _label_skeleton(*, deploy: DeployRecord, slice_id: str, window_end: datetime) -> dict[str, Any]:
    return {
        "label_id": f"lbl_{deploy.deploy_id}",
        "estimand_id": ESTIMAND_ID,
        "slice": {
            "dimensions": ["per_service", "per_environment"],
            "values": {"per_service": deploy.service, "per_environment": deploy.environment},
            "slice_id": slice_id,
        },
        "identity_claims": [
            {"authority": "git", "key_type": "commit_id", "value": deploy.commit_sha},
            {"authority": "internal_directory", "key_type": "service_id", "value": SERVICE},
        ],
        "observation_window": {
            "start": _iso(deploy.deployed_at),
            "end": _iso(window_end),
        },
        "label_confidence": "certain",
        "label_delay": "PT5M",
        "governance_envelope": _governance_envelope(),
        "producing_system": PRODUCING_SYSTEM,
        "producing_version": PRODUCING_VERSION,
        "logic_ref": LOGIC_REF,
    }


def _governance_envelope() -> dict[str, Any]:
    return {
        "tenant_id": "forge-works",
        "data_classification": "internal",
        "purpose_limitation": ["reliability_prediction"],
        "retention_days": 365,
        "residency_region": "us-east-1",
        "redaction_policy_ref": "none",
        "access_policy_ref": "policies/dr-labels",
        "cross_tenant_training_allowed": False,
    }


def _breach_in_window(
    breaches: list[SLOBreach], start: datetime, end: datetime
) -> SLOBreach | None:
    for b in breaches:
        if start <= b.event_time < end:
            return b
    return None


def _monitor_muted_during(
    monitor_events: list[MonitorStateChange], start: datetime, end: datetime
) -> bool:
    current_state = "ok"
    for event in monitor_events:
        if event.event_time > end:
            break
        if event.event_time <= start:
            current_state = event.state
        elif current_state in MUTED_STATES:
            return True
        else:
            current_state = event.state
    return current_state in MUTED_STATES


def _iso(t: datetime) -> str:
    return t.isoformat().replace("+00:00", "Z")
