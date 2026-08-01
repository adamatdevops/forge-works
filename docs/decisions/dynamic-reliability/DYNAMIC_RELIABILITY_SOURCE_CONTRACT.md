# Dynamic Reliability — Source Contract (v0.1)

> **Status:** Design stub (v0.1). First artifact of the "Dynamic Reliability" design phase.
> **Origin:** Discussion in `planning/IMPORTANT_IDEA.md` (2026-07-24, local-only per repo `.gitignore` convention).
> **Location note:** Migrated 2026-07-25 from `planning/DYNAMIC_RELIABILITY_SOURCE_CONTRACT_v0.md` to this tracked path — the v0.1 corpus is stable enough to belong under `docs/decisions/`. Sibling design docs migrated in the same batch; see `docs/decisions/dynamic-reliability/README.md` for the index. `planning/IMPORTANT_IDEA.md` (origin discussion) stays local; `roadmap/AUTOMATIONS_BACKLOG.md` (full backlog) also stays local — AB-028..032 summarized in the README.
> **Lifecycle note:** Once the design phase completes and this doc + siblings graduate to v1.0, `planning/IMPORTANT_IDEA.md` becomes deletable and the docs may be consolidated into a single `docs/decisions/DYNAMIC_RELIABILITY.md`.
> **v0.1 provenance:** Restructured 2026-07-24 in response to Codex round-1 critique; post-hoc dispositions review 2026-07-25 (reconciled.md retained locally under `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/` per the codex-review workflow — that path is repo-ignored by design, contact repo owner for the full audit trail). Major changes: authority hierarchy replaces operator/reviewer as primary doctrine (F11), v0 scope narrowed to shadow-mode/advisory-only (F1), namespaced identity claims replace flat join-key catalog (F14), severity demoted to presentation metadata (F9), governance envelope added as required field (F8), adapter-SDK note narrows the "no engine edits" claim (F23), iteration protocol permits experimental AB-NNN filing before v1 (F4).

---

## 1. Purpose

Define the single contract that any external source must satisfy to be plugged into the ForgeWorks Dynamic Reliability layer.

**Design principle:** the *predictive core* of the engine never hardcodes knowledge about a specific source. Terraform, DataDog, PagerDuty, Salesforce, and any future/internal tool conform to the same contract at the predictive-core boundary. Source-specific engineering (auth, pagination, rate limits, ordering, retries, extraction) still exists per source — but it lives in an **adapter SDK** (see §8), not in the predictive core.

**What this document is:** the source-side interface — what each source must declare (via the adapter layer) to be legible to the predictive core.

