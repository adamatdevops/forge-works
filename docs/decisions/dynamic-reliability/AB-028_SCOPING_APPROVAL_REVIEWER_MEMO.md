# AB-028 Scoping-Approval Reviewer Memo (v0.2 draft)

> **Status:** One reviewer's opinion on the AB-028 scoping-approval decisions, refined 2026-08-02 after Codex round-1 loop critique. Companion to `AB-028_SCOPING_APPROVAL_AGENDA.md` — NOT a decision doc. The meeting still decides; this memo exists so the meeting has a straw-doc to react to instead of starting from a blank page.
> **Reviewer:** first-pass memo written by ADR-authored review (not the RFC drafter). Explicitly a *perspective*, not a *conclusion*.
> **Companion to:** [`AB-028_SCOPING_APPROVAL_AGENDA.md`](AB-028_SCOPING_APPROVAL_AGENDA.md) — the agenda is the source of truth for decision options; this memo picks one option per item and defends it (with explicit epistemic caveats per §B/§C item where the reviewer lacks domain evidence).
> **What this memo is:** a starting point for the meeting to challenge. If every recommendation here survives without pushback, the meeting has rubber-stamped a single author's opinion — the exact failure mode the agenda's §0 warns against. Adversarial engagement is the goal.
> **What this memo is not:** the RFC. The RFC ships thresholds as proposals; this memo does not upgrade them to locks. Only the meeting's minutes do.
> **v0.2 change (2026-08-02):** every §B/§C recommendation now carries an explicit epistemic-status line — reasoning-from-principles vs empirically-verified vs conditional-on-external-input. Codex round-1 loop surfaced that v0.1's "defensible" and "typical" language claimed sourcing that didn't exist; v0.2 keeps the picks (memo role: give the meeting something to react to) but honest-labels their basis. §A A3 status corrected from `✔` to `◐ Partial` after empirical check of `adapters.py` — production `EventLoader`s do not exist yet.

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
| A3 | Pre-scoping metadata pull scripts exist | **◐ Partial.** Metadata-window pass tool shipped as PR #25; the `EventLoader` Protocol exists at `src/label-derivation-spike/forge_works/dr/ab028_spike/adapters.py`; **only a `SyntheticEventLoader` reference impl exists — no `TerraformEventLoader` or `DataDogEventLoader` class has been written.** See unmet checks below. |
| A4 | Spike execution owner assigned | ✘ Not yet named. The meeting must produce a name before adjourning with APPROVED status. |

**A3 unmet checks** (v0.2 correction after empirical check of `adapters.py`):

- [ ] `TerraformEventLoader` implementation (reading Terraform state + apply-history events for the slice)
- [ ] `DataDogEventLoader` implementation (reading DataDog monitor state + SLO burn events for the slice)
- [ ] DataDog API token provisioned and stored via approved secret management
- [ ] Terraform state read-access credential provisioned (or state-file mount point declared)
- [ ] MLflow experiment ID reserved for the metadata pass
- [ ] Modeling-window write-lock enforced (e.g., MLflow tag `modeling_window_locked=true` with tooling that refuses inspection of the locked range)
- [ ] Successful bounded-window smoke run against real data (e.g., 24h `webhook-gateway prod` slice) end-to-end through the pass, reporting non-empty counts

**Reviewer note (v0.2):** the agenda's expectation that A3 was ready has NOT been met — the memo v0.1 status `✔` was misleading. The tool's **contract** (via the Protocol) is in place, but no real-data code path exists. Prior v0.1 estimate "~1 day of work" for the two loader classes is a reasonable ceiling, but each loader is an unwritten class plus at least one plumbing test; the API-token side-work (procurement + approval) may dominate wall-clock.

---

## §B. Lock items — reviewer recommendation per item

### B1 — Threshold lock (§6.1 M1 / M2 / M3)

**Recommendation: Option 1 — accept RFC v0.2 proposals** (M1 AUCPR lower CI ≥ 0.05 lift + normalized ≥ prevalence + 0.10; M2 ECE ≤ 0.10; M3 Brier strict inequality vs. baselines + constant-predictor).

