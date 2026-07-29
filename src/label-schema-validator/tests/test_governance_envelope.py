from __future__ import annotations

from typing import Any

import pytest
from forge_works.dr.label_schema_validator import validate_label_event

SC_36_REQUIRED_SUBFIELDS = (
    "tenant_id",
    "data_classification",
    "purpose_limitation",
    "retention_days",
    "residency_region",
    "redaction_policy_ref",
    "access_policy_ref",
    "cross_tenant_training_allowed",
)


@pytest.mark.parametrize("subfield", SC_36_REQUIRED_SUBFIELDS)
def test_missing_sc_36_subfield_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any, subfield: str
) -> None:
    valid_eligible_event["governance_envelope"].pop(subfield)
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.field_path == f"governance_envelope.{subfield}" for err in result.errors)


def test_only_tenant_id_rejects_multiple(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["governance_envelope"] = {"tenant_id": "forge-works"}
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    field_paths = {err.field_path for err in result.errors}
    for subfield in SC_36_REQUIRED_SUBFIELDS:
        if subfield == "tenant_id":
            continue
        assert f"governance_envelope.{subfield}" in field_paths
