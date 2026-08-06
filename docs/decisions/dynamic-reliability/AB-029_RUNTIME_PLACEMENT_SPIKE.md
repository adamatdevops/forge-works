# AB-029 Runtime Placement Architecture Spike RFC (v0.2 draft) — where do Dynamic Reliability predictors actually run?

> **Status:** Scoping draft (v0.2). Not yet approved for execution. Approval means: the 6 options are locked in, the 8 benchmark dimensions are locked in, and the spike may begin instrumentation.
> **Owner:** Platform team (spike execution owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Runs in parallel with:** AB-028 feasibility spike. Shares AB-028's reference workload where useful. Independent of contract graduation.
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-029` (backlog is repo-ignored; canonical scope on this document).
> **Option A pre-implementation acknowledged:** commits `0a1c406` (PR #31) and prior benchmark-framework scaffold shipped Option A's sibling-Flink module (`src/flink-jobs/dr-predictor/`, 8 Java files) + a `SiblingFlinkPrototype` Python class with static D4 / D7 scores of 5 BEFORE this RFC reached scoping-approval. Options B–F remain stubs. Scoring is frozen until parity is restored under §8 R1 remediation.

---

## 1. Why this spike exists

Codex round-1 loop on the design corpus (retrospective at `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md`, F18) flagged that SC §2 + PC §5 selected streaming Flink + Kafka as the runtime placement BEFORE establishing the latency, throughput, state, model-size, or availability requirements that justify it. The design corpus is doctrine-neutral about placement; the assumption "we run in Flink because ForgeWorks runs in Flink" needs evidence.

This spike closes that gap. Its output — a documented comparison matrix across 6 placement options, benchmarked on the same reference workload against pre-declared dimensions with absolute score anchors and corpus-non-negotiable hard gates — turns the placement choice from *default* into *justified*.

The spike is deliberately **architecture-only, no live traffic, uses AB-028's reference workload for representative benchmarking**. Its purpose is to answer one question: which placement option best fits ForgeWorks's Dynamic Reliability v0 constraints (advisory-only, shadow-mode, calibration-observable), while leaving room for v1+ upgrades?

---

## 2. Scope

### 2.1 In-scope

- **Six placement options** (§3) evaluated against eight dimensions (§4).
- **Reference workload:** the AB-028 spike's deploy-SLO-breach estimand on `(webhook-gateway, prod)`. Same input events, same feature construction. Enables apples-to-apples comparison. Model class + feature construction dependency management per §5.1.
- **Prototype-scale benchmarks:** each option gets a minimal prototype running the AB-028 model against 30 days of historical events; measurements collected per §4 dimensions.
- **Comparison matrix (§6):** each option × each dimension, with quantitative measurements where possible, qualitative scoring where not.
- **Recommendation:** primary + fallback option, with the specific evidence that supports the ranking.
- **Contract-level implications surfaced:** if the winning option implies SC / PC / VOC / GT changes, capture the *proposal + impact analysis* in the Decision Record. Any actual contract amendment ships as a **separately reviewed, separately owned PR** after the Decision Record is accepted — the runtime winner does not itself approve doctrine changes (see §7).

### 2.2 Out-of-scope

- **Production-scale load testing.** v0 is shadow-mode / advisory-only; production throughput isn't the constraint. Prototype-scale (30-day replay) suffices for a placement decision.
- **Model performance re-evaluation.** AB-028 owns model quality; this spike takes the AB-028 model as-is and measures the RUNTIME properties around it.
- **T3/T4 actuation placement.** All 6 options are evaluated for T1/T2 (evidence + recommendation) only. T3/T4 placement is a separate doctrine change (see corpus README §v0 doctrine).
- **Multi-tenant / multi-region deployment.** v0 is single-tenant (`forge-works` per governance envelope). Cross-region placement is a v1+ concern.
- **Cost optimization beyond first-pass.** Cost per prediction is one dimension (§4), but full FinOps analysis (spot pricing, reserved instances, autoscaling profiles) is out of scope; representative on-demand pricing suffices.

### 2.3 Non-goals

- **Not a bake-off with a winner-take-all mandate.** The output is a comparison matrix + recommendation; the recommendation may be "primary X, fallback Y, revisit at v1" rather than "X is best forever."
- **Not a rewrite of the corpus.** Placement affects PC §3.3 / §4.3 (freshness metadata) and possibly SC §5 (source access patterns); it does not touch the contract SHAPES (§2.1 required fields, §3 estimand definitions, §4 confidence semantics).
- **Not tightly coupled to AB-028 execution results.** Uses AB-028's *reference workload construction* (deploy-SLO-breach on webhook-gateway prod), not AB-028's *results*. Runs in parallel — but see §5.1 for the model-class dependency gate.

### 2.4 Assumed workload envelope

Weights in §6.2 and gates in §6.3 are derived from the following predeclared v0 shadow-mode envelope. If measurement reveals reality exceeds any bound by ≥10×, the scoping-approval assumption is void and weights must be re-derived.

| Property | v0 assumption | Derived from |
|----------|---------------|--------------|
| Baseline event rate | ≤ 50 events/sec (webhook-gateway prod slice, normalized events) | Existing normalizer throughput on `forge.events.normalized.v1` |
| Prediction cadence | ≤ 10 predictions/min (one per deploy event, shadow-mode) | AB-028 §4.1 slice scope + deploy-marker frequency |
| Prediction volume | ≤ 1M predictions / month | Extrapolation from cadence × 30d |
| Slice count | 1 (webhook-gateway × prod) | AB-028 §4.1 |
| Model count | 1 (deploy_slo_breach_60m_association_v0) | AB-028 §5.3 spike scope |
| Model size | ≤ 10 MB (logistic regression or small tree ensemble; see §5.1) | AB-028 §5.3 candidates |
| Retention (predictions) | ≥ 90 days | PC §5 lifecycle + calibration horizon |
| Concurrent model rollouts | ≤ 1 | v0 no A/B testing |
| Expected v0.x growth | slice count → 3, model count → 3 | Corpus §Follow-ups AB-028..032 evolution |

This envelope is a scoping-approval input, not a spike deliverable. AB-028 execution may refine specific numbers; if that happens, RFC amendment per §12.

---

## 3. Placement options under evaluation

Each option describes: what it is, why it might win, why it might lose.

### 3.1 Option A — Sibling Flink job (baseline)

- **What:** New Flink job under `src/flink-jobs/dr-predictor/`, sibling to existing `pattern-matcher`, `event-router`, `insight-generator`. Consumes normalized events off Kafka, emits predictions to a new topic, calibration events to MLflow.
- **Why might win:** Matches every existing operational surface (deploy, monitor, scale). Team already runs 3 Flink jobs; adding a 4th is the lowest cognitive load. Backpressure + replay handled by Flink primitives.
- **Why might lose:** Model loading + inference inside Flink JVM adds ~200MB memory footprint per TaskManager per model; if we ship 10+ models this scales poorly. Also: Flink checkpointing overhead for a mostly-stateless predictor is wasted.

### 3.2 Option B — Extension of existing `pattern-matcher` Flink job

- **What:** `pattern-matcher` gains a new operator branch that runs the DR predictor alongside its existing pattern detection.
- **Why might win:** Fewer moving parts (one Flink job vs. two). Shared consumer group → automatic parallelism alignment.
- **Why might lose:** Concept mixing — `pattern-matcher` is a deterministic rule engine; DR is probabilistic inference. Failure in one path shouldn't take down the other, but shared job means shared failure domain. Cognitive load on future maintainers who don't expect ML inference inside a pattern matcher.

### 3.3 Option C — Extension of existing `insight-generator` Flink job

- **What:** `insight-generator` gains a DR-predictor operator. Naturally aligned since `insight-generator` already produces "here's what I noticed" outputs.
- **Why might win:** Concept fit is best of the "extend existing" options — inference-shaped output is what `insight-generator` already does. Shared calibration/output plumbing.
- **Why might lose:** Same shared-failure-domain concern as B. Plus: `insight-generator` may have its own scaling profile (bursty on incident correlation) that differs from DR predictor's steady-state profile.

### 3.4 Option D — Scheduled batch job + materialized-view store + change notifications

- **What (pinned candidate):** **Airflow scheduled DAG + in-cluster Postgres materialized view + lightweight Kafka change-notification topic.** DAG runs every 60s (configurable); reads recent events from `forge.events.normalized.v1` via Kafka consumer offset; scores in Python (sklearn / XGBoost); upserts predictions to a Postgres table; publishes `forge.predictions.dynamic_reliability.v1` change notifications after each write. (Variants deliberately excluded: warehouse read (BigQuery / Snowflake — data-residency + governance concerns per §6.3 hard gate); Prefect / Dagster / Argo Workflows (Airflow already deployed under `infra/airflow/`, alternative orchestrators would carry unquantified cognitive-load penalty in §4 D7 without evidence-backed justification).)
- **Why might win:** Simplest operational model. Python-native → any model class works (sklearn, XGBoost, PyTorch). No JVM. Model rollout = redeploy a Python service.
- **Why might lose:** Latency floor = batch interval + processing time. If DR predictions need to surface within ~60s of a deploy marker, batch is too slow. Freshness semantics are covered by existing PC §3.3 `input_freshness` + `valid_until` and §4.3 `revalidate_after`; no new contract field required, but the batch option must populate these accurately.

### 3.5 Option E — Dedicated inference service (KServe)

- **What (pinned candidate):** **KServe (Kubeflow) InferenceService** in the existing `forge-works` cluster, backed by an sklearn-runtime pod pulling models from the MLflow registry (AB-032 dependency). Thin Flink job consumes events from `forge.events.normalized.v1`, calls the KServe endpoint via gRPC, writes predictions back to `forge.predictions.dynamic_reliability.v1`. (Variants deliberately excluded: NVIDIA Triton (GPU-optimized, no v0 GPU need; larger operational footprint than KServe for CPU-only sklearn); TF Serving / TorchServe (framework-specific, no v0 TensorFlow/PyTorch commitment); BentoML / Ray Serve / custom FastAPI (unquantified operational maturity vs KServe's Kubernetes-native lifecycle).)
- **Why might win:** Best model-flexibility story — batching, canary deploys, model versioning, A/B testing all first-class via KServe. Model rollout = MLflow registry push + KServe revision. First-class ties to AB-032 MLflow readiness dimensions.
- **Why might lose:** Highest operational complexity. New service to run, monitor, on-call. Cross-service latency (Flink ↔ KServe) is a new failure mode. Overkill for v0 model class (small logistic regression or tree ensemble per §5.1). AB-032 verdict on registry governance is a hard prerequisite (see §6.3).

### 3.6 Option F — Standalone Python Kafka consumer

- **What (pinned candidate):** **Python `aiokafka` consumer service** deployed as a Kubernetes Deployment (3 replicas, consumer-group parallelism), reads `forge.events.normalized.v1`, scores in Python (sklearn / XGBoost), publishes predictions to `forge.predictions.dynamic_reliability.v1` via `aiokafka` producer, writes calibration events to MLflow. State (windowed features) held in Redis via existing `redis` deployment. Consumer-lag-driven autoscaling via keda scaling adapter.
- **Why might win:** Streaming (not batch) + Python (not JVM) — combines Option D's Python-native model flexibility with Option A's freshness envelope. Team already runs Python (backend), so no new language. No new orchestrator (K8s Deployment).
- **Why might lose:** Consumer-group management, backpressure, state, and exactly-once delivery are all manual (Flink primitives replaced by application code). Redis-for-state adds an operational surface. Lower ceiling on parallelism vs Flink for high-fanout slices at v1+ scale. Cognitive load medium — Python patterns are new (Kafka consumer-group management, keda-driven scaling) even if the language is not.

---

## 4. Benchmark dimensions

Each option is measured against these eight dimensions. Measurements collected on the AB-028 reference workload (30 days of historical events, deploy-SLO-breach estimand, webhook-gateway prod slice).

| # | Dimension | Measurement | Units |
|---|-----------|-------------|-------|
| D1 | **Historical reproducibility** | Time to reproduce the last 30 days of predictions from each option's canonical retained source (Kafka offset zero for streaming options; warehouse/table timestamp for batch; MLflow experiment replay for KServe). Common correctness threshold: byte-identical predictions on ≥99.9% of replayed events. | seconds + completion % |
| D2 | **Backpressure handling** | Behavior at 10× §2.4 baseline input rate (500 events/sec) — does it queue, drop, block upstream, or degrade gracefully? | qualitative + max sustainable QPS |
| D3 | **Model rollout mechanics** | Steps + time from "new model artifact in MLflow registry" to "predictions using new model" | ordered steps + wall-clock |
| D4 | **Failure isolation** | Impact of predictor crash on: (a) other Flink jobs / co-located jobs, (b) Kafka backlog, (c) upstream data producers. Explicitly measures blast radius when the predictor faults; operability sub-checks (telemetry / MTTR / rollback / abstention) live in D8. | qualitative severity |
| D5 | **Cost per prediction** | Fully-loaded infra cost for 1M predictions (compute + storage + network) at representative on-demand pricing | USD |
| D6 | **Latency envelope** | Wall-clock time from source event committed to Kafka to prediction available to consumer | p50 / p95 / p99 milliseconds |
| D7 | **Cognitive load on platform team** | New concepts, tools, or runbooks required. Baseline: existing Flink stack. | qualitative 1-5 + concrete new-concept list |
| D8 | **Evidence integrity + operability** | Composite dimension covering: (a) replay determinism (does D1 replay produce identical predictions?); (b) prediction identity stability under retry (idempotent write to the output topic / view); (c) full PC §3 field-conformance emission (every required field populated on every prediction); (d) lifecycle event delivery per PC §5 (no dropped `superseded` / `expired` events under crash + restart); (e) label-join viability per GT §7 join key (predictions remain joinable to independently validated label events); (f) audit-sink completeness under retry and crash (MLflow tracking log receives 100% of predictions); (g) operability: predeclared telemetry (Prometheus metrics), alerting (SLO-tied), MTTR envelope, rollback path, model fallback/abstention behavior, runbook executability, ownership attestation. | qualitative + coverage % per sub-check |

---

## 5. Benchmark methodology

- **Reference workload:** AB-028's deploy-SLO-breach on `(webhook-gateway, prod)`. Same 30-day window (see AB-028 §4.1). Same feature construction (AB-028 §4.3). Same model class per the §5.1 dependency gate below.
- **Prototype scale:** each option runs a minimal viable prototype — just enough to measure, not production-ready. E.g., Option D uses the pinned Airflow-DAG + Postgres candidate from §3.4, not a full DataOps setup.
- **Shared instrumentation:** predictions emitted by every option go to the same audit sink (MLflow tracking log per PC §4.2 + AB-028's evaluation log per AB-028 §7 deliverables). This ensures the comparison is on runtime properties, not measurement drift.
- **Shared infrastructure topology:** all six options run in the same in-cluster environment (`forge-works` cluster, one dedicated namespace per prototype, common resource quota derived from §2.4 baseline event rate). Cross-option infra parity is a scoring input, not a nuisance to be normalized post-hoc.
  - **Options B and C special case:** the *shared-failure-domain* property they derive from co-existing with `pattern-matcher` (B) or `insight-generator` (C) IS what §4 D4 is measuring. Running B/C in isolated namespaces would defeat the measurement. B/C prototypes MUST run inside the actual sibling job (as a new operator branch or add-on), then D4 is measured via explicit failure-injection tests (kill the sibling operator, observe crash-propagation into the DR predictor path).
  - **Fixed-cost normalization:** report both shared-fixed-cost (allocated fraction for B/C) and dedicated-fixed-cost (own quota for A/D/E/F) so §4 D5 comparison is apples-to-apples.
- **Sample size:** each measurement repeated 3 times; report mean + range. Cost measurements are single-run + extrapolated (repeating full 30-day replay 3× is prohibitively expensive).

### 5.1 AB-028 dependency management

§5's "same feature construction (AB-028 §4.3)" and "same model class" are inputs, not outputs — AB-029 cannot proceed to measurement without them locked. AB-028 has not executed as of RFC v0.2.

**Gate:** at scoping-approval, one of the following MUST be true:

- **Path A (preferred):** AB-028 pre-locks the model class + feature-construction spec as a lightweight pre-execution commitment (a `docs/decisions/dynamic-reliability/AB-028_MODEL_SPEC.md` v0.1 or an AB-028 RFC §5.3 update). AB-029 §5 reference workload cites that spec directly.
- **Path B (portable-bundle fallback):** AB-029 pre-declares its own portable benchmark bundle independent of AB-028's execution: a fixed feature-set (subset of AB-028 §4.3), a fixed sklearn logistic-regression baseline (declared here, not delegated), and — if a tree-ensemble is a live candidate for AB-028 — a second sklearn `HistGradientBoostingClassifier` bundle. Each option is measured under both bundles; §6 comparison reports rankings under each. AB-028 execution later either confirms one bundle as canonical or invalidates a placement decision that only held under the other.

**Path B is the safety net** — if Path A hasn't materialized 5 business days before scoping-approval, AB-029 executes under Path B and files an amendment note explaining the choice.

**Consequence for §9 timeline:** T+0 = scoping-approval + Path A/B resolution. T+1w starts model-bundle preparation, not prototype scaffolding.

---

## 6. Predeclared decision framework

### 6.1 Comparison matrix

The spike output is a 6×8 matrix (6 options × 8 dimensions) with measurements per cell. Each cell also carries a qualitative note (e.g., "Option A D2 backpressure: 8000 QPS sustained; graceful degradation via checkpoint pause") so the comparison is auditable.

### 6.2 Scoring

Per-dimension score: 1 (worst-tolerable) to 5 (best-in-class), against **absolute anchors predeclared in §6.2.1** — NOT relative to the other options. Ties allowed. Rationale MUST be one sentence per cell.

Weighting (predeclared, locked at scoping-approval; rationale grounded in §2.4 workload envelope):

| Dimension | Weight | Why |
|-----------|--------|-----|
| D1 Historical reproducibility | 3 | Retraining + audit-window reconstruction require bounded recomputation time; missing this makes retraining slow, not calibration impossible (per §4 D1 revised framing). |
| D2 Backpressure | 2 | §2.4 baseline is ≤50 events/sec; §4 D2 10× headroom (500 events/sec) is adequate for v0. Weight bumps to 3 if §2.4 envelope invalidates (per §2.4 clause). |
| D3 Model rollout | 4 | We WILL iterate on models; friction here compounds. §2.4 assumes model count grows 1→3 at v0.x. |
| D4 Failure isolation | 4 | Advisory-only means low blast radius, but engineer trust depends on isolation from deterministic paths. |
| D5 Cost per prediction | 2 | §2.4 assumes ≤1M predictions/month; cost is a v1 concern unless an option is >10× more expensive than the rest (retained). |
| D6 Latency envelope | 3 | Deploy-SLO-breach estimand is ~60min horizon; latency <60s is more than sufficient. |
| D7 Cognitive load | 3 | Real cost paid every day; underweighting this leads to abandoned tech. |
| D8 Evidence integrity + operability | 4 | Corpus non-negotiable per README §Graduation criteria (live lifecycle stream, cohort calibration, audit-sink enforcement, attested operating model). An option that ships fast predictions but silently drops 30% is unacceptable. |

Weighted score per option = Σ(dimension_score × dimension_weight). Maximum possible = 5 × (3+2+4+4+2+3+3+4) = 125. Recommendation = highest score of options that pass ALL §6.3 hard gates, with fallback = second-highest passing option if within 10% of top score. Sensitivity analysis per §6.2.2 must confirm rank stability before recommendation is issued.

### 6.2.1 Absolute score anchors

Anchors are absolute (not relative). "Missing data" = score 0 = failure to measure, escalate to methodology fix in a follow-up round; NOT a proxy for a low score.

| Dim | Score 1 (worst-tolerable) | Score 3 (baseline-acceptable) | Score 5 (best-in-class) |
|-----|---------------------------|-------------------------------|-------------------------|
| D1 | >12h to reproduce 30d; <99% byte-identical | ≤4h; ≥99.5% byte-identical | ≤1h; ≥99.99% byte-identical |
| D2 | Blocks upstream at 5× baseline | Queues + graceful degradation at 10× baseline | Sustains 10× with no consumer-lag growth |
| D3 | ≥8 manual steps OR ≥60min wall-clock | 3-5 steps AND ≤15min wall-clock | 1-2 steps AND ≤5min wall-clock |
| D4 | Predictor crash takes down ≥1 sibling job OR blocks upstream Kafka producers | Predictor crash isolated to own consumer group; sibling jobs continue | Predictor crash isolated; automatic recovery <30s |
| D5 | >$1000 / 1M predictions | $100-$1000 / 1M | ≤$100 / 1M |
| D6 | p95 >30s | p95 ≤10s | p95 ≤1s |
| D7 | ≥3 new tools/languages AND ≥2 new runbook categories | 1-2 new concepts, extending existing runbooks | 0 new concepts; all patterns exist in current stack |
| D8 | Any sub-check <80% coverage OR any listed sub-check missing telemetry | All 7 sub-checks ≥95% coverage; predeclared telemetry + alerting; MTTR ≤ 15min | All 7 sub-checks ≥99% coverage; SLO-tied alerting; MTTR ≤ 5min; abstention path exercised in drill |

An option unable to be measured on a dimension (e.g., §4 D1 for an implementation that cannot replay) scores 0 for that dimension — which via §6.3 hard gates disqualifies the option from a recommendation.

### 6.2.2 Sensitivity analysis (mandatory before recommendation)

Weighted-sum ranking over ordinal 1-5 scores is fragile. Before issuing the recommendation:

- Recompute rank under ±1 score perturbation per cell (worst-case direction per option) — do rank orderings survive?
- Recompute rank under ±1 weight perturbation per dimension — do rank orderings survive?
- Report Pareto dominance across all 6 options (no option strictly worse across all 8 dimensions than any other option should exist among finalists).
- If winner is not robust (rank flips under any perturbation OR does not strictly Pareto-dominate the runner-up on ≥5 of 8 dimensions), recommendation is conditional: "primary X pending confirmation on dimension Y" or "primary X and Y tied — decision requires additional dimension weight decision."

### 6.3 Go / no-go per option — absolute hard gates

Gates are applied BEFORE scoring. Any option failing ANY gate is disqualified regardless of scores on other dimensions. Gates are absolute (against §6.2.1 anchors and framework doctrine), NOT derived from relative rank.

**Structural gates:**

- **G1 — Score ≥ 3 on all weight-4 dimensions (D3, D4, D8).** A "worst-tolerable" (score 1 or 2) on any high-weight dimension is a doctrinal failure, not a trade-off. Distinguish from the removed v0.1 rule "score = 1 with weight ≥ 3" — that rule was invalid because §6.2 v0.1 scores were relative.
- **G2 — No breaking changes to PC §3 estimand semantics or GT §2.1 required fields.** Structural corpus incompatibility.

**Corpus non-negotiables (from README §v0 doctrine + §Graduation criteria):**

- **G3 — T1/T2-only authority.** Any option whose only viable operating mode requires T3/T4 authority (e.g., inference-service configuration that mandates auto-remediation) is disqualified — v0 is advisory-only.
- **G4 — Full PC §3 emission conformance.** Option must be capable of populating every required PC §3 field on every prediction, verified in D8.
- **G5 — Governance envelope enforcement.** Option must preserve strictest-input classification, retention, residency, purpose limitation, access control, and abstention-on-underspecification. Any option requiring data egress from the `forge-works` cluster (e.g., managed inference service, warehouse read) that cannot enforce residency + access-control policies is disqualified. Verified via D8 sub-check (e) and a governance test.
- **G6 — Model-artifact immutability.** Option must consume model versions as immutable references (e.g., an MLflow registered-model version, not a mutable pointer). Mirrors AB-032 §6.3 model-immutability disqualification rule.
- **G7 — Audit + lifecycle event delivery.** Option must deliver PC §5 lifecycle events (`superseded`, `expired`, etc.) reliably; verified in D8 sub-check (d).
- **G8 — Label-join viability.** Predictions must remain joinable to independently validated label events via the GT §7 join key (see §10 AB-030 clarification); verified in D8 sub-check (e).
- **G9 — Abstention / fallback path exists.** If model artifact is unavailable, feature freshness is stale (per PC §3.3 `input_freshness`), or scoring times out, option must have a documented abstention path (`type=abstain` with `reason`) rather than emit a degraded prediction or fail silently. Verified in D8 sub-check (g).
- **G10 — MLflow-dependent options block on AB-032 verdict.** Options E and F (and any variant of A that loads models from MLflow) cannot be scored a production-ready recommendation before AB-032 assessment closes with a GO verdict. If AB-032 verdict is NO-GO or pending at scoring time, the option is scoped as "conditional on AB-032 GO" in the Decision Record and MAY still be primary/fallback but with an explicit AB-032-blocker note.

Disqualification MUST be documented per option with the specific failing gate + evidence, not silently dropped. An option disqualified under one gate may still be scored on the remaining dimensions for retrospective learning; it just cannot be the recommendation.

---

## 7. Deliverables

- Comparison matrix published in the spike report at `research/spikes/AB-029-runtime-placement/<timestamp>/matrix.md` (or similar path; final location decided at execution). Matrix includes: raw measurements per cell, absolute score per §6.2.1, disqualification gate results per §6.3, sensitivity analysis per §6.2.2.
- Prototype code for each option retained in `research/spikes/AB-029-runtime-placement/prototypes/<option>/` — deliberately marked as prototype-quality, not production candidates. Option A's pre-existing scaffold under `src/flink-jobs/dr-predictor/` is treated as its prototype; §8 R1 remediation governs the effort-parity check.
- Recommendation issued in a Decision Record at `docs/decisions/dynamic-reliability/RUNTIME_PLACEMENT.md` (v0) — **canonical placement doctrine for the v0 reference workload only** (webhook-gateway prod, deploy-SLO-breach 60m association estimand, §2.4 workload envelope). Captures: chosen primary, chosen fallback, evidence supporting the ranking, disqualified options + why, sensitivity analysis, and **contract-level implication proposals + impact analyses** (see §7.1) — but NOT the amendments themselves.
- **Contract amendment PRs (SC / PC / VOC / GT) are separately reviewed and separately owned** — filed AFTER the Decision Record is accepted, each with its own reviewer set and per-doc owner. The runtime winner does not itself approve doctrine changes.
- Backlog entry AB-029 acceptance criteria checked off (comparison matrix + recommendation + Decision Record + amendment proposals filed to owners).

### 7.1 Mandatory reassessment triggers on the RUNTIME_PLACEMENT decision

The Decision Record commits to reassessment (re-run this RFC's methodology on the recommended option + at least the runner-up) whenever ANY of the following triggers fire:

- Model format changes (e.g., logistic regression → gradient-boosted tree ensemble → deep model).
- Model size increases ≥2× the size at recommendation time.
- Model count in production ≥3 (from §2.4 v0 assumption of 1).
- Baseline event rate exceeds §2.4 envelope by ≥5× (from ≤50 events/sec → ≥250 events/sec).
- New slice added beyond `(webhook-gateway, prod)`.
- Availability target changes from advisory-only to any consumer requiring an uptime SLO.
- Tenancy or region expansion (any cross-cluster, cross-region, or multi-tenant consumer).
- T3/T4 authority proposed for any consumer of these predictions (requires the entire authority-hierarchy reassessment per README §v0 doctrine).

Reassessment does not automatically flip the recommendation — it re-runs the methodology, publishes the updated matrix, and issues a Decision Record amendment (retain / flip / conditional).

---

## 8. Risks

- **R1 — Prototype quality bias + Option A pre-implementation.** A well-instrumented prototype for one option may look better than a rushed prototype for another. **Option A is not starting from zero:** commits `0a1c406` (PR #31, `feat(dr): AB-029 Option A sibling-Flink prototype v0.1.0`) shipped 8 Java files under `src/flink-jobs/dr-predictor/` plus a Python `SiblingFlinkPrototype` class in `src/runtime-placement-benchmark/forge_works/dr/ab029_spike/prototypes.py` that already assigns static D4=5 and D7=5. The pre-implementation was documented in the CHANGELOG at PR-time as "first real prototype," but transparency does not offset scoring asymmetry against Options B–F which are stubs. Mitigation: (a) **scoring is FROZEN** on all options until (b) equivalent bootstrap effort has been invested in Options B–F (same author, ≤2 days each, tracked by commit + timesheet) OR (c) scoring is performed by a blinded reviewer against §6.2.1 absolute anchors, with option identities anonymized. Choice between (b) and (c) is a scoping-approval input. Option A's D4=5 and D7=5 static values are RESET to "not scored" until the parity condition is met.
- **R2 — Measurement drift.** Different options may report metrics differently. Mitigation: shared MLflow tracking sink + explicit metric definitions in §4; single-source-of-truth for the AB-028 reference workload.
- **R3 — Scoring hindsight bias.** Weights (§6.2) locked at scoping-approval BEFORE measurements. If measurements reveal a dimension is more/less important than pre-declared, that's a note for the Decision Record but does NOT retroactively change the ranking.
- **R4 — 6 options is a lot.** If early measurements clearly disqualify 2+ options via §6.3 rules, spike may reduce to 3 finalists and re-scope. Document any option dropped and why.
- **R5 — Recommendation may be "none of the above."** If all 6 options score below a floor (e.g., top score < 40 / max 105 — per §6.2 weights across D1-D8), the recommendation is to spike a 7th option. Not a failure — a valid outcome for a scoping spike. (v0.1 wording said "spike a 6th"; Option F was added in v0.2 as the resolution of that gap — the escalation path is therefore now a 7th, not repeat of Option F.)

---

## 9. Timeline (indicative — not committed)

- **T + 0:** Scoping-approval on this RFC. §3 options and §4 dimensions and §6.2 weights locked; §5 methodology refinements permitted.
- **T + 1w:** Prototype scaffolding for all 6 options (skeleton + AB-028 workload wired in).
- **T + 2w:** Measurement runs 1 (all 6 options × all 8 dimensions).
- **T + 3w:** Measurement runs 2 + 3 (repeats for D1–D4, D6, D8); §6.3 disqualification review.
- **T + 4w:** Comparison matrix compiled; Decision Record drafted with recommendation; contract-implications PRs (if any) drafted.

Timeline is indicative. Runs in parallel with AB-028 feasibility spike execution; can share the AB-028 workload harness once AB-028 begins execution.

---

## 10. Related documents

- [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) *(v0.2)* — reference workload source. AB-029 uses AB-028's deploy-SLO-breach worked estimand as the benchmark input. Model-class + feature-construction coupling managed per §5.1 dependency gate (not independent — depends on either an AB-028 pre-execution model-spec lock (Path A) or an AB-029 portable-bundle fallback (Path B)).
- [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) *(v0.5, library v0.1.0 shipped)* — AB-030 validates *label* events (`forge.events.ground_truth.v1`), NOT prediction events. Every AB-029 option emits predictions (`forge.predictions.dynamic_reliability.v1`), not labels — so the library is NOT wired into prediction emission. What each option DOES owe: predictions must remain joinable to the independently validated label stream via the GT §7 join key (see §6.3 gate G8 + §4 D8 sub-check (e)). If a future option owns a separately deployed label-producing component (none of A–F do at v0), that component would then wire the library.
- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) *(v0.1)* — batch/freshness semantics are covered by existing §3.3 (`computed_at`, `valid_from`, `valid_until`, `input_freshness`) and §4.3 (`revalidate_after`); no new `staleness` field required for Option D. PC §5 is prediction lifecycle events, distinct from freshness metadata. Contract-level implications, if any, are surfaced in the Decision Record as *proposals + impact analyses*; actual amendments ship as separate PC-owned PRs (per §7).
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) *(v0.1)* — SC §2 source access patterns may need annotation per placement option (streaming consumer vs. batch reader). Any such annotation ships as a separate SC-owned PR per §7.
- [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) *(v0.3)* — every option consumes the same GT contract for its label-join viability (§6.3 gate G8, §4 D8 sub-check (e)). No option emits labels; the label producer is a separately owned component (AB-030 library consumer).
- [`AB-032_MLFLOW_READINESS.md`](AB-032_MLFLOW_READINESS.md) *(v0.1)* — MLflow-dependent options (E, F, and Option A variants that load from registry) block on AB-032 verdict per §6.3 gate G10. AB-032 is prerequisite, not sister-spike-only.
- [`README.md`](README.md) — corpus index. AB-029 v0.1 already listed in the in-flight-spike-RFCs table (2026-07-29 entry); v0.2 lift will update the row + provenance in the same PR.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-029 entry tracks execution status.

---

## 11. Provenance

- **2026-07-29:** v0.1 draft. Codex round-1 loop on design corpus (2026-07-24, F18) flagged that placement was chosen without evidence; this RFC scopes the evidence spike. Runs in parallel with AB-028 (`3bc95ef` on main). Base commit: current main tip (`661aff5`).
- **2026-08-02:** v0.1 → v0.2 lift. Codex round-1 loop on this RFC (audit trail at `research/feedback_loops/dynamic-reliability-AB-029_RUNTIME_PLACEMENT_SPIKE/20260802T094334Z/` — repo-ignored, per corpus convention) returned `needs-revision` with 18 findings (10 HIGH / 8 MEDIUM). 14 findings applied directly; 2 refined into structural mergers (governance folded from a new dimension into §6.3 hard gates; operability sub-checks folded from a D4 extension into the new D8); 2 partials scoped (workload envelope disclosed without weight bumps; canonical scoping added without dropping the doctrine label); 0 disagreements. Second-look over-concession audit performed pre-apply (88.9% → 77.8% AGREE ratio after refinements). v0.2 structural changes: **+1 option (F: standalone Python Kafka consumer)**, **+1 dimension (D8: evidence integrity + operability)**, **pinned architectures for D (Airflow + Postgres materialized view) and E (KServe)**, **absolute per-dimension score anchors §6.2.1**, **sensitivity analysis §6.2.2**, **corpus non-negotiable hard gates §6.3 (G1–G10)**, **workload envelope §2.4**, **AB-028 dependency gate §5.1 (Path A / Path B)**, **Decision Record scoped to v0 reference workload with mandatory reassessment triggers §7.1**, **§10 corrections (AB-030 label-vs-prediction disambiguation; PC §3.3/§4.3 freshness cross-ref; AB-032 prerequisite)**, **§8 R1 rewritten to acknowledge Option A pre-implementation asymmetry with scoring freeze until parity restored**. Base commit: current main tip (`7f9f14c`).

---

## 12. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval, this RFC becomes the contract for the spike execution; changes to §3 options, §4 dimensions, §6.2 weights, §6.2.1 anchors, or §6.3 gates require RFC amendments.
- On spike completion, the Decision Record at `docs/decisions/dynamic-reliability/RUNTIME_PLACEMENT.md` (v0) becomes the canonical placement doctrine **for the v0 reference workload** (per §7 scoping); this RFC may be archived under `research/spikes/AB-029-runtime-placement/` at that time. §7.1 reassessment triggers govern when the Decision Record itself must be re-run.