**Epistemic status (v0.2):** *reasoning-from-principles* — this reviewer has NOT run a power analysis on the projected 50/15/30 positive floors and has NOT cited a published calibration benchmark for the 0.10 ECE ceiling. The recommendation is a straw-doc pick worth defending under meeting inspection, not a sourced-benchmark endorsement.

**Reasoning:**

- The margins are proposed as a plausible "advisory-only at T2" evidence bar. A 0.05 AUCPR-lift lower CI vs. the max baseline is *intended* to be a real gap on realistic sample sizes — not so tight that noise passes, not so wide that a small-but-real signal fails. **The meeting should confirm whether it is by running the power analysis called for in H(new) below.**
- M2's 0.10 ECE ceiling is a commonly-cited round-number target for probabilistic recommendations. **Meeting should either cite an internal calibration-cohort baseline or accept the number as reviewer-proposed-not-benchmarked.**
- M3's strict inequality (not `≤`) is important — the v0.1 draft's `≤` would have permitted tied Brier with baselines, which is not evidence of lift.
- **Codex F11 lift** (normalized floor above prevalence) is defensible against the risk of "GO on a worse-than-random model" when prevalence is high.

**Required to promote this recommendation from straw-doc to lock (v0.2):**

- Prospective power analysis (not merely count projection — see B4 v0.2) demonstrating that at 50/15/30 positive floors, the 0.05 AUCPR-difference CI is narrow enough to exclude zero under plausible effect sizes.
- Either a citation for the 0.10 ECE ceiling OR meeting-minuted acceptance that the ceiling is set by reviewer proposal, not benchmark.

**What would change my recommendation:**

- If PR #25 metadata pass (against real data, once wired — see A3 unmet checks) shows base rate > 15% with tight per-split floors — then the 0.10 normalized-lift-over-prevalence bar becomes very tight (prevalence + 0.10 approaches or exceeds AUCPR = 0.25, which is a stretch for tabular models on small data). **Correction from v0.1:** at that point consider **Option 2 (amend M1 margin — lower the 0.10 normalized-lift-over-prevalence bar or reformulate as absolute AP threshold)**, not Option 3. Option 3 addresses infeasibility caused by multiplicity across M1+M2+M3+C1, not by M1's own absolute floor.

**Adversarial angle for the meeting to press:**

- Is 0.05 absolute lift meaningful if the CI is wide because per-split positive counts are near the §4.4 floor? Consult PR #25's projected floors output before locking — noting that the pass's current "prospective power analysis" is actually only count extrapolation (see B4 v0.2 correction); a proper CI-width simulation is what would answer this question.

---

### B2 — Rule list lock (§5.1)

> **Agenda staleness callout (v0.2):** Agenda §B2 line 58 lists a rule set (`deploy-hour heuristics / rollback-recent / error-rate-recent / cross-service-dependency`) that DOES NOT MATCH the current RFC §5.1 (`apply_failed-6h / slo_burning-1h / monitor-state / IAM+apply_failed-7d / plan_diff > P90`). The RFC is the source of truth; the agenda has drifted. This memo works from the RFC's actual list. **The agenda needs a coordinated update** — filed as part of the memo v0.2 lift (agenda §B2 line 58 replaced with the RFC-current list; see agenda commit alongside this file).

**Recommendation: Provisional Option 1 — accept RFC v0.2 proposals conditional on SRE consultation** (5 rules: apply_failed-last-6h, slo_burning-last-1h, monitor warning/alert, sensitive-resource-touched + apply_failed-last-7d, plan_diff_size > P90).

**Epistemic status (v0.2):** *provisional pending SRE input* — this reviewer is NOT an SRE on the `webhook-gateway prod` slice. The pick stands as "here's what an RFC-endorsed baseline looks like for the meeting to react to." Meeting outcome: (a) SRE confirms → lock Option 1; (b) SRE names missing rules → Option 2 (add rules); (c) SRE says a listed rule is weak/wrong → Option 3 (drop or amend); (d) no SRE in the room → dated deferral of B2 only (per agenda §0 APPROVED WITH DEFERRALS envelope; §B1/B3/B4 can still lock).

**Reasoning:**

