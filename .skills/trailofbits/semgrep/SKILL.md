---
name: semgrep
vendor: trailofbits
slug: trailofbits/semgrep
source-url: https://github.com/trailofbits/skills/tree/main/plugins/static-analysis/skills/semgrep
source-canonical: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/static-analysis/skills/semgrep
source-sha: a56045e9ae00b3506cacefea0f672aab0a1a6e3c
audited: 2026-05-20
goal: 3
tier: 2
tool-scope: shell-execute+repo-write
target-agents: [claude-code, codex]
context-cost-tokens: 2198
owner: adamatdevops
---

<!-- Source: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/static-analysis/skills/semgrep/SKILL.md · SHA: a56045e9ae00b3506cacefea0f672aab0a1a6e3c · Audited: 2026-05-20 · **18th vendored skill — third of THREE simultaneous adoptions from the trailofbits/static-analysis multi-skill plugin bundle (§AN sarif-parsing + §AO codeql + §AP semgrep). See §AN sarif-parsing Notes for full bundle audit + AB-037 candidate-resolution event narrative; this Notes paragraph is the §AP semgrep specifics.** **Tier-staleness audit + cross-agent surface analysis (per new §4.4.3 step 2 + §AGENT_SKILLS.md §2E same-model bounded-subagent carve-out):** (i) **YES — file-write directives at SKILL.md L48-62**: `mkdir -p $OUTPUT_DIR/raw $OUTPUT_DIR/results` (creates output directory), scan output to `$OUTPUT_DIR/raw/<lang>-<ruleset>.{json,sarif}`, merged result at `$OUTPUT_DIR/results/results.sarif` via `merge_sarif.py` script. **File CREATE → Tier 2 per §J R3-A-3.** (ii) `allowed-tools: Bash Read Glob Task AskUserQuestion TaskCreate TaskList TaskUpdate` — `Bash` (shell-execute) + `Task` (cross-agent host tool) declared; (iii) NO `commands/` directory; (iv) **YES — network egress**: Semgrep CLI fetches rulesets from `semgrep.dev/p/<ruleset>` registry (skill mandates `--metrics=off` at L20 to suppress telemetry, but rule-fetching is still network), AND `references/rulesets.md` references GitHub-URL rulesets (`https://github.com/trailofbits/semgrep-rules`, `https://github.com/0xdea/semgrep-rules`, etc.) which require git clone (network); (v) **YES — `Task` tool declared in `allowed-tools`**: SKILL.md L5 says "Run Semgrep static analysis scan on a codebase using parallel subagents" + L23 "Spawn all scan Tasks in a single message" — TOOL-LEVEL cross-agent surface (not prompt-level). **NEW §4.4.3 step 2 audit checklist gap surfaced + backpatched:** the new (v) signature was originally written for PROMPT-LEVEL invocations ("ask GPT-4"); §AP demonstrates the TOOL-LEVEL pattern (`Task` declared in `allowed-tools` frontmatter). Per §AGENT_SKILLS.md §2E same-model bounded-subagent carve-out (see lines ~306-404), the cross-agent surface qualifies for Tier 2 downgrade if ALL of: (a) registry-named OR (b) vendored-named OR (c) inline-generic; AND condition 1 same model family + 2 no external API + 3 same tool grants + 4 bounded by audited source. **§AP semgrep qualifies via condition (b) vendored-named**: `agents/semgrep-scanner.md` is bundled at the audited SHA with frontmatter `tools: Bash(semgrep scan:*), Bash` — sub-agent's Bash is constrained-then-bare (semgrep CLI allowlist with bare-Bash fallback for `wait`, `mkdir`, etc. per the scanner agent's L21-22 + L29-35 parallel-execution pattern). Per the §AGENT_SKILLS.md §2E "Cross-agent normative predicate" (lines ~406-426): (1) execution boundary is INTERNAL (host's Task tool, same process tree) ✅; (2) child grant set ⊆ parent grant set — child has Bash (allowlist + bare), parent has Bash + Task — child's Bash is subset of parent's Bash ✅; (3) grant inheritance is PROVABLE via vendored-named spec file ✅. **All 3 normative-predicate conditions FAIL the cross-agent classification → §AP qualifies for same-model bounded-subagent carve-out → Tier 2 (not Tier 3).** Final Tier 2 verdict for §AP semgrep: `shell-execute+repo-write+cross-agent` triple-compound (matches the new compound; the cross-agent component is acknowledged in the tool-scope declaration even though carve-out applies). **Intra-skill Tier-3 escalation gate (parallel to §D anthropics/skill-creator's `claude --` script escalation):** the parallel sub-agent SPAWN itself (the `Task` tool invocation at SKILL.md L23 "Spawn all scan Tasks in a single message") MUST require user-approval per §4.5.2 step 4 Tier-3 escalation rule — neutral 3-option prompt before the Task batch is launched. Same pattern as §D bundled-script escalation. **§AP Policy Gates (codified at §4.5.3 §AP entry):** (i) Phase-A/Phase-B gate per Tier 2; (ii) intra-skill Tier-3 escalation gate for `Task` batch spawn (parallel sub-agent invocation requires neutral 3-option user confirmation); (iii) `--metrics=off` MUST be included in every `semgrep` invocation (SKILL.md L20 mandates; agent applying §AP MUST emit `[§AP metrics-off enforcement: <command>]` transcript line when invoking semgrep); (iv) Step 3 hard gate at SKILL.md L21 — user MUST explicitly approve scan plan (rulesets + target + engine + mode) before any subagent Task is spawned; the original "scan this codebase" request is NOT approval. **Bundle:** SKILL.md 2198t + 3 references/*.md (4917t — `scanner-task-prompt.md` 1559t, `scan-modes.md` 1153t, `rulesets.md` 2205t) + 1 workflows/scan-workflow.md (2983t) + `scripts/merge_sarif.py` (1598t — Python script, R2-2 audit: subprocess.run() calls for SARIF Multitool with Python fallback, NO model-client invocations, NO env-var-indirected commands, falls back to pure-Python if multitool unavailable) + `agents/semgrep-scanner.md` (vendored-named sub-agent per §2E condition (b), bounded Bash(semgrep scan:*) + bare Bash for parallel execution `wait`) + LICENSE byte-identical. **Worst-case archive 11,696 tokens** — exceeds §3B 5K-preferred cap; the 6 companion files (3 references + 1 workflow + 1 script + 1 agent) are load-on-demand. **Cluster-coupling with §F/§G/§H/§J + §AN/§AO (FIRST 7-skill ToB cluster):** §AP shares upstream repo + SHA `a56045e9...` with all 6 other ToB adoptions; ToB cluster grows 4→7 skills, becomes LARGEST cluster in framework. Sub-cluster within static-analysis plugin: §AP semgrep is the SCAN-EXECUTION skill (paired with §AO codeql); both feed into §AN sarif-parsing (output processing). Canonical pipeline chains: (i) `§AP semgrep scan → §AN sarif-parsing` (process semgrep output); (ii) **multi-tool aggregation chain** `§AO codeql + §AP semgrep → §AN sarif-parsing` (aggregate findings from both scanners via merge_sarif.py). **`scripts/merge_sarif.py` R2-2 hardening audit:** ✅ `subprocess.run` calls for SARIF Multitool invocation (process-spawn YES); ✅ NO `claude`/`anthropic`/`messages.create`/SDK tokens; ✅ NO env-var-indirected commands (explicit args); SARIF processing only — falls back to pure Python if multitool unavailable; per §2E "Bundled-script same-model self-invocation" clause: **NON-APPLICABLE** (no model-client invocation). **`agents/semgrep-scanner.md` sub-agent audit:** ✅ vendored at audited SHA + frontmatter `tools: Bash(semgrep scan:*), Bash` (constrained Bash with allowlist + bare-Bash fallback for `wait`/`mkdir`); ✅ NO model-client invocations in agent body; ✅ agent body is pure scan-execution discipline (rulesets, parallel execution, output requirements, error handling); per §2E condition (b) vendored-named ✅; per cross-agent normative predicate all 3 conditions FAIL → carve-out applies. **Body sha256:** `c21e09f5bfd47a03...`. **§D-parallel observation:** §AP semgrep + §D anthropics/skill-creator share the "Tier 2 with bundled sub-agent + intra-skill Tier-3 escalation" shape — SECOND such skill in the framework. -->


# Semgrep Security Scan

Run a Semgrep scan with automatic language detection, parallel execution via Task subagents, and merged SARIF output.

## Essential Principles

1. **Always use `--metrics=off`** — Semgrep sends telemetry by default; `--config auto` also phones home. Every `semgrep` command must include `--metrics=off` to prevent data leakage during security audits.
2. **User must approve the scan plan (Step 3 is a hard gate)** — The original "scan this codebase" request is NOT approval. Present exact rulesets, target, engine, and mode; wait for explicit "yes"/"proceed" before spawning scanners.
3. **Third-party rulesets are required, not optional** — Trail of Bits, 0xdea, and Decurity rules catch vulnerabilities absent from the official registry. Include them whenever the detected language matches.
4. **Spawn all scan Tasks in a single message** — Parallel execution is the core performance advantage. Never spawn Tasks sequentially; always emit all Task tool calls in one response.
5. **Always check for Semgrep Pro before scanning** — Pro enables cross-file taint tracking and catches ~250% more true positives. Skipping the check means silently missing critical inter-file vulnerabilities.

## When to Use

- Security audit of a codebase
- Finding vulnerabilities before code review
- Scanning for known bug patterns
- First-pass static analysis

## When NOT to Use

- Binary analysis → Use binary analysis tools
- Already have Semgrep CI configured → Use existing pipeline
- Need cross-file analysis but no Pro license → Consider CodeQL as alternative
- Creating custom Semgrep rules → Use `semgrep-rule-creator` skill
- Porting existing rules to other languages → Use `semgrep-rule-variant-creator` skill

## Output Directory

All scan results, SARIF files, and temporary data are stored in a single output directory.

- **If the user specifies an output directory** in their prompt, use it as `OUTPUT_DIR`.
- **If not specified**, default to `./static_analysis_semgrep_1`. If that already exists, increment to `_2`, `_3`, etc.

In both cases, **always create the directory** with `mkdir -p` before writing any files.

```bash
# Resolve output directory
if [ -n "$USER_SPECIFIED_DIR" ]; then
  OUTPUT_DIR="$USER_SPECIFIED_DIR"
else
  BASE="static_analysis_semgrep"
  N=1
  while [ -e "${BASE}_${N}" ]; do
    N=$((N + 1))
  done
  OUTPUT_DIR="${BASE}_${N}"
fi
mkdir -p "$OUTPUT_DIR/raw" "$OUTPUT_DIR/results"
```

The output directory is resolved **once** at the start of Step 1 and used throughout all subsequent steps.

```
$OUTPUT_DIR/
├── rulesets.txt                 # Approved rulesets (logged after Step 3)
├── raw/                         # Per-scan raw output (unfiltered)
│   ├── python-python.json
│   ├── python-python.sarif
│   ├── python-django.json
│   ├── python-django.sarif
│   └── ...
└── results/                     # Final merged output
    └── results.sarif
```

## Prerequisites

**Required:** Semgrep CLI (`semgrep --version`). If not installed, see [Semgrep installation docs](https://semgrep.dev/docs/getting-started/).

**Optional:** Semgrep Pro — enables cross-file taint tracking, inter-procedural analysis, and additional languages (Apex, C#, Elixir). Check with:

```bash
semgrep --pro --validate --config p/default 2>/dev/null && echo "Pro available" || echo "OSS only"
```

**Limitations:** OSS mode cannot track data flow across files. Pro mode uses `-j 1` for cross-file analysis (slower per ruleset, but parallel rulesets compensate).

## Scan Modes

Select mode in Step 2 of the workflow. Mode affects both scanner flags and post-processing.

| Mode | Coverage | Findings Reported |
|------|----------|-------------------|
| **Run all** | All rulesets, all severity levels | Everything |
| **Important only** | All rulesets, pre- and post-filtered | Security vulns only, medium-high confidence/impact |

**Important only** applies two filter layers:
1. **Pre-filter**: `--severity MEDIUM --severity HIGH --severity CRITICAL` (CLI flag)
2. **Post-filter**: JSON metadata — keeps only `category=security`, `confidence∈{MEDIUM,HIGH}`, `impact∈{MEDIUM,HIGH}`

See [scan-modes.md](references/scan-modes.md) for metadata criteria and jq filter commands.

## Orchestration Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ MAIN AGENT (this skill)                                          │
│ Step 1: Detect languages + check Pro availability                │
│ Step 2: Select scan mode + rulesets (ref: rulesets.md)           │
│ Step 3: Present plan + rulesets, get approval [⛔ HARD GATE]     │
│ Step 4: Spawn parallel scan Tasks (approved rulesets + mode)     │
│ Step 5: Merge results and report                                 │
└──────────────────────────────────────────────────────────────────┘
         │ Step 4
         ▼
┌─────────────────┐
│ Scan Tasks      │
│ (parallel)      │
├─────────────────┤
│ Python scanner  │
│ JS/TS scanner   │
│ Go scanner      │
│ Docker scanner  │
└─────────────────┘
```

## Workflow

**Follow the detailed workflow in [scan-workflow.md](workflows/scan-workflow.md).** Summary:

| Step | Action | Gate | Key Reference |
|------|--------|------|---------------|
| 1 | Resolve output dir, detect languages + Pro availability | — | Use Glob, not Bash |
| 2 | Select scan mode + rulesets | — | [rulesets.md](references/rulesets.md) |
| 3 | Present plan, get explicit approval | ⛔ HARD | AskUserQuestion |
| 4 | Spawn parallel scan Tasks | — | [scanner-task-prompt.md](references/scanner-task-prompt.md) |
| 5 | Merge results and report | — | Merge script (below) |

**Task enforcement:** On invocation, create 5 tasks with blockedBy dependencies (each step blocks the previous). Step 3 is a HARD GATE — mark complete ONLY after user explicitly approves.

**Merge command (Step 5):**

```bash
uv run {baseDir}/scripts/merge_sarif.py $OUTPUT_DIR/raw $OUTPUT_DIR/results/results.sarif
```

## Agents

| Agent | Tools | Purpose |
|-------|-------|---------|
| `static-analysis:semgrep-scanner` | Bash | Executes parallel semgrep scans for a language category |

Use `subagent_type: static-analysis:semgrep-scanner` in Step 4 when spawning Task subagents.

## Rationalizations to Reject

| Shortcut | Why It's Wrong |
|----------|----------------|
| "User asked for scan, that's approval" | Original request ≠ plan approval. Present plan, use AskUserQuestion, await explicit "yes" |
| "Step 3 task is blocking, just mark complete" | Lying about task status defeats enforcement. Only mark complete after real approval |
| "I already know what they want" | Assumptions cause scanning wrong directories/rulesets. Present plan for verification |
| "Just use default rulesets" | User must see and approve exact rulesets before scan |
| "Add extra rulesets without asking" | Modifying approved list without consent breaks trust |
| "Third-party rulesets are optional" | Trail of Bits, 0xdea, Decurity catch vulnerabilities not in official registry — REQUIRED |
| "Use --config auto" | Sends metrics; less control over rulesets |
| "One Task at a time" | Defeats parallelism; spawn all Tasks together |
| "Pro is too slow, skip --pro" | Cross-file analysis catches 250% more true positives; worth the time |
| "Semgrep handles GitHub URLs natively" | URL handling fails on repos with non-standard YAML; always clone first |
| "Cleanup is optional" | Cloned repos pollute the user's workspace and accumulate across runs |
| "Use `.` or relative path as target" | Subagents need absolute paths to avoid ambiguity |
| "Let the user pick an output dir later" | Output directory must be resolved at Step 1, before any files are created |

## Reference Index

| File | Content |
|------|---------|
| [rulesets.md](references/rulesets.md) | Complete ruleset catalog and selection algorithm |
| [scan-modes.md](references/scan-modes.md) | Pre/post-filter criteria and jq commands |
| [scanner-task-prompt.md](references/scanner-task-prompt.md) | Template for spawning scanner subagents |

| Workflow | Purpose |
|----------|---------|
| [scan-workflow.md](workflows/scan-workflow.md) | Complete 5-step scan execution process |

## Success Criteria

- [ ] Output directory resolved (user-specified or auto-incremented default)
- [ ] All generated files stored inside `$OUTPUT_DIR`
- [ ] Languages detected with file counts; Pro status checked
- [ ] Scan mode selected by user (run all / important only)
- [ ] Rulesets include third-party rules for all detected languages
- [ ] User explicitly approved the scan plan (Step 3 gate passed)
- [ ] All scan Tasks spawned in a single message and completed
- [ ] Every `semgrep` command used `--metrics=off`
- [ ] Approved rulesets logged to `$OUTPUT_DIR/rulesets.txt`
- [ ] Raw per-scan outputs stored in `$OUTPUT_DIR/raw/`
- [ ] `results.sarif` exists in `$OUTPUT_DIR/results/` and is valid JSON
- [ ] Important-only mode: post-filter applied before merge; unfiltered results preserved in `raw/`
- [ ] Results summary reported with severity and category breakdown
- [ ] Cloned repos (if any) cleaned up from `$OUTPUT_DIR/repos/`
