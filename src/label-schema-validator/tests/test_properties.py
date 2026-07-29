from __future__ import annotations

from copy import deepcopy
from typing import Any

from forge_works.dr.label_schema_validator import validate_label_event
from forge_works.dr.label_schema_validator.rules import (
    ELIGIBILITY_VALUES,
    LABEL_CONFIDENCE_VALUES,
    OUTCOME_SOURCE_VALUES,
)
from hypothesis import (
    HealthCheck,
    given,
    settings,
    strategies as st,
)

_FIXTURE_SETTINGS = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])

REQUIRED_TOP_LEVEL = (
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
    "producing_system",
    "producing_version",
    "logic_ref",
)

EXPECTED_ERROR_CODES = frozenset(
    {
        "MissingRequiredField",
        "EnumOutOfRange",
        "FieldTypeMismatch",
        "LabelDelayInvalid",
        "ProvenanceIncomplete",
        "ProducingVersionInvalid",
        "DirectObservationMustBeCertain",
        "ManualIneligibleRequiresReason",
        "CorrectionEventIncomplete",
        "CensoredEventNotTruncated",
        "ObservationWindowInvalid",
        "InterventionPresentInconsistent",
        "EmittedBeforeWindowClosed",
        "OutcomeUnexpectedOnNonEligible",
        "OriginalHorizonEndUnexpected",
        "IneligibilityReasonUnexpected",
        "OutcomeNotInVocabulary",
        "EstimandNotInCatalog",
    }
)

EXPECTED_WARNING_CODES = frozenset(
    {
        "LabelDelayExceedsThreshold",
        "CorrectionReasonSurfaced",
        "DerivedOutcomeUncertain",
        "LogicRefSchemeUnrecognized",
        "InterventionIdsUnusuallyLarge",
        "EstimandCatalogNotConfigured",
        "UnknownField",
    }
)


def test_p1_seed_schema_generated_event_passes(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert result.is_valid


@_FIXTURE_SETTINGS
@given(field_to_drop=st.sampled_from(REQUIRED_TOP_LEVEL))
def test_p2_mutation_drops_required_field(
    field_to_drop: str,
    valid_eligible_event: dict[str, Any],
    catalog: Any,
) -> None:
    event = deepcopy(valid_eligible_event)
    event.pop(field_to_drop, None)
    result = validate_label_event(event, estimand_catalog=catalog)
    assert not result.is_valid


@_FIXTURE_SETTINGS
@given(eligibility=st.sampled_from(sorted(ELIGIBILITY_VALUES)))
def test_p2_eligibility_shape_valid(
    eligibility: str,
    valid_eligible_event: dict[str, Any],
    valid_censored_event: dict[str, Any],
    valid_missing_data_event: dict[str, Any],
    valid_manual_ineligible_event: dict[str, Any],
    catalog: Any,
) -> None:
    events = {
        "eligible": valid_eligible_event,
        "censored": valid_censored_event,
        "missing_data": valid_missing_data_event,
        "manual_ineligible": valid_manual_ineligible_event,
    }
    result = validate_label_event(events[eligibility], estimand_catalog=catalog)
    assert result.is_valid


def test_p3_idempotence_literal_equality(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    first = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    second = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert first == second


def test_p3_idempotence_across_mutations(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event.pop("label_id")
    first = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    second = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert first == second


def test_p4_error_codes_all_within_expected_set(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    empty_event: dict[str, Any] = {}
    result = validate_label_event(empty_event, estimand_catalog=catalog)
    for err in result.errors:
        assert err.code in EXPECTED_ERROR_CODES, f"unexpected error code {err.code!r}"


@_FIXTURE_SETTINGS
@given(enum_value=st.text(min_size=1, max_size=20))
def test_p4_unknown_enum_uses_stable_code(
    enum_value: str,
    valid_eligible_event: dict[str, Any],
    catalog: Any,
) -> None:
    if enum_value in OUTCOME_SOURCE_VALUES or enum_value in LABEL_CONFIDENCE_VALUES:
        return
    event = deepcopy(valid_eligible_event)
    event["outcome_source"] = enum_value
    result = validate_label_event(event, estimand_catalog=catalog)
    assert any(err.code == "EnumOutOfRange" for err in result.errors)


def test_p4_warning_codes_all_within_expected_set(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["mystery"] = "value"
    valid_eligible_event["outcome_source"] = "derived"
    valid_eligible_event["label_confidence"] = "uncertain"
    valid_eligible_event["logic_ref"] = "ftp://example/rule"
    valid_eligible_event["intervention_present"] = True
    valid_eligible_event["intervention_ids"] = [f"intv_{i:04x}" for i in range(15)]
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    for w in result.warnings:
        assert w.code in EXPECTED_WARNING_CODES, f"unexpected warning code {w.code!r}"
