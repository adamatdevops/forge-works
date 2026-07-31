# AB-028 Scoping-Approval Reviewer Memo (v0.1 draft)

> **Status:** One reviewer's opinion on the AB-028 scoping-approval decisions. Companion to `AB-028_SCOPING_APPROVAL_AGENDA.md` — NOT a decision doc. The meeting still decides; this memo exists so the meeting has a straw-doc to react to instead of starting from a blank page.
> **Reviewer:** first-pass memo written by ADR-authored review (not the RFC drafter). Explicitly a *perspective*, not a *conclusion*.
> **Companion to:** [`AB-028_SCOPING_APPROVAL_AGENDA.md`](AB-028_SCOPING_APPROVAL_AGENDA.md) — the agenda is the source of truth for decision options; this memo picks one option per item and defends it.
> **What this memo is:** a starting point for the meeting to challenge. If every recommendation here survives without pushback, the meeting has rubber-stamped a single author's opinion — the exact failure mode the agenda's §0 warns against. Adversarial engagement is the goal.
> **What this memo is not:** the RFC. The RFC ships thresholds as proposals; this memo does not upgrade them to locks. Only the meeting's minutes do.

---

## Reading order

Read the agenda first. Then read this memo alongside it — for each §B / §C item, the agenda enumerates the options; this memo picks one and says why. Then challenge the pick during the meeting.

