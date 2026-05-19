---
name: error-analysis
vendor: hamelsmu
slug: hamelsmu/error-analysis
source-url: https://github.com/hamelsmu/evals-skills/tree/main/skills/error-analysis
source-canonical: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/error-analysis
source-sha: febdb335bd658a01f756b8b5b3364277a4fa6a4a
audited: 2026-05-19
goal: 1
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1696
owner: adamatdevops
---

<!-- Source: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/error-analysis/SKILL.md · SHA: febdb335bd658a01f756b8b5b3364277a4fa6a4a · Audited: 2026-05-19 · **12th vendored skill + 3rd hamelsmu-vendor adoption + EXTENDS the cluster from 2 to 3 skills (first 3-skill cluster co-adoption in the framework)** (community vendor per AGENTS.md §4.4.1 known-community list; provenance 3 capped at axis maximum per §4.4.4). Single-file SKILL.md (no companion files; 1696 body tokens / 7925 body bytes after upstream YAML frontmatter strip per AGENT_SKILLS.md §2D body-extraction algorithm; full-file 1763 tokens / 8255 bytes). Tier 1 read-only + transform: SKILL.md L13-145 specifies READ ~100 LLM-pipeline traces + 7-step structured process (collect → read + pass/fail → categorize into 5-10 categories → label all traces → compute failure rates → decide fix-or-instrument per category → iterate) emitted as INLINE transcript content (failure-annotation tables per L47-56, category definitions, failure-rate computations) — NO file CREATE, NO file EDIT, NO shell-execute, NO skill-declared network egress. Per §J R3-A-3 create-vs-edit operation-surface doctrine: the Python snippet at L104-109 (`failure_rates = labeled_df[failure_columns].sum() / len(labeled_df); failure_rates.sort_values(ascending=False)`) is INLINE documentation showing the computation formula, NOT a runtime execution directive the agent applying §AJ executes (the user runs it in their preferred environment per L102 "spreadsheet / annotation app / simple script"); same pattern as §AH's JSON schema example at L109-114. FOURTH adoption (after §J + §AG + §AH) to MAINTAIN its eval-list pre-adoption Tier estimate; strengthens the inline-output-stays-Tier-1 provisional observation from §AG R1 B-R1-2 from 3 datapoints to 4 datapoints. **Cluster-coupling with §AG + §AH (EXTENDED pattern from 2-skill to 3-skill):** same upstream repo + same SHA `febdb33...` + same MIT LICENSE — first 3-skill cluster co-adoption in the framework. Completes the eval-methodology pipeline: §AJ (discover failure modes from traces) → §AG (audit eval-system design) → §AH (author binary judges for known failure modes). **First adopted-skill-to-adopted-skill internal reference in the framework**: SKILL.md L131 cites `write-judge-prompt` (now adopted as §AH) as the instrumentation path for failure modes warranting LLM-judge evaluators — codified at AGENTS.md §4.5.3 §AJ gate entry as the canonical §AJ → §AH pipeline chain. Two additional sister-skill forward references (`generate-synthetic-data` at L36; `build-review-interface` at L102) are UN-adopted advisory citations per AGENT_SKILLS.md §2E "Conditional load of an UN-adopted target" clause. Trace-sourcing escape-hatch rule (added at §AJ adoption): if user has NO traces available, §AJ is non-applicable until traces exist — agent surfaces `generate-synthetic-data` UN-adopted sister and either waits for sister adoption or proceeds inline with explicit user direction recorded as transcript note (defends against SKILL.md L159 anti-pattern "Brainstorming failure categories before reading traces"). NO `claude -p` subprocess paths, NO bundled subagents — §2E carve-outs (Bundled-script same-model self-invocation + same-model bounded-subagent) are both NON-APPLICABLE. Vendor concentration after §AJ: 4 ToB / 3 hamelsmu / 2 Anthropic / 1 OpenAI / 1 obra / 1 CodeRabbit = 4/12 = 33.3% ToB (drops from 36.4%); §J R3-B-2 ToB cluster gate remains INACTIVE under strict `>50%` rule. Body byte-identical to upstream verified via Python byte-compare (body sha256 `8243ee67f593fd7942f7e2724beabf485bf50b29b2af5ba05e3b812bf961f859`; 7925 body bytes; upstream blob SHA `ed2f60f6123aa635063b8f73647dc66c91c20254`). See AGENTS.md §4.5.3 §AJ entry + research/agents/evaluation_list.md §AJ Notes for full adoption decision record. -->

# Error Analysis

Guide the user through reading LLM pipeline traces and building a catalog of how the system fails.

## Overview

1. Collect ~100 representative traces
2. Read each trace, judge pass/fail, and note what went wrong
3. Group similar failures into categories
4. Label every trace against those categories
5. Compute failure rates to prioritize what to fix

## Core Process

### Step 1: Collect Traces

Capture the full trace: input, all intermediate LLM calls, tool uses, retrieved documents, reasoning steps, and final output.

**Target: ~100 traces.** This is roughly where new traces stop revealing new kinds of failures. The number depends on system complexity.

**From real user data (preferred):**
- Small volume: random sample
- Large volume: sample across key dimensions (query type, user segment, feature area)
- Use embedding clustering (K-means) to ensure diversity

**From synthetic data (when real data is sparse):**
- Use the generate-synthetic-data skill
- Run synthetic queries through the full pipeline and capture complete traces

### Step 2: Read Traces and Take Notes

Present each trace to the user. For each one, ask: **did the system produce a good result?** Pass or Fail.

For failures, note what went wrong. Focus on the **first thing that went wrong** in the trace — errors cascade, so downstream symptoms disappear when the root cause is fixed. Don't chase every issue in a single trace.

