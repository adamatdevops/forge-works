# AB-032 MLflow Production-Readiness Assessment RFC (v0.2 draft) — is the existing tracking-only MLflow deployment safe to depend on for calibrated-confidence predictors?

> **Status:** Scoping draft (v0.2, refined 2026-08-02 after Codex round-1 loop critique). Not yet approved for execution. Approval means: the 8 readiness dimensions are locked in, the assessment methodology is locked in, the workload envelope + owner names for D5 are produced live in-meeting, and the assessment may begin instrumentation.
> **Owner:** Platform / SRE (assessment owner TBD at scoping-approval).
> **Corpus:** [`docs/decisions/dynamic-reliability/README.md`](README.md).
> **Runs in parallel with:** AB-028 feasibility spike, AB-029 runtime placement spike. Does NOT block the spikes (they may use MLflow in "development mode"). DOES block any calibrated-confidence predictor going to production per PC §8.
> **Related backlog entry:** `roadmap/AUTOMATIONS_BACKLOG.md#AB-032` (backlog is repo-ignored; canonical scope on this document).

---

## 1. Why this readiness assessment exists

Codex round-1 loop on the design corpus (retrospective at `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/reconciled.md`, F20) flagged that:

- `PREDICTION_CONTRACT.md` §4.2 anchors model provenance to MLflow via required `model_id` (MLflow-anchored) + `model_version` (semver) fields;
- PC §8 requires **continuous** per-cohort calibration publication to MLflow ("sliding-window calibration measurements published continuously to MLflow"); weekly is the audit cadence, not the safety cadence;
- `DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` §5 (Open questions) records MLflow readiness as a v1-prerequisite question — the design *assumes* MLflow serves calibration curves + model registry, and that assumption is under evaluation by this RFC;

… but the existing MLflow deployment at `infra/mlflow/base/mlflow.yaml` was provisioned to serve **experiment tracking only**. Registry governance, artifact durability, calibration serving, model promotion RBAC, and availability characteristics have never been assessed. Depending on unassessed infrastructure for production-shipping calibrated confidence would be a governance violation of the corpus's own attestation posture.

This RFC scopes the assessment. Its output — a per-dimension readiness report with a bounded "OK / not OK / OK with mitigations" verdict per dimension and an overall production-dependency verdict — turns the corpus's MLflow assumption from *implicit design assumption* into *evidenced runtime substrate*.

The assessment is deliberately **audit-and-report, no infrastructure changes**. Its purpose is to answer one question: is the existing MLflow deployment production-safe to depend on for the specific reference workload declared in §2.1 + §5.D5 (namely: `deploy_slo_breach_60m_association_v0`, continuous per-cohort calibration per PC §8, and the workload envelope locked at scoping-approval)? The verdict is scoped to that reference workload only — additional estimands, additional model classes, or workload growth beyond the envelope require explicit delta assessment per §12 reassessment triggers, not automatic verdict extension.

---

## 2. Scope

### 2.1 In-scope

- **Eight readiness dimensions** (§4) evaluated against the existing `infra/mlflow/` deployment.
- **Reference workload:** the AB-028 spike's expected MLflow write pattern — experiment tracking (per training run), artifact storage (model binaries + calibration curves), model registry stages, **continuous per-cohort calibration publication per PC §8** (sliding-window recomputation as ground-truth events arrive on the label stream; event-driven drift alarms; circuit-breaker fallback on error-budget exhaustion). Weekly baseline calibration remains as the audit cadence per PC §8, but the safety cadence is continuous — the workload envelope in §5.D5 sizes for both.
- **Assessment methodology (§5):** each dimension gets a predeclared pass/fail definition + measurement method + evidence artifact.
- **Backup / restore drill** — one full backup + restore of the MLflow Postgres backend, executed against the actual `forge-postgres-postgresql` service. Documented as a runbook.
- **Auth / promotion RBAC verification** — actual invocation of promotion APIs with restricted and unrestricted credentials.
- **Gap filing:** any dimension that fails or fails-with-mitigations gets a follow-up AB-NNN entry filed with concrete scope, not a hand-wave.
- **Verdict:** overall "OK to depend on for calibration + model provenance" statement, with per-dimension breakdown and specific mitigations required (if any).

### 2.2 Out-of-scope

- **Infrastructure changes.** This RFC does not change `infra/mlflow/`. If dimensions fail, the assessment REPORTS the failure and files follow-up AB-NNN entries; those entries own the change.
- **Alternative model-registry platforms.** Weights & Biases, Neptune, SageMaker Model Registry — all deferred to a v1+ decision if MLflow proves unfit. This assessment is scoped to the existing deployment.
- **T3/T4 actuation-time model serving.** All 8 dimensions (D1-D8, per v0.2 §4) are evaluated for T1/T2 (prediction produced + published + audit-visible) only. T3/T4 model serving latency is a different problem addressed by AB-029.
- **Multi-region MLflow.** v0 is single-cluster (`dev` cluster only, per the current Kustomize base). Multi-region deployment is a v1+ concern.
- **Cost optimization.** Cost is one input to D5 capacity planning, but full FinOps analysis (spot pricing, S3 lifecycle policies, RDS reservation) is out of scope; representative on-demand pricing suffices.

### 2.3 Non-goals

- **Not a rewrite of PC §4.2 or PC §8.** Those sections state MLflow-as-substrate; if MLflow proves unfit, the substrate assumption changes and PC amendments follow — but that's a downstream consequence, not this RFC's deliverable.
- **Not blocking on AB-028 spike completion.** The spike uses MLflow in "development mode" per AB-028 §2.2 R4 — no production-readiness dependency. This assessment can run fully in parallel and its verdict is required before the AB-028 spike's OUTPUT model can be promoted for T1 production use.
- **Not a compliance audit.** SOC 2 / ISO 27001 / regulatory-specific reviews are out of scope. The assessment covers operational readiness for the ForgeWorks corpus's own attestation posture, not external certification.

