from __future__ import annotations

from typing import Any

from forge_works.dr.label_schema_validator import validate_label_event
from forge_works.dr.label_schema_validator.types import ValidatorConfig


def test_w1_label_delay_exceeds_threshold(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["label_delay"] = "PT2H"
    config = ValidatorConfig(label_delay_warning_threshold="PT1H")
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog, config=config)
    assert result.is_valid
    assert any(w.code == "LabelDelayExceedsThreshold" for w in result.warnings)


def test_w1_no_warning_without_threshold(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["label_delay"] = "PT2H"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert not any(w.code == "LabelDelayExceedsThreshold" for w in result.warnings)


def test_w2_correction_reason_surfaced(
    valid_manual_correction_event: dict[str, Any], catalog: Any
) -> None:
    result = validate_label_event(valid_manual_correction_event, estimand_catalog=catalog)
    assert result.is_valid
    assert any(w.code == "CorrectionReasonSurfaced" for w in result.warnings)


def test_w4_derived_outcome_uncertain(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["outcome_source"] = "derived"
    valid_eligible_event["label_confidence"] = "uncertain"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert any(w.code == "DerivedOutcomeUncertain" for w in result.warnings)


def test_w5_logic_ref_scheme_unrecognized(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["logic_ref"] = "ftp://example.com/rule"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert any(w.code == "LogicRefSchemeUnrecognized" for w in result.warnings)


def test_w6_intervention_ids_unusually_large(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["intervention_present"] = True
    valid_eligible_event["intervention_ids"] = [
        f"intv_2026-07-24T10:00:00Z_{i:04x}" for i in range(11)
    ]
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert any(w.code == "InterventionIdsUnusuallyLarge" for w in result.warnings)


def test_w7_estimand_catalog_not_configured(
    valid_eligible_event: dict[str, Any],
) -> None:
    result = validate_label_event(valid_eligible_event)
    assert result.is_valid
    assert any(w.code == "EstimandCatalogNotConfigured" for w in result.warnings)


def test_w3_deleted_never_emitted(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not any(w.code == "GovernanceEnvelopeMinimal" for w in result.warnings)


def test_w8_deleted_never_emitted(valid_censored_event: dict[str, Any], catalog: Any) -> None:
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert not any(w.code == "CensoredWindowUnverifiable" for w in result.warnings)


def test_unknown_field_warns(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["mystery_field"] = "some_value"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert any(
        w.code == "UnknownField" and w.field_path == "mystery_field" for w in result.warnings
    )


def test_reserved_x_prefix_no_warning(valid_eligible_event: dict[str, Any], catalog: Any) -> None:
    valid_eligible_event["x_git_sha"] = "8f3b21c"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid
    assert not any(w.code == "UnknownField" for w in result.warnings)
