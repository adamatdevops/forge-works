# Dynamic Reliability — Design Corpus (v0.1)

> **Status:** Design phase, v0.1 across all 5 docs. Not yet promoted to v1.0.
> **Owner:** Platform team (originator: repo owner).
> **Origin:** Discussion in `planning/IMPORTANT_IDEA.md` (2026-07-24, local-only). Restructured 2026-07-24 after Codex round-1 loop; post-hoc dispositions review 2026-07-25; migrated from `planning/` to this tracked path 2026-07-25.
> **Related decision docs:** `docs/decisions/SDLC_STRATEGY.md`, `docs/decisions/RELEASE_TOOLING.md`, `docs/decisions/AUTH_ARCHITECTURE.md`.

## What is Dynamic Reliability?

A design phase exploring a second doctrine for AI inside ForgeWorks: not just a *reviewer* of the engine (CodeRabbit / OWASP DC / Snyk pattern) but a first-class *evidence-generation* or *recommendation* surface **inside** the engine, consuming the same normalized event streams that the deterministic Flink jobs already consume.

The v0 scope is deliberately narrow: **shadow-mode / advisory-only**. Predictions are visible to human-facing surfaces and audit sinks; they never gate deterministic checks, block deployments, or trigger remediation. Any T3/T4 authority (autonomous action) requires a separate approved doctrine change and is out of v0 scope.

## The 5 design docs

Read in this order:

| # | Doc | One-line hook |
|---|-----|---------------|
| 1 | [`DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md`](DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md) | The upstream interface — what any source must declare to be legible to ForgeWorks (pool, vocabulary, timeframe, identity claims, segmentation, governance envelope). |
| 2 | [`PREDICTION_CONTRACT.md`](PREDICTION_CONTRACT.md) | The downstream mirror — what any consumer sees when it reads a prediction, plus per-type confidence, provenance, arbitration handoff. |
| 3 | [`VOCABULARY_DESIGN.md`](VOCABULARY_DESIGN.md) | Deep dive on the source contract's vocabulary field — quality dimensions, 6-step methodology, retention criterion, anti-patterns, model-vocab compatibility. |
| 4 | [`GROUND_TRUTH_INTERVENTION_CONTRACT.md`](GROUND_TRUTH_INTERVENTION_CONTRACT.md) | Label stream + intervention stream — what makes calibration, drift detection, and counterfactual evaluation possible. |
| 5 | [`DOCTRINE_INTERPLAY.md`](DOCTRINE_INTERPLAY.md) | Operational rules of the authority hierarchy; decision-time arbitration envelope; how predictions coexist with deterministic gates. |

### In-flight spike RFCs (v0.1 phase)

| Doc | Status | Purpose |
|-----|--------|---------|
| [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) | v0.2 draft (Codex round-2 loop applied 2026-07-26) — awaiting scoping-approval | The evidence gate for `PREDICTION_CONTRACT.md` §11 v0 → v1 graduation. Single source pair (Terraform + DataDog), single slice (webhook-gateway prod), single estimand (deploy-SLO-breach 60m — observational form per AB-033), offline replay, predeclared metrics with lower-95%-CI-bound thresholds vs. rules + logistic regression baselines. Execution blocked on AB-030 `label_schema_validator` library. |
| [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) | v0.2 draft (Codex round-1 loop applied 2026-07-28) — awaiting scoping-approval; v0.2 → v1 gated on 3 GT amendments | Shared library that enforces `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2.1/§2.2/§3/§5 rules on every label event before emission. Blocks AB-028 spike execution per that RFC's §3 Schema-conformance block. |

## How the docs fit together

```
IMPORTANT_IDEA.md (origin, local-only in planning/)
        │
        ▼
DYNAMIC_RELIABILITY_SOURCE_CONTRACT ─────────┐
        │                                    │
        ├──▶ VOCABULARY_DESIGN (§3.2 deep dive)
        │
        ▼
PREDICTION_CONTRACT  ◀── GROUND_TRUTH_INTERVENTION_CONTRACT
        │                       (labels + interventions)
        │
        ▼
