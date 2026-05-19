---
name: write-judge-prompt
vendor: hamelsmu
slug: hamelsmu/write-judge-prompt
source-url: https://github.com/hamelsmu/evals-skills/tree/main/skills/write-judge-prompt
source-canonical: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/write-judge-prompt
source-sha: febdb335bd658a01f756b8b5b3364277a4fa6a4a
audited: 2026-05-19
goal: 1
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1524
owner: adamatdevops
---

<!-- Source: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/write-judge-prompt/SKILL.md · SHA: febdb335bd658a01f756b8b5b3364277a4fa6a4a · Audited: 2026-05-19 · **11th vendored skill + 2nd hamelsmu-vendor adoption + sister/cluster co-adoption to §AG** (community vendor per AGENTS.md §4.4.1 known-community list; provenance 3). Single-file SKILL.md (no companion files; 1524 body tokens / 7263 body bytes after upstream YAML frontmatter strip per AGENT_SKILLS.md §2D body-extraction algorithm; full-file 1621 tokens / 7709 bytes; ~24% smaller than §AG's SKILL.md). Tier 1 read-only + transform: SKILL.md L13-145 specifies READ user-supplied failure mode + labeled traces + domain context, then OUTPUT a judge-prompt design composed of 4 canonical components (Task & Evaluation Criterion, Pass/Fail Definitions, Few-Shot Examples, Structured Output Format) emitted as INLINE transcript content — NO file CREATE, NO file EDIT, NO shell-execute, NO skill-declared network egress. Per §J R3-A-3 create-vs-edit operation-surface doctrine: the JSON schema example at L109-114 (`{"critique": "...", "result": "Pass or Fail"}`) is INLINE documentation showing the structured-output format the PRODUCED judge prompt will use at the user's eval-pipeline runtime, NOT a file-write directive emitted by the agent applying §AH. THIRD adoption (after §J + §AG) to MAINTAIN its eval-list pre-adoption Tier estimate; strengthens the inline-output-stays-Tier-1 provisional observation from §AG R1 B-R1-2 (2 datapoints → 3 datapoints) but still recorded as observational, NOT normative doctrine per the limited-sample caveat. **Cluster-coupling with §AG (NEW pattern):** same upstream repo + same SHA `febdb33...` + same MIT LICENSE — first "cluster co-adoption" in the framework where one source attests both skills; quarterly §4.4.5 review can verify both with a single upstream check. Cluster boundary: §AG audits existing judge prompts; §AH authors new ones; chain §AG → §AH when fixing identified design flaws (audit identifies; author corrects per the 4-component pattern). Two sister-skill forward references (`validate-evaluator` at L143 for judge calibration; `error-analysis` at L17 as workflow prerequisite) are advisory citations to UN-adopted targets; the agent MUST NOT auto-load any sister per AGENT_SKILLS.md §2E "Conditional load of an UN-adopted target" clause (codified at AGENTS.md §4.5.3 §AH entry). Code-based-check escape hatch (SKILL.md L19): the skill explicitly directs "Exhaust code-based options before reaching for a judge — many failure modes that seem subjective reduce to keyword checks, regex, or API calls when you understand the domain" — the agent MUST respect this preference and present code-based alternatives FIRST when applicable. Binary-only constraint (SKILL.md L38): outputs are strictly Pass/Fail; Likert scales / letter grades / numeric scores are explicitly forbidden by the skill's prerequisite — the agent applying §AH MUST reject Likert-style designs and counter-propose binary alternatives (multiple binary judges if severity capture is needed, per L142). NO `claude -p` subprocess paths, NO bundled subagents — §2E carve-outs (Bundled-script same-model self-invocation + same-model bounded-subagent) are both NON-APPLICABLE. Vendor concentration after §AH: 4 ToB / 2 Anthropic / 1 OpenAI / 1 obra / 1 CodeRabbit / 2 hamelsmu = 4/11 = 36.4% ToB (drops from 40%); §J R3-B-2 ToB cluster gate remains INACTIVE under strict `>50%` rule. Body byte-identical to upstream verified via Python byte-compare (body sha256 `12685e98f3a73d353160f84a9b1ef8ea240b8b09ced4a0f87d030ecaa53351b7`; 7263 body bytes; upstream blob SHA `573526caf372ec7cf3f7927502e0f4ae85b6e0ef`). See AGENTS.md §4.5.3 §AH entry + research/agents/evaluation_list.md §AH Notes for full adoption decision record. -->

# Write LLM-as-Judge Prompt

Design a binary Pass/Fail LLM-as-Judge evaluator for one specific failure mode. Each judge checks exactly one thing.

## Prerequisites

- Error analysis is complete. The failure mode is identified.
- You have human-labeled traces for this failure mode (at least 20 Pass and 20 Fail examples).
- A code-based evaluator cannot check this failure mode. Exhaust code-based options before reaching for a judge — many failure modes that seem subjective reduce to keyword checks, regex, or API calls when you understand the domain. Example: detecting whether an AI interviewing coach suggests "general" questions (asking about typical behavior instead of a specific past event) seems to require semantic understanding, but in practice a keyword check for words like "usually," "typical," and "normally" could work quite well.

## The Four Components

Every judge prompt requires exactly four components:

### 1. Task and Evaluation Criterion

State what the judge evaluates. One failure mode per judge.

```
You are an evaluator assessing whether a real estate assistant's email
uses the appropriate tone for the client's persona.
```

Not: "Evaluate whether the email is good" or "Rate the email quality from 1-5."

### 2. Pass/Fail Definitions

Outcomes are strictly binary: Pass or Fail. No Likert scales, no letter grades, no partial credit. Define exactly what constitutes Pass and Fail. These definitions come from your error analysis failure mode descriptions.

```
## Definitions

PASS: The email matches the expected communication style for the client persona:
- Luxury Buyers: formal language, emphasis on exclusive features, premium
  market positioning, no casual slang
- First-Time Homebuyers: warm and encouraging tone, educational explanations,
  avoids jargon, patient and supportive
- Investors: data-driven language, ROI-focused, market analytics, concise
  and professional

FAIL: The email uses a tone mismatched to the client persona. Examples:
- Using casual slang ("hey, check out this pad!") for a luxury buyer
- Using heavy financial jargon for a first-time homebuyer
- Using overly emotional language for an investor
```

### 3. Few-Shot Examples

Include labeled Pass and Fail examples from your human-labeled data.

```
## Examples

### Example 1: PASS
Client Persona: Luxury Buyer
Email: "Dear Mr. Harrington, I am pleased to present an exclusive listing
at 1200 Pacific Heights Drive. This distinguished property features..."
Critique: The email opens with a formal salutation and uses language
consistent with luxury positioning — "exclusive listing," "distinguished
property." No casual slang or informal phrasing. The tone matches the
luxury buyer persona throughout.
Result: Pass

### Example 2: FAIL
Client Persona: Luxury Buyer
Email: "Hey! Just found this awesome place you might like. It's got a
pool and stuff, super cool neighborhood..."
Critique: The greeting "Hey!" is informal. Phrases like "awesome place,"
"got a pool and stuff," and "super cool" are casual slang inappropriate
for a luxury buyer. The email reads like a text message, not a
professional communication for a high-end client.
Result: Fail

### Example 3: PASS (borderline)
Client Persona: First-Time Homebuyer
Email: "Hi Sarah, I found a property that might be a great fit for your
first home. The neighborhood has good schools nearby, and the monthly
payment would be similar to what you're currently paying in rent..."
Critique: The greeting is warm but not overly casual. The email explains
the property in relatable terms — comparing mortgage to rent, mentioning
schools — which is educational without being condescending. It avoids
jargon like "amortization" or "LTV ratio." While not deeply technical,
this matches the supportive tone expected for a first-time buyer.
Result: Pass
```

**Rules for selecting examples:**
- Include at least one clear Pass, one clear Fail, and one borderline case. Borderline examples are the most valuable — they teach nuance.
- Draw examples from the training split (10-20% of labeled data set aside for this purpose).
- Any example used in the judge prompt must be excluded from dev and test sets. Using dev/test examples is data leakage.
- 2-4 examples is typical. Performance plateaus after 4-8.

### 4. Structured Output Format

Enforce structured output using your LLM provider's schema enforcement (e.g., `response_format` in OpenAI, tool definitions in Anthropic) or a library like Instructor or Outlines. If the provider doesn't support schema enforcement, specify the JSON schema in the prompt.

The output must include a critique before the verdict. Placing the critique first forces the judge to articulate its assessment before committing to a decision.

```json
{
  "critique": "string — detailed assessment of the output against the criterion",
  "result": "Pass or Fail"
}
```

Critiques must be detailed, not terse. A good critique explains what specifically was correct or incorrect and references concrete evidence from the output. The critiques in your few-shot examples set the bar for the level of detail the judge will produce.

## Choosing What to Pass to the Judge

Feed only what the judge needs for an accurate decision:

| Failure Mode | What the Judge Needs |
|-------------|---------------------|
| Tone mismatch | Client persona + generated email |
| Answer faithfulness | Retrieved context + generated answer |
| SQL correctness | User query + generated SQL + schema |
| Instruction following | System prompt rules + generated response |
| Tool call justification | Conversation history + tool call + tool result |

For long documents, feed only the relevant snippet, not the entire document.

## Model Selection

Start with the most capable model available. The same model used for the main task works as judge (the judge performs a different, narrower task). Optimize for cost later once alignment is confirmed.

## Anti-Patterns

- **Vague criteria like "is this helpful?"** Target a specific, observable failure mode from error analysis.
- **Holistic judge for the entire trace.** A single judge covering multiple dimensions produces unactionable verdicts.
- **No few-shot examples.** Without examples, the model won't know what counts as a failure in your application.
- **Dev/test examples used as few-shot.** This is data leakage. Use only the training split.
- **Likert scales (1-5, letter grades, etc.).** Binary pass/fail only. Likert scales produce scores that sound precise but can't be calibrated: annotators disagree on the difference between a 3 and a 4, and the judge inherits that noise. Binary forces you to define a clear decision boundary upfront, which makes inter-annotator agreement measurable and the judge's errors actionable. If you need to capture severity, use multiple binary judges (e.g., "factually wrong" and "dangerously wrong") rather than one ordinal scale.
- **Skipping validation.** Measure alignment with human labels using validate-evaluator before trusting the judge.
- **Judges for specification failures without fixing the prompt first.** If the prompt never asked for the behavior, add the instruction before building an evaluator. For critical requirements, a judge can still serve as a regression guard.
