# Ground-Truth + Intervention Contract (v0) — What Reality Says Happened

> **Status:** Design stub (v0). Drafted 2026-07-24 in response to Codex round-1 loop findings F3 + F10 flagging that deferring this schema blocks calibration, drift measurement, retraction, and any credible baseline comparison.
> **Origin:** Sibling of `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` and `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md`. Referenced from PREDICTION_CONTRACT §6.2, §8, §9 AP-6.
> **Location note:** Migrated 2026-07-25 from `planning/GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` to this tracked path — see `docs/decisions/dynamic-reliability/README.md` for the corpus index.
> **Scope:** the label stream (what really happened) and the intervention stream (what actions were taken because of predictions). Together they enable calibration, drift detection, retraction, and treatment-aware evaluation. Not the model architecture, not the wire format — those live in their own siblings.
> **Blocking status:** without this doc at v0, `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md` cannot graduate to v1 (its graduation criterion §11 lists this doc explicitly). AB-030 tracks the completion (backlog entry local per repo convention; summary in the README).

---

## 1. Why this doc exists

Predictions are only useful if they can be scored against reality. A model that emits `at_risk` predictions with no downstream mechanism to observe whether the predicted outcome occurred is a model that:

- Cannot be calibrated (§3 of PC).
- Cannot detect drift (§8 of PC).
- Cannot be retracted (§5 of PC — retraction requires knowing you were wrong).
- Cannot be compared against a deterministic baseline (AB-028 blocker).
- Cannot be evaluated for treatment effect vs. base rate (AP-6 counterfactual protocol).

Every one of those capabilities depends on **ground-truth events**: a separate event stream that says "here's what actually happened" for each predicted eligible slice.

Predictions ALSO cause actions in v1+ (T3/T4 doctrine). Those actions distort the ground truth — an auto-rollback triggered by an `at_risk` prediction changes whether the SLO breach *would have* occurred. That's the counterfactual problem (AP-6). The **intervention stream** carries what was done, when, and by whom (human or automated).

Both streams need contracts. Otherwise ground truth arrives as an ad-hoc mess and treatment-effect estimation is impossible.

---

## 2. The label stream contract (`forge.events.ground_truth.v1`)

**Purpose:** carry authoritative "here's what actually happened" events, joinable to predictions via identity claims + slice + time window.

### 2.1 Required fields per label event

- `label_id` — unique per emission. Immutable.
- `estimand_id` — which estimand this label is FOR. Every estimand (per PREDICTION_CONTRACT §3.0) has a stable identifier; labels carry it so the label stream doesn't need to guess which prediction it validates.
- `slice` — same `dimensions` / `values` / `slice_id` shape as PREDICTION_CONTRACT §3.5. The label applies to this slice.
- `identity_claims` — same shape as SC §3.4. Labels carry the same namespaced identity claims as source events, resolved through the same entity-resolution layer.
- `observation_window` — the wall-clock window during which the outcome was observed (`start`, `end`).
- `outcome` — the observed outcome, drawn from the estimand's namespaced outcome vocabulary (e.g., for the deploy-SLO-breach estimand: `slo_breach_occurred` / `slo_breach_absent`).
- `outcome_source` — how the outcome was determined:
  - `direct_observation` — the outcome was directly observed on the source stream (e.g., a `datadog.slo_burning` event during the window).
  - `derived` — the outcome was computed from other events (e.g., "no SLO events during window AND no incident opened" → `slo_breach_absent`).
  - `manual_correction` — a human explicitly labeled the outcome (see §4).
- `label_confidence` — for `derived` outcomes, how certain the derivation is (`certain` / `likely` / `uncertain`). Direct observations are always `certain`.
- `label_delay` — time from `observation_window.end` to `label_id` emission. Long delays affect calibration cadence.
- `eligibility` — per §3.
- `governance_envelope` — same shape as SC §3.6; label events inherit the strictest governance from any input.

### 2.2 Label provenance

Every label event MUST carry:
- `producing_system` — what emitted the label (a Flink job that watches `datadog.*` for slo_burning events; a manual-correction service; a specific integration).
- `producing_version` — semver of the producing system.
- `logic_ref` — pointer to the exact rule/query/model that produced the label. Enables audit.

