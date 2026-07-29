# AB-030 Label Schema Validator Scoping RFC (v0.4 draft) — shared library for `forge.events.ground_truth.v1` conformance

> **Status:** Scoping draft (v0.4 — GT contract v0.3 amendments landed 2026-07-29 resolving 4 non-GT v0.3 → v1 items: W3 delete, `logic_ref` scheme enumeration, `intervention_ids` bound, estimand catalog governance). Not yet approved for build. Approval means: the API surface, validation rules, and distribution model are locked and the library may be implemented.
> **v0.4 changes:** (i) §3.4 W3 `GovernanceEnvelopeMinimal` DELETED — redundant with §3.1 SC §3.6 full-shape enforcement (a label with only `tenant_id` already hard-rejects on the 7 missing SC §3.6 fields). (ii) §3.4 W5 `LogicRefSchemeUnrecognized` status note updated — GT §2.2 v0.3 codifies the canonical scheme list; W5 upgrades to hard-reject at library v1. (iii) §3.4 W6 `InterventionIdsUnusuallyLarge` status note updated — GT §6.2 v0.3 defines canonical bound = 10 + element constraints; W6 upgrades to hard-reject at library v1. (iv) §2.2 estimand-catalog out-of-scope entry updated — GT §9 v0.3 resolves governance via YAML catalog at `docs/decisions/dynamic-reliability/estimand_catalog.yaml`; catalog format and API surface stable, wiring is producer responsibility. §13 v0.3 → v1 acceptance criteria for these 4 items flipped to `[x]`.
> **v0.3 changes:** the 3 GT-amendment blockers from RFC v0.2 §13 have landed (GT v0.2 amendments in the same PR). §3.1 `outcome` and `slice` rows lock to the GT-defined canonical rules; §3.3 CR4 locks to hard-reject on missing / non-truncated `original_horizon_end`; W8 `CensoredWindowUnverifiable` deleted (no longer needed — GT §2.1 now requires the field). §7.1 fixtures updated accordingly. §13 v0.2 → v1 acceptance criteria for F3/F4/F8 flipped to `[x]`.
> **Owner:** Platform team (build owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Blocks:** AB-028 feasibility spike execution (per `AB-028_FEASIBILITY_SPIKE.md` §3 Schema-conformance block — spike halts with `blocked_on: AB-030` if this library is not available at execution time).
> **Enabled by:** `GROUND_TRUTH_INTERVENTION_CONTRACT.md` v0.1 (§2.1 required fields, §2.2 provenance rules, §3 eligibility semantics, §5 censoring, §7 anti-patterns).
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-030` (backlog is repo-ignored; canonical scope on this document).

---

## 1. Why this library exists

Codex round-2 loop on `AB-028_FEASIBILITY_SPIKE.md` (F19) surfaced that the spike RFC's label emission would duplicate the schema knowledge already declared in `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2. Ad-hoc emission — the spike's `label_derivation_service` handrolling required-field checks and provenance rules against its own copy of the contract — is the AP-C1-adjacent failure mode: two label producers holding two copies of "the schema" drift, and drift on the label stream silently invalidates every downstream calibration measurement.

The fix is a **shared library** — one code artifact that every label producer (the AB-028 spike deriver, future production derivers, manual-correction services, backfill jobs) MUST call before emitting to `forge.events.ground_truth.v1`. The library is the single source of truth for "does this event conform to GT §2 as currently versioned"; the GT contract is the source of truth for what the rules ARE; the library is the source of truth for what the rules currently ENFORCE.

The library is deliberately **narrow, synchronous, and stateless**. Its purpose is one function: given a candidate label event, return a verdict — accept, reject with typed errors, or accept-with-warnings for advisory-only issues. No emission, no I/O, no queuing, no correlation. Emission stays with the producer; conformance moves to the library.

---

## 2. Scope

### 2.1 In-scope

- **Label event validation** — every field enumerated in GT §2.1 (11 required fields including `label_id`, `estimand_id`, `slice`, `identity_claims`, `observation_window`, `outcome`, `outcome_source`, `label_confidence`, `label_delay`, `eligibility`, `governance_envelope`).
- **Provenance rule enforcement** — GT §2.2's three provenance fields (`producing_system`, `producing_version`, `logic_ref`) enforced as hard-reject when absent (per GT §2.2 rule "a label without provenance is not a label").
- **Eligibility enum enforcement** — the four eligibility values from GT §3 (`eligible` / `censored` / `missing_data` / `manual_ineligible`) plus their conditional-field requirements (e.g., `manual_ineligible` MUST carry `ineligibility_reason`).
- **Governance envelope shape validation** — same shape as SC §3.6; the library validates shape only, not inheritance semantics (per §2.2 out-of-scope).
- **Outcome-source × label-confidence consistency** — GT §2.1 rule "direct observations are always `certain`"; library rejects `outcome_source: direct_observation` with `label_confidence != certain`.
- **Correction-event consistency** — GT §4 correction events MUST carry `corrects_label_id`, `correction_reason` from a bounded enum, and `correction_authority`; library rejects malformed corrections.
- **Censored-event consistency** — GT §5 censored labels MUST have truncated `observation_window` where `end < original horizon end`; library rejects claims of censoring with un-truncated windows.
- **Distribution as a Python package** — installable via the monorepo's package manifest; single import path `forge_works.dr.label_schema_validator`.
- **Semver policy** — MAJOR bump when a previously-passing event would now reject; MINOR bump when a new hard-reject rule lands with a deprecation window; PATCH bump for warning additions and internal changes.

### 2.2 Out-of-scope

- **Governance envelope INHERITANCE validation** — the library validates shape (per SC §3.6), not "did this label inherit the strictest envelope from its inputs" (that requires input-event access, which is producer-side). Filed as GT §11 v1 graduation criterion, not this library's problem.
- **Intervention event validation** — GT §6.1 fields are a separate schema. Deferred to a sibling library if/when needed (see §11 Related documents). This RFC covers labels only.
- **Semantic validation of `outcome` values against estimand catalogs** *(v0.2 refinement per Codex round-1 F2/F12; v0.4 status update — GT §9 v0.3 resolves catalog governance.)* API accepts an OPTIONAL `estimand_catalog` parameter (see §4.1). If provided → library hard-rejects outcomes not in the estimand's vocabulary AND enforces GT §7 AP-C5 estimand-version stability. If absent → library skips catalog membership check and emits warning `EstimandCatalogNotConfigured` (per §3.4 W7). Canonical catalog location: [`docs/decisions/dynamic-reliability/estimand_catalog.yaml`](estimand_catalog.yaml) (GT §9 v0.3 resolution — YAML file, PR-review change process, AP-C5 enforced via required `estimand_id` bump on outcome-vocabulary changes). Producer wiring: `EstimandCatalog.load_from_yaml(...)` at validator init.
- **Duplicate-`label_id` detection** — requires state across events. Emission-side deduplication is producer responsibility.
- **Late-arriving-evidence policy** — GT §9 open question. The library accepts corrections with any `correction_reason` from the enum; the "how far back" policy is enforced by producers, not the schema library.
- **Serialization/deserialization** — the library takes a Python `dict` (or a typed dataclass in v0.2+) as input. Wire-format parsing (JSON, Avro, Protobuf) is upstream of the library.
- **Identity-claim resolution semantics** *(v0.2 addition per Codex round-1 F6.)* GT §2.1 requires identity claims be "resolved through the same entity-resolution layer" as source events. Library validates only entry SHAPE (§3.1 `identity_claims` row); the resolution invariant is producer responsibility, verified at label-derivation-service boundaries via integration test (see §7.3).
- **Correction target-label existence** *(v0.2 addition per Codex round-1 F10.)* GT §4 defines `corrects_label_id` as pointing to the label being superseded. Library cannot query the label stream (stateless). Reference existence + composite-key match (`estimand_id + slice + observation_window`) is stream-side projection responsibility (the calibration-consumer projection resolves per GT §4). Library validates reference FORMAT only.
- **Correction append-only enforcement** *(v0.2 addition per Codex round-1 F14.)* GT §4 says "corrections are additive, never mutative". Stateless per-event library cannot enforce append-only across events. Stream-side responsibility (Kafka append-only topic + projection reads most-recent-per-key).
- **Silent-censoring detection** *(v0.2 addition per Codex round-1 F15.)* GT §7 AP-C3 forbids omitting censored labels. Library cannot detect ABSENT events. Producer completeness monitor responsibility — reconciles eligible-prediction-window inventory against emitted labels.
- **Intervention-join completeness** *(v0.2 addition per Codex round-1 F11.)* GT §6.2 requires that when a matching prior intervention exists, the label carries `intervention_present: true` + `intervention_ids`. Library validates the SHAPE when the producer asserts a join (§3.3 CR6); it does not verify the boolean is CORRECT given actual intervention history — that join is producer responsibility, verified via integration test.

### 2.3 Non-goals

- **Not a general-purpose schema validator.** Library is bound to `forge.events.ground_truth.v1` and its correction/censoring variants. If a fifth event stream needs validation, it gets its own library (or the GT library grows a sibling module — decided per case).
- **Not a runtime gate on the label stream itself.** The library runs in the producer, before emission. Consumers of `forge.events.ground_truth.v1` MAY re-validate as a belt-and-suspenders check, but the library is not deployed as a Kafka interceptor or a Flink filter in v0.
- **Not a calibration-eligibility filter.** GT §2.1 rule "calibration measurement uses `eligible` labels only" is enforced by consumers (calibration jobs), not by the schema library. The library accepts all four eligibility values as schema-valid.

---

## 3. Validation rules

### 3.1 GT §2.1 required-field checks (hard reject)

For a candidate event to pass, ALL 11 required fields per GT §2.1 MUST be present and non-null (subject to the two GT-amendment blockers flagged below):

| Field | Type | Notes |
|-------|------|-------|
| `label_id` | string | Non-empty. Uniqueness NOT checked (out of scope §2.2). |
| `estimand_id` | string | Non-empty. If `estimand_catalog` param provided (§4.1), membership + version-stability enforced (per GT §7 AP-C5); otherwise emit W7 `EstimandCatalogNotConfigured` and skip membership. |
| `slice` | object | Full PC §3.5 shape enforced (per GT §2.1 + GT §8 v0.2 worked example): `dimensions` (list, non-empty), `values` (object, non-empty), `slice_id` (string, non-empty) all required. Missing sub-field → `MissingRequiredField(slice.<subfield>)`. *(v0.3 lift — GT §8 worked example was amended in the same PR to use the full PC §3.5 shape, resolving the §2.1/§8 contradiction that AB-030 Codex round-1 F4 surfaced.)* |
| `identity_claims` | list | Shape per SC §3.4 — each entry has `authority`, `key_type`, `value`, plus optional resolution metadata. Resolution invariant out-of-scope (§2.2). |
| `observation_window` | object | `start` and `end` both required, ISO-8601 datetime strings; `end > start` enforced (see §3.3 CR5). |
| `outcome` | string | **Conditionally required per GT §2.1 v0.2:** required when `eligibility == eligible` (non-empty string; vocabulary membership via `estimand_catalog` per `estimand_id` row); MUST be absent when `eligibility == censored / missing_data / manual_ineligible`. Presence on a non-eligible label → reject with `OutcomeUnexpectedOnNonEligible`. Absence on an eligible label → reject with `MissingRequiredField(outcome)`. *(v0.3 lift — GT §2.1 was amended in the same PR to make outcome conditional, resolving the §2.1/§3 contradiction that AB-030 Codex round-1 F3 surfaced.)* |
| `outcome_source` | enum | One of `direct_observation` / `derived` / `manual_correction`. |
| `label_confidence` | enum | One of `certain` / `likely` / `uncertain`. |
| `label_delay` | ISO-8601 duration | Parseable per ISO-8601 duration grammar AND non-negative (`>= PT0S`). Negative or unparseable → reject with `LabelDelayInvalid`. Temporal consistency with emission time: see §3.3 CR7. |
| `eligibility` | enum | One of `eligible` / `censored` / `missing_data` / `manual_ineligible`. |
| `governance_envelope` | object | Shape per SC §3.6 canonical model — every required SC §3.6 field enforced (not just `tenant_id`); enum values checked; nested constraints per SC §3.6. Library imports the SC §3.6 model definition rather than restating a reduced shape. Inheritance semantics out-of-scope (§2.2). |

Missing field → reject with `MissingRequiredField(field_name)`. Type mismatch → reject with `FieldTypeMismatch(field_name, expected, actual)`. Enum violation → reject with `EnumOutOfRange(field_name, value, allowed)`. Conditional-field-presence violations use the specific rules noted per row (e.g., `OutcomeUnexpectedOnNonEligible`).

### 3.2 GT §2.2 provenance-field checks (hard reject)

All three provenance fields MUST be present and non-null:

- `producing_system` — string, non-empty.
- `producing_version` — string, non-empty AND valid SemVer 2.0.0 (per GT §2.2 "semver of the producing system"). Non-semver → reject with `ProducingVersionInvalid(value)`. *(v0.2 change per Codex round-1 F1 — v0.1 accepted build hashes, which contradicted GT §2.2 verbatim; if real producers need non-semver identifiers, GT §2.2 must be amended first via a separate PR.)*
- `logic_ref` — string, non-empty. Scheme is checked as a warning only: recognized schemes are `mlflow://`, `git://`, `https://`, `s3://`, `arn:`. Unrecognized scheme → warn W5 `LogicRefSchemeUnrecognized(scheme)`. Full pointer validity (existence, revision/digest match) NOT enforced (GT §2.2 doesn't currently enumerate the required components; GT amendment can codify later).

Missing any of the three → reject with `ProvenanceIncomplete(missing_fields)`. This mirrors GT §2.2's "a label without provenance is not a label" rule directly.

### 3.3 Cross-field consistency (hard reject)

Rules that require checking multiple fields together:

- **CR1 — Direct observation is certain.** `outcome_source == "direct_observation"` implies `label_confidence == "certain"`. Violation → `DirectObservationMustBeCertain`.
- **CR2 — Manual-ineligible requires reason.** `eligibility == "manual_ineligible"` implies `ineligibility_reason` field present and non-empty. Violation → `ManualIneligibleRequiresReason`.
- **CR3 — Correction event shape.** `outcome_source == "manual_correction"` implies `corrects_label_id`, `correction_reason` (from enum: `misclassified_by_derivation` / `context_missed_by_automated_source` / `late_arriving_evidence` / `disputed_semantics`), and `correction_authority` all present. Violation → `CorrectionEventIncomplete(missing_fields)`. *Presence check only.* Per-estimand accountable-owner attestation (GT §4 "must be attested" + AP-C1) is context-dependent and inherently out of reach for a stateless per-event validator; delegated to the operating model per predictor (VOCABULARY §8 AP-7), verified via integration-test pattern documented in §7.3. Correction target-label existence + composite-key match: see §2.2 out-of-scope entry.
- **CR4 — Censored window is truncated.** `eligibility == "censored"` implies `original_horizon_end` field present (per GT §2.1 v0.2) AND `observation_window.end < original_horizon_end`. Missing field → `MissingRequiredField(original_horizon_end)`. Non-truncated (`observation_window.end >= original_horizon_end`) → `CensoredEventNotTruncated`. *(v0.3 lift — GT §2.1 v0.2 defines `original_horizon_end` canonically for censored labels; the v0.2 interim W8 `CensoredWindowUnverifiable` warning has been deleted.)*
- **CR5 — Observation window ordering.** `observation_window.end > observation_window.start`. Violation → `ObservationWindowInvalid`.
- **CR6 — Intervention-present shape (shape only, not join completeness).** If `intervention_present == true`, `intervention_ids` MUST be a non-empty list. Violation → `InterventionPresentInconsistent`. *(v0.2 change per Codex round-1 F17 — v0.1 also required intervention_ids to be absent/empty when boolean is false; GT §6.2 doesn't specify a false-case representation, so that constraint was invention and has been dropped.)* Join CORRECTNESS (whether the boolean is right given actual intervention history) is out-of-scope (§2.2) — producer responsibility per GT §6.2.
- **CR7 — Emission after window close.** *(v0.2 addition per Codex round-1 F7.)* If the event carries an `emitted_at` field, enforce `emitted_at >= observation_window.end` (labels cannot be emitted before the observation window closes, per GT §3 "no label can exist until the observation window closes"). Violation → `EmittedBeforeWindowClosed`. If `emitted_at` absent, skip; producer responsibility for supplying emission timestamp.

### 3.4 Warnings (accept-with-warnings)

Advisory issues that don't reject but surface for consumer attention. Warnings NEVER block emission. Producers log warnings to their observability sink; the validator returns them in `ValidationResult.warnings`.

- **W1 — Long label delay.** `label_delay > <configured_threshold>`. Warn: `LabelDelayExceedsThreshold(threshold)`. *(v0.2 change per Codex round-1 F19 — v0.1 hard-coded `PT1H` which was invention; threshold is now a validator config parameter, default `None` (no default warning). Producers/platform team configure per-slice.)* Rationale: GT §2.1 acknowledges "long delays affect calibration cadence" without specifying a number.
- **W2 — Correction reason surfaced for observability.** `outcome_source == "manual_correction"` implies observability tag for consumer filtering. Warn: `CorrectionReasonSurfaced(reason)`. *(v0.2 change per Codex round-1 F20 — v0.1 warned only on `disputed_semantics` with an editorial "signals estimand drift" gloss; both the selective focus and the interpretation were invention. Now a pass-through observability tag on all correction events, no interpretation.)*
- *(W3 `GovernanceEnvelopeMinimal` DELETED in v0.4 — SC §3.6 defines 8 required sub-fields; §3.1 `governance_envelope` row already hard-rejects on any missing SC §3.6 required field. A label with only `tenant_id` was never actually reachable to the warning path — it fails 7 hard-reject checks first. W3 is redundant. The W3 error code is retired and MUST NOT be reused for a different rule per §4.3 error-code stability contract.)*
- **W4 — Derived outcome uncertain.** *(v0.2 addition per Codex round-1 F16.)* `outcome_source == "derived"` AND `label_confidence == "uncertain"` → warn `DerivedOutcomeUncertain`. Rationale: GT §7 AP-C4 identifies this pair as unsafe for ordinary calibration. Event stays schema-valid; consumers filter or opt in per their calibration protocol.
- **W5 — Logic-ref scheme unrecognized.** *(v0.2 addition per Codex round-1 F13; v0.4 status update — GT §2.2 v0.3 amendment now codifies the canonical scheme list.)* Emitted from §3.2 when `logic_ref` scheme is outside `{mlflow://, git://, https://, s3://, arn:}` (per GT §2.2). Warn `LogicRefSchemeUnrecognized(scheme)`. **Upgrades to hard-reject at library v1** — kept as warning through library v0 to allow producer migration. New schemes may be added via GT §2.2 amendment PR.
- **W6 — Intervention IDs unusually large.** *(v0.2 addition per Codex round-1 F18; v0.4 status update — GT §6.2 v0.3 amendment codifies canonical bound = 10 + element constraints.)* If `len(intervention_ids) > 10` (per GT §6.2 canonical bound), warn `InterventionIdsUnusuallyLarge(count, bound=10)`. Element constraints (non-empty string, `intv_<timestamp>_<hash>` format, uniqueness) enforced per GT §6.2 as separate hard-reject in §3.3 CR6. **Upgrades to hard-reject at library v1** — kept as warning through library v0 to allow producer migration.
- **W7 — Estimand catalog not configured.** *(v0.2 addition per Codex round-1 F2/F12.)* Emitted from §3.1 `estimand_id` row when `estimand_catalog` param is absent from validator call. Warn `EstimandCatalogNotConfigured`. Producer opts in by wiring the catalog per §4.1.
- *(W8 `CensoredWindowUnverifiable` deleted in v0.3 — GT §2.1 v0.2 now requires `original_horizon_end` on censored labels, so §3.3 CR4 hard-rejects missing/non-truncated cases; no warning-tier needed. The W8 error code is retired and MUST NOT be reused for a different rule per §4.3 error-code stability contract.)*

### 3.5 Unknown-field policy (closed-world default)

*(v0.2 addition per Codex round-1 F22 — v0.1 didn't decide open- vs. closed-world.)*

- **Default:** closed-world. Unknown top-level fields → warn `UnknownField(name)` (not reject). This surfaces typos and accidentally-included keys to observability without blocking emission.
- **Reserved extension namespace:** keys prefixed `x_` are producer-owned extensions and skip the warning. Producers use this for observability-only fields (e.g., `x_git_sha`, `x_deploy_id`) that aren't part of GT §2.1 but are useful in downstream projections.
- **Forward compatibility:** future GT versions may add fields. Library upgrade lands the new field in §3.1 with a MINOR bump per §5.2; producers upgrade at their own pace during the deprecation window.
- **Correction-only fields** (`corrects_label_id`, `correction_reason`, `correction_authority`, `original_horizon_end`, `ineligibility_reason`, `emitted_at`) are known conditional fields — not warned even when the triggering condition (e.g., `outcome_source == manual_correction`) is absent.

---

## 4. API surface

### 4.1 Signature

```python
from forge_works.dr.label_schema_validator import (
    validate_label_event,
    ValidationResult,
    EstimandCatalog,
    ValidatorConfig,
)

def validate_label_event(
    event: dict | LabelEvent,
    estimand_catalog: EstimandCatalog | None = None,
    config: ValidatorConfig | None = None,
) -> ValidationResult:
    ...
```

Single function. Synchronous. Stateless (the catalog and config are caller-owned; the validator does not cache or mutate). No I/O.

- **`estimand_catalog`** *(v0.2 addition per Codex round-1 F2/F12)* — optional; when provided, enables outcome-vocabulary membership check + estimand-version pinning (per GT §7 AP-C5). When absent, library emits W7 `EstimandCatalogNotConfigured` and skips those checks. Catalog governance mechanism itself remains out of scope (GT §9 open question) but the API is ready for it.
- **`config`** *(v0.2 addition)* — optional; validator config carrying thresholds (W1 `label_delay_warning_threshold`, W6 `intervention_ids_soft_bound`) and feature toggles. Default `ValidatorConfig()` uses safe defaults (no delay warning, W6 threshold = 10).

### 4.2 Return shape

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool                          # True iff no hard-reject errors
    errors: tuple[ValidationError, ...]     # empty when is_valid=True
    warnings: tuple[ValidationWarning, ...] # may be non-empty regardless of is_valid
    library_version: str                    # library semver, e.g. "0.2.0"
    contract_revision: str                  # GT contract revision, e.g. "v1"
                                            # (matches forge.events.ground_truth.v1)
```

*(v0.2 changes per Codex round-1 F23 + F24 — `validated_at` removed (reading the clock in a pure result was impure and contradicted §7.2's idempotence property; audit timestamp belongs at emission-log time, producer responsibility). `schema_version` split into `library_version` + `contract_revision` so consumers pinning on either can tell which changed at MAJOR bump.)*

Producers pattern-match on `is_valid` for emit-vs-drop; log both `errors` and `warnings` to the observability sink alongside the emitted event for downstream audit.

### 4.3 Error contract

`ValidationError` and `ValidationWarning` are typed subclasses (per rule name in §3.1–§3.4). Each carries a `code` (kebab-case, stable across versions), `message` (human-readable, may change), and `field_path` (JSONPath-like, e.g., `slice.values.per_service`).

The `code` values are the stability contract — consumers that pin behavior to specific error codes get semver protection (MAJOR bump if a code is removed or its meaning changes; MINOR bump if a new code lands with a deprecation window on any older overlapping rule).

---

## 5. Distribution and versioning

### 5.1 Package layout

- Import path: `forge_works.dr.label_schema_validator`
- Repository location: `src/python/forge_works/dr/label_schema_validator/` (new subpackage under existing `src/python/`; sibling to other dynamic-reliability libraries as they land).
- Test location: `tests/python/forge_works/dr/label_schema_validator/`.
- Package metadata: single `pyproject.toml` entry under the existing monorepo Python package.

### 5.2 Semver policy

The library carries two version numbers (per `ValidationResult`, §4.2): `library_version` (this package's semver) and `contract_revision` (the GT contract revision the library enforces).

- **`library_version` MAJOR** — a previously-passing event now hard-rejects, OR an error `code` is removed / redefined. Requires: 90-day deprecation window announced in `CHANGELOG.md` + explicit ratification in the AB-030 backlog entry.
- **`library_version` MINOR** — a new hard-reject rule lands, gated behind an off-by-default flag for the deprecation window; auto-enables at the announced MAJOR boundary. Also: new warnings, new optional API parameters, new error codes with a deprecation window on any older overlapping rule.
- **`library_version` PATCH** — internal refactors, docstring changes, warning-message-text improvements. No behavior change to hard-rejects, warnings, or error codes.
- **`contract_revision`** — matches the GT stream suffix (`forge.events.ground_truth.v1` → `contract_revision: "v1"`). Bumps only when GT introduces a wire-incompatible schema change (a new stream suffix). Library ships alongside the GT amendment PR per §5.3.

### 5.3 Change process

Any change to `§3 Validation rules` in this RFC (or to GT §2.1/§2.2/§3/§5) MUST land as a coordinated pair: the GT contract patch and the library patch ship in the same PR, or the earlier lands with an explicit `pending_library_upgrade: AB-030` note in `CHANGELOG.md`. Producers pin the library version; upgrades are opt-in during the deprecation window and mandatory at the MAJOR boundary.

---

## 6. Failure semantics

- **Hard reject (§3.1, §3.2, §3.3)** — `is_valid: False`. Producer MUST NOT emit the event. Producer logs the errors to observability sink AND to a producer-owned "invalid-label" sink (retained for 90 days) so schema-drift is diagnosable without archaeology.
- **Warn (§3.4)** — `is_valid: True`. Producer MAY emit; warnings surface to observability. Consumers (calibration jobs, drift monitors) MAY filter on warning presence but MUST NOT reject events on warnings alone.
- **Library crash** — if `validate_label_event` itself throws (bug in the library), producer MUST NOT emit and MUST alert. Fail-closed on library bugs, per the AP-C4 spirit ("derivation as ground truth" — a broken validator is worse than a strict validator).

Consumer-side: consumers of `forge.events.ground_truth.v1` MAY re-validate. If a consumer-side re-validation rejects an event that its producer accepted, that's a version-mismatch incident (both sides log; alert to owning team). This is NOT expected under normal operation.

---

## 7. Test criteria

### 7.1 Conformance test suite

*(v0.3 fixture-count update reflects: v0.2 round-1 additions — CR7 + W4/W5/W6/W7, F1 semver, F5 SC §3.6 canonical, F7 label_delay non-negative, F17 CR6 rewording; PLUS v0.3 GT-amendment additions — 3 new fixture groups for F3 outcome-conditional, F4 slice full-shape, F8 censored-label schema hard-reject cases. W8 was retired in v0.3 and is not tested.)*

- **Golden happy paths** — one per `outcome_source` × `eligibility` combination (12 events), each fully-populated per §3, all pass with zero warnings (with `estimand_catalog` provided to suppress W7).
- **Missing-field rejects** — 11 events, each dropping one GT §2.1 unconditionally-required field; each rejects with the corresponding `MissingRequiredField`. Conditional fields (F3 `outcome`, F4 `slice` sub-fields, F8 `original_horizon_end`) tested in their own fixture groups below.
- **Conditional-field rules (F3 outcome-eligibility interaction)** — 4 events: (a) `eligibility: eligible` with outcome → passes; (b) `eligibility: eligible` without outcome → `MissingRequiredField(outcome)`; (c) `eligibility: censored` without outcome → passes; (d) `eligibility: censored` WITH outcome → `OutcomeUnexpectedOnNonEligible`.
- **Slice full-shape (F4)** — 3 events, each dropping one of `slice.dimensions` / `slice.values` / `slice.slice_id`; each rejects with the corresponding `MissingRequiredField(slice.<subfield>)`.
- **Censored-label schema (F8)** — 3 events: (a) `eligibility: censored` with `original_horizon_end > observation_window.end` → passes; (b) `eligibility: censored` without `original_horizon_end` → `MissingRequiredField(original_horizon_end)`; (c) `eligibility: censored` with `original_horizon_end <= observation_window.end` → `CensoredEventNotTruncated`.
- **Provenance-incomplete rejects** — 3 events, each dropping one GT §2.2 provenance field; each rejects with `ProvenanceIncomplete`.
- **Semver enforcement** — 2 events with malformed `producing_version` (non-semver build hash, empty); each rejects with `ProducingVersionInvalid`.
- **Governance envelope full-shape** — N events (N = required-field count of SC §3.6) each dropping one SC §3.6 required field; each rejects with the corresponding `MissingRequiredField`.
- **`label_delay` non-negative** — 1 event with negative duration; rejects with `LabelDelayInvalid`.
- **Cross-field violations** — 7 events, one per CR1, CR2, CR3, CR4 (covered by "Censored-label schema (F8)" fixture group above), CR5, CR6, CR7; each rejects with the corresponding typed error.
- **CR7 absent variant** — 1 event with no `emitted_at`; passes (CR7 skipped).
- **Warning triggers** — 6 events, one per W1 (with configured threshold), W2, W4 (`derived + uncertain`), W5 (`logic_ref: ftp://…`), W6 (`intervention_ids` count > 10), W7 (no catalog); each passes with the corresponding warning. *(W3 was deleted in v0.4 as redundant; W8 was deleted in v0.3; neither tested.)*
- **Unknown-field policy** — 3 events: (a) event with `x_git_sha` → passes with zero warnings; (b) event with `typo_field` → passes with `UnknownField(typo_field)`; (c) event with correction-only field on a non-correction event → not warned per §3.5 exception list.
- **Estimand catalog** — 4 events: (a) valid outcome in catalog → passes; (b) outcome not in catalog → rejects with `OutcomeNotInVocabulary`; (c) estimand_id references different version semantics than catalog → rejects with `EstimandVersionMismatch` (AP-C5); (d) catalog absent → passes with W7.

### 7.2 Property tests (hypothesis-driven)

*(v0.2 rewrite per Codex round-1 F25 — v0.1's first property was trivially weak (elided type/enum/shape/temporal/reference checks); now grounded in canonical schema generation.)*

- **P1 — Schema-generated events pass.** Generate events from the canonical schema union (SC §3.6 governance envelope + PC §3.5 slice + GT §2.1 field types + GT §2.2 provenance); every schema-conformant event → `is_valid: True` with zero errors.
- **P2 — Mutate one invariant at a time.** Take a schema-generated valid event; mutate exactly one invariant (drop a required field / flip an enum out of range / negate a duration / break cross-field consistency); assert the validator rejects with the SPECIFIC typed error corresponding to the mutation.
- **P3 — Idempotence (literal equality).** `validate_label_event(event, catalog, config)` is idempotent — repeated calls with the same inputs return equal `ValidationResult` (literal equality, no `modulo` — `validated_at` was removed per §4.2 v0.2 change).
- **P4 — Error-code stability golden file.** Every typed error and warning code emitted by the library corresponds to a fixture in a golden file. Adding a new code → MINOR bump AND golden-file update in the same PR. Removing or renaming a code → MAJOR bump per §5.2 (change process gate).

### 7.3 AB-028 spike integration test

The spike's `label_derivation_service` (v0 build) imports the library and calls `validate_label_event` before each emission. Integration test: spike test-mode run against a fixture of 100 historical deploy events produces 100 valid label events with zero rejects. Any reject during spike run means the deriver is emitting non-conformant events — spike halts, fixed before real emission begins.

---

## 8. Deliverables

- Library code at `src/python/forge_works/dr/label_schema_validator/` per §5.1.
- Test suite at `tests/python/forge_works/dr/label_schema_validator/` covering §7.1 + §7.2.
- Integration hook in AB-028 spike deriver (delivered as part of AB-028, not AB-030; AB-030 ships the library, AB-028 wires the call).
- CHANGELOG entry under `### Added` for library shipping.
- Backlog entry AC line 441 flipped from `[ ]` to `[x]` when library is imported by at least one producer.
- Sibling reference added to GT §11 Related documents pointing back at this RFC.

---

## 9. Risks

- **R1 — Schema drift between GT contract and library.** If a GT §2 patch lands without a library patch, producers emit events that pass old library but violate new contract. Mitigation: §5.3 change process — coordinated PRs or explicit `pending_library_upgrade` marker.
- **R2 — Library becomes a chokepoint.** Every label producer imports this library; a bug ships to everyone. Mitigation: §5.2 semver + deprecation windows + strict test suite § 7 + fail-closed on library crash (§6).
- **R3 — Under-specification.** This RFC enumerates 6 cross-field rules and 3 warnings; GT §2 has more implicit constraints (e.g., what does "identity claims resolved through the same entity-resolution layer" mean for validation?). Mitigation: v0.1 ships the enumerated rules; gaps surface via producer feedback and become v0.2 additions.
- **R4 — Governance envelope validation split (shape here, inheritance elsewhere).** Producers may forget the inheritance side. Mitigation: producer-side lint or a sibling library — filed as GT §11 v1 graduation criterion, tracked in AB-030 backlog entry AC.

---

## 10. Timeline (indicative — not committed)

- **T + 0:** Scoping-approval on this RFC. §3 validation rules and §4 API surface locked; §5–§7 refinements permitted.
- **T + 1w:** v0.1.0 library implementation + §7.1 conformance suite.
- **T + 2w:** §7.2 property tests + AB-028 spike integration hook.
- **T + 3w:** v0.1.0 tagged; AB-028 spike deriver imports library; §7.3 integration test passes on historical fixture.

Timeline is indicative. AB-028 spike execution unblocks at T + 3w or when v0.1.0 tags — whichever is later.

---

## 11. Related documents

- [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) *(v0.1)* — the source-of-truth contract for §2.1 required fields, §2.2 provenance, §3 eligibility, §5 censoring, §7 anti-patterns. Every rule in §3 of this RFC traces to a GT section.
- [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) *(v0.2)* — the first consumer. §3 Schema-conformance block delegates label validation to this library; spike halts with `blocked_on: AB-030` if library is not available.
- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) *(v0.1)* — labels are the ground truth against which PC predictions are calibrated. `estimand_id` field connects both.
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) *(v0.1)* — `identity_claims` (SC §3.4) and `governance_envelope` (SC §3.6) shapes are shared with labels.
- [`README.md`](README.md) — corpus index. AB-030 to be added to the in-flight-spike RFCs table on scoping-approval.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-030 entry tracks this RFC's shipping status.

---

## 12. Provenance

- **2026-07-28:** v0.1 draft. Codex round-2 loop on AB-028 spike RFC (F19, 2026-07-26) delegated the label-schema-validation-library concern to AB-030; this RFC scopes that library specifically (distinct from AB-030's broader GT v0 → v1 lifecycle in the backlog entry). Base commit: `fac4ea8` (same precedent as AB-028 and AB-033 branches — dedupes on rebase when corpus lands on main via PR #16 or another PR).
- **2026-07-28:** v0.2 — Codex round-1 critique loop applied (audit trail at `research/feedback_loops/dynamic-reliability-AB-030_LABEL_SCHEMA_VALIDATOR/20260728T070856Z/` — local-only) returned `needs-revision` with 12 HIGH / 13 MEDIUM / 0 LOW findings. Over-concession review flagged 7 corrections (F19/F20/F21 softened warnings; F2/F12/F13/F18 shifted from GT-blockers to API refinements via optional `estimand_catalog` param + new warnings W5/W6). Twenty of twenty-five findings applied in-place; 3 remain GT-amendment blockers (F3 outcome-conditional presence, F4 slice-shape §2.1/§8 contradiction, F8 invented `original_horizon_end`) — filed as §13 v0.2 → v1 acceptance criteria. Two partial agreements (F9 correction_authority attestation, F10 corrects_label_id resolution) codified as explicit §2.2 out-of-scope entries with delegation to producer + integration test.
- **2026-07-29:** v0.3 — GT contract amendments landed in coordinated PR (per §5.3 change process). §3.1 `outcome` and `slice` rows locked to canonical GT-defined rules (F3 + F4); §3.3 CR4 locked to hard-reject on missing / non-truncated `original_horizon_end` (F8); §3.4 W8 `CensoredWindowUnverifiable` deleted (no longer needed); §7.1 conformance fixtures updated with 3 new fixture groups covering F3/F4/F8 hard-reject cases; §13 v0.2 → v1 acceptance criteria for F3/F4/F8 flipped to `[x]`. Zero new API surface changes; zero new warnings. Coordinated GT v0.1 → v0.2 patches: §2.1 conditional-field split (`outcome` conditional on eligibility, `original_horizon_end` conditional on censored, `ineligibility_reason` conditional on manual_ineligible); §3 conditional-field summary table; §5 censored-label schema shape + worked example; §8 worked-example slice expansion.
- **2026-07-29 (afternoon):** v0.4 — 4 non-GT v0.3 → v1 items resolved in coordinated PR with GT v0.2 → v0.3 amendments. (i) §3.4 W3 `GovernanceEnvelopeMinimal` DELETED — redundant with §3.1 SC §3.6 full-shape enforcement (unreachable warning path); error code retired per §4.3. (ii) §3.4 W5 `LogicRefSchemeUnrecognized` status updated — GT §2.2 v0.3 codifies canonical scheme list; W5 upgrades to hard-reject at library v1. (iii) §3.4 W6 `InterventionIdsUnusuallyLarge` status updated — GT §6.2 v0.3 defines bound = 10 + element constraints; W6 upgrades to hard-reject at library v1. (iv) §2.2 estimand-catalog out-of-scope entry updated — GT §9 v0.3 resolves governance via YAML catalog at [`estimand_catalog.yaml`](estimand_catalog.yaml); catalog seeded with `deploy_slo_breach_60m_association_v0`. §7.1 warning-triggers fixture count reduced 7 → 6 (W3 deleted). §13 v0.3 → v1 acceptance criteria for these 4 items flipped to `[x]`. Zero AB-030 blockers remain on GT contract side; remaining v1 item is AB-028 spike integration test.

---

## 13. v0.4 → v1 acceptance criteria

*(v0.2 filed 3 GT-amendment prerequisites (F3/F4/F8); v0.3 landed those amendments and lifted the interim rules. v0.4 resolved the 4 remaining non-GT v0.3 → v1 items (W3 confirm-or-drop, `logic_ref` schemes, `intervention_ids` bound, estimand catalog governance). Only remaining v1 item: AB-028 spike integration.)*

- [x] **GT §2.1 amendment — outcome conditional presence (F3).** LANDED 2026-07-29. GT §2.1 v0.2 makes `outcome` conditionally required (present iff `eligibility == eligible`); §3 gained a conditional-field summary table. RFC §3.1 `outcome` row locked; new fixture group added to §7.1.
- [x] **GT §2.1 amendment — slice shape reconciliation (F4).** LANDED 2026-07-29. GT §8 v0.2 worked example expanded to full PC §3.5 shape (`dimensions` + `values` + `slice_id`). RFC §3.1 `slice` row locks to full-shape enforcement.
- [x] **GT §2.1 + §5 amendment — censored-label schema completion (F8).** LANDED 2026-07-29. GT §2.1 v0.2 defines `original_horizon_end` as conditionally required (present iff `eligibility == censored`); GT §5 documents the truncation rule + worked example. RFC §3.3 CR4 locked to hard-reject; W8 `CensoredWindowUnverifiable` deleted.

Other v0.3 → v1 items (non-blocking on GT):

- [x] **W3 confirm-or-drop** — RESOLVED 2026-07-29 v0.4: SC §3.6 requires 8 sub-fields; §3.1 hard-reject on missing SC §3.6 field already covers the "envelope has only tenant_id" case. W3 was redundant. DELETED (error code retired per §4.3 stability contract).
- [x] **Estimand catalog governance** (GT §9) — RESOLVED 2026-07-29 v0.4: GT §9 v0.3 amendment defines canonical YAML catalog at `docs/decisions/dynamic-reliability/estimand_catalog.yaml`, PR-review change process, AP-C5 enforced via required `estimand_id` bump on outcome-vocabulary changes. Catalog seeded with one entry (`deploy_slo_breach_60m_association_v0`). §2.2 out-of-scope entry updated with the canonical location + API wiring pattern.
- [x] **`logic_ref` scheme enumeration** (GT §2.2 amendment, per Codex round-1 F13) — RESOLVED 2026-07-29 v0.4: GT §2.2 v0.3 amendment codifies `{mlflow://, git://, https://, s3://, arn:}`. §3.4 W5 status note updated: "upgrades to hard-reject at library v1".
- [x] **`intervention_ids` bound** (GT §6.2 amendment, per Codex round-1 F18) — RESOLVED 2026-07-29 v0.4: GT §6.2 v0.3 amendment defines canonical bound = 10 + element constraints (non-empty string, `intv_<timestamp>_<hash>` format, uniqueness). §3.4 W6 status note updated: "upgrades to hard-reject at library v1".
- [ ] AB-028 spike deriver has integrated the library (per §8 deliverables + §7.3 integration test) and confirmed no library-side rejects on production-representative fixtures.

---

## 14. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval (v0.2 → v1), this RFC becomes the contract for the shipped library; changes to library behavior require RFC amendments.
- On library v1.0.0, the RFC content folds into the library's own docstring / package README; this file may be superseded and archived under `research/` at that time.
