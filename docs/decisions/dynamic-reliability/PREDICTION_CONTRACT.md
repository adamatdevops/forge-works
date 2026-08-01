# Prediction Contract (v0.1) — Consumer-Side Interface for Dynamic Reliability

> **Status:** Design stub (v0.1).
> **Origin:** Downstream mirror of `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`. Requested in the design-phase discussion originating in `planning/IMPORTANT_IDEA.md` (origin discussion, local-only per repo `.gitignore` convention).
> **Location note:** Migrated 2026-07-25 from `planning/PREDICTION_CONTRACT_v0.md` to this tracked path — see `docs/decisions/dynamic-reliability/README.md` for the corpus index and the AB-028..032 follow-up summary.
> **Lifecycle note:** Same as sibling design docs — deletable pointer `IMPORTANT_IDEA.md` closes when this doc + the source contract graduate to v1.0.
> **Scope:** what a Dynamic Reliability prediction looks like to a *consumer* under the v0 doctrine (T1/T2 only — advisory/shadow-mode), what the consumer must know to trust or ignore it, what the consumer classes are, how the consumer interface stays plugin-shaped so new consumers can subscribe without engine changes. Not the model architecture, not the wire format, not the ground-truth / intervention schema, not the arbitration protocol — each has its own sibling doc.
> **v0.1 provenance:** Restructured 2026-07-24 after Codex round-1 loop; post-hoc dispositions review 2026-07-25 (reconciled.md retained locally under `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/` per the codex-review workflow — that path is repo-ignored by design). Major changes: authority-hierarchy doctrine replaces operator/reviewer (F11), v0 scope narrowed to shadow-mode/advisory-only (F1), new §3.0 worked estimand (F2), cross-pool modes removed from v0 (F5), namespaced identity claims replace flat correlation keys (F14), per-type confidence semantics (F13), explanation_ref replaces raw feature-contributions (F17), governance envelope required (F8), old §4.4 (disagreement signals) removed and replaced with new §4.5 (policy reference / arbitration handoff) (F7), lifecycle events emitted separately instead of field mutation (F16), topic partitioning fixed (F19), consumer classes narrowed to advisory-only (F1), confidence continuous monitoring + circuit breakers (F24), AP-6 rewritten with counterfactual protocol (F10), graduation criteria updated for shadow-mode + ground-truth dependency (F3, F20).
>
> **2026-07-27 (AB-033):** §3.0 worked estimand rewritten from causal wording ("the deployment *causes* an SLO breach") to observational form (`deploy_slo_breach_60m_association_v0` — `P(breach | deploy, eligibility)`). Estimand-form caveat block added. Sister-doc rewrites: §10 walkthrough estimand paraphrase updated; `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §8 `estimand_id` aligned to the v0 association form; `README.md` v0-doctrine section carries an observational-form pointer. Surfaced by Codex round-2 critique loop on the AB-028 spike RFC (F10); backlog entry AB-033.

---

## 1. What is the prediction contract?

**Rationale:** The source contract defines the *upstream* interface — what any source must declare to be legible to ForgeWorks. The prediction contract defines the *downstream* interface — what any consumer sees when it reads a Dynamic Reliability prediction. Both exist for the same reason: the engine must not hardcode knowledge about specific sources *or* specific consumers.

**Context:** Without a contract, consumer code drifts into the engine. Every "the model outputs a 0-1 score" or "the model version is in this field" assumption becomes a coupling that breaks when the engine evolves. The contract absorbs the change so consumers don't have to.

**Simplification:** The source contract is what sources *emit*. The prediction contract is what consumers *see*.

**Analogy:** HTTP. Servers can be anything (Nginx, Node, Go, a Python script). Clients can be anything (browser, curl, mobile app, another service). Neither knows or cares about the other's implementation. The contract is the request/response shape, the status codes, the headers. Predictions need the same shape.

---

## 2. Doctrine — authority hierarchy, and v0 shadow-mode scope

**v0.1 doctrine reset** (per Codex F1, F11). The original v0 organized consumers around "operator doctrine" runtime placement — CI gates that could short-circuit deterministic checks, auto-remediation systems that could act autonomously. Codex correctly flagged that this conflates **runtime placement** with **decision authority**.

**Why shadow-mode / advisory-only in v0** *(post-hoc dispositions review 2026-07-25)*: the original v0.1 rewrite cited `.codex/config.toml [ml]` as "binding project posture." That file is user-scoped Codex-agent behavior config (lives at `~/.codex/`, not in the repo) and is **not** repo-tracked ForgeWorks doctrine. The advisory-only v0 scope still stands, but on independent grounds — F10 (self-fulfilling prediction) shows counterfactual identification is impossible without shadow-mode-first accumulation, and AB-028's feasibility spike has no evidence base yet to justify T3/T4 authority. Codifying "advisory-only v0" as repo-tracked doctrine (in `planning/SCOPE.md`, `planning/VISION.md`, or a dedicated `ML_DOCTRINE.md`) is a v1 prerequisite; see SC §5 open questions.

**Primary doctrine axis (aligned with SOURCE_CONTRACT §2):** authority hierarchy. Every consumer of a Dynamic Reliability prediction operates at exactly one tier:

| Tier | Name | v0 status | Example consumer |
|---|---|---|---|
| T1 | **Evidence generation** | ✅ In v0 | Audit sink logging every prediction for calibration |
| T2 | **Recommendation** | ✅ In v0 | Slack digest posting `at_risk` warnings to on-call |
| T3 | **Human-approved decision** | ❌ v1+ (requires doctrine change) | Deploy-gate flow that warns author but requires ack |
| T4 | **Actuation** | ❌ v1+ (requires per-class doctrine approval) | Auto-rollback, auto-scale, auto-block |

**v0 doctrinal scope:** predictions are **advisory**. Consumers at T1 (evidence) or T2 (recommendation) only. Predictions MAY annotate, prioritize, contextualize, or ask a human to look. They MAY NOT gate deterministic checks, block deployments, or trigger remediation. A prediction that says `at_risk` cannot cause any state change in ForgeWorks by itself.

**Three reasons the mirror still matters** (unchanged from v0):

**(a) Consumer diversity.** Predictions get consumed by fundamentally different systems even within T1/T2 — a dashboard needs a trend, a Slack digest needs a summary, an audit sink needs full provenance, a downstream pipeline stage needs a stream. A contract that only serves one of them well forces bespoke translation layers.

**(b) Trust and auditability.** Even a T1/T2 consumer's action (surfacing a warning, escalating an alert) needs to be *justifiable later*. The contract must carry the reasoning surface.

**(c) Doctrine coexistence.** The **reviewer-doctrine gates** (OWASP DC, Snyk, Checkov, CodeRabbit) already gate deployments at T3/T4 via existing enforcement. Their verdicts will sometimes agree with Dynamic Reliability predictions and sometimes disagree. The **decision-time arbitration** (how a T3/T4 surface reconciles a T2 recommendation with a T4 gate verdict) is out of scope for this contract — it lives in `DOCTRINE_INTERPLAY.md`. This contract only ensures every prediction carries the **arbitration reference** (§4.5) so the arbitration layer has what it needs.

---

## 3. The contract — six required fields (mirrors of source contract §3)

Every prediction carries these. Names parallel the source contract's six fields (SC §3.1–§3.6) so the symmetry is obvious.

| Source contract field | Prediction contract mirror | Why the mirror |
|---|---|---|
| **Pool** (SC §3.1) | **Scope** (§3.1) | Which pool(s) does this prediction cover; which signal role |
| **Vocabulary** (SC §3.2) | **Prediction Type** (§3.2) | The shape and enumeration of possible prediction values |
| **Timeframe** (SC §3.3) | **Horizon + Freshness** (§3.3) | What time window is being predicted, how stale the prediction itself is |
| **Identity Claims** (SC §3.4) | **Correlation Claims** (§3.4) | Namespaced identity claims for joining with source events / peer predictions / downstream actions |
| **Segmentation** (SC §3.5) | **Slice** (§3.5) | Which segmentation slice this prediction is for |
| **Governance Envelope** (SC §3.6) | **Governance Envelope** (§3.6) | Tenant / classification / retention / residency / access policy |

### 3.0 Worked estimand for v0 — the concrete question this contract predicts

*(New in v0.1, per Codex F2. **Rewritten 2026-07-27 (AB-033) — causal wording replaced with observational form; see estimand-form caveat below.**)* Predictions must be *about something specific*. The original v0 named the target as "Dynamic Reliability" without defining an operationally testable estimand — Codex correctly flagged that a portfolio-of-estimands framing needs at least one worked estimand to be legible.

**v0 worked estimand — observational form (`deploy_slo_breach_60m_association_v0`):** for a `(service, environment)` slice, predict:

> **P(an SLO breach is observed within 60 minutes of the deploy marker | the next deployment to this slice is observed, conditional on the eligibility set below)**

with:
- **Eligibility:** a deployment event exists for the slice within the horizon; the slice has ≥30 days of observation history; `input_freshness` < 5 minutes.
- **Label window:** 60 minutes post-deploy; any SLO breach in `datadog.slo_burning` / `datadog.slo_burned` state counts.
- **Censoring:** if the next deployment happens within 60 minutes (new deploy = new prediction context), the label is censored.
- **Abstention:** if eligibility fails or `input_freshness` violates the threshold, the prediction abstains (`type=abstain`).
- **Error costs:** asymmetric — false negatives (miss a real breach) cost ~10× false positives (unnecessary caution). Consumers use this to calibrate their thresholds.
- **Decision informed:** at T2, a `deploy_at_risk` recommendation surfaces to the deploy author and to `#platform-oncall`. NO gating in v0.