**Rule:** a label without provenance is not a label. Consumers reject.

---

## 3. Eligibility — not every prediction gets a label

A prediction is *eligible for evaluation* only if a matching label event can exist. Non-eligibility is a first-class outcome, not a bug.

**Sources of non-eligibility:**

- **Censoring** (§5): the observation window was cut short by a new deployment / event that reset the counterfactual.
- **Missing data:** the source events needed to derive the outcome weren't emitted during the window (e.g., the DataDog monitor was muted).
- **Manual override:** an operator declared the observation window uninformative (e.g., "we were doing scheduled maintenance; the SLO breach doesn't count").
- **Insufficient horizon:** the prediction's horizon hasn't elapsed yet — no label can exist until the observation window closes.

**Label event MUST carry `eligibility`:**
- `eligible` — outcome value is present, meaningful, evaluable.
- `censored` — see §5.
- `missing_data` — window closed but derivation failed; no confident outcome.
- `manual_ineligible` — human declared uninformative; carries `ineligibility_reason` free-text (audited).

**Calibration measurement uses `eligible` labels only.** Consumer libraries filter.

---

## 4. Human corrections

Humans can correct labels. Not all outcomes are derivable from the source stream; sometimes reality requires human interpretation.

**Correction event shape:**

Corrections are additive events on the same `forge.events.ground_truth.v1` stream, with:
- `outcome_source: manual_correction`
- `corrects_label_id` — the original label event this correction supersedes.
- `correction_reason` — one of: `misclassified_by_derivation` / `context_missed_by_automated_source` / `late_arriving_evidence` / `disputed_semantics`.
- `correction_authority` — who applied the correction (must be attested via the operating model per predictor, VOCABULARY §8 AP-7).

**Rule:** corrections are additive, never mutative. Original label event stays for audit. Calibration consumers use the most-recent-uncorrected-or-corrected outcome per `estimand_id + slice + observation_window`, computed by a projection.

**Anti-pattern (AP-C1):** allowing anyone with write access to the label stream to correct labels. The correction authority MUST be constrained to the accountable data owner per the operating model. Otherwise labels become subjective and calibration becomes political.

---

## 5. Censoring

**Definition:** an observation window is *censored* when a new event resets the counterfactual before the window naturally closes.

**Worked example** (deploy-SLO-breach estimand): a prediction is made at T0 for deployment D1 with a 60-minute observation window (T0 to T0+60m). At T0+30m, a new deployment D2 lands on the same slice. The remaining 30 minutes are now "post-D2 reality," not "post-D1 reality." The label for D1 is CENSORED at T0+30m.

**Censoring rules per estimand:**
- Every estimand declares its censoring events (per PREDICTION_CONTRACT §3.0 estimand definition).
- Censored labels are emitted with `eligibility: censored` and the truncated observation window.
- Calibration excludes censored labels by default. Advanced consumers may use survival-analysis techniques (Kaplan-Meier estimators) that handle censoring properly — those consumers opt in explicitly.

**Rule:** censoring is emitted on the label stream, not implicit. A label event with `eligibility: censored` is more informative than the absence of a label event.

---

## 6. The intervention stream contract (`forge.events.interventions.v1`)

**Purpose:** carry authoritative "here's an action taken because of a prediction" events. Enables counterfactual reasoning about treatment effects.

**v0 status:** intervention events exist even in shadow-mode v0 — they carry actions taken by humans in response to prediction-surfaced warnings. When v1+ enables T3/T4 automated actuation, the same stream carries the automated interventions.

### 6.1 Required fields per intervention event

- `intervention_id` — unique per emission.
- `triggered_by_prediction_id` — the prediction that motivated this intervention (see §7 AP-C2 if absent).
- `intervention_type` — namespaced (e.g., `human.investigate` / `human.rollback` / `human.mute_alert` in v0; `automation.rollback` / `automation.scale_up` / `automation.block_deploy` in v1+).
- `intervention_authority_tier` — the authority tier at which this intervention was taken (T3 or T4 typically; T2 for humans acting on advisory information).
- `actor` — who took the action (human ID or automation-service ID).
- `applied_at` — when the intervention actually took effect.
- `alternatives_considered` — bounded list (default max 3) of other actions considered but not taken. Enables downstream reasoning about what would have happened otherwise.
- `counterfactual_estimation_method` — how the counterfactual outcome (what would have happened without this intervention) is intended to be estimated. Options: `randomized_holdback` / `propensity_score_matching` / `doubly_robust` / `not_estimated`.
- `governance_envelope` — same shape as SC §3.6.

