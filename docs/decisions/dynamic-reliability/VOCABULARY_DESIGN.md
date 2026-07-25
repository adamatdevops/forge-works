# Vocabulary Design — How to Build the Alphabet Your Models Reason Over (v0.1)

> **Status:** Design stub (v0.1).
> **Origin:** Deep dive on `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` §3.2, requested in the design-phase discussion.
> **Location note:** Migrated 2026-07-25 from `planning/VOCABULARY_DESIGN.md` to this tracked path — see `docs/decisions/dynamic-reliability/README.md` for the corpus index.
> **Lifecycle note:** Same as sibling design docs — deletable pointer `planning/IMPORTANT_IDEA.md` closes when this doc + the source contract graduate to v1.0. This doc itself lives until its content is absorbed into an eventual `docs/decisions/DYNAMIC_RELIABILITY.md` consolidated spec.
> **Scope:** what a vocabulary *is*, why it's load-bearing, how to design one from scratch, granularity trade-offs, patterns per source shape, evolution rules, anti-patterns, worked example. Not a wire-format spec, not a runtime-normalization spec — those live in their own siblings.
> **v0.1 provenance:** Revised 2026-07-24 after Codex round-1 loop; post-hoc dispositions review 2026-07-25 (reconciled.md retained locally under `research/feedback_loops/planning-dynamic_reliability_design/20260724T093159Z/` per the codex-review workflow — that path is repo-ignored by design). Key changes: §2(c) severity/outcome demoted to presentation metadata (F9), §4 step 4 composite retention replaces frequency threshold (F6), §7 evolution table adds model-vocab compat contract (F15), §8 AP-7 expanded to operational ownership (F21), §9 worked example updated for namespaced tokens.

---

## 1. What is a vocabulary?

**Rationale:** Models can't reason over unstructured, unbounded input. They reason over tokens drawn from a known finite set. The vocabulary is that set. Everything downstream — feature engineering, model architecture, prediction quality, cross-source correlation — is downstream of vocabulary choices.

**Context:** In the source contract, vocabulary is one of six fields (§3.2). But it's not one-sixth of the design work — it's closer to half. The other five fields become largely mechanical once the vocabulary is right; if the vocabulary is wrong, nothing else can compensate.

**Simplification:** A vocabulary is the alphabet your models get to work with.

**Analogy:** A camera's sensor. The sensor decides which wavelengths get captured and at what resolution. Everything downstream — image processing, ML analysis, human viewing — is fundamentally bounded by the sensor's choices. A bad sensor cannot be rescued by better software. Vocabulary is the sensor for a source.

---

## 2. Why vocabulary is the load-bearing decision

Three reasons, in order of severity:

**(a) Downstream irreversibility.** If your vocabulary conflates `terraform.apply_failed` and `terraform.apply_partial` into a single token `terraform.apply_not_success`, no downstream model can ever tell them apart. Information lost at the interface layer cannot be recovered downstream. Every ambiguity in the vocabulary is a permanent ceiling on prediction quality.

**(b) Model-size inheritance.** The whole "small model wins on structured input" thesis (source contract §Q3) rests on the assumption that the structuring is well done. A vocabulary with clean signal-to-noise ratio lets a tiny model win. A vocabulary that's noisy, ambiguous, or under-informative forces bigger models to compensate — undoing the efficiency gain that motivated the design in the first place.

**(c) Domain-semantic preservation** *(v0.1, revised per Codex F9).* The original v0 claimed a global 5-level severity scale plus canonical outcome-label enum would "make cross-source joins work." Codex flagged this as a design failure: `terraform.apply.failed` (Terraform) and `datadog.slo.burning` (DataDog) both mapping to severity `high` DOESN'T mean the reliability model should reason about them the same way — they describe fundamentally different events with different consequences, base rates, and action classes. Equating them by shared label manufactures false cross-source correlations.

