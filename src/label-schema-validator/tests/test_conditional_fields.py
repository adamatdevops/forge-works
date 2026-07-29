from __future__ import annotations

from typing import Any

from forge_works.dr.label_schema_validator import validate_label_event


def test_eligible_without_outcome_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event.pop("outcome")
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(
        err.code == "MissingRequiredField" and err.field_path == "outcome" for err in result.errors
    )


def test_censored_with_outcome_rejects(valid_censored_event: dict[str, Any], catalog: Any) -> None:
    valid_censored_event["outcome"] = "slo_breach_occurred"
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "OutcomeUnexpectedOnNonEligible" for err in result.errors)


def test_valid_censored_event_passes(valid_censored_event: dict[str, Any], catalog: Any) -> None:
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert result.is_valid


def test_censored_missing_original_horizon_end_rejects(
    valid_censored_event: dict[str, Any], catalog: Any
) -> None:
    valid_censored_event.pop("original_horizon_end")
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(
        err.field_path == "original_horizon_end" and err.code == "MissingRequiredField"
        for err in result.errors
    )


def test_censored_non_truncated_rejects(valid_censored_event: dict[str, Any], catalog: Any) -> None:
    valid_censored_event["observation_window"]["end"] = valid_censored_event["original_horizon_end"]
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "CensoredEventNotTruncated" for err in result.errors)


def test_eligible_with_original_horizon_end_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["original_horizon_end"] = "2026-07-24T11:15:03Z"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "OriginalHorizonEndUnexpected" for err in result.errors)


def test_manual_ineligible_requires_reason(
    valid_manual_ineligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_manual_ineligible_event.pop("ineligibility_reason")
    result = validate_label_event(valid_manual_ineligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "ManualIneligibleRequiresReason" for err in result.errors)


def test_valid_manual_ineligible_passes(
    valid_manual_ineligible_event: dict[str, Any], catalog: Any
) -> None:
    result = validate_label_event(valid_manual_ineligible_event, estimand_catalog=catalog)
    assert result.is_valid


def test_valid_missing_data_passes(valid_missing_data_event: dict[str, Any], catalog: Any) -> None:
    result = validate_label_event(valid_missing_data_event, estimand_catalog=catalog)
    assert result.is_valid


def test_slice_missing_dimensions_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["slice"].pop("dimensions")
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.field_path == "slice.dimensions" for err in result.errors)


def test_slice_missing_slice_id_rejects(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["slice"].pop("slice_id")
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.field_path == "slice.slice_id" for err in result.errors)
