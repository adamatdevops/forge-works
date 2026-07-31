# AB-028 Feasibility Spike — Scoping-Approval Meeting Agenda

> **Status:** Pre-meeting draft (2026-07-27). Companion to `AB-028_FEASIBILITY_SPIKE.md` v0.2. Superseded by the RFC's own §6 numbers + meeting-outcome attribution once decisions land (this doc closes; the RFC becomes the source of truth).
> **Purpose:** walk-in agenda for the AB-028 scoping-approval meeting. Every item is a decision the meeting must produce; each is scoped so the RFC can be edited in-place with the locked numbers + meeting date.
> **Owner:** meeting chair (TBD). Recorder: TBD.
> **Pre-read:** `AB-028_FEASIBILITY_SPIKE.md` (v0.2), `PREDICTION_CONTRACT.md` §3.0, `GROUND_TRUTH_INTERVENTION_CONTRACT.md` §2, `SC §4` (source contract vocabulary), `research/feedback_loops/dynamic-reliability-AB-028_FEASIBILITY_SPIKE/20260726T082924Z/reconciled.md` §"Post-application over-concession review" (repo-ignored — request separately if not on-machine).
> **Straw-doc:** [`AB-028_SCOPING_APPROVAL_REVIEWER_MEMO.md`](AB-028_SCOPING_APPROVAL_REVIEWER_MEMO.md) — one reviewer's recommendation per §B/§C item. Read alongside this agenda so the meeting has a perspective to challenge rather than a blank page. Explicitly not a decision doc; the memo's own §E flags where the reviewer lacks domain input (§B2 SRE, §B4 real metadata, §C2 operating-model owner).

---

## 0. Meeting outcome — what "approved" means

The meeting produces one of three outcomes, recorded verbatim at the top of `AB-028_FEASIBILITY_SPIKE.md` §11 provenance:

- **APPROVED** — every §A / §B / §C decision below has a locked answer; the RFC is edited to reflect them; spike execution may begin as soon as the pre-scoping metadata-window pass (RFC §4.4) completes AND AB-030 `label_schema_validator` ships AND AB-033 lands.
- **APPROVED WITH DEFERRALS** — the meeting locks the non-deferrable items (§A + §B); one or more §C items get a documented "return to this meeting in ≤ 2 weeks" clock. Execution does not begin until the deferred items land.
- **NOT APPROVED** — the RFC needs a material revision before another scoping-approval attempt. The meeting produces the revision brief (what changed the answer, what a v0.3 must show).

**Rubber-stamp guard:** every "proposed" number the RFC ships with was authored by one person (the RFC drafter). The meeting's job is to challenge them, not confirm them. The three OCs in §C are the specific spots where round-2's own over-concession review flagged authorial defaults — those items require an explicit answer, not silence.

---

## §A. Blocking prerequisites — verify before opening decision items

If any of the below is red, the meeting either resolves it inline (small) or reschedules (large). Not decision items — status checks.

| # | Item | Owner-check | Blocking? |
|---|------|-------------|-----------|
| A1 | AB-033 (`PREDICTION_CONTRACT.md` §3.0 observational-form estimand) has landed on `main` | Confirm PR #16 merged; RFC §3 caveat still references the observational form. | Yes — spike report cannot quote correctly-worded estimand IDs otherwise. |
| A2 | AB-030 `label_schema_validator` library scoping RFC drafted (execution can wait; scoping cannot) | Confirm AB-030 has at minimum a contract sketch (what fields, what validation, where it lives). | Yes for start-of-execution, not for scoping-approval outcome. Meeting notes the AB-030 status; approval means "spike may begin as soon as AB-030 ships." |
| A3 | Pre-scoping metadata window (RFC §4.4) is ready to run | Confirm 30-day metadata pull scripts exist for `webhook-gateway prod`; MLflow experiment ID reserved; write-lock on the modeling window in place so no one inspects it early. | Yes — the meeting locks thresholds informed by the metadata-window pass, so the pass must be runnable immediately post-meeting. |
| A4 | Spike execution owner assigned | Confirm one named engineer accepts §7 deliverables + §9 timeline. | Yes — an unowned spike doesn't ship. |

---

## §B. Non-negotiable lock items — the four RFC-mandated decisions

These are the four items RFC §2.1 marks "must be locked at scoping-approval." Each has a **proposal** (from the RFC), a **decision question** for the meeting, and **options** with trade-offs. The meeting picks one option per item (or produces its own).

