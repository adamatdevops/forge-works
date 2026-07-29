from __future__ import annotations

from typing import Any

import pytest
from forge_works.dr.label_schema_validator import validate_label_event

REQUIRED_TOP_LEVEL_FIELDS = (
    "label_id",
    "estimand_id",
    "slice",
    "identity_claims",
    "observation_window",
    "outcome_source",
    "label_confidence",
    "label_delay",
    "eligibility",
    "governance_envelope",
)


@pytest.mark.parametrize("field_name", REQUIRED_TOP_LEVEL_FIELDS)
def test_missing_required_field_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any, field_name: str
) -> None:
    valid_eligible_event.pop(field_name)
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.field_path.startswith(field_name) for err in result.errors)


def test_valid_eligible_event_passes(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert result.errors == ()


def test_outcome_source_enum_out_of_range(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["outcome_source"] = "not_an_enum"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EnumOutOfRange" for err in result.errors)


def test_label_confidence_enum_out_of_range(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["outcome_source"] = "derived"
    valid_eligible_event["label_confidence"] = "very_certain"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EnumOutOfRange" for err in result.errors)


def test_eligibility_enum_out_of_range(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["eligibility"] = "not_eligible"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EnumOutOfRange" for err in result.errors)


def test_label_delay_negative_rejects(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["label_delay"] = "-PT1H"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "LabelDelayInvalid" for err in result.errors)


def test_label_delay_unparseable_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["label_delay"] = "not-a-duration"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "LabelDelayInvalid" for err in result.errors)
