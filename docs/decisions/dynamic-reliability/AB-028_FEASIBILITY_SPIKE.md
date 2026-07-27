# AB-028 Feasibility Spike RFC (v0.2 draft) — Dynamic Reliability, first evidence

> **Status:** Scoping draft (v0.2 — methodological corrections from Codex round-2 loop applied 2026-07-26). Not yet approved for execution. Approval means: predeclared thresholds are locked and the spike may begin data collection.
> **Owner:** Platform team (spike execution owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Blocks:** `PREDICTION_CONTRACT.md` §11 v0 → v1 graduation, and by extension the whole v0.1 corpus.
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-028` (backlog is repo-ignored; canonical scope on this document).

---

## 1. Why this spike exists

The Codex round-1 loop on the design corpus (retrospective at `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md`, F12) flagged that the 4-doc design jumped to production-shaped graduation criteria without any evidence that a small model beats a deterministic or statistical baseline on ForgeWorks's normalized events. This spike closes that gap. Its output — a documented model-lift-over-baselines comparison on a single predeclared estimand — is what turns the corpus from *plausible* into *justified*.

The `PREDICTION_CONTRACT.md` §11 v0 → v1 graduation criteria list "AB-028 feasibility spike produced evidence that the model lifts over the deterministic baseline on the predeclared metrics" as a required checkbox. No further v0 → v1 promotion on the design corpus is planned until this spike delivers its go / no-go decision.

The spike is deliberately **offline-only, single-estimand, single-slice, T1-only, no model deployed live**. Its purpose is to answer one question: does a model on ForgeWorks's normalized events provide measurable lift over deterministic rules and logistic regression on the deploy-SLO-breach estimand, on a single production-representative slice, on 30–60 days of historical data?

---

## 2. Scope

### 2.1 In-scope

- **One source pair:** Terraform (deployment events + apply outcomes) + DataDog (SLO burn events + monitor state). Rationale: cleanest first source per `DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` §4 worked example, and DataDog carries the label events per `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2.
- **One slice:** `(per_service = webhook-gateway, per_environment = prod)`. Rationale: sufficient deploy volume for statistical power on a 30–60 day window; matches PC §10 worked walkthrough.
- **One estimand:** the PC §3.0 v0 worked estimand — `P(next deployment to this slice causes SLO breach within 60 minutes of the deploy marker)`. Estimand definition frozen; any change means a new estimand ID, not an amendment.
- **One consumer:** offline audit sink only (T1). Predictions written to a MLflow-tracked evaluation log; nothing surfaces to humans or gates any process during the spike.
- **Baselines:** two, both trained on the same feature matrix as the model.
  1. **Rules-based baseline** — a deploy-time heuristic list (e.g., "recent apply_failed in last 24h" OR "deploy in freeze window" OR "monitor already in warning state" → `at_risk`). The list is enumerated and frozen in §5.2 before training.
  2. **Logistic regression baseline** — plain LR on the same features. Standard scaler, L2 regularization, cross-validated on the training window. No feature engineering the model doesn't also get.
- **Predeclared metrics with named thresholds** — §6. Thresholds must be locked at scoping-approval, before training data is inspected.
- **Offline replay** — 30–60 days of historical data replayed through the pipeline. No live-model deployment.
- **MLflow tracking** — every training run + baseline run logged to MLflow (metrics, params, model artifacts, calibration curves). Enables audit and reruns.

### 2.2 Out-of-scope

- **T2/T3/T4 consumers.** No Slack messages, no dashboards, no gate integration, no automation. First AB-NNN for surfacing predictions to humans is a follow-up filed after go decision.
- **Any other estimand** (rollback probability, incident-cluster probability, cost-anomaly). Same spike shape can be repeated later.
- **Any other slice.** Cross-slice generalization is a v1+ concern; a single-slice spike is enough to say go / no-go on the corpus.
- **Runtime placement.** AB-029 runs in parallel. This spike uses whatever offline replay harness is cheapest — sibling Flink job is the default, but batch replay in a Python notebook is acceptable if it's faster to iterate.
- **MLflow production readiness.** AB-032 addresses this separately. The spike may use MLflow in a "development" mode; production-hardening happens before v1.
- **Live intervention capture.** `intervention_present: true` cases in the label stream (§4.2) are noted but not used as counterfactual evidence — v0 has no randomization, and this spike does not attempt counterfactual estimation. Labels with intervention present are analyzed separately.
- **Model architecture debate.** The spike picks one reasonable model class (see §5.3) and runs. If the go/no-go depends on model class, the spike outcome is "inconclusive, re-scope with tighter model comparison."

### 2.3 Non-goals

- **"Better than existing production."** There is no existing production model for this estimand. The comparison is model vs. baselines on the same data, not vs. a live system.
- **"Prove the corpus is right."** The corpus is v0.1; this spike is not a corpus review. The spike either delivers lift-over-baselines or it doesn't; either result is legitimate input to the go/no-go decision.
- **A shippable model.** Even on a go verdict, the model is not "ready to deploy" — v1 graduation requires the full §11 checklist, not just this spike.

---

## 3. Worked estimand (verbatim from PREDICTION_CONTRACT.md §3.0)

> For a `(service, environment)` slice, predict:
>
> **P(the next deployment to this slice causes an SLO breach within 60 minutes of the deploy marker)**
>
> with:
> - **Eligibility:** a deployment event exists for the slice within the horizon; the slice has ≥30 days of observation history; `input_freshness` < 5 minutes.
> - **Label window:** 60 minutes post-deploy; any SLO breach in `datadog.slo_burning` / `datadog.slo_burned` state counts.
> - **Censoring:** if the next deployment happens within 60 minutes (new deploy = new prediction context), the label is censored.
> - **Abstention:** if eligibility fails or `input_freshness` violates the threshold, the prediction abstains (`type=abstain`).
> - **Error costs:** asymmetric — false negatives (miss a real breach) cost ~10× false positives (unnecessary caution). Consumers use this to calibrate their thresholds.
> - **Decision informed:** at T2, a `deploy_at_risk` recommendation surfaces to the deploy author and to `#platform-oncall`. NO gating in v0.

**Estimand ID for this spike:** `deploy_slo_breach_60m_v1` (matches the estimand referenced in GT §8 worked example).

**Observational-vs-causal caveat** *(added 2026-07-26 — surfaced by Codex round-2 critique loop; F10.)* PC §3.0 words the estimand causally ("deployment causes SLO breach"). This spike, being observational by design (no randomization, no counterfactual identification methodology, and intervention-present outcomes segregated per §2.2), measures **the observational association**:

> **P(SLO breach observed within 60min of deploy marker | slice, features, no confirmed intervention during the window)**

Causal interpretation of the model's output requires counterfactual identification methodology that v0's shadow-mode-only posture cannot yet provide. A GO verdict from this spike is evidence for **advisory-only recommendations at T2** (the deploy author sees a `deploy_at_risk` note pre-deploy); it is **not** evidence supporting T3/T4 gating, blocking, or automated actuation. The corpus-level correction to PC §3.0's estimand wording is tracked as **AB-033** — separate backlog entry, filed 2026-07-26.

---

## 4. Data plan

### 4.1 Time window

*(v0.2 tightening per F9 — separates pre-scoping metadata inspection from modeling-window inspection; see §4.4 for the pre-scoping window definition.)*

- **Modeling window:** 60 days target, 30 days minimum. 60 preferred for statistical power on the positive class; 30 acceptable if data-quality issues on 60d force a shorter window.
- **Pre-scoping metadata window:** additional 30 days immediately preceding the modeling window (per §4.4). Used ONLY for volume + base-rate + missing-data-rate estimates; **excluded permanently** from training/validation/test.
- **Train / validation / test split** *(on the modeling window)*: temporal, not random. Train = first 70%; validation = middle 15%; test = last 15%. Test window is held out at scoping-approval time and touched **only** for the final metric report per §6.4.
- **Base-rate discussion moved to §4.4** (part of the metadata-window analysis).

### 4.2 Label construction (per `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2)

*(v0.2 rewrite — surfaced by Codex round-2 critique loop; F1 outcome_source doctrine + calibration-cohort validity, F15 estimand-purity restore, F19 schema-conformance delegation to AB-030.)*

The spike is the first live implementation of the GT §2 label stream contract for one estimand. Labels are constructed offline from historical DataDog SLO events. Both classes carry `label_confidence: certain` — the distinction is `outcome_source`:

- **Positive label** (`outcome: slo_breach_occurred`, `outcome_source: direct_observation`, `label_confidence: certain`): a `datadog.slo_burning` (or `datadog.slo_burned`) event fires with the slice's SLO IDs during the 60-minute observation window. Direct observation per GT §2.1.
- **Negative label** (`outcome: slo_breach_absent`, `outcome_source: derived`, `label_confidence: certain`): the window closed, no `slo_burning`/`slo_burned` event fired with the slice's SLO IDs, and no `datadog.incident_opened` event references the slice. The absence-of-signal derivation is certain under a well-instrumented DataDog integration (see missing-data eligibility below for when it isn't).
- **Censored label** (`eligibility: censored`, `outcome_source: derived`): a new deployment to the slice landed inside the window. Excluded from primary calibration by default (per GT §5); may be used by advanced survival-analysis consumers as a stretch goal, out of spike scope.
- **Missing-data label** (`eligibility: missing_data`, `outcome_source: derived`): DataDog monitor state was `muted` or `unknown` during the window — cannot confidently derive absence-of-breach. Excluded from all analysis cohorts.
- `manual_correction` (`outcome_source: manual_correction`) — RESERVED. No human corrections in spike execution; the enum value is reserved for future post-spike correction workflow (AB-030 v1).

