---
name: systematic-debugging
vendor: obra
slug: obra/systematic-debugging
source-url: https://github.com/obra/superpowers/tree/main/skills/systematic-debugging
source-canonical: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/systematic-debugging
source-sha: f2cbfbefebbfef77321e4c9abc9e949826bea9d7
audited: 2026-05-20
goal: 1
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 2303
owner: adamatdevops
---

<!-- Source: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/systematic-debugging/SKILL.md · SHA: f2cbfbefebbfef77321e4c9abc9e949826bea9d7 · Audited: 2026-05-20 · **15th vendored skill + 2nd obra-vendor adoption (FIRST obra cluster co-adoption — §AF + §AM share repo `obra/superpowers` + SHA `f2cbfbef...`; second cluster after hamelsmu and ToB) + Author: Jesse Vincent (obra), known-community per AGENTS.md §4.4.1 + FIRST adoption to surface upstream-consolidation candidate-resolution event (filed as AB-036 — upstream consolidated `root-cause-tracing/` INTO `systematic-debugging/` on 2025-12-18 commit `5845b527`; the original eval-list candidate path no longer exists at upstream `main`; this adoption pins the canonical successor)**. Bundle: 12 files = SKILL.md + 3 referenced .md companions (root-cause-tracing.md → SKILL.md L114, defense-in-depth.md → L283, condition-based-waiting.md → L284) + 1 referenced TS example (condition-based-waiting-example.ts) + 1 user-utility script (find-polluter.sh — bash bisection tool, NOT referenced from SKILL.md; vendored for provenance) + 4 QA pressure-test scaffolds (test-pressure-1/2/3.md, test-academic.md — designed to evaluate agent compliance with methodology, NOT load-bearing for agent operation) + 1 meta-documentation (CREATION-LOG.md) + LICENSE. **§AGENT_SKILLS.md §2D body-extraction algorithm:** SKILL.md body 2303 tokens / 9743 bytes post-frontmatter-strip; full-file 2330 tokens / 9884 bytes; body sha256 `24eaf14d2d4aa053efa03a219ab77c4d7d4ccee0a1900124d2940fe47a040cb5`. **Bundle worst-case archive: 9737 tokens** (SKILL.md 2330 + root-cause-tracing.md 1315 + defense-in-depth.md 818 + condition-based-waiting.md 847 + condition-based-waiting-example.ts 1195 + find-polluter.sh 460 + test-pressure-1/2/3.md 449+582+601 + test-academic.md 140 + CREATION-LOG.md 1000) — exceeds §3B 5K-preferred cap but well under hard limits; QA pressure-test files (test-pressure-*.md, test-academic.md) and meta-doc (CREATION-LOG.md) sum to ~2772 tokens and are load-on-demand only (not auto-loaded with SKILL.md). Acknowledged per §3B archive-load metering. **Tier 1 read-only** per the new §4.4.3 step 2 Tier-staleness audit checklist (codified 2026-05-20 at 2026-Q2 §4.4.5): (i) NO explicit file-write directives in SKILL.md body — grep'd `Save|Write the|Create a file|Output to|writes? to` returned ZERO matches; (ii) NO `allowed-tools` frontmatter (SKILL.md upstream YAML has only `name` + `description`); (iii) NO network egress (no curl/fetch/POST); (iv) NO cross-agent invocation directives (no "ask GPT-4" / "invoke <model-X>"); (v) Embedded bash snippets at SKILL.md L90-106 (echo/security/codesign) are USER-FACING DIAGNOSTIC EXAMPLES showing what the user would emit, NOT agent-execution directives — same pattern as §J's `uv add` recommendations. The 4-phase methodology (Root Cause → Pattern → Hypothesis → Implementation) emits inline transcript content (process guidance + diagnostic prompts) — no file CREATE / EDIT / shell-execute / network. **Inline-transcript-output Tier 1 (normative since 2026-Q2 §4.4.5):** SKILL.md emits 4-phase process guidance + Iron Law + Red Flags catalog + Rationalizations table — all inline transcript content; SEVENTH adoption to maintain Tier 1 estimate (after §J/§AG/§AH/§AJ/§AK/§AL; first since the elevation to normative this quarter). **`find-polluter.sh` script audit per §4.4.3 step 1 Codex Round-2 R2-2 hardening:** 63-line bash, uses `set -e`, runs `find` + `npm test` + `ls` (process spawns); NO `claude`/`anthropic` invocations; NO env-var-indirected commands; NO model-client SDK imports. SKILL.md does NOT reference or direct execution of `find-polluter.sh` — the script is a USER UTILITY for test-pollution bisection (analogous to §J's `dependabot.yml` + `pre-commit-config.yaml` inert templates). Per §2E "Bundled-script same-model self-invocation" clause: NON-APPLICABLE (no model-client invocation; script is user-runnable, not agent-runnable per SKILL.md direction). **`condition-based-waiting-example.ts` audit:** 5054-byte TypeScript file is referenced from `condition-based-waiting.md` (L?-? — referenced as "see condition-based-waiting-example.ts for full implementation"); pure example code (no executable script frontmatter; not invoked at runtime by agent). **Three cross-skill references in SKILL.md:** (a) L179 + L287 `superpowers:test-driven-development` — UN-adopted at upstream (path `skills/test-driven-development/` exists on `obra/superpowers/main` but not in our framework; advisory citation per AGENT_SKILLS.md §2E "Conditional load of an UN-adopted target" clause; the agent MUST NOT auto-load); (b) L288 `superpowers:verification-before-completion` — **ALREADY ADOPTED as §AF** (FOURTH adopted-skill-to-adopted-skill internal reference in the framework after §AJ→§AH, §AK→§AH, §AL→§AJ; FIRST cross-cluster reference where both skills are in the SAME repo at the SAME SHA — both `obra/superpowers` @ `f2cbfbef...`; codified as canonical §AM → §AF SUCCESSOR chain: §AM Phase 4 Step 1 "Verify Fix" workflow chains to §AF "verify don't claim shipped" doctrine when the fix is being declared complete). **Cluster-co-adoption pattern (SECOND in framework after hamelsmu's 5-skill cluster):** obra cluster now contains 2 skills (§AF + §AM) at shared SHA `f2cbfbef...`; per §4.4.5 cluster-co-adoption note, quarterly source-SHA review for obra cluster MAY be executed as ONE shared upstream check, BUT each skill's Decision Record MUST still be independently attested (rule was elevated to normative-elevation-candidate at 2026-Q2 §4.4.5; obra cluster is the SECOND empirical datapoint after hamelsmu's 5-skill cluster). **§AF sister-reference status backpatch (per §4.5.3 maintenance rule codified at §AK):** §AF's previously-solo obra-vendor entry is BACKPATCHED in this commit to acknowledge §AM as the cluster sibling at shared SHA. **§AF Ordering basis backpatch (per §4.5.5 later-sibling rule):** §AF's Ordering basis line is BACKPATCHED in this commit to reflect the 2-skill obra sequence: §AF `1bbde5c` (2026-05-16 audit date) → §AM `<TBD>` (2026-05-20 audit date). **§J R3-A-3 file-CREATE escalation NON-APPLICABLE:** SKILL.md emits no Write tool calls + no file-creation directives; the Quick Reference table at L260-265 and Common Rationalizations table at L247-256 are inline ASCII/markdown scaffolds the agent emits as transcript content (per the inline-transcript trichotomy codified 2026-05-20 at §4.4.5 quarterly review). **AB-036 candidate-resolution event (filed 2026-05-20 in eval-list, gitignored):** the original eval-list candidate `root-cause-tracing` (Notes line 181, ✅ score 5) was consolidated upstream INTO `systematic-debugging` on 2025-12-18; eval-list Notes column needs update to reflect: (a) `root-cause-tracing` standalone path no longer exists; (b) methodology lives on at `systematic-debugging`; (c) the candidate row's Goal §1 score of 5 transfers to `systematic-debugging` cleanly + score axes remain valid. Filing AB-036 establishes the FIRST upstream-consolidation candidate-resolution doctrine — future quarterly reviews should grep eval-list for any candidates whose upstream paths have been consolidated, renamed, or removed. -->


# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   **WHEN system has multiple components (CI → build → signing, API → service → database):**

   **BEFORE proposing fixes, add diagnostic instrumentation:**
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   **Example (multi-layer system):**
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)

