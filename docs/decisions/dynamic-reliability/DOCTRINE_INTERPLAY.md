# Doctrine Interplay (v0) — How Predictions and Gates Coexist

> **Status:** Design stub (v0). Drafted 2026-07-24 in response to Codex round-1 loop findings F7 + F11 flagging that (a) requiring producer-owned disagreement signals inside every prediction was architecturally wrong, and (b) operator-vs-reviewer was the wrong primary doctrine axis.
> **Origin:** Sibling of `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` and `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md`. Referenced from PC §2, §4.5, §6.
> **Location note:** Migrated 2026-07-25 from `planning/DOCTRINE_INTERPLAY.md` to this tracked path — see `docs/decisions/dynamic-reliability/README.md` for the corpus index.
> **Scope:** the operational rules of the authority hierarchy; the decision-time arbitration envelope; how a T3/T4 decision authority composes a T1/T2 Dynamic Reliability prediction with T3/T4 reviewer-doctrine gate verdicts; policy versioning; doctrine-change process. Not a scoring policy (per-policy scoring is out of scope — this doc defines the *shape* the arbitration takes, not which policies are best).
> **Blocking status:** *(revised 2026-07-25 post-hoc dispositions review.)* This doc's v0→v1 progression is a **T3/T4 consumer prereq**, NOT a PC/SC v0→v1 blocker. In v0 predictions are advisory-only (no arbitration fires), so PC/SC can graduate without this doc reaching v1. AB-031 tracks completion (backlog entry local per repo convention; summary in the README).

---

## 1. Why this doc exists

Two doctrines exist inside ForgeWorks:

- **Reviewer doctrine** (T3/T4 in the authority hierarchy) — deterministic gates that already enforce decisions today: OWASP DC / Snyk / Checkov / CodeRabbit block deploys, prevent merges, fail CI. These have been operating for months. Their verdicts are load-bearing on shipping decisions.
- **Operator-adjacent doctrine** (T1/T2 in the authority hierarchy, v0 scope) — Dynamic Reliability predictions that describe probabilistic future outcomes. Advisory in v0; potentially informing T3/T4 decisions in v1+ under a per-class doctrine change.