**Primary calibration cohort** = all `eligible` labels of BOTH classes (positives with `direct_observation` + negatives with `derived`). Both classes carry `label_confidence: certain`; the M2 ECE / M3 Brier / calibration curves are computed on this two-class cohort. There is no secondary `likely` cohort — the previous v0.1 draft mislabeled derived-absent negatives as `likely` and then excluded them, which would have left calibration undefined on positives only.

**Estimand purity — scheduled maintenance is NOT eligibility-filtered.** *(v0.2 change per F15.)* Adding a `manual_ineligible` filter for scheduled-maintenance windows would silently change the estimand's population (PC §3.0 defines eligibility using deployment presence + ≥30d history + freshness; scheduled maintenance is not one of those conditions; GT AP-C5 forbids post-hoc estimand redefinition). Instead: maintenance-window deploys stay in the population, AND the spike report (§7 deliverables) splits results into maintenance vs. non-maintenance cohorts. If the maintenance cohort behaves systematically differently, that's information for v1 planning, not a reason to exclude.

Labels carry the `intervention_present` flag per GT §6.2 — but the spike does not use intervention-present labels for model evaluation (§2.2). They are logged for future cohort analysis.

**Provenance** per GT §2.2: `producing_system: ab028_spike_label_deriver`, `producing_version: 0.2.0`, `logic_ref: mlflow://experiments/ab-028/label_derivation.py@<sha>`.