- Each rule maps to a specific rules-first mental model an SRE would articulate: "we just failed", "we're already burning", "monitor's already unhappy", "risky resource type + recent failures", "big blast radius change".
- Rule 5's `P90(plan_diff_size)` is data-derived on training window only (per F7) — good discipline; not a hand-picked constant.
- Empirical-rate probability mapping per F7 keeps the rules baseline calibration-comparable — critical for M2 ECE and C1 expected loss.

**What would change my recommendation:**

- If the platform team's SRE reviewer says "we'd obviously also check X" (e.g., "deploy in maintenance window") that isn't on the list, add it as Option 2. **This is the specific rubber-stamp risk on B2.** The reviewer writing this memo is NOT an SRE on this stack; the meeting MUST include SRE input on this item.

**Adversarial angle for the meeting to press:**

- Ask an SRE who owns webhook-gateway prod today: "what rules would you actually use to guess whether a deploy will breach the SLO?" Compare their list against the 5. Any additions get filed as Option 2.
- Rule 4 (sensitive-resource + apply_failed-last-7d) — is 7d the right window? An SRE might say 24h or 30d.
- **Rule-aggregation probe (v0.2 addition):** the RFC's empirical-rate mapping collapses all-rule matches into two scores (`P(pos|any match)` vs `P(pos|no match)`) — that's a two-score ranker. A real ops team would likely use rule-specific severity, match count, or ordered risk bands. Ask the SRE whether the deployable rules mental model would use richer aggregation than pure OR. If yes, either the baseline needs to reflect it OR the meeting explicitly minutes the OR aggregation with a documented rationale so future readers know it was a scope-limiting choice, not a diligence gap.

---

### B3 — Feature list lock (§4.3)

**Recommendation: BLOCKING DISCREPANCY — no recommendation until RFC ↔ code parity matrix is green.**

**Epistemic status (v0.2):** *empirically-blocked* — reading `src/label-derivation-spike/forge_works/dr/ab028_spike/features.py:126-160` against RFC §4.3 shows the current implementation diverges from the RFC in both directions:

**B3.1 RFC-to-code-to-source-contract parity matrix** (v0.2 addition):

