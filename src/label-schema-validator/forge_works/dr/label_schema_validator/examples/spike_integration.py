"""Mock label-derivation-service demonstrating AB-028 spike integration pattern.

Per AB-030 RFC v0.5 §7.3: the spike's `label_derivation_service` (v0 build) imports
the label_schema_validator library and calls `validate_label_event` before each
emission. This module is the reference implementation the real AB-028 spike deriver
will build on — same integration surface, no side effects.

Halt-on-reject behavior: if the validator rejects any event, the deriver raises
`LabelValidationRejected` before emitting. Per RFC §7.3: "Any reject during spike
run means the deriver is emitting non-conformant events — spike halts, fixed
before real emission begins."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from forge_works.dr.label_schema_validator import validate_label_event

if TYPE_CHECKING:
    from forge_works.dr.label_schema_validator import EstimandCatalog, ValidationResult

ESTIMAND_ID = "deploy_slo_breach_60m_association_v0"
HORIZON = timedelta(minutes=60)


@dataclass(frozen=True)
class DeployEvent:
    deploy_id: str
    commit_sha: str
    service: str
    environment: str
    deployed_at: datetime
    slo_breach_at: datetime | None = None
    next_deploy_at: datetime | None = None
    monitor_muted: bool = False


class LabelValidationRejected(Exception):  # noqa: N818 — public API, preserved for RFC §7.3 semantics
    def __init__(self, deploy: DeployEvent, result: ValidationResult) -> None:
        super().__init__(
            f"label_schema_validator rejected label for deploy {deploy.deploy_id!r}: "
            f"{[e.code for e in result.errors]}"
        )
        self.deploy = deploy
        self.result = result


@dataclass
class MockLabelDerivationService:
    catalog: EstimandCatalog
    emitted: list[dict[str, Any]] = field(default_factory=list)
    warnings_seen: list[str] = field(default_factory=list)

    def derive_and_emit(self, deploy: DeployEvent) -> ValidationResult:
        label = self._derive(deploy)
        result = validate_label_event(label, estimand_catalog=self.catalog)
        if not result.is_valid:
            raise LabelValidationRejected(deploy, result)
        self.warnings_seen.extend(w.code for w in result.warnings)
        self.emitted.append(label)
        return result

    def _derive(self, deploy: DeployEvent) -> dict[str, Any]:
        window_end = deploy.deployed_at + HORIZON

        censored = deploy.next_deploy_at is not None and deploy.next_deploy_at < window_end
        muted = deploy.monitor_muted

        base = {
            "label_id": f"lbl_{deploy.deploy_id}",
            "estimand_id": ESTIMAND_ID,
            "slice": {
                "dimensions": ["per_service", "per_environment"],
                "values": {"per_service": deploy.service, "per_environment": deploy.environment},
                "slice_id": f"{deploy.service}.{deploy.environment}",
            },
            "identity_claims": [
                {"authority": "git", "key_type": "commit_id", "value": deploy.commit_sha},
                {
                    "authority": "internal_directory",
                    "key_type": "service_id",
                    "value": deploy.service,
                },
            ],
            "observation_window": {
                "start": deploy.deployed_at.isoformat().replace("+00:00", "Z"),
                "end": window_end.isoformat().replace("+00:00", "Z"),
            },
            "outcome_source": "direct_observation",
            "label_confidence": "certain",
            "label_delay": "PT5M",
            "governance_envelope": _governance_envelope(),
            "producing_system": "mock_label_derivation_service",
            "producing_version": "0.1.0",
            "logic_ref": f"mlflow://logic/{ESTIMAND_ID}/derivation.py",
        }

        if censored and deploy.next_deploy_at is not None:
            base["eligibility"] = "censored"
            base["observation_window"]["end"] = deploy.next_deploy_at.isoformat().replace(
                "+00:00", "Z"
            )
            base["original_horizon_end"] = window_end.isoformat().replace("+00:00", "Z")
            return base

        if muted:
            base["eligibility"] = "missing_data"
            return base

        base["eligibility"] = "eligible"
        base["outcome"] = "slo_breach_occurred" if deploy.slo_breach_at else "slo_breach_absent"
        return base


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


def generate_deploy_fixture(count: int) -> list[DeployEvent]:
    base_time = datetime(2026, 6, 1, 8, 0, 0, tzinfo=UTC)
    fixture: list[DeployEvent] = []
    for i in range(count):
        deployed_at = base_time + timedelta(hours=6 * i)
        breach_pattern = i % 5
        censor_pattern = i % 17
        mute_pattern = i % 23

        slo_breach_at = None
        if breach_pattern == 0:
            slo_breach_at = deployed_at + timedelta(minutes=30)

        next_deploy_at = None
        if censor_pattern == 3:
            next_deploy_at = deployed_at + timedelta(minutes=25)

        fixture.append(
            DeployEvent(
                deploy_id=f"dep_{i:04d}",
                commit_sha=f"{i:040x}",  # pragma: allowlist secret
                service="webhook-gateway",
                environment="prod",
                deployed_at=deployed_at,
                slo_breach_at=slo_breach_at,
                next_deploy_at=next_deploy_at,
                monitor_muted=(mute_pattern == 5 and censor_pattern != 3),
            )
        )
    return fixture