**Estimand ID convention:** `<domain>_<outcome>_<window>_<form>_<version>`. `form` is `association` (observational, v0-shipped) or `ate` / `cate` / `att` (causal, v1+). Version bumps on any change to eligibility, label window, censoring rule, or form.

**Estimand-form caveat — observational, not causal** *(AB-033, 2026-07-27; surfaced by Codex round-2 loop on AB-028 spike RFC, F10.)*

The estimand above is **observational**: it measures the association `P(breach | deploy, eligibility)` in the ForgeWorks observation stream. It is **not** a causal claim about deployments causing breaches. Prior wordings ("the next deployment ... **causes** an SLO breach ...") implied `P(breach | do(deploy))`, an intervention-conditional distribution that requires counterfactual identification methodology (randomized holdback / propensity-score matching / instrumental variables / doubly-robust estimation) that v0's shadow-mode-only posture cannot provide. Under v0:

- **No randomization.** Deployments are chosen by humans on non-random schedules (release calendars, incident-driven hotfixes, feature-flag rollouts). Deployment timing is confounded with the very risk factors the model tries to score.
- **No counterfactual observation.** For every deployed slice-window, the "would-have-been-if-not-deployed" outcome is unobservable; v0 has no comparison cohort of matched non-deploys.
- **Intervention-present outcomes segregated, not adjusted.** Per `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2.2, rollback / mute / deploy-pause events are labeled `intervention_present` and segregated from the primary training cohort. That prevents intervention-contaminated labels from biasing the observational estimate, but does not upgrade the estimate to causal.

**What a v0 GO verdict on this estimand supports:**

- ✅ **T1** evidence generation (audit sink logs association strength for calibration and drift monitoring).
- ✅ **T2** advisory recommendations ("this deploy is at elevated observed risk; on-call, please look" — the human decides).
- ❌ **T3/T4** gating, blocking, or actuation. Automated action against an observational risk score assumes the score would still hold under intervention, which the estimand cannot demonstrate. T3/T4 requires a causal-form estimand (`_ate_v1+` / `_cate_v1+`) and the counterfactual identification protocol in `GROUND_TRUTH_INTERVENTION_CONTRACT.md` AP-6.

**Consumer discipline:** any consumer displaying or acting on `deploy_slo_breach_60m_association_v0` MUST NOT paraphrase it as "this deploy will cause a breach" in human-facing surfaces. Correct paraphrases: "elevated observed breach risk," "historical breach-association pattern matches," "similar deploys have been followed by breaches." The estimand ID makes the observational form explicit; drift into causal language in Slack messages, dashboards, or docs regresses the fix.

This is the estimand the AB-028 feasibility spike will target — as an observational-association measurement, not a causal one. Other estimands (rollback association, incident-cluster association, cost-anomaly association) will follow the same shape: eligibility + label window + censoring + abstention + asymmetric costs + informed decision + explicit form suffix. Causal-form counterparts (`_ate_v1+`, etc.) are v1+ work gated on the identification protocol referenced above.

### 3.1 Scope

**Definition:** The pool(s) this prediction is computed over, and which signal role the prediction plays.

**Required sub-fields:**
- `pools` — one or more entries from the canonical pool set (SC §3.1). **v0 constraint: single pool only.**
- `signal_role` — one of `observation` / `recommendation` (mirrors SC §3.1 orthogonal signal roles). v0 predictions are `recommendation` (T2) or emitted for `observation` (T1, e.g. calibration logs).
- `pools_contributing_now` — which sources within the pool actually had fresh data in the freshness window.

**v0.1 change per Codex F5:** the original `cross_pool_intersect` / `cross_pool_weighted` / `cross_pool_worst` aggregation modes are **removed from v0**. Cross-pool aggregation is deferred pending: (a) a shared estimand across the pools involved, (b) explicit missingness model, (c) calibrated component models, (d) learned weights validated per pool combination. Full design in a future `CROSS_POOL_AGGREGATION_v0.md` (not yet drafted).

### 3.2 Prediction Type

**Definition:** The output vocabulary — what shape the prediction takes and what values are legal within it.

**Required sub-fields:**
- `type` — one of `score` (bounded scalar), `class` (categorical from an enum), `probability_distribution`, `abstain` (v0.1 addition: model refuses to predict for stated reason).
- `type_version` — semver of the type schema. Consumers reject predictions with an unknown `type_version` rather than coercing.
- `value` — the actual prediction, shaped per `type`.
- `value_enum` — for `class` and `probability_distribution` types, the namespaced enum (per VOCABULARY §7 model-vocab compat) this value is drawn from. Must be declared, not implied.
- `compatibility_range` — the model-vocabulary compatibility range (per VOCABULARY §7 F15). Consumers verify their handling capability before acting.
- `abstain_reason` — required when `type=abstain` (e.g., `out_of_distribution`, `input_stale`, `insufficient_data`, `calibration_degraded`).

**Design constraint:** the type is the output-side analog of the source vocabulary. Everything in `VOCABULARY_DESIGN.md` about closed sets, versioning, and evolution applies here.

**Onboarding hint:** most v0 consumers want `class` or `score`. `abstain` is first-class — a model refusing to predict is more valuable than a low-confidence guess. `probability_distribution` is useful only when the consumer will do its own downstream reasoning. `recommendation`-type (structured action suggestions) is deferred to v1+ because v0 is advisory-only.

### 3.3 Horizon + Freshness

**Definition:** The temporal envelope of the prediction — what future window it covers, and how old the prediction itself is.

**Required sub-fields:**
- `horizon` — how far into the future this prediction applies (`next_5m`, `next_1h`, `next_24h`, `next_7d`).
- `computed_at` — when the prediction was generated (ISO 8601 UTC).
- `valid_from` / `valid_until` — the wall-clock window this prediction covers.
- `input_freshness` — the oldest input data that fed the prediction. Older than the source's `max_age_useful` → prediction is degraded.
- `supersedes` — the `prediction_id` this one replaces, if any (chain-of-supersession lives in the lifecycle event stream, §5).

**Rule:** a consumer that acts on a prediction after `valid_until` is misusing the contract. The contract should make this hard — the value field itself becomes `null` past `valid_until`, with metadata still legible for audit.

### 3.4 Correlation Claims (was: Correlation Keys)

**Definition:** The namespaced identity claims this prediction carries so consumers can correlate it with source events (upstream), other predictions (peer), and downstream actions taken because of it. Mirrors SC §3.4 exactly — the same identity model, now expressed as an outgoing claim rather than incoming.

**v0.1 change per Codex F14:** the original design listed flat `service_name` / `deployment_sha` / `customer_id` keys as if they were globally-joinable. Renamed to Correlation Claims and restructured to match the source-side namespaced identity model.

**Required sub-fields:**
- `prediction_id` — unique per emission. Immutable. Never reused.
- `identity_claims` — the same shape as SC §3.4 `emitted_claims`: `(authority, key_type, value, join_reliability, validity_window)` per claim. Populated to whatever precision the prediction's slice allows.
- `source_event_ids` — a bounded set of upstream `event_id`s that most influenced this prediction (top-N by attribution weight, default N=10). Auditability, not full reproducibility.
- `parent_prediction_id` — set when this prediction is derived from another prediction. Enables audit tools to walk the dependency chain (AP-7 cascading-trust prevention).

**Design constraint:** joins to source events / other predictions go through the same **entity-resolution layer** as source-side claims (SC §3.4). No string-matching on the wire; scored resolutions.

### 3.5 Slice

**Definition:** The segmentation slice this prediction is for.

**Required sub-fields:**
- `dimensions` — the segmentation dimensions the slice uses (from SC §3.5 canonical set).
- `values` — the specific values for each dimension (`{per_service: 'webhook-gateway', per_environment: 'prod'}`).
- `slice_id` — a stable identifier for the slice, so consumers can subscribe by slice without knowing the model.

**Rule:** the slice must be a subset of the source's declared segmentation dimensions. A prediction can't be sliced on a dimension no contributing source populates.

### 3.6 Governance Envelope

**Definition:** Same required envelope as SC §3.6. Predictions inherit governance metadata from their input sources; when multiple sources contribute, the prediction takes the **strictest** classification / shortest retention / narrowest residency across inputs.

Non-optional. A prediction whose input sources have missing or conflicting governance envelopes cannot emit; the model must abstain (`type=abstain`, `abstain_reason=governance_underspecified`).

---

## 4. Additional consumer-side fields (no upstream mirror)

Four fields exist only on the downstream side — they answer questions consumers ask that sources don't need to answer. **v0.1 change:** old §4.4 "Disagreement Signals" REMOVED per Codex F7; replaced with §4.5 "Policy Reference."

### 4.1 Confidence — per prediction type

*(v0.1 rewrite per Codex F13.)* The original v0 defined a single `confidence` scalar with unclear semantics across output types. Codex flagged that correctness and interval coverage require a precisely defined event and differ by output type. Fixed:

| `type` | Confidence representation | Required sub-fields |
|---|---|---|
| `score` | Prediction interval | `interval_lower` / `interval_upper` at declared coverage (default 95%); `calibration_dataset_id`; `sample_size`; `Brier_score` or `interval_coverage` measured on the calibration cohort. |
| `class` | Calibrated class probabilities | `class_probabilities` map; `calibration_curve_ref`; `ECE` (expected calibration error) measured on the calibration cohort. |
| `probability_distribution` | Distributional metrics | `class_probabilities`; `log_loss` and `Brier_score` on the calibration cohort. |
| `abstain` | n/a | `abstain_reason` (already required); no confidence. |

**Common required metadata across all types:**
- `calibration_dataset_id` — which held-out dataset the calibration was measured on.
- `calibration_cohort` — the slice / population the calibration applies to (calibration on cohort ≠ global calibration).
- `sample_size` — how many observations backed the calibration.
- `out_of_distribution` — flag: is this prediction on inputs that look like the calibration cohort, or outside it? If outside, calibration numbers don't necessarily transfer.
- `calibration_method` — how the calibration was computed (`bootstrap`, `bayesian_posterior`, `calibration_curve`, `platt_scaling`, `isotonic_regression`, `model_native_uncalibrated`).

**Rule:** consumers reject predictions whose `calibration_method = model_native_uncalibrated` unless the consumer is explicitly opted into cold-start behavior. `out_of_distribution = true` predictions carry usable calibration warnings but consumers must weight them accordingly.

### 4.2 Provenance

**Required sub-fields:**
- `model_id` — which model produced this prediction (MLflow-anchored).
- `model_version` — semver of the model.
- `vocabulary_versions` — the source vocabulary version(s) the inputs were emitted under. Plural when the prediction spans multiple sources.
- `training_data_window` — the time window of data the model was trained on.
- `explanation_ref` *(v0.1 change per Codex F17; **forward-declared** — post-hoc note 2026-07-25)* — pointer (URI or storage key) to per-prediction attribution data, plus `explanation_method` metadata. Not raw features in the event. Actual attribution lives in an access-controlled store; consumers who need it (audit, debugging) fetch on demand. Reasons: attribution methods have different semantics; SHAP top-K on correlated features is not causal; broadcasting feature values across every event exposes input details unnecessarily. **Forward-declared caveat:** the access-controlled explanation store is not yet designed — the field is *reserved*, not backed by infra. A follow-up AB-NNN (owed by the first attribution-consuming class to land) will design the store; until then producers may emit `explanation_ref: null` with `explainability_class: sampled` and store attribution only for a sample.
- `explainability_class` — one of `full` (attribution retrievable per prediction), `sampled` (attribution retained for a sampled subset), `not_explainable_by_design` (documented rationale required, e.g., black-box vendor model).

**Rule:** predictions with `explainability_class = not_explainable_by_design` require a citation of the doctrine approval permitting the class. No black-box models slip through by omission.

### 4.3 Consumer Hints

**Required sub-fields:**
- `revalidate_after` — the timestamp at which this prediction should be re-queried even if `valid_until` hasn't passed. Enables cheap staleness checks.
- `human_readable_summary` — short natural-language description for human-facing surfaces. Never consumed by automation.
- `recommended_action` — reserved for v1+; MUST be absent in v0 (`type=recommendation` is v1+).

### 4.4 REMOVED — Disagreement Signals

*(v0.1: removed per Codex F7.)* The original v0 required `deterministic_gates_status`, `agreement`, and `disagreement_notes` on every prediction — the producer had to carry gate verdicts as a snapshot. Codex correctly flagged that (a) gate verdicts are asynchronous and mutable, so a producer-owned snapshot is stale by design; (b) my own §10 worked example demonstrated the problem — 3 PASS gates listed alongside `agreement: no_applicable_gates`.

**Resolution:** predictions and deterministic verdicts emit independently to their own streams. Agreement / arbitration is computed at **decision time** by the arbitration layer, not by the producer. See `DOCTRINE_INTERPLAY.md` for how the arbitration envelope composes prediction + gate references + applicability + policy version.

Every prediction still carries a lightweight arbitration handoff — see §4.5.

### 4.5 Policy Reference *(new in v0.1)*

**Definition:** the arbitration doctrine version this prediction was generated under. Enables `DOCTRINE_INTERPLAY.md`-based arbitration at decision time.

**Required sub-fields:**
- `policy_version` — semver of the doctrine version in effect when this prediction was emitted (e.g., `doctrine-2026-07-24-shadow-mode-v0`).
- `applicable_authority_tier` — the maximum authority tier this prediction is allowed to inform (`T1` or `T2` in v0). Consumers acting at higher tiers than this MUST ignore the prediction.
- `arbitration_envelope_hint` — optional hint about which arbitration envelope shape applies (e.g., `deploy_time_arbitration_v1`). Consumers use this to look up the correct decision-time composition.

The arbitration envelope itself (the shape a decision authority composes at decision time) is `DOCTRINE_INTERPLAY.md`'s responsibility. This field is the pointer, not the envelope.

---

## 5. Prediction lifecycle — event-based, not mutation

*(v0.1 rewrite per Codex F16, F19.)* The original v0 said predictions were "never mutated" AND simultaneously that expired values become `null` / retracted originals get a `retracted_at` field. Codex correctly flagged the contradiction: immutable Kafka event streams cannot mutate fields on already-emitted events.

**v0.1 correct model:** predictions and their lifecycle transitions are **separate event streams**. Prediction facts are immutable; state changes publish new events on a lifecycle stream.

| Stream | Event types | Purpose |
|---|---|---|
| `forge.predictions.v1` | prediction emissions | Immutable prediction facts. One event per emission. |
| `forge.predictions.lifecycle.v1` | `prediction_superseded`, `prediction_expired`, `prediction_retracted` | State transitions. Reference original `prediction_id`. |
| Current-state projection | Materialized KV view / query API *(forward-declared — post-hoc note 2026-07-25)* | Built from the two streams above. Provides "what is the current view for this slice." **Forward-declared caveat:** the KV projection infra is not yet designed; the description is *architectural intent*, not a live component. Consumers that need current state in v0 either (a) consume both event streams and reduce locally, or (b) wait for the projection to be built (owed by the first consumer that needs it — likely AB-029's runtime placement spike). |

**Topic partitioning** *(v0.1 fix per Codex F19).* The original v0 proposed `forge.predictions.<pool>.<slice_id>` — a topic per slice, which would explode Kafka topic cardinality (SC §3.5 admits `per_deployment` and other high-cardinality dimensions). Fixed:
- Small fixed set of versioned topics: `forge.predictions.v1`, `forge.predictions.lifecycle.v1`.
- Partitioned by `hash(tenant_id, slice_id)` — provides same-slice ordering guarantees without topic-per-slice cardinality.
- Consumers subscribe to the topic + filter by slice OR use the current-state projection (KV view) with change notifications.

**Consumer implications:**
- A consumer subscribed to prediction events only sees the immutable facts; to know which one is "current," it must also consume the lifecycle stream OR query the projection.
- Audit consumers (§6.5) subscribe to both streams for full historical fidelity.
- Human-facing surfaces (§6.2) prefer the projection — they want current state, not the event history.

---

## 6. Consumer patterns — v0 shadow-mode consumers only

*(v0.1 rewrite per Codex F1.)* The original v0 listed 5 consumer classes including two (deterministic-gate short-circuit and auto-remediation) that operate at T3/T4 — outside v0 scope. Fixed: 3 consumer classes in v0, 2 deferred.

### 6.1 Human-facing surface consumer (T2)

**Examples:** Slack digest to `#platform-oncall`, Grafana panel, PR-comment annotation, dashboard warning banner.
**Reads:** `value`, per-type confidence, `human_readable_summary`, `horizon`, `computed_at`, `slice`, `policy_version` (for arbitration display).
**Ignores:** `identity_claims`, `explanation_ref` (retrievable on demand via drill-down).
**Action pattern:** display, don't act. Provide drill-down affordances (link to arbitration composer, feature attribution, model card).
**In v0:** first-class. This is the primary consumer class.

