---
name: generate-synthetic-data
vendor: hamelsmu
slug: hamelsmu/generate-synthetic-data
source-url: https://github.com/hamelsmu/evals-skills/tree/main/skills/generate-synthetic-data
source-canonical: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/generate-synthetic-data
source-sha: febdb335bd658a01f756b8b5b3364277a4fa6a4a
audited: 2026-05-19
goal: 1
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1104
owner: adamatdevops
---

<!-- Source: https://github.com/hamelsmu/evals-skills/tree/febdb335bd658a01f756b8b5b3364277a4fa6a4a/skills/generate-synthetic-data/SKILL.md · SHA: febdb335bd658a01f756b8b5b3364277a4fa6a4a · Audited: 2026-05-19 · **14th vendored skill + 5th hamelsmu-vendor adoption + EXTENDS the cluster from 4 to 5 skills (first 5-skill cluster co-adoption in the framework AND completes the full hamelsmu/evals-skills candidate set)** (community vendor per AGENTS.md §4.4.1 known-community list; provenance 3 capped at axis maximum). Single-file SKILL.md (no companion files; 1104 body tokens / 4985 body bytes after upstream YAML frontmatter strip per AGENT_SKILLS.md §2D body-extraction algorithm; full-file 1196 tokens / 5427 bytes; **SMALLEST single-file Tier 1 skill in the cluster** — ~36% smaller than §AG's 1696 body tokens). Tier 1 read-only + transform: SKILL.md L13-129 specifies READ application description + failure hypotheses + existing traces, then guides the user through 6-step synthetic-data-generation process (define dimensions → draft 20 tuples with user → generate more tuples with LLM → convert tuples to natural-language queries → filter for quality → run queries through pipeline) emitted as INLINE transcript content (dimension definitions, tuple lists, LLM-prompt scaffolds, query-filtering decisions, stratified-sampling tables) — NO file CREATE, NO file EDIT, NO shell-execute, NO skill-declared network egress. Step 6 instructs the USER to execute generated queries through their LLM pipeline; the agent applying §AL does NOT execute the queries. SIXTH adoption (after §J + §AG + §AH + §AJ + §AK) to MAINTAIN its eval-list pre-adoption Tier estimate; **EXCEEDS N≥5 elevation threshold** from §AG R1 B-R1-2 for the inline-output-stays-Tier-1 provisional observation — strong evidence for normative codification at next §4.4.5 quarterly review. **Cluster-coupling with §AG + §AH + §AJ + §AK (EXTENDED pattern from 4-skill to 5-skill + COMPLETES the cluster):** same upstream repo + same SHA `febdb33...` + same MIT LICENSE — first 5-skill cluster co-adoption in the framework AND §AL is the 5th and final skill in the upstream `hamelsmu/evals-skills` candidate set; cluster is now COMPLETE (no more sister adoptions possible from this repo). **Canonical PRECURSOR to §AJ** — closes the §AJ 0-trace mode UN-adopted-target gate (per §4.5.3 §AJ trace-sourcing rule backpatch) AND the §AG no-infrastructure path UN-adopted-target gate (per §4.5.3 §AG sister-reference status backpatch). THIRD adopted-skill-to-adopted-skill internal reference in the framework (after §AJ→§AH at §AJ L131 and §AK→§AH at §AK L5) — §AJ L36 → §AL canonical PRECURSOR direction. Extends the eval-methodology pipeline: §AL bootstrap synthetic → §AJ discover failures → §AH author judges → §AK validate judges (→ optionally §AG audit). **Vendor-concentration milestone**: hamelsmu becomes LARGEST vendor at 5/14 = 35.7%, overtaking ToB (4/14 = 28.6%) for the first time. **Dimension-discipline rules from upstream SKILL.md (codified as gates):** (i) failure-hypothesis-grounded dimensions; (ii) user-confirmed tuples required before LLM-augmented generation; (iii) two-step generation discipline (separate prompts for tuples vs queries); (iv) realism-filter required. **Anti-pattern enforcement rules (codified as gates):** (i) domain-realism guard for complex/structured domains; (ii) low-resource-language guard; (iii) realism-judgability requirement. **Output-volume mode distinction (parallel to §AJ trace-count + §AK sample-size):** bootstrap (10-29) / standard (30-99) / saturation (≥100) per SKILL.md L93 target. NO `claude -p` subprocess paths, NO bundled subagents — §2E carve-outs (Bundled-script same-model self-invocation + same-model bounded-subagent) are both NON-APPLICABLE. Body byte-identical to upstream verified via Python byte-compare (body sha256 `2200459349ecdcd5bdaaad60950f940c743d155e26d6cdc495445efda6045f5e`; 4985 body bytes; upstream blob SHA `37b8e12ceb020f0fdf7c9c8bf7f3d3fce3dd506f1dfecdc64c25f80c10130da2`). See AGENTS.md §4.5.3 §AL entry + research/agents/evaluation_list.md §AL Notes for full adoption decision record. -->