These will disagree. That's not a bug — they measure different things (deterministic present-state facts vs. probabilistic future-state estimates). But someone has to compose them at decision time. Without a protocol:
- Consumers invent ad-hoc rules ("if the model disagrees with Snyk, trust Snyk") that fragment and drift.
- Predictions try to carry gate context (the original v0 design's error — Codex F7), which fails because gate verdicts are asynchronous and mutable.
- Humans see conflicting UI ("build blocked by Checkov" vs. "runtime predictor says stable") with no context for which to prioritize.

**The protocol has to make three things explicit:**

1. Which authority tier each surface operates at.
2. What the arbitration envelope looks like when a decision authority composes a prediction with gate verdicts.
3. How disagreement gets resolved: agreement / disagreement / undetermined / not-applicable, and what each state permits or blocks.

---

## 2. Authority hierarchy — operational rules per tier

Recap from SC §2 and PC §2, with per-tier operational implications:

### T1 — Evidence generation

**Authority:** none. Emits observations; no downstream authority.
**Examples:** vocabulary emission, prediction audit logs, anomaly-flag production, calibration measurements.
**Operating rules:**
- No arbitration envelope required (T1 doesn't make decisions).
- Consumers may filter/aggregate freely.
- Must carry governance envelope + provenance.

### T2 — Recommendation

**Authority:** none. Advises; decision authority stays elsewhere.
**Examples:** Slack digest with `at_risk` warnings, dashboard annotations, PR-comment suggestions, prioritized worklists.
**Operating rules:**
- Recommendations are *always visible*; they inform but never enforce.
- Consumers may act on them at their own authority tier (a human seeing the recommendation is a T3 human deciding).
- Must carry `policy_version` + `applicable_authority_tier` (per PC §4.5) so consumers know how far the recommendation is allowed to reach.
- No arbitration required for the recommendation itself; the surface consuming it may arbitrate internally.

### T3 — Human-approved decision

**Authority:** routine automation with human-in-loop for exceptions.
**Examples:** auto-approve-if-clean workflows where any exception requires human sign-off; auto-merge PRs that pass all gates AND a human has approved.
**Operating rules:**
- MUST compose an arbitration envelope before deciding (see §4).
- Human sign-off path required for any exception; identity of approver logged.
- Emits an intervention event (per GROUND_TRUTH_INTERVENTION_CONTRACT §6) recording the decision + arbitration state.

### T4 — Actuation

**Authority:** autonomous action, subject to explicit per-class doctrine approval.
**Examples:** auto-rollback, auto-scale, auto-block-deploy.
**Operating rules:**
- **NOT permitted in v0.** No T4 surfaces consume Dynamic Reliability predictions in v0. Existing T4 gates (Snyk on `main` push, etc.) that don't consume predictions continue to operate unchanged.
- MUST compose an arbitration envelope before actuating.
- Must carry counterfactual estimation method (per GROUND_TRUTH_INTERVENTION_CONTRACT §6.1) so treatment effect can be measured later.
- Doctrine change to enable a T4 predictor-informed class requires: RFC + AB-NNN + operating model attested + rollback authority named + circuit-breaker verified.

### Tier crossings — forbidden shapes

- A T1 emitter that a downstream T3/T4 consumer treats as ground truth: forbidden. T1 is evidence, not truth.
- A T2 recommendation consumed by a T4 automation without going through T3 first: forbidden in v0 (requires doctrine change).
- A T4 surface that produces T1 evidence about its own actions: **required** — every T4 actuation MUST emit an intervention event, which becomes T1 evidence for future calibration.

---

## 3. The arbitration envelope — shape

**Definition:** the structured object a T3 or T4 decision authority composes at *decision time* to compose predictions with gate verdicts and produce a decision.

**v0 shape:**

```yaml
arbitration_envelope_id: arb_<timestamp>_<hash>
composed_at: <iso8601>
composing_authority: <service_id or user_id>
authority_tier: <T3 | T4>
policy_version: <doctrine_version>
policy_envelope_shape: <named shape reference, e.g. deploy_time_arbitration_v1>

decision_subject:
  # what's being decided about
  slice: {per_service: ..., per_environment: ...}
  action_class: <e.g. deploy | merge | rollback>
  actor: <who requested the action>

prediction_references:
  # every prediction that informed this decision
  - prediction_id: <id>
    policy_version_at_emit: <doctrine version prediction was emitted under>
    applicable_authority_tier: <T1 | T2>
    read_at: <iso8601>
    value: <as-of-read snapshot>
    confidence_snapshot: <as-of-read snapshot per PC §4.1>

gate_references:
  # every deterministic gate whose verdict informed this decision
  - gate_id: <e.g. owasp_dc | snyk | checkov | code_rabbit>
    verdict: <pass | fail | not_applicable>
    verdict_at: <iso8601 when the verdict was determined>
    read_at: <iso8601 when the arbitration read the verdict>

applicability:
  # per input, is it applicable to THIS decision?
  # e.g., Snyk's dependency-scan verdict is applicable to a deploy, not applicable to a documentation-only merge
  - reference: <prediction_id or gate_id>
    applicable: <true | false>
    applicability_reason: <machine-readable classifier + optional human note>

agreement:
  # computed from applicable inputs only
  state: <agree | disagree | undetermined | no_applicable_inputs>
  breakdown:
    # per applicable input, what did it say
    - reference: <prediction_id or gate_id>
      says: <normalized {block | allow | at_risk | healthy}>

decision:
  outcome: <allow | block | conditional | defer_to_human>
  rationale_ref: <pointer to structured rationale>
  human_override_status: <not_required | required | applied>
```

**Key properties:**

- **Composition happens at decision time, not at prediction time.** Predictions and gates emit independently; the arbitration envelope is built fresh per decision by the decision authority.
- **Every input has an applicability decision.** A gate that fires on an unrelated concern (Snyk on a doc-only PR) is not applicable to the current decision even though it's fresh.
- **Agreement is computed from applicable inputs only.** Non-applicable inputs don't distort the agreement state.
- **Human override is a first-class outcome.** If the arbitration policy demands human sign-off, the envelope records whether it was requested + who applied it.

---

## 4. Composing an envelope — the decision-time flow

Reference implementation (any T3/T4 decision authority follows this):

1. **Read the current arbitration policy.** The policy names the input classes it cares about (predictions from which pools/estimands, gates from which tools) and the decision function.
2. **Fetch fresh inputs.** For each required prediction: query the projection (PC §5) for the current prediction on the target slice. For each required gate: query the gate's current verdict on the target subject.
3. **Determine applicability** per input against the current decision. Rules live in the arbitration policy, not per-consumer.
4. **Compute agreement state** across applicable inputs.
5. **Apply the decision function** — the policy's rule mapping (agreement × per-input verdicts × counterfactual constraints) → decision outcome.
6. **Determine human-override requirement** — some policies require human sign-off for `disagree` or `undetermined` states.
7. **Emit the arbitration envelope** to `forge.events.arbitration.v1` (proposed topic).
8. **Emit an intervention event** to the intervention stream (per GROUND_TRUTH_INTERVENTION_CONTRACT §6) recording the decision.
9. **Apply the decision** (allow / block / conditional).

**The whole flow is auditable.** Anyone asking "why was this deploy blocked?" or "why was this PR merged?" can retrieve the arbitration envelope and see: which predictions + gates were considered, which were applicable, what the policy said, what the human (if any) decided.

---

## 5. Agreement states — resolution rules

| State | Definition | Default decision | Override options |
|---|---|---|---|
| `agree` | All applicable inputs indicate the same action class (all `block` OR all `allow`). | Follow the agreed action. | Human override always available; audited. |
| `disagree` | Applicable inputs split — some `block`, some `allow`. | **Fail-closed** default: block. Alternative policies (fail-open for low-risk actions) require explicit policy version + doctrine approval. | Human override required (T3) or forbidden (T4 for high-risk classes) per policy. |
| `undetermined` | Not enough applicable inputs (e.g., a critical gate is `not_applicable` and no prediction covers the decision). | Fail-closed default; block until more evidence arrives. | Human override with rationale (audited). |
| `no_applicable_inputs` | All inputs deemed non-applicable to the current decision. | Fall back to the surface's default (may be `allow`). | This state is legitimate; not a bug. Common for edge-case decisions no gate covers. |

**Fail-closed as default doctrine:** disagreement blocks. Rationale: T4 automations acting on `disagree` risk are worse than a false block. The default can be overridden per action class + per policy — an action class like "documentation merge" may fail-open on `disagree` because the risk is trivial. Never fail-open by omission.

---

## 6. Policy versioning + doctrine change process

**Doctrine versioning:** every arbitration policy carries `policy_version` (semver). Predictions carry `policy_version` too (the doctrine version they were emitted under, per PC §4.5). Arbitration envelopes carry BOTH — the policy version of the arbitration itself, AND the policy version of each prediction it composes. Mismatched policy versions are audited but not automatically rejected (the arbitration policy decides what to do).

**Doctrine change process:**

1. **Propose** — an RFC / design doc naming the change, the motivation, the affected authority tiers, the affected action classes, the rollback plan.
2. **AB-NNN entry** — filed in `roadmap/AUTOMATIONS_BACKLOG.md` per the loop's discipline. Doctrine changes DO NOT skip backlog governance.
3. **Codex round** — non-optional for doctrine changes. The independence check is precisely the point.
4. **Attestation** — operating model per predictor + per gate + per action class (VOCABULARY §8 AP-7).
5. **Shadow run** — new doctrine runs in shadow (arbitration envelopes emitted but the decision is the OLD doctrine's) for a declared window (default 4 weeks).
6. **Human comparison audit** — humans review shadow arbitration envelopes against old-doctrine decisions.
7. **Cutover approval** — signed by the accountable owner.
8. **New doctrine version** — bumped, effective from an announced timestamp.
9. **Rollback authority** — named, reachable, exercised in a drill before cutover.

**Never:**
- Enable a new T3/T4 action class by config toggle.
- Silently version-bump an arbitration policy without the process above.
- Take a doctrine change to production without the shadow-run window.

---

## 7. Worked example — deploy-time arbitration

**Setup:** a T3 deploy-gating surface (v1+ scenario, since T3 predictor-informed decisions are out of scope for v0 — but showing the shape for design completeness). The surface decides whether to allow a deploy of `webhook-gateway prod` at deploy time.

**Inputs it queries:**
- Snyk verdict on the changed dependencies.
- Checkov verdict on the changed Terraform.
- OWASP DC verdict on the runtime image.
- Dynamic Reliability prediction (from the worked example in PC §10) — `at_risk` at 62%.

**Composed arbitration envelope:**

```yaml
arbitration_envelope_id: arb_2026-07-24T10:19:00Z_b8f2
composed_at: 2026-07-24T10:19:00Z
composing_authority: deploy-gate-service
authority_tier: T3
policy_version: deploy_arbitration_v1.2
policy_envelope_shape: deploy_time_arbitration_v1

decision_subject:
  slice: {per_service: webhook-gateway, per_environment: prod}
  action_class: deploy
  actor: git-push:8f3b21c

prediction_references:
  - prediction_id: pred_2026-07-24T10:15:03Z_a4f2b8
    policy_version_at_emit: doctrine-2026-07-24-shadow-mode-v0
    applicable_authority_tier: T2      # v0 predictions are T2-max
    read_at: 2026-07-24T10:19:00Z
    value: at_risk
    confidence_snapshot:
      class_probabilities: {healthy: 0.15, at_risk: 0.62, regressed: 0.23}
      ECE: 0.037

gate_references:
  - {gate_id: owasp_dc, verdict: pass, verdict_at: 2026-07-24T10:12:00Z, read_at: 2026-07-24T10:19:00Z}
  - {gate_id: snyk, verdict: pass, verdict_at: 2026-07-24T10:14:00Z, read_at: 2026-07-24T10:19:00Z}
  - {gate_id: checkov, verdict: pass, verdict_at: 2026-07-24T10:13:00Z, read_at: 2026-07-24T10:19:00Z}

applicability:
  - {reference: pred_2026-07-24T10:15:03Z_a4f2b8, applicable: false, applicability_reason: prediction_at_T2_exceeds_authority_tier_T3}
  - {reference: owasp_dc, applicable: true}
  - {reference: snyk, applicable: true}
  - {reference: checkov, applicable: true}

agreement:
  state: agree
  breakdown:
    - {reference: owasp_dc, says: allow}
    - {reference: snyk, says: allow}
    - {reference: checkov, says: allow}

decision:
  outcome: allow
  rationale_ref: rationale://arb_2026-07-24T10:19:00Z_b8f2
  human_override_status: not_required
```

**Notes on this example:**
- The prediction was marked NOT applicable — its `applicable_authority_tier: T2` doesn't reach up to a T3 deploy-gating decision. This is v0 behavior working as designed.
- All three gates agreed on `allow`, so the arbitration was `agree` → `allow`.
- The prediction is still visible in the audit trail; someone reviewing the deploy could see "the runtime predictor said `at_risk` at this deploy time but wasn't authorized to influence the decision" — this is the shadow-mode signal that feeds future doctrine-change decisions.

**Contrast (v1+ scenario):** if the same deploy happened AFTER a doctrine change that permitted T2-predictions to inform T3 deploy gates with a `warn + require_ack` policy, the same envelope would show:
- Prediction `applicable: true`.
- Agreement state: `disagree` (gates say `allow`, prediction says `at_risk`).
- Decision: `defer_to_human` — the deploy author gets a warn, must ack the risk before proceeding.

That's the shape a future v1+ doctrine change would take. The envelope structure doesn't change; only the applicability and the policy's decision function do.

---

## 8. Anti-patterns

**AP-D1: Producer-owned agreement.** A prediction that carries its own `agreement` field with gate verdicts (the old PC v0 design, Codex F7). Producer-owned agreement is stale by design. **Fix:** producer emits, arbitration composes at decision time.

**AP-D2: Implicit applicability.** A consumer that treats every input as applicable unless proven otherwise. **Fix:** applicability is explicit per input; the arbitration policy names the applicability rules per action class.

**AP-D3: Silent doctrine drift.** Changing arbitration policy without a version bump + shadow-run + attestation. **Fix:** the doctrine-change process (§6) is non-optional. CI checks enforce policy version presence on every arbitration envelope.

**AP-D4: Missing rationale reference.** Arbitration envelope without a `rationale_ref` — the decision was made but the reasoning wasn't recorded. **Fix:** `rationale_ref` required; consumers reject envelopes without one.

**AP-D5: Fail-open by default.** Setting `disagree` state to allow-through without explicit doctrine approval. **Fix:** fail-closed is the default; fail-open requires per-action-class doctrine + attestation.

**AP-D6: Rubber-stamp human overrides.** Human override applied without a written rationale, or applied by an actor without the authority per operating model. **Fix:** override requires rationale; overrider identity checked against operating-model authority.

---

## 9. Graduation criteria — v0 → v1

- [ ] Arbitration envelope schema at v0.
- [ ] Reference implementation (any T3 surface) demonstrated: reads gates + predictions, computes applicability, emits envelope + intervention event, applies decision.
- [ ] Fail-closed default doctrine documented and defaulted in the reference implementation.
- [ ] Doctrine-change process (§6) exercised end-to-end at least once for a low-risk change.
- [ ] `human_override_status` mechanism working: humans can apply overrides, overrides carry rationale + authority.
- [ ] `forge.events.arbitration.v1` stream live and consumed by at least one audit sink.
- [ ] AP-D1 through AP-D6 all have detection or prevention mechanisms in place.

---

## 10. Open questions

- [ ] **Arbitration policy language** — how are arbitration policies expressed? YAML rules? A small DSL? Real code (Python / Rego)? Trade-off: readable vs. expressive vs. auditable.
- [ ] **Policy storage** — where do arbitration policies live? Git-tracked (yes), but also read by the runtime — a policy service? Configmap? Static file? Different answers imply different rollout mechanics.
- [ ] **Cross-tenant arbitration** — a decision that spans tenants (e.g., a shared-service deploy affecting multiple customer tenants) — is that one envelope or one per tenant?
- [ ] **Envelope size ceiling** — an arbitration composing 20 predictions × 15 gates has 35 input references; envelope grows. Cap? Reference-by-projection (envelope carries only IDs, projection resolves)?
- [ ] **Retroactive arbitration audit** — a policy change reveals that past decisions would have been different under the new policy. Do we backfill? Emit "would-have-been" envelopes for historical decisions? Or just note the change in the policy history?
- [ ] **Interaction with existing branch protection** — GitHub branch protection is a T4 gate already in production. It doesn't consume arbitration envelopes. Do we wrap it, or leave it as an out-of-band gate that the arbitration policy references?

---

## 11. Related documents

- `docs/decisions/dynamic-reliability/PREDICTION_CONTRACT.md` *(v0.1)* — predictions carry `policy_version` + `applicable_authority_tier` (§4.5) so arbitration knows what tier they can reach.
- `docs/decisions/dynamic-reliability/DYNAMIC_RELIABILITY_SOURCE_CONTRACT.md` *(v0.1)* — authority hierarchy defined in §2; this doc is its operational extension.
- `docs/decisions/dynamic-reliability/GROUND_TRUTH_INTERVENTION_CONTRACT.md` *(drafted v0)* — every arbitration decision emits an intervention event to the intervention stream.
- `docs/decisions/dynamic-reliability/VOCABULARY_DESIGN.md` *(v0.1)* — §8 AP-7 operating model per predictor; this doc extends the concept to per-gate and per-action-class operating models.
- `planning/WIRE_PROTOCOL.md` — arbitration envelope serialization. Not yet drafted.
- `roadmap/AUTOMATIONS_BACKLOG.md` — AB-031 tracks this doc's lifecycle.

---

## 12. Iteration protocol

- Substantive changes bump `v0` → `v0.1` → `v0.2` → …
- Blocks PC v0 → v1 graduation until this doc reaches v0.
- Blocks every future T3/T4 doctrine-change RFC — the RFC MUST cite the arbitration policy shape defined here.
- On v1, content moves to `docs/decisions/DYNAMIC_RELIABILITY.md` alongside siblings.