**The v0.1 doctrine:** vocabulary tokens are **namespaced by source** (`terraform.*`, `datadog.*`) and cross-source features become **task-specific and learned**, not equated by shared labels. Global severity remains but is **presentation metadata only** — used for human-facing surfaces (Slack digests, dashboards) and never as a training signal or a join key. Consumers reason about domain-semantic differences; the vocabulary preserves them instead of flattening them.

**Corollary:** vocabulary design is a *design-phase* activity, not a *build-phase* one. Building a bad vocabulary into code is cheap; getting it out again is expensive because every downstream consumer has assumed the shape.

---

## 3. The four quality dimensions

Good vocabularies score well on all four; the four are in tension.

| Dimension | Question it answers | Failure mode |
|---|---|---|
| **Fidelity** | Does each token carry information a model can use? | Semantically empty tokens (a token that fires 99% of the time is signal-free) |
| **Discriminability** | Are distinct real-world events distinct tokens? | Meaningful events collapsed into the same token (`terraform.apply_failed` = `terraform.apply_partial`) |
| **Stability** | Do tokens keep their meaning over time? | Silent semantic drift (a token that meant one thing in Q1, something else in Q4, same name) |
| **Compactness** | Is the vocabulary as small as possible while preserving the above? | Bloat causes sparsity (most tokens have too few observations to learn from) |

**The tension:** discriminability pushes toward more tokens; compactness pushes toward fewer; fidelity constrains both; stability is orthogonal but constrains how the other three can evolve.

**How to resolve tension:** always prefer *fidelity* → *discriminability* → *stability* → *compactness*, in that order. It is easier to shrink a large-but-faithful vocabulary later than to enlarge a small-but-lossy one (see §7 evolution rules).

---

## 4. The 6-step design methodology

Applied when onboarding a new source or redesigning an existing one.

### Step 1 — Survey the source

Pull 30 days of raw data. Understand what the source *actually* emits — not what its docs claim. Sources under-document and over-produce; the delta between the two is where vocabulary design lives.

**Deliverable:** a raw-event frequency histogram covering ≥30 days.

### Step 2 — Enumerate raw event types

List every distinct event category, sorted by frequency. Include the long tail — you need to see it before you decide to prune it.

**Deliverable:** flat list of distinct event categories with observed counts.

### Step 3 — Cluster by causal similarity