### B1. Threshold lock — §6.1 primary metrics (M1 AUCPR, M2 ECE, M3 Brier)

**RFC proposal (v0.2 §6.1):**
- **M1 AUCPR:** lower 95% CI bound of (model AP − max(rules AP, LR AP)) ≥ **0.05**; AND model AP ≥ **observed_test_prevalence + 0.10** (normalized 10pp lift over prevalence).
- **M2 ECE:** model ECE ≤ **0.10**; AND lower 95% CI bound of (rules ECE − model ECE) > 0 AND (LR ECE − model ECE) > 0. Binning: equal-mass, 10 bins, min 5 obs/bin.
- **M3 Brier:** model Brier < base_rate × (1 − base_rate); AND per-baseline strict inequality lower-CI-bound.

**Decision question:** are these three thresholds the GO/no-GO bar the meeting is willing to defend post-hoc?

**Options:**
1. **Accept as-proposed** — RFC v0.2 numbers stand.
2. **Amend margins** — e.g., raise AUCPR margin to 0.10 (harder GO), or lower to 0.03 (softer GO); adjust ECE ceiling; adjust Brier requirements.
3. **Substitute a single primary comparison** — RFC §6 escape valve: M1 primary, M2/M3/C1 diagnostic. Fires if the pre-scoping power analysis shows Bonferroni multiplicity makes any 4-way bar unfalsifiable.

**Test to apply:** "if the model narrowly passes this bar, do we have the conviction to promote PC to v1?" If no, the bar is too soft. If the answer is "we'd want more evidence before promotion regardless of the bar," the bar is too hard for a feasibility spike (which is about *lifting over baselines*, not *proving production readiness*).

### B2. Rule list lock — §5.1 rules baseline

**RFC proposal (v0.2 §5.1):** 5 rules covering deploy-hour heuristics, plan-diff-size threshold (Rule 5, `P90(plan_diff_size)` from training window), rollback-recent, error-rate-recent, cross-service-dependency.

**Decision question:** is the 5-rule list the honest deterministic baseline a rules-first team would actually deploy, or is it a strawman?