### 6.2 Intervention → outcome join

When a label event fires on the same `(estimand_id, slice, observation_window)` as a prior intervention event, the label MUST carry:
- `intervention_present` — boolean.
- `intervention_ids` — bounded list of intervention events that occurred within the observation window.

This is what turns naive accuracy into treatment-aware evaluation. A `slo_breach_absent` outcome that occurred in the presence of an intervention is not the same signal as the same outcome without intervention.

---

## 7. Anti-patterns

**AP-C1: Unconstrained label corrections.** See §4.

**AP-C2: Intervention with no prediction reference.** An action taken "because of a prediction" that doesn't carry the `triggered_by_prediction_id` cannot be attributed. The intervention stream ignores such events for treatment-effect purposes; the audit stream still keeps them (they're not fabrications, just unattributable). **Fix:** intervention-emitting consumers MUST always include the prediction reference. Automation frameworks enforce.

**AP-C3: Silent censoring.** Not emitting a label event because the window was censored. The absence of a label looks like a missing outcome, indistinguishable from an unemitted-but-derivable label. **Fix:** censored windows explicitly emit `eligibility: censored` labels.

**AP-C4: Derivation as ground truth.** A label event emitted with `outcome_source: derived` and `label_confidence: uncertain` is not a solid label. Consumers that use it as if it were miscalibrate the model. **Fix:** calibration consumers use `label_confidence: certain` only by default; opt-in for `likely`; never `uncertain` without explicit protocol.

**AP-C5: Post-hoc estimand redefinition.** Changing what an estimand's outcome means after labels have accumulated. Invalidates the calibration history. **Fix:** estimand versions are stable; changing the outcome semantics means creating a new estimand (`estimand_id` bumped), not editing an existing one.

**AP-C6: Cross-tenant label leakage.** A label event's governance envelope must inherit the strictest governance from the prediction it evaluates AND from the source events it derived from. Otherwise calibration data crosses tenant boundaries silently.

---

## 8. Worked example — label + intervention for the runtime worked estimand

**Setup:** the runtime-pool prediction from PREDICTION_CONTRACT §10 (`pred_2026-07-24T10:15:03Z_a4f2b8`) predicted `at_risk` for `webhook-gateway prod` deployment `8f3b21c`, with a 60-minute horizon.

**Timeline:**
- T0 (10:15:03Z): prediction emitted.
- T0+3m (10:18:00Z): human on-call sees the Slack digest and investigates.
- T0+8m (10:23:00Z): on-call decides to do nothing (no intervention).
- T0+42m (10:57:00Z): `datadog.slo_burning` fires; SLO breach observed.
- T1+60m (11:15:03Z): observation window closes.
- T1+65m (11:20:00Z): derived-label producer emits the label event.

**Intervention event** (emitted at T0+8m):

```yaml
intervention_id: intv_2026-07-24T10:23:00Z_c81a44
triggered_by_prediction_id: pred_2026-07-24T10:15:03Z_a4f2b8
intervention_type: human.investigate_no_action
intervention_authority_tier: T2         # human acting on advisory info
actor: user:jsmith@forge-works
applied_at: 2026-07-24T10:23:00Z
alternatives_considered:
  - human.rollback
  - human.mute_alert
counterfactual_estimation_method: not_estimated
governance_envelope: {tenant_id: forge-works, ...}
```

**Label event** (emitted at T1+65m):

