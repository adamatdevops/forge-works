from __future__ import annotations

from typing import Any

import pytest
from forge_works.dr.label_schema_validator import validate_label_event

PROVENANCE_FIELDS = ("producing_system", "producing_version", "logic_ref")


@pytest.mark.parametrize("field_name", PROVENANCE_FIELDS)
def test_missing_provenance_field_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any, field_name: str
) -> None:
    valid_eligible_event.pop(field_name)
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(
        err.code == "ProvenanceIncomplete" and err.field_path == field_name for err in result.errors
    )


def test_semver_rejects_build_hash(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["producing_version"] = "abc123def"  # pragma: allowlist secret
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "ProducingVersionInvalid" for err in result.errors)


def test_semver_accepts_prerelease(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["producing_version"] = "1.2.0-alpha.1"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