5. **Trace Data Flow**

   **WHEN error is deep in call stack:**

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique.

   **Quick version:**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code in same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing pattern, read reference implementation COMPLETELY
   - Don't skim - read every line
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?
   - What assumptions does it make?

### Phase 3: Hypothesis and Testing

**Scientific method:**

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Write it down
   - Be specific, not vague

2. **Test Minimally**
   - Make the SMALLEST possible change to test hypothesis
   - One variable at a time
   - Don't fix multiple things at once

3. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

4. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for help
   - Research more

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - Automated test if possible
   - One-off test script if no framework
   - MUST have before fixing
   - Use the `superpowers:test-driven-development` skill for writing proper failing tests

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the architecture (step 5 below)**
   - DON'T attempt Fix #4 without architectural discussion

5. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new shared state/coupling/problem in different place
   - Fixes require "massive refactoring" to implement
   - Each fix creates new symptoms elsewhere

   **STOP and question fundamentals:**
   - Is this pattern fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we refactor architecture vs. continue fixing symptoms?

   **Discuss with your human partner before attempting more fixes**

   This is NOT a failed hypothesis - this is a wrong architecture.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 4.5)

## your human partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Supporting Techniques

These techniques are part of systematic debugging and available in this directory:

- **`root-cause-tracing.md`** - Trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** - Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** - Replace arbitrary timeouts with condition polling

**Related skills:**
- **superpowers:test-driven-development** - For creating failing test case (Phase 4, Step 1)
- **superpowers:verification-before-completion** - Verify fix worked before claiming success

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common