```yaml
label_id: lbl_2026-07-24T11:20:00Z_e11f92
estimand_id: deploy_slo_breach_60m_association_v0
slice: {per_service: webhook-gateway, per_environment: prod}
identity_claims:
  - {authority: git, key_type: commit_id, value: 8f3b21c, ...}
  - {authority: internal_directory, key_type: service_id, value: webhook-gateway, ...}
observation_window:
  start: 2026-07-24T10:15:03Z
  end: 2026-07-24T11:15:03Z
outcome: slo_breach_occurred
outcome_source: direct_observation      # datadog.slo_burning fired during window
label_confidence: certain
label_delay: PT4M57S
eligibility: eligible
intervention_present: true
intervention_ids: [intv_2026-07-24T10:23:00Z_c81a44]
producing_system: label_derivation_service
producing_version: 1.2.0
logic_ref: mlflow://logic/deploy_slo_breach_60m_association_v0/derivation.py
governance_envelope: {tenant_id: forge-works, ...}
```

**What calibration does with this pair:**

The prediction was `at_risk` (correct — a breach occurred). Intervention was `human.investigate_no_action`, which is functionally equivalent to "no intervention" for treatment-effect purposes. Calibration records: `(class_probabilities.at_risk = 0.62, outcome = breach)` — a correct prediction at 62% confidence. If enough of these accumulate, `class_probabilities.at_risk = 0.62` should correlate with a ~62% empirical breach rate (well-calibrated).

If instead the intervention had been `human.rollback`, the counterfactual (would there have been a breach without the rollback?) becomes the load-bearing question. In v0 we log this and let AB-028's spike develop the counterfactual estimation methodology; v1+ automation requires the counterfactual protocol to work.

---

## 9. Open questions

- [ ] **Estimand catalog governance** — who owns the `estimand_id` catalog? Where is it stored? Adding a new estimand is a design event; process needed.
- [ ] **Manual-correction UX** — the "correction authority" is a role; how do humans actually apply corrections? A GitHub-issue-driven workflow? An MLflow annotation? A dedicated CLI?
- [ ] **Counterfactual estimation defaults** — what's the default `counterfactual_estimation_method` for the first few v0 estimands, given we have no randomization mechanism yet? `not_estimated` and revisit at v1+?
- [ ] **Label backfill on estimand version bump** — when an estimand's outcome semantics change (via version bump), do we backfill labels for historical predictions under the new semantics? Expensive; also arguably wrong (predictions were made under the old semantics).
- [ ] **Late-arriving evidence** — a `slo_breach_absent` label emitted at T+65m gets a `correction_reason: late_arriving_evidence` correction at T+7d because a customer-reported incident surfaced. How far back do we allow corrections to reach? Deprecation window analog?
- [ ] **Intervention taxonomy** — the intervention_type enum is per-authority-tier and per-pool. Who curates? First pass: same operating-model-per-predictor owner (VOCABULARY §8 AP-7); revisit as it grows.

---

## 10. Graduation criteria — v0 → v1

- [ ] Label stream live for at least one estimand (the AB-028 worked estimand).
- [ ] Intervention stream live for at least one T2 human-action class.
- [ ] Human-correction workflow attested for at least one accountable data owner.
- [ ] Censoring emitted correctly for at least one censoring event in the wild.
- [ ] Calibration measurement running continuously and publishing to MLflow.
- [ ] At least one confirmed correction event (a human amended a derived label).
- [ ] Governance envelope inheritance verified on cross-tenant test data.

---

## 11. Related documents

- `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md` *(v0.1)* — consumer of labels; upstream of interventions. Graduation criterion §11 depends on this doc reaching v0.
- `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` *(v0.1)* — label events carry the same identity claims + governance envelope shape.
- `docs/decisions/dynamic-reliability/DOCTRINE_INTERPLAY.md` *(drafted v0)* — arbitration protocol consumes prediction + gate verdicts + intervention history.
- `docs/decisions/dynamic-reliability/VOCABULARY_DESIGN.md` *(v0.1)* — outcome vocabularies live under §5 canonical mapping; namespaced.
- `planning/WIRE_PROTOCOL.md` — event serialization. Not yet drafted.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-030 tracks this doc's v0 → v1 lifecycle.

---

## 12. Iteration protocol

- Same as sibling design docs. Substantive changes bump `v0` → `v0.1` → `v0.2` → …
- Blocks `PREDICTION_CONTRACT_v0.md` v0 → v1 graduation until this doc reaches v0.
- On v1, content moves to `docs/decisions/DYNAMIC_RELIABILITY.md` alongside siblings.