Explicit caveat on reviewer scope: the reviewer authoring this memo has NOT independently verified the ML methodology behind §B1 threshold proposals, has NOT run the pre-scoping metadata pass (PR #25) against real DataDog data (data access not granted), and has NOT surveyed the platform team to independently verify §B2 rule realism. The recommendations below are reasoned from the RFC + doctrine documents; they inherit any blind spots the RFC has.

---

## §A. Prerequisites status (informational — the meeting reads and moves on)

| # | Item | Reviewer status |
|---|------|-----------------|
| A1 | AB-033 (PC §3.0 observational estimand) merged on main | ✔ Confirmed merged as PR #16 (2026-07-28). |
| A2 | AB-030 `label_schema_validator` library scoping RFC drafted | ✔ Library shipped as PR #22 (v0.1.0); spike integration scaffold as PR #23; conditional-field rules stable per GT v0.3. |
| A3 | Pre-scoping metadata pull scripts exist | ✔ Metadata-window pass tool shipped as PR #25; runs against synthetic data today, real Terraform + DataDog loaders drop in via the `EventLoader` Protocol. Real data-access wiring is the remaining gap. |
| A4 | Spike execution owner assigned | ✘ Not yet named. The meeting must produce a name before adjourning with APPROVED status. |

**Reviewer note:** A3 has changed since the agenda was drafted — the metadata pass tool now exists as executable code. What was "confirm scripts exist" is now "point the tool at real data." That's a smaller lift than the agenda originally implied, but not zero: the `EventLoader` implementation for Terraform + DataDog still needs to be written (~1 day of work, plus API-token provisioning).

---

## §B. Lock items — reviewer recommendation per item

### B1 — Threshold lock (§6.1 M1 / M2 / M3)

**Recommendation: Option 1 — accept RFC v0.2 proposals** (M1 AUCPR lower CI ≥ 0.05 lift + normalized ≥ prevalence + 0.10; M2 ECE ≤ 0.10; M3 Brier strict inequality vs. baselines + constant-predictor).

**Reasoning:**

- The margins are defensible on the "advisory-only at T2" evidence bar. A 0.05 AUCPR-lift lower CI vs. the max baseline is a real gap on realistic sample sizes — not so tight that noise passes, not so wide that a small-but-real signal fails.
- M2's 0.10 ECE ceiling matches typical calibration targets for probabilistic recommendations at low base rates.
- M3's strict inequality (not `≤`) is important — the v0.1 draft's `≤` would have permitted tied Brier with baselines, which is not evidence of lift.
- **Codex F11 lift** (normalized floor above prevalence) is defensible — it prevents "GO on a worse-than-random model" when prevalence is high.

**What would change my recommendation:**

- If PR #25 metadata pass (against real data, once wired) shows base rate > 15% with tight per-split floors — then the 0.10 normalized-lift-over-prevalence bar becomes very tight (prevalence + 0.10 approaches or exceeds AUCPR = 0.25, which is a stretch for tabular models on small data). At that point, consider Option 3 (single primary comparison on M1, demote M2/M3/C1 to diagnostic).

**Adversarial angle for the meeting to press:**

- Is 0.05 absolute lift meaningful if the CI is wide because per-split positive counts are near the §4.4 floor? Consult PR #25's projected floors output before locking.

---

### B2 — Rule list lock (§5.1)

**Recommendation: Option 1 — accept RFC v0.2 proposals** (5 rules: apply_failed-last-6h, slo_burning-last-1h, monitor warning/alert, sensitive-resource-touched + apply_failed-last-7d, plan_diff_size > P90).

**Reasoning:**

- Each rule maps to a specific rules-first mental model an SRE would articulate: "we just failed", "we're already burning", "monitor's already unhappy", "risky resource type + recent failures", "big blast radius change".
- Rule 5's `P90(plan_diff_size)` is data-derived on training window only (per F7) — good discipline; not a hand-picked constant.
- Empirical-rate probability mapping per F7 keeps the rules baseline calibration-comparable — critical for M2 ECE and C1 expected loss.

**What would change my recommendation:**

- If the platform team's SRE reviewer says "we'd obviously also check X" (e.g., "deploy in maintenance window") that isn't on the list, add it as Option 2. **This is the specific rubber-stamp risk on B2.** The reviewer writing this memo is NOT an SRE on this stack; the meeting MUST include SRE input on this item.

**Adversarial angle for the meeting to press:**

- Ask an SRE who owns webhook-gateway prod today: "what rules would you actually use to guess whether a deploy will breach the SLO?" Compare their list against the 5. Any additions get filed as Option 2.
- Rule 4 (sensitive-resource + apply_failed-last-7d) — is 7d the right window? An SRE might say 24h or 30d.

---

### B3 — Feature list lock (§4.3)

**Recommendation: Option 1 — accept RFC v0.2 proposals** (4 families: deployment metadata, recent-history rolling counts at 1h/6h/24h/7d, slice-state monitor + incident, deploy-content sensitive-resource + plan-diff-size).

**Reasoning:**

- The four families cover the standard tabular-ML feature axes for a deploy-risk prediction: what was deployed, what's happening around it, what state is the system in, what's the change's blast radius.
- Strict as-of-T0 boundary is enforced in the harness (PR #24 `features.py`) with `assert_no_lookahead_for` — implementation-level guarantee, not just doctrinal.

**What would change my recommendation:**

- If the platform team observes features that are trivially available and demonstrably predictive that AREN'T on the list, add them. Candidates to probe: `deploy_author_seniority_weeks`, `time_since_last_deploy`, `pending_alerts_on_dependency_services`.
- If any feature is on the list but is **unavailable in the historical event stream** (schema drift, retention gap), remove BEFORE label opening per §4.3's discipline — never after.

**Adversarial angle for the meeting to press:**

- SC §4 requires every feature to trace to a source contract vocabulary entry. Walk the list; find features that don't trace and either promote them to SC vocabulary or drop.
- Are any features leakage-adjacent? E.g., "current DataDog monitor state" might use a state-derivation window that peeks past T0 in edge cases.

---

### B4 — Volume + base-rate confirmation (§4.4)

**Recommendation: Option 1 — approve now, lock post-metadata** (approve §B1/B2/B3 conditional on the metadata pass meeting §4.4 bounds).

**Reasoning:**

- PR #25 (metadata pass tool) exists NOW as executable code. Wiring the `EventLoader` for real Terraform + DataDog is ~1 day of engineering work. The meeting should NOT block on the metadata pass output before locking §B1-§B3; instead, lock conditionally and reconvene on volume-only if the pass produces surprises.
- The metadata pass includes a prospective power projection that computes expected per-split positive counts BEFORE training data is inspected — this is the discipline §4.4 asks for.
- Option 2 (adjourn, run metadata, reconvene) adds ~1 week of coordination overhead for a case where the numbers rarely surprise. Reserve it for when there's genuine uncertainty about the base rate.

**What would change my recommendation:**

- If the platform team has NO handle on the current base rate for webhook-gateway prod SLO breaches — no dashboard, no ballpark — then Option 2 (adjourn, run metadata first). Guessing here is expensive later.

**Adversarial angle for the meeting to press:**

- What's the current dashboard-visible SLO-breach rate on webhook-gateway prod over the last 30 days? If that number isn't known within the meeting, the base-rate lock should not happen — run the metadata pass first (Option 2).

---

## §C. Over-concession probes — reviewer recommendation per item

The RFC's own §C recommendations (from the agenda) are echoed here, but the reviewer adds their reasoning + adversarial angles.

### C1 — §6.3 constraint stacking (precision + warnings + FPR)

**Recommendation: Option 1 — simplify to precision + warnings** (drop FPR ceiling). **Concurs with RFC agenda recommend-line.**

**Reasoning:**

- FPR ceiling was doctrinal leftover from the pre-F5 draft. F5 explicitly said FPR is the wrong metric at low base rate (FDR ≠ FPR); the RFC replaced it with precision floor as the FDR-side bound. Keeping FPR ceiling alongside its replacement is doctrine drift — future readers will re-confuse the two.
- Precision floor already bounds what the T2 consumer sees (FDR-side).
- Warnings-per-week already bounds operator workload.
- Two constraints is the tightest defensible set at this base rate.

**What would change my recommendation:**

- If there's a documented operating-model reason FPR needs to stay separate — cite it. Nothing in the RFC references such a doc.

**Adversarial angle for the meeting to press:**

- If the answer is "keep all three for belt-and-suspenders," explicitly minute the defense so future readers know it was a deliberate choice not doctrine drift.

---

### C2 — §6.3 severity weights + 30% cost-reduction bar

**Recommendation: Option A if an operating-model owner is identifiable in the room. Option B (retreat to placeholders) if no owner can be named.** **Concurs with RFC agenda recommend-line.**

**Reasoning:**

- The `k=10` FN:FP cost ratio is sourced (PC §3.0). The severity weights (3/2/1) and 30% reduction bar are not sourced. Numbers dressed as predeclarations that lack sourcing undercut the spike's own "predeclared means defensible" premise (Codex F3's exact warning).
- If a PagerDuty-severity-to-weight mapping exists (or an on-call-cost-per-hour by severity), pin the weights to that source. That's Option A.
- If no owner exists TODAY, Option B is honest — the RFC's placeholders become explicitly `TO BE LOCKED` and the meeting either sources them post-hoc or defers §C2 (and locks §B1/B2/B3/B4 without it).

**What would change my recommendation:**

- Option C (unweighted expected loss) becomes attractive if severity data itself is noisy — DataDog SLO-event severity tags are set by monitor configs; if the monitor configs aren't consistent across the slice, weights based on them inherit the noise.

**Adversarial angle for the meeting to press:**

- Who owns the on-call cost model at ForgeWorks? If nobody can name the owner in 30 seconds, that IS the answer — no owner means no source, means Option B.

---

### C3 — §6 bootstrap machinery (block bootstrap + Bonferroni)

**Recommendation: Option 2 — simplify to CI-non-zero test** (standard bootstrap, no block, no Bonferroni). **Concurs with RFC agenda recommend-line's first option; falls back to Option 3 if the meeting wants to further simplify gating structure.**

**Reasoning:**

- The block-bootstrap-with-60min-blocks + Bonferroni-across-4-primaries protocol is production-grade inferential machinery on a v0.1 scoping RFC. Codex F3 asked for "a paired temporal bootstrap **or equivalent** interval procedure"; the RFC picked the heaviest end.
- Option 2 ("point estimate above margin AND 95% bootstrap CI on the difference does not include zero") captures most of the anti-noise value at a fraction of the implementation cost.
- PR #24 (harness) implements Option 1 today (`metrics.py::bootstrap_ci_of_difference` uses block bootstrap). If the meeting picks Option 2, the harness needs to swap the block bootstrap for standard bootstrap — small code change (~20 lines).

**What would change my recommendation:**

- If the platform team wants the strongest defensibility signature possible for the spike report (e.g., if audit / compliance reviewers will read it), keep Option 1. The overhead pays for itself if the spike report will face adversarial review.
- If the meeting believes M1 primary + M2/M3/C1 diagnostic is the honest evidence bar (i.e., the corpus-graduation gate only needs one metric to lift), Option 3.

**Adversarial angle for the meeting to press:**

- Who reads the spike report? If it's just the platform team + AB-028 sign-off, Option 2 is enough. If it's external audit (SOC 2 / regulatory review), Option 1 is worth the overhead.

---

## §D. Sign-off checklist mapping

For each agenda §D checklist item, this memo provides:

- [x] **B1 thresholds** — memo recommends Option 1; meeting decides
- [x] **B2 rules** — memo recommends Option 1 **subject to SRE input** (mandatory challenge point)
- [x] **B3 features** — memo recommends Option 1 subject to SC-vocabulary trace check
- [x] **B4 volume** — memo recommends Option 1 (approve conditional on PR #25 metadata pass output)
- [x] **C1** — memo recommends Option 1 (drop FPR ceiling)
- [x] **C2** — memo recommends Option A if owner named, else Option B
- [x] **C3** — memo recommends Option 2 (simplify to CI-non-zero), or Option 3 if further simplification wanted
- [ ] **Spike execution owner** — memo cannot recommend; the meeting produces the name
- [ ] **Timeline sign-off** — memo defers to the meeting; RFC §9 timeline is indicative
- [x] **AB-030 status** — confirmed shipped
- [x] **AB-033 status** — confirmed merged as PR #16

---

## §E. Meeting-outcome scenarios per this memo

If the meeting adopts EVERY recommendation in this memo without pushback, the outcome is **APPROVED** with:

- §B1/B2/B3/B4 locked at RFC v0.2 proposal values, with B2 explicitly flagged for SRE consultation (may re-open) and B4 conditional on PR #25 metadata output being within §4.4 bounds
- §C1 amended: FPR ceiling dropped; precision floor + warnings-per-week only
- §C2 outcome depends on whether an operating-model owner is nameable in the room
- §C3 amended: block-bootstrap + Bonferroni → standard-bootstrap CI-non-zero (harness change needed: ~20 lines in PR #24 `metrics.py`)

**But: if the meeting adopts every recommendation without pushback, it has rubber-stamped a single reviewer's opinions. That's the exact failure mode the agenda's §0 warns against.** The reviewer authoring this memo does not have SRE domain knowledge for §B2, has not seen the real metadata output for §B4, and cannot identify the operating-model owner for §C2. Those three items in particular MUST see live debate.

---

## Provenance

- **2026-07-31:** v0.1 draft. Written as a companion to `AB-028_SCOPING_APPROVAL_AGENDA.md` after PR #25 (metadata pass tool) shipped and made §A3 tractable. Purpose: give the meeting a straw-doc to react to instead of a blank page, while preserving the agenda's challenge-don't-confirm structure. Not reviewed by the meeting chair. Not a decision doc.
