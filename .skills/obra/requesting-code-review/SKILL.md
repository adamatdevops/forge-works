---
name: requesting-code-review
vendor: obra
slug: obra/requesting-code-review
source-url: https://github.com/obra/superpowers/tree/main/skills/requesting-code-review
source-canonical: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/requesting-code-review
source-sha: f2cbfbefebbfef77321e4c9abc9e949826bea9d7
audited: 2026-05-20
goal: 1
tier: 2
tool-scope: shell-execute
target-agents: [claude-code, codex]
context-cost-tokens: 622
owner: adamatdevops
---

<!-- Source: https://github.com/obra/superpowers/tree/f2cbfbefebbfef77321e4c9abc9e949826bea9d7/skills/requesting-code-review/SKILL.md · SHA: f2cbfbefebbfef77321e4c9abc9e949826bea9d7 · Audited: 2026-05-20 · **30th vendored skill + 5th obra-cluster member + CLOSES §4.4.4 soft cap at 30/30 exactly + 14TH Tier 1→2 correction at adoption review per §4.4.3 step 2 v2 audit (N=22 staleness datapoints with 14 corrections + 3 deferrals + 5 confirm-Tier-1; correction rate ~64% — still FAR above 25% convergence threshold).** **Tier-staleness audit (per §4.4.3 step 2 v2 checklist):** (i-bis bundled-script sub-case FIRED): SKILL.md L18-19 prescribes `BASE_SHA=$(git rev-parse HEAD~1)` + `HEAD_SHA=$(git rev-parse HEAD)`; template L25-27 prescribes `git diff --stat {BASE_SHA}..{HEAD_SHA}` + `git diff {BASE_SHA}..{HEAD_SHA}`. Both are shell-execute mandates. (ii-bis bundled-sub-agent sub-case): YES — `code-reviewer.md` is a bundled sub-agent template (4802 bytes / 1076t); invoked via Task tool with `general-purpose` type (INLINE-GENERIC per §2E condition c carve-out — registry-named subagent type, no encoded content, bounded by single dispatch scope). (iii) NO bundled slash command. (iv) NO direct network egress in skill body. (v) NO cross-agent surface beyond §2E condition (c) bounded-subagent carve-out. **Final Tier 2 verdict for §BB requesting-code-review**: `shell-execute` — runs `git rev-parse`, `git diff`, `git diff --stat` via Bash to compute SHA range and produce diff for sub-agent review. NO repo-write (skill itself doesn't write artifacts; the dispatched reviewer returns inline transcript per §J R3-A-3 trichotomy; user/operator decides on fixes). **14TH Tier 1→2 correction** at adoption review — eval-list AC row implied Tier 1 (4/1 score), actual surface is Tier 2 because of `git rev-parse`/`git diff` shell mandates. **Sister-skill BOOKEND PAIR with §AU** receiving-code-review: §BB codifies REQUEST-SIDE methodology (compute SHAs + dispatch reviewer + act on feedback); §AU codifies RECEIVE-SIDE methodology (resist false consensus + identify-yes-bias + push back when wrong). LIFECYCLE PAIR mirrors §F (ask-questions-if-underspecified) → §AF (verification-before-completion). **obra cluster (5-skill EXTENSION):** §AF + §AM + §AU + §AV + §BB at shared SHA `f2cbfbef...`. obra cluster is SECOND-LARGEST after ToB (11). **6-of-7 vendor clusters span 6 distinct cluster sizes** post-§BB: 11/5/5/2/2/1 (ToB / hamelsmu / obra / Anthropic / CodeRabbit / OpenAI / phuryn-solo). **NEW worst-case-archive MINIMUM in framework**: 1698t archive (SKILL.md 622t + code-reviewer.md 1076t) — beats prior §AS minimum of 2539t by ~33%. SMALLEST Tier-2 in framework. **§2E condition (c) inline-generic same-model bounded-subagent carve-out APPLIED** — Task tool with `general-purpose` type is the INLINE-GENERIC pattern; no vendored or registry-named subagent type involved. **§AF + §AM + §AU + §AV gate entries BACKPATCHED in this commit** per §4.5.3 sister-reference status maintenance rule (4 gate entries — extends obra cluster gate-stack to 5). **Canonical lifecycle pairs (NEW)**: (1) §F → §AF (ask before start → verify before claim done); (2) §BB → §AU (request review → receive feedback). Two complete bookend pairs across framework. **AB-038 inverse-validation #6**: §BB eval-list rationale was content-grounded ("Codifies REQUEST-SIDE review methodology; bookend pair with receiving-code-review (§AU); already practiced via /codex-review slash command") — passed rationale-vs-content check cleanly. SIXTH content-grounded PASS event. **CLOSES §4.4.4 soft cap exactly at 30/30 active-adopted** — future adoptions require explicit attestation per §4.4.4 cap doctrine. **Bundle:** SKILL.md 666t full-file (622t body / 2649b post-frontmatter-strip per §2D; body sha256 partial match upstream) + 1 code-reviewer.md template (1076t) + LICENSE copied from cluster sibling. **Worst-case archive 1698 tokens** — NEW MINIMUM, well under §3B 5K-preferred cap. **Direct project fit for forge-works:** (1) **PR review prep** — codifies how to dispatch /codex-review with proper SHA range + plan/requirements + description; (2) **Pre-merge gate** — mandatory review before merge to main per upstream "Mandatory" use cases; (3) **Pairs with §AU** — REQUEST→RECEIVE lifecycle bookend; (4) **Integrates with §AT (gh-address-comments)** — request-review → receive-feedback → address-PR-comments end-to-end PR workflow. **Sister-skill cross-references:** SKILL.md body §Integration with Workflows references "Subagent-Driven Development" + "Executing Plans" (other obra cluster siblings — NOT adopted; UN-adopted-target gates filed for potential future adoption decision). **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §BB is Phase B from invocation start (runs `git rev-parse` immediately). Phase A NON-APPLICABLE — no inline-only path exists. Standard 3-option Tier 2 confirmation prompt fires at first invocation. **NO transitive `load skill X` refs, NO `claude -p` CLI subprocess paths, NO model-client invocations.** The §2E "Bundled-script same-model self-invocation" clause is NON-APPLICABLE (only bundled file is a prompt template, not a script). -->



# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code reviewer subagent:**

Use Task tool with `general-purpose` type, fill template at `code-reviewer.md`

**Placeholders:**
- `{DESCRIPTION}` - Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each task or at natural checkpoints
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: requesting-code-review/code-reviewer.md
