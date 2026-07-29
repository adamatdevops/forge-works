# AB-029 Runtime Placement Architecture Spike RFC (v0.1 draft) — where do Dynamic Reliability predictors actually run?

> **Status:** Scoping draft (v0.1). Not yet approved for execution. Approval means: the 5 options are locked in, the benchmark dimensions are locked in, and the spike may begin instrumentation.
> **Owner:** Platform team (spike execution owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Runs in parallel with:** AB-028 feasibility spike. Shares AB-028's reference workload where useful. Independent of contract graduation.
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-029` (backlog is repo-ignored; canonical scope on this document).

---

## 1. Why this spike exists

Codex round-1 loop on the design corpus (retrospective at `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md`, F18) flagged that SC §2 + PC §5 selected streaming Flink + Kafka as the runtime placement BEFORE establishing the latency, throughput, state, model-size, or availability requirements that justify it. The design corpus is doctrine-neutral about placement; the assumption "we run in Flink because ForgeWorks runs in Flink" needs evidence.

This spike closes that gap. Its output — a documented comparison matrix across 5 placement options, benchmarked on the same reference workload against pre-declared dimensions — turns the placement choice from *default* into *justified*.

The spike is deliberately **architecture-only, no live traffic, uses AB-028's reference workload for representative benchmarking**. Its purpose is to answer one question: which placement option best fits ForgeWorks's Dynamic Reliability v0 constraints (advisory-only, shadow-mode, calibration-observable), while leaving room for v1+ upgrades?

---

## 2. Scope

### 2.1 In-scope

- **Five placement options** (§3) evaluated against seven dimensions (§4).
- **Reference workload:** the AB-028 spike's deploy-SLO-breach estimand on `(webhook-gateway, prod)`. Same input events, same feature construction. Enables apples-to-apples comparison.
- **Prototype-scale benchmarks:** each option gets a minimal prototype running the AB-028 model against 30 days of historical events; measurements collected per §4 dimensions.
- **Comparison matrix (§6):** each option × each dimension, with quantitative measurements where possible, qualitative scoring where not.
- **Recommendation:** primary + fallback option, with the specific evidence that supports the ranking.
- **Contract-level implications back-propagated:** if the winning option requires SC / PC / VOC / GT changes (e.g., a batch option needs `staleness` semantics that PC §5 doesn't have), file those as v0.2 amendments in the same PR.

### 2.2 Out-of-scope

- **Production-scale load testing.** v0 is shadow-mode / advisory-only; production throughput isn't the constraint. Prototype-scale (30-day replay) suffices for a placement decision.
- **Model performance re-evaluation.** AB-028 owns model quality; this spike takes the AB-028 model as-is and measures the RUNTIME properties around it.
- **T3/T4 actuation placement.** All 5 options are evaluated for T1/T2 (evidence + recommendation) only. T3/T4 placement is a separate doctrine change (see corpus README §v0 doctrine).
- **Multi-tenant / multi-region deployment.** v0 is single-tenant (`forge-works` per governance envelope). Cross-region placement is a v1+ concern.
- **Cost optimization beyond first-pass.** Cost per prediction is one dimension (§4), but full FinOps analysis (spot pricing, reserved instances, autoscaling profiles) is out of scope; representative on-demand pricing suffices.

### 2.3 Non-goals

- **Not a bake-off with a winner-take-all mandate.** The output is a comparison matrix + recommendation; the recommendation may be "primary X, fallback Y, revisit at v1" rather than "X is best forever."
- **Not a rewrite of the corpus.** Placement affects PC §5 (runtime metadata) and possibly SC §5 (source access patterns); it does not touch the contract SHAPES (§2.1 required fields, §3 estimand definitions, §4 confidence semantics).
- **Not blocking on AB-028 completion.** Uses AB-028's *reference workload construction* (deploy-SLO-breach on webhook-gateway prod), not AB-028's *results*. Can run in parallel.

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

- **What:** Airflow (or similar) scheduled batch job runs every N minutes; reads recent events from Kafka via consumer offset or from a warehouse; scores in Python; writes predictions to a materialized view (Postgres / BigQuery / etc.); publishes change notifications on a lightweight topic.
- **Why might win:** Simplest operational model. Python-native → any model class works (sklearn, XGBoost, PyTorch). No JVM. Model rollout = redeploy a Python service.
- **Why might lose:** Latency floor = batch interval + processing time. If DR predictions need to surface within ~60s of a deploy marker, batch is too slow. Freshness semantics require an explicit `staleness` field on predictions (contract implication for PC §5).

### 3.5 Option E — Dedicated inference service (Triton / KServe)

- **What:** Standalone inference service (NVIDIA Triton, Kubeflow KServe, or similar) with its own scaling story. Flink job (thin) consumes events, calls the inference service via gRPC, writes predictions back to Kafka.
- **Why might win:** Best model-flexibility story — GPU-backed inference, batching, model versioning, A/B testing all first-class. Model rollout = pushing a new model version to Triton.
- **Why might lose:** Highest operational complexity. New service to run, monitor, on-call. Cross-service latency (Flink ↔ Triton) is a new failure mode. Overkill for v0 model class (probably a small logistic regression or gradient-boosted tree).

---

## 4. Benchmark dimensions

Each option is measured against these seven dimensions. Measurements collected on the AB-028 reference workload (30 days of historical events, deploy-SLO-breach estimand, webhook-gateway prod slice).

| # | Dimension | Measurement | Units |
|---|-----------|-------------|-------|
| D1 | **Replay behavior** | Time to replay 30 days of events from Kafka offset zero to current tip | seconds |
| D2 | **Backpressure handling** | Behavior at 10× input rate — does it queue, drop, block upstream, or degrade gracefully? | qualitative + max sustainable QPS |
| D3 | **Model rollout mechanics** | Steps + time from "new model artifact in MLflow registry" to "predictions using new model" | ordered steps + wall-clock |
| D4 | **Failure isolation** | Impact of predictor crash on: (a) other Flink jobs, (b) Kafka backlog, (c) upstream data producers | qualitative severity |
| D5 | **Cost per prediction** | Fully-loaded infra cost for 1M predictions (compute + storage + network) at representative on-demand pricing | USD |
| D6 | **Latency envelope** | Wall-clock time from source event committed to Kafka to prediction available to consumer | p50 / p95 / p99 milliseconds |
| D7 | **Cognitive load on platform team** | New concepts, tools, or runbooks required. Baseline: existing Flink stack. | qualitative 1-5 + concrete new-concept list |

---

## 5. Benchmark methodology

- **Reference workload:** AB-028's deploy-SLO-breach on `(webhook-gateway, prod)`. Same 30-day window (see AB-028 §4.1). Same feature construction (AB-028 §4.3). Same model class (AB-028 §5.3 spike model pick — small tree ensemble or logistic regression).
- **Prototype scale:** each option runs a minimal viable prototype — just enough to measure, not production-ready. E.g., Option D uses a plain Airflow DAG + Postgres, not a full DataOps setup.
- **Shared instrumentation:** predictions emitted by every option go to the same audit sink (MLflow tracking log per PC §4.2 + AB-028's evaluation log per AB-028 §7 deliverables). This ensures the comparison is on runtime properties, not measurement drift.
- **Isolation:** each option runs on a separate namespace / cluster / project as appropriate to prevent resource contention biasing measurements.
- **Sample size:** each measurement repeated 3 times; report mean + range. Cost measurements are single-run + extrapolated (repeating full 30-day replay 3× is prohibitively expensive).

---

## 6. Predeclared decision framework

### 6.1 Comparison matrix

The spike output is a 5×7 matrix (5 options × 7 dimensions) with measurements per cell. Each cell also carries a qualitative note (e.g., "Option A D2 backpressure: 8000 QPS sustained; graceful degradation via checkpoint pause") so the comparison is auditable.

### 6.2 Scoring

Per-dimension score: 1 (worst) to 5 (best), relative to the other options. Ties allowed. Rationale MUST be one sentence per cell.

Weighting (predeclared, locked at scoping-approval):

| Dimension | Weight | Why |
|-----------|--------|-----|
| D1 Replay behavior | 3 | Critical for retraining + audit; missing this makes calibration impossible. |
| D2 Backpressure | 2 | v0 is low-volume; matters more at v1. |
| D3 Model rollout | 4 | We WILL iterate on models; friction here compounds. |
| D4 Failure isolation | 4 | Advisory-only means low blast radius, but engineer trust depends on isolation from deterministic paths. |
| D5 Cost per prediction | 2 | v0 volumes are small; cost is a v1 concern unless an option is >10× more expensive than the rest. |
| D6 Latency envelope | 3 | Deploy-SLO-breach estimand is ~60min horizon; latency <60s is more than sufficient. |
| D7 Cognitive load | 3 | Real cost paid every day; underweighting this leads to abandoned tech. |

Weighted score per option = Σ(dimension_score × dimension_weight). Recommendation = highest score, with fallback = second-highest if within 10% of top score.

### 6.3 Go / no-go per option

An option is disqualified BEFORE scoring if:
- Any dimension score = 1 with weight ≥ 3 (e.g., a placement that can't do replay is disqualified regardless of other strengths).
- Contract implication would require breaking changes to PC §3 estimand semantics or GT §2.1 required fields (structural incompatibility with the corpus).

Disqualification MUST be documented with the specific failing dimension + why the failure is disqualifying, not silently dropped.

---

## 7. Deliverables

- Comparison matrix published in the spike report at `research/spikes/AB-029-runtime-placement/<timestamp>/matrix.md` (or similar path; final location decided at execution).
- Prototype code for each option retained in `research/spikes/AB-029-runtime-placement/prototypes/<option>/` — deliberately marked as prototype-quality, not production candidates.
- Recommendation issued in a Decision Record at `docs/decisions/dynamic-reliability/RUNTIME_PLACEMENT.md` (v0) capturing: chosen primary, chosen fallback, evidence supporting the ranking, contract-level implications if any.
- Contract-level amendments (SC / PC / VOC / GT bumped to v0.2) filed as separate coordinated PRs where the recommendation requires them.
- Backlog entry AB-029 acceptance criteria checked off (comparison matrix + recommendation + Decision Record + contract implications).

---

## 8. Risks

- **R1 — Prototype quality bias.** A well-instrumented prototype for one option may look better than a rushed prototype for another. Mitigation: same author writes all 5 prototypes; time-box each to comparable effort (e.g., 2 days each); document time invested per option.
- **R2 — Measurement drift.** Different options may report metrics differently. Mitigation: shared MLflow tracking sink + explicit metric definitions in §4; single-source-of-truth for the AB-028 reference workload.
- **R3 — Scoring hindsight bias.** Weights (§6.2) locked at scoping-approval BEFORE measurements. If measurements reveal a dimension is more/less important than pre-declared, that's a note for the Decision Record but does NOT retroactively change the ranking.
- **R4 — 5 options is a lot.** If early measurements clearly disqualify 2+ options via §6.3 rules, spike may reduce to 3 finalists and re-scope. Document any option dropped and why.
- **R5 — Recommendation may be "none of the above."** If all 5 options score below a floor (e.g., top score < 40 / max 105), the recommendation is to spike a 6th option. Not a failure — a valid outcome for a scoping spike.

---

## 9. Timeline (indicative — not committed)

- **T + 0:** Scoping-approval on this RFC. §3 options and §4 dimensions and §6.2 weights locked; §5 methodology refinements permitted.
- **T + 1w:** Prototype scaffolding for all 5 options (skeleton + AB-028 workload wired in).
- **T + 2w:** Measurement runs 1 (all 5 options × all 7 dimensions).
- **T + 3w:** Measurement runs 2 + 3 (repeats for D1–D4, D6); §6.3 disqualification review.
- **T + 4w:** Comparison matrix compiled; Decision Record drafted with recommendation; contract-implications PRs (if any) drafted.

Timeline is indicative. Runs in parallel with AB-028 feasibility spike execution; can share the AB-028 workload harness once AB-028 begins execution.

---

## 10. Related documents

- [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) *(v0.2)* — reference workload source. AB-029 uses AB-028's deploy-SLO-breach worked estimand as the benchmark input; independent of AB-028's results.
- [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) *(v0.3)* — every option MUST wire the label_schema_validator library into its emission path (per AB-030 §2.1 in-scope).
- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) *(v0.1)* — §5 runtime metadata may need a `staleness` field if Option D (batch) wins; that's a contract-level implication filed as a v0.2 amendment.
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) *(v0.1)* — SC §2 source access patterns may need annotation per placement option (streaming consumer vs. batch reader).
- [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) *(v0.2)* — label emission path per option; every option consumes the same GT contract.
- [`README.md`](README.md) — corpus index. AB-029 to be added to the in-flight-spike-RFCs table on scoping-approval.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-029 entry tracks execution status.

---

## 11. Provenance

- **2026-07-29:** v0.1 draft. Codex round-1 loop on design corpus (2026-07-24, F18) flagged that placement was chosen without evidence; this RFC scopes the evidence spike. Runs in parallel with AB-028 (`3bc95ef` on main). Base commit: current main tip (`661aff5`).

---

## 12. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval, this RFC becomes the contract for the spike execution; changes to §3 options, §4 dimensions, or §6.2 weights require RFC amendments.
- On spike completion, the Decision Record at `docs/decisions/dynamic-reliability/RUNTIME_PLACEMENT.md` (v0) becomes the canonical placement doctrine; this RFC may be archived under `research/spikes/AB-029-runtime-placement/` at that time.