Write observations, not explanations. "SQL missed the budget constraint" not "The model probably didn't understand the budget."

**Template:**

```
| Trace ID | Trace | What went wrong | Pass/Fail |
|----------|-------|-----------------|-----------|
| 001      | [full trace] | Missing filter: pet-friendly requirement ignored in SQL | Fail |
| 002      | [full trace] | Proposed unavailable times despite calendar conflicts | Fail |
| 003      | [full trace] | Used casual tone for luxury client; wrong property type | Fail |
| 004      | [full trace] | - | Pass |
```

**Heuristics:**
- Do NOT start with a pre-defined failure list. Let categories emerge from what the user actually sees.
- If the user is stuck articulating what feels wrong, prompt with common failure types: made-up facts, malformed output, ignored user requirements, wrong tone, tool misuse.

### Step 3: Group Failures into Categories

After reviewing 30-50 traces, start grouping similar notes into categories. Don't wait until all 100 are done — grouping early helps sharpen what to look for in the remaining traces. The categories will evolve. The goal is names that are specific and actionable, not perfect.

1. Read through all the failure notes
2. Group similar ones together
3. Split notes that look alike but have different root causes
4. Give each category a clear name and one-sentence definition

**When to split vs. group:**

Split these (different root causes):
- "Made up property features (solar panels)" vs. "Made up client activity (scheduled a tour never requested)" — one fabricates external facts, the other fabricates user intent.

Group these (same root cause):
- "Missing bedroom count filter" + "Missing pet-friendly filter" + "Missing price range filter" → **Missing Query Constraints**

**LLM-assisted clustering** (use only after the user has reviewed 30-50 traces):

```
Here are failure annotations from reviewing LLM pipeline traces.
Group similar failures into 5-10 distinct categories.
For each category, provide:
- A clear name
- A one-sentence definition
- Which annotations belong to it

Annotations:
[paste annotations]
```

Always review LLM-suggested groupings with the user. LLMs cluster by surface similarity (e.g., grouping "app crashes" and "login is slow" because both mention login).

**Aim for 5-10 categories** that are:
- Distinct (each failure belongs to one category)
- Clear enough that someone else could apply them consistently
- Actionable (each points toward a specific fix)

### Step 4: Label Every Trace

Go back through all traces and apply binary labels (pass/fail) for each failure category. Each trace gets a column per category. Use whatever tool the user prefers — spreadsheet, annotation app (see build-review-interface), or a simple script.

### Step 5: Compute Failure Rates

```python
failure_rates = labeled_df[failure_columns].sum() / len(labeled_df)
failure_rates.sort_values(ascending=False)
```

The most frequent failure category is where to focus first.

### Step 6: Decide What to Do About Each Failure

Work through each category with the user in this order:

**Can we just fix it?** Many failures have obvious fixes that don't need an evaluator at all:
- The prompt never mentioned the requirement. Example: the LLM never includes photo links in emails because the prompt never asked for them. Add the instruction.
- A tool is missing or misconfigured. Example: the user wants to reschedule but there's no rescheduling tool exposed to the LLM. Add the tool.
- An engineering bug in retrieval, parsing, or integration. Fix the code.

If a clear fix resolves the failure, do that first. Only consider an evaluator for failures that persist after fixing.

**Is an evaluator worth the effort?** Not every remaining failure needs one. Building and maintaining evaluators has real cost. Ask the user:
- Does this failure happen frequently enough to matter?
- What's the business impact when it does happen? A rare failure that causes revenue loss may outrank a frequent failure that's merely annoying.
- Will this evaluator actually get used to iterate on the system, or is it checkbox work?

Reserve evaluators for failures the user will iterate on repeatedly. Start with the highest-frequency, highest-impact category.

**For failures that warrant an evaluator:** prefer code-based checks (regex, parsing, schema validation) for anything objective. Use write-judge-prompt only for failures that require judgment. Critical requirements (safety, compliance) may warrant an evaluator even after fixing the prompt, as a guardrail.

### Step 7: Iterate

Expect 2-3 rounds of reviewing and refining categories. After each round:
- Merge categories that overlap
- Split categories that are too broad
- Clarify definitions where the user would hesitate
- Re-label traces with the refined categories

## Stopping Criteria

Stop reviewing when new traces aren't revealing new kinds of failures. Roughly: ~100 traces reviewed with no new failure types appearing in the last 20. The exact number depends on system complexity.

## Trace Sampling Strategies

When production volume is high, use a mix:

| Strategy | When to Use | Method |
|----------|------------|--------|
| **Random** | Default starting point | Sample uniformly from recent traces |
| **Outlier** | Surface unusual behavior | Sort by response length, latency, tool call count; review extremes |
| **Failure-driven** | After guardrail violations or user complaints | Prioritize flagged traces |
| **Uncertainty** | When automated judges exist | Focus on traces where judges disagree or have low confidence |
| **Stratified** | Ensure coverage across user segments | Sample within each dimension |

## Anti-Patterns

- **Brainstorming failure categories before reading traces.** Read first, categorize what you find.
- **Starting with pre-defined categories.** A fixed list causes confirmation bias. Let categories emerge.
- **Skipping the user for initial review.** The user must review the first 30-50 traces to ground categories in domain knowledge.
- **Using generic scores as categories.** "Hallucination score," "helpfulness score," "coherence score" are not grounded in the application's actual failure modes.
- **Building evaluators before fixing obvious problems.** Fix prompt gaps, missing tools, and engineering bugs first.
- **Treating this as a one-time activity.** Re-run after every significant change: new features, prompt rewrites, model switches, production incidents.