### 6.2 Audit consumer (T1)

**Examples:** MLflow-backed retrospective sink, calibration-history store, ground-truth-join sink (using `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`).
**Reads:** the full contract, plus the lifecycle event stream, plus governance envelope for retention enforcement.
**Ignores:** nothing.
**Action pattern:** append-only storage with tenant-scoped access. Joins to ground-truth events for calibration measurement. Feeds retraining decisions.
**In v0:** first-class. Required for calibration to work at all.

### 6.3 Pipeline consumer (T1 or T2)

**Examples:** a downstream Flink job that consumes reliability predictions and computes higher-order signals (e.g., cross-service reliability blast radius as its own T1/T2 stream).
**Reads:** the full contract, plus `parent_prediction_id` for the chain-of-derivation.
**Ignores:** `human_readable_summary`.
**Action pattern:** treat upstream predictions as *inputs*, not as ground truth. Uncertainty compounds (AP-7). A downstream prediction consuming an upstream one at confidence 0.8 should NOT itself claim confidence >0.8 without justification.
**In v0:** first-class as long as the downstream prediction is itself T1/T2. A pipeline consumer that produces T3/T4 predictions requires a doctrine change.

### 6.4 REMOVED FROM v0 — Deterministic-gate consumer (T3/T4)

*(Deferred per F1.)* A CI check that considers short-circuiting a deterministic gate based on a prediction is a T3 or T4 surface — requires a doctrine change and is outside v0 scope. Deferred to v1+ pending: (a) evidence from AB-028 that model lift over the deterministic baseline is meaningful, (b) `DOCTRINE_INTERPLAY.md`-defined arbitration protocol, (c) explicit approval per class of gate.

