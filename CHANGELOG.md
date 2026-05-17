# Changelog

All notable changes to ForgeWorks are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **Authentication Frontend** (Action Plan 5)
  - Login page at `/login` with LoginForm component
  - Register page at `/register` with RegisterForm component
  - Next.js middleware for route protection
  - AuthGuard component for client-side protected routes
  - AuthButton integrated in dashboard header
  - Redirect logic for authenticated/unauthenticated users
- **ADR `docs/decisions/RELEASE_TOOLING.md`** — captures the Changesets → Conventional Commits + release-please decision, evaluated against eight factors (flow methodology, branch strategy, semver, cadence, industry standards, best practices, stack composition, vision)
- **PR status lifecycle labeler** — 4-state convention `pr status:{opened,review,merged,closed}` mirrored into `.github/labels.yml` (so `labels-sync.yml` keeps the repo consistent), plus a new `.github/workflows/pr-status-labeler.yml` that auto-transitions on `pull_request` events (opened/reopened/converted_to_draft → opened, ready_for_review/review_requested → review, closed → merged|closed). "Blocked" stays in the orthogonal `status:blocked` work-state label — one source of truth. Renovate's `addLabels: ["pr status:opened"]` (in `.github/renovate.json5`) seeds the lifecycle on every dependency PR — using `addLabels` instead of `labels` so packageRules' major-bump override doesn't drop it
- **Checkov IaC scan job in `ci.yml`** — new `checkov` job runs the [Checkov](https://github.com/bridgecrewio/checkov) OSS CLI directly (NOT the Bridgecrew SaaS App) against `kubernetes`, `dockerfile`, and `github_actions` frameworks. Findings export to SARIF and upload to the GitHub Security tab via `github/codeql-action/upload-sarif`. First-pass uses `soft_fail: true` to baseline the existing footprint without breaking CI; tightening per-severity policy follows triage. Wired into the `ci-success` aggregate. Adopted following the framework in `research/github_apps/GITHUB_APPS.md` §2A (OSS CLI preferred over Marketplace App when both exist) — complements the existing CodeQL job on the disjoint infra-vs-application-code surface and goes deeper than Snyk IaC on policy breadth (1000+ built-in policies vs Snyk's narrower set)
- **`codecov.yml` repo-root config** — Codecov was already uploading via `codecov/codecov-action@v4` (commit `bd7e221`) but operating on Codecov's defaults: no flag definitions, no ignore list, no PR-comment layout, no threshold policy. New `codecov.yml` codifies: per-flag path mappings (`backend → src/backend/app/`, `frontend → src/frontend/src/`), carryforward semantics (a missing flag upload uses the previous value rather than collapsing to 0%), ignore list for tests/vendored/generated/migrations/infra/docs/research, PR-comment layout, and **advisory-only thresholds for the first rollout** (`informational: true` on both project and patch status — Codecov will post comments and Check Runs but will not fail PRs until baselines stabilize). After ~2 weeks of data we flip the informational flags off and promote the Codecov Check Run to Required in branch protection. Also fixed the backend coverage upload step in `ci.yml` which was missing `flags: backend` (frontend already had its flag) — backend coverage was uploading unflagged so it didn't apply to the `backend` flag rules. Adopted per `research/github_apps/evaluation_list.md` (Decision Record: Codecov)
- **Codecov Test Analytics enabled for backend (Pytest) + frontend (Vitest)** — separate feature from coverage; tracks flaky tests, slow tests, and recent failure patterns across PRs. JUnit XML output added to both runners: `pytest --junitxml=junit.xml` in the backend test step; `vitest.config.mts` `test.reporters` block now emits `['default', ['junit', { outputFile: 'junit.xml' }]]` when `process.env.CI` is set (local dev keeps the plain default reporter). Two new upload steps in `ci.yml` use `codecov/test-results-action@v1` (the dedicated Test Analytics action, distinct from `codecov-action`), each scoped to its flag and gated by `if: ${{ !cancelled() }}` so failure data still uploads when tests fail (the whole point of analytics) but not when a job is intentionally cancelled
- **Sentry SDK wired into FastAPI backend** — `sentry_sdk.init()` called before `FastAPI()` instantiation in `src/backend/app/main.py`; FastAPI integration auto-enables because `fastapi` is already in the dep tree. Init is gated on `SENTRY_DSN`: no-op when the env var is unset (local dev default), so the SDK ships dormant. Reads `SENTRY_DSN`, `SENTRY_ENVIRONMENT` (falls back to `ENVIRONMENT`), and `SENTRY_RELEASE` (falls back to `app_version`) from `app.core.config.settings`. `send_default_pii=False` is set explicitly — auth headers and JWTs would otherwise leak into events. Validated end-to-end against the `forge-works-backend` Sentry project (org `adamatdevops-hs`, region `us.sentry.io`) on 2026-05-14 via a temporary `/sentry-debug` endpoint raising `ZeroDivisionError`; the event surfaced as `FORGE-WORKS-BACKEND-1` with the Sentry middleware visible in the traceback, then the debug endpoint was reverted ([ef375f3], [1aef655]). Production cluster wiring deferred to AB-021 (blocks on AB-002 + backend Deployment manifest)
- **`.coderabbit.yaml` repo-root config** — pre-emptive doctrine codification for the CodeRabbit App (Decision Record in `research/github_apps/evaluation_list.md`; App install pending). Five pre-install gates baked in: (1) `request_changes_workflow: false` prevents formal "Request Changes" reviews from blocking merges; (2) no commit-mutating features used → CodeRabbit can only post advisory comments; (3) no `labels:` block → no race with `pr-status-labeler.yml` / `labels-sync.yml`; (4) default bot identity (`@coderabbitai`) preserves §3C "bot must not impersonate human"; (5) training-data opt-out remains a one-time dashboard verification before install (documented in the file header). Path filters scope review to `src/**` only (excludes lockfiles, generated artifacts, tests, migrations, infra, docs, research). Per-directory `path_instructions` for backend/frontend/flink-jobs/.github/workflows enforce project doctrine (RichFunction lifecycle in Flink, SHA-pin convention in workflows, no `any` in TS, etc.). Per-language linters that already run in CI (ruff/eslint/hadolint/yamllint/markdownlint/gitleaks) are disabled in `tools` block to avoid duplicate noise on PR comments — CodeRabbit's value is semantic/architectural review, not re-running tools we already gate on
- **`forge-skills` MCP loader (AB-022 Phase 1)** — in-house stdio MCP server at `tools/forge-skills-mcp/` that serves vendored skills from `.skills/<vendor>/<slug>/SKILL.md` identically to Claude Code and Codex CLI. Replaces upstream `claude-skills-mcp` v1.0.0 which was broken on 2026-05-15 (silent backend no-start; remote mode unimplemented). Stack: Python 3.11+, FastMCP, Pydantic v2, PyYAML. Exposes 4 tools: `list_skills(tier_max)`, `get_skill(slug)`, `find_skills(query, tier_max)`, `loader_health()`. Server-side doctrine enforcement: 40-char hex SHA validation on `source-sha` (per `AGENT_SKILLS.md` §2D); categorical rejection of `tool-scope: git-write` or `workflow-write` (per §2E); path/frontmatter consistency check on every scan. 19 tests pass (unit + integration); ruff-clean. Documented at `tools/forge-skills-mcp/README.md`. `AGENTS.md` §4.4 swapped `claude-skills-mcp` → `forge-skills` as the primary dual-agent loader. Phase 1 is file-vendored only; runtime fetch lands in Phase 3 per `roadmap/ACTION_PLAN_SKILL_LOADERS.md`
- **AGENTS.md §4.5 "Skill invocation triggers — runtime rules for adopted skills"** — new doctrine section codifying when agents MUST consult adopted skills via `mcp__forge-skills__get_skill`. Before §4.5 existed, adoption only made a skill discoverable via `list_skills`; whether the agent invoked it on a given task depended on per-session judgment, producing inconsistent behavior. §4.5 codifies trigger → skill mapping for every active adopted skill (4 today: §F, §AF, §G, §H), with a compact §4.5.1 trigger table, a §4.5.2 6-step invocation pattern (including Tier-2 user-confirmation gate for shell/write phases, with neutral 3-option prompt + ambiguous-response handling), a §4.5.3 Policy Gates Index that lifts load-bearing policy gates from `evaluation_list.md` Notes into always-loaded doctrine (e.g., §H's `issue-writer` Tier-3 forward-reference gate, the observed-vs-enforced binary distinction, the same-model bounded-subagent carve-outs for `function-analyzer` and `adversarial-modeler`), a §4.5.4 pairing doctrine documenting both chained (§G→§H) and lifecycle-bookend (§F+§AF) patterns, a §4.5.5 update procedure tying §4.5.1 row + §4.5.3 entry maintenance atomically to `evaluation_list.md` updates (with the audit-gap acknowledgment that transcript-citation enforcement is observance-based, AB-025 backlog filed), and a §4.5.6 anti-pattern list (8 items). Two callsite edits land atomically: §4.4.3 step 3 (Decision Record completion) gains "+ add §4.5.1 row + §4.5.3 entry" substep; §4.4.6 removal procedure gains "+ remove §4.5.1 row + §4.5.3 entry" as step 3. The §4.5 doctrine was hardened through a 3-round Codex feedback loop (R1: 9 findings 3H+4M+2L, R2: 7 findings 2H+3M+2L, R3: 2 findings 1M+1L — convergence visible in the finding-count trajectory). Notable doctrine-level decisions made during the loop: SHOULD→MUST modal hardening (R1 F1) to match §3.6 strictness; Codex review-profile fallback routes to direct vendored-file Read (R1 F6 + R2 F2) rather than to AGENT_SKILLS.md framework doctrine; Tier-2 Phase A/Phase B split with explicit boundary rule distinguishing skill-content reads (admin) from workload-input reads (data) (R1 F2 + R2 F1 + R3 F1); 7-condition exception eliminated in favor of a single Codex review-profile case (R2 F5). Round-1+2+3 audit trail at `research/feedback_loops/agents-skill-invocation-triggers/20260516T193023Z/` (local-only, gitignored). AGENTS.md grew from 290 to 389 lines (+99 lines)
- **Fifth vendored skill: `anthropics/skill-creator` — first Anthropic-first-party + first meta-skill + first Tier 2 with intra-skill Tier-3 escalation** — adopted via the AGENTS.md §4.4.3 7-step process; first Anthropic-published skill landed under the forge-skills loader, and the framework's most complex adoption to date. Vendored at `.skills/anthropics/skill-creator/` (SKILL.md + 17 companion files: 3 bundled same-model subagent defs in `agents/` — `analyzer.md`/`comparator.md`/`grader.md`; `assets/eval_review.html` HTML template; `eval-viewer/{generate_review.py, viewer.html}` local loopback HTTP server for eval result review; `references/schemas.md` JSON schema docs; 8 executable Python scripts in `scripts/` — `__init__.py`, `aggregate_benchmark.py`, `generate_report.py`, `improve_description.py`, `package_skill.py`, `quick_validate.py`, `run_eval.py`, `run_loop.py`, `utils.py`; plus `LICENSE.txt`) from `github.com/anthropics/skills` @ SHA `f458cee31a7577a47ba0c9a101976fa599385174`. Audited 2026-05-17: ✅ no encoded content; ✅ no transitive `load skill X` refs; ⚠️ THREE distinct cross-reference patterns flagged + handled this round, two requiring NEW framework carve-outs: (1) **bundled same-model subagents** — `agents/{grader,comparator,analyzer}.md` shipped WITHIN the skill (not `~/.claude/agents/` registry like §G's `function-analyzer` or §H's `adversarial-modeler`); same Claude model family, child grants ⊆ parent via Task tool, no external API; satisfies the §2E same-model bounded-subagent carve-out via the **broadened condition 4** added this round (allows both registry-installed AND vendored-skill-local agent specs pinned by source SHA; pre-existing condition 4 only covered registry). (2) **`claude -p` subprocess invocations in 3 scripts** — `scripts/run_eval.py` L71-85, `scripts/improve_description.py` L26-45, `scripts/run_loop.py` (orchestrator) invoke `subprocess.Popen(["claude", "-p", ...])` to spawn a fresh Claude CLI session whose tool grants load from `~/.claude/settings.json` (NOT bounded by parent's scope); **does NOT** satisfy §2E bounded-subagent condition 3 (`child grants ⊆ parent`) because the subprocess opens a fresh tool envelope. The §2E **"Bundled-script same-model self-invocation"** clause added this round (Round-6) codifies the new pattern: such scripts default to Tier 3 — per-invocation user approval — even when the parent skill is Tier 2; the clause is **mechanism-agnostic** (covers CLI subprocesses, SDK calls in fresh processes, container-launched model spawns, env-variable-indirected command construction) with a **fail-closed default for inconclusive cases** (added Round-2 of the Codex loop) and a parallel `AGENTS.md §4.4.3 step 1` audit-checklist addition for detecting subprocess + model-client tokens at adoption review. (3) **Local loopback HTTP server** — `eval-viewer/generate_review.py` launches an HTTP server on `localhost:<port>` for eval result review; loopback-only, NOT external network for Tier classification; documented for transparency. **Tier 2 with intra-skill Tier-3 escalation** (corrected from eval-list authoring's Tier 1 estimate per §4.4.3 step 1 + step 2; overall skill operates as Tier 2 `shell-execute+repo-write`, but the three `claude -p` scripts are gated at Tier 3 per the new §2E clause via `AGENTS.md §4.5.3` Gate 2 with explicit gate-sequencing doctrine: Tier-2 Phase-B confirmation FIRST, then per-script Tier-3 approval IMMEDIATELY BEFORE each escalated invocation; approval for one Tier-3 script does NOT carry to another in the same session). Measured runtime context cost via tiktoken cl100k_base: SKILL.md body 7252 tokens; worst-case read-into-context archive (SKILL.md + 5 read-by-Claude companions: 3 `agents/*.md` + `references/schemas.md` + `assets/eval_review.html`) = **18659 tokens** (recorded in frontmatter); full archive including the 8 executable Python scripts + viewer.html + generate_review.py = 50312 tokens, but those execute via shell rather than load into Claude's context window (methodology note per AGENT_SKILLS.md §3B). Above 10K hard-justify threshold per §3B — justified by skill being skill-authoring-phase-only (not always-loaded; only fetched when user engages in skill creation/optimization workflow), same logic as §G (audit-phase) and §H (PR-review-phase). Author Anthropic, first-party (authors of the SKILL.md format itself). Fit: meta-skill for authoring local skills under `.skills/forge-works/<slug>/` — direct hit on §1 Goal #1 (codify project-specific operations); strategic-pair with the in-house forge-skills MCP loader. **AGENTS.md §4.5.1 trigger row** added: triggers on "Create / modify / improve a skill, run skill evals, optimize skill description for triggering accuracy, benchmark skill performance, or package a skill"; may pair with §F (ask-questions-if-underspecified) when the create-a-skill request is itself underspecified. **AGENTS.md §4.5.3 §D Policy Gates Index** entry added with **5 gates**: Tier-2 user-confirmation gate, intra-skill Tier-3 escalation gate (with explicit gate-sequencing for combined Phase-B + Tier-3 flows), bundled same-model subagents carve-out citation, observed-vs-enforced shell-execute caveat, local HTTP server documentation. **AGENTS.md §4.5.6 anti-pattern list** grew from 8 to 9 items (new entry for "Executing a §2E bundled-script same-model self-invocation path without per-invocation Tier-3 user approval" — explicitly calls out Phase-B approval does NOT cascade to Gate 2). Adoption budget post-landing: **5 / 30** (per §4.4.4 soft cap; first Tier 2 + Tier-3 hybrid). Body byte-identical to upstream verified via Python byte-compare (32625 bytes; SHA `0b58e93f8aeb0a23...` for body content); 16 companion files (excluding the synthesized forge-skills frontmatter on SKILL.md + LICENSE.txt + scripts/**init**.py) byte-identical via shasum at adoption. The §D adoption was hardened through a **3-round Codex feedback loop** (R1: 4 findings 2M+2L → R2: 3 findings 1M+2L → R3: 0 findings `solid` — clean convergence in 3 rounds vs §H's 5+ rounds). Notable doctrine-level decisions during the loop: §2E trigger framing rewritten to be mechanism-agnostic with explicit "provable subset" test + fail-closed default (R1-F1 + R2-F1); §2E condition 4 broadened to allow vendored bundled subagents (R1-F2) and calibrated to acknowledge registry entries can be equivalently bounded under matching governance (R2-F3); §4.4.3 step 1 audit-checklist gained a subprocess + model-client scan bullet for §2E enforceability at adoption review (R2-F2); §4.5.3 gate-sequencing paragraph codified for combined Phase-B + Tier-3 flows (R1-F3); §4.5.6 9th anti-pattern explicitly distinguishes Phase-B approval from Gate 2 cascade (R1-F4). Round-1+2+3 audit trail at `research/feedback_loops/agents-evaluation_list/20260517T070135Z/` (local-only, gitignored)
- **Fourth vendored skill: `trailofbits/differential-review` — first Tier 2 adoption** — adopted via the AGENTS.md §4.4.3 7-step process; first Tier 2 skill landed under the forge-skills loader. Vendored at `.skills/trailofbits/differential-review/` (SKILL.md + 4 sibling companion files in the skill dir — `adversarial.md`, `methodology.md`, `patterns.md`, `reporting.md`; sibling layout, NOT a `resources/` subdir as in §G) from `github.com/trailofbits/skills` @ SHA `a56045e9ae00b3506cacefea0f672aab0a1a6e3c` (same canonical repo as §F + §G). Audited 2026-05-16: ✅ no encoded content, ✅ embedded bash blocks are inspectable + scoped to declared diff-review purpose (allowed binaries explicitly listed in the Decision Record: `git` for read-only diff/log/blame/checkout, `gh` for read-only PR view, `find` + `grep` for enumeration/search — no destructive shell ops), ✅ no executable python/node snippets, ⚠️ TWO cross-reference patterns flagged and handled by **two new framework carve-outs added this round** (Round-5 amendment to AGENT_SKILLS.md §2C + §2E): (1) the `adversarial-modeler` Claude Code subagent referenced in SKILL.md is a same-model bounded subagent with fewer tool grants than the parent → satisfies the Round-4 same-model carve-out → in-set delegation, NOT cross-agent; if user's `~/.claude/agents/` lacks `adversarial-modeler` the spawn fails-closed and the agent reads `adversarial.md` manually instead; (2) conditional cross-skill composition with §G `audit-context-building` (methodology.md L9/L17/L178/L181 + SKILL.md L125/L162/L163) — all gated by explicit `if available / if NOT available` graceful-degradation conditionals → satisfies the new **Cross-skill composition carve-out** (Round-5, §2E): composing with another already-adopted skill in our own audited loader is the OPPOSITE of supply-chain expansion. A forward reference to a not-yet-adopted `issue-writer` skill (SKILL.md L137-139 + reporting.md L344/L349-354) includes prescriptive command syntax under an "Integration" heading; Codex Round-5 Finding 3 flagged this as too strong for "documentation-only" classification and surfaced a third doctrinal state — **Conditional load of an UN-adopted target** — that the original §2E carve-out didn't cover. AGENT_SKILLS.md §2E was amended this round with a new clause requiring an explicit per-invocation-user-approval gate (Tier 3 default) in the Decision Record for any conditional invocation of a non-adopted target; §H Notes now explicitly states agents MUST NOT invoke `issue-writer` without user approval until/unless it is adopted via its own §4.4.3 process. **Tier 2** (corrected from eval-list authoring's Tier 1 estimate per §4.4.3 step 1; upstream frontmatter declares `allowed-tools: Read Write Grep Glob Bash` → repo-write + shell-execute scope per AGENT_SKILLS.md §2E). Loader enum extended this round to accept `shell-execute+repo-write` (extends Round-3's `read-only+transform` precedent); `tools/forge-skills-mcp/src/forge_skills_mcp/frontmatter.py` ToolScope literal updated + new test in `tests/test_frontmatter.py` (7/7 pass; no other ruff/test regressions). Measured runtime context cost 1668 tokens (SKILL.md only — what the loader's `get_skill` serves); total vendored archive 8087 tokens worst-case including 4 companion files (`adversarial.md` 1186t, `methodology.md` 1688t, `patterns.md` 1742t, `reporting.md` 1803t) loaded on-demand when SKILL.md's Decision Tree directives are followed. Above 5K-preferred but under 10K hard-justify per AGENT_SKILLS.md §3B — justified by skill being PR-review-phase-only, not always-loaded. Author Trail of Bits, first-party. Fit: pre-commit Decision Record patches, PR review against base SHA, Flink 1.20 → 2.0 version-bump review (Task #24). Pairs with §G `audit-context-building` as the security-review pipeline: §G builds baseline context, §H reviews diffs against it. Adoption budget post-landing: 4 / 30 (per §4.4.4 soft cap). Body byte-identical to upstream verified via Python byte-compare (6596 bytes); 4 companion files byte-identical via shasum. Upstream plugin also ships `agents/adversarial-modeler.md` + `commands/diff-review.md` (slash command) at plugin root — these are NOT vendored as part of §H per §4.4.3 strict reading; user may install separately if desired. Two further AGENT_SKILLS.md §2E doctrine amendments landed in the same PR per Codex Round-5 Findings 1 + 2: (a) cross-skill composition condition 2 ("graceful degradation") tightened — the fallback must produce the same artifact class and preserve core acceptance criteria, not just satisfy "if available / if NOT available" wording; reviewer-check clause added to reject perfunctory fallbacks; (b) new "observed vs. enforced" doctrine paragraph clarifies that `shell-execute` Tier 2 binary lists are auditor-facing observed usage, NOT runtime allowlists, unless the loader provides per-binary enforcement (Phase 1 forge-skills loader does not); Decision Records must explicitly distinguish "observed in upstream content" from "enforced at runtime". §H Tool scope was rewritten accordingly to lead with "Effective shell grant per upstream `allowed-tools: ... Bash`: full Bash tool surface is in scope at runtime — NOT a binary-level allowlist", with git/gh/find/grep labeled as observed (not enforced). Codex Round-5 Findings 4 + 5 (both LOW — same-model carve-out condition 3 wording nit + multi-file layout policy gap) were deferred consistent with the prior-round nit-deferral pattern. Round-5 audit trail at `research/feedback_loops/agents-evaluation_list/20260516T190219Z/` (local-only, gitignored). Loader-runtime note: the live MCP server caches the Python `Literal` enum and will reject `shell-execute+repo-write` until the next Claude Code session restart spawns a fresh server process; disk state is correct + unit tests confirm the enum landing
- **Third vendored skill: `trailofbits/audit-context-building`** — adopted via the AGENTS.md §4.4.3 7-step process; first multi-file vendored skill under the forge-skills loader. Vendored at `.skills/trailofbits/audit-context-building/` (SKILL.md + 3 companion files in `resources/`) from `github.com/trailofbits/skills` @ SHA `a56045e9ae00b3506cacefea0f672aab0a1a6e3c` (same canonical repo as §F). Audited 2026-05-16: ✅ no encoded content, ✅ no transitive `load skill X` refs (the 3 relative refs to `resources/*.md` are companion-file links, not cross-skill), ✅ no cross-agent invocations (§8 references `function-analyzer` subagent which is within Claude's own toolset — bounded subagent spawn per AGENTS.md §4.4.3 spirit, not cross-LLM), ✅ no executable shell/python/node snippets. Tier 1 (read-only / advisory; "pure context building only" per skill's §10 Non-Goals which explicitly excludes vulnerability findings, fix proposals, PoCs, exploit modeling, severity rating). Measured runtime context cost 2133 tokens (SKILL.md only — what the Phase 1 loader serves via `get_skill`); total vendored archive 7549 tokens including 3 companion files (`COMPLETENESS_CHECKLIST.md` 425t, `FUNCTION_MICRO_ANALYSIS_EXAMPLE.md` 4419t, `OUTPUT_REQUIREMENTS.md` 572t) loaded on-demand when the SKILL.md's relative refs are followed. Author Trail of Bits, first-party. Gateway skill for sensitive-code review (normalizer IAM, auth boundaries, Sentry redaction, ML advisory output paths); pairs with the upcoming Engine Phase 6 work. Adoption budget post-landing: 3 / 30 (per §4.4.4 soft cap). All 4 files byte-identical to upstream verified via cmp + shasum
- **Second vendored skill: `obra/verification-before-completion`** — adopted via the AGENTS.md §4.4.3 7-step process; second skill landed under the forge-skills loader. Vendored at `.skills/obra/verification-before-completion/SKILL.md` from `github.com/obra/superpowers` @ SHA `f2cbfbefebbfef77321e4c9abc9e949826bea9d7`. Audited 2026-05-16: ✅ no encoded content, ✅ no transitive `load skill X` refs, ✅ no cross-agent invocations, ✅ no executable shell/python/node snippets (code blocks contain illustrative patterns like `[Run test command]`, not actual commands). Tier 1 (read-only / advisory; upstream's `read-only + transform` simplified to `read-only` at vendoring per loader's §2E enum). Measured context cost 987 tokens (cl100k_base via tiktoken) — within the eval-list 1-2K range. Author Jesse Vincent (obra) is known-community per AGENTS.md §4.4.1 → content review applied per solo-author rule and passed. Pairs with §F (ToB ask-questions-if-underspecified) as bookend skills for agent honesty: ask before starting → verify before claiming done. Adoption budget post-landing: 2 / 30 (per §4.4.4 soft cap). Byte-identical body verified via shasum against upstream
- **First vendored skill: `trailofbits/ask-questions-if-underspecified`** — adopted via the AGENTS.md §4.4.3 7-step process; first skill landed under the forge-skills loader. Vendored at `.skills/trailofbits/ask-questions-if-underspecified/SKILL.md` from `github.com/trailofbits/skills` @ SHA `a56045e9ae00b3506cacefea0f672aab0a1a6e3c` (the marketplace plugin path is canonical; an identical `.codex/skills/` mirror exists upstream). Audited 2026-05-16: ✅ no encoded content, ✅ no transitive `load skill X` refs, ✅ no cross-agent invocations, ✅ no executable shell/python/node snippets (only formatting examples). Tier 1 (read-only / advisory). Measured context cost 884 tokens (cl100k_base via tiktoken) — within 12% of the eval-list ~1K estimate. Decision Record at `research/agents/evaluation_list.md` §F updated with audited SHA + measured cost + canonical-home path. Smoke-tested via `mcp__forge-skills__list_skills` and `get_skill` — both Claude Code and interactive Codex pick the skill up on next `list_skills` call (the forge-skills scanner rescans per-request, no restart needed). Reinforces AGENTS.md §3.6 "don't infer missing requirements"; highest-leverage skill identified in the agents evaluation pass
- **MCP invocation pattern: pre-built `.venv` + direct python (AB-022 fix)** — original `uv run --directory ...` MCP invocation failed under Codex's sandboxed `codex exec` because `uv` writes to `~/.cache/uv/` (outside the workspace) at runtime, which seatbelt blocks; Codex surfaces the failure as `error: "user cancelled MCP tool call"` (misleading — the server never started). Replaced with `.venv/bin/python -m forge_skills_mcp --skills-root <abs path>` + `env = { PYTHONDONTWRITEBYTECODE = "1" }` so the spawned Python performs zero writes at runtime. `.venv` lives inside `tools/forge-skills-mcp/` (gitignored). `--skills-root` is passed explicitly because Codex inherits its own CWD to spawned MCP servers, not the package's directory, so the default cwd-walker can't locate `.skills/`. Same investigation also confirmed Codex 0.130.0 auto-cancels MCP tool calls in `codex exec --profile review` (sandbox=read-only, approval=never) **by design** — no public config key (`always_allow`, `auto_approve`, `tools.default_tools_approval_mode`, per-server allowlist) overrides this; documented as a known constraint in `AGENTS.md` §4.4 preamble and `tools/forge-skills-mcp/README.md` § "Codex sandbox constraint". The `/codex-review` loop is unaffected (it reviews diffs, doesn't need skills); dual-agent skill access holds for interactive development sessions

### Changed

- **Release process: Changesets → Conventional Commits + manual `git tag` (interim) → release-please (target)** — `RELEASE.md` rewritten to describe the interim manual process; release-please wires in task #23
- **CI Success aggregate now gates on Security job** — `ci.yml` was silently passing CI Success when Snyk failed; added `needs.security.result` to the conditional
- **Language version constraints tightened to match CI** — was producing scan-time drift on the Snyk App (installed 2026-05-12) where Snyk's runners could pick a different interpreter/runtime than CI uses, generating false positives/negatives. `src/backend/pyproject.toml`: `requires-python = ">=3.11"` → `">=3.11,<3.13"` (locks to 3.11.x/3.12.x — Snyk and CI now agree). Root `package.json` and (newly added) `src/frontend/package.json` `engines` blocks: `node` `>=18.0.0` → `>=20.0.0 <22.0.0`, `pnpm` `>=8.0.0` → `>=9.0.0 <10.0.0` (matches `packageManager: pnpm@9.15.0` pin and CI's Node 20). Frontend package previously had no `engines` block at all — Snyk would have defaulted to its own Node version when scanning the workspace
- **`codecov/codecov-action@v4` → `@v5`** across both backend + frontend coverage uploads; passes `token: ${{ secrets.CODECOV_TOKEN }}` explicitly per Codecov dashboard onboarding (v5 supports OIDC tokenless upload on public repos, but explicit token is more reliable across branch-protection scenarios and works identically for both public and private repos). Same `token` argument also added to the `codecov/test-results-action@v1` steps for Test Analytics so they authenticate consistently
- **`pytest --cov-branch` added** to the backend test step (branch coverage in addition to line coverage — distinguishes "both true/false legs of an `if` were tested" from "only one was"; more granular signal for the `codecov/patch` Check Run). Kept `--cov=app` (explicit scope) instead of Codecov wizard's `--cov` (auto-detect) because explicit is more deterministic
- **`fetch-depth: 2`** added to checkout step in `test-backend` and `test-frontend` jobs — Codecov needs HEAD + previous commit to compute diff coverage and resolve the PR base ref; default `fetch-depth: 1` was leaving Codecov to guess

### Removed

- **Changesets infrastructure** — `.changeset/` directory, `.github/workflows/changeset-check.yml`, `.github/workflows/release.yml`, `pnpm changeset:*` / `pnpm release` scripts, `@changesets/cli` + `@changesets/changelog-github` devDependencies, `needs-changeset` + `skip-changeset` labels. Rationale in `docs/decisions/RELEASE_TOOLING.md`
- **Label cleanup** — pruned 12 labels from the repo to make `.github/labels.yml` the single source of truth: `breaking-change` (redundant with `semver:major`), `needs-changeset` + `skip-changeset` (Changesets removed in `ebc141f`), 3 GitHub defaults overlapping with `type:*` (`bug` → `type:fix`, `documentation` → `type:docs`, `enhancement` → `type:feature`), and 6 unused GitHub triage defaults (`duplicate`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`). Kept `security` (referenced by `renovate.json5` `vulnerabilityAlerts`) and added it to the manifest

### Security

- **Bumped `jackson-core` 2.15.3 → 2.18.7** across all 3 Flink modules — fixes 2 HIGH-severity Snyk findings (Allocation of Resources Without Limits / DoS, SNYK-JAVA-COMFASTERXMLJACKSONCORE-15907551 and -15365924)
- **Added dated `.snyk` ignores** for 8 HIGH transitive CVEs in `kafka-clients@3.4.0`, `commons-lang3@3.12.0`, and `lz4-java@1.8.0` — all require Flink 1.20 → 2.0 to remediate at the source. Each ignore carries a per-CVE rationale, in-context mitigation note, and an `expires: 2026-08-10` re-evaluation date. Tracked under task #24 (Flink 2.0 upgrade evaluation)
- **Snyk `.snyk` policy path** — added `--policy-path=.snyk` to both Snyk steps in `ci.yml`. With `--all-projects`, Snyk only auto-applies a `.snyk` file to manifests at the same path as the policy file; our Flink poms live under `src/flink-jobs/<module>/`, so without `--policy-path` the root ignores were silently skipped
- **Maven Snyk `--exclude`** — Maven step now uses basename-only exclude `tests,frontend,node_modules,.venv,venv` (mirrors the Python step). Stops the Maven scan from picking up npm/Python manifests and surfacing irrelevant cross-ecosystem CVEs
- **Bumped `next` 16.1.1 → 16.2.3** in the frontend — fixes Medium-severity [CVE-2025-59471](https://nvd.nist.gov/vuln/detail/CVE-2025-59471) (DoS via Image Optimizer `/_next/image` when `remotePatterns` is configured for external image domains; impact preemptive — we don't currently configure `remotePatterns`). Renovate-driven, PR #9 ([f2748eb])
- **Bumped `python-dotenv` → 1.2.2** in the backend — fixes Medium-severity [CVE-2026-28684](https://nvd.nist.gov/vuln/detail/CVE-2026-28684) (CVSS 6.6, local attack vector with required user interaction). Renovate-driven, PR #5 ([eaeb021])
- **Bumped `pyjwt` 2.10.1 → 2.12.0** in the backend — fixes [CVE-2026-32597](https://nvd.nist.gov/vuln/detail/CVE-2026-32597) (same vulnerability class as CVE-2025-59420 which rated CVSS 7.5 HIGH on Authlib). Renovate-driven, PR #7 ([8d312b6])
- **Bumped `pytest` 9.0.2 → 9.0.3** in the backend dev-deps — fixes Medium-severity [CVE-2025-71176](https://nvd.nist.gov/vuln/detail/CVE-2025-71176) (CVSS 6.8, predictable `/tmp/pytest-of-{user}` path allows local DoS or potential privilege escalation on UNIX; dev-tool only, not present in any production wheel). Renovate-driven, PR #4 ([137fd92])
- **Bumped `black` 25.12.0 → 26.3.1** in the backend dev-deps — fixes **HIGH-severity** [CVE-2026-32274](https://nvd.nist.gov/vuln/detail/CVE-2026-32274) (CVSS 8.7, most severe in this batch). Dry-run before merge confirmed identical reformatting behavior between v25 and v26 on this codebase (same 45-of-82 files flagged, same patches) so the bump is binary-only and reformats no source files. Black is not wired into pre-commit or CI — the project uses `ruff format` (line-length 100); `[tool.black]` config in `src/backend/pyproject.toml` (line-length 88) is orphan and a candidate for removal in a future cleanup. Renovate-driven, PR #10 ([7c84026])

### Fixed

- **`.coderabbit.yaml` `tone_instructions` parse error** — first CodeRabbit run on PR #10 (triggered `2026-05-13`) reported `Validation error: String must contain at most 250 character(s) at "tone_instructions"` and fell back to Organization-UI defaults instead of our YAML. The literal-block form (350+ chars) was over CodeRabbit's per-field limit. Replaced with a single-quoted flow scalar trimmed to 233 chars while preserving the substantive doctrine guidance (cite paths/lines, Conventional Commits, no premature abstractions, no WHAT-comments, advisory only). All 5 doctrine pre-checks remain in effect; once parsed, the YAML becomes the source of truth instead of dashboard defaults
- **Frontend test step ran in watch mode + masked failures** — `ci.yml` invoked `pnpm test --coverage --passWithNoTests`, which (a) launched vitest in watch mode (would never terminate), (b) passed flags pnpm didn't recognize, (c) was wrapped in `continue-on-error: true` so the broken step appeared green. Replaced with `pnpm test:coverage` (uses the existing `vitest run --coverage` script) and removed `continue-on-error`. The frontend's ~10 unit-test files now actually gate CI
- **Frontend coverage tooling** — added `@vitest/coverage-v8@4.0.16` as a frontend devDependency (vitest config required `provider: 'v8'` but the peer dep was never installed); exact-pinned `vitest` + `@vitest/coverage-v8` to `4.0.16` (no caret) because `@vitest/coverage-v8` declares vitest as an _exact_ peer — caret ranges let the two drift apart and produced a peer-dep mismatch on `pnpm install` (Renovate can group-bump them when newer 4.x lands); added `'lcov'` to `vitest.config.mts` `coverage.reporter` so the Codecov upload step in `ci.yml` actually receives coverage data instead of silently no-op'ing on a missing `lcov.info`
- **Flink SpotBugs cleanup across all 3 modules** — addressed 66 SpotBugs findings (13 event-router + 19 insight-generator + 34 pattern-matcher) and flipped `failOnError` from `false` (rollout) to `true` (gate) across all 3 module poms. Real fixes: `serialVersionUID = 1L` added to 19 Serializable classes; defensive `Collections.unmodifiableList/Map` getters and `new ArrayList/HashMap<>()` setter copies on DTO `Map`/`List` fields (`EventEnvelope`, `Insight`, both `PatternAlert`s) to close `EI_EXPOSE_REP`/`EI_EXPOSE_REP2`; narrowed `catch (Exception)` to `catch (NoSuchAlgorithmException)` in `sha256` helpers (3 places); replaced 6 double-brace-init anonymous `HashMap` blocks with `Map.of()` to close `SIC_INNER_SHOULD_BE_STATIC_ANON`; refactored `InsightAggregator.processElement` and `PatternWindowFunction.enrichWithScore` to use setters since getters now return unmodifiable views; narrowed `catch (Exception)` to `catch (RuntimeException)` in `ModelLoader.reloadFromMLflow` (best-effort skip on runtime failures; the inner `mlflowAdapter.checkForUpdate` already absorbs its own checked exceptions). False positives suppressed via shared `src/flink-jobs/spotbugs-exclude.xml` with rationale: `UWF_FIELD_NOT_INITIALIZED_IN_CONSTRUCTOR` on Flink RichFunction subclasses (state init is `open()` lifecycle, not constructor); `SE_TRANSIENT_FIELD_NOT_RESTORED` on Flink Schema impls (transient `ObjectMapper` re-initialized in `open()` plus defensive null-check guard); and `SE_TRANSIENT_FIELD_NOT_RESTORED` on `PatternWindowFunction.modelLoader` + `ModelLoader.{reloadScheduler,mlflowAdapter}` (re-initialized via the same `open()` / `initialize()` lifecycle — `ModelLoader` is held through a transient field, so the parent is never actually deserialized in our pipeline)

### Pending

- Database migration for auth tables (requires Docker)
- End-to-end auth flow testing
- ML training pipeline
- Real-time anomaly detection
- Cost optimization engine

---

## [0.8.0] - 2026-05-10

Sprint E5.1c platform release: multi-source normalizers, DLQ pipeline,
codified IAM, plus a CI hardening pass that brings Java tooling, Python
security rules, and a full pre-commit hooks suite online.

### Added

- **Multi-source normalizers** — `TerraformNormalizer` and `GitHubActionsNormalizer` join the existing K8s normalizer; each runs as its own Deployment with its own Kafka input topic and IRSA role ([26a8c59])
- **Per-source isolation guard** — `FW_EXPECTED_SOURCE` env var causes a normalizer pod to reject events whose `source` field doesn't match its declared scope; mismatches go to DLQ ([26a8c59])
- **DLQ pipeline on exception** — normalizer routes any unexpected processing error to `forge.dlq.events` instead of crashing; S3 errors propagate explicitly so they can be retried ([26a8c59])
- **CUE ↔ Pydantic schema fidelity gate** — CI job that diffs the CUE schemas in `src/normalizer/cue/` against the Pydantic models and fails on drift ([26a8c59])
- **IAM codified in `infra/iam/`** — the IRSA roles for the three normalizer service accounts now live in version-controlled Terraform/manifests instead of being applied ad-hoc ([26a8c59])
- **Pre-commit hooks suite** — 18 hooks across 7 upstream repos: trailing-whitespace, end-of-file-fixer, check-yaml/json/toml, check-merge-conflict, mixed-line-ending, ruff (lint + format), prettier, yamllint, markdownlint-cli2, shellcheck, hadolint, detect-secrets ([8ec09fc])
- **ruff `S` security rules** (flake8-bandit) added to root and backend ruff configs ([b5796ef])
- **Maven Spotless + SpotBugs** wired into all 3 Flink modules; Spotless enforces google-java-format 1.33.0 AOSP, SpotBugs runs at `effort=Max threshold=Low` with `failOnError=false` for the rollout phase ([b5796ef])
- **CI `java-build` matrix job** — runs `mvn verify` per Flink module on every push, gating Spotless + SpotBugs + tests ([b5796ef])
- **`docs/PRE_COMMIT_EVALUATION.md`** — decision framework and hook-by-hook verdict explaining the 18-hook selection ([8ec09fc], [b5796ef])
- **Engine Phase 6 forward reference** in `roadmap/ACTION_PLAN_ENGINE_PHASE-5.md` — points at the planned Agentic Reasoning Layer that consumes Phase 5's normalized context ([0eea6cd])

### Changed

- **CI Java toolchain bumped to JDK 21** (was 11) — required by google-java-format 1.33.0 which references `com/sun/tools/javac/tree/JCTree$JCAnyPattern` (Java 21+). Bytecode targets unchanged: each Flink pom keeps `<maven.compiler.source/target>11</>` ([9abab8b], [a101019])
- **Spotless plugin upgraded** 2.46.1 → 3.4.0 across all Flink poms; `<importOrder/>` and `<removeUnusedImports/>` removed so google-java-format owns ordering end-to-end ([178f400])
- **Java formatting authority consolidated to Spotless** — the `pretty-format-java` pre-commit hook was diverging from Spotless's import handling on every commit (likely a JVM-version effect between pre-commit's bundled JRE and the Maven JVM); the hook was removed and `mvn spotless:apply` is now sole authority ([178f400])
- **`markdownlint` allowed_elements** — added `p` and `em` to MD033 allow-list for the README's centered architecture-image pattern ([a101019])
- **Normalizer package discovery** — `src/normalizer/pyproject.toml` switched from explicit `packages = ["app"]` to `[tool.setuptools.packages.find]` with `include=["app*"]` so newly added subpackages auto-discover ([6471248])

### Fixed

- **Normalizer wheel was missing `app.normalizers` and `app.routes` subpackages** — `pyproject.toml` declared `packages = ["app"]` which ships only top-level `app/` files; pods crashed at startup with `ModuleNotFoundError: No module named 'app.normalizers'` and were CrashLoopBackOff on dev cluster for ~22h before discovery during v0.8.0 cluster verify ([6471248])
- **Backend `ruff` UP042 violations on CI Lint** — root `ruff.toml` added UP042 to ignore, but `src/backend/pyproject.toml` has its own `[tool.ruff]` block which wins by setuptools' nearest-config precedence; UP042 added to the backend block too ([178f400])
- **Markdownlint debt cleared** across 6 docs files: heading-increment in `AWS_INFRA_ACTION_PLAN.md` (4×) and `NAMING_CONVENTION.md`; table-pipe-style + table-column-count in `DOMAIN_VOCABULARY.md` (3 tables); trailing whitespace in `DOMAIN_VOCABULARY.md` + `BRAINSTORM.md` + `Brainstorm-Discussion.md` + `FEEDBACK_LOOP.md`; missing trailing newline in `STACK.md`; broken link fragment in `EKS_OPERATIONS.md`; duplicate `## References` heading in `roadmap/TASKS.md` ([a101019])
- **Yamllint long-line errors** in `.github/workflows/normalizer-image.yml` (lines 41 / 108 / 109 exceeded 120 chars) — refactored URL into shell vars and grouped step-summary echoes into a single redirect block ([9abab8b])
- **GHCR provenance-attestation rejection** on normalizer image push — added `provenance: false` to `docker/build-push-action@v5` step ([bed15fa])
- **Editable-install package discovery** in CI for the normalizer test job ([88a1940])
- **Hadolint DL3008 false-positive** on normalizer Dockerfile — suppressed to match the existing backend Dockerfile pattern ([d139725])

### Internal

- **`.gitignore`** now excludes `.claude/`, `.cursor/`, and `.codex/` from remote tracking; previously-tracked AI-tooling files removed from the repo ([ab8dfde], [1823fe0], [02656f3])
- Editor-config tweaks consolidated under the gitignore work ([73c1c65], [a90e5d9])

---

## [0.4.0] - 2025-01-14

### Phase 4: Real-time - Complete

#### WebSocket Infrastructure (Sprint 4.1)

- **Connection Manager**
  - Channel-based subscriptions (services, anomalies, pipelines, kubernetes)
  - Automatic reconnection with exponential backoff
  - Heartbeat/ping-pong for connection health
  - Broadcast events to subscribed clients

- **Frontend Integration**
  - `useWebSocket` hook for real-time connections
  - `useRealtimeServices` hook for service updates
  - `useRealtimeAnomalies` hook for anomaly alerts
  - `useRealtimePipelines` hook for pipeline status
  - `useRealtimeKubernetes` hook for K8s updates
  - TanStack Query cache invalidation on events
  - Connection status indicator component

#### Kubernetes Adapter (Sprint 4.2)

- **Backend Adapter** (`src/backend/app/adapters/kubernetes.py`)
  - Mock/Live mode switching via environment
  - Cluster info and health status
  - Namespace listing and management
  - Node status with resource metrics (CPU/Memory)
  - Deployment status with replica counts
  - Pod health with container states
  - Pod log retrieval

- **API Routes** (`/api/v1/kubernetes`)
  - `GET /cluster` - Cluster information
  - `GET /stats` - Aggregate statistics
  - `GET /namespaces` - List namespaces
  - `GET /nodes` - List nodes with metrics
  - `GET /deployments` - List deployments
  - `GET /deployments/{ns}/{name}` - Deployment details
  - `GET /pods` - List pods
  - `GET /pods/{ns}/{name}/logs` - Pod logs

- **KubernetesLayer Component**
  - View modes: Overview, Deployments, Pods, Nodes
  - Stats cards with health indicators
  - Resource utilization progress bars
  - Real-time status updates
  - Collapsible deployment details

#### CI/CD Workflows (Sprint 4.3)

- **Unified CI Workflow** (`.github/workflows/ci.yml`)
  - Lint job: Ruff (Python) + ESLint (TypeScript) + TypeCheck
  - Security job: Gitleaks + Snyk
  - Test Backend: pytest with coverage → Codecov
  - Test Frontend: vitest with coverage → Codecov
  - Build: Docker (backend) + Next.js (frontend)
  - CI Success gate for all jobs

- **Supporting Workflows**
  - Release workflow with Changesets
  - Changeset validation on PRs
  - Auto-labeler for packages
  - Labels sync from configuration

#### Bug Fixes

- Fixed hydration mismatch in LayerPanel (DndContext client-only rendering)
- Fixed `layer.glueKeys` undefined error with optional chaining
- Added placeholder UI for server-side rendering

#### Repository Maintenance

- Added TypeScript, ESLint, Ruff, Snyk badges to README
- Updated .gitignore with AI/Codex directory exclusions
- Removed tracked .codex directories from repository

---

## [0.3.0] - 2025-01-12

### Phase 3: Experience - Complete

#### Frontend Dashboard (Next.js 14+)

- **Layer Architecture Implementation**
  - LayerPanel with visibility toggles and drag reordering
  - LayerRenderer with lazy loading and Suspense boundaries
  - GlueBus pub/sub system for cross-layer communication

- **Layer Components (5 layers)**
  - ServicesLayer: Service catalog with health status, filtering, actions
  - TemplatesLayer: Golden path templates with recommendations
  - AnomaliesLayer: Anomaly detection with acknowledge/resolve workflows
  - PipelineLayer: GitHub workflow runs and deployment status
  - MetricsLayer: DORA metrics, health scores, deployment stats

- **UI Components (shadcn/ui)**
  - Card, Button, Badge, Skeleton, Progress, Accordion
  - Custom StatusBadge, ServiceCard, MetricCard components
  - Responsive design with Tailwind CSS

- **State Management**
  - Zustand store for layer state persistence
  - TanStack Query for data fetching with caching
  - Real-time updates with configurable refresh intervals

#### Backend Enhancements

- **Anomalies API** (`/api/v1/anomalies`)
  - Full CRUD operations
  - Acknowledge/Resolve workflows
  - Filtering by severity, type, status
  - Statistics endpoint

- **Metrics API** (`/api/v1/metrics`)
  - Comprehensive dashboard metrics
  - DORA metrics calculation
  - Service health aggregation
  - Deployment statistics

- **Live Adapters**
  - GitHubLiveAdapter: Repository info, workflow runs, commits
  - ArgoCDLiveAdapter: Application sync status, health checks
  - Mock/Live mode switching via environment variables

#### Testing & Quality

- 31 frontend tests (unit + integration)
- Accessibility audit (WCAG 2.1 AA compliance)
- Performance optimization (lazy loading, memoization)
- TypeScript strict mode compliance

#### Documentation

- Comprehensive API documentation (`docs/API.md`)
- 10 Mermaid architecture diagrams (`docs/diagrams/SYSTEM_DIAGRAMS.md`)
  - System Context (C4 L1)
  - Container Diagram (C4 L2)
  - Component Diagrams (C4 L3) - Backend & Frontend
  - Data Flow, Deployment, Sequence Diagrams
  - ERD, Layer Architecture, Adapter Pattern diagrams

---

## [0.2.0] - 2025-01-08

### Phase 2: Intelligence - Complete

#### Added

- ML Template Recommender endpoint (`POST /api/v1/templates/recommend`)
- Rule-based recommendation model
- Anti-pattern warning detection
- Override logging and audit trail
- Training data generation (750+ synthetic records)
- Workload-to-template scoring logic

#### Technical Details

- Recommendation input: workload_type, language, requirements
- Recommendation output: ranked templates with scores, warnings
- Response time target: <500ms achieved

---

## [0.1.0] - 2025-01-08

### Phase 1: Foundation - Complete

#### Added

- TurboRepo + PNPM monorepo architecture
- FastAPI backend structure
- Service Catalog API with full CRUD operations
  - `GET /api/v1/services` - List all services
  - `GET /api/v1/services/{id}` - Service detail
  - `POST /api/v1/services` - Create service
  - `GET /api/v1/services/stats` - Service statistics
- Template API with ML-powered recommendations (rule-based Phase 1)
  - `GET /api/v1/templates` - List templates
  - `GET /api/v1/templates/{id}` - Template detail
- Database schema with Alembic migrations
- Database models: Team, Service, Template, Anomaly, Recommendation, Action
- Async SQLAlchemy with PostgreSQL support
- Pydantic schemas for request/response validation
- Seed data for demo purposes
- Health check endpoints with adapter status
- Mock adapters for GitHub and ArgoCD integrations
- Docker Compose for local development
- PNPM workspaces for frontend/backend/shared packages
- Comprehensive documentation (MONOREPO_SETUP.md, LOCAL_DEV.md)
- Project configuration files (LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md)
- Integration tests with pytest-asyncio

#### Infrastructure

- PostgreSQL 15 database
- GitHub adapter with mock mode for repositories, branches, commits, PRs, and workflows
- ArgoCD adapter with mock mode for applications, sync operations, and deployment status

---

## [0.0.1] - 2025-01-06

### Phase 0: Planning - Complete

#### Added

- Initial project scaffold
- Project vision and identity (`planning/VISION.md`)
- Feature scope definition (`planning/SCOPE.md`)
- System architecture design (`decisions/ARCHITECTURE.md`)
- Technology stack selection (`decisions/TECH_STACK.md`)
- Architectural Decision Records (ADR 001-006)
- MVP definition (`docs/MVP.md`)
- Success criteria (`docs/SUCCESS_CRITERIA.md`)
- Golden Path requirements (`docs/GOLDEN_PATH_REQUIREMENTS.md`)
- Phase-based roadmap (`roadmap/PHASE.md`)
- Task management framework (`roadmap/TASKS.md`)
- Prioritization framework (`roadmap/PRIORITIZATION.md`)
- Action plan templates (`roadmap/ACTION_PLAN.md`)

---

## Version History Summary

| Version | Phase                 | Status       | Date       |
| ------- | --------------------- | ------------ | ---------- |
| 1.0.0   | Phase 5: Intelligence | Planned      | TBD        |
| 0.4.0   | Phase 4: Real-time    | **Complete** | 2025-01-14 |
| 0.3.0   | Phase 3: Experience   | Complete     | 2025-01-12 |
| 0.2.0   | Phase 2: Intelligence | Complete     | 2025-01-08 |
| 0.1.0   | Phase 1: Foundation   | Complete     | 2025-01-08 |
| 0.0.1   | Phase 0: Planning     | Complete     | 2025-01-06 |

---

## Links

- [Phase Definitions](roadmap/PHASE.md)
- [Task Management](roadmap/TASKS.md)
- [Phase 3 Action Plan](roadmap/ACTION_PLAN_PHASE3.md)
- [Layers Architecture](docs/features/LAYERS_ARCHITECTURE.md)
- [Prioritization Framework](roadmap/PRIORITIZATION.md)
