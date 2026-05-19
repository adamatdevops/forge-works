---
name: eval-audit
vendor: hamelsmu
slug: hamelsmu/eval-audit
source-url: https://github.com/hamelsmu/evals-skills/tree/main/skills/eval-audit
source-canonical: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/eval-audit
source-sha: febdb335bd658a01f756b8b5b3364277a4fa6a4a
audited: 2026-05-19
goal: 3
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1970
owner: adamatdevops
---

<!-- Source: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/eval-audit/SKILL.md · SHA: febdb335bd658a01f756b8b5b3364277a4fa6a4a · Audited: 2026-05-19 · **10th vendored skill + 1st hamelsmu-vendor adoption + 1st eval-quality-methodology skill** (community vendor per AGENTS.md §4.4.1 known-community list; provenance 3). Single-file SKILL.md (no companion files; 1970 body tokens / 9505 body bytes after upstream YAML frontmatter strip per AGENT_SKILLS.md §2D body-extraction algorithm; full-file 2071 tokens / 9949 bytes). Tier 1 read-only + transform: SKILL.md L18-175 specifies READ artifacts + six diagnostic checks (error analysis, evaluator design, judge validation, human-review process, labeled data, pipeline hygiene) + inline Report Format at L164-175 — NO file CREATE, NO file EDIT, NO shell-execute, NO skill-declared network egress. Per §J R3-A-3 create-vs-edit operation-surface doctrine: the `Report Format` template at L168-173 is inline transcript content the agent emits as a chat response, NOT a file-write directive — file-CREATE Tier-2 escalation is NON-APPLICABLE. SECOND adoption (after §J) to MAINTAIN its eval-list pre-adoption Tier estimate; provisional observation (2 datapoints, heterogeneous workflow shapes; softened 2026-05-19 per Codex §AG R1 Section B Finding B-R1-2): skills whose primary deliverable is inline transcript output have so far remained Tier 1, while workflows requiring file CREATE have tended to escalate — recorded as observational, NOT normative doctrine. Seven sister-skill forward references (`error-analysis`, `generate-synthetic-data`, `write-judge-prompt`, `validate-evaluator`, `build-review-interface`, and implicitly `evaluate-rag` + `meta-skill` from the same upstream repo) are advisory citations to UN-adopted targets; the agent MUST NOT auto-load any sister per AGENT_SKILLS.md §2E "Conditional load of an UN-adopted target" clause (codified at AGENTS.md §4.5.3 §AG entry). Optional observability-MCP reads (Phoenix / Braintrust / LangSmith / Truesight at SKILL.md L28) use the USER's existing host MCP grants — NOT skill-declared egress; same pattern as §A's optional MCP integrations clause. NO `claude -p` subprocess paths, NO bundled subagents — §2E carve-outs (Bundled-script same-model self-invocation + same-model bounded-subagent) are both NON-APPLICABLE. Vendor concentration after §AG: 4 ToB / 2 Anthropic / 1 OpenAI / 1 obra / 1 CodeRabbit / 1 hamelsmu (new) = 4/10 = 40% ToB (drops from 44%); §J R3-B-2 ToB cluster gate remains INACTIVE under strict `>50%` rule. Body byte-identical to upstream verified via Python byte-compare (body sha256 `366a16f8e777e3326f52f4065e4036703590897b0b9bfe3076ef72c74a6486d1`; 9505 body bytes; upstream blob SHA `3f1fcbf5657db80bc613973b753071d6e9b0b563`). See AGENTS.md §4.5.3 §AG entry + research/agents/evaluation_list.md §AG Notes for full adoption decision record. -->

# Eval Audit

Inspect an LLM eval pipeline and produce a prioritized list of problems with concrete next steps.

## Overview

1. Gather eval artifacts: traces, evaluator configs, judge prompts, labeled data, metrics dashboards
2. Run diagnostic checks across six areas
3. Produce a findings report ordered by impact, with each finding linking to a fix

## Prerequisites