### 2.4 Target deployment and trust boundary

The verdict this assessment produces applies to a specific target — not a general MLflow-readiness declaration. The assessment MUST identify the following before it begins:

- **Target cluster:** the specific Kubernetes cluster the assessed MLflow is deployed in (currently `dev` cluster per `infra/mlflow/base/mlflow.yaml` Kustomize base). **If the eventual production cluster differs (e.g., a `prod` cluster is provisioned before this assessment executes), the verdict is scoped to whichever cluster the assessment actually runs against — no cross-cluster inference.**
- **Namespaces:** MLflow's own namespace (`forge-ml`), Postgres backing-store namespace (`forge-engine`), and any consumer namespaces that hold identities used in §5.D1 auth matrix.
- **Service accounts + IAM roles:** the exact workload identity MLflow uses for S3 access (IRSA role or shared cluster IAM), the identity used by `training-pipeline` writers, the identity used by `release-engineer` promoters (if any exist — currently NONE per §3 line 65).
- **Data classes handled:** what SC §3.6 governance classifications flow through the MLflow instance (production model artifacts, calibration curves, training data manifests, run metrics). Determines what governance envelope §4 D3 must verify propagation of.
- **Production consumers:** which predictor deployments (Options A/D/E/F from AB-029) will consume this MLflow instance's model_id/model_version resolution and calibration curves. Currently: none in production; the AB-028 spike output is the first candidate consumer.
- **Trust boundary:** in-cluster (pod-to-pod TLS + NetworkPolicy) vs cross-cluster (mTLS via ingress) vs external-consumer (IAM-scoped read-only). The assessment tests whatever boundary the target consumers actually cross.

**Verdict scope statement (mandatory in the report):** every dimension's PASS/FAIL is qualified by the target-deployment tuple above. Changing any element — different cluster, different consumer, new data class, expanded trust boundary — invalidates the verdict per §12 reassessment triggers.

**Explicit exclusion:** if the `dev` cluster is used as a test surrogate for a not-yet-provisioned `prod` cluster, a production PASS verdict CANNOT be issued from `dev`-cluster evidence. Test-surrogate assessment produces a "would-pass-in-prod-conditional-on" verdict only.

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
| Resources | Requests: 100m CPU / 512Mi. Limits: 500m CPU / 1Gi. | Sized for tracking-only workload. Capacity for continuous calibration publication per PC §8 (primary safety cadence — full envelope quantified in §5.D5, with weekly baseline as an additive audit layer) × N cohorts × M models is untested. |
| Probes | Liveness / readiness / startup on `/health` | Standard. No SLI defined for external consumers. |
| Registry stages | Default MLflow stages available (`None`, `Staging`, `Production`, `Archived`) | No enforcement policy. Any writer can promote to `Production`. No aliases configured. |
| Secrets | Postgres password from Secret `mlflow-db-secret` | Standard. No S3 credential secret visible in this manifest — assumed IRSA or shared cluster IAM. |

**Provisional read (hypothesis, not conclusion):** the manifest-visible state suggests D1 (auth), D3 (artifact bucket, formerly numbered D5 in v0.1 draft — see the v0.2 dimension re-lettering below), and D6 (HA) may not pass without follow-up work. **This is a hypothesis to test, NOT a foregone conclusion to document.** §5 (Assessment methodology) MUST run in full even if early findings appear to confirm the provisional read — see §5.0 "Execution rules" (v0.2). Provisional reads have been wrong before; the value of the assessment is that it collects raw evidence, not that it ratifies the drafter's expectation.

---

## 4. Readiness dimensions

Eight dimensions (v0.2: expanded from 6 after Codex round-1 loop surfaced gaps in client-runtime + software-lifecycle coverage; folded observability into D6, platform-security into D1, governance envelope into D3), each with a predeclared **fitness definition** — what "OK to depend on" means for that dimension, in advance of measurement — so the assessment cannot rubber-stamp on the day.

### D1 — Authentication, authorization, and platform security *(v0.2 renamed from "Authentication and authorization"; folds H13 platform-security)*

**Fitness definition:** every write to the tracking server (log_run, log_metric, log_artifact, log_model) is authenticated with a workload identity, not a shared/anonymous credential. Every registry transition (`Staging` → `Production`) requires a distinct promotion identity that not all writers hold. Read-only clients (audit consumers, dashboards) can read metrics + calibration curves without holding promotion identity. Additionally (platform-security prerequisites for meaningful auth): TLS in transit end-to-end (client → server → Postgres, and client → S3); NetworkPolicy restricts pod-to-MLflow access to explicit allowlist; least-privilege IAM (S3 bucket policy scoped to specific paths; Postgres grants scoped to specific schemas); Kubernetes Secrets contain no long-lived credentials without a rotation runbook; documented outbound egress destinations (no unexpected calls to Databricks telemetry, etc.).

**Failure modes this dimension catches:** any-writer-can-promote, silent identity drift, unattributed model overwrites, unattributed calibration overwrites, plaintext credentials in transit, over-scoped IAM permitting cross-bucket writes, never-rotated Postgres passwords, unexpected outbound telemetry.

### D2 — Backend-store durability

**Fitness definition:** the Postgres backing store has a documented backup cadence, a documented retention window, and a **rehearsed** restore procedure (not just "we have backups" — an actual restore drill against a scratch database). RPO ≤ 24h, RTO ≤ 4h for the tracking-server workload. Additionally: **storage-headroom monitoring** with alarm delivery verified — Postgres disk-usage alerts fire before disk-full, alerts route to on-call.