**Schema conformance** *(v0.2 addition per F19.)* Label emission uses the shared `label_schema_validator` library delivered by **AB-030** (`GROUND_TRUTH_INTERVENTION_CONTRACT.md` v0 → v1). If AB-030's validator library is not available when spike execution begins, spike halts with `blocked_on: AB-030` verdict. Emitting labels ad-hoc from the spike would duplicate contract knowledge and drift; the AB-030 dependency is explicit.

### 4.3 Feature construction

Features are computed at prediction time (deploy marker T0) from the historical event stream *before T0* only — no look-ahead. Feature families:

- **Deployment metadata** (from Terraform): resource types touched, resource count, plan-to-apply delta size, deploy author role, deploy hour-of-day, deploy day-of-week.
- **Recent-history features** (rolling windows before T0): count of `terraform.apply_failed` in {1h, 6h, 24h, 7d}, count of `datadog.slo_burning` on the slice in {1h, 6h, 24h}, time-since-last-apply, time-since-last-slo-breach.
- **Slice-state features**: current DataDog monitor state per SLO (ok / warning / alert / muted / unknown), current active-incident count for the slice, days-since-slice-was-added.
- **Deploy-content features** (Terraform plan derived): count of resource *creates* vs. *updates* vs. *destroys*, whether IAM/security-group/network resources are touched, plan diff size in bytes.

**Feature versioning:** *(v0.2 tightening per F12.)* the feature list is frozen at scoping-approval. Adding features mid-spike invalidates the test cohort and requires re-scoping. **Removing features is permitted ONLY for schema-drift or availability failures documented BEFORE label opening** — i.e., before any label value is inspected against feature values. Any outcome-informed removal (e.g., "we saw this feature didn't help on validation, drop it") invalidates the test cohort and forces re-scoping. Every removal is logged to MLflow with reason, timestamp, and pre-label vs. post-label attestation.

### 4.4 Volume back-of-envelope + pre-scoping metadata window

*(v0.2 rewrite — surfaced by Codex round-2 critique loop; F9 predeclaration coherence, F2 minimum-positive floors per split, F20 sampling location.)*

**Pre-scoping metadata window** — resolves the F9 tension between "thresholds lock before training data is inspected" (RFC §2.1) and "scoping-approval confirms actual historical volume + positive-class counts" (previous §4.4). The historical replay window is split in two:

- **Metadata-only pre-scoping window** — 30 days (immediately preceding the scoping-approval meeting). Inspected ONLY for volume, base-rate, censoring-rate, and missing-data-rate estimates that feed prospective power analysis. **Excluded permanently from training/validation/test.** No feature values inspected; no label values inspected; only counts.
- **Modeling window** — the 60-day rolling window used for training/validation/test (per §4.1). Untouched until scoping-approval locks the RFC. First inspection of any modeling-window label or feature value = spike execution has begun.