| RFC §4.3 feature | Implementation in `features.py` | Status |
|------------------|--------------------------------|--------|
| `count of resource creates vs updates vs destroys` (Deploy-content family) | Not implemented — code has only `resource_count` (single scalar) | **Missing — required by RFC** |
| `current active-incident count for the slice` (Slice-state family) | Not implemented — code has `recent_incidents_24h` (24h rolling count) — DIFFERENT semantics | **Semantic mismatch** |
| `days-since-slice-was-added` | ✓ implemented as `days_since_slice_added` | **OK** |
| `count of terraform.apply_failed in {1h, 6h, 24h, 7d}` | ✓ implemented as `apply_failed_last_{1,6,24,168}h` | **OK — verify 168h == 7d convention** |
| `count of datadog.slo_burning in {1h, 6h, 24h}` | ✓ implemented as `slo_burning_last_{1,6,24}h` | **OK** |
| `time-since-last-apply` | ✓ implemented as `time_since_last_apply_failure_h` | **OK** |
| `time-since-last-slo-breach` | ✓ implemented as `time_since_last_breach_h` | **OK** |
| `current DataDog monitor state per SLO` | ✓ implemented as `monitor_state__{state}` one-hot | **OK — see leakage probe below** |
| `plan diff size in bytes` | ✓ implemented as `plan_diff_size` | **OK** |
| `resource types touched` | ✓ implemented as `resource_type__{rt}` one-hot | **OK** |
| `deploy author role`, `hour-of-day`, `day-of-week` | ✓ implemented | **OK** |
| **NOT IN RFC** — `is_friday_pm` | ✓ code adds it | **Undeclared — either promote to RFC or remove** |
| **NOT IN RFC** — `sensitive_resource_touched` boolean | ✓ code adds it | **Undeclared — promote to RFC (implicit in "IAM/security-group/network resources touched" bullet, but the aggregate boolean isn't itemized)** |

Meeting locks §B3 only after this matrix is green: every "Missing," "Semantic mismatch," and "Undeclared" row is resolved (add code, amend RFC, or explicitly document as intentional deferral). Recommend the parity check runs BEFORE the scoping-approval meeting so the meeting has a resolved matrix in hand.

**Reasoning (background, applies once matrix is green):**

- The four families cover the standard tabular-ML feature axes for a deploy-risk prediction: what was deployed, what's happening around it, what state is the system in, what's the change's blast radius. This is the intended coverage; the code diverges from it in the specifics called out above.
- **Correction (v0.2):** the harness's `assert_no_lookahead_for` (PR #24 `features.py:185-196`) is a **synthetic-stream sanity check**, not an implementation-level guarantee. The helper's own docstring says: "Sanity check used by tests: no synthetic-stream event with time >= t0 can be visible to the feature builder at T0." It only rejects supplied synthetic events at/after T0; it does NOT validate DataDog state-derivation semantics, event vs ingestion time reconciliation, late arrivals, or monitor-state boundary derivations against real source data. Real-data temporal-join safety requires source-specific tests that the harness does not yet include.

**What would change my recommendation** (once matrix is green):

- If the platform team observes features that are trivially available and demonstrably predictive that AREN'T on the list, add them. Candidates to probe: `deploy_author_seniority_weeks`, `time_since_last_deploy`, `pending_alerts_on_dependency_services`.
- If any feature is on the list but is **unavailable in the historical event stream** (schema drift, retention gap), remove BEFORE label opening per §4.3's discipline — never after.

**Adversarial angle for the meeting to press:**

- SC §4 requires every feature to trace to a source contract vocabulary entry. Walk the list; find features that don't trace and either promote them to SC vocabulary or drop. **`is_friday_pm` needs an explicit trace** (via `hour_of_day` + `day_of_week` composition, or as its own vocabulary entry).
- Are any features leakage-adjacent? E.g., "current DataDog monitor state" might use a state-derivation window that peeks past T0 in edge cases. **Request source-specific temporal-join tests** using DataDog event time vs ingestion time; test monitor-state derivation across state-transition boundaries at exactly T0; test late-arrivals scenarios (event with `event_time < T0` but `ingestion_time > T0`).

---

### B4 — Volume + base-rate confirmation (§4.4)

**Recommendation: Option 2 — approve after metadata pass runs against real data** (adjourn, run pass, reconvene to lock §B1/B2/B3).

**Epistemic status (v0.2):** *flipped from v0.1 Option 1 after empirical check* — v0.1 assumed the metadata pass tool could produce lockable evidence today. Two facts changed the recommendation: (a) the tool has no real-data path (per A3 unmet checks — only `SyntheticEventLoader` exists in `adapters.py`); (b) reading `metadata_window.py`'s `ProjectedModelingWindow` dataclass shows it produces **count projections**, not prospective **power analysis**. The RFC / tool docstring calls it "prospective power-analysis projection" but the output carries `projected_train_positives`/etc. with no CI-width or detectable-effect calculation. A count projection is necessary but not sufficient for locking thresholds whose falsifiability depends on CI width.

**Superseded v0.1 recommendation:** Option 1 (approve conditional on metadata pass meeting §4.4 bounds) — retained for audit-trail visibility only.

**Reasoning (v0.2):**

- PR #25 shipped a solid metadata-pass framework, but its `ProjectedModelingWindow` output is count extrapolation. A proper prospective power analysis simulates the AUCPR-difference CI width across plausible effect sizes (e.g., 0.03 / 0.05 / 0.10) under temporal block structure at the projected sample sizes, and reports the smallest effect the design could detect at the 95% CI's lower bound. Without that, "count meets floor" does not answer "CI narrow enough for a falsifiable GO on 0.05 lift."
- The A3 unmet checks (write two `EventLoader` classes, provision credentials, get a smoke run) block Option 1's "approve conditional" path anyway — there is no pass output today to be conditional on.
- Option 2 (adjourn, run metadata, reconvene) adds one meeting cycle of coordination overhead — worth the delay to produce defensible locks. **v0.2 note:** the v0.1 "~1 week" and "numbers rarely surprise" language has been dropped as unsupported.

**Required to move from Option 2 back to Option 1** (for a future scoping-approval attempt):

- All A3 unmet checks green (`TerraformEventLoader`, `DataDogEventLoader`, credentials, MLflow experiment reservation, write-lock, smoke run).
- Metadata pass extended to include prospective power analysis proper (CI-width simulation at 0.03 / 0.05 / 0.10 effect sizes; report detectable-effect floor at 50/15/30 positive splits).
- Real-data pass output shows base rate within §4.4 bounds AND CI-width simulation shows M1 0.05 AUCPR-lift detectable.

**What would change my recommendation:**

- If the meeting has NO tolerance for a one-cycle delay AND explicitly minutes "we accept locking §B1-§B3 on synthetic-pass extrapolation as an interim measure until real-data results land, understanding thresholds may need to change" — then a modified Option 1 becomes defensible with that caveat recorded.
- If the platform team has NO handle on the current base rate for webhook-gateway prod SLO breaches — no dashboard, no ballpark — Option 2 is doubly warranted. Guessing here is expensive later.

**Adversarial angle for the meeting to press:**

- What's the current dashboard-visible SLO-breach rate on webhook-gateway prod over the last 30 days? If that number isn't known within the meeting, the base-rate lock should not happen — run the metadata pass first (Option 2).

---

## §C. Over-concession probes — reviewer recommendation per item

The RFC's own §C recommendations (from the agenda) are echoed here, but the reviewer adds their reasoning + adversarial angles.

### C1 — §6.3 constraint stacking (precision + warnings + FPR)

**Recommendation: Option 1 — simplify to precision + warnings** (drop FPR ceiling). **Concurs with RFC agenda recommend-line.**

**Reasoning:**

- FPR ceiling is doctrinally superseded per RFC round-2 F5 (FDR ≠ FPR at low base rate; precision floor is the FDR-side bound). Keeping FPR ceiling alongside its replacement invites re-confusion in future reads.
- Precision floor already bounds what the T2 consumer sees (FDR-side).
- Warnings-per-week already bounds operator workload.
- Two constraints is the tightest defensible set at this base rate.

**Empirical binding pre-condition (v0.2):** before dropping FPR ceiling, the meeting should confirm on the metadata pass output (once real-data available) that FPR is redundant with precision + warnings-per-week across the candidate operating-threshold range. If FPR binds at any threshold where precision + warnings does not, retain FPR ceiling and record the empirical binding rationale (Option 3). Codex round-1 loop on this memo flagged that "categorical" dismissal of FPR was too strong without empirical redundancy evidence.

**What would change my recommendation:**

- If there's a documented operating-model reason FPR needs to stay separate — cite it. Nothing in the RFC references such a doc.

**Adversarial angle for the meeting to press:**

- If the answer is "keep all three for belt-and-suspenders," explicitly minute the defense so future readers know it was a deliberate choice not doctrine drift.

---

### C2 — §6.3 severity weights + 30% cost-reduction bar

**Recommendation: Option A only if a named owner produces both written artifacts (severity-weight mapping source AND reduction-bar source with cost calculation) before the meeting closes. Option B (retreat to placeholders) if no owner exists anywhere. If an owner is identifiable but the artifacts require research, use a dated §C2 deferral (per agenda §0 APPROVED WITH DEFERRALS envelope).** **Refines the agenda recommend-line for artifact-completion rigor (v0.2).**

**Reasoning:**

- The `k=10` FN:FP cost ratio is sourced (PC §3.0). The severity weights (3/2/1) and 30% reduction bar are not sourced. Numbers dressed as predeclarations that lack sourcing undercut the spike's own "predeclared means defensible" premise (Codex F3's exact warning).
- Agenda §C2 Option A explicitly requires the owner to produce "severity weight source" AND "reduction-bar source with cost calculation" — not just "an owner is named." **v0.2 correction:** naming an owner in-the-room is NECESSARY but NOT SUFFICIENT for Option A — the artifacts themselves must land before the number is retained. Otherwise the memo's Option A gate permits invented numbers to survive on owner-identity alone.
- If a PagerDuty-severity-to-weight mapping exists (or an on-call-cost-per-hour by severity), pin the weights to that source. That's Option A.
- If no owner exists ANYWHERE (not just "not in the room today"), Option B is honest — the RFC's placeholders become explicitly `TO BE LOCKED` and the meeting either sources them post-hoc or defers §C2 (and locks §B1/B2/B3/B4 without it).
- Absence-in-the-room is not proof of no-owner. If the owner is a specific engineer (e.g., an on-call lead, a director) or a specific channel/list (e.g., `#sre-oncall`), Option A can proceed via dated §C2 deferral rather than immediately collapsing to Option B.