### 6.5 REMOVED FROM v0 — Automation consumer (T3/T4)

*(Deferred per F1.)* Auto-remediation / auto-rollback / auto-block-deploy are all T4 surfaces. Deferred to v1+ pending shadow-mode operating history (AB-031, forthcoming) and per-class doctrine approval.

---

## 7. Prediction shape by pool — v0 typical defaults

Different pools tend toward different `type` values. Heuristic, not a rule. All confidence semantics are per-type per §4.1.

| Pool | Typical `type` | Typical horizon | Notes |
|---|---|---|---|
| `infra` | `class` (`stable` / `drifting` / `degraded` / `failing`) | `next_1h` – `next_24h` | Infra state changes on the timescale of applies; short horizons rarely useful |
| `delivery` | `score` (0-1 build/deploy success probability) | `next_5m` – `next_1h` | Aligns with typical build/deploy duration |
| `runtime` | `class` or `score` | `next_5m` – `next_1h` | Fast horizons; SLO structure often dictates the shape |
| `incident` | `probability_distribution` over incident-severity classes | `next_15m` – `next_4h` | Distributional shape lets on-call decide their own risk tolerance |
| `vcs` | `class` | `next_1h` – `next_24h` | `recommendation`-type deferred to v1+ per §3.2 |
| `product` | `score` | `next_1h` – `next_7d` | Product-facing metrics move slower; longer horizons possible |
| `business` | `score` or `probability_distribution` | `next_24h` – `next_30d` | Longest horizons; slowest to move but consequences largest |