**Expected deploy volume for `webhook-gateway prod`:** order of magnitude 5–30 deploys/day, to be confirmed during scoping-approval from the metadata window ONLY. On a 60-day modeling window, that's ~300–1800 deploys, ~6–140 positives at 2–8% base rate.

**Minimum positive-label floors per split** *(v0.2 replacement for the previous 20-training-positives floor per F2)*:

- **Training set** (70% of modeling window): ≥50 positive labels after eligibility filtering.
- **Validation set** (15%): ≥15 positive labels.
- **Test set** (15%): ≥30 positive labels.

If any of these floors fails when the modeling window opens: spike halts with `inconclusive` verdict; report published; escalation options are (a) extend modeling window to 90 days, (b) reconsider slice choice, or (c) file `AB-NNN` for a longer-history spike variant. Baselines still run and are reported.

Floor values above are **proposals**; scoping-approval locks the final numbers based on prospective power analysis on the pre-scoping metadata window. Power analysis targets: the AUCPR-lift 95% CI (per §6.4 GO rule) is narrow enough that the ≥margin bar is falsifiable.

**Sampling and reweighting location** *(v0.2 addition per F20)*:

- **Validation and test cohorts:** NO resampling, NO class reweighting. Natural prevalence preserved end-to-end so calibration measurements (M2 ECE / M3 Brier) are interpretable.
- **Training cohort only:** class balancing via `class_weight` in LR (§5.2) and GBT (§5.3) is permitted. SMOTE / synthetic oversampling explicitly forbidden.
- **Feature scaler / target encoder:** fit on training only, applied to val/test.
- **Calibration wrapper** (§5.3, extended to §5.2 per F8): fit on a disjoint held-out fold within training; probabilities on val/test are calibrated against the wrapper's mapping, not re-fit.

**Base-rate expectation** (from §4.1): 2–8%. If actual base rate on the pre-scoping metadata window is <1% or >20%, spike reports the discrepancy at scoping-approval and re-evaluates whether the estimand is well-scoped before proceeding (rather than after training).

---

## 5. Baselines and model

### 5.1 Baseline 1 — rules

*(v0.2 rewrite — surfaced by Codex round-2 critique loop; F7 empirical-rate probability mapping, F17 mechanism explicitly declared.)*

An explicit heuristic list, frozen at scoping-approval, evaluated at prediction time. Predicts `at_risk` (positive) if ANY rule matches; otherwise `not_at_risk`. Proposed rule list (subject to scoping-approval finalization):

1. Any `terraform.apply_failed` event on the slice in the last 6 hours.
2. Any `datadog.slo_burning` event on the slice in the last 1 hour.
3. Current DataDog monitor state = `warning` or `alert` on any of the slice's SLO monitors.
4. Deploy touches IAM, security-group, or network resources AND slice had ≥1 `apply_failed` in last 7d.
5. Deploy plan diff size > 90th-percentile of historical plans on the slice.

**Rules are not "trained" in the ML sense** — no gradient, no hyperparameters, no cross-validation, no learned weights. But some rule constants are **data-derived from the training window** and frozen before validation/test. Rule 5's `P90(plan_diff_size)` is such a constant: computed on the training window only, then frozen at scoping-approval, versioned with the rule set, and logged to MLflow as `rules_baseline/rule_5_threshold`. No rule constant is computed on validation or test data.

**Probability output for calibration-comparable metrics** *(v0.2 change per F7)*: rules produce a native binary prediction. For M2 ECE / M3 Brier / M1 AUCPR (probabilistic metrics), rule matches are mapped to the **empirical breach rate on the training window under that condition**, not to arbitrary constants:

- `P(positive | any rule matches)` — computed on training window, frozen.
- `P(positive | no rule matches)` — computed on training window, frozen.

These two frozen empirical rates become the rules baseline's probability output for calibration-comparable metrics. This removes the 0.9/0.1 handicap the v0.1 draft would have imposed (which would have deflated the rules baseline's ECE artificially — GT §2 defines calibration as correspondence between predicted probabilities and observed outcomes; 0.9/0.1 corresponds to no observed rate).

**Also reported**: the rules baseline's native binary operating-point metrics (precision, recall, FPR, warnings-per-week at the match/no-match cutoff). §6.3 C1 uses expected loss, which uses the frozen empirical rates.

### 5.2 Baseline 2 — logistic regression

*(v0.2 tightening — surfaced by Codex round-2 critique loop; F8 calibration wrapper alignment with model, F13 time-respecting CV.)*