Group events that would trigger the same downstream reliability response. `terraform.plan_started` and `terraform.plan_completed` cluster into a "plan lifecycle" bucket (same downstream: log it, don't act). `terraform.apply_failed` and `terraform.apply_partial` do NOT cluster — different downstream (one triggers a full rollback investigation, the other a targeted resource check).

**Heuristic:** if two events would produce identical downstream actions across all consumers, they should collapse to one token. Otherwise, keep them distinct.

**Deliverable:** clusters with candidate token names + rationale. All names namespaced by source (`<source>.<token>`).

### Step 4 — Composite retention (was: prune by frequency) — v0.1 change per Codex F6

**Original v0 rule (retired):** anything below ~1% frequency goes into `unknown_<type>`. Codex correctly flagged that this discards precisely the rare-but-high-cost events that security, incident, chaos, and DR predictors must preserve. Decision theory says retention depends on **information value × error cost**, not frequency alone.

**v0.1 composite retention criterion.** A token is retained if the composite score `prevalence × severity × predictive_value × action_difference × error_cost_asymmetry` clears a per-task threshold. Concretely:

- **prevalence** — observed frequency in the survey window (the old rule; now one input, not the rule).
- **severity** — the presentation-severity anchor (from §5 canonical mapping); used only to weight, not to determine outcome equivalence.
- **predictive_value** — historical correlation with downstream reliability outcomes (learned from the pilot).
- **action_difference** — do consumers act differently on this token vs. its coarser sibling? If yes, retain distinct.
- **error_cost_asymmetry** — cost of missing this token vs. cost of over-firing on it. Security-incident-class tokens have vastly asymmetric costs.

**Practical guidance:**
- **Common tokens** (prevalence >1%) — retain by default unless action_difference = 0.
- **Rare tokens** (prevalence 0.1-1%) — retain if any of {severity ≥ high, predictive_value > baseline, error_cost_asymmetry > 10:1}.
- **Very rare tokens** (prevalence <0.1%) — retain only if error_cost_asymmetry is catastrophic (security incident class, DR event, data-loss class). Otherwise route to `<source>.unknown_<type>`.
- **Alternative treatments for retained rare tokens:** hierarchical features (roll up to a category token that fires more often, retain the specific token as a sub-flag), synthetic augmentation, or dedicated anomaly-detection treatment outside the classifier.

**Deliverable:** the token set with per-token justification citing the composite criterion.

### Step 5 — Define the canonical mapping *(v0.1: presentation-only semantics)*

Every token maps to:
- an entry in the canonical severity scale (`info` / `low` / `medium` / `high` / `critical`) — **presentation metadata only**, per §2(c). Used for human-facing surfaces; NOT a training signal, NOT a join key.
- if applicable, an outcome label. **Namespaced by source** (`terraform.apply.success`, `datadog.slo.recovered`) — the outcome enum is per-source, resolved through `GROUND_TRUTH_INTERVENTION_CONTRACT_v0.md` for cross-source semantics.

The mapping table is a *presentation contract*, not a *reasoning contract*. Consumers that need to reason about outcomes read the namespaced token, not the severity label.

**Deliverable:** the mapping table + explicit note that severity does not equate tokens across sources.

### Step 6 — Pilot with a downstream consumer

Feed the vocabulary into a stub model, a rule-based downstream job, or even a spreadsheet. Discover what it *can't* express. Every "I need to ask a question this vocabulary can't answer" is a v0.1 punch-list item.

**Deliverable:** v0 vocabulary + a written punch list of expressiveness gaps discovered during the pilot.

**Do not skip step 6.** Vocabularies that never touch a consumer are almost always wrong in ways that don't surface until much later, when correction is expensive. The `AB-028` feasibility spike is where step 6 lives operationally.

---

## 5. Granularity trade-offs — the split/merge spectrum

Three hypothetical vocabularies for the same Terraform events:

| Design | Token count | Discriminability | Sparsity | Verdict |
|---|---|---|---|---|
| **Ultra-fine** | ~300 | Every resource × state × region distinct | Catastrophic (most tokens have <10 obs/week) | ❌ Unusable — nothing to train on |
| **Ultra-coarse** | 5 | `plan`, `apply`, `destroy`, `drift`, `error` | Zero (every token dense) | ❌ Blind — can't distinguish an S3 destroy from an EC2 destroy |
| **Well-designed** | ~30 | Event lifecycle × outcome, resource type kept as separate field | Dense on most tokens | ✅ Works |

**Heuristic thresholds** *(v0.1: subsumed by §4 step 4 composite criterion, but useful as first-pass filter)*:
- A token that fires >1% of the time in the pilot data is probably worth keeping distinct.
- A token that fires between 0.1% and 1% is a *composite-criterion decision* per §4 step 4.
- A token that fires <0.1% goes into `<source>.unknown_<type>` **unless** error_cost_asymmetry is catastrophic (see §4 step 4 exceptions for security/DR/data-loss classes).

**The composition trap:** when tempted to add tokens like `terraform.apply_failed_aws_instance_us_east_1`, stop. That's *four independent axes* (event, outcome, resource type, region) collapsed into one token. Keep them as separate structured fields on the event; let the downstream model compose them. Vocabulary tokens are for the *primary axis of the event*; secondary axes live in fields.

**The rule:** the vocabulary answers *what kind of event happened*. Fields answer *what it happened to, when, where, by whom*. Don't mix them.

---

## 6. Source-shape patterns

Sources come in three canonical shapes. Each has a different vocabulary design pattern. Recognize the shape first; the vocabulary design follows.

### 6.1 Event-log-shaped

**Examples:** Terraform, GitHub Actions, Jenkins, PagerDuty, ArgoCD deployment events.
**Pattern:** discrete events with clear lifecycles (started → completed / failed / cancelled).
**Vocabulary shape:** `<source>.<lifecycle-phase>_<outcome>` (e.g., `terraform.apply_completed`, `terraform.apply_failed`, `github.workflow_run_cancelled`).
**Typical size:** 10-50 tokens.
**Key design decision:** how much resource-type granularity to bake into the token vs. defer to a separate field. Default: keep resource type as a field, not in the token, unless downstream consumers demonstrably need to distinguish.

### 6.2 State-snapshot-shaped

**Examples:** Kubernetes resource states, LaunchDarkly flag states, ArgoCD sync-status states.
**Pattern:** periodic snapshots of "what is currently true." No natural lifecycle events; state *transitions* must be computed by diffing consecutive snapshots.
**Vocabulary shape:** state tokens (`argocd.synced`, `argocd.out_of_sync`) + a smaller set of transition tokens (`argocd.transitioned_to_synced`, `argocd.transitioned_to_degraded`).
**Typical size:** 5-20 state tokens + a similar count of transition tokens.
**Key design decision:** what counts as a transition. Every diff — including transient blips — or only diffs that persist beyond a debounce window (e.g., 30s)? Default: debounce.

### 6.3 Metric-shaped

**Examples:** Prometheus, DataDog metrics, latency histograms, error-rate gauges.
**Pattern:** continuous numeric streams. There are no natural tokens — you have to invent them by bucketing.
**Vocabulary shape:** bucket names (`datadog.p99_over_slo`, `prometheus.error_rate_above_baseline`) + threshold-crossing events.
**Typical size:** 10-30 tokens, driven by SLO structure.
**Key design decision:** bucket boundaries. These are arbitrary numeric thresholds masquerading as data — pick them badly and the vocabulary encodes the wrong story. Default: derive buckets from documented SLOs. Never invent thresholds from vibes.

### 6.4 Hybrid

Some sources (Sentry — events + aggregate error rates; GitHub — events + PR/repo state; Kubernetes — events + resource states) blend two or three shapes. Vocabulary is the union of the per-shape vocabularies with careful namespacing.

---

## 7. Evolution rules — changing a vocabulary without breaking downstream

Vocabularies change. The rules for changing them safely — and **the model-vocabulary compatibility contract** (v0.1 addition per Codex F15):

| Change | Rule | Deployed-model requirement | Version bump |
|---|---|---|---|
| **Add a token** | Safe *at the source*. Downstream models with `compatibility_range` covering the new vocab version handle it; models outside the range MUST quarantine/fallback-route the unknown token, not silently coerce. Requires conformance tests, dual encoding during migration, shadow retraining before the new vocab is eligible for production inference. | Model versions in the compatibility range OR quarantine behavior verified. | Minor (v0.1 → v0.2) |
| **Deprecate a token** | Two-step: mark deprecated (still emitted, downstream warned), wait ≥N weeks, then stop emitting. Never remove without a deprecation window. | Consumers subscribed to the deprecated token must acknowledge migration before removal. | Minor on deprecate, major on removal |
| **Split** (one token → many) | Emit both old and new tokens in parallel for a deprecation window. Downstream migrates. Then drop old. | Same. | Minor on split, major on old-token removal |
| **Merge** (many → one) | Same pattern. Emit both, migrate consumers, drop old. | Same. | Minor on merge, major on old-token removal |
| **Rename** | ❌ **Never rename.** Deprecate the old token + add a new one with the new name. Renaming silently corrupts historical data. | n/a | n/a |
| **Semantic drift** (token starts meaning something different) | This is a *bug*, not an evolution. Fix by deprecating the drifted token + adding a new one. Never let semantics drift under the same name. | n/a | n/a — treat as bug |

**v0.1 correction to "Add a token: always safe":** the original claim was that adding is always safe because downstream sees the new token and treats it as unknown until retrained. Codex correctly flagged (F15) that this is only true if downstream *has explicit unknown-token behavior*. A deployed model with a fixed feature encoder can crash, silently degrade, or produce miscalibrated predictions when it hits an unseen category. So: adding a token is safe **only when the model-vocab compatibility contract is honored** — declared `compatibility_range`, tested `on_unknown_token` behavior (quarantine, not silent coerce), and shadow retraining before the new vocab reaches production inference.

**The invariant:** every change is *additive during the migration window*, *subtractive only after consumers have migrated*. Same doctrine as safe database schema migrations.

**Deprecation window:** default 4 weeks. Longer if downstream consumers are known to have slow retraining cycles.

**Provenance:** every emitted event carries the vocabulary version it was produced under. Consumers that see an older version know they're looking at historical data and can decide whether to accept, coerce, or reject.

---

## 8. Anti-patterns — the specific failure modes

Named so they can be pointed at in review.

**AP-1: The "unknown" dumping ground.** Everything hard-to-classify goes into `unknown_*`. Over time `unknown_*` becomes the modal token. The vocabulary has failed silently — it's technically valid, semantically empty. **Detection:** if `unknown_*` is >5% of traffic, the vocabulary needs redesign.

**AP-2: Free-text-as-token.** Using the source's `message` or `description` field as a token. Unbounded cardinality, zero discriminability, every message unique = every message meaningless. **Fix:** extract the structural fields the message *encodes* (severity, event type, resource), not the message itself.

**AP-3: Timestamp-in-token.** `error_2026_q3` is a versioned token pretending to be a semantic one. Time is a separate dimension (source-contract Timeframe field), never a vocabulary token. **Fix:** tag the event with a timestamp field; keep the vocabulary time-agnostic.

**AP-4: User-input-in-token.** Anything the source's *users* can customize — custom event names, custom tags, arbitrary labels — is not a stable vocabulary. Two customers of the same source will produce non-comparable data. **Fix:** map user input into structural categories that the vocabulary defines; discard the free text or move it to a field.

**AP-5: Cardinality explosion via composition.** `apply_failed_aws_instance_us_east_1` combines four independent axes into one token. Vocabulary size grows multiplicatively; sparsity kills the model. **Fix:** keep axes as separate structured fields. Vocabulary tokens are for the *primary event axis only*.

**AP-6: Untagged vocabulary version.** Vocabulary changes emitted without a version field. When you evolve, historical data is indistinguishable from current data. Every migration silently corrupts backfill. **Fix:** every event carries `vocabulary_version: <semver>`. Non-negotiable.

**AP-7: Vocabulary owner ≠ operational owner** *(v0.1 expansion per Codex F21).* Naming a vocabulary owner is table stakes; it does NOT establish operational ownership for model failures, data incidents, drift alerts, or inference outages. A source with `owner: platform-team` in its contract can still have no accountable model owner, no data owner, no service owner, no on-call path, no SLOs, no rollback authority, no retraining cadence, no incident runbook.

The **operating model per predictor** (v0.1) is a separate required attestation, distinct from vocabulary ownership:
- **Accountable model owner** — reviews model changes, signs off on retraining, owns model risk.
- **Accountable data owner** — owns data quality upstream, responds to drift alerts.
- **Accountable service owner** — owns runtime SLOs, availability, capacity.
- **On-call path** — how do people learn the prediction pipeline is degraded? Whose pager fires?
- **SLOs** — freshness, latency, availability, calibration error budget.
- **Rollback authority** — who can pull a model out of production, and by what mechanism?
- **Retraining cadence** — declared, staffed, monitored.
- **Incident runbooks** — how to respond to specific failure modes (unknown-token spike, calibration drift, source silence).
- **No-production-if-unstaffed rule** — if any of the above roles is unstaffed, the predictor does not run in production. Full stop.

**Fix for AP-7:** every source contract carries a vocabulary owner (light-weight); every *predictor* consuming that vocabulary carries an operating-model attestation (heavy). PRs touching the vocabulary require vocabulary-owner approval; PRs promoting a predictor to production require operating-model verification.

**AP-8: Copying the source's own vocabulary verbatim.** Just because DataDog emits 47 monitor state names doesn't mean the ForgeWorks vocabulary should have 47 tokens. The source's vocabulary was designed for the source's users, not for a reliability model. Curate. **Fix:** always apply the 6-step methodology; never accept a source's raw token set as-is.

---

## 9. Worked walkthrough — DataDog vocabulary (runtime pool, v0.1)

Applying the 6-step methodology to DataDog. Chosen deliberately because it's a *different shape* from Terraform — this stress-tests both the source contract and the methodology.

**Step 1 — Survey.** DataDog is a *hybrid-shaped* source. It emits (a) time-series metrics (metric-shaped), (b) monitor state changes (state-snapshot-shaped, transitions matter more than states), (c) discrete events like deploy markers (event-log-shaped). Three sub-shapes in one source — apply per-shape methodology, then union.

**Step 2 — Enumerate raw event types.**
- Monitor states: `ok`, `warn`, `alert`, `no_data`, `skipped` (5 values).
- Monitor transitions: 5 × 4 = 20 raw transitions (any → any).
- Discrete events: `deploy_marker`, `alert_ack`, `mute`, `unmute`, `note_added`, `alert_recovered`, `custom_event`.
- Metrics: continuous — no natural tokens; must bucket.

**Step 3 — Cluster by causal similarity.**
- Monitor transitions cluster by direction: `datadog.transition_worsened` vs. `datadog.transition_improved`. But `datadog.entered_alert` and `datadog.entered_warn` do *not* cluster — different downstream (alert triggers paging; warn triggers logging). Keep those distinct.
- Discrete events: `datadog.deploy_marker` is critical (correlation anchor for cross-source joins). `alert_ack` / `mute` / `unmute` / `note_added` cluster into `datadog.operator_action` — they're metadata.
- Metrics: bucket via SLO structure — `datadog.slo_met`, `datadog.slo_at_risk`, `datadog.slo_burning`, `datadog.slo_burned`.

**Step 4 — Composite retention.** `skipped` monitor state is rare (<0.1%) but not high-error-cost — route to `datadog.unknown_monitor_state`. `custom_event` is user-defined (AP-4) — either route to `operator_action` if actionable or drop. `datadog.alert_ack` fires at moderate frequency but has **near-zero predictive_value** for future reliability — collapse into `operator_action` per composite criterion even though prevalence would suggest keeping distinct.

**Step 5 — Canonical mapping (presentation only, per v0.1 §5):**

| Token | Presentation severity | Namespaced outcome |
|---|---|---|
| `datadog.entered_alert` | critical | `datadog.runtime.regressed` |
| `datadog.entered_warn` | medium | `datadog.runtime.at_risk` |
| `datadog.transition_improved` | low | `datadog.runtime.recovering` |
| `datadog.slo_burning` | high | `datadog.runtime.regressed` |
| `datadog.slo_burned` | critical | `datadog.runtime.regressed` |
| `datadog.slo_at_risk` | medium | `datadog.runtime.at_risk` |
| `datadog.slo_met` | info | (none) |
| `datadog.deploy_marker` | info | (none — but critical cross-ref via identity claims) |
| `datadog.operator_action` | info | (none) |
| `datadog.unknown_monitor_state` | info | (none) |

**Note (v0.1):** severity column here is presentation only. `datadog.entered_alert` at severity `critical` is NOT equivalent to `terraform.destroy_started` at severity `critical`. Different domains, different consequences. The reliability model sees the namespaced tokens directly.

**Step 6 — Pilot.** Feed 30 days of DataDog data through this vocabulary into a stub reliability scorer (formal home: AB-028 feasibility spike). Punch list from expected pilot: verify `datadog.deploy_marker` events carry a `git.commit_id` identity claim (per source-contract §3.4) for cross-referencing to the deployment source. If not, that's the v0.2 fix.

**Stress-test result:** the v0.1 contract shape holds. DataDog required namespaced tokens (which v0.1 mandates), presentation-only severity (v0.1 §2c), and one composite-retention decision that would have been mis-made by v0's frequency threshold (`alert_ack` dropped despite moderate frequency, because predictive_value is near zero).

---

## 10. When is a vocabulary "done"?

Never fully. But the graduation criteria to move from v0 → v1:

- [ ] Pilot with ≥1 downstream consumer completed (§4 step 6; formal home: AB-028)
- [ ] `unknown_*` traffic <5% of total (AP-1 threshold)
- [ ] Canonical severity mapping complete (presentation only)
- [ ] Namespaced outcome labels defined for supervised-training tokens
- [ ] Version field present on emitted events (AP-6)
- [ ] Model-vocab compatibility contract declared and tested (§7, per F15)
- [ ] Vocabulary owner named in the source contract (AP-7)
- [ ] Operating model per predictor attested (AP-7, v0.1 addition)
- [ ] Deprecation window policy documented for this source (§7)
- [ ] Stress-tested against ≥1 different-shaped source's vocabulary for cross-source consistency

A vocabulary that meets all ten is v1-ready. Missing any of them means design work remains.

---

## 11. Open questions

- [ ] **Automated drift detection threshold** — the source contract §3.2 says "detect unknown tokens and emit a vocabulary-drift signal." What counts as drift worth surfacing? Sustained ≥1% new-unknown for ≥7 days? Instantaneous spike? Both?
- [ ] **Vocabulary owner enforcement** — is this a CI check on source-contract PRs, a CODEOWNERS rule, or both?
- [ ] **Operating model attestation mechanism** *(v0.1)* — is the operating model (§8 AP-7) tracked in-repo (a YAML file per predictor), out-of-repo (Confluence / wiki), both? What enforces the no-production-if-unstaffed rule at deployment time?
- [ ] **Metric bucketing methodology across sources** — every metric-shaped source needs bucket boundaries. Is there a general methodology (percentile-based? SLO-derived? error-budget-driven?) or is this per-source?
- [ ] **Vocabulary version placement in the wire format** — top-level field on every event, or embedded in a `_meta` block? Deferred to `WIRE_PROTOCOL.md` but affects vocabulary evolution mechanics.
- [ ] **Historical-data coercion policy** — when the vocabulary evolves, do we re-emit historical events under the new vocabulary (expensive, correct) or leave them tagged with the old version (cheap, forces model to handle multiple versions)? Both are defensible.
- [ ] **Rare-event token treatment** *(v0.1)* — the composite retention criterion (§4 step 4) admits security-class and DR-class tokens even at very low prevalence. Are these best handled as first-class vocabulary tokens, or as hierarchical rollups, or as dedicated anomaly-detection streams outside the primary classifier?

---

## 12. Related documents

- `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` *(v0.1)* — parent doc; this is the deep dive on §3.2. v0.1 restructure includes namespaced identity claims (§3.4), governance envelope (§3.6), authority-hierarchy doctrine (§2).
- `planning/IMPORTANT_IDEA.md` — origin discussion (ephemeral; deletable when design phase closes).
- `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md` *(v0.1)* — downstream mirror; consumer side. Inherits v0.1 evolution rules from this doc.
- `docs/decisions/dynamic-reliability/GROUND_TRUTH_INTERVENTION_CONTRACT.md` *(drafted v0)* — sibling. Namespaced outcome labels resolve through this doc's semantics.
- `docs/decisions/dynamic-reliability/DOCTRINE_INTERPLAY.md` *(drafted v0)* — sibling. Authority hierarchy operational rules; arbitration envelope.
- `planning/WIRE_PROTOCOL.md` — JSON vs. Avro vs. Protobuf, schema evolution, versioning. Not yet drafted; affects vocabulary evolution mechanics (§11).

---

## 13. Iteration protocol

Same as the source contract:
- Substantive changes bump `v0` → `v0.1` → `v0.2` → …
- Graduates to v1.0 when the checklist in §10 is met AND at least one non-DataDog metric-shaped source has been fed through the methodology successfully.
- Experimental AB-NNN entries file before v1 (v0.1 alignment with source contract §6). AB-028 (feasibility spike) is where §4 step 6 lives operationally.
- On v1.0, this doc's content moves to `docs/decisions/DYNAMIC_RELIABILITY.md` and this file can be deleted along with `IMPORTANT_IDEA.md`.