**Namespaced enums** (v0.1): the `value_enum` for each pool is namespaced per source-contract-emitted outcomes. `infra`'s `failing` is `terraform.infra.failing`, `runtime`'s `at_risk` is `datadog.runtime.at_risk`. Never bare tokens.

**Rule:** default to the typical shape for the pool. Deviating is fine when justified — an infra pool that produces `probability_distribution` for an actively-drifting environment is reasonable. Just document why.

---

## 8. Confidence + freshness — safety mechanisms

*(v0.1 rewrite per Codex F24.)* The original v0 mandated weekly calibration refresh; Codex correctly flagged that weekly is inadequate for 5-minute-horizon predictions where drift can invalidate a model long before the next weekly job. Fixed.

**Continuous safety mechanisms (v0.1):**

- **Continuous outcome monitoring** where labels are available in real-time. As ground-truth events arrive on the label stream (per `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`), predictions get scored against outcomes as soon as the label window closes. Sliding-window calibration measurements published continuously to MLflow.
- **Cohort-level calibration** — calibration measured per slice cohort, not globally. A model may be well-calibrated on `(webhook-gateway, prod, us-east-1)` and poorly-calibrated on `(worker-batch, staging, eu-west-1)` at the same time. Cohort-level metrics catch this.
- **Data-drift alarms** — feature-distribution drift measured on the input stream, event-driven. Alarms fire on distribution shift, not calendar cadence.
- **Abstain state as first-class outcome** — when the model detects out-of-distribution inputs or calibration degradation past threshold, it emits `type=abstain` with a reason. Preferable to a low-confidence guess.
- **Circuit breakers on error budgets** — every model declares a calibration error budget (e.g., ECE ≤ 0.05 measured over rolling 24h). When the budget is exhausted, the circuit breaker fires: the model auto-fallback-routes to advisory-only (or full abstention) until re-validated. NOT a manual intervention.
- **Weekly baseline calibration refresh** — still exists as a floor, but the continuous mechanisms above are the safety net. Weekly is the audit cadence, not the safety cadence.

