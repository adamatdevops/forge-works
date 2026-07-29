from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from forge_works.dr.label_schema_validator.types import (
    ValidationError,
    ValidationWarning,
)

if TYPE_CHECKING:
    from forge_works.dr.label_schema_validator.types import (
        EstimandCatalog,
        ValidatorConfig,
    )

OUTCOME_SOURCE_VALUES = frozenset({"direct_observation", "derived", "manual_correction"})
LABEL_CONFIDENCE_VALUES = frozenset({"certain", "likely", "uncertain"})
ELIGIBILITY_VALUES = frozenset({"eligible", "censored", "missing_data", "manual_ineligible"})
CORRECTION_REASONS = frozenset(
    {
        "misclassified_by_derivation",
        "context_missed_by_automated_source",
        "late_arriving_evidence",
        "disputed_semantics",
    }
)

SC_36_REQUIRED_FIELDS = (
    "tenant_id",
    "data_classification",
    "purpose_limitation",
    "retention_days",
    "residency_region",
    "redaction_policy_ref",
    "access_policy_ref",
    "cross_tenant_training_allowed",
)

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

ISO_DURATION_RE = re.compile(
    r"^(-)?P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?"
    r"(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)

KNOWN_LOGIC_REF_SCHEMES = ("mlflow://", "git://", "https://", "s3://", "arn:")

KNOWN_CONDITIONAL_FIELDS = frozenset(
    {
        "corrects_label_id",
        "correction_reason",
        "correction_authority",
        "original_horizon_end",
        "ineligibility_reason",
        "emitted_at",
        "intervention_present",
        "intervention_ids",
    }
)

CANONICAL_TOP_LEVEL_FIELDS = (
    frozenset(
        {
            "label_id",
            "estimand_id",
            "slice",
            "identity_claims",
            "observation_window",
            "outcome",
            "outcome_source",
            "label_confidence",
            "label_delay",
            "eligibility",
            "governance_envelope",
            "producing_system",
            "producing_version",
            "logic_ref",
        }
    )
    | KNOWN_CONDITIONAL_FIELDS
)


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    return not (isinstance(value, str) and not value)


def _parse_iso8601(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_duration_seconds(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    match = ISO_DURATION_RE.match(value)
    if not match:
        return None
    sign, years, months, days, hours, minutes, seconds = match.groups()
    total = (
        int(years or 0) * 365 * 86400
        + int(months or 0) * 30 * 86400
        + int(days or 0) * 86400
        + int(hours or 0) * 3600
        + int(minutes or 0) * 60
        + float(seconds or 0)
    )
    return -total if sign == "-" else total


def _err(code: str, message: str, field_path: str = "") -> ValidationError:
    return ValidationError(code=code, message=message, field_path=field_path)


def _warn(code: str, message: str, field_path: str = "") -> ValidationWarning:
    return ValidationWarning(code=code, message=message, field_path=field_path)


def _check_scalar_required(event: dict[str, Any], name: str) -> list[ValidationError]:
    if _is_present(event.get(name)):
        return []
    return [_err("MissingRequiredField", f"{name} required", name)]


def _check_enum(event: dict[str, Any], name: str, allowed: frozenset[str]) -> list[ValidationError]:
    value = event.get(name)
    if not _is_present(value):
        return [_err("MissingRequiredField", f"{name} required", name)]
    if value not in allowed:
        return [
            _err(
                "EnumOutOfRange",
                f"{name} must be one of {sorted(allowed)}",
                name,
            )
        ]
    return []


def _check_slice(event: dict[str, Any]) -> list[ValidationError]:
    slice_val = event.get("slice")
    if not isinstance(slice_val, dict) or not slice_val:
        return [_err("MissingRequiredField", "slice required", "slice")]
    return [
        _err("MissingRequiredField", f"slice.{sub} required", f"slice.{sub}")
        for sub in ("dimensions", "values", "slice_id")
        if not _is_present(slice_val.get(sub))
    ]


def _check_identity_claims(event: dict[str, Any]) -> list[ValidationError]:
    identity_claims = event.get("identity_claims")
    if isinstance(identity_claims, list) and identity_claims:
        return []
    return [_err("MissingRequiredField", "identity_claims required", "identity_claims")]


def _check_observation_window(event: dict[str, Any]) -> list[ValidationError]:
    obs_window = event.get("observation_window")
    if not isinstance(obs_window, dict):
        return [_err("MissingRequiredField", "observation_window required", "observation_window")]
    return [
        _err(
            "MissingRequiredField",
            f"observation_window.{sub} required",
            f"observation_window.{sub}",
        )
        for sub in ("start", "end")
        if not _is_present(obs_window.get(sub))
    ]


def _check_label_delay(event: dict[str, Any]) -> list[ValidationError]:
    label_delay = event.get("label_delay")
    if not _is_present(label_delay):
        return [_err("MissingRequiredField", "label_delay required", "label_delay")]
    seconds = _parse_duration_seconds(label_delay)
    if seconds is None or seconds < 0:
        return [
            _err(
                "LabelDelayInvalid",
                "label_delay must be a non-negative ISO-8601 duration",
                "label_delay",
            )
        ]
    return []


def _check_governance_envelope(event: dict[str, Any]) -> list[ValidationError]:
    governance = event.get("governance_envelope")
    if not isinstance(governance, dict):
        return [
            _err(
                "MissingRequiredField",
                "governance_envelope required",
                "governance_envelope",
            )
        ]
    return [
        _err(
            "MissingRequiredField",
            f"governance_envelope.{sub} required per SC §3.6",
            f"governance_envelope.{sub}",
        )
        for sub in SC_36_REQUIRED_FIELDS
        if governance.get(sub) is None
    ]


def check_required_fields(
    event: dict[str, Any],
    catalog: EstimandCatalog | None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for name in ("label_id", "estimand_id"):
        errors.extend(_check_scalar_required(event, name))
    errors.extend(_check_slice(event))
    errors.extend(_check_identity_claims(event))
    errors.extend(_check_observation_window(event))
    errors.extend(_check_enum(event, "outcome_source", OUTCOME_SOURCE_VALUES))
    errors.extend(_check_enum(event, "label_confidence", LABEL_CONFIDENCE_VALUES))
    errors.extend(_check_label_delay(event))
    errors.extend(_check_enum(event, "eligibility", ELIGIBILITY_VALUES))
    errors.extend(_check_governance_envelope(event))

    eligibility = event.get("eligibility")
    errors.extend(_check_conditional_outcome(event, eligibility, catalog))
    errors.extend(_check_conditional_censoring(event, eligibility))
    errors.extend(_check_conditional_manual_ineligible(event, eligibility))
    return errors


def _check_conditional_outcome(
    event: dict[str, Any],
    eligibility: Any,
    catalog: EstimandCatalog | None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    outcome = event.get("outcome")
    if eligibility == "eligible":
        if not _is_present(outcome):
            errors.append(
                _err(
                    "MissingRequiredField", "outcome required when eligibility=eligible", "outcome"
                )
            )
        elif catalog is not None:
            entry = catalog.lookup(event.get("estimand_id", ""))
            if entry is None:
                errors.append(
                    _err(
                        "EstimandNotInCatalog",
                        f"estimand_id {event.get('estimand_id')!r} not found in catalog",
                        "estimand_id",
                    )
                )
            elif outcome not in entry.outcome_vocabulary:
                errors.append(
                    _err(
                        "OutcomeNotInVocabulary",
                        f"outcome {outcome!r} not in vocabulary {list(entry.outcome_vocabulary)}",
                        "outcome",
                    )
                )
    elif eligibility in {"censored", "missing_data", "manual_ineligible"} and outcome is not None:
        errors.append(
            _err(
                "OutcomeUnexpectedOnNonEligible",
                f"outcome must be absent when eligibility={eligibility}",
                "outcome",
            )
        )
    return errors


def _check_conditional_censoring(
    event: dict[str, Any],
    eligibility: Any,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    horizon = event.get("original_horizon_end")
    if eligibility == "censored":
        if not _is_present(horizon):
            errors.append(
                _err(
                    "MissingRequiredField",
                    "original_horizon_end required when eligibility=censored",
                    "original_horizon_end",
                )
            )
        else:
            obs_end = _parse_iso8601((event.get("observation_window") or {}).get("end"))
            horizon_dt = _parse_iso8601(horizon)
            if obs_end is not None and horizon_dt is not None and not (obs_end < horizon_dt):
                errors.append(
                    _err(
                        "CensoredEventNotTruncated",
                        "observation_window.end must be < original_horizon_end when censored",
                        "observation_window.end",
                    )
                )
    elif horizon is not None:
        errors.append(
            _err(
                "OriginalHorizonEndUnexpected",
                "original_horizon_end must be absent unless eligibility=censored",
                "original_horizon_end",
            )
        )
    return errors


def _check_conditional_manual_ineligible(
    event: dict[str, Any],
    eligibility: Any,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    reason = event.get("ineligibility_reason")
    if eligibility == "manual_ineligible":
        if not _is_present(reason):
            errors.append(
                _err(
                    "ManualIneligibleRequiresReason",
                    "ineligibility_reason required when eligibility=manual_ineligible",
                    "ineligibility_reason",
                )
            )
    elif reason is not None:
        errors.append(
            _err(
                "IneligibilityReasonUnexpected",
                "ineligibility_reason must be absent unless eligibility=manual_ineligible",
                "ineligibility_reason",
            )
        )
    return errors


def check_provenance(event: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = [
        _err("ProvenanceIncomplete", f"{name} required", name)
        for name in ("producing_system", "producing_version", "logic_ref")
        if not _is_present(event.get(name))
    ]

    version = event.get("producing_version")
    if _is_present(version) and not SEMVER_RE.match(str(version)):
        errors.append(
            _err(
                "ProducingVersionInvalid",
                f"producing_version {version!r} is not valid SemVer 2.0.0",
                "producing_version",
            )
        )
    return errors


def check_cross_field(event: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    outcome_source = event.get("outcome_source")
    label_confidence = event.get("label_confidence")
    if outcome_source == "direct_observation" and label_confidence != "certain":
        errors.append(
            _err(
                "DirectObservationMustBeCertain",
                "outcome_source=direct_observation requires label_confidence=certain",
                "label_confidence",
            )
        )

    if outcome_source == "manual_correction":
        errors.extend(
            _err(
                "CorrectionEventIncomplete",
                f"{name} required for manual_correction events",
                name,
            )
            for name in ("corrects_label_id", "correction_authority")
            if not _is_present(event.get(name))
        )
        reason = event.get("correction_reason")
        if not _is_present(reason):
            errors.append(
                _err(
                    "CorrectionEventIncomplete",
                    "correction_reason required for manual_correction events",
                    "correction_reason",
                )
            )
        elif reason not in CORRECTION_REASONS:
            errors.append(
                _err(
                    "EnumOutOfRange",
                    f"correction_reason must be one of {sorted(CORRECTION_REASONS)}",
                    "correction_reason",
                )
            )

    obs_window = event.get("observation_window")
    if isinstance(obs_window, dict):
        start = _parse_iso8601(obs_window.get("start"))
        end = _parse_iso8601(obs_window.get("end"))
        if start is not None and end is not None and not (end > start):
            errors.append(
                _err(
                    "ObservationWindowInvalid",
                    "observation_window.end must be > observation_window.start",
                    "observation_window",
                )
            )

    if event.get("intervention_present") is True:
        ids = event.get("intervention_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(
                _err(
                    "InterventionPresentInconsistent",
                    "intervention_ids must be a non-empty list when intervention_present=true",
                    "intervention_ids",
                )
            )

    emitted_at = event.get("emitted_at")
    if _is_present(emitted_at) and isinstance(obs_window, dict):
        emitted_dt = _parse_iso8601(emitted_at)
        end_dt = _parse_iso8601(obs_window.get("end"))
        if emitted_dt is not None and end_dt is not None and emitted_dt < end_dt:
            errors.append(
                _err(
                    "EmittedBeforeWindowClosed",
                    "emitted_at must be >= observation_window.end",
                    "emitted_at",
                )
            )
    return errors


def collect_warnings(
    event: dict[str, Any],
    config: ValidatorConfig,
    catalog: EstimandCatalog | None,
) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []

    threshold = config.label_delay_warning_threshold
    if threshold is not None:
        delay_seconds = _parse_duration_seconds(event.get("label_delay"))
        threshold_seconds = _parse_duration_seconds(threshold)
        if (
            delay_seconds is not None
            and threshold_seconds is not None
            and delay_seconds > threshold_seconds
        ):
            warnings.append(
                _warn(
                    "LabelDelayExceedsThreshold",
                    f"label_delay {event.get('label_delay')} exceeds configured threshold {threshold}",
                    "label_delay",
                )
            )

    if event.get("outcome_source") == "manual_correction":
        reason = event.get("correction_reason")
        if reason in CORRECTION_REASONS:
            warnings.append(
                _warn(
                    "CorrectionReasonSurfaced",
                    f"correction_reason={reason} (observability tag)",
                    "correction_reason",
                )
            )

    if event.get("outcome_source") == "derived" and event.get("label_confidence") == "uncertain":
        warnings.append(
            _warn(
                "DerivedOutcomeUncertain",
                "derived outcome with uncertain confidence — unsafe for ordinary calibration (GT §7 AP-C4)",
                "label_confidence",
            )
        )

    logic_ref = event.get("logic_ref")
    if (
        isinstance(logic_ref, str)
        and logic_ref
        and not any(logic_ref.startswith(scheme) for scheme in KNOWN_LOGIC_REF_SCHEMES)
    ):
        scheme = logic_ref.split("://", 1)[0] if "://" in logic_ref else logic_ref.split(":", 1)[0]
        warnings.append(
            _warn(
                "LogicRefSchemeUnrecognized",
                f"logic_ref scheme {scheme!r} not in {list(KNOWN_LOGIC_REF_SCHEMES)}",
                "logic_ref",
            )
        )

    intervention_ids = event.get("intervention_ids")
    if (
        isinstance(intervention_ids, list)
        and len(intervention_ids) > config.intervention_ids_soft_bound
    ):
        warnings.append(
            _warn(
                "InterventionIdsUnusuallyLarge",
                f"intervention_ids count {len(intervention_ids)} exceeds soft bound {config.intervention_ids_soft_bound}",
                "intervention_ids",
            )
        )

    if catalog is None:
        warnings.append(
            _warn(
                "EstimandCatalogNotConfigured",
                "estimand_catalog not provided — vocabulary membership and version-stability checks skipped",
                "estimand_id",
            )
        )
    return warnings


def collect_unknown_field_warnings(event: dict[str, Any]) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []
    for name in event:
        if name in CANONICAL_TOP_LEVEL_FIELDS or name.startswith("x_"):
            continue
        warnings.append(_warn("UnknownField", f"unknown top-level field {name!r}", name))
    return warnings