**What would change my recommendation:**

- Option C (unweighted expected loss) becomes attractive if severity data itself is noisy — DataDog SLO-event severity tags are set by monitor configs; if the monitor configs aren't consistent across the slice, weights based on them inherit the noise.

**Adversarial angle for the meeting to press:**

- Who owns the on-call cost model at ForgeWorks? If nobody can name the owner in 30 seconds AND no channel / list / role can be pointed to — that's the Option B answer. If an owner or channel CAN be pointed to but the artifacts don't exist in-room, that's the dated §C2 deferral path (not immediate Option B).

---

### C3 — §6 bootstrap machinery (block bootstrap + Bonferroni)

**Recommendation: Option 2 — simplify to CI-non-zero test** (standard bootstrap, no block, no Bonferroni). **Concurs with RFC agenda recommend-line's first option; falls back to Option 3 if the meeting wants to further simplify gating structure.**

**Reasoning:**

- The block-bootstrap-with-60min-blocks + Bonferroni-across-4-primaries protocol is production-grade inferential machinery on a v0.1 scoping RFC. Codex F3 asked for "a paired temporal bootstrap **or equivalent** interval procedure"; the RFC picked the heaviest end.
- Option 2 ("point estimate above margin AND 95% bootstrap CI on the difference does not include zero") captures most of the anti-noise value at a fraction of the implementation cost.
- **Implementation-cost correction (v0.2):** PR #24 (harness) already implements Option 1 today (`metrics.py:193-221` `bootstrap_ci_of_difference` with `_block_index` helper). Picking Option 2 does NOT save implementation effort — it requires REPLACING the existing block-bootstrap implementation with standard bootstrap (~20 lines to remove; `_block_index` becomes dead code). Cost comparison is evidence-bar vs current-impl weight, not implementation-delta. v0.1 phrased this backwards as if Option 2 was the smaller lift.
- An autocorrelation analysis on the metadata pass output (once real-data available — see B4 v0.2) can justify IID bootstrap if events are effectively independent at the block scale. Without that analysis, Option 2's default is asserted, not derived.