**Options:**
1. **Accept as-proposed** — 5 rules stand; scoping-approval attests to fair-baseline test.
2. **Add rules** — the meeting identifies 1–3 additional rules a rules-first team would obviously include (e.g., "deploy on Friday afternoon" if that's actually observed).
3. **Remove rules** — the meeting drops rules that don't reflect the team's actual deterministic mental model.

**Test to apply:** "if the model beats these 5 rules, will a rules-advocate say 'you missed the good rules'?" A rules baseline the team's own SRE would call weak fails the fair-baseline standard and invalidates the lift-over-baseline evidence.

### B3. Feature list lock — §4.3 feature construction

**RFC proposal (v0.2 §4.3):** the feature list is frozen at scoping-approval; adding features mid-spike invalidates test cohort; outcome-informed removal invalidates test cohort. Removals only permitted for schema-drift / availability failures documented before label opening.

**Decision question:** is the ~N-feature list (as enumerated in RFC §4.3) complete for the pre-scoping metadata inspection to test, or does the meeting see obvious gaps?

**Options:**
1. **Accept feature list as-proposed** — RFC §4.3 stands.
2. **Add features** — the meeting names 1–5 additional feature groups (each with source vocabulary attribution per SC §4).
3. **Explicitly exclude features** — the meeting names features to omit and documents why (e.g., available-but-noisy-signal, leakage risk).

**Test to apply:** every feature must trace to a source contract vocabulary entry. Ad-hoc features (not from SC vocabulary) get called out and either promoted to SC vocabulary as a follow-up or dropped.

### B4. Volume + base-rate confirmation — §4.4 pre-scoping metadata window pass

**RFC proposal (v0.2 §4.4):** metadata-only pass on the 30-day pre-scoping window confirms expected volume (5–30 deploys/day for `webhook-gateway prod`, 6–140 positives at 2–8% base rate on the 60-day modeling window); if base rate < 1% or > 20%, spike re-scopes; §4.4 per-split floors (50/15/30 positives train/validation/test proposed) are locked via prospective power analysis after metadata pass.

**Decision question:** does the meeting accept the pre-scoping metadata pass as the authoritative volume-lock mechanism, or does it want to inspect the metadata output before locking?

**Options:**
1. **Approve now, lock post-metadata** — approve every §B item conditional on the metadata pass meeting §4.4 bounds. If the pass falls outside bounds, the meeting reconvenes on the volume item only; §B1/B2/B3 stay locked.
2. **Approve after metadata** — the meeting adjourns; runs metadata pass; reconvenes to lock §B1/B2/B3 armed with actual volume numbers. Adds ~1 week to the timeline; produces more defensible locks.
3. **Reject volume methodology** — the meeting doesn't accept the "metadata-only pre-scoping window" separation as adequate; RFC §4.4 needs revision.

**Test to apply:** if per-split positive counts come in at the floor (50/15/30), is the meeting confident the M1/M2/M3 CIs will be tight enough for the GO bar to be falsifiable? If not, option 2 or 3.

---

## §C. Over-concession probes — round-2 flagged authorial defaults

Per `feedback_loop_post_application_review`, round-2 applied 19/20 findings (>95% one-sided) and the post-application review flagged 3 real over-concessions. Each is a `[C<N>]` item below with an explicit **rubber-stamp risk** and a **counter-question** — the meeting must answer these, not skip them. If the meeting agrees with the RFC as-proposed, the reason for agreement gets minuted (not silent assent).

### C1. §6.3 constraint stacking — precision + warnings + FPR

**RFC as-proposed (v0.2 §6.3):** operating threshold gated by THREE simultaneous constraints — precision floor ≥ 0.40, warnings-per-week ≤ 5, FPR ceiling ≤ 25%. All three sit on top of expected-loss minimization.

**Rubber-stamp risk:** precision × prevalence × deploy-rate ≈ warnings-per-week; the two constraints are largely redundant at this base rate. FPR ceiling was the very metric Codex F5 said was wrong for this decision surface (FPR ≠ FDR at low base rate); keeping it as "belt and suspenders" alongside its correct replacement invites re-confusion in downstream reads of the RFC.

**Counter-question:** does the FPR ceiling do any work the precision floor doesn't already do, or is it doctrine drift from the pre-F5 draft?

**Options:**
1. **Simplify to precision + warnings** — drop FPR ceiling; precision floor is the FDR-side bound, warnings-per-week is the operator-workload bound.
2. **Simplify to precision + expected-loss L only** — drop both warnings and FPR; the expected-loss floor via C1 pass condition already captures the operator-cost side.
3. **Keep all three** — the meeting explicitly defends why FPR ceiling is not doctrine drift; minutes record the defense.

**Recommend option 1.** Round-2 review's own recommendation. Two constraints is the tightest defensible set: precision floor bounds what the human sees; warnings-per-week bounds the alert volume the human can process.

### C2. §6.3 severity weights + 30% cost-reduction bar

**RFC as-proposed (v0.2 §6.3):** severity weights `w(critical)=3.0`, `w(major)=2.0`, `w(warning)=1.0`; C1 pass condition requires ≥ 30% expected-loss reduction vs. both baselines.

**Rubber-stamp risk:** the `k=10` FN:FP cost ratio is sourced (PC §3.0). The per-severity weights (3/2/1) are not — no operating-model doc grounds them. The 30% reduction bar is fully invented — Codex F6 asked for "define severity mapping and expected-loss equation," not "pick a specific reduction threshold." Numbers dressed as predeclarations that lack sourcing undercut the spike's own "predeclared means defensible" premise (the exact "hidden guesses dressed as bars" pattern Codex F3 warned against).

**Counter-question:** who owns the on-call cost model, and what number does it produce for "an SLO breach missed by the predictor is worth X on-call hours"?

**Options:**
1. **Option A — source the numbers.** Meeting names an operating-model owner (per VOCABULARY §8 AP-7 accountable data owner pattern). Owner produces: severity weight source (e.g., existing PagerDuty severity taxonomy → weight mapping), reduction-bar source (e.g., "30% expected-loss reduction ≈ N on-call hours/week saved per the current SLA"). Numbers stay in RFC with sourcing attribution.
2. **Option B — retreat to placeholders.** RFC edits `w(*)` and `> 0.30` to `TO BE LOCKED AT SCOPING-APPROVAL`. The meeting itself sources them, or defers §C2 and locks §B1/B2/B3/B4 without it.
3. **Option C — replace with unweighted expected loss.** Drop severity weighting entirely; C1 becomes `(L_baseline_unweighted − L_model_unweighted) / L_baseline_unweighted > <lock>`. Simpler; loses severity signal but eliminates the sourcing gap.

**Recommend option A if an owner is identifiable in the room, else option B.** Option C is a fallback if severity data itself turns out to be unreliable (breach severities are DataDog-tagged; if tagging is noisy, weights based on them inherit the noise).

### C3. §6 bootstrap machinery — block bootstrap + Bonferroni

**RFC as-proposed (v0.2 §6):** temporal block bootstrap (1000 resamples, 60min blocks); Bonferroni correction across 4 primary comparisons at α=0.05 (per-test α=0.0125); every threshold expressed as lower-95%-CI-bound.

**Rubber-stamp risk:** production-grade inferential machinery on a v0.1 scoping RFC. Codex F3 asked for "a paired temporal bootstrap **or equivalent** interval procedure"; the RFC picked the heaviest end. A simpler procedure — "point estimate above margin AND 95% bootstrap CI does not include zero" — captures most of the anti-noise value at a fraction of the implementation cost.

**Counter-question:** is the block-bootstrap + Bonferroni protocol serving the spike's evidence bar, or the RFC drafter's caution?

**Options:**
1. **Keep as-proposed** — full block bootstrap + Bonferroni. Highest defensibility; highest implementation cost.
2. **Simplify to CI-non-zero test** — "point estimate above margin AND 95% bootstrap CI on the difference does not include zero." Standard bootstrap (not block; not Bonferroni). Adequate for v0.1 evidence bar.
3. **Substitute single primary comparison** — RFC's own escape valve: M1 primary, M2/M3/C1 diagnostic. Removes the multiplicity-correction weight entirely; keeps the full CI machinery for the one primary metric.

**Recommend option 2 or 3.** Option 2 if the meeting wants to keep multi-metric gating and just simplifies the interval procedure. Option 3 if the meeting wants to simplify the whole gating structure. Option 1 only if the meeting explicitly defends the production-grade weight on a v0.1 spike.

---

## §D. Sign-off checklist

Every item below must have a name attached before the meeting adjourns with an APPROVED outcome:

- [ ] **B1 — thresholds** locked (specific numbers, in RFC §6.1)
- [ ] **B2 — rules baseline** locked (specific rules, in RFC §5.1)
- [ ] **B3 — feature list** locked (specific features, in RFC §4.3)
- [ ] **B4 — volume + base-rate** methodology confirmed (option 1/2/3 in RFC §4.4)
- [ ] **C1 — §6.3 constraints** decision recorded (option 1/2/3 or explicit "keep as-proposed" with defense)
- [ ] **C2 — severity weights + reduction bar** decision recorded (option A/B/C or explicit sourcing)
- [ ] **C3 — bootstrap machinery** decision recorded (option 1/2/3)
- [ ] Spike execution owner named
- [ ] Timeline sign-off (per RFC §9 indicative dates) or revision
- [ ] AB-030 status confirmed (blocking-for-execution)
- [ ] AB-033 status confirmed (PR #16 merged / awaiting)
- [ ] Meeting outcome recorded verbatim at RFC §11 provenance

---

## §E. Post-meeting closeout

Once the meeting adjourns:

1. **RFC v0.3 edit-in-place** — apply every §B / §C decision to `AB-028_FEASIBILITY_SPIKE.md` §4.3 / §4.4 / §5.1 / §6.1 / §6.3 / §6. Attribution: `*(v0.3 lock — scoping-approval meeting YYYY-MM-DD)*` on each edited stanza.
2. **§11 provenance entry** — new bullet: "YYYY-MM-DD: RFC v0.3 — scoping-approval outcome APPROVED / APPROVED WITH DEFERRALS / NOT APPROVED. Decisions applied inline; agenda doc `AB-028_SCOPING_APPROVAL_AGENDA.md` records what was probed. Attendees: `[list]`. Owner: `[name]`."
3. **This agenda doc closes** — mark status "Superseded by RFC v0.3 §11 provenance entry (YYYY-MM-DD)." Retain in repo as the historical record of what the meeting was set up to probe (not what it decided — that's the RFC's job).
4. **Backlog updates** — AB-028 status: `IN PROGRESS (scoping)` → `IN PROGRESS (execution)`; AB-030 acceptance criterion for `label_schema_validator` reaffirmed as gate-for-start; any newly-filed follow-ups from §C answers get their own AB-NNN entries.

---

## Provenance

- **2026-07-27:** Agenda doc drafted as companion to `AB-028_FEASIBILITY_SPIKE.md` v0.2. Structured to surface the three over-concessions from the round-2 post-application review (`research/feedback_loops/dynamic-reliability-AB-028_FEASIBILITY_SPIKE/20260726T082924Z/reconciled.md` §"Post-application over-concession review") so scoping-approval doesn't rubber-stamp authorial defaults. Not yet reviewed by the meeting chair.