Access to eval artifacts (traces, evaluator configs, judge prompts, labeled data) via an observability MCP server or local files. If none exist, skip to "No Eval Infrastructure."

## Connecting to Eval Infrastructure

Check whether the user has an observability MCP server connected (Phoenix, Braintrust, LangSmith, Truesight or similar). If available, use it to pull traces, evaluator definitions, and experiment results. If not, ask for local files: CSVs, JSON trace exports, notebooks, or evaluation scripts.

## Diagnostic Checks

Work through each area below. Inspect available artifacts, determine whether the problem exists, and record a finding if it does.

Prioritize findings by impact on the user's product. Present the most impactful findings first.

### 1. Error Analysis

**Check:** Has the user done systematic error analysis on real or synthetic traces?

Look for: labeled trace datasets, failure category definitions, notes from trace review. If evaluators exist but no documented failure categories, error analysis was likely skipped.

**Finding if missing:** Evaluators built without error analysis measure generic qualities ("helpfulness", "coherence") instead of actual failure modes. Start with `error-analysis`, or `generate-synthetic-data` first if no traces exist.

See: [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/index.html), [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)

**Check:** Were failure categories brainstormed or observed?

Generic labels borrowed from research ("hallucination score", "toxicity", "coherence") suggest brainstorming. Application-grounded categories ("missing query constraints", "wrong client tone", "fabricated property features") suggest observation.

**Finding if brainstormed:** Generic categories miss application-specific failures and produce evaluators that score well on paper but miss real problems. Re-do with `error-analysis`, starting from traces.