DOCTRINE_INTERPLAY (arbitration; T3/T4 only, not v0-live)
```

The source and prediction contracts are structural mirrors: 6 required fields on each side, symmetric so a consumer of one is oriented for the other. The vocabulary doc goes deep on the field where design mistakes are permanent (once information is lost at vocabulary time, no downstream model can recover it). The ground-truth doc is the calibration substrate — without it, "confidence" on predictions is uninterpretable. The doctrine doc defines the arbitration envelope; it's not v0-live (v0 is advisory-only, so no arbitration fires) but the shape is drafted so T3/T4 has a target when it becomes in-scope.

## v0 doctrine — advisory-only

The authority hierarchy replaces the earlier "operator vs. reviewer" framing (which conflated *runtime placement* with *decision authority*). Every AI-involved surface belongs to exactly one tier:

| Tier | Name | v0 status |
|---|---|---|
| T1 | Evidence generation | ✅ In v0 (audit sinks, calibration logs) |
| T2 | Recommendation | ✅ In v0 (Slack digests, dashboard annotations) |
| T3 | Human-approved decision | ❌ v1+ (requires doctrine change) |
| T4 | Actuation (autonomous) | ❌ v1+ (per-class doctrine approval) |

Reasoning for the shadow-mode-only v0 posture: F10 (self-fulfilling prediction) — without shadow-mode accumulation of untreated outcomes, we cannot distinguish "the outcome that would have happened without intervention" from "the outcome that happened because of the intervention." Calibration is impossible without that separation. AB-028 (feasibility spike) has produced no evidence base yet to justify T3/T4 either.

**Estimand form under v0 — observational, not causal** *(AB-033, 2026-07-27; surfaced by Codex round-2 loop on AB-028 spike RFC, F10.)* All v0 estimands are of the observational-association form (`_association_v0` suffix in the estimand ID; e.g. `deploy_slo_breach_60m_association_v0`). They measure `P(outcome | trigger, eligibility)` in the ForgeWorks observation stream, not `P(outcome | do(trigger))`. A T2 advisory recommendation ("this deploy is at elevated observed risk") is what a GO verdict supports; T3/T4 gating or actuation requires a causal-form estimand (`_ate_v1+`) whose identification protocol is defined in `GROUND_TRUTH_INTERVENTION_CONTRACT.md` AP-6. See `PREDICTION_CONTRACT.md` §3.0 estimand-form caveat for the full argument (no randomization → no counterfactual observation → intervention-present outcomes segregated, not adjusted).

*(Note: an earlier draft cited `~/.codex/config.toml [ml]` as "binding project posture" for the advisory-only stance. That file is user-scoped Codex-agent behavior config, NOT repo-tracked ForgeWorks doctrine. Codifying "advisory-only v0" as a repo-tracked stance — in `planning/SCOPE.md`, `planning/VISION.md`, or a dedicated `ML_DOCTRINE.md` — is a v1 prerequisite; see SOURCE_CONTRACT §5 open questions.)*

## Follow-ups — AB-028 through AB-033

Codex round-1 flagged that the design corpus jumped to production-shaped graduation criteria without evidence. These experimental backlog entries file BEFORE v1 (unblocking the planning deadlock) and produce the evidence v1 needs. **The full entries live in `roadmap/AUTOMATIONS_BACKLOG.md` — repo-ignored per the "BIBLE DOCS — Internal guidelines" convention. Summaries below.**

| ID | Title | Priority | Why it exists |
|---|---|---|---|
| AB-028 | Dynamic Reliability feasibility spike | **High** | Terraform + DataDog worked estimand, one slice, offline replay, predeclared metrics vs. rules + logistic-regression baselines. **Blocks PC v0→v1 graduation.** |
| AB-029 | Runtime placement architecture spike | Medium | Compare 5 options (sibling Flink / pattern-matcher extension / insight-generator extension / batch materialized view / dedicated inference service). Runs in parallel with AB-028. |
| AB-030 | `GROUND_TRUTH_INTERVENTION_CONTRACT.md` v0 → v1 (incl. shared `label_schema_validator` library) | High | v0 drafted 2026-07-24; v1 requires live label + intervention streams, human-correction workflow, censoring emission, calibration measurement in MLflow. Library scoping RFC filed at [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) (2026-07-28) — blocks AB-028 spike execution. |
| AB-031 | `DOCTRINE_INTERPLAY.md` v0 → v1 | Medium | v0 drafted 2026-07-24. **T3/T4 consumer prereq, NOT a PC/SC v0→v1 blocker** (downgraded 2026-07-25 post-hoc dispositions review — v0 is advisory-only, arbitration doesn't fire). |
| AB-032 | MLflow production-readiness assessment | Medium | Existing `infra/mlflow/` serves tracking-server workload only. Registry governance / artifact durability / calibration serving / model promotion RBAC unverified. Blocks any calibrated-confidence predictor going to prod. |
| AB-033 | `PREDICTION_CONTRACT.md` §3.0 estimand-wording clarification (observational vs. causal) | High | Filed 2026-07-26 (Codex round-2 loop on AB-028 spike RFC, F10). Corpus-level rewrite: PC §3.0 estimand wording from causal (`causes`) to observational (`P(breach \| deploy, eligibility)`), explicit estimand ID convention introduced (`_association_v0` / `_ate_v1+`), estimand-form caveat added. Sister-doc edits in GT §8 and this README v0-doctrine section. Precedes AB-028 execution so the spike report can quote correctly-worded estimand IDs. |

## Codex round-1 audit trail

The v0.1 restructure landed in response to a 22-finding Codex critique (10 HIGH, 12 MEDIUM). All 22 findings were applied; a post-hoc dispositions review on 2026-07-25 corrected 5 over-concessions (F1 grounding, F7 magnitude, F9 rationale, F17/F19 forward-declarations).

**Full audit trail retained locally** under `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/` (repo-ignored — the `codex-review` workflow hard-codes this path for its round artifacts; keeping specific loops out of git preserves symmetry with future loops).

Contact the repo owner for access to:
- `prompt.md` — the brainstorm-scope prompt (~94KB, 4 planning docs inlined).
- `codex_response.md` — Codex's raw 22-finding response (~20KB).
- `reconciled.md` — per-finding disposition table, applied edits, sister-doc propagation verification, and the post-hoc dispositions review section.

## Graduation criteria — v0 → v1

Per each doc's §11 (or equivalent):
- All required fields implemented and populated by ≥1 shadow-mode model.
- Per-type confidence semantics implemented; cohort-level calibration measured.
- Governance envelope enforced by the audit sink.
- Lifecycle event stream live; consumed by ≥1 projection.
- `GROUND_TRUTH_INTERVENTION_CONTRACT.md` at v0 (AB-030).
- AB-028 feasibility spike delivered model-lift-over-baseline evidence.
- MLflow production-readiness assessment complete (AB-032).
- Operating model per production predictor attested.
- Circuit-breaker mechanism exercised in a controlled drill.

**v1 does NOT require:** any T3/T4 consumer to exist. Those are separate doctrine changes, each earning their own AB-NNN entries under a future v1.x actuation-doctrine RFC. `DOCTRINE_INTERPLAY.md` reaching v1 (AB-031) is a T3/T4-consumer prereq, not a v0→v1 blocker for the other four docs.

## Provenance

- **2026-07-24:** All 5 docs drafted at v0 (SC, VOC, PC as full v0; GROUND_TRUTH, DOCTRINE_INTERPLAY as new siblings). Codex round-1 loop critique returned same day; 22 findings applied → v0.1 restructure across all 5 docs. AB-028..032 filed.
- **2026-07-25:** Post-hoc dispositions review corrected 5 over-concessions from the round-1 application; corrections landed in-place in each doc (`Why shadow-mode` blocks, forward-declared caveats, downgraded blocking statuses).
- **2026-07-25:** Design corpus migrated from `planning/` (repo-ignored) to `docs/decisions/dynamic-reliability/` (tracked). Filenames dropped `_v0` suffix to align with existing `docs/decisions/` convention. This README written as index + AB-028..032 summary + audit-trail pointer.
- **2026-07-26:** [`AB-028_FEASIBILITY_SPIKE.md`](AB-028_FEASIBILITY_SPIKE.md) scoping RFC drafted at v0.1 — the load-bearing v0 → v1 evidence gate for the corpus. Awaiting scoping-approval meeting to lock predeclared thresholds before spike execution begins.
- **2026-07-26:** AB-028 spike RFC bumped to v0.2. Codex round-2 critique loop (audit trail at `research/feedback_loops/dynamic-reliability-AB-028_FEASIBILITY_SPIKE/20260726T082924Z/` — local-only) returned `needs-revision` with 13 HIGH / 7 MEDIUM findings on evidence integrity, calibration validity, baseline fairness, statistical power gating, causal-vs-observational estimand wording, and cost-weighted decision framework. Nineteen of twenty findings applied in-place; F19 delegated to AB-030 (shared `label_schema_validator` library); F10 filed as AB-033 for the corpus-level PC §3.0 estimand-wording correction. Post-application over-concession review scheduled.
- **2026-07-27 (AB-033):** PC §3.0 worked-estimand rewrite — causal wording ("deployment *causes* SLO breach") replaced with observational form (`P(breach | deploy, eligibility)`, ID `deploy_slo_breach_60m_association_v0`). Explicit estimand ID convention introduced. Estimand-form caveat added to PC §3.0. Sister-doc edits: GT §8 `estimand_id` aligned to the v0 association form; this README v0-doctrine section carries the observational-form pointer + AB-033 row added to the follow-ups table. Origin: Codex round-2 critique loop on AB-028 spike RFC (F10, 2026-07-26).
- **2026-07-28:** [`AB-030_LABEL_SCHEMA_VALIDATOR.md`](AB-030_LABEL_SCHEMA_VALIDATOR.md) scoping RFC drafted at v0.1 — shared library for `forge.events.ground_truth.v1` conformance. Filed as the F19 delegation from Codex round-2 loop on AB-028 spike RFC; scopes the AB-028-blocking library specifically (distinct from AB-030's broader GT v0 → v1 lifecycle tracked in the backlog entry). GT §11 Related documents updated with pointer. In-flight-spike RFCs table added to this README.