**What this document is not:**
- Not the model architecture (that's downstream of the contract).
- Not the wire protocol (JSON schema, protobuf, Avro — deferred to `WIRE_PROTOCOL.md`).
- Not the ingestion runtime (Flink job / connector / batch — deferred to AB-029 architecture spike).
- Not the full source catalog (this doc has one worked example only).
- Not the ground-truth or intervention schema (deferred to `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`).

---

## 2. Doctrine — authority hierarchy, not operator/reviewer

**Primary doctrine axis:** *authority hierarchy* — every AI-involved surface in ForgeWorks belongs to exactly one tier:

| Tier | Name | Authority | Examples |
|---|---|---|---|
| T1 | **Evidence generation** | Produces observations; no downstream authority. | Vocabulary emission, anomaly-flag production, feature attribution logs. |
| T2 | **Recommendation** | Advises humans/systems; decision authority stays elsewhere. | PR-comment suggestions (CodeRabbit shape), dashboard annotations, prioritized worklists. |
| T3 | **Human-approved decision** | Routine automation with human-in-loop for exceptions. | Auto-approve-if-clean workflows where a human must sign off on any exception. |
| T4 | **Actuation** | Autonomous action; requires explicit per-class doctrine approval. | Auto-rollback, auto-scale, auto-block-deploy. **Forbidden in v0.** |

**v0 doctrinal scope:** Dynamic Reliability predictions live at **T1 (evidence generation) or T2 (recommendation) ONLY** in v0. Predictions may annotate, prioritize, or contextualize; they MUST NOT gate deterministic checks, block deployments, or trigger remediation. Any T3/T4 surface requires a separate approved doctrine change and NEVER lands in v0.

**Why:** Codex round-1 flagged that the original operator/reviewer framing conflated *runtime placement* with *decision authority* — this doctrine keeps them independent. The v0 constraint to T1/T2 rests on independent grounds: F10 (self-fulfilling prediction) shows that any T3/T4 authority in v0 makes counterfactual identification impossible — without shadow-mode accumulation, "the intervention that fired because of the prediction" and "the outcome that would have occurred anyway" are unrecoverable. AB-028's feasibility spike has produced no evidence base yet to justify T3/T4 either. *(Post-hoc dispositions review 2026-07-25: the earlier v0.1 language cited `.codex/config.toml [ml]` as "binding project posture" — that file is user-scoped Codex-agent behavior config, NOT repo-tracked ForgeWorks doctrine. Codifying "advisory-only v0" as repo-tracked doctrine is a v1 prerequisite; see §5.)*

**Runtime placement** (inside engine vs. outside), **lifecycle timing** (pre-deploy vs. runtime), and **pool-specific policies** are all secondary dimensions, orthogonal to the authority tier. A T2-recommendation source can be inside the engine (a Flink job publishing recommendations) OR outside (a scanner posting PR comments). A T1-evidence source can run pre-deploy OR at runtime.

**Reviewer doctrine** (deterministic gates like OWASP DC, Snyk, Checkov, CodeRabbit) is not a competing doctrine — those are T3/T4 surfaces (a Snyk verdict on `main` push blocks the deploy). They cohabit with T1/T2 Dynamic Reliability surfaces through the arbitration protocol in `DOCTRINE_INTERPLAY.md` (drafted v0 2026-07-24).

---

## 3. The contract — six required fields

Every source declares the following. Each field has a strict definition + a "how to fill it out" hint. Fields 3.1–3.5 mirror the original v0 five-field structure; §3.6 (Governance Envelope) was added in v0.1 per Codex F8.

### 3.1 Pool

**Definition:** The reliability pool(s) this source contributes to. A pool is a coarse-grained **domain** category.

**Initial pools (extensible):**
- `infra` — declarative infrastructure state (Terraform, Pulumi, CDK, CloudFormation)
- `delivery` — build + deploy pipelines (Jenkins, GitHub Actions, ArgoCD, GitLab CI)
- `runtime` — production behavior (Prometheus, DataDog, Sentry, New Relic)
- `incident` — alert + response signals (PagerDuty, Opsgenie, Statuspage)
- `vcs` — code-change events (GitHub, GitLab, Bitbucket)
- `product` — user-facing outcomes (LaunchDarkly flags, Amplitude analytics)
- `business` — downstream customer signals (Salesforce, Stripe, Zendesk)
- `custom` — anything internal that speaks the contract

A source may declare membership in multiple pools (e.g., GitHub is both `vcs` and `delivery` when GitHub Actions is in use).

**Orthogonal signal role** *(new in v0.1, per Codex F22):* every emitted event ALSO declares one of:
- `observation` — data that predictions reason over (default; most sources)
- `label` — ground truth (dedicated stream per `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md`)
- `intervention` — action taken because of a prediction (dedicated stream, enables counterfactual eval)
- `policy` — the decision policy version applied (metadata about which arbitration rules were active)
- `feedback` — human corrections applied to prior predictions

Pool = domain axis. Signal role = supervision/control axis. Independent. A source can emit multiple signal roles across different event types (e.g., PagerDuty emits `observation` for alerts, `feedback` when an on-call marks an alert as false-positive).

**Onboarding hint:** if none of the existing pools fit, propose a new pool in your source's contract PR. New pools require a one-line justification and MUST be additive.

---

### 3.2 Vocabulary

**Definition:** The closed token set this source emits + the compatibility contract for how it evolves.

**Required sub-fields:**
- `event_types` — the enumerated set of distinct event categories this source produces. **Tokens MUST be namespaced by source** (v0.1 change per F9): `terraform.plan_started`, `terraform.apply_failed`, `datadog.slo_burning`, etc. Never bare `apply_failed` or `slo_burning` — namespacing prevents semantic collision when multiple sources emit similarly-named events with different meanings.
- `resource_types` — the enumerated set of things this source acts on (potentially large; growing enum allowed). Also namespaced (`terraform.aws_instance`, `datadog.monitor`).
- `severity_scale` — canonical 5-level scale (`info` / `low` / `medium` / `high` / `critical`). **Presentation metadata only** (v0.1 change per F9) — used for human-facing surfaces (Slack digests, dashboards) but NEVER as a training signal or a cross-source join key. Two events sharing severity `high` (a Terraform `apply_failed` and a DataDog `slo_burning`) are NOT equivalent — different consequences, different base rates, different action classes. Cross-source features become task-specific and learned, not equated by shared labels.
- `outcome_labels` — the ground-truth labels a supervised model could train against. Also namespaced (`terraform.apply.success`, `terraform.apply.partial`). See `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` for how these get bound to actual observed outcomes.
- `compatibility_range` *(new in v0.1, per Codex F15)* — the model-vocab compatibility contract. Declares which model versions can consume this vocabulary version; any deployed model outside the range must quarantine/fallback-route on unknown tokens rather than silently coerce.

**Design constraint:** the vocabulary MUST be finite and versioned. Vocabulary drift (new enum values) is a first-class event — the engine SHOULD detect unknown tokens and emit a vocabulary-drift signal rather than silently coerce.

**Onboarding hint:** don't try to model every possible token in v0. Enumerate the top-N by frequency, mark the rest as `<source>.unknown_<type>`, and let the vocabulary grow from real traffic — BUT: rare-but-catastrophic events (security incident classes, DR events, catastrophic-failure states) MAY warrant retention regardless of frequency; see `VOCABULARY_DESIGN.md` §4/§5 for the composite retention criterion (F6).

> **Deep dive in a dedicated design doc:** the deeper questions — *what makes a good vocabulary?*, *how to design one from scratch for a new source?*, *how to evolve one without breaking downstream models?*, *token granularity trade-offs* — are covered in `docs/decisions/dynamic-reliability/VOCABULARY_DESIGN.md` (v0.1). This contract only specifies the *shape* a vocabulary must take; VOCABULARY_DESIGN.md covers how to build a good one.

---

### 3.3 Timeframe

**Definition:** The temporal characteristics of the source's signal — cadence, freshness, and decay.

**Required sub-fields:**
- `cadence` — `streaming` / `near-realtime` / `periodic` / `on-demand`.
- `max_age_useful` — after how long does this signal stop contributing to a prediction?
- `decay_curve` — `flat` / `linear` / `exponential` (half-life declared separately).
- `expected_gap_tolerance` — the longest inter-event gap that is *normal* for this source. Gaps longer than this ARE a signal.

**Onboarding hint:** default to `exponential` decay with a half-life = 25% of `max_age_useful` if you have no better information. Tune from data later.

---

### 3.4 Identity Claims (was: Cross-References)

**Definition:** The **namespaced identity claims** this source emits so downstream consumers can join them across sources through a versioned entity-resolution layer.

**v0.1 change per Codex F14:** the original design treated `service_name`, `resource_id`, `customer_id` etc. as globally-joinable flat keys. That's not an identity model — it's a name-collision generator. Distributed identity requires namespace, authority, validity window, and match confidence. Renamed to Identity Claims to make the shape explicit.

**Required sub-fields:**
- `emitted_claims` — the identity claims this source emits. Each claim is a tuple: `(authority, key_type, source_field, join_reliability, validity_window)`.
  - `authority` — who mints this identifier (e.g., `terraform` for its own resource IDs, `github` for its own commit SHAs, `internal_directory` for canonical service names).
  - `key_type` — one of the canonical claim types: `service_id`, `deployment_id`, `commit_id`, `resource_id`, `request_id`, `trace_id`, `team_id`, `tenant_id`.
  - `source_field` — where the raw value lives in the source event.
  - `join_reliability` — `always` / `usually` (>80%) / `sometimes` (20-80%) / `rarely` (<20%).
  - `validity_window` — how long a claim of this shape stays authoritative (e.g., Terraform `resource_id` is authoritative for the lifetime of the resource in state).
- `no_direct_join_keys` *(strong claim)* — the source MUST NOT emit un-namespaced identifiers that consumers might mistake for canonical keys. Only namespaced claims go on the wire.

**Design constraint:** joins are resolved through the **entity-resolution layer**, not by string-matching on the wire. The ER layer maintains: source authority per claim type, validity windows, match method (exact / fuzzy / probabilistic), match confidence. Two claims joining is not a boolean — it's a scored resolution.

**Onboarding hint:** if your source has NO claims that resolve to canonical entities, it can still contribute to same-pool same-source predictions, but it cannot participate in cross-source correlation. That's a real limitation to flag in the contract, not a bug in the source.

---

### 3.5 Segmentation

**Definition:** The dimensions the source supports for slicing predictions.

**Required sub-fields:**
- `dimensions` — the segmentation axes this source populates: `per_service`, `per_environment`, `per_region`, `per_team`, `per_tenant`, `per_customer_tier`, `per_deployment`, `per_release_channel`. (Extensible; canonical set lives repo-global.)
- `default_segmentation` — the coarsest useful slice when no dimension is specified.
- `cardinality_hints` — approximate cardinality (`low` < 10, `medium` 10-1000, `high` > 1000).

**Onboarding hint:** don't declare a dimension you can't reliably populate. A source that says "yes, I support `per_customer_tier`" but only tags 5% of events is worse than a source that honestly says "no."

---

### 3.6 Governance Envelope *(new in v0.1, per Codex F8)*

**Definition:** The data-governance metadata every emitted event MUST carry. Non-optional. Sources that cannot fill it are quarantined to a governance-restricted pool.

**Required sub-fields:**
- `tenant_id` — the tenant/organization identifier the event belongs to. Cross-tenant joins are forbidden by default.
- `data_classification` — `public` / `internal` / `confidential` / `restricted`. Determines who can consume this data downstream.
- `purpose_limitation` — the purposes this data may be used for (e.g., `reliability_prediction`, `incident_correlation`). Predictions consuming this event MUST be for a listed purpose.
- `retention_days` — how long this event and its derivatives may be retained. Ground-truth joins and calibration histories inherit this.
- `residency_region` — the region(s) the data may be stored/processed in.
- `redaction_policy_ref` — pointer to the redaction rules applied to this event (e.g., PII fields already stripped, or `none`).
- `access_policy_ref` — pointer to the access-control policy for downstream consumers.
- `cross_tenant_training_allowed` — default `false`. Only `true` after explicit approval documented at the referenced policy.

**Why non-optional:** the design admits sources that carry PII, customer IDs, business signals (Salesforce, Stripe, Zendesk). Without a governance envelope on every event, downstream consumers (models, dashboards, MLflow artifacts, audit sinks) have no basis to enforce residency, retention, or tenant isolation.

**Onboarding hint:** if your source emits data that spans tenants, you MUST partition per-tenant at the source and emit distinct events, one per tenant. Never emit a single event that mixes tenant scopes.

---

## 4. Worked example — Terraform (source contract v0.1)

Filling out the contract for Terraform as the cleanest first source (declarative, versioned, small vocabulary, well-defined event model). Updated for v0.1: namespaced vocabulary, identity claims (not flat keys), governance envelope.

```yaml
source: terraform
version: 0.2.0                       # bumped for v0.1 contract shape
owner: platform-team                 # PLACEHOLDER — see AP-7 / Operating model note in §5
contract_version: v0.1

pool:
  - infra
signal_roles:
  observation: true                   # most events
  intervention: false                 # Terraform doesn't act on predictions
  label: partial                      # apply outcomes are labels for infra-pool predictors

vocabulary:
  event_types:
    - terraform.plan_started
    - terraform.plan_completed
    - terraform.plan_failed
    - terraform.apply_started
    - terraform.apply_completed
    - terraform.apply_failed
    - terraform.apply_partial
    - terraform.drift_detected
    - terraform.state_lock_acquired
    - terraform.state_lock_released
    - terraform.state_lock_contention
    - terraform.destroy_started
    - terraform.destroy_completed

  resource_types:
    namespace: terraform
    enum_policy: growing_enum
    initial_top_n: 50
    unknown_token: terraform.unknown_resource

  severity_scale:
    presentation_only: true           # v0.1: NOT a training signal, NOT a join key
    canonical_mapping:
      info:     [terraform.plan_started, terraform.plan_completed, terraform.state_lock_acquired, terraform.state_lock_released]
      low:      [terraform.apply_started, terraform.apply_completed]
      medium:   [terraform.drift_detected, terraform.apply_partial, terraform.state_lock_contention]
      high:     [terraform.plan_failed, terraform.apply_failed]
      critical: [terraform.destroy_started]

  outcome_labels:
    - terraform.apply.success
    - terraform.apply.partial
    - terraform.apply.failed
    - terraform.apply.reverted

  compatibility_range:
    min_model_version: 0.1.0
    max_model_version: 0.x            # any 0.x model; bump on breaking vocab changes
    on_unknown_token: quarantine       # not silent_coerce

timeframe:
  cadence: near-realtime
  max_age_useful: 90d
  decay_curve: exponential
  half_life: 14d
  expected_gap_tolerance: 7d

identity_claims:
  emitted_claims:
    - authority: internal_directory
      key_type: service_id
      source_field: tags.Service
      join_reliability: usually
      validity_window: while_resource_exists
    - authority: terraform_workspace
      key_type: environment
      source_field: workspace
      join_reliability: always
      validity_window: while_workspace_exists
    - authority: cloud_provider
      key_type: region
      source_field: provider.region
      join_reliability: always
      validity_window: forever
    - authority: git
      key_type: commit_id
      source_field: run.commit_sha
      join_reliability: always
      validity_window: forever
    - authority: terraform
      key_type: resource_id
      source_field: address           # e.g. aws_instance.web[0]
      join_reliability: always
      validity_window: while_resource_exists
  no_direct_join_keys: true

segmentation:
  dimensions:
    - per_service
    - per_environment
    - per_region
    - per_team
    - per_deployment
  default_segmentation: per_environment
  cardinality_hints:
    per_service: medium
    per_environment: low
    per_region: low
    per_team: low-medium
    per_deployment: high

governance_envelope:
  tenant_id: forge-works               # single-tenant deployment for now
  data_classification: internal        # infra state; no PII
  purpose_limitation: [reliability_prediction, incident_correlation]
  retention_days: 730
  residency_region: [us-east-1, eu-west-1]
  redaction_policy_ref: policies/redaction/terraform_v1.yaml
  access_policy_ref: policies/access/infra_pool_v1.yaml
  cross_tenant_training_allowed: false
```

---

## 5. Open questions (to close before v1)

- [ ] **Ground-truth + intervention schema** — `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` must reach v0 before this contract can graduate. AB-030.
- [ ] **Doctrine interplay** — `DOCTRINE_INTERPLAY.md` v0 drafted 2026-07-24. Its v0→v1 promotion is a **T3/T4 consumer prereq**, NOT an SC/PC v0→v1 blocker *(post-hoc dispositions review 2026-07-25)*. AB-031.
- [ ] **Architecture placement** — Flink sibling vs. `pattern-matcher` extension vs. batch materialized view vs. dedicated inference service. AB-029 architecture spike.
- [ ] **Feasibility spike** — one source pair, one slice, one binary outcome, one read-only consumer, offline replay against deterministic + logistic-regression baselines with predeclared AUCPR, calibration (ECE + Brier), latency, cost. AB-028. Blocks contract graduation to v1.
- [ ] **MLflow readiness** — the design assumes MLflow serves calibration curves + model registry. Readiness assessment (auth, HA, backup/restore, promotion authority, artifact durability) needed before production. AB-032 ([scoping RFC v0.1](AB-032_MLFLOW_READINESS.md)).
- [ ] **Wire protocol** — JSON on Kafka is the default; case for Avro/Protobuf for schema evolution deferred to `WIRE_PROTOCOL.md`.
- [ ] **Vocabulary registration flow** — how does a new enum value get added? Manual PR / auto-register with review threshold / both?
- [ ] **Cross-reference key governance** — who owns the canonical key-type list in §3.4? What's the process to add a new one?
- [ ] **Source-onboarding SLA** — target time-to-productive for a new source (<1 week engineering + <1 week shadow traffic).
- [ ] **Second worked example** — non-IaC source (DataDog for `runtime`, or PagerDuty for `incident`) to stress-test the contract.
- [ ] **Operating model per predictor** *(new per F21)* — vocabulary owner ≠ operational owner. Model risk owner, data owner, service owner, on-call path, SLOs, rollback authority, retraining cadence, incident runbooks — the roles that must be staffed before *any* consumer of this source's predictions runs in production. Sourced from AP-7 in `VOCABULARY_DESIGN.md`.
- [ ] **Cross-pool aggregation** *(deferred per F5)* — the original v0 named `cross_pool_intersect` / `cross_pool_weighted` / `cross_pool_worst` modes; those were removed in v0.1. Deferred pending shared estimand, explicit missingness model, calibrated components, learned weights validated per pool combination. Belongs in a future `CROSS_POOL_AGGREGATION_v0.md`.
- [ ] **Repo-tracked home for advisory-only-v0 doctrine** *(post-hoc dispositions review 2026-07-25)* — v0.1 currently derives "shadow-mode / advisory-only" from F10's counterfactual argument (see §2 "Why"). That's a per-doc justification, not a project-level commitment. Before v1 promotion, this stance must land in a repo-tracked home: `planning/SCOPE.md` (currently IDP-scope only, finalized 2025-01-04), `planning/VISION.md`, or a new `planning/ML_DOCTRINE.md`. Otherwise v1 is graduating against a doctrine that lives only inside its own planning docs.

---

## 6. Iteration protocol

- Each substantive change to this document bumps `v0` → `v0.1` → `v0.2` → … in the title. v0.1 is this revision.
- **Experimental backlog entries (AB-NNN) may file BEFORE v1** (v0.1 change per Codex F4) to break the "no backlog until v1 / v1 needs production evidence" deadlock. AB-028 through AB-032 filed 2026-07-24 as the initial batch. v1 becomes the *retrospective* on those entries, not the *prerequisite* to filing them.
- The document stays `v0.x` until:
  1. At least two non-IaC source contracts have been drafted against it.
  2. All §5 open questions are closed.
  3. AB-028 feasibility spike produces evidence that a small model beats the deterministic baseline on the predeclared metrics.
  4. `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` has reached v0. (`DOCTRINE_INTERPLAY.md` at v0 is drafted but its v1 promotion is a T3/T4 doctrine-change prereq, not an SC/PC v0→v1 blocker — post-hoc dispositions review 2026-07-25.)
- On v1.0 the doc moves to `docs/decisions/DYNAMIC_RELIABILITY.md` and `planning/IMPORTANT_IDEA.md` becomes deletable.

---

## 7. Related documents

- `docs/decisions/dynamic-reliability/VOCABULARY_DESIGN.md` *(v0.1)* — deep dive on §3.2. Rewritten in v0.1 for composite retention (F6), severity as presentation metadata (F9), model-vocab compat (F15), operational ownership (F21).
- `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md` *(v0.1)* — downstream mirror. Rewritten for authority-hierarchy doctrine, shadow-mode v0 scope, decision-time arbitration envelope replaces required disagreement-signals, lifecycle events not mutation, per-type confidence.
- `docs/decisions/dynamic-reliability/GROUND_TRUTH_INTERVENTION_CONTRACT.md` *(drafted v0)* — new sibling. Label provenance, outcome window, censoring, human corrections, interventions, eligibility-for-evaluation.
- `docs/decisions/dynamic-reliability/DOCTRINE_INTERPLAY.md` *(drafted v0)* — new sibling. Authority hierarchy in operational terms; decision-time arbitration envelope; agreement/disagreement resolution.
- `planning/WIRE_PROTOCOL.md` — JSON vs. Avro vs. Protobuf, schema evolution. Not yet drafted.
- `planning/IMPORTANT_IDEA.md` — origin discussion (ephemeral; deletable when design phase closes).
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-028 through AB-032 filed 2026-07-24. Future AB-NNNs as v0.x work uncovers them.

---

## 8. Adapter SDK — narrowing the "no engine edits" claim

**v0.1 addition per Codex F23.** The original claim "onboarding a new source = filling out this contract" was too strong. Sources require real per-source engineering: authentication, pagination, rate limits, ordering guarantees, retry semantics, extraction of raw fields, semantic normalization to namespaced vocabulary tokens. None of that goes away — it's just packaged in an adapter, outside the predictive core.

**The correct claim:** *"Onboarding a new source requires no predictive-core changes."* The predictive core (feature engineering, models, calibration, aggregation) is source-agnostic. Adapters bear source-specific engineering.

**Adapter SDK requirements:**
- **Capability declaration** — which contract fields the adapter can fill (some sources genuinely can't emit all six §3 fields — declare that upfront).
- **Conformance fixtures** — golden-file test inputs/outputs covering the adapter's typical event shapes.
- **Replay tests** — the adapter must handle at-least-once delivery, out-of-order events, and gap recovery.
- **Rate-limit behavior** — declared and enforced; the predictive core assumes the adapter respects source APIs.
- **Failure isolation** — an adapter crash doesn't cascade to the predictive core or to other adapters.
- **Explicit ownership** — every adapter has an accountable owner (source or team). Adapter without owner = adapter that eventually breaks silently.

The SDK spec itself is out of scope for this doc; it'll live in a sibling once the first two source adapters exist and the shape is proven.
