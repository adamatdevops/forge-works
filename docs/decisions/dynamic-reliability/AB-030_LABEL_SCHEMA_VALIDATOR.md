# AB-030 Label Schema Validator Scoping RFC (v0.1 draft) — shared library for `forge.events.ground_truth.v1` conformance

> **Status:** Scoping draft (v0.1 — pre-Codex-loop). Not yet approved for build. Approval means: the API surface, validation rules, and distribution model are locked and the library may be implemented.
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

- **Governance envelope INHERITANCE validation** — the library validates shape, not "did this label inherit the strictest envelope from its inputs" (that requires input-event access, which is producer-side). Filed as GT §11 v1 graduation criterion, not this library's problem.
- **Intervention event validation** — GT §6.1 fields are a separate schema. Deferred to a sibling library if/when needed (see §11 Related documents). This RFC covers labels only.
- **Semantic validation of `outcome` values against estimand catalogs** — the library validates that `outcome` is present and a string; it does NOT verify the string is a member of the estimand's declared outcome vocabulary. That check requires estimand-catalog access, which is a v1-era governance surface (GT §9 open question).
- **Duplicate-`label_id` detection** — requires state across events. Emission-side deduplication is producer responsibility.
- **Late-arriving-evidence policy** — GT §9 open question. The library accepts corrections with any `correction_reason` from the enum; the "how far back" policy is enforced by producers, not the schema library.
- **Serialization/deserialization** — the library takes a Python `dict` (or a typed dataclass in v0.2+) as input. Wire-format parsing (JSON, Avro, Protobuf) is upstream of the library.

### 2.3 Non-goals

- **Not a general-purpose schema validator.** Library is bound to `forge.events.ground_truth.v1` and its correction/censoring variants. If a fifth event stream needs validation, it gets its own library (or the GT library grows a sibling module — decided per case).
- **Not a runtime gate on the label stream itself.** The library runs in the producer, before emission. Consumers of `forge.events.ground_truth.v1` MAY re-validate as a belt-and-suspenders check, but the library is not deployed as a Kafka interceptor or a Flink filter in v0.
- **Not a calibration-eligibility filter.** GT §2.1 rule "calibration measurement uses `eligible` labels only" is enforced by consumers (calibration jobs), not by the schema library. The library accepts all four eligibility values as schema-valid.

---

## 3. Validation rules

### 3.1 GT §2.1 required-field checks (hard reject)

For a candidate event to pass, ALL 11 required fields per GT §2.1 MUST be present and non-null:

| Field | Type | Notes |
|-------|------|-------|
| `label_id` | string | Non-empty. Uniqueness NOT checked (out of scope §2.2). |
| `estimand_id` | string | Non-empty. Membership in an estimand catalog NOT checked (out of scope §2.2). |
| `slice` | object | Shape per PC §3.5 — `dimensions`, `values`, `slice_id` all required. |
| `identity_claims` | list | Shape per SC §3.4 — each entry has `authority`, `key_type`, `value`, plus optional resolution metadata. |
| `observation_window` | object | `start` and `end` both required, ISO-8601 datetime strings; `end > start` enforced. |
| `outcome` | string | Non-empty. Vocabulary membership NOT checked (out of scope §2.2). |
| `outcome_source` | enum | One of `direct_observation` / `derived` / `manual_correction`. |
| `label_confidence` | enum | One of `certain` / `likely` / `uncertain`. |
| `label_delay` | ISO-8601 duration | Parseable per ISO-8601 duration grammar. |
| `eligibility` | enum | One of `eligible` / `censored` / `missing_data` / `manual_ineligible`. |
| `governance_envelope` | object | Shape per SC §3.6 — `tenant_id` required; other fields optional. |

Missing field → reject with `MissingRequiredField(field_name)`. Type mismatch → reject with `FieldTypeMismatch(field_name, expected, actual)`. Enum violation → reject with `EnumOutOfRange(field_name, value, allowed)`.

### 3.2 GT §2.2 provenance-field checks (hard reject)

All three provenance fields MUST be present and non-null:

- `producing_system` — string, non-empty.
- `producing_version` — string, non-empty. Semver parseability NOT enforced (producers may use build hashes).
- `logic_ref` — string, non-empty. URL parseability NOT enforced (producers may use `mlflow://` or other schemes).

Missing any of the three → reject with `ProvenanceIncomplete(missing_fields)`. This mirrors GT §2.2's "a label without provenance is not a label" rule directly.

### 3.3 Cross-field consistency (hard reject)