**What would change my recommendation:**

- If the platform team wants the strongest defensibility signature possible for the spike report (e.g., if audit / compliance reviewers will read it), keep Option 1. The overhead pays for itself if the spike report will face adversarial review.
- If the meeting believes M1 primary + M2/M3/C1 diagnostic is the honest evidence bar (i.e., the corpus-graduation gate only needs one metric to lift), Option 3.

**Adversarial angle for the meeting to press:**

- Who reads the spike report? If it's just the platform team + AB-028 sign-off, Option 2 is enough. If it's external audit (SOC 2 / regulatory review), Option 1 is worth the overhead.

---

## §D. Sign-off checklist mapping (v0.2 — restructured to expose conditionality)

For each agenda §D checklist item, this memo provides a position + explicit lock preconditions + failure mode if the precondition isn't met. `[x]` boxes replaced with structured columns after Codex round-1 flagged that the v0.1 `[x]` obscured that most items had unmet conditions.

| Item | Memo position | Required to lock | Owner (to identify in-meeting) | Failure mode if unmet |
|------|---------------|------------------|--------------------------------|-----------------------|
| **B1 thresholds** | Provisional Option 1 (reasoning-from-principles) | Prospective power analysis on real data; benchmark citation for 0.10 ECE OR minuted acceptance as reviewer-proposed | ML methodology reviewer (unnamed) | NOT APPROVED on B1 → meeting reduces to Option 2 (amend margins) or Option 3 (single primary) |
| **B2 rules** | Provisional Option 1 conditional on SRE consultation | Named `webhook-gateway prod` SRE approves list OR names missing rules | SRE lead (unnamed) | NOT APPROVED on B2 → dated deferral (§B1/B3/B4 can still lock) |
| **B3 features** | **Blocking discrepancy — no recommendation** | RFC↔code parity matrix (§B3.1) green: all Missing/Semantic-mismatch/Undeclared rows resolved | RFC drafter + harness author | NOT APPROVED on B3 → matrix work happens pre-meeting or meeting defers B3 |
| **B4 volume** | Option 2 (adjourn, run real-data pass) | Real EventLoaders exist (see A3 unmet); prospective power analysis extended to CI-width simulation | Spike execution owner + platform SRE for API access | Option 2 IS the position; the "lock" is a deferred sub-meeting |
| **C1** | Option 1 (drop FPR ceiling) + empirical binding pre-condition | Metadata pass output confirms FPR redundant with precision + warnings-per-week across threshold range | Metadata pass runner | Retain FPR ceiling (Option 3) with empirical binding rationale minuted |
| **C2** | Option A if owner produces artifacts; Option B if no owner exists anywhere; dated deferral if owner exists but artifacts require research | Written severity-weight source AND reduction-bar source with cost calculation | On-call cost model owner (unnamed; check `#sre-oncall` / director-level) | Option B (retreat to `TO BE LOCKED` placeholders) OR dated §C2 deferral |
| **C3** | Option 2 (simplify to CI-non-zero) subject to autocorrelation check | Autocorrelation analysis on metadata pass output justifying IID bootstrap | Metadata pass runner | Option 1 (retain block bootstrap) if events are correlated at block scale |
| **Spike execution owner** | Memo cannot recommend | Named engineer accepts §7 deliverables + §9 timeline | Meeting produces | APPROVED impossible per agenda §A A4 |
| **Timeline sign-off** | Memo defers; RFC §9 indicative | Meeting confirms or revises §9 dates against owner's actual capacity | Spike execution owner (once named) | Revision noted at RFC §11 |
| **AB-030 status** | ✔ Confirmed shipped (PR #22 v0.1.0) | — | — | — |
| **AB-033 status** | ✔ Confirmed merged as PR #16 | — | — | — |

**Notes:**

- Items with "unnamed" owners require the meeting to produce a name (or a channel/role pointer) before the item can lock — per agenda §D "a name attached" requirement.
- Failure-mode column shows what the meeting outcome becomes if the precondition is not met — this is the operational meaning of "the memo picked X but Y wasn't there."

---

## §E. Meeting-outcome scenarios per this memo (v0.2 — corrected against agenda §0)

Agenda §0 defines three outcomes: APPROVED (every §A/§B/§C decision locked in-meeting), APPROVED WITH DEFERRALS (§A + §B locked; one or more §C items on a dated deferral clock), NOT APPROVED (RFC needs material revision).

v0.1 said "the outcome is APPROVED with B2 may-reopen, B4 conditional, C2 depends" — that's a category error: those conditional states disqualify from APPROVED per agenda §0. v0.2 maps memo positions to correct outcome labels:

**Scenario S1 — best case (all memo preconditions met in-meeting):**
- Named SRE approves B2 rule list → B2 locks
- RFC↔code parity matrix arrives green pre-meeting → B3 locks (or matrix resolved in-meeting on small deltas)
- Real EventLoaders + power analysis have already run → B4 flips back to modified Option 1 and locks
- Named on-call cost model owner produces severity + reduction-bar artifacts → C2 Option A locks
- **Outcome: APPROVED.** Every §A/§B/§C item locked.

**Scenario S2 — memo's baseline expectation (most preconditions unmet in-meeting):**
- B2 SRE input landed as a probe but SRE explicitly wants a shift-follow-up before committing → B2 dated deferral
- B3 parity matrix identifies residual items requiring code changes → B3 dated deferral
- B4 stays at Option 2 (adjourn, run real pass) → B4 explicitly reopens the meeting on volume
- C2 owner named but artifacts pending → C2 dated deferral (or Option B fallback)
- C3 autocorrelation check pending → C3 dated deferral
- **Outcome: APPROVED WITH DEFERRALS** on the §B items — technically this requires per agenda §0 that §B are locked; if 2+ §B items are deferred, the outcome becomes NOT APPROVED. Meeting decides how many §B deferrals are tolerable.

**Scenario S3 — no domain input arrives:**
- B2 SRE absent + B3 parity matrix not run + B4 no real data + C2 no owner → 4+ items unresolved
- **Outcome: NOT APPROVED.** Meeting produces a revision brief for a future v0.3 attempt.

**Rubber-stamp check:** if the meeting adopts every memo recommendation without pushback, it has rubber-stamped a single reviewer's opinions — the exact failure mode agenda §0 warns against. The reviewer authoring this memo does not have SRE domain knowledge for §B2, has not seen the real metadata output for §B4, and cannot identify the operating-model owner for §C2. Those three items in particular MUST see live debate — and the memo's provisional/blocking/conditional positions on them are DESIGNED to force debate rather than allow silent assent.

---

## Provenance

- **2026-07-31:** v0.1 draft. Written as a companion to `AB-028_SCOPING_APPROVAL_AGENDA.md` after PR #25 (metadata pass tool) shipped and made §A3 tractable. Purpose: give the meeting a straw-doc to react to instead of a blank page, while preserving the agenda's challenge-don't-confirm structure. Not reviewed by the meeting chair. Not a decision doc.
- **2026-08-02:** v0.1 → v0.2 lift. Codex round-1 loop on this memo (audit trail at `research/feedback_loops/dynamic-reliability-AB-028_SCOPING_APPROVAL_REVIEWER_MEMO/20260802T102431Z/` — repo-ignored, per corpus convention) returned `needs-revision` with 16 findings (10 HIGH / 6 MEDIUM). Empirical verification pass performed against `adapters.py` / `features.py` / `metadata_window.py` / `metrics.py` before disposition; all major Codex claims about repo state verified true. 8 findings applied directly; 3 refined pre-apply during second-look over-concession audit (H1 folded into per-§B edits; H3/H5 softened from "no recommendation" to "provisional with epistemic caveat" to preserve straw-doc role); 1 misattributed (M6 rule-list discrepancy — Codex framed as memo bug; empirical check showed AGENDA is stale, memo matches RFC; agenda-side fix in same PR); 1 GAP-added (M7 rule-aggregation probe). 0 disagreements. Structural changes: **§A A3 status `✔` → `◐ Partial` with 7-item unmet-check list** (empirical check: only `SyntheticEventLoader` exists in `adapters.py`; no Terraform/DataDog loaders); **§B1 language softened** ("defensible" and "typical calibration targets" removed as unsourced; epistemic status "reasoning-from-principles" added; power-analysis pre-condition for lock; M4 Option 3 semantic fix); **§B2 provisional Option 1 conditional on SRE consultation** with agenda-staleness callout + rule-aggregation probe; **§B3 changed to "blocking discrepancy — no recommendation"** with new §B3.1 RFC↔code parity matrix (empirical check: RFC §4.3 lists create/update/destroy counts + current active-incident count NOT in `features.py`; code adds `is_friday_pm`/`recent_incidents_24h` NOT in RFC); **`assert_no_lookahead_for` downgraded to "synthetic-stream sanity check"** (docstring: "Sanity check used by tests"); **§B4 flipped v0.1 Option 1 → v0.2 Option 2** (real data pass required; count projection ≠ power analysis per `metadata_window.py::ProjectedModelingWindow` inspection); **§C1 empirical binding pre-condition added** (retain FPR ceiling if it binds independently); **§C2 owner must produce written artifacts** (not just be named); **§C3 implementation-cost claim corrected** (block bootstrap already implemented in `metrics.py:193-221`; Option 2 requires REPLACEMENT not addition); **§D checklist restructured** as conditionality-aware table with lock preconditions + owners + failure modes; **§E outcome scenarios rewritten** with 3 scenarios mapped to agenda §0 outcome labels (v0.1 mislabeled conditional-heavy state as APPROVED). Second-look over-concession audit performed pre-apply (93.75% → 87.5% AGREE ratio after 3 refinements catching Codex's memo-role-vs-authority-role confusion). Agenda-side coordinated fix: `AB-028_SCOPING_APPROVAL_AGENDA.md` §B2 line 58 rule list updated to match RFC §5.1 (previously described stale deploy-hour / rollback-recent / error-rate-recent / cross-service-dependency set).