Standard `sklearn.linear_model.LogisticRegression` with:
- L2 regularization (C = 1.0 default; tuned via time-respecting CV — see below).
- Standard scaling of numeric features (scaler fit on training only).
- One-hot for low-cardinality categoricals; target encoding with smoothing for high-cardinality (e.g., resource_types), fit on training only.
- Class weight = balanced (base rate is very asymmetric).
- **Isotonic calibration wrapper** *(v0.2 change per F8)*: same as GBT (§5.3). Fit on a disjoint held-out fold within the training cohort. This removes the calibration asymmetry the v0.1 draft would have created (raw LR probabilities vs. isotonic-calibrated GBT probabilities is not an apples-to-apples ECE comparison).
- **Cross-validation for hyperparameter search** *(v0.2 change per F13)*: `sklearn.model_selection.TimeSeriesSplit` OR blocked temporal folds with embargo. Embargo size ≥ max(label window = 60min, longest rolling-history feature window = 7d). Preprocessing fit fold-locally, not globally.
- Trained on the same feature matrix as the model (§5.3).

Deliberately no interactions, no polynomial features. This is the "obvious first thing" baseline. If the model can't beat LR on this feature set, either the features are already saturating the signal or the model class doesn't add value.

### 5.3 Model — spike picks one

*(v0.2 tightening — surfaced by Codex round-2 critique loop; F8 calibration wrapper aligned with LR, F13 time-respecting CV.)*

**Recommended:** gradient-boosted trees (XGBoost or LightGBM) with:
- **Hyperparameter search:** small grid over `n_estimators ∈ {100, 300}`, `max_depth ∈ {3, 5, 7}`, `learning_rate ∈ {0.05, 0.1}`. Total 12 configs.
- **Cross-validation** *(v0.2 change per F13)*: same time-respecting protocol as LR (§5.2) — `TimeSeriesSplit` OR blocked temporal folds with embargo ≥ max(60min, 7d). Preprocessing fit fold-locally.
- Class weight = balanced.
- **Isotonic calibration wrapper** on top, fit on a disjoint held-out fold within training. **Identical calibration protocol to LR (§5.2)** so M2 ECE is a fair comparison.
- Same feature matrix as baselines. No feature engineering the baselines don't get.

**Rationale for GBT over deep learning:** the data volume (~1000 deploys) is too small for deep sequence models to have a fair shot; GBT is the standard-of-care for tabular data at this scale. Rules out one class of "model was undertrained" defense on a no-go.

**Rationale for GBT over LR-with-interactions:** the LR baseline already covers "linear-in-features" hypothesis space. GBT tests whether nonlinear feature combinations help.

If GBT loses to LR, the spike reports that outcome honestly — it's meaningful evidence that the model class chosen doesn't add value on this data, not a spike failure.

---

## 6. Predeclared metrics and thresholds

*(v0.2 rewrite — surfaced by Codex round-2 critique loop; F3 bootstrap-CI decision gate, F4 validation-selected operating threshold, F5 precision floor + warnings/week, F6 expected-loss with severity weighting, F11 relative AUCPR floor, F14 O1-O4 dropped from GO bar, F16 baseline-comparison matrix, F18 ECE binning spec.)*

**All thresholds below are proposed. Lock them at scoping-approval before the modeling window is inspected.** Metadata inspection on the pre-scoping window (§4.4) is permitted and expected. Once locked, thresholds are the GO/no-GO bar; adjusting them post-training is a documented spike-outcome amendment, not a routine change.

**Sampling-uncertainty policy across all §6 metrics** *(v0.2 addition per F3)*: any threshold comparing model to baseline uses **temporal block bootstrap CIs**, 1000 resamples, blocks sized to the label window (60min) to preserve within-window dependence. A "pass" requires the **lower 95% CI bound on the model-minus-baseline difference to exceed the declared margin**, not merely a point-estimate crossing. Multiplicity policy: Bonferroni correction across the four primary comparisons (M1, M2, M3, C1) at α = 0.05 (so per-test α = 0.0125). Scoping-approval MAY substitute a single primary comparison (M1 as primary, M2/M3/C1 as diagnostic) if power analysis shows the multiplicity correction leaves the primary bar unfalsifiable.

### 6.1 Primary metrics — comparisons by metric

*(v0.2 change per F16 — the previous "must beat both baselines" heading was inconsistent with per-metric baseline applicability.)*