Rules that require checking multiple fields together:

- **CR1 — Direct observation is certain.** `outcome_source == "direct_observation"` implies `label_confidence == "certain"`. Violation → `DirectObservationMustBeCertain`.
- **CR2 — Manual-ineligible requires reason.** `eligibility == "manual_ineligible"` implies `ineligibility_reason` field present and non-empty. Violation → `ManualIneligibleRequiresReason`.
- **CR3 — Correction event shape.** `outcome_source == "manual_correction"` implies `corrects_label_id`, `correction_reason` (from enum), and `correction_authority` all present. Violation → `CorrectionEventIncomplete(missing_fields)`.
- **CR4 — Censored window is truncated.** `eligibility == "censored"` implies `original_horizon_end` field present AND `observation_window.end < original_horizon_end`. Violation → `CensoredEventNotTruncated`.
- **CR5 — Observation window ordering.** `observation_window.end > observation_window.start`. Violation → `ObservationWindowInvalid`.
- **CR6 — Intervention-present shape.** If `intervention_present == true`, `intervention_ids` MUST be a non-empty list; if `intervention_present == false`, `intervention_ids` MUST be absent or empty. Violation → `InterventionPresentInconsistent`.

### 3.4 Warnings (accept-with-warnings)

Advisory issues that don't reject but surface for consumer attention:

- **W1 — Long label delay.** `label_delay > PT1H`. Warn: `LabelDelayExceedsOneHour`. Rationale: GT §2.1 note "long delays affect calibration cadence."
- **W2 — Correction reason is `disputed_semantics`.** Warn: `CorrectionSemanticsDisputed`. Rationale: this reason is a signal of estimand-definition drift; calibration consumers may want to segregate.
- **W3 — Governance envelope has only `tenant_id`.** Warn: `GovernanceEnvelopeMinimal`. Rationale: SC §3.6 recommends richer envelopes; label with only `tenant_id` is schema-valid but sparse.

Warnings NEVER block emission. Producers log warnings to their observability sink; the validator returns them in `ValidationResult.warnings`.

---

## 4. API surface

### 4.1 Signature

```python
from forge_works.dr.label_schema_validator import validate_label_event, ValidationResult

def validate_label_event(event: dict | LabelEvent) -> ValidationResult:
    ...
```

Single function. Synchronous. Stateless. No I/O.

### 4.2 Return shape

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool                          # True iff no hard-reject errors
    errors: tuple[ValidationError, ...]     # empty when is_valid=True
    warnings: tuple[ValidationWarning, ...] # may be non-empty regardless of is_valid
    schema_version: str                     # library semver at check time, e.g. "0.1.0"
    validated_at: datetime                  # UTC ISO-8601, for audit
```

Producers pattern-match on `is_valid` for emit-vs-drop; log both `errors` and `warnings` to the observability sink with the emitted event for downstream audit.

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

- **MAJOR** — a previously-passing event now hard-rejects. Requires: 90-day deprecation window announced in `CHANGELOG.md` + explicit ratification in the AB-030 backlog entry.
- **MINOR** — a new hard-reject rule lands, gated behind an off-by-default flag for the deprecation window; auto-enables at the announced MAJOR boundary.
- **PATCH** — new warnings, internal refactors, docstring changes, message-text improvements. No behavior change to hard-rejects.

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

- **Golden happy paths** — one per `outcome_source` × `eligibility` combination (12 events), each fully-populated per §3, all pass with zero warnings.
- **Missing-field rejects** — 11 events, each dropping one GT §2.1 required field; each rejects with the corresponding `MissingRequiredField`.
- **Provenance-incomplete rejects** — 3 events, each dropping one GT §2.2 provenance field; each rejects with `ProvenanceIncomplete`.
- **Cross-field violations** — 6 events, one per CR1–CR6; each rejects with the corresponding typed error.
- **Warning triggers** — 3 events, one per W1–W3; each passes with the corresponding warning.

### 7.2 Property tests (hypothesis-driven)

- Any event with all 11 required fields + 3 provenance fields present and cross-field-consistent → `is_valid: True`.
- Any event missing any required field → `is_valid: False`.
- `validate_label_event` is idempotent — repeated calls on the same event return equal `ValidationResult` (modulo `validated_at`).

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

---

## 13. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval, this RFC becomes the contract for the shipped library; changes to library behavior require RFC amendments.
- On library v1.0.0, the RFC content folds into the library's own docstring / package README; this file may be superseded and archived under `research/` at that time.
