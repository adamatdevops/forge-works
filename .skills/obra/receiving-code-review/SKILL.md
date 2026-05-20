---
name: receiving-code-review
vendor: obra
slug: obra/receiving-code-review
source-url: https://github.com/obra/superpowers/tree/main/skills/receiving-code-review
source-canonical: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/receiving-code-review
source-sha: f2cbfbefebbfef77321e4c9abc9e949826bea9d7
audited: 2026-05-20
goal: 1
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1469
owner: adamatdevops
---

<!-- Source: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/receiving-code-review/SKILL.md · SHA: f2cbfbefebbfef77321e4c9abc9e949826bea9d7 · Audited: 2026-05-20 · **23rd vendored skill + 3rd obra-vendor adoption (after §AF verification-before-completion + §AM systematic-debugging) + EXTENDS obra cluster from 2 to 3 skills (§AF + §AM + §AU at shared SHA `f2cbfbef...`, THIRD member of the obra cluster) + TWELFTH consecutive Tier 1 estimate-confirm at adoption review (eval-list pre-adoption Tier-1 estimate HELD per new §4.4.3 step 2 audit — second consecutive Tier-1 estimate-correct adoption when Tier-1 was the eval-list pre-adoption estimate; N=15 staleness datapoints with 11 corrections + 3 deferrals + 1 confirm-Tier-1; pattern starting to show estimate-correct trend for non-Tier-2 candidates) + SECOND AB-036 candidate-resolution event filed in this same commit (testing-anti-patterns → test-driven-development consolidation discovered during this adoption's proactive AB-036 follow-up audit per the AB-036 doctrine).** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **NO file-write directives** — grep'd SKILL.md for `Save|Write the|Create a file|Output to|writes? to|mkdir` returned ZERO; the methodology is pure prose about HOW to receive code review feedback; (ii) NO `allowed-tools` frontmatter (upstream YAML has only `name` + `description` — same pattern as §AM); (iii) NO `commands/` directory; (iv) **NO direct network egress** — the only network reference is SKILL.md L205 "When replying to inline review comments on GitHub, reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment" which is a USER-RECOMMENDATION about HOW to format gh api replies (proper API endpoint to use), NOT an agent-execution directive — same pattern as §J's `uv add` recommendations + §M's bash diagnostic examples. The agent applying §AU does NOT run `gh api` itself; it provides guidance to the user. If the user explicitly requests the agent to post the reply, that's a SEPARATE invocation of §AR (CodeRabbit-specific) or §AT (generic PR-comment handling) — the right skill at that point. (v) NO `Task` tool / cross-agent surface declared. **Final Tier 1 verdict for §AU receiving-code-review**: `read-only` — pure methodology emitting inline-transcript content (Response Pattern at L16-25, Forbidden Responses at L29-38, Source-Specific Handling at L59-86, YAGNI Check at L88-98, Implementation Order at L100-111, Push-Back guidance at L113-129, Common Mistakes table at L165-174, Real Examples at L176-201). Per the inline-output-stays-Tier-1 normative rule codified at 2026-Q2 §4.4.5 (per Codex §AG R1 B-R1-2 elevation), §AU qualifies — emits process guidance + counter-argument patterns + acknowledgment templates as inline transcript content; no file CREATE/EDIT/shell/network. **TWELFTH adoption to maintain Tier 1 estimate** (after §J/§AG/§AH/§AJ/§AK/§AL/§AM + the inline-output normative elevation; §AU is the SECOND post-normative Tier 1 confirm-without-correction after §AM). **Obra cluster EXTENSION (FIRST 3-skill obra cluster):** §AF + §AM + §AU share repo `obra/superpowers` + SHA `f2cbfbef...` — THIRD member of the obra cluster, cluster grows 2→3. Per §4.4.5 cluster-co-adoption note, quarterly source-SHA review MAY use ONE shared upstream check covering all 3 obra skills (each Decision Record still independently attested). **§AF + §AM gate entries BACKPATCHED in this commit** per §4.5.3 sister-reference status maintenance rule (codified at §AK): both §AF and §AM were previously 2-skill cluster siblings; now have §AU as third cluster member. **§AF + §AM Ordering basis backpatch (per §4.5.5 later-sibling rule):** obra cluster sequence §AF `1bbde5c` (2026-05-16) → §AM `<am-sha>` (2026-05-20 earlier) → §AU `<TBD>` (2026-05-20 later). **6-of-6 vendor clusters now extended (cluster-co-adoption pattern proven at scale across vendor sizes):** hamelsmu 5-skill / ToB 7-skill / **obra 3-skill (NEW SIZE — third-largest cluster)** / CodeRabbit 2 / Anthropic 2 / OpenAI 2 — empirically validated across 6 vendor profiles + 6 cluster sizes (5, 7, 3, 2, 2, 2) + 6 Tier-mix shapes (hamelsmu all-Tier-1 / ToB mixed Tier-1+Tier-2 / **obra all-Tier-1 NOW (was Tier-1+Tier-1; §AU is also Tier 1 → still all-Tier-1)** / CodeRabbit all-Tier-3 / Anthropic Tier-2+Tier-2 / OpenAI Tier-2+Tier-2). STRONGEST evidence yet for 2026-Q3 normative elevation of the §4.4.5 cluster-co-adoption rule from provisional to normative. **Sister-skill cross-references:** ZERO direct cross-references to other adopted skills (the only adjacency is the obra cluster co-adoption at shared SHA — distinct skills with distinct workflows; §AF is verify-before-completion, §AM is systematic-debugging, §AU is receiving-code-review). **AB-036 candidate-resolution event #2 (filed inline in eval-list as part of THIS adoption commit, validating the AB-036 doctrine in production for the SECOND time):** `testing-anti-patterns` (eval-list line 182, ✅ score 4) was CONSOLIDATED INTO `test-driven-development` on 2025-12-18 (commit `718ec45d3358` — "Integrate testing-anti-patterns into test-driven-development", same consolidation day as root-cause-tracing → systematic-debugging that triggered AB-036 originally). The standalone `skills/testing-anti-patterns/` path NO LONGER EXISTS at obra/superpowers `main` OR at §AF/§AM/§AU's SHA `f2cbfbef...`. **AB-036 doctrine VALIDATED for the SECOND time** — at AB-036 filing (during §AM adoption), the obra candidates testing-anti-patterns + receiving-code-review were flagged as proactive consolidation-check candidates; the proactive check during §AU adoption discovered exactly the predicted consolidation event for testing-anti-patterns (and confirmed receiving-code-review still exists standalone). This is the strongest possible validation of the AB-036 doctrine in practice — the proactive check predicted the right consolidation event class on a NEW skill at the SAME consolidation date. **AB-036 doctrine refinement (NEW)**: the 2025-12-18 obra/superpowers commit consolidated MULTIPLE skills simultaneously (root-cause-tracing → systematic-debugging + testing-anti-patterns → test-driven-development). Future quarterly reviews should grep eval-list for ALL obra candidates whose paths predate 2025-12-18 + grep upstream for consolidation events on that date or later. **`test-driven-development` (the testing-anti-patterns consolidation target) is itself an UN-adopted sister of §AM** (referenced at §AM SKILL.md L179 + L287 as `superpowers:test-driven-development`) and now ALSO the testing-anti-patterns consolidation successor. Recommended for next-session adoption as §AV to fully resolve AB-036 candidate #2 (the path is `skills/test-driven-development/` containing SKILL.md 9867 bytes + `testing-anti-patterns.md` 8251 bytes as a consolidated component file — SAME pattern as systematic-debugging containing root-cause-tracing.md). Direct project fit for forge-works: TDD discipline applies to backend pytest + frontend vitest test authoring; complements §AS webapp-testing (Playwright E2E) by adding unit-test discipline + §AM systematic-debugging (Phase 4 Step 1 "Create Failing Test Case") by adding the formal TDD workflow. The cluster would extend to 4-skill obra cluster (§AF + §AM + §AU + §AV) and continue exercising the cluster-co-adoption normative-elevation case. **Bundle:** SKILL.md 1513t full-file (1469t body, 6029b post-frontmatter-strip per §2D canonical algorithm; body sha256 `6385a196f86e3fe6...`) + LICENSE byte-identical to §AF/§AM (same repo + SHA). **Worst-case archive 1513 tokens** — well under §3B 5K-preferred cap; SECOND-smallest Tier-1 single-file bundle after §F ask-questions (884t). **NO transitive `load skill X` refs, NO bundled subagents, NO `claude -p` CLI subprocess paths, NO model-client invocations, NO companion files** — single-file SKILL.md with LICENSE only. The §2E "Bundled-script same-model self-invocation" clause and the §2E same-model bounded-subagent carve-out are both **non-applicable** (no scripts, no subagents). **Direct project fit for forge-works:** §AU pairs naturally with §AR coderabbitai/autofix + §AT openai/gh-address-comments + §H differential-review in the PR-review-receiving workflow — §AU provides the METHODOLOGY (how to evaluate review feedback technically vs performatively), §AR/§AT provide the EXECUTION (applying selective fixes from PR comments). Canonical chain when receiving PR review feedback: §AU evaluate-feedback-methodology → §AR (if CodeRabbit) OR §AT (if generic) for execution → §AF verification-before-completion when declaring fixes shipped. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 1:** §AU is read-only methodology — NO Phase-A/Phase-B gate (no shell-execute, no repo-write, no network); per AGENTS.md §3.2 advisory-only, agent emits process guidance + counter-argument patterns as inline transcript content; user reviews via reading the agent's response. No neutral 3-option prompt required. -->


# Code Review Reception

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**NEVER:**
- "You're absolutely right!" (explicit CLAUDE.md violation)
- "Great point!" / "Excellent feedback!" (performative)
- "Let me implement that now" (before verification)

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

## Handling Unclear Feedback

```
IF any item is unclear:
  STOP - do not implement anything yet
  ASK for clarification on unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

**Example:**
```
your human partner: "Fix 1-6"
You understand 1,2,3,6. Unclear on 4,5.

❌ WRONG: Implement 1,2,3,6 now, ask about 4,5 later
✅ RIGHT: "I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Source-Specific Handling

### From your human partner
- **Trusted** - implement after understanding
- **Still ask** if scope unclear
- **No performative agreement**
- **Skip to action** or technical acknowledgment

### From External Reviewers
```
BEFORE implementing:
  1. Check: Technically correct for THIS codebase?
  2. Check: Breaks existing functionality?
  3. Check: Reason for current implementation?
  4. Check: Works on all platforms/versions?
  5. Check: Does reviewer understand full context?

IF suggestion seems wrong:
  Push back with technical reasoning

IF can't easily verify:
  Say so: "I can't verify this without [X]. Should I [investigate/ask/proceed]?"

IF conflicts with your human partner's prior decisions:
  Stop and discuss with your human partner first
```

**your human partner's rule:** "External feedback - be skeptical, but check carefully"

## YAGNI Check for "Professional" Features

```
IF reviewer suggests "implementing properly":
  grep codebase for actual usage

  IF unused: "This endpoint isn't called. Remove it (YAGNI)?"
  IF used: Then implement properly
```

**your human partner's rule:** "You and reviewer both report to me. If we don't need this feature, don't add it."

## Implementation Order

```
FOR multi-item feedback:
  1. Clarify anything unclear FIRST
  2. Then implement in this order:
     - Blocking issues (breaks, security)
     - Simple fixes (typos, imports)
     - Complex fixes (refactoring, logic)
  3. Test each fix individually
  4. Verify no regressions
```

## When To Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Legacy/compatibility reasons exist
- Conflicts with your human partner's architectural decisions

**How to push back:**
- Use technical reasoning, not defensiveness
- Ask specific questions
- Reference working tests/code
- Involve your human partner if architectural

**Signal if uncomfortable pushing back out loud:** "Strange things are afoot at the Circle K"

## Acknowledging Correct Feedback

When feedback IS correct:
```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
❌ "Thanks for [anything]"
❌ ANY gratitude expression
```

**Why no thanks:** Actions speak. Just fix it. The code itself shows you heard the feedback.

**If you catch yourself about to write "Thanks":** DELETE IT. State the fix instead.

## Gracefully Correcting Your Pushback

If you pushed back and were wrong:
```
✅ "You were right - I checked [X] and it does [Y]. Implementing now."
✅ "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing."

❌ Long apology
❌ Defending why you pushed back
❌ Over-explaining
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |
| Can't verify, proceed anyway | State limitation, ask for direction |

## Real Examples

**Performative Agreement (Bad):**
```
Reviewer: "Remove legacy code"
❌ "You're absolutely right! Let me remove that..."
```

**Technical Verification (Good):**
```
Reviewer: "Remove legacy code"
✅ "Checking... build target is 10.15+, this API needs 13+. Need legacy for backward compat. Current impl has wrong bundle ID - fix it or drop pre-13 support?"
```

**YAGNI (Good):**
```
Reviewer: "Implement proper metrics tracking with database, date filters, CSV export"
✅ "Grepped codebase - nothing calls this endpoint. Remove it (YAGNI)? Or is there usage I'm missing?"
```

**Unclear Item (Good):**
```
your human partner: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.
✅ "Understand 1,2,3,6. Need clarification on 4 and 5 before implementing."
```

## GitHub Thread Replies

When replying to inline review comments on GitHub, reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment.

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Verify. Question. Then implement.

No performative agreement. Technical rigor always.
