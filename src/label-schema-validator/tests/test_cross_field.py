from __future__ import annotations

from typing import Any

from forge_works.dr.label_schema_validator import validate_label_event


def test_cr1_direct_observation_must_be_certain(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["outcome_source"] = "direct_observation"
    valid_eligible_event["label_confidence"] = "likely"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "DirectObservationMustBeCertain" for err in result.errors)


def test_cr3_correction_event_incomplete(
    valid_manual_correction_event: dict[str, Any], catalog: Any
) -> None:
    valid_manual_correction_event.pop("correction_authority")
    result = validate_label_event(valid_manual_correction_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "CorrectionEventIncomplete" for err in result.errors)


def test_cr3_correction_reason_enum_out_of_range(
    valid_manual_correction_event: dict[str, Any], catalog: Any
) -> None:
    valid_manual_correction_event["correction_reason"] = "made_up_reason"
    result = validate_label_event(valid_manual_correction_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EnumOutOfRange" for err in result.errors)


def test_cr5_observation_window_invalid(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["observation_window"] = {
        "start": "2026-07-24T11:15:03Z",
        "end": "2026-07-24T10:15:03Z",
    }
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "ObservationWindowInvalid" for err in result.errors)


def test_cr6_intervention_present_true_without_ids(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["intervention_present"] = True
    valid_eligible_event["intervention_ids"] = []
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "InterventionPresentInconsistent" for err in result.errors)


def test_cr6_intervention_present_false_with_ids_absent_passes(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["intervention_present"] = False
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid


def test_cr7_emitted_before_window_closed(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["emitted_at"] = "2026-07-24T10:30:00Z"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EmittedBeforeWindowClosed" for err in result.errors)


def test_cr7_emitted_after_window_closed_passes(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["emitted_at"] = "2026-07-24T11:20:00Z"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid


def test_cr7_no_emitted_at_skipped(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    assert "emitted_at" not in valid_eligible_event
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
