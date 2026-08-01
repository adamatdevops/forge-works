# AB-032 MLflow Production-Readiness Assessment RFC (v0.1 draft) — is the existing tracking-only MLflow deployment safe to depend on for calibrated-confidence predictors?

> **Status:** Scoping draft (v0.1). Not yet approved for execution. Approval means: the 6 readiness dimensions are locked in, the assessment methodology is locked in, and the assessment may begin instrumentation.
> **Owner:** Platform / SRE (assessment owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Runs in parallel with:** AB-028 feasibility spike, AB-029 runtime placement spike. Does NOT block the spikes (they may use MLflow in "development mode"). DOES block any calibrated-confidence predictor going to production per PC §8.
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-032` (backlog is repo-ignored; canonical scope on this document).

---

## 1. Why this readiness assessment exists

Codex round-1 loop on the design corpus (retrospective at `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md`, F20) flagged that:

- `PREDICTION_CONTRACT.md` §4.2 anchors model provenance to MLflow (`model_ref: mlflow://models/...`);
- PC §8 requires weekly per-cohort calibration publication to MLflow;
- `DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` §11 assumes MLflow serves calibration curves + model registry as a runtime dependency of every predictor;

… but the existing MLflow deployment at `infra/mlflow/base/mlflow.yaml` was provisioned to serve **experiment tracking only**. Registry governance, artifact durability, calibration serving, model promotion RBAC, and availability characteristics have never been assessed. Depending on unassessed infrastructure for production-shipping calibrated confidence would be a governance violation of the corpus's own attestation posture.

This RFC scopes the assessment. Its output — a per-dimension readiness report with a bounded "OK / not OK / OK with mitigations" verdict per dimension and an overall production-dependency verdict — turns the corpus's MLflow assumption from *implicit* into *evidenced*.

The assessment is deliberately **audit-and-report, no infrastructure changes**. Its purpose is to answer one question: is the existing MLflow deployment production-safe to depend on for `deploy_slo_breach_60m_association_v0` (and by extension, all future v0 estimands), or does it need work first?

---

## 2. Scope

### 2.1 In-scope

- **Six readiness dimensions** (§4) evaluated against the existing `infra/mlflow/` deployment.
- **Reference workload:** the AB-028 spike's expected MLflow write pattern — experiment tracking (per training run), artifact storage (model binaries + calibration curves), model registry stages, weekly per-cohort calibration publication per PC §8.
- **Assessment methodology (§5):** each dimension gets a predeclared pass/fail definition + measurement method + evidence artifact.
- **Backup / restore drill** — one full backup + restore of the MLflow Postgres backend, executed against the actual `forge-postgres-postgresql` service. Documented as a runbook.
- **Auth / promotion RBAC verification** — actual invocation of promotion APIs with restricted and unrestricted credentials.
- **Gap filing:** any dimension that fails or fails-with-mitigations gets a follow-up AB-NNN entry filed with concrete scope, not a hand-wave.
- **Verdict:** overall "OK to depend on for calibration + model provenance" statement, with per-dimension breakdown and specific mitigations required (if any).

### 2.2 Out-of-scope

- **Infrastructure changes.** This RFC does not change `infra/mlflow/`. If dimensions fail, the assessment REPORTS the failure and files follow-up AB-NNN entries; those entries own the change.
- **Alternative model-registry platforms.** Weights & Biases, Neptune, SageMaker Model Registry — all deferred to a v1+ decision if MLflow proves unfit. This assessment is scoped to the existing deployment.
- **T3/T4 actuation-time model serving.** All 6 dimensions are evaluated for T1/T2 (prediction produced + published + audit-visible) only. T3/T4 model serving latency is a different problem addressed by AB-029.
- **Multi-region MLflow.** v0 is single-cluster (`dev` cluster only, per the current Kustomize base). Multi-region deployment is a v1+ concern.
- **Cost optimization.** Cost is one input to D5 capacity planning, but full FinOps analysis (spot pricing, S3 lifecycle policies, RDS reservation) is out of scope; representative on-demand pricing suffices.

### 2.3 Non-goals

- **Not a rewrite of PC §4.2 or PC §8.** Those sections assume "MLflow is the substrate"; if MLflow proves unfit, the substrate assumption changes and PC amendments follow — but that's a downstream consequence, not this RFC's deliverable.
- **Not blocking on AB-028 spike completion.** The spike uses MLflow in "development mode" per AB-028 §2.2 R4 — no production-readiness dependency. This assessment can run fully in parallel and its verdict is required before the AB-028 spike's OUTPUT model can be promoted for T1 production use.
- **Not a compliance audit.** SOC 2 / ISO 27001 / regulatory-specific reviews are out of scope. The assessment covers operational readiness for the ForgeWorks corpus's own attestation posture, not external certification.

---

## 3. Current state — what `infra/mlflow/` provides today

Verified from `infra/mlflow/base/mlflow.yaml` at commit `87d5072` (main tip at RFC-drafting time):

| Aspect | Current state | Observation |
| --- | --- | --- |
| MLflow version | `ghcr.io/mlflow/mlflow:v2.19.0` | Reasonable; server released 2024-11. No auth plugin loaded. |
| Deployment topology | Single-replica `Deployment`, namespace `forge-ml` | No `PodDisruptionBudget`, no `HorizontalPodAutoscaler`. Any node drain or eviction causes MLflow downtime. |
| Backend store | PostgreSQL at `forge-postgres-postgresql.forge-engine.svc:5432/mlflow` | Shares Postgres cluster with `forge-engine`. Backup posture inherited from that Postgres, not verified here. |
| Artifact root | `s3://fw-models-dev/mlflow/artifacts` | **DEV bucket.** Production-shipping calibration curves + model binaries CANNOT land in `-dev`; this is a hard blocker on any production dependency. |
| Auth | No `--app-name basic-auth` flag; no reverse-proxy auth annotation on Service | Server-side MLflow API is un-authenticated. Any pod in the cluster can write, promote, or delete anything. |
| Resources | Requests: 100m CPU / 512Mi. Limits: 500m CPU / 1Gi. | Sized for tracking-only workload. Capacity for weekly calibration publication × N cohorts × M models is untested. |
| Probes | Liveness / readiness / startup on `/health` | Standard. No SLI defined for external consumers. |
| Registry stages | Default MLflow stages available (`None`, `Staging`, `Production`, `Archived`) | No enforcement policy. Any writer can promote to `Production`. No aliases configured. |
| Secrets | Postgres password from Secret `mlflow-db-secret` | Standard. No S3 credential secret visible in this manifest — assumed IRSA or shared cluster IAM. |

**Provisional read:** the deployment is tracking-quality, not production-quality. At least D1 (auth), D5 (artifact bucket), and D6 (HA) look unlikely to pass without follow-up work. This is a hypothesis; the assessment (§5) is the evidence.

---

## 4. Readiness dimensions

Six dimensions, each with a predeclared **fitness definition** — what "OK to depend on" means for that dimension, in advance of measurement — so the assessment cannot rubber-stamp on the day.

### D1 — Authentication and authorization

**Fitness definition:** every write to the tracking server (log_run, log_metric, log_artifact, log_model) is authenticated. Every registry transition (`Staging` → `Production`) requires a distinct promotion identity that not all writers hold. Read-only clients (audit consumers, dashboards) can read metrics + calibration curves without holding promotion identity.

**Failure modes this dimension catches:** any-writer-can-promote, silent identity drift, unattributed model overwrites, unattributed calibration overwrites.

### D2 — Backend-store durability

**Fitness definition:** the Postgres backing store has a documented backup cadence, a documented retention window, and a **rehearsed** restore procedure (not just "we have backups" — an actual restore drill against a scratch database). RPO ≤ 24h, RTO ≤ 4h for the tracking-server workload.

**Failure modes this dimension catches:** untested backups, backups that don't restore, restore procedure not runbookable, silent Postgres growth to disk-full without alarm.

### D3 — Artifact-store durability

**Fitness definition:** artifacts (model binaries, calibration curves, training data manifests) land in a bucket with (a) versioning enabled, (b) lifecycle policy documented (specifically: no auto-delete of anything referenced by a registry `Production`-stage model), (c) cross-region replication configured or explicitly deferred with a documented risk statement. `-dev`-suffixed buckets DISQUALIFY the deployment from production dependency by definition.

**Failure modes this dimension catches:** artifact loss on bucket lifecycle sweep, silent overwrites of production-referenced artifacts, dev-bucket dependency for prod workload.

### D4 — Registry governance

**Fitness definition:** the model registry supports (a) named stages / aliases per PC §4.2's `model_ref` scheme; (b) an enforceable promotion policy — Production-stage transitions gated on a distinct identity from Staging-stage transitions; (c) immutable model versions (once logged, the artifact hash cannot change without a new version); (d) auditable transition history (who promoted what, when, via what workflow).

**Failure modes this dimension catches:** silent model swaps, unauditable promotions, PC §4.2's `model_ref` resolving to a mutable target.

### D5 — Capacity and scaling

**Fitness definition:** the current deployment can absorb the expected steady-state MLflow load — sized against a concrete workload envelope: N deploy-cohort × weekly calibration-refresh × M candidate models under evaluation. Steady-state P95 API latency (log_run, log_metric, log_model) ≤ 500ms; steady-state Postgres growth ≤ documented projection; steady-state S3 write throughput ≤ documented projection.

Requires a concrete workload envelope BEFORE assessment; drafted in §5.D5.

**Failure modes this dimension catches:** capacity exhaustion under production write patterns, silent tracking-server slowdowns that mask training-pipeline problems, Postgres growth to disk-full during hot week.

### D6 — Availability and reconvergence

**Fitness definition:** the MLflow tracking server has (a) a documented SLO — availability target + measurement window + consequence-of-breach; (b) a PodDisruptionBudget preventing simultaneous replica loss during voluntary evictions; (c) either multi-replica configuration OR a documented "single replica is acceptable because writes are idempotent and calibration schedule tolerates ≤ N minutes of downtime" statement with N quantified against the calibration cadence.

**Failure modes this dimension catches:** silent MLflow downtime during a calibration publication window causing calibration gap, node-drain-caused tracking loss, un-SLI'd runtime dependency.

---

## 5. Assessment methodology

For each dimension, the assessment produces: (a) evidence artifact (test output / config diff / runbook); (b) verdict (`PASS` / `PASS-WITH-MITIGATIONS` / `FAIL`); (c) if `PASS-WITH-MITIGATIONS` or `FAIL`, a filed AB-NNN follow-up with concrete scope.

### D1 methodology

1. `kubectl exec` into an in-cluster pod not-in-namespace-`forge-ml`, curl `mlflow:5000/api/2.0/mlflow/registered-models/create`, verify what identity (if any) is required.
2. `kubectl exec` into a namespace-`forge-ml` pod, curl the same, verify what identity (if any) is required.
3. From outside the cluster (kubectl proxy or Ingress), attempt the same.
4. Record: any of the three that succeeds without authentication is a D1 finding.

### D2 methodology

1. Query `forge-postgres-postgresql`'s Kustomize / Helm values for backup configuration.
2. Locate the most recent backup artifact; verify recency < 24h.
3. Provision a scratch Postgres instance (test namespace); restore the backup to it.
4. Connect MLflow (test replica) to the restored database; verify list_experiments, list_runs, and list_registered_models return the pre-backup state.
5. Time the full drill. Record wall-clock as RTO. Compute RPO from backup cadence.

### D3 methodology

1. Verify `s3://fw-models-dev/mlflow/artifacts` — bucket-name substring `-dev` disqualifies for production per D3 fitness definition. This is a foregone finding at RFC-drafting time; the assessment confirms and documents the required bucket-move scope.
2. Check versioning + lifecycle policy on the current bucket (evidence for the eventual production bucket's required config).
3. Document the migration path: create `fw-models-prod` per D3 fitness, cutover pattern, artifact backfill strategy for existing tracking-mode runs (or explicit "existing runs stay in dev; production starts fresh in prod" statement).

### D4 methodology

1. Enumerate registry stages available on the deployed MLflow version (v2.19.0 supports both stages and aliases; document which the corpus will adopt).
2. Attempt a `Staging` → `Production` transition using two identities: (a) a "training-pipeline" identity that should NOT be able to promote to production; (b) a "release-engineer" identity that SHOULD. If both succeed or both fail, promotion governance is un-enforced (D4 finding).
3. Verify model-version immutability: log a model, re-upload a different artifact under the same version — MLflow should reject. If accepted, D4 finding.
4. Query the audit log (`model-version-transition` events) for the promotion attempts in step 2. If not queryable, D4 finding.

### D5 methodology

**Workload envelope (predeclared):** the assessment sizes against:

- **Experiment tracking:** ≤ 500 training runs / month per active spike (AB-028 + AB-029 + future spikes ≤ 5 in flight), so ≤ 2,500 runs / month steady state.
- **Calibration publication:** per PC §8, weekly per-cohort. Assume 10 cohorts × 1 model / cohort × 1 curve / week = 40 calibration writes / month. Each ~100KB.
- **Model artifacts:** ≤ 20 model versions promoted / month; artifact size ≤ 100MB per version.
- **Concurrent writers:** ≤ 3 (training pipeline, calibration publisher, human-triggered runs).

Assessment: replay the workload envelope for 24h against the deployed MLflow; measure P50 / P95 / P99 API latencies on log_run, log_metric, log_model; measure Postgres row growth; measure S3 write throughput; extrapolate to 30-day projection. Compare against fitness thresholds.

Envelope numbers are placeholders; refined at scoping-approval by the AB-028 owner (who has the actual training-run frequency) and the PC §8 calibration-publication owner (currently unnamed — this is a `[NEEDS-OWNER]` marker for scoping-approval).

### D6 methodology

1. Query the Kubernetes API for the MLflow Deployment's PodDisruptionBudget (`kubectl get pdb -n forge-ml`). If none present, D6 finding.
2. Drain the node hosting the MLflow pod (`kubectl drain <node> --dry-run=server` to preview; only actually drain on a test cluster). Measure how long the tracking API is unavailable.
3. Retrieve or, if absent, propose an SLO for the tracking server: availability target (e.g., 99.5% monthly), measurement window (30d rolling), consequence (calibration publication skips one cycle → alert to SRE; two cycles → automatic advisory-to-fallback per PC §8).
4. If single-replica remains: verify the "idempotent writes + N-minute-tolerable-downtime" statement is documented AND N is smaller than the calibration cadence gap tolerance.

---

## 6. Predeclared decision framework

### 6.1 Per-dimension verdicts

For each of D1-D6, one of:

- **PASS** — fitness definition met without qualification. No follow-up filed.
- **PASS-WITH-MITIGATIONS** — fitness definition met given specific mitigations (e.g., "OK for calibration publication only, NOT for model promotion until D4 gap closed"). Follow-up AB-NNN filed with scope + owner.
- **FAIL** — fitness definition not met, and the gap blocks the specific corpus dependency in that dimension. Follow-up AB-NNN filed with scope + owner + rough effort estimate.

### 6.2 Overall verdict

The overall "OK to depend on MLflow for `deploy_slo_breach_60m_association_v0` in production" verdict is derived, not voted:

- **All 6 PASS** → OK to depend on. Production T1 predictor may ship.
- **All non-FAIL, ≥ 1 PASS-WITH-MITIGATIONS** → OK to depend on FOR THE SCOPE covered by the mitigations. Explicit boundary statement required (e.g., "OK for tracking + calibration publication, NOT OK for promotion RBAC until AB-XXX closes D4 gap").
- **≥ 1 FAIL** → NOT OK to depend on until the FAIL dimensions close. Follow-up work must complete before production T1 predictor ships. Assessment closes with a specific list of prerequisite work.

### 6.3 Disqualification rules

Regardless of the aggregate verdict, any of these is an automatic **NOT OK**:

- **D3 FAIL** — artifact store on `-dev` bucket (or any bucket named to suggest non-production) disqualifies for production dependency until a `-prod` bucket cutover completes.
- **D1 FAIL** — un-authenticated tracking server disqualifies for anything beyond the assessment itself (writing an assessment finding to an un-auth'd server is only acceptable because the assessment WRITES the finding).
- **D4 FAIL** on immutability — mutable model versions break PC §4.2's `model_ref` audit-integrity promise. No aggregate score compensates.

### 6.4 What "OK to depend on" DOES NOT mean

- It does NOT mean MLflow is the best long-term choice; it means it clears the bar for v0 dependency.
- It does NOT extend to v1+ estimands automatically; each new estimand's demands are compared against the assessed capacity envelope (D5) at the time of shipping.
- It does NOT include multi-region, HA-across-zone, or DR-across-region posture; those are v1+ concerns filed as their own AB-NNNs if the corpus needs them.

---

## 7. Deliverables

- **AB-032 Readiness Report** at `docs/decisions/dynamic-reliability/MLFLOW_READINESS_ASSESSMENT.md` (v0.1) — per-dimension verdicts, evidence artifacts referenced, overall verdict, filed follow-up AB-NNN list, dated.
- **Postgres backup / restore runbook** at `docs/runbooks/mlflow-postgres-restore.md` — the D2 drill turned into an executable runbook.
- **Filed follow-up AB-NNN entries** in `roadmap/AUTOMATIONS_BACKLOG.md` for every dimension that lands `PASS-WITH-MITIGATIONS` or `FAIL`. Each entry: concrete scope, owner (or `[NEEDS-OWNER]`), rough effort estimate, dependency on AB-032 report.
- **CHANGELOG entry** under `### Added` referencing the report + linked follow-ups.
- **README follow-up-table row-set closure** — AB-032 row updated with resolution date + link to report.

---

## 8. Risks

- **R1: Assessment produces "PASS" on paper but real production load breaks the deployment.** Mitigation: D5 envelope MUST be conservative; if the actual production load exceeds envelope by > 2× on any dimension, the report's PASS is invalidated and a re-assessment is required before further production dependency. This is documented in the report's own "re-assessment triggers" section.
- **R2: Follow-up AB-NNN entries file and then rot.** Mitigation: each filed entry gets a `blocks:` annotation naming the specific corpus dependency it blocks (e.g., "blocks: PC §4.2 model promotion, PC §8 weekly calibration"). Rot-check is a `grep AB-032 roadmap/` at any future spike scoping approval.
- **R3: The assessment surfaces a broken assumption in the corpus itself** — e.g., PC §8's "weekly per-cohort calibration" turns out to be a load the current deployment cannot support at any reasonable sizing. Mitigation: this is a valid outcome; the report's overall verdict may be "corpus assumption needs revision, filed as AB-NNN, cannot bless dependency until revised." Assessment is not obligated to preserve corpus assumptions that don't survive contact with the substrate.
- **R4: Backup / restore drill against `forge-postgres-postgresql` risks the shared Postgres cluster.** Mitigation: drill runs against a scratch database + scratch namespace only; no touching of the production `mlflow` database. Documented in the D2 methodology (§5.D2 step 3: "Provision a scratch Postgres instance (test namespace)").
- **R5: D1 auth verification requires attempting unauthorized promotion — could be misread as an actual attack.** Mitigation: assessment MUST be pre-announced to SRE + security (asynchronous FYI is sufficient); assessment output includes an "attempted operations" appendix so any security monitoring is not left guessing.
- **R6: Cross-namespace assessment (D1) requires cluster-admin identity for the assessor.** Mitigation: this is a governance property of the assessment itself; assessor identity is named in the report's provenance section.

---

## 9. Timeline (indicative — not committed)

- **T + 0:** Scoping approval. Owner named; workload envelope numbers (D5) refined by AB-028 owner + PC §8 calibration owner.
- **T + 1w:** D1, D3, D4 verifications complete (they are largely config / API inspections; no drills required).
- **T + 2w:** D2 backup/restore drill executed; runbook drafted. D6 SLO drafted (may require SRE consultation).
- **T + 3w:** D5 workload envelope replay against deployment; measurements captured; report drafted.
- **T + 4w:** Report reviewed; follow-up AB-NNNs filed; overall verdict published.

Timeline is indicative. Runs fully in parallel with AB-028 + AB-029 spike execution. Can run before either spike completes (the assessment does not depend on spike outputs — spike outputs depend on the assessment for production graduation).

---

## 10. Related documents

- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) *(v0.1)* — §4.2 anchors `model_ref` to MLflow; §8 requires weekly per-cohort calibration to MLflow. Both are the source of MLflow-as-runtime-dependency; both are consumers of this assessment's verdict.
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) *(v0.1)* — §11 documents MLflow-readiness as a v1-prerequisite open question; this RFC is that question's execution vehicle.
- [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) *(v0.2)* — §7 discusses model provenance; MLflow registry is the substrate.
- [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) *(v0.2)* — §2.2 R4 explicitly runs in MLflow "development mode" during spike execution; this RFC's verdict gates AB-028's spike output moving to production.
- [`AB-029_RUNTIME_PLACEMENT_SPIKE.md`](AB-029_RUNTIME_PLACEMENT_SPIKE.md) *(v0.1)* — independent; all placement options assume MLflow as tracking + registry substrate.
- [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) *(v0.3)* — independent; validator library has no MLflow dependency.
- [`README.md`](README.md) — corpus index. AB-032 to be added to the in-flight-spike-RFCs table on scoping-approval.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-032 entry tracks execution status. Filed 2026-07-24 alongside AB-028 through AB-031.
- `infra/mlflow/base/mlflow.yaml` — the deployment under assessment.

---

## 11. Provenance

- **2026-08-01:** v0.1 draft. Codex round-1 loop on design corpus (2026-07-24, F20) flagged that PC §4.2 + PC §8 assume MLflow production-readiness that was never assessed; this RFC scopes the assessment. Runs in parallel with AB-028 spike execution (`e69e3f5` on main) and AB-029 benchmark framework (`6cc9032` on main). Base commit: current main tip (`87d5072`).

---

## 12. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval, this RFC becomes the contract for the assessment; changes to §4 dimensions, §5 methodology, or §6 verdict framework require RFC amendments.
- On assessment completion, the report at `docs/decisions/dynamic-reliability/MLFLOW_READINESS_ASSESSMENT.md` becomes the canonical production-dependency verdict for the current infra state; this RFC may be archived under `research/spikes/AB-032-mlflow-readiness/` at that time.
- Verdict is bound to an infra-state snapshot (base commit SHA of `infra/mlflow/`). Any subsequent change to `infra/mlflow/` invalidates the verdict and triggers a re-assessment (which may be a delta-only re-run of the affected dimensions).