**Failure modes this dimension catches:** untested backups, backups that don't restore, restore procedure not runbookable, silent Postgres growth to disk-full without alarm, restored database that can't resolve to backed-up artifacts.

### D3 — Artifact-store durability + governance envelope *(v0.2 renamed from "Artifact-store durability"; folds H2 governance-storage)*

**Fitness definition:** artifacts (model binaries, calibration curves, training data manifests) land in a bucket with (a) versioning enabled, (b) lifecycle policy documented (specifically: no auto-delete of anything referenced by a registry `Production`-stage model), (c) cross-region replication configured or explicitly deferred with a documented risk statement. Additionally (governance envelope per SC §3.6): (d) retention enforcement matches source-contract governance metadata (e.g., a training-data-manifest referencing PII must respect the source's retention window); (e) residency enforcement (bucket region matches the strictest-input residency classification); (f) tenant isolation (per-tenant path prefixes with IAM policies preventing cross-tenant read where SC §3.6 requires); (g) purpose-limitation enforcement (calibration-only reads cannot download training data).

**§6.3 disqualification rule:** `-dev`-suffixed buckets (or any bucket named to suggest non-production under adopted ForgeWorks convention) trip a **policy disqualification** — technical properties (a)-(g) MUST also independently pass; naming is a policy backstop, not the sole gate.

**Failure modes this dimension catches:** artifact loss on bucket lifecycle sweep, silent overwrites of production-referenced artifacts, dev-bucket dependency for prod workload, PII-classified artifact retained past source's retention window, cross-tenant metadata leak.

### D4 — Registry governance

**Fitness definition:** the model registry supports (a) named stages / aliases resolvable to PC §4.2's required `model_id` (MLflow-anchored) + `model_version` (semver) fields; (b) an enforceable promotion policy — Production-stage transitions gated on a distinct identity from Staging-stage transitions; (c) immutable model versions (once logged, the artifact content-hash cannot change without a new version — verified via canonical digest recorded at registration + re-resolution check after mutation attempts through both MLflow API and direct S3); (d) auditable transition history (who promoted what, when, via what workflow — queryable via `model-version-transition` audit-log API).

**Failure modes this dimension catches:** silent model swaps (mutability), unauditable promotions, PC §4.2's `model_id` resolving to a mutable target, unauthorized promotion attributed to no identity or the wrong identity.

### D5 — Capacity and scaling

**Fitness definition:** the current deployment can absorb the expected MLflow load — sized against a concrete workload envelope covering BOTH continuous safety-cadence writes (per PC §8: sliding-window calibration recomputation as label events arrive, drift-alarm evaluations, circuit-breaker firings) AND weekly audit-cadence baseline. Steady-state P95 API latency (log_run, log_metric, log_model) ≤ 500ms; steady-state Postgres growth ≤ documented projection; steady-state S3 write throughput ≤ documented projection; burst behavior at 10× steady-state does not exhaust database connections or trigger S3 throttling that causes silent write loss.

Workload envelope + owner names are a **scoping-approval outcome requirement** (see §5.D5 — the scoping-approval meeting must produce named owners for AB-028 model-training + PC §8 calibration publication before the meeting adjourns with APPROVED, OR the D5 item is deferred per agenda-style APPROVED WITH DEFERRALS envelope).

**Failure modes this dimension catches:** capacity exhaustion under production write patterns, silent tracking-server slowdowns that mask training-pipeline problems, Postgres growth to disk-full during hot week, S3 throttling under burst load causing silent calibration-write loss, database connection exhaustion under 100+ parallel training runs, retry amplification storming the deployment.

### D6 — Availability, observability, and operator alerting *(v0.2 renamed from "Availability and reconvergence"; folds H12 observability)*

**Fitness definition:** the MLflow tracking server has (a) a **predeclared** SLO — availability target + measurement window + max contiguous outage + publication deadline + retry budget + recovery threshold, ALL locked BEFORE assessment (no proposing the SLO during assessment); (b) a PodDisruptionBudget preventing simultaneous replica loss during voluntary evictions; (c) either multi-replica configuration OR a documented "single replica is acceptable because writes are idempotent and calibration schedule tolerates ≤ N minutes of downtime" statement with **N explicitly quantified in minutes against the continuous safety cadence** (per PC §8); (d) continuous SLI export (Prometheus metrics for API latency P50/P95/P99, Postgres connection pool utilization, S3 write success rate, calibration-publication success rate); (e) alert routing verified (SLI breach → PagerDuty or equivalent on-call); (f) dashboard evidence (SRE-facing dashboard covering (d) SLIs + calibration-gap detection); (g) synthetic probe from a canary consumer measuring end-to-end path; (h) controlled alert-drill executed (deliberately breach the SLI in a test namespace; verify alert fires + resolves).

**Failure modes this dimension catches:** silent MLflow downtime during a calibration publication window causing calibration gap, node-drain-caused tracking loss, un-SLI'd runtime dependency, alerts configured but never routed, dashboards labeled "SRE" that no SRE actually watches, circuit-breaker fires without operator visibility.

### D7 — Client SDK integration and runtime resilience *(v0.2 NEW; adopts H10)*

**Fitness definition:** the MLflow Python SDK version used by predictor code is pinned to a specific version compatible with the server v2.19.0 (verified against MLflow's compatibility matrix). SDK behavior under partial failure is verified: (a) timeout defaults are explicit (not "wait forever"); (b) retry semantics documented (which errors retry, which do not, retry budget cap); (c) credential refresh works transparently (IRSA token expiry handled without predictor restart); (d) duplicate-write idempotency verified (retrying `log_metric` at same step does not double-count); (e) partial-failure fallback documented (if MLflow is unreachable, predictor abstains via PC §3 `type=abstain` rather than blocking or emitting a low-confidence guess); (f) predictor-side abstention path exercised in a controlled test where MLflow is deliberately made unreachable.

**Failure modes this dimension catches:** SDK version drift breaking log_metric calls silently; predictor hangs indefinitely on MLflow timeout; retry storms amplifying a brief MLflow blip into an outage; expired IRSA tokens causing predictor restart cascades; duplicate writes corrupting calibration; predictors emitting misleading confidence when the calibration substrate is unreachable.

### D8 — Software lifecycle and upgrade compatibility *(v0.2 NEW; adopts M21)*

**Fitness definition:** the deployed MLflow server pins to an **immutable image digest** (not a mutable tag like `v2.19.0`); all Python dependencies installed in the pod (currently `psycopg2-binary`, `boto3` per the manifest) are pinned to specific versions with hashes; a documented upgrade path exists for MLflow minor versions (v2.19 → v2.20+) including schema-migration rehearsal + rollback plan; vulnerability-scan posture for the pinned image documented + monitored; client/server compatibility matrix documented for supported SDK versions; server restart reproducibility verified (deleting the pod and letting Kubernetes recreate produces the same behavior).

**Failure modes this dimension catches:** silent MLflow behavior change when the `v2.19.0` tag is repointed upstream; dependency drift breaking Postgres or S3 connectivity across restarts; MLflow schema migration silently corrupting registry state; CVE published against `mlflow:v2.19.0` with no owner; SDK-server incompatibility surfacing only after client-side upgrade.

---

## 5. Assessment methodology

For each dimension, the assessment produces: (a) evidence artifact (test output / config diff / runbook); (b) verdict (`PASS` / `PASS-WITH-MITIGATIONS` / `FAIL`); (c) if `PASS-WITH-MITIGATIONS` or `FAIL`, a filed AB-NNN follow-up with concrete scope.

### 5.0 Execution rules *(v0.2 NEW — addresses M22 foregone-conclusion risk)*

- **Full D1-D8 execution is mandatory** even if an early automatic NOT-OK verdict is reached under §6.3. Skipping remaining dimensions after an early veto turns the assessment into ceremonial gap-documentation.
- **Raw commands + outputs published** as evidence artifacts (not just prose summaries). The reader must be able to reproduce the finding.
- **Assessor identity independent of the deployment owner.** The person who owns `infra/mlflow/base/mlflow.yaml` MUST NOT be the assessor; assessor name recorded in the report's provenance.
- **Baseline findings separated from post-remediation verification.** If the assessment finds a FAIL and the deployment is subsequently fixed, the fixed state is a NEW assessment round (v0.2 report or later), not a retrospective flip of the v0.1 finding.

### D1 methodology *(v0.2 — actor-by-operation matrix per H5)*

Test all combinations of {identity} × {operation} to build the auth matrix. Any un-authenticated success where authenticated required is a D1 finding; any authenticated success where authorization should have denied is a D1 finding.

**Identities to test:**
- (I0) no-identity / anonymous
- (I1) in-cluster pod, namespace ≠ `forge-ml`, no service-account credentials attached
- (I2) in-cluster pod, namespace = `forge-ml`, default service account
- (I3) in-cluster pod, namespace = `forge-ml`, "training-pipeline" service account (once D1 remediation provisions one — see §D4 prerequisite)
- (I4) in-cluster pod, namespace = `forge-ml`, "release-engineer" service account (once provisioned)
- (I5) external client via kubectl proxy or Ingress, no credential
- (I6) external client with cluster-admin kubeconfig

**Operations to test:**
- Tracking mutations: `log_run`, `log_metric`, `log_param`, `log_artifact`, `log_model`, `delete_run`
- Registry mutations: `create_registered_model`, `transition_model_version_stage` (`None → Staging`, `Staging → Production`, `Production → Archived`), `delete_model_version`
- Reads: `list_experiments`, `search_runs`, `get_metric_history`, `get_registered_model`, `download_artifacts`
- Direct artifact-store operations: S3 `PutObject` on `s3://<bucket>/mlflow/artifacts/...`, S3 `GetObject`, S3 overwrite of an existing artifact path

**Platform-security checks** (§4 D1 additions):
- Verify TLS termination between client + server (inspect Service annotations / Ingress config); verify MLflow → Postgres uses TLS (check `sslmode` in connection string); verify MLflow → S3 uses HTTPS.
- Verify NetworkPolicy on the `forge-ml` namespace scoping pod-to-MLflow ingress.
- Verify Secret `mlflow-db-secret` has documented rotation cadence.
- Query pod egress destinations (via NetworkPolicy or observed logs); confirm no unexpected outbound calls.

### D2 methodology *(v0.2 — extended per M15 disk-full + M16 artifact linkage)*

1. Query `forge-postgres-postgresql`'s Kustomize / Helm values for backup configuration.
2. Locate the most recent backup artifact; verify recency < 24h.
3. Provision a scratch Postgres instance (test namespace); restore the backup to it.
4. Connect MLflow (test replica) to the restored database; verify list_experiments, list_runs, and list_registered_models return the pre-backup state.
5. **Artifact-linkage verification (v0.2):** for a representative sample of restored runs (≥5) and registry versions (≥3), fetch the referenced model artifact / calibration curve / manifest from S3 using the restored metadata; verify content-hash matches pre-backup values. Document any inconsistency between Postgres backup state and S3 state as a D2 finding (Postgres+S3 consistent-backup strategy required or reconciliation approach documented).
6. **Storage-headroom + alarm test (v0.2):** query Postgres disk-usage metrics + configured alarm thresholds; verify at least one storage-headroom alarm is configured with growth-forecast projection; deliberately breach the threshold in a test namespace and verify alert delivery.
7. Time the full drill. Record wall-clock as RTO. Compute RPO from backup cadence.

### D3 methodology *(v0.2 — governance envelope sub-checks per H2 fold)*

1. Verify `s3://fw-models-dev/mlflow/artifacts` — bucket-name substring `-dev` trips the §6.3 policy-backstop rule (per adopted ForgeWorks convention). Document as a policy finding; independently continue to steps 2-5.
2. **Technical durability:** check versioning enabled + lifecycle policy documented + cross-region replication configured OR explicit deferral with risk statement.
3. **Governance envelope sub-checks (per SC §3.6):**
   - Retention: verify bucket lifecycle policies match the strictest source-contract retention requirements for classified data flowing through MLflow.
   - Residency: verify bucket region matches strictest-input residency classification.
   - Tenant isolation: verify per-tenant path prefixes exist with IAM policies preventing cross-tenant reads where required.
   - Purpose limitation: verify calibration-only reader identities cannot download training-data manifests.
   - Classification propagation: verify SC governance metadata propagates from source events → MLflow tags → artifact-store object tags where the compliance model requires it.
4. Document the migration path: create `fw-models-prod` per D3 fitness (including all governance sub-checks); cutover pattern; artifact backfill strategy (or explicit "existing runs stay in dev; production starts fresh in prod" statement).
5. If any of §3 governance sub-checks fails, file follow-up AB-NNN naming the specific SC §3.6 requirement violated.

### D4 methodology *(v0.2 — D1 prerequisite declared per H6; digest recording per M14)*

**Prerequisite:** D4 execution requires D1 remediation to have provisioned distinct identities (`training-pipeline` + `release-engineer` service accounts with role bindings). If D1 finds any-writer-can-promote (per §3 line 65: "any pod in the cluster can write, promote, or delete anything"), D4 result is **automatically FAIL for the pre-remediation baseline**; the two-identity test in step 2 is reserved for a post-remediation reassessment round.

1. Enumerate registry stages available on the deployed MLflow version (v2.19.0 supports both stages and aliases; document which the corpus will adopt for resolution of PC §4.2 `model_id` + `model_version`).
2. *(Post-remediation only)* Attempt a `Staging` → `Production` transition using two identities: (a) `training-pipeline` identity that should NOT be able to promote to production; (b) `release-engineer` identity that SHOULD. If both succeed or both fail, promotion governance is un-enforced (D4 finding).
3. **Immutability with digest recording (v0.2):** log a model; record its canonical content-hash digest at registration; attempt mutation via BOTH (a) MLflow API (`log_model` with same version) and (b) direct S3 `PutObject` overwrite of the artifact path; re-resolve the model version via MLflow API; verify content-hash unchanged. If either mutation succeeds and re-resolution returns a changed hash, D4 finding.
4. Query the audit log (`model-version-transition` events) for all promotion attempts. If not queryable, D4 finding. Verify each transition has an attributed identity (not "anonymous" or empty).

### D5 methodology *(v0.2 — continuous calibration envelope per H4; scoping-gate for owners per H7 refined; burst per M17)*

**Workload envelope (scoping-approval outcome requirement):** the meeting produces named owners for (a) AB-028 model-training workload (who determines training-run frequency + retries + retry budget); (b) PC §8 calibration-publication workload (who owns continuous-cadence calibration recomputation). Envelope numbers below are v0.2 placeholders — each is confirmed or overridden at scoping-approval:

- **Experiment tracking:** ≤ 500 training runs / month per active spike (AB-028 + AB-029 + future spikes ≤ 5 in flight), so ≤ 2,500 runs / month steady state.
- **Continuous calibration (per PC §8):** sliding-window recomputation triggered by ground-truth label arrivals. Assume ≤ 10 cohorts × label-arrival-rate 100 events/day/cohort = 1,000 calibration writes/day = ~30,000 writes/month. Each ~100KB. **Weekly baseline calibration is additive**: ~40 writes/month at ~100KB.
- **Drift-alarm evaluations (per PC §8):** feature-distribution drift computed on every prediction OR on a sampled subset; assume 100 evaluations/day/cohort × 10 cohorts = 1,000/day = ~30,000/month. Each ~10KB.
- **Model artifacts:** ≤ 20 model versions promoted / month; artifact size ≤ 100MB per version.
- **Concurrent writers:** ≤ 10 (training pipeline, continuous calibration publisher, drift-alarm publishers per cohort, human-triggered runs). Burst up to 50 during a training-fleet rerun.

**Assessment execution:**
1. Replay the workload envelope for 24h steady-state against the deployed MLflow; measure P50/P95/P99 API latencies; measure Postgres row growth; measure S3 write throughput.
2. **Burst phase (v0.2 addition):** for a bounded window (e.g., 10 minutes), replay at 10× steady-state; verify no database-connection exhaustion; verify no S3 throttling causing silent write loss; verify retry-amplification does not compound the burst.
3. **Soak phase (v0.2 addition):** replay steady-state for 24h continuous; verify no Postgres connection leak, no memory growth beyond documented limit, no S3 client-side retry queue growth.
4. Extrapolate to 30-day projection; compare against fitness thresholds.

**Scoping-approval gate:** if the AB-028 owner + PC §8 calibration owner cannot be named at the scoping-approval meeting, D5 is **deferred with a dated follow-up** (per §6 APPROVED WITH DEFERRALS envelope); §B1-§B4-analog items may still lock. Deferred D5 blocks the overall verdict on the production-dependency question.

### D6 methodology *(v0.2 — predeclared SLO per H8; real drain per M18; observability per H12 fold)*

**Prerequisite:** SLO tuple predeclared BEFORE assessment. If no SLO document exists, D6 result is FAIL (not "draft one during assessment"). The scoping-approval meeting either produces the SLO tuple or defers D6 pending SLO drafting by an SRE.

**SLO tuple to predeclare:** availability target (e.g., 99.5% monthly); measurement window (e.g., 30d rolling); max contiguous outage (e.g., 15 minutes — must be tighter than PC §8 continuous calibration cadence tolerance); publication deadline for calibration-gap detection (how long before an operator sees a calibration miss); retry budget (how many client-side retries before the client abstains); recovery threshold (SLI recovery time before the system is considered healthy again).

1. Query the Kubernetes API for the MLflow Deployment's PodDisruptionBudget (`kubectl get pdb -n forge-ml`). If none present, D6 finding.
2. **Real drain against a representative disposable clone (v0.2):** provision a clone of the MLflow deployment with identical scheduling / PDB / storage / DNS / replica settings in a test namespace; execute actual `kubectl drain` (not `--dry-run=server`) on the node hosting the clone; capture client-visible outage duration, failed write count, retry-storm behavior, recovery time. Server-side dry-run does NOT satisfy this step — it does not measure client-visible unavailability.
3. Verify the SLO tuple against measured outage from step 2: if measured outage exceeds max-contiguous-outage, D6 FAIL.
4. If single-replica remains: verify the "idempotent writes + N-minute-tolerable-downtime" statement is documented AND N is **quantified in minutes explicitly against the PC §8 continuous safety cadence** (not "reasonable" or "tolerable" — a specific integer).
5. **Observability sub-checks (v0.2):**
   - Prometheus SLI export exists for: API latency P50/P95/P99, Postgres connection pool utilization, S3 write success rate, calibration-publication success rate. Any missing metric is an observability finding.
   - Alert routing verified: pick one SLI, deliberately breach in a test namespace, verify alert reaches PagerDuty / configured on-call channel within documented latency.
   - Dashboard evidence: SRE-facing dashboard covering the SLIs above + calibration-gap detection exists AND has documented ownership (which SRE is responsible for watching it).
   - Synthetic probe: a canary consumer measuring end-to-end path (log_metric → search_runs read-back) with latency-tracked alerting on failure.
   - Circuit-breaker drill: verify PC §8's circuit-breaker fires and routes predictors to advisory-only when the calibration error budget exhausts.

### D7 methodology *(v0.2 NEW — client SDK integration per H10)*

1. Enumerate all predictor codebases that import `mlflow` (grep repo for MLflow SDK imports); document the SDK version pinned in each. Verify SDK version compatible with server v2.19.0 per MLflow's compatibility matrix.
2. For each predictor, verify explicit timeout configuration (not the SDK default of "wait indefinitely"); document the timeout value.
3. Retry semantics test: deliberately return HTTP 500 from a mock MLflow endpoint; verify predictor retries the documented number of times then abstains (per PC §3 `type=abstain`), not indefinitely, not silently.
4. Credential-refresh test: rotate the IRSA token (or equivalent) mid-run; verify predictor transparently picks up the new credential without restart.
5. Duplicate-write idempotency: call `log_metric` twice with the same key + step; verify only one row is recorded (or that both are recorded with distinguishable metadata such that downstream aggregation is unambiguous).
6. Partial-failure fallback: deliberately make MLflow unreachable (NetworkPolicy block); verify predictor emits `type=abstain` with `reason=mlflow_unreachable` per PC §3 rather than blocking or emitting a low-confidence guess.

### D8 methodology *(v0.2 NEW — software lifecycle per M21)*

1. Verify the manifest pins to an **immutable image digest** (e.g., `mlflow/mlflow@sha256:...`), not a mutable tag (`mlflow/mlflow:v2.19.0`). If tag-pinned, D8 finding.
2. Verify all Python dependencies installed in the pod (`psycopg2-binary`, `boto3`) are pinned to specific versions with hashes (e.g., via a `requirements.txt` with `--hash=sha256:...` or an image layer that pins them). If unpinned, D8 finding.
3. Vulnerability posture: query the pinned image against the CVE database (Trivy or equivalent scanner); document any HIGH-or-CRITICAL findings + their remediation status per the existing Snyk/OWASP-DC defer conventions.
4. Client/server compatibility: document which MLflow SDK versions are supported against server v2.19.0; verify §D7's predictor pins fall within the compatibility matrix.
5. Schema migration rehearsal: on a test MLflow instance, execute a v2.19 → v2.20+ upgrade using MLflow's documented migration path; verify migration succeeds + rollback path succeeds. Document the migration runbook.
6. Restart reproducibility: delete the MLflow pod; let Kubernetes recreate; verify the recreated pod is byte-identical (same image digest, same env vars, same volume mounts) and returns to serving within a documented time budget.

---

## 6. Predeclared decision framework

### 6.1 Per-dimension verdicts

For each of D1-D8, one of:

- **PASS** — fitness definition met without qualification. No follow-up filed.
- **PASS-WITH-MITIGATIONS** — fitness definition met given **implemented and verified** compensating controls that are in-place TODAY. Follow-up AB-NNN filed for any residual scope + owner. *(v0.2 tightening per H9: planned-but-not-implemented mitigations do NOT qualify — those are FAIL until closure + reassessment. "OK for calibration publication only, NOT for model promotion until D4 gap closed" is FAIL on the promotion functionality, not a mitigation.)*
- **FAIL** — fitness definition not met, and the gap blocks the specific corpus dependency in that dimension. Follow-up AB-NNN filed with scope + owner + rough effort estimate.

### 6.2 Overall verdict

The overall "OK to depend on MLflow for the reference workload declared in §2.1 + §5.D5 (per §2.4 target-boundary tuple)" verdict is derived, not voted:

- **All 8 PASS** → OK to depend on for the declared reference workload. Production T1 predictor may ship for the specific `deploy_slo_breach_60m_association_v0` estimand + workload envelope; other estimands require delta assessment per §12.
- **All non-FAIL, ≥ 1 PASS-WITH-MITIGATIONS (implemented compensating controls per §6.1 v0.2 tightening)** → OK to depend on FOR THE SCOPE covered by the implemented mitigations. Explicit boundary statement required (e.g., "OK for tracking + calibration publication with the alerting alarm-drill from D6 in place; unspecified scope for high-burst training-fleet reruns exceeding D5 envelope").
- **≥ 1 FAIL** → NOT OK to depend on until the FAIL dimensions close. Follow-up work must complete before production T1 predictor ships. Assessment closes with a specific list of prerequisite work.

### 6.3 Disqualification rules — no-mitigation-permitted list *(v0.2 rewrite per M23 to remove §6.2 redundancy)*

The dimensions below MUST be classified FAIL if their fitness gap exists AND can never be downgraded to PASS-WITH-MITIGATIONS. This differs from the §6.2 aggregate rule (which says any FAIL → NOT OK): §6.3 is the list of gaps for which even a compensating-control PASS-WITH-MITIGATIONS is not acceptable — the gap must actually close.

- **D1 FAIL on any-writer-can-mutate** — un-authenticated tracking server disqualifies for anything beyond the assessment itself. The assessment writes findings to an un-auth'd server only because that action IS the assessment output.
- **D3 FAIL on `-dev` bucket** — policy backstop per adopted ForgeWorks convention. Independent of the D3 technical properties (all of which MUST also independently pass — the naming rule is not a substitute for versioning + lifecycle + governance sub-checks).
- **D3 FAIL on governance envelope** — SC §3.6 propagation to MLflow artifacts is a corpus non-negotiable; a bucket that cannot enforce residency / retention / tenant-isolation for the classified data flowing through it is not usable for production dependency regardless of naming.
- **D4 FAIL on immutability** — mutable model versions break PC §4.2's `model_id` + `model_version` audit-integrity promise.
- **D4 FAIL on promotion RBAC (v0.2 addition per M20)** — unauthorized-promotion capability OR missing-transition-attribution defeats the audit-integrity promise identically to mutability. Both are D4 gate conditions.

### 6.4 What "OK to depend on" DOES NOT mean

- It does NOT mean MLflow is the best long-term choice; it means it clears the bar for v0 dependency.
- It does NOT extend to v1+ estimands automatically; each new estimand's demands are compared against the assessed capacity envelope (D5) at the time of shipping.
- It does NOT include multi-region, HA-across-zone, or DR-across-region posture; those are v1+ concerns filed as their own AB-NNNs if the corpus needs them.

---

## 7. Deliverables

- **AB-032 Readiness Report** at `docs/decisions/dynamic-reliability/MLFLOW_READINESS_ASSESSMENT.md` (v0.1) — per-dimension verdicts across D1-D8, evidence artifacts referenced (raw commands + outputs, not just prose per §5.0), overall verdict, target-boundary tuple (per §2.4), workload envelope + owner attribution (per §5.D5), filed follow-up AB-NNN list, dated. Assessor identity independent of deployment owner (per §5.0).
- **Postgres backup / restore runbook** at `docs/runbooks/mlflow-postgres-restore.md` — the D2 drill turned into an executable runbook.
- **Filed follow-up AB-NNN entries** in `roadmap/AUTOMATIONS_BACKLOG.md` for every dimension that lands `PASS-WITH-MITIGATIONS` or `FAIL`. Each entry: concrete scope, owner (or `[NEEDS-OWNER]`), rough effort estimate, dependency on AB-032 report.
- **CHANGELOG entry** under `### Added` referencing the report + linked follow-ups.
- **README follow-up-table row-set closure** — AB-032 row updated with resolution date + link to report.

---

## 8. Risks

- **R1: Assessment produces "PASS" on paper but real production load breaks the deployment.** Mitigation: D5 envelope MUST be conservative; if the actual production load exceeds envelope by > 2× on any dimension, the report's PASS is invalidated and a re-assessment is required before further production dependency. This is documented in the report's own "re-assessment triggers" section.
- **R2: Follow-up AB-NNN entries file and then rot.** Mitigation: each filed entry gets a `blocks:` annotation naming the specific corpus dependency it blocks (e.g., "blocks: PC §4.2 model promotion, PC §8 continuous calibration"). Rot-check is a `grep AB-032 roadmap/` at any future spike scoping approval.
- **R3: The assessment surfaces a broken assumption in the corpus itself** — e.g., PC §8's continuous per-cohort calibration (sliding-window recomputation on label arrival, drift alarms, circuit-breaker firings) turns out to be a load the current deployment cannot support at any reasonable sizing. Mitigation: this is a valid outcome; the report's overall verdict may be "corpus assumption needs revision, filed as AB-NNN, cannot bless dependency until revised." Assessment is not obligated to preserve corpus assumptions that don't survive contact with the substrate.
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

- [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) *(v0.1)* — §4.2 defines required `model_id` (MLflow-anchored) + `model_version` (semver) fields for provenance; §8 requires continuous per-cohort calibration to MLflow (sliding-window recomputation on label arrival) with weekly as the audit-cadence baseline. Both are the source of MLflow-as-runtime-dependency; both are consumers of this assessment's verdict. *(v0.2 fix: v0.1 draft incorrectly cited a `model_ref: mlflow://models/...` scheme not present in PC §4.2, and characterized §8 as weekly-only — the actual contract is continuous safety cadence.)*
- [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) *(v0.1)* — §5 (Open questions) records MLflow readiness as a v1-prerequisite question — the design *assumes* MLflow serves calibration curves + model registry, and that assumption is under evaluation by this RFC. §3.6 defines the governance envelope that D3 governance sub-checks (v0.2) must verify propagation of. *(v0.2 fix: v0.1 draft incorrectly cited "SC §11" — SC has no §11; the correct anchor is SC §5 Open questions.)*
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
- **2026-08-02:** v0.1 → v0.2 lift. Codex round-1 loop on this RFC (audit trail at `research/feedback_loops/dynamic-reliability-AB-032_MLFLOW_READINESS/20260802T104925Z/` — repo-ignored, per corpus convention) returned `needs-revision` with 25 findings (13 HIGH / 12 MEDIUM). Empirical verification pass performed against PC §4.2 + §8 and SC before disposition; 3 verifiable Codex claims about the corpus (RFC misattributed `model_ref` to PC §4.2 where actual fields are `model_id` + `model_version`; RFC called PC §8 "weekly" where actual contract is continuous safety cadence; RFC cited SC §11 which doesn't exist — MLflow readiness is at SC §5) all confirmed correct. 13 findings applied directly; 7 refined-with-folding to avoid dimension proliferation (H1 target-boundary → new §2.4 subsection not a scored dim; H12 observability folded into D6; H13 platform-security folded into D1; H2 governance-storage folded into D3 fitness + §6.3 hard gate; M20 D4 promotion-RBAC folded into §6.3; M21 software-lifecycle became new D8; M23 §6.3 redefined as no-mitigation-permitted list vs §6.2 aggregate rule); 3 partials (M15 D2 disk-full alarm methodology extended; M19 D3 `-dev` bucket kept as policy backstop with technical properties also required; H7 D5 owners refined to scoping-approval-outcome-requirement not pre-lock); 2 GAP added to methodology (M22 §5.0 mandatory-full-execution rule; M24 bundled with H1); 0 disagreements. Structural changes: **6 dimensions → 8** (NEW D7 client-SDK integration + runtime resilience; NEW D8 software lifecycle + upgrade compatibility; D1/D3/D6 renamed to absorb folded scope); **§2.4 target deployment and trust boundary subsection**; **§5.0 execution rules (mandatory D1-D8 completion + assessor independence + baseline vs remediation separation)**; **§5.D1 rewritten as actor-by-operation matrix (7 identities × ~15 operations + platform-security sub-checks)**; **§5.D4 declares D1 identity provisioning as hard prerequisite**; **§5.D5 continuous calibration workload envelope per PC §8 + burst/soak phases + scoping-approval-outcome owner-naming gate**; **§5.D6 predeclared SLO tuple + real drain against disposable clone + observability sub-checks**; **§5.D7 + §5.D8 new methodologies**; **§6.1 PASS-WITH-MITIGATIONS tightened to require implemented + verified controls**; **§6.3 rewritten as no-mitigation-permitted list**; **§10 PC §4.2 + PC §8 + SC §5 citation corrections**; **§12 verdict binding rewritten as dependency-fingerprint tuple (infra/mlflow + Postgres + S3 bucket policy + IAM + NetworkPolicy + Ingress + cluster version) with per-dimension reassessment triggers**. Second-look over-concession audit performed pre-apply (100% AGREE ratio held after refinements — this loop's over-concession risk was dimension proliferation not substance rescue; caught 5 requested new dims → 2 net new after folding). Base commit: current main tip (`6622596`).

---

## 12. Iteration protocol

- Same as sibling scoping RFCs. Substantive changes bump `v0.1` → `v0.2` → …
- Post-scoping-approval, this RFC becomes the contract for the assessment; changes to §4 dimensions, §5 methodology, §6.1 verdict semantics, or §6.3 no-mitigation-permitted list require RFC amendments.
- On assessment completion, the report at `docs/decisions/dynamic-reliability/MLFLOW_READINESS_ASSESSMENT.md` becomes the canonical production-dependency verdict for the assessed reference workload (per §2.1 + §5.D5) on the assessed dependency-fingerprint tuple (per below); this RFC may be archived under `research/spikes/AB-032-mlflow-readiness/` at that time.
- **Verdict binding — dependency-fingerprint tuple (v0.2 rewrite per H11):** verdict is bound to ALL of the following, not just `infra/mlflow/`:
  - `infra/mlflow/base/mlflow.yaml` at a specific commit SHA
  - Postgres cluster manifest fingerprint (the `forge-postgres-postgresql` deployment + backup config at a specific commit)
  - S3 bucket policy hash for the artifact bucket
  - IAM role trust-policy fingerprint for the MLflow workload identity
  - NetworkPolicy manifest for the `forge-ml` namespace
  - Ingress manifest for any external MLflow exposure
  - Kubernetes cluster version
  - MLflow image digest + Python dependency hashes (per D8)
  - Predictor SDK versions (per D7)
- **Per-dimension reassessment triggers:** any change to the manifest / policy / config listed above invalidates the verdict for the affected dimension(s) and triggers reassessment (delta-only where possible, full where the change is structural). Examples: Postgres backup-config change → D2 reassessment; S3 bucket-policy change → D3 reassessment; IAM trust-policy change → D1 reassessment; MLflow image-digest change → D8 + D6 (behavior may change) reassessment; new predictor SDK version → D7 reassessment.