# Generate Synthetic Data

Generate diverse, realistic test inputs that cover the failure space of an LLM pipeline.

## Prerequisites

Before generating synthetic data, identify where the pipeline is likely to fail. Ask the user about known failure-prone areas, review existing user feedback, or form hypotheses from available traces. Dimensions (Step 1) must target anticipated failures, not arbitrary variation.

## Core Process

### Step 1: Define Dimensions

Dimensions are axes of variation specific to your application. Choose dimensions based on where you expect failures.

```
Dimension 1: [Name] — [What it captures]
  Values: [value_a, value_b, value_c, ...]

Dimension 2: [Name] — [What it captures]
  Values: [value_a, value_b, value_c, ...]

Dimension 3: [Name] — [What it captures]
  Values: [value_a, value_b, value_c, ...]
```

Example for a real estate assistant:

```
Feature: what task the user wants
  Values: [property search, scheduling, email drafting]

Client Persona: who the user serves
  Values: [first-time buyer, investor, luxury buyer]

Scenario Type: query clarity
  Values: [well-specified, ambiguous, out-of-scope]
```

Start with 3 dimensions. Add more only if initial traces reveal failure patterns along new axes.

### Step 2: Draft 20 Tuples with the User

A tuple is one combination of dimension values defining a specific test case. Present 20 draft tuples to the user and iterate until they confirm the tuples reflect realistic scenarios. The user's domain knowledge is essential here — they know which combinations actually occur and which are unrealistic.

```
(Feature: Property Search, Persona: Investor, Scenario: Ambiguous)
(Feature: Scheduling, Persona: First-time Buyer, Scenario: Well-specified)
(Feature: Email Drafting, Persona: Luxury Buyer, Scenario: Out-of-scope)
```

### Step 3: Generate More Tuples with an LLM

```
Generate 10 random combinations of ({dim1}, {dim2}, {dim3})
for a {your application description}.

The dimensions are:
{dim1}: {description}. Possible values: {values}
{dim2}: {description}. Possible values: {values}
{dim3}: {description}. Possible values: {values}

Output each tuple in the format: ({dim1}, {dim2}, {dim3})
Avoid duplicates. Vary values across dimensions.
```

### Step 4: Convert Each Tuple to a Natural Language Query

Use a separate prompt for this step. Single-step generation (tuples + queries together) produces repetitive phrasing.

```
We are generating synthetic user queries for a {your application}.
{Brief description of what it does.}

Given:
{dim1}: {value}
{dim2}: {value}
{dim3}: {value}

Write a realistic query that a user might enter. The query should
reflect the specified persona and scenario characteristics.

Example: "{one of your hand-written examples}"

Now generate a new query.
```

### Step 5: Filter for Quality

Review generated queries. Discard and regenerate when:
- Phrasing is awkward or unrealistic
- Content doesn't match the tuple's intent
- Queries are too similar to each other

Optional: use an LLM to rate realism on a 1-5 scale, discard below 3.

### Step 6: Run Queries Through the Pipeline

Execute all queries through the full LLM pipeline. Capture complete traces: input, all intermediate steps, tool calls, retrieved docs, final output.

**Target: ~100 high-quality, diverse traces.** This is a rough heuristic for reaching saturation (where new traces stop revealing new failure categories). The number depends on system complexity.

## Sampling Real User Data

When you have real queries available, don't sample randomly. Use stratified sampling:

1. **Identify high-variance dimensions** — read through queries and find ways they differ (length, topic, complexity, presence of constraints).
2. **Assign labels** — for small sets, with the user; for large sets, use K-means clustering on query embeddings.
3. **Sample from each group** — ensures coverage across query types, not just the most common ones.

When both real and synthetic data are available, use synthetic data to fill gaps in underrepresented query types.

## Anti-Patterns

- **Unstructured generation.** Prompting "give me test queries" without the dimension/tuple structure produces generic, repetitive, happy-path examples.
- **Single-step generation.** Generating tuples and queries in one prompt produces less diverse results than the two-step separation.
- **Arbitrary dimensions.** Dimensions that don't target failure-prone regions waste test budget.
- **Skipping user review of tuples.** Without the user validating tuples first, you can't judge whether LLM-generated tuples are realistic.
- **Synthetic data when no one can judge realism.** If no one can judge whether a synthetic trace is realistic, use real data instead.
- **Synthetic data for complex domain-specific content** (legal filings, medical records) where LLMs miss structural nuance.
- **Synthetic data for low-resource languages or dialects** where LLM-generated samples are unrealistic.