See: [Who Validates the Validators?](https://arxiv.org/abs/2404.12272)

### 2. Evaluator Design

**Check:** Are evaluators binary pass/fail?

Flag any that use Likert scales (1-5), letter grades (A-F), or numeric scores without a clear pass/fail threshold.

**Finding if not binary:** Likert scales are difficult to calibrate. Annotators disagree on the difference between a 3 and a 4, and judges inherit that noise. Consider converting to binary pass/fail with explicit definitions using `write-judge-prompt`.

See: [Creating an LLM Judge That Drives Business Results](https://hamel.dev/blog/posts/llm-judge/)

**Check:** Do LLM judge prompts target specific failure modes?

Flag any that evaluate holistically ("Is this response helpful?", "Rate the quality of this output").

**Finding if vague:** Holistic judges produce unactionable verdicts. Each judge should check exactly one failure mode with explicit pass/fail definitions and few-shot examples. Use `write-judge-prompt`.

**Check:** Are code-based checks used where possible?

Flag LLM judges used for objectively checkable criteria: format validation, constraint satisfaction, keyword presence, schema conformance.

**Finding if over-relying on judges:** Replace objective checks with code (regex, parsing, schema validation, execution tests). Reserve LLM judges for criteria requiring interpretation.

**Check:** Are similarity metrics used as primary evaluation?

Flag ROUGE, BERTScore, cosine similarity, or embedding distance used as the main evaluator for generation quality.

**Finding if present:** These metrics measure surface-level overlap, not correctness. They suit retrieval ranking but not generation evaluation. Replace with binary evaluators grounded in specific failure modes.

See: [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)

### 3. Judge Validation

**Check:** Are LLM judges validated against human labels?

Look for: confusion matrices, TPR/TNR measurements, alignment scores. Judges in production with no validation data is a critical finding.

**Finding if unvalidated:** An unvalidated judge may consistently miss failures or flag passing traces. Measure alignment using TPR and TNR on a held-out test set. Use `validate-evaluator`.

See: [Creating an LLM Judge That Drives Business Results](https://hamel.dev/blog/posts/llm-judge/)

**Check:** Is alignment measured with TPR/TNR or with raw accuracy?

Flag "accuracy", "percent agreement", or Cohen's Kappa as the primary alignment metric.

**Finding if using accuracy:** With class imbalance, raw accuracy is misleading: a judge that always says "Pass" gets 90% accuracy when 90% of traces pass but catches zero failures. Use TPR and TNR, which map directly to bias correction. Use `validate-evaluator`.

**Check:** Is there a proper train/dev/test split?

Check whether few-shot examples in judge prompts come from the same data used to measure judge performance.

**Finding if leaking:** Using evaluation data as few-shot examples inflates alignment scores and hides real judge failures. Split into train (few-shot source), dev (iteration), and test (final measurement). Use `validate-evaluator`.

### 4. Human Review Process

**Check:** Who is reviewing traces?

Determine whether domain experts or outsourced annotators are labeling data.

**Finding if outsourced without domain expertise:** General annotators catch formatting errors but miss domain-specific failures (wrong medical dosage, incorrect legal citation, mismatched property features). Involve a domain expert.

See: [A Field Guide to Improving AI Products](https://hamel.dev/blog/posts/field-guide/)

**Check:** Are reviewers seeing full traces or just final outputs?

**Finding if output-only:** Reviewing only the final output hides where the pipeline broke. Show the full trace: input, intermediate steps, tool calls, retrieved context, and final output.

**Check:** How is data displayed to reviewers?

Flag raw JSON, unformatted text, or spreadsheets with trace data in cells.

**Finding if raw format:** Reviewers spend effort parsing data instead of judging quality. Format in natural representation: render markdown, syntax-highlight code, display tables as tables. Use `build-review-interface`.

See: [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)

### 5. Labeled Data

**Check:** Is there enough labeled data?

For error analysis, ~100 traces is the rough target for saturation. For judge validation, ~50 Pass and ~50 Fail examples are needed for reliable TPR/TNR. If labeled data is sparse, collect more by sampling traces more effectively:

- **Random:** Always include a random sample alongside other strategies to discover unknown issues.
- **Clustering:** Group traces by semantic similarity and review representatives from each cluster.
- **Data analysis:** Analyze statistics on latency, turns, tool calls, and tokens for outliers.
- **Classification:** Use existing evals, a predictive model, or an LLM to surface problematic traces. Use with caution.
- **Feedback:** Use explicit customer feedback (complaints, thumbs-down signals) to filter traces.

**Finding if insufficient:** Small datasets produce unreliable failure rates and wide confidence intervals. Use the sampling strategies above to collect more labeled data, or supplement with `generate-synthetic-data`.

### 6. Pipeline Hygiene

**Check:** Is error analysis re-run after significant changes?

Check when error analysis was last performed relative to model switches, prompt rewrites, new features, or production incidents.

**Finding if stale:** Failure modes shift after pipeline changes, and evaluators built for the old pipeline miss new failure types. Re-run error analysis after every significant change.

**Check:** Are evaluators maintained?

Look for periodic re-validation of judges or refreshed evaluation datasets.

**Finding if set-and-forget:** Evaluators degrade as the pipeline evolves. Re-validate judges against fresh human labels and update eval datasets to reflect current usage.

## No Eval Infrastructure

If the user has no eval artifacts (no traces, no evaluators, no labeled data):

1. Start with `error-analysis` on a sample of real traces.
2. If no production data exists, use `generate-synthetic-data` to create test inputs, run them through the pipeline, then apply `error-analysis` to the resulting traces.
3. Do not recommend building evaluators, judges, or dashboards before completing error analysis.

## Report Format

Present findings ordered by impact. For each:

```
### [Problem Title]
**Status:** [Problem exists / OK / Cannot determine]
[1-2 sentence explanation of the specific problem found]
**Fix:** [Concrete action, referencing a skill or article]
```

Group under the six diagnostic areas. Omit areas where no problems were found.

## Anti-Patterns

- Running the audit as a checklist without inspecting actual artifacts.
- Reporting generic advice disconnected from what was found in the user's pipeline.
- Recommending evaluators before error analysis is complete.
- Suggesting LLM judges for failures that code-based checks can handle.
- Treating this audit as a one-time event. Re-audit after significant pipeline changes.