**Design principle:** consumers cannot detect model drift on their own; the model must self-report degradation via the `abstain` state, the confidence metadata, and the circuit-breaker fallback. Consumers reject `model_native_uncalibrated` and `out_of_distribution` predictions by default.

---

## 9. Anti-patterns — consumer-side failure modes (v0.1)

Named like the vocabulary anti-patterns so they can be pointed at in review.

**AP-1: Bare-verdict consumption.** Consumer reads only `value`, ignores confidence, freshness. **Fix:** every consumer gates on at least `confidence` (per §4.1 type-appropriate) AND `input_freshness`.

**AP-2: Stale-prediction action.** Consumer acts on a prediction past its `valid_until` (or with `input_freshness` older than the source's `max_age_useful`). **Fix:** enforce freshness gate in the consumer library, not per-consumer.

**AP-3: Uncalibrated-confidence trust.** Consumer thresholds on confidence without checking `calibration_method` and `out_of_distribution`. **Fix:** consumers reject `model_native_uncalibrated` unless opted-in for cold-start; treat `out_of_distribution = true` as reduced confidence.

**AP-4: Cross-authority-tier consumption.** Consumer operating at higher authority tier than the prediction's `applicable_authority_tier` allows. **Fix:** consumers verify `applicable_authority_tier ≥ own_tier` before acting. In v0, no consumer above T2 may act on any prediction.

**AP-5: Provenance-blind logging.** Consumer stores predictions without provenance (model_id, version, calibration ref). **Fix:** governance envelope + provenance required in audit-sink schemas.

**AP-6: Self-fulfilling prediction** *(v0.1 rewrite per Codex F10).* Original v0 acknowledged the problem but hand-waved the fix at "record that action was taken." Codex correctly flagged that this doesn't identify whether degradation would have occurred without intervention — a T3/T4 consumer that acts on `at_risk` predictions could optimize for triggering interventions rather than accuracy.

**v0.1 counterfactual protocol** (in order of preference):

1. **Shadow mode first** (this is v0's whole doctrine — no interventions fire, model learns without gaming).
2. **Controlled holdbacks** where safe — some qualifying predictions randomly don't trigger action (v1+ only, since v0 has no actions at all). Provides counterfactual data on untreated outcomes.
3. **Randomized escalation** — for interventions with variable escalation levels, randomize the level so the treatment effect at each level is estimable.
4. **Intervention propensity logging** — every intervention records (a) the prediction that triggered it, (b) the alternate action(s) considered, (c) the counterfactual estimation method used.
5. **Treatment-aware evaluation metrics** — uplift models, doubly-robust estimation. Naive accuracy on treated cases is misleading.
6. **Separate metrics** — prediction quality, intervention benefit, intervention harm — measured and reported independently. A model that predicts `at_risk` and triggers a rollback that avoids a breach was "correct" AND the intervention was "beneficial," but the two facts should never be conflated into a single "hit rate."

The full protocol is `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`'s territory; this AP just says "if you're going to enable T3/T4 in v1+, this protocol is non-negotiable."

**AP-7: Cascading trust.** Downstream pipeline consumer treats upstream predictions as ground truth. Uncertainty compounds; downstream confidence is silently invalid. **Fix:** downstream predictions must propagate upstream confidence into their own confidence computation. `parent_prediction_id` field enables the discipline; consumer libraries enforce.

**AP-8: Threshold buried in consumer code.** Consumer's action threshold is a hard-coded number. **Fix:** thresholds in repo-tracked config per consumer; consumers cite the config path in their operating-model attestation (VOCABULARY §8 AP-7).

**AP-9: Cross-consumer summary drift.** Every human-facing surface builds its own natural-language summary from structured fields. **Fix:** `human_readable_summary` is the single source of truth; consumers render it as-is.

---

## 10. Worked walkthrough — runtime-pool prediction, v0.1

Stress-test the v0.1 contract by walking one prediction through the shadow-mode consumers.

**Setup:** the `runtime`-pool model consumes DataDog vocabulary (VOCABULARY §9 v0.1 namespaced tokens) plus Terraform vocabulary (SC §4 v0.1) plus GitHub deploy events. It's asked the v0 worked estimand `deploy_slo_breach_60m_association_v0` (§3.0): "P(SLO breach observed within 60 minutes of the next deploy to `service:webhook-gateway env:prod` | that deploy is observed, eligibility satisfied)." *(Observational form per §3.0 AB-033 rewrite — the T2 surface renders this as "elevated observed breach risk," not "will cause a breach.")*

**Prediction emitted** (single event on `forge.predictions.v1`):

```yaml
prediction_id: pred_2026-07-24T10:15:03Z_a4f2b8
policy_version: doctrine-2026-07-24-shadow-mode-v0
applicable_authority_tier: T2

scope:
  pools: [runtime]
  signal_role: recommendation
  pools_contributing_now: [runtime]

prediction_type:
  type: class
  type_version: v0.1.0
  value: at_risk
  value_enum: [datadog.runtime.healthy, datadog.runtime.at_risk, datadog.runtime.regressed]
  compatibility_range:
    min_model_version: 0.1.0
    max_model_version: 0.x
    on_unknown_token: quarantine

horizon_freshness:
  horizon: next_1h
  computed_at: 2026-07-24T10:15:03Z
  valid_from: 2026-07-24T10:15:03Z
  valid_until: 2026-07-24T11:15:03Z
  input_freshness: 2026-07-24T10:14:47Z    # 16s old — within threshold
  supersedes: pred_2026-07-24T10:10:03Z_9c1e33

correlation_claims:
  identity_claims:
    - authority: internal_directory
      key_type: service_id
      value: webhook-gateway
      join_reliability: always
      validity_window: while_service_exists
    - authority: terraform_workspace
      key_type: environment
      value: prod
      join_reliability: always
      validity_window: while_workspace_exists
    - authority: cloud_provider
      key_type: region
      value: us-east-1
      join_reliability: always
      validity_window: forever
    - authority: git
      key_type: commit_id
      value: 8f3b21c
      join_reliability: always
      validity_window: forever
  source_event_ids:
    - dd_evt_78221    # datadog.entered_warn on error_rate monitor
    - dd_evt_78219    # datadog.slo_at_risk on latency SLO
    - tf_evt_11334    # terraform.apply_completed on webhook-gateway module 6 min ago
  parent_prediction_id: null

slice:
  dimensions: [per_service, per_environment]
  values: {per_service: webhook-gateway, per_environment: prod}
  slice_id: runtime_webhook-gateway_prod

governance_envelope:
  tenant_id: forge-works
  data_classification: internal
  purpose_limitation: [reliability_prediction, incident_correlation]
  retention_days: 730
  residency_region: [us-east-1]
  redaction_policy_ref: policies/redaction/runtime_v1.yaml
  access_policy_ref: policies/access/runtime_pool_v1.yaml
  cross_tenant_training_allowed: false

confidence:
  # type is 'class' → calibrated class probabilities
  class_probabilities:
    datadog.runtime.healthy: 0.15
    datadog.runtime.at_risk: 0.62
    datadog.runtime.regressed: 0.23
  calibration_curve_ref: mlflow://models/runtime-reliability-v3/calibration/2026-07-24
  ECE: 0.037
  calibration_dataset_id: runtime-holdout-2026-07-15
  calibration_cohort: {per_service: webhook-gateway, per_environment: prod}
  sample_size: 8412
  out_of_distribution: false
  calibration_method: calibration_curve

provenance:
  model_id: runtime-reliability-v3
  model_version: 3.2.1
  vocabulary_versions:
    datadog: 0.4.0
    terraform: 0.2.0
  training_data_window: 2026-04-01T00:00:00Z / 2026-07-15T00:00:00Z
  explanation_ref: mlflow://predictions/pred_2026-07-24T10:15:03Z_a4f2b8/attribution
  explainability_class: full

consumer_hints:
  revalidate_after: 2026-07-24T10:30:03Z
  human_readable_summary: >
    webhook-gateway (prod) is at-risk (62%) for the next hour.
    Latency SLO is burning error budget and error rate has crossed
    the warn threshold — both changes started ~6 minutes after
    the last apply of deployment 8f3b21c.
    Advisory only — no automated action will be taken.
  recommended_action: null    # v0 is advisory
```

**Consumer A — human-facing surface (Slack digest to `#platform-oncall`):**

Reads: `value`, `class_probabilities`, `human_readable_summary`, `horizon`, `slice`, `policy_version`. Renders:

> ⚠️ `webhook-gateway (prod)` — **at_risk** for next 1h (62% class probability).
> [full summary text]
> **Advisory only — no automated action will be taken** *(shadow-mode)*.
> [Investigate] [Ack] [Mute for 1h] [View attribution]

Ignores: `identity_claims`, `explanation_ref` (surfaced on drill-down), `calibration_dataset_id`.

**Consumer B — audit sink (MLflow retrospective store):**

Reads: the full contract, plus the lifecycle event stream, plus governance envelope for retention.
Stores: append-only, tenant-scoped. Joins to future ground-truth events (via `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`) as they arrive.
Contribution: continuous calibration measurement per cohort; when calibration ECE degrades past the model's declared budget, publishes a circuit-breaker event and the runtime pool auto-fallback-routes to full-abstention.

**Consumer C — pipeline consumer (blast-radius calculator, T1 shadow):**

Reads: this prediction as input to a higher-order T1 shadow prediction ("expected blast radius if `webhook-gateway prod` regresses given upstream/downstream dependencies").
Emits its own T1 prediction with `parent_prediction_id: pred_2026-07-24T10:15:03Z_a4f2b8`.
Its own confidence must incorporate this prediction's confidence (AP-7 discipline).

**Not-a-consumer:** the deploy pipeline. In v0, no CI/CD surface reads Dynamic Reliability predictions. This is the shadow-mode discipline — the deploy flow is unaware of the prediction stream. That changes only if AB-028 spike delivers evidence AND a doctrine change is approved for T3/T4 deployment gating.

**Contract stress-test result (v0.1):** the same prediction feeds three different consumers cleanly, none acts autonomously, all have enough context to justify their action later. Adding a fourth consumer (a Grafana panel, a PR-comment surface) requires zero engine changes — subscribe to the topic and read the same shape. Adding a T3/T4 consumer, however, requires an EXPLICIT doctrine change — not a config toggle. That's the v0 shadow-mode discipline working as designed.

---

## 11. Graduation criteria — v0 → v1

*(v0.1 rewrite per Codex F3, F4, F12, F20.)* The original v0 required "production model + two consumers + lifecycle behavior implemented" as v1 prerequisites, creating the planning deadlock Codex flagged (F4). Restructured: v0 → v1 requires *evidence*, and the experimental AB-NNN entries (see §14) accumulate that evidence *before* v1 files.

- [ ] All six required fields (§3) implemented and populated by at least one shadow-mode model.
- [ ] Per-type confidence semantics (§4.1) implemented and cohort-level calibration measured.
- [ ] Governance envelope (§3.6) enforced by the audit sink.
- [ ] Lifecycle event stream (§5) live and consumed by at least one projection.
- [ ] `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` at v0 (AB-030).
- [ ] AB-028 feasibility spike produced evidence that the model lifts over the deterministic baseline on the predeclared metrics.
- [ ] MLflow production-readiness assessment complete (AB-032; [scoping RFC v0.1](AB-032_MLFLOW_READINESS.md)).
- [ ] At least one worked "disagreement observation" documented — a shadow-mode prediction that would have disagreed with a deterministic gate had it been in the decision path, logged for post-hoc analysis. Full arbitration protocol exercise is a T3/T4 doctrine-change prereq (see AB-031), NOT a v0→v1 blocker.
- [ ] Operating model per production predictor attested (VOCABULARY §8 AP-7).
- [ ] Circuit-breaker mechanism (§8) exercised in a controlled drill.

**v1 does NOT require:** any T3/T4 consumer to exist. Those are separate doctrine changes, each earning its own AB-NNN entries under the umbrella of a v1.x actuation-doctrine RFC. `DOCTRINE_INTERPLAY.md` reaching v0 (AB-031) is a **T3/T4 doctrine-change prereq**, not a v0→v1 blocker for this contract — v0 is advisory-only, arbitration doesn't fire, so the doctrine doc's absence at v1 is tolerable. *(Post-hoc dispositions review 2026-07-25.)*

---

## 12. Open questions

- [ ] **Continuous calibration substrate** — is MLflow the right home for per-cohort continuous calibration? Or does the calibration store want to be separate (Prometheus / a custom store)? AB-032 addresses ([scoping RFC v0.1](AB-032_MLFLOW_READINESS.md); D5 capacity dimension explicitly scopes the calibration-write envelope).
- [ ] **Retraction protocol precision** — the lifecycle stream fires `prediction_retracted` events. What triggers a retraction? Model discovers it was wrong after ground-truth arrival? A calibration circuit-breaker fires? A human tags a prediction as bad? All three?
- [ ] **Cold-start handling for new models** — a new model has no calibration curve yet. §8 says consumers reject `model_native_uncalibrated` unless opted-in. What's the bootstrap protocol for the first N days of a new model?
- [ ] **Cross-consumer coordination** — when two v0 consumers surface the same prediction differently (Slack says "at_risk 62%", dashboard says "at_risk"), how do humans reconcile? Is that a UX problem to solve, or a `human_readable_summary` discipline problem?
- [ ] **Ground-truth event schema shape** *(v0.1 clarification)* — the schema is now under AB-030 (formerly deferred here). Every prediction-consumer contract depends on it. What does a `label` event on the label stream look like structurally?
- [ ] **Consumer registration** — is there a repo-tracked registry of "who consumes what predictions"? Useful for change-impact analysis when a prediction type evolves. Currently informal.
- [ ] **Per-tier consumer enforcement** — how is `applicable_authority_tier ≥ own_tier` (AP-4) actually enforced? A consumer library gate? A CI check on consumer PRs? A policy-as-code rule?
- [ ] **Cross-pool aggregation** *(deferred per F5)* — the v0.1 contract removed the cross-pool aggregation modes. When cross-pool comes back, does it want its own doc, or a §3.1 extension?

---

## 13. Related documents

- `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` *(v0.1)* — upstream mirror.
- `docs/decisions/dynamic-reliability/VOCABULARY_DESIGN.md` *(v0.1)* — deep dive on vocabulary. §3.2 (Prediction Type) inherits evolution rules from there.
- `docs/decisions/dynamic-reliability/GROUND_TRUTH_INTERVENTION_CONTRACT.md` *(drafted v0)* — the label + intervention stream. Prediction contract's §6.2, §8, §9 AP-6 all depend on it.
- `docs/decisions/dynamic-reliability/DOCTRINE_INTERPLAY.md` *(drafted v0)* — decision-time arbitration envelope; consumer of prediction + gate streams.
- `planning/IMPORTANT_IDEA.md` — origin discussion (ephemeral).
- `planning/WIRE_PROTOCOL.md` — JSON vs. Avro vs. Protobuf. Not yet drafted; affects the field serialization in §3-§4.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-028 through AB-032 filed 2026-07-24.

---

## 14. Iteration protocol

Same as sibling design docs (v0.1 aligned with SC §6):
- Substantive changes bump `v0` → `v0.1` → `v0.2` → …
- Experimental AB-NNN entries file BEFORE v1 (AB-028 through AB-032 filed 2026-07-24). v1 is the stabilization/retrospective on those entries, not the prerequisite.
- Graduates to v1.0 when the §11 checklist is met.
- On v1.0, this doc's content moves to `docs/decisions/DYNAMIC_RELIABILITY.md` and this file can be deleted along with `IMPORTANT_IDEA.md` and siblings.
