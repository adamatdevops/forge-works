from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from forge_works.dr.label_schema_validator import CatalogEntry, EstimandCatalog


@pytest.fixture
def valid_eligible_event() -> dict[str, Any]:
    return deepcopy(
        {
            "label_id": "lbl_2026-07-24T11:20:00Z_e11f92",
            "estimand_id": "deploy_slo_breach_60m_association_v0",
            "slice": {
                "dimensions": ["per_service", "per_environment"],
                "values": {"per_service": "webhook-gateway", "per_environment": "prod"},
                "slice_id": "webhook-gateway.prod",
            },
            "identity_claims": [
                {"authority": "git", "key_type": "commit_id", "value": "8f3b21c"},
            ],
            "observation_window": {
                "start": "2026-07-24T10:15:03Z",
                "end": "2026-07-24T11:15:03Z",
            },
            "outcome": "slo_breach_occurred",
            "outcome_source": "direct_observation",
            "label_confidence": "certain",
            "label_delay": "PT4M57S",
            "eligibility": "eligible",
            "governance_envelope": {
                "tenant_id": "forge-works",
                "data_classification": "internal",
                "purpose_limitation": ["reliability_prediction"],
                "retention_days": 365,
                "residency_region": "us-east-1",
                "redaction_policy_ref": "none",
                "access_policy_ref": "policies/dr-labels",
                "cross_tenant_training_allowed": False,
            },
            "producing_system": "label_derivation_service",
            "producing_version": "1.2.0",
            "logic_ref": "mlflow://logic/deploy_slo_breach_60m_association_v0/derivation.py",
        }
    )


@pytest.fixture
def valid_censored_event(valid_eligible_event: dict[str, Any]) -> dict[str, Any]:
    event = deepcopy(valid_eligible_event)
    event["eligibility"] = "censored"
    event["observation_window"]["end"] = "2026-07-24T10:45:03Z"
    event["original_horizon_end"] = "2026-07-24T11:15:03Z"
    event.pop("outcome", None)
    return event


@pytest.fixture
def valid_missing_data_event(valid_eligible_event: dict[str, Any]) -> dict[str, Any]:
    event = deepcopy(valid_eligible_event)
    event["eligibility"] = "missing_data"
    event.pop("outcome", None)
    return event


@pytest.fixture
def valid_manual_ineligible_event(valid_eligible_event: dict[str, Any]) -> dict[str, Any]:
    event = deepcopy(valid_eligible_event)
    event["eligibility"] = "manual_ineligible"
    event["ineligibility_reason"] = "scheduled_maintenance"
    event.pop("outcome", None)
    return event


@pytest.fixture
def valid_manual_correction_event(valid_eligible_event: dict[str, Any]) -> dict[str, Any]:
    event = deepcopy(valid_eligible_event)
    event["outcome_source"] = "manual_correction"
    event["label_confidence"] = "certain"
    event["corrects_label_id"] = "lbl_2026-07-24T11:20:00Z_orig"
    event["correction_reason"] = "misclassified_by_derivation"
    event["correction_authority"] = "user:data-owner@forge-works"
    return event


@pytest.fixture
def catalog() -> EstimandCatalog:
    return EstimandCatalog(
        entries={
            "deploy_slo_breach_60m_association_v0": CatalogEntry(
                estimand_id="deploy_slo_breach_60m_association_v0",
                outcome_vocabulary=("slo_breach_occurred", "slo_breach_absent"),
                version="v0",
                owner="platform-team",
            ),
        }
    )
