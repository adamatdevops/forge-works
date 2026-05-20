---
name: variant-analysis
vendor: trailofbits
slug: trailofbits/variant-analysis
source-url: https://github.com/trailofbits/skills/tree/main/plugins/variant-analysis/skills/variant-analysis
source-canonical: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/variant-analysis/skills/variant-analysis
source-sha: a56045e9ae00b3506cacefea0f672aab0a1a6e3c
audited: 2026-05-20
goal: 3
tier: 2
tool-scope: shell-execute+repo-write
target-agents: [claude-code, codex]
context-cost-tokens: 1170
owner: adamatdevops
---

<!-- Source: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/variant-analysis/skills/variant-analysis/SKILL.md · SHA: a56045e9ae00b3506cacefea0f672aab0a1a6e3c · Audited: 2026-05-20 · **25th vendored skill + 8th ToB-vendor adoption + EXTENDS ToB cluster from 7 to 8 skills (LARGEST cluster — 8/25 = 32.0% concentration) + ELEVENTH Tier 1→2 correction at adoption review per new §4.4.3 step 2 audit (N=17 staleness datapoints with 11 corrections + 3 deferrals + 3 confirm-Tier-1) + ADOPTED IMMEDIATELY POST-AB-038 (FIRST adoption after the AB-038 candidate-resolution event was filed for mattpocock/skills; AB-038 doctrine refinement codified TODAY around brand-vs-content rationale validation).** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **YES — implicit file-write directives:** the agent COPIES query templates from `resources/codeql/*.ql` + `resources/semgrep/*.yaml` to adapt them to specific bug patterns (file CREATE per §J R3-A-3 when writing the adapted query); the variant-report-template.md at L142 is also a copy-and-adapt template; (ii) NO `allowed-tools` frontmatter in SKILL.md (host's default tool envelope); **BUT the bundled `commands/variants.md` slash command DECLARES `allowed-tools: Read Grep Glob Bash Task`** — Bash + Task surfaces in the slash command (matches §AP semgrep precedent for bundled slash commands with Bash + Task); (iii) `commands/variants.md` IS present (bundled slash command — second framework-vendored slash command after AB-035 spec-to-code-compliance's deferred candidate; FIRST adopted-with-bundled-slash-command in the framework — at 25 adoptions); (iv) **shell-execute via ripgrep (`rg` at SKILL.md L40)** + Semgrep CLI + CodeQL CLI per Tool Selection table at L75-82; same gh-CLI-style mediated network pattern as §H; (v) `Task` declared in slash command's `allowed-tools` — TOOL-LEVEL cross-agent surface (same pattern as §AP semgrep). Per §AGENT_SKILLS.md §2E same-model bounded-subagent carve-out condition (b) vendored-named — the slash command itself is vendored at the audited SHA + tool grants are subset of typical agent envelope; carve-out applies → §AW is Tier 2 (not Tier 3). The slash command body is a thin wrapper that just "Invokes the variant-analysis skill for the full workflow" — Task tool may be reserved for future parallel-spawn use; the SKILL.md itself does NOT direct parallel Task spawns. **Final Tier 2 verdict for §AW variant-analysis**: `shell-execute+repo-write` — runs `rg`/`semgrep`/`codeql` via Bash + writes adapted query files via Write tool + writes variant-report.md via Write tool. Matches §AO codeql + §AP semgrep pattern. **Bundle:** SKILL.md 1221t full-file (1170t body / 5352b post-frontmatter-strip per §2D; body sha256 `3d2266c7fca6b969...`) + METHODOLOGY.md 2247t (companion methodology — strategic guidance referenced at SKILL.md L72 "For deeper strategic guidance, see METHODOLOGY.md") + variant-report-template.md 376t (report template at resources/) + 5 codeql/*.ql files (3131t total: cpp 931 + go 519 + java 576 + javascript 452 + python 653) + 5 semgrep/*.yaml files (2629t total: cpp 775 + go 462 + java 481 + javascript 425 + python 486) + commands/variants.md 115t (bundled slash command) + LICENSE byte-identical to other ToB skills. **Worst-case archive: 9719 tokens** — exceeds §3B 5K-preferred cap; the 10 query template files (~5760t combined) + METHODOLOGY.md (~2247t) are load-on-demand (agent reads them WHEN selecting a query template for the target language, NOT at SKILL.md ingest). Acknowledged per §3B archive-load metering. **ToB cluster (8-skill — LARGEST in framework, NEW SIZE CLASS):** §F + §G + §H + §J + §AN + §AO + §AP + §AW at shared SHA `a56045e9...` — ToB cluster grows 7→8 skills (NEW size class: 8-skill cluster, distinct from prior sizes 2/4/5/7). ToB concentration: 8/25 = **32.0%** (up from 29.2%); still below 50% gate. §J R3-B-2 ToB cluster gate remains INACTIVE under strict `>50%` rule. **6-of-6 vendor clusters now span 6 distinct cluster sizes** (5 / **8 NEW** / 4 / 2 / 2 / 2) — ToB extends to a NEW size class (8-skill). The size-class progression 2 → 3 → 4 → 5 → 7 → 8 now spans the framework's working range MORE DENSELY. STRONGEST evidence yet for 2026-Q3 normative elevation. **Direct project fit for forge-works:** post-CVE variant search across the codebase — DIRECT VALUE for Flink 1.20 → 2.0 upgrade (task #24 per eval-list: "After Flink 1.20 → 2.0 upgrade, find variants of patched patterns elsewhere"). Pairs naturally with §AO codeql (the bundled CodeQL query templates can be adapted then run via §AO) + §AP semgrep (Semgrep templates via §AP) + §AN sarif-parsing (SARIF output processing) + §H differential-review (PR-diff context). **Static-analysis sub-cluster relationships:** §AW is a METHODOLOGY skill that USES §AO + §AP as execution tools. Canonical chain: `<CVE patched> → §AW understand original issue + create exact-match pattern → §AW iteratively generalize (5-step process) → §AO codeql / §AP semgrep run the adapted query → §AN sarif-parsing process results → §AW Step 5 analyze + triage`. **Sister-skill cross-references in SKILL.md:** L22 `audit-context-building` (= §G ADOPTED), L24 `issue-writer` (UN-adopted — not in current framework), L25 `audit-context-building` (= §G again). The two §G references are now ADOPTED-sister citations; the `issue-writer` is UN-adopted advisory per §2E "Conditional load of an UN-adopted target" clause. **5-step process compactness:** SKILL.md presents the methodology as 5 numbered steps (Understand → Exact Match → Identify Abstraction Points → Iteratively Generalize → Analyze and Triage) with explicit STOP criterion ("Stop when false positive rate exceeds ~50%"). The discipline is well-bounded. **Critical Pitfalls section (L93-130)** enumerates 4 common mistakes: narrow search scope, pattern too specific, single vulnerability class, missing edge cases — each with example + mitigation. **Bundled slash command `commands/variants.md`:** thin wrapper (551 bytes) declaring `allowed-tools: Read Grep Glob Bash Task` + body "Invoke the `variant-analysis` skill for the full workflow." Slash command name `/trailofbits:variants` (per L2 `name: trailofbits:variants`). This is the FIRST ADOPTED-WITH-BUNDLED-SLASH-COMMAND skill in the framework — AB-035 spec-to-code-compliance was DEFERRED partly over bundled slash command + sub-agent + multi-skill bundle issues; §AW adopts a SIMPLER variant (single skill + slash command + no bundled sub-agent + no Python scripts) successfully. **NEW framework lift surfaced + flagged for §4.4.5 codification:** bundled slash command at `commands/<slug>.md` declaring `Bash` + `Task` is acceptable as part of a Tier 2 adoption WHEN the slash command body is a thin wrapper invoking the skill (not directly executing tools); the slash command's tool declarations apply to its OWN execution (which here is just skill-invocation). Future adopters with bundled slash commands MUST verify the slash command body is a thin wrapper (no direct tool execution) OR run a separate Tier audit on the command's actual workflow. **No vendored Python/shell scripts** (the 11 query template files are pure data — .ql + .yaml — NOT executable; agent copies them to adapt). The §2E "Bundled-script same-model self-invocation" clause is NON-APPLICABLE (no scripts at all). **Sub-cluster relationship to other ToB skills:** §F/§G/§H/§J are foundational (clarification / context-building / differential-review / Python tooling); §AN/§AO/§AP form the static-analysis 3-skill sub-cluster; §AW joins as the METHODOLOGY skill that PAIRS WITH §AO/§AP (variant search using their query engines). Canonical post-CVE chain: §H differential-review (patch context) → §G audit-context-building (deep understanding) → §AW variant-analysis (5-step search methodology + query templates) → §AO codeql / §AP semgrep (run adapted queries) → §AN sarif-parsing (process results) → §H differential-review (review variant findings for PR). **§AB-038 doctrine validation:** §AW adoption immediately after AB-038 filing for mattpocock/skills validates the AB-038 doctrine inversely — §AW's eval-list rationale ("Find variants of a known vulnerability across the codebase. High-leverage after any CVE patch (Flink 1.20 → 2.0 specifically)") was content-grounded, NOT brand-based (Trail of Bits is a brand BUT the rationale cites specific use cases not brand reputation). The rationale-vs-content check passed cleanly. AB-038 doctrine refinement: **brand-based rationale FAILS at content review (e.g., mattpocock); content-grounded rationale PASSES (e.g., §AW variant-analysis citing specific Flink-upgrade use cases)**. -->


# Variant Analysis

You are a variant analysis expert. Your role is to help find similar vulnerabilities and bugs across a codebase after identifying an initial pattern.

## When to Use

Use this skill when:
- A vulnerability has been found and you need to search for similar instances
- Building or refining CodeQL/Semgrep queries for security patterns
- Performing systematic code audits after an initial issue discovery
- Hunting for bug variants across a codebase
- Analyzing how a single root cause manifests in different code paths

## When NOT to Use

Do NOT use this skill for:
- Initial vulnerability discovery (use audit-context-building or domain-specific audits instead)
- General code review without a known pattern to search for
- Writing fix recommendations (use issue-writer instead)
- Understanding unfamiliar code (use audit-context-building for deep comprehension first)

## The Five-Step Process

### Step 1: Understand the Original Issue

Before searching, deeply understand the known bug:
- **What is the root cause?** Not the symptom, but WHY it's vulnerable
- **What conditions are required?** Control flow, data flow, state
- **What makes it exploitable?** User control, missing validation, etc.

### Step 2: Create an Exact Match

Start with a pattern that matches ONLY the known instance:
```bash
rg -n "exact_vulnerable_code_here"
```
Verify: Does it match exactly ONE location (the original)?

### Step 3: Identify Abstraction Points

| Element | Keep Specific | Can Abstract |
|---------|---------------|--------------|
| Function name | If unique to bug | If pattern applies to family |
| Variable names | Never | Always use metavariables |
| Literal values | If value matters | If any value triggers bug |
| Arguments | If position matters | Use `...` wildcards |

### Step 4: Iteratively Generalize

**Change ONE element at a time:**
1. Run the pattern
2. Review ALL new matches
3. Classify: true positive or false positive?
4. If FP rate acceptable, generalize next element
5. If FP rate too high, revert and try different abstraction

**Stop when false positive rate exceeds ~50%**

### Step 5: Analyze and Triage Results

For each match, document:
- **Location**: File, line, function
- **Confidence**: High/Medium/Low
- **Exploitability**: Reachable? Controllable inputs?
- **Priority**: Based on impact and exploitability

For deeper strategic guidance, see [METHODOLOGY.md](METHODOLOGY.md).

## Tool Selection

| Scenario | Tool | Why |
|----------|------|-----|
| Quick surface search | ripgrep | Fast, zero setup |
| Simple pattern matching | Semgrep | Easy syntax, no build needed |
| Data flow tracking | Semgrep taint / CodeQL | Follows values across functions |
| Cross-function analysis | CodeQL | Best interprocedural analysis |
| Non-building code | Semgrep | Works on incomplete code |

## Key Principles

1. **Root cause first**: Understand WHY before searching for WHERE
2. **Start specific**: First pattern should match exactly the known bug
3. **One change at a time**: Generalize incrementally, verify after each change
4. **Know when to stop**: 50%+ FP rate means you've gone too generic
5. **Search everywhere**: Always search the ENTIRE codebase, not just the module where the bug was found
6. **Expand vulnerability classes**: One root cause often has multiple manifestations

## Critical Pitfalls to Avoid

These common mistakes cause analysts to miss real vulnerabilities:

### 1. Narrow Search Scope

Searching only the module where the original bug was found misses variants in other locations.

**Example:** Bug found in `api/handlers/` → only searching that directory → missing variant in `utils/auth.py`

**Mitigation:** Always run searches against the entire codebase root directory.

### 2. Pattern Too Specific

Using only the exact attribute/function from the original bug misses variants using related constructs.

**Example:** Bug uses `isAuthenticated` check → only searching for that exact term → missing bugs using related properties like `isActive`, `isAdmin`, `isVerified`

**Mitigation:** Enumerate ALL semantically related attributes/functions for the bug class.

### 3. Single Vulnerability Class

Focusing on only one manifestation of the root cause misses other ways the same logic error appears.

**Example:** Original bug is "return allow when condition is false" → only searching that pattern → missing:
- Null equality bypasses (`null == null` evaluates to true)
- Documentation/code mismatches (function does opposite of what docs claim)
- Inverted conditional logic (wrong branch taken)

**Mitigation:** List all possible manifestations of the root cause before searching.

### 4. Missing Edge Cases

Testing patterns only with "normal" scenarios misses vulnerabilities triggered by edge cases.

**Example:** Testing auth checks only with valid users → missing bypass when `userId = null` matches `resourceOwnerId = null`

**Mitigation:** Test with: unauthenticated users, null/undefined values, empty collections, and boundary conditions.

## Resources

Ready-to-use templates in `resources/`:

**CodeQL** (`resources/codeql/`):
- `python.ql`, `javascript.ql`, `java.ql`, `go.ql`, `cpp.ql`

**Semgrep** (`resources/semgrep/`):
- `python.yaml`, `javascript.yaml`, `java.yaml`, `go.yaml`, `cpp.yaml`

**Report**: `resources/variant-report-template.md`