| # | Metric | Baseline comparison | Threshold | Rationale |
|---|--------|---------------------|-----------|-----------|
| M1 | **AUCPR** (average precision, sklearn `average_precision_score`) on held-out test cohort | Model vs. rules AND vs. LR | Lower 95% CI bound of (model AP − max(rules AP, LR AP)) ≥ **0.05**; AND model AP ≥ **observed_test_prevalence + 0.10** (**normalized lift over prevalence**, i.e., ≥10 absolute percentage points above the random-classifier baseline; replaces v0.1's absolute floor of 0.15 which could be below prevalence at base rate >15% per F11) | AUCPR = average precision; explicit to eliminate the F11 trapezoidal-vs-average-precision ambiguity. Normalized floor guards against "GO on a worse-than-random model." |
| M2 | **Expected Calibration Error (ECE)** on eligible test cohort | Model vs. rules AND vs. LR (per F16 correction) | Model ECE ≤ **0.10**; AND lower 95% CI bound of (rules ECE − model ECE) > 0 AND (LR ECE − model ECE) > 0. **Binning:** equal-mass (equal-count), 10 bins. Minimum 5 observations per bin; under-populated bins merged into neighbors and merge logged. Reported ECE = population-weighted mean absolute deviation between bin-mean-predicted-probability and bin-observed-frequency. Also reported: **maximum calibration error (MCE)** and **reliability diagram** (per F18). | 0.10 is a defensible upper bound for advisory-only use. F7 patched rules to produce empirical-rate probabilities, so rules baseline now has a meaningful ECE. F18 nails down the binning spec. |
| M3 | **Brier score** on eligible test cohort | Model vs. rules AND vs. LR AND vs. constant-predictor (per F16) | Model Brier < base_rate × (1 − base_rate) (constant-predictor Brier); AND lower 95% CI bound of (rules Brier − model Brier) > 0 AND (LR Brier − model Brier) > 0 | Constant-predictor baseline is a sanity floor; per-baseline strict inequality replaces the v0.1 "≤ LR Brier" tie-permitting rule. |

### 6.2 Operational metrics — REPORTED, not gated

*(v0.2 change per F14 — O1-O4 removed from the corpus-graduation GO/no-go bar.)*

Latency, cost, and feature-computation timing depend on the runtime placement decision **owned by AB-029**, not AB-028. Measuring them on an ad-hoc offline notebook or replay harness (per §2.2) cannot support a runtime-viability GO for corpus-graduation purposes.

Instead, O1-O4 are reported as **diagnostic** metrics for AB-029's use:

| # | Metric | Reporting target (informational) |
|---|--------|----------------------------------|
| O1 | Inference latency p50 (on the spike harness) | Report; provide to AB-029 as a data point. |
| O2 | Inference latency p95 (on the spike harness) | Report; provide to AB-029. |
| O3 | Operational cost per prediction (offline replay accounting) | Report; provide to AB-029. Not a fully-loaded production cost. |
| O4 | Feature computation latency p95 (on the spike harness) | Report; provide to AB-029. |

Corpus graduation depends only on M1, M2, M3, and C1. Runtime-viability GO is AB-029's determination.

### 6.3 Cost-weighted metric — asymmetric error costs

*(v0.2 rewrite — surfaced by Codex round-2 critique loop; F4 threshold selected on validation not test, F5 precision floor + warnings/week budget, F6 explicit 10× FN cost + severity weighting.)*

Per PC §3.0, false negatives cost ~10× false positives. Per AB-028 scope, false-negative cost is severity-weighted. C1 implements both.

**Predeclared severity weights** `w(sev)`, locked at scoping-approval:
- `critical` = 3.0
- `major` = 2.0
- `warning` = 1.0

**Predeclared cost ratio** `k` = 10 (FN:FP), from PC §3.0.

**Expected loss on a cohort:**

```text
L = k × Σ_{missed_positives i} w(sev_i)  +  Σ_{false_positives}(1)
```

Where `sev_i` is the observed SLO breach severity for missed positive `i`, drawn from DataDog's SLO event severity classification.

**Operating threshold selection** *(F4 fix)*: for each model (model, LR baseline, rules baseline), select the operating threshold on **validation** at the point minimizing L(validation). Freeze the threshold. Evaluate all C1 metrics **once** on test at the frozen threshold.

**C1 pass condition** *(F6 fix)*:

```text
lower 95% CI bound of (L_baseline − L_model) / L_baseline  > 0.30
for BOTH baseline ∈ {rules, LR}
```

i.e., model expected loss must be at least 30% lower than each baseline's expected loss, with statistical significance.

**Additional constraints on the model's chosen threshold** *(F5 fix — FPR alone is insufficient given the base-rate fallacy)*:

- **Precision floor:** model precision on validation cohort at chosen threshold ≥ **0.40**. Prevents a "low expected loss" threshold that would drown the T2 consumer in false alerts.
- **Warnings-per-week budget:** ≤ **5 warnings per week per slice** at chosen threshold on validation cohort. Reflects operational human workload.
- **FPR ceiling:** ≤ **25%** on validation cohort at chosen threshold. Retained as a specificity floor; note this is FPR (population level), NOT FDR (what the human sees), which is bounded by the precision floor above.

At the frozen threshold, the spike report publishes: recall, precision, FPR, warnings-per-week, cost-weighted L, breakdown by severity class.

### 6.4 Go / no-go decision

*(v0.2 rewrite — per §6.2 F14 change O1-O4 are diagnostic not gating; per §6.1/§6.3 F3 change all comparisons require lower-CI-bound gating.)*

- **GO:** M1, M2, M3, C1 all pass their lower-CI-bound thresholds against their per-metric baselines (§6.1, §6.3). Report published; `PREDICTION_CONTRACT.md` §11 v0 → v1 checkbox for AB-028 lift-over-baselines is checked. Follow-up AB-NNN filed for next-step promotion work (feature-store, live deploy, T2 surface). O1-O4 are attached as diagnostic input to AB-029.
- **NO-GO:** ANY of M1, M2, M3, C1 fails its lower-CI-bound threshold. Retrospective published (Codex-review-style loop welcomed). Corpus does not graduate to v1. Follow-up work either: (a) revise design corpus based on what went wrong; (b) pause the Dynamic Reliability initiative; (c) abandon and file an ADR explaining why.
- **INCONCLUSIVE:** the spike hits a data-quality wall (§4.4 minimum-positive floors fail, base rate <1% or >20%) OR the CI bounds are so wide that a "pass" is unfalsifiable at the declared α (per §6 sampling-uncertainty policy). Retrospective published; spike re-scoped and re-run, not resolved by amendment.

---

## 7. Deliverables

At spike conclusion, in `docs/decisions/dynamic-reliability/AB-028_SPIKE_REPORT.md`:

- Executive summary: go / no-go / inconclusive verdict, one-line rationale.
- Metric table: every threshold in §6 with actual value, pass/fail column.
- Calibration curves: rules vs. LR vs. model, on the eligible test cohort.
- PR-AUC curves: rules vs. LR vs. model.
- Feature importance summary (for the model): top 20 features by SHAP or gain.
- Data quality issues surfaced during the spike (censoring rate, missing-data rate, muted-monitor rate).
- Recommended next AB-NNN entries (whether go or no-go).
- MLflow experiment link: `mlflow://experiments/ab-028/`.

Every training run logged to MLflow. Feature matrix and labels stored under `research/spikes/ab-028/` (repo-ignored per convention; MLflow is the source of truth for artifacts).

---

## 8. Risks

- **R1: Insufficient positive-class volume.** 60d @ 3% base rate on webhook-gateway may yield too few positives for one or more of the per-split floors (train ≥50, val ≥15, test ≥30 per §4.4 v0.2). Mitigation *(v0.2 change per F2 + F9)*: pre-scoping metadata window (§4.4) inspects volume + base-rate + eligibility-rate counts BEFORE thresholds are locked and BEFORE the modeling window is touched. Scoping-approval uses that inspection for a prospective power analysis; if the analysis shows any per-split floor cannot be met on the target modeling window, escalation options are (a) extend modeling window to 90d, (b) reconsider slice choice, or (c) file `AB-NNN` for a longer-history spike variant. Hard floor stops the spike per §4.4 rather than producing a fake-power result.
- **R2: AB-030 (GT contract v0 implementation) not far enough along.** GT is drafted at v0 but not implemented as live infrastructure. This spike is the first implementation of GT §2 for one estimand. Mitigation: label derivation logic is scoped to this spike's slice and estimand only; the code is a candidate for extraction into GT §2's canonical implementation in a follow-up AB-NNN, not a general-purpose label service.
- **R3: AB-029 (runtime placement) unresolved.** Latency thresholds in §6.2 depend on the runtime placement decision owned by AB-029. Mitigation *(v0.2 change per F14)*: §6.2 O1-O4 are now REPORTED as diagnostic input to AB-029, not gating GO/no-GO. Corpus graduation depends on M1, M2, M3, C1 only. AB-029 owns the runtime-viability determination independently.
- **R4: MLflow tracking-only setup insufficient.** Current MLflow serves tracking only; AB-032 tracks production-readiness. Mitigation: spike uses MLflow in "development mode" — experiment tracking, artifact storage — without depending on registry governance, calibration serving, or promotion RBAC. Production-hardening is a v1 prereq, not a spike prereq.
- **R5: Interventions in historical data confound the model AND the estimand is observational, not causal.** The historical window contains human-taken actions (rollbacks, mutes, deploy pauses) that changed outcomes. The spike does not attempt counterfactual estimation (per §2.2 out-of-scope). Mitigation: intervention-present labels segregated from the primary training cohort (§4.2). If the intervention-present cohort is >20% of eligible labels, the spike report flags this as a distortion signal and recommends counterfactual-methodology work before v1. **See §3 observational-vs-causal caveat** *(v0.2 addition per F10)* — the estimand as-worded in PC §3.0 uses causal language ("causes"), but this spike measures observational association only. GO evidence supports T2 advisory-only; it does NOT support T3/T4 gating or actuation. AB-033 tracks the corpus-level correction to PC §3.0's estimand wording.
- **R6: Feature leakage.** Recent-history features (§4.3) are computed at T0 — care needed that no feature accidentally uses events at T > T0. Mitigation: feature computation uses a strict "as-of T0" boundary; the spike includes a unit test that asserts no feature depends on any event with `event_time > T0`.
- **R7: Scoping-approval bikeshedding on thresholds.** Endless debate on whether 0.05 AUCPR lift is enough. Mitigation: scoping-approval is a single meeting with a documented outcome; thresholds are locked in the RFC by editing this file with the final numbers and the meeting-date attribution; further changes are documented spike-outcome amendments.

---

## 9. Timeline (indicative)

Rough shape, not a commitment. Real timeline depends on data-quality issues surfaced during setup.

| Week | Milestone |
|------|-----------|
| 0 | Scoping-approval meeting: lock thresholds (§6), confirm volume estimate (§4.4), confirm rule list (§5.1), confirm feature list (§4.3). RFC edited with locked values. |
| 1 | Terraform + DataDog adapters emit historical events to a scratch topic in the v0.1-compliant shape. Label derivation for the estimand runs; label volume + eligibility report published to spike thread. |
| 2 | Feature computation pipeline; rules baseline metric report. |
| 3 | LR baseline; feature matrix stability check; MLflow experiments initialized. |
| 4 | Model training runs (12-config grid + isotonic calibration); calibration curves; PR-AUC curves. |
| 5 | Metric report against locked thresholds; go / no-go / inconclusive verdict; spike report drafted. |
| 6 | Spike report published to `docs/decisions/dynamic-reliability/AB-028_SPIKE_REPORT.md`; PC §11 checkbox actioned. |

Total: ~6 weeks of engineer-time, not necessarily 6 elapsed weeks (parallelism possible with AB-029, AB-030, AB-032 spike work).

---

## 10. Related documents

- [`README.md`](README.md) — corpus index.
- [`AB-028_SCOPING_APPROVAL_AGENDA.md`](AB-028_SCOPING_APPROVAL_AGENDA.md) — companion agenda doc for the scoping-approval meeting; enumerates every RFC-mandated lock item (§B) and the round-2 over-concession probes (§C) so the meeting doesn't rubber-stamp authorial defaults. Closes and is superseded by the RFC's §11 provenance entry once the meeting outcome lands.
- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) §3.0 (worked estimand), §11 (graduation criteria consuming this spike).
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) §4 (Terraform worked example; source shape for the spike's adapter).
- [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) §2 (label stream contract; the spike is its first implementation), §5 (censoring), §6.2 (intervention join), §8 (worked example for this estimand).
- [`VOCABULARY_DESIGN.md`](VOCABULARY_DESIGN.md) §9 (Terraform worked walkthrough — feature vocabulary source).
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-028 backlog entry (local-only); AB-029, AB-030, AB-032 parallel/dependent entries.
- `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md` — Codex round-1 audit (local-only); F12 is the finding that motivated this spike.

---

## 11. Provenance

- **2026-07-26:** RFC drafted at v0.1 as the natural next step after the corpus migration (fac4ea8, 2026-07-25). Predeclared thresholds are proposals awaiting scoping-approval lock.
- **2026-07-26:** RFC bumped to v0.2. Nineteen methodological corrections from Codex round-2 critique loop applied — evidence integrity, calibration validity, baseline fairness, statistical power gating, causal-vs-observational estimand caveat, and cost-weighted decision framework. Round audit trail: `research/feedback_loops/dynamic-reliability-AB-028_FEASIBILITY_SPIKE/20260726T082924Z/` (local-only per repo `.gitignore` convention — `prompt.md`, `codex_response.md`, `reconciled.md`).
- **2026-07-27:** Scoping-approval agenda companion doc drafted at `AB-028_SCOPING_APPROVAL_AGENDA.md`. Structured to force decisions on every RFC-mandated lock item (§B — thresholds, rules, features, volume) plus the three over-concessions from the round-2 post-application review (§C — §6.3 constraint stacking, invented severity weights + 30% bar, bootstrap machinery weight). Meeting outcome will edit-in-place here as v0.3 with scoping-approval attribution on each locked stanza.
