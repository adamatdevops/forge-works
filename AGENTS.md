# AGENTS.md — forge-works doctrine for AI agents

> **Audience.** Any AI agent operating inside this repository (Codex, Claude Code, future agents). Codex reads this file automatically per session. Treat the rules below as binding unless explicitly overridden by the user in the current session.
>
> **Companion file:** `CLAUDE.md` (not present at root yet — Claude Code currently loads guidance from `.claude/` and auto-memory). The two files agree on doctrine; this one is the source of truth.

---

## 1. What this repo is

**forge-works** is an Internal Developer Platform (IDP) that orchestrates service creation through ML-guided golden-path templates and provides visibility into a service ecosystem. It is NOT a deployment tool, NOT a Kubernetes replacement, NOT a full PaaS.

**Intent.** Portfolio-grade demonstration of platform engineering, governance-through-design, and ML-assisted decision support. The platform's posture is _agentless_ (no autonomous agents in the runtime loop) and _orchestration-not-replacement_ (we coordinate existing tools; we don't reimplement them).

**Explicit scope denials** (these are out-of-scope, not "future work"):

- ❌ Infrastructure provisioning (Terraform/Pulumi/Crossplane orchestration is not the platform's job)
- ❌ Cluster management (we run _on_ Kubernetes, we don't manage Kubernetes)
- ❌ GitOps control plane (no ArgoCD / Flux orchestration role)
- ❌ Autonomous ML (no agent loops making unsupervised production decisions)

**Stack surfaces** (one-line each):

- **Backend** (`src/backend/`) — FastAPI · Python 3.11+ · uv lockfile (`uv.lock`) · ruff (lint+format) authority · pytest + Codecov flags
- **Frontend** (`src/frontend/`) — Next.js 14+ · TypeScript strict · Tailwind · vitest + Codecov flags
- **Flink jobs** (`src/flink-jobs/`) — 3 modules (event-router, insight-generator, pattern-matcher) · Java 21 (bytecode target 11) · Spotless (google-java-format 1.33.0 AOSP) · SpotBugs at `effort=Max threshold=Low failOnError=true`
- **Normalizers** (`src/normalizer/`) — Python · 3 source-specific deployments (Kubernetes, Terraform, GitHub Actions) · CUE↔Pydantic schema fidelity gate · DLQ on exception · `FW_EXPECTED_SOURCE` isolation guard
- **Infra** (`infra/`) — kustomize YAML today (Terraform planned per `infra/iam/trust-policies/fw-forge-engine-normalizer-terraform-sa-trust.json`)
- **Roadmap** (`roadmap/`) — phase plans + AB-NNN backlog (gitignored; local-only)

**Versioning & release.** Conventional Commits + manual `git tag` today; release-please planned (AB-001). See `docs/decisions/RELEASE_TOOLING.md`.

---

## 2. Authority — who decides what

- **Git commit / push** — user is sole authority. Agents edit and report; the user commits and pushes. No `git commit`, no `git push`, no `git tag` from agents without explicit per-instance approval.
- **Branch protection** — `main` requires up-to-date branches (`strict: true`) and passing required Check Runs.
- **Release process** — manual `git tag` interim; release-please target (AB-001).
- **PR status labels** — every PR carries one `pr status:{opened,review,merged,closed}` label. `status:blocked` is orthogonal. Automated by `.github/workflows/pr-status-labeler.yml`; mirrored in `.github/labels.yml`.
- **Decision Records** — any new third-party tool (Action, App, MCP server) gets a Decision Record before adoption. Templates live in:
  - `research/github_actions/GITHUB_ACTIONS.md` §7
  - `research/github_apps/GITHUB_APPS.md` §7
  - `research/mcp/MCP_SERVERS.md` §7
- **Backlog** — non-trivial fixes go in `roadmap/AUTOMATIONS_BACKLOG.md` as `AB-NNN` entries with Priority / Effort / Phase / Why / Scope / Dependencies / Acceptance Criteria. Not one-liner notes. The file is gitignored (`/roadmap/` in `.gitignore:9`).

---

## 3. Doctrine — non-negotiable rules

### 3.1 Security & supply chain

- **SHA-pin third-party GitHub Actions** per `research/github_actions/GITHUB_ACTIONS.md` §2D. First-party (`actions/*`, `github/*`) may use major-version tags; everything else gets a 40-char SHA + `# vN.x.x` comment. The tj-actions/changed-files compromise (CVE-2025-30066) is the canonical reason. Current pin-policy debt tracked as AB-006.
- **OSS CLI preferred over Marketplace App** when both exist for the same scanner (Checkov OSS in CI, not Bridgecrew App; Trivy/Gitleaks/Hadolint OSS, not their SaaS variants). Less data egress, no permission grant, no Required-Check zombification risk on uninstall.
- **Snyk for whole-tree CVE scanning** — App-driven (installed 2026-05-12), `.snyk` policy at repo root, dated ignores with re-evaluation dates.
- **No secrets in repo.** Use repo secrets or AWS OIDC (planned). `gitleaks` runs in CI; pre-commit `detect-secrets` runs locally. The Sentry release-deploy URL is treated as a secret (token-bearing segment in the URL itself).
- **PII redaction default ON** in observability — `sentry_sdk.init(send_default_pii=False, ...)` is non-optional.

### 3.2 AI-assisted tooling — advisory-only

- AI tools comment, suggest, and review. They never auto-commit to protected branches, never auto-merge, never modify workflow files. CodeRabbit configured with `request_changes_workflow: false`; Codex CLI runs in `--sandbox read-only` for the feedback loop.
- Codex GitHub App is explicitly **skipped** — CodeRabbit covers PR-time AI review; Codex value is consumed via the CLI loop (`/codex-review`) for pre-commit doctrine validation. See `research/github_apps/evaluation_list.md`.
- Training-data opt-out is verified at the dashboard layer for every AI tool before adoption (CodeRabbit gate 1, ChatGPT/Codex data controls).

### 3.3 Quality gates

- **Conventional Commits.** One-sentence subjects (`feat(scope): …`, `fix(scope): …`, `chore(scope): …`, `docs(scope): …`). Narrative goes to `CHANGELOG.md` with SHA refs `([abc1234])`. No bodies on commits unless the SHA-ref doesn't fit.
- **`CHANGELOG.md` format** — [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections (Added / Changed / Deprecated / Removed / Fixed / Security). Each bullet states the _why_, links to SHA(s), and references CVE numbers / framework sections where applicable.
- **pre-commit owns formatting.** 18 hooks across 7 repos (trailing-whitespace, end-of-file-fixer, check-yaml/json/toml, check-merge-conflict, mixed-line-ending, ruff lint+format, prettier, yamllint, markdownlint-cli2, shellcheck, hadolint, detect-secrets). See `docs/PRE_COMMIT_EVALUATION.md`. CI does not re-author code — prettier/ruff in CI would duplicate the gate; both are explicitly NOT wired in `ci.yml`.
- **No `// removed` / `// TODO(legacy)` comments.** Delete unused code outright. No backwards-compat shims, no renamed `_var` placeholders.
- **No multi-paragraph docstrings.** One short line max. Comments explain WHY (non-obvious constraints), not WHAT (the code).

### 3.4 Tier classification — third-party tools

Per `GITHUB_ACTIONS.md` §4 and `GITHUB_APPS.md` §4:

- **Tier 1** — read-only, no secrets. Default for linters, SAST, formatters in check-only mode.
- **Tier 2** — repo writes, scoped secrets. Allowed but guarded; requires SHA-pin + explicit `permissions:` block + Decision Record.
- **Tier 3** — deployment / privileged. Allowed only on critical release path; first-party or Verified Creator; OIDC over static creds.

Most tools should be Tier 1. Tier 3 is limited to a handful (cloud auth, registry login, release publishing, image signing).

### 3.5 ML posture — Decision Engine outputs

The platform's _own_ ML outputs (golden-path recommendations, decision support, scoring) follow a strict advisory posture — distinct from §3.2 which governs AI _dev tools_:

- **Assistive, not autonomous** — ML proposes, humans dispose. No model output executes without an explicit user action.
- **Explainable required** — every recommendation surfaces inputs + confidence + reasoning. Black-box models do not ship.
- **Override required** — every recommendation is overridable. UI/UX makes override a first-class action, not a hidden affordance.
- **Confidence required** — recommendations carry a confidence signal; low-confidence outputs are flagged, not hidden.
- **No production serving** — the platform does not host model serving in the production critical path. Inference is offline / advisory / pre-computed.

Governance model: **design, not policy.** Constraints are baked into the platform's affordances (what the UI/API lets you do); they are not enforced via after-the-fact policy engines.

### 3.6 External authoritative docs

Architecture, planning, and platform doctrine live in an external design workspace outside this repository (ADRs, planning, roadmap, vendor evaluations). Rules:

- **External docs are canonical.** When local code or agent suggestions conflict with external docs, external docs win.
- **Don't copy external content into the repo.** Reference and cite; do not duplicate. External docs are the source of truth; copies rot.
- **Don't infer missing requirements.** If a constraint isn't in the external docs or this file, ask before assuming. Especially when changes touch architecture, ML posture, or platform boundaries.
- **Warn on overclaim.** Don't describe in-progress work as shipped, and don't describe demonstrations as production-grade. Match the artifact's actual maturity.

---

## 4. Process patterns

### 4.1 Planning → execution flow

Non-trivial work (new feature, sprint, architectural change) follows:

1. **Plan** — `roadmap/ACTION_PLAN_*.md` (e.g. `ACTION_PLAN_ENGINE_PHASE-5.md`). Plan first, code second.
2. **Backlog** — automation work / infra-debt lands in `roadmap/AUTOMATIONS_BACKLOG.md` as `AB-NNN` entries.
3. **Implementation** — small commits, Conventional Commits subjects.
4. **CHANGELOG** — narrative bullet per logical change, with SHA refs.
5. **PR** — labels auto-applied; CodeRabbit review (advisory); CI gates.
6. **Merge** — user only; branch protection enforces.

### 4.2 Pre-commit doctrine validation — Codex feedback loop

For Decision Records, evaluations, and substantial design docs:

1. Author the artifact (Claude Code).
2. Run `/codex-review <artifact-path>` — Claude packages a critique prompt, invokes `codex exec --profile review`, captures the response.
3. Codex returns structured findings (JSON, validated against `research/feedback_loops/codex-finding-schema.json`).
4. Claude classifies each finding (agree/disagree/gap/nit) with framework citations; user decides which to apply.
5. Patches land in the artifact with provenance ("Surfaced by Codex round-N critique loop (YYYY-MM-DD)").

Quality bar — every loop output must:

- Cite framework section explicitly (`§2D`, `§4`, `§7`).
- Verify against repo state before patching (`Read`/`grep`/`Bash`).
- Propagate to sister documents (patterns shared across files patched together).
- Honor template fully — no placeholders in new Decision Records.
- File proper `AB-NNN` backlog entries (not one-liners) for out-of-scope work.
- Counter when warranted — the loop is bidirectional, not rubber-stamp.

Full convention: `research/feedback_loops/README.md`.

### 4.3 Decision Records

Any third-party tool adoption requires a Decision Record with all 13 fields from the relevant framework §7 (URL · Source · Goal · Tier · Score · Verified · Action type · Pin policy · Permissions · Secrets · OIDC · Runner · Renovate-tracked · Owner · Removal · Notes). No "TBD", no skipped fields. If a field doesn't apply, write `n/a` with a one-line justification.

### 4.4 Skill adoption — third-party agent skill integration process

> Binding adoption gate for any skill from `research/agents/evaluation_list.md`. **Don't register a skill in any agent's load order without completing this process.** Framework: `research/agents/AGENT_SKILLS.md` (selection criteria, tiers, threat model). This section is the operations manual.
>
> **Dual-agent skill delivery.** Skills are shared between Claude Code and Codex CLI — same content, same Source SHA, both agents load identically. The mechanism: register the **`forge-skills`** MCP server (built in-house under `tools/forge-skills-mcp/`; supersedes the upstream `claude-skills-mcp` which is broken in v1.0.0) in **both** `~/.codex/config.toml` (under `[mcp_servers.forge-skills]`) and Claude Code's MCP config (via `claude mcp add forge-skills -- ...`). Once registered in both places, "served via forge-skills" in a Decision Record's `Adoption mode:` field means **both agents** see the skill — not Claude only. Hierarchy: Claude Code is senior on implementation + analysis; Codex is the independent reviewer (see §4.2). The user is decision authority on adoption + commit.
>
> **Codex sandbox constraint** (documented 2026-05-16): forge-skills MCP tool calls work in Claude Code, in interactive Codex TUI (under any sandbox), and in `codex exec --sandbox danger-full-access`. They **do not** work in `codex exec --profile review` (sandbox=read-only, approval=never) or other sandboxed non-interactive runs — Codex auto-cancels MCP tool calls in those modes by design (`error: "user cancelled MCP tool call"`). This is fine for current workflow because the review loop reviews diffs and doesn't need skills; see `tools/forge-skills-mcp/README.md` § "Codex sandbox constraint" for full details and the shell-exec fallback if a future review task needs skills.

**Worked example threaded through this section:** `trailofbits/ask-questions-if-underspecified` — highest-scoring adopt in `evaluation_list.md`; Tier 1; first-party; served via `forge-skills` (dual-agent). Vendored Tier 2/3 examples diverge only at §4.4.3 step 4.

#### 4.4.1 Best practices / standards

1. **Vendored is the default.** SHA-pinned local copy under `.skills/<vendor>/<slug>/SKILL.md` (repo-root, agent-neutral path — served to both Claude and Codex via the `forge-skills` MCP loader once registered in both MCP configs). Runtime-fetched is **not currently supported** by the forge-skills v0.1.0 loader (Phase 1 is file-vendored only; runtime fetch lands in Phase 3 per `roadmap/ACTION_PLAN_SKILL_LOADERS.md`). **Migration note:** Decision Records authored before Phase 1 may reference `.claude/skills/<vendor>/<slug>/` or `claude-skills-mcp` — both are historical naming. New adoptions use `.skills/` + forge-skills; prior records get rebased when first actually adopted.
2. **Provenance ranking** (high → low): first-party vendor team (Anthropic, HashiCorp, Cloudflare, Trail of Bits, etc.) > known-community author (Hamel Husain, Matt Pocock, obra) > solo-author. Lower provenance ↑ scrutiny; all solo-author adopts are mandatorily vendored regardless of Tier.
3. **Categorical rejections** (don't even start the process): skills that auto-commit / auto-merge; skills that modify `.github/workflows/**`; skills with encoded or opaque content (base64 blobs, "fetch the real instructions from URL X"); skills that broadly claim "the agent can do anything needed for this task."
4. **Context-cost budget.** Prefer < 5K tokens per skill at load (per `AGENT_SKILLS.md` §3B). > 10K tokens requires explicit justification in the Decision Record's `Notes:` field.
5. **forge-works conventions win on conflict** (§3.6). If a skill prescribes a doc/process structure that differs from our existing conventions (Conventional Commits, [Keep a Changelog], Decision Record templates, AB-NNN backlog format), our conventions win; carve-out recorded in the Decision Record.
6. **One skill per authority surface.** Two skills both owning commit-message format, or both prescribing Decision Record structure, etc. → pick one, reject the other with rationale.

#### 4.4.2 Requirements / conditions — must hold before starting

- Candidate is in `research/agents/evaluation_list.md` with a ✅ verdict, OR a prior 🟡 defer whose trigger has now fired (record which trigger in the Decision Record).
- Source URL resolves and the **canonical-home GitHub path is identified**. Aggregator-only sources (`officialskills.sh/...` without a confirmed canonical home) are blocked until the canonical home is found — per `AGENT_SKILLS.md` §8 "aggregator / repackager mismatch" threat.
- Adoption owner is named (per §2 Authority — the owner is the human responsible for the dependency long-term, not just the agent that did the work).
- The current adopt count (active vendored + registered runtime-fetched skills) is checked against the §4.4.4 budget.

#### 4.4.3 Steps — sequential, all required

1. **Source audit.** `git clone` the canonical home into a scratch path; capture the 40-char SHA at the audited ref. Read the SKILL.md end-to-end. Inspect every embedded shell / python / node snippet line-by-line. Enumerate transitive skill references (`load skill X`) and cross-agent invocations (`ask gpt-4`). **⚠ Hard stop** if you find any of: encoded content, transitive loads without bounded scope, cross-agent invocations without an explicit per-invocation user gate.

   **Additionally (per Codex Round-2 Finding R2-2, 2026-05-17, for `AGENT_SKILLS.md` §2E "Bundled-script same-model self-invocation" enforceability):** for any vendored executable script (any file under `scripts/`, `bin/`, `tools/`, or with a shebang line), scan for process-spawn primitives (`subprocess.Popen`, `subprocess.run`, `os.system`, `os.exec*`, `shell=True` paths, IPC primitives) AND model-client invocation tokens (`claude`, `anthropic`, model-SDK imports/calls like `messages.create`, env-variable-indirected command construction where the variable defaults to or could be overridden to one of those). Document every match in the Decision Record's Notes with file path + line range. Unresolved indirection (e.g., a command built from an env var with no audited default) defaults to **Tier 3** per §2E "Fail-closed default for inconclusive cases".

   _Example:_ `git clone github.com/trailofbits/skills /tmp/audit-trailofbits` → SHA `<40-char>`; `ask-questions-if-underspecified/SKILL.md` is plain prose, ~900 tokens, no shell, no transitive refs, no cross-agent, no vendored scripts. Proceed.

2. **Tier confirmation.** Observed tool scope (read-only / shell-execute / repo-write / network / cross-agent / external-write) → `AGENT_SKILLS.md` §4 Tier. If the observed Tier differs from the eval-list Tier, update the Decision Record and re-justify before proceeding.

   _Example:_ Tier 1 (read-only). Matches the eval-list assignment.

3. **Decision Record completion.** Replace every placeholder in the `AGENT_SKILLS.md` §7 14-field template with measured values: real `Source SHA`, real `Context cost` (count tokens with `tiktoken` or the loader's counter — don't ship the eval-list rough estimate), real `Tool scope`, real `Removal procedure`. No `<verify at adoption review>` markers may survive into the recorded artifact.

   **Additionally (per §4.5.5 atomic co-edit doctrine, added 2026-05-16):** add a row to the §4.5.1 trigger table for the newly-adopted skill with a specific trigger condition + tier + pairing; add a per-skill entry to the §4.5.3 Policy Gates Index listing all load-bearing gates (use "no policy gates" for Tier-1 skills with no special constraints). Both edits land in the SAME PR as the Decision Record update — no defer.

   _Example:_ `Source SHA: <sha>` · `Context cost: ~900 tokens (measured via tiktoken cl100k_base)` · `Adoption mode: vendored via forge-skills` · `Removal: delete .skills/trailofbits/ask-questions-if-underspecified/ directory`.

4. **Adoption.** The forge-skills loader serves vendored skills from `.skills/<vendor>/<slug>/SKILL.md` to both agents over MCP. Phase 1 is **file-vendored only** (runtime fetch lands in Phase 3 — see `roadmap/ACTION_PLAN_SKILL_LOADERS.md`).
   - **All skills (Tier 1-3):** create `.skills/<vendor>/<slug>/`, copy the audited `SKILL.md` + any companion files verbatim with YAML frontmatter conforming to `tools/forge-skills-mcp/README.md` § "SKILL.md frontmatter schema" (name, vendor, slug, source-url, source-canonical, source-sha, audited, goal, tier, tool-scope, target-agents, context-cost-tokens, owner). The loader rescans on each `list_skills` call — no service restart needed.

   _Example:_ Vendor `trailofbits/ask-questions-if-underspecified` at `.skills/trailofbits/ask-questions-if-underspecified/SKILL.md` with the audited 40-char SHA in frontmatter. Both Claude Code (`mcp__forge-skills__list_skills`) and interactive Codex (after Allow prompt) see the new skill on next call — no session restart needed because the scanner re-walks on each invocation.

   **Dual-agent verification:** after adoption, confirm Claude sees the skill via `mcp__forge-skills__list_skills` (it should appear in the `skills` array). For Codex, use **interactive `codex` TUI** with a probe like _"Call forge-skills list_skills and tell me which skills are registered"_ — `codex exec --profile review` is not a valid verification path because MCP auto-cancels under read-only sandbox (see §4.4 preamble Codex constraint note). Asymmetric visibility means the MCP server is registered on only one side, or the SKILL.md frontmatter failed validation — fix before declaring step 4 complete.

5. **Smoke test / validation.** Invoke the skill on a small, bounded task with deliberate edge cases (an underspecified request for a clarifying-questions skill; a benign file write for a write-scoped skill; etc.). Observe:
   - Does the skill operate strictly within declared scope? (No surprise tool calls outside the Tier.)
   - Does its output respect §3.2 advisory-only? (No auto-commits, no workflow edits, no destructive git.)
   - Does the measured context cost match the §4.4.3 step-3 estimate within ±20%?

   **⚠ Roll back** if any answer is no: deregister / delete the vendored copy, file a bug against the upstream skill, requeue in the eval list as 🟡 defer with the failure recorded.

   _Example:_ Invoke on a deliberately underspecified prompt (`"clean up the file"`). Skill responds with clarifying questions (target file, definition of "clean up", success criteria), no tool calls beyond reads. Validation pass.

6. **Codex doctrine review.** Run `/codex-review` on the Decision Record (the record is itself a doctrine-relevant artifact per §4.2 quality bar). Apply Codex's findings or counter with framework citations.

7. **Commit & changelog.** One-sentence Conventional Commits subject: `feat(skills): adopt <vendor>/<slug> via <mode>`. `CHANGELOG.md` bullet under `### Added` with SHA refs (commit + audited skill SHA) and one-line rationale.

#### 4.4.4 Criteria — adopt vs defer vs skip

| Signal                                                                                          | Decision                                                 |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Eval-list score sum ≥ 28 (across the 7 axes of `AGENT_SKILLS.md` §5) AND no hard-stop at step 1 | **Adopt**                                                |
| Score 20–27 AND a near-term, observable trigger exists                                          | **🟡 Defer** with trigger recorded                       |
| Score < 20 OR hard-stop at step 1                                                               | **❌ Skip** with one-line rationale                      |
| Score ≥ 28 but the adopt-count budget is exhausted (> 30 active skills)                         | **🟡 Defer** with displacement candidate identified      |
| Skill is Tier 3 (cross-agent / external-write)                                                  | **Decision Record + per-invocation user gate** mandatory |

The 30-skill budget is a soft cap to prevent context-window flood and audit-debt accumulation. If exceeded, retire a lower-scoring incumbent before adopting.

#### 4.4.5 Validation — after adoption (ongoing)

- **First-run audit** within the first 3 invocations: re-check tool scope and §3.2 compliance in actual use. Easier to catch drift early than after the skill is load-bearing.
- **Source-SHA tracking.** Renovate does not cover agent skills today. Manual quarterly review (calendar reminder, owned by the named Decision Record owner) compares the recorded SHA against the canonical home's current state. Any update lands as a PR through this same process — never auto-update.
- **AGENTS.md conflict check.** When this file changes, re-read every adopted skill's Decision Record `Notes:` carve-outs to confirm they still hold against the new doctrine.
- **Telemetry-light observation.** Note in the session transcript when a skill fires; if a skill never fires across 30 days of relevant work, queue it for removal (the adopt-budget slot is more valuable than the unused skill).

#### 4.4.6 Removal — when, how

A skill is removed when **any** of these conditions hits:

- Source-SHA tracking surfaces a malicious or quality-degrading upstream update.
- First-run audit or later use shows §3.2 / §3.6 violations.
- A higher-scoring alternative covers the same authority surface (skill-displacement).
- The adopt-count budget needs to free a slot for a higher-priority adoption.
- The skill has not fired across 30+ days of relevant work (per §4.4.5 telemetry-light observation).

Procedure (executed from the Decision Record's `Removal procedure:` field):

1. `git rm -r .skills/<vendor>/<slug>/` — both Claude and Codex stop seeing the skill on next `list_skills` call (the forge-skills scanner rescans per request).
2. Update `CHANGELOG.md` under `### Removed` with reason + SHA refs.
3. **Remove the corresponding §4.5.1 trigger-table row + §4.5.3 Policy Gates Index entry** (per §4.5.5 atomic co-edit). Same PR; no defer.
4. If credentials were associated with the skill, rotate them; record rotation in the same commit.

### 4.5 Skill invocation triggers — runtime rules for adopted skills

§4.4 governs **adoption** (selection, vendoring, scoring, validation, removal). This section governs **runtime invocation** — when an agent should call `mcp__forge-skills__get_skill(<slug>)` on a skill that's already been adopted. Adoption alone does not invoke a skill: the forge-skills MCP loader serves content on demand; agents must deliberately fetch.

**When a trigger condition listed below fires, the agent MUST consult the named skill before proceeding.** "MUST" matches the hardness of surrounding doctrine (§3.6 "don't infer", §4.4.3 "all required") — skipping a fired trigger silently is a doctrine breach catchable in `evaluation_list.md` Codex review or §4.4.5 first-run audit.

**Exception (single, narrow):** when running under `codex exec --profile review` (read-only sandbox + approval=never), Codex 0.130.0 auto-cancels `mcp__forge-skills__*` calls by design (per the §4.4 preamble Codex constraint note). In that path, the agent MUST:

1. Cite the constraint in the session transcript explicitly ("Skill X unavailable under codex review profile per AGENTS.md §4.4 preamble + §4.5 exception").
2. **Read the vendored skill content directly from `.skills/<vendor>/<slug>/` via the agent's Read tool** — these files are in the read-only sandbox and are the same content the MCP loader would have served. Quote the specific section(s) used so the reviewer can verify which doctrine was applied.

The fallback is NOT "derive the workflow from `AGENT_SKILLS.md` inline" — `AGENT_SKILLS.md` is the selection framework, not per-skill content. Workflow detail lives in the vendored `methodology.md` / companion files.

Interactive Claude Code and interactive `codex` TUI sessions invoke normally — the exception applies only to the non-interactive `codex exec --profile review` path.

#### 4.5.1 Trigger table

| Trigger condition                                                                                                                                                                                                                                         | Skill                                            | Tier                                                | Pairing                                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------- |
| User request is underspecified — missing inputs, multiple plausible interpretations, or assumes context the agent doesn't have (e.g., "fix the bug", "make the API better")                                                                               | §F `trailofbits/ask-questions-if-underspecified` | 1                                                   | lifecycle bookend with §AF (task-start)                                   |
| About to declare a task complete (e.g., "shipped", "done", "PR ready", "✅ tests pass", "ready to commit")                                                                                                                                                | §AF `obra/verification-before-completion`        | 1                                                   | lifecycle bookend with §F (task-end)                                      |
| About to read or review sensitive code (auth boundaries, IAM, crypto, normalizer redaction, ML advisory paths, Sentry PII handling, any code touching secrets-bearing surfaces)                                                                           | §G `trailofbits/audit-context-building`          | 1                                                   | precedes §H (chained, when both apply)                                    |
| PR / commit / diff security review (e.g., "review PR #N", "is this safe to merge", "security-review the changes since X", "Flink 1.20→2.0 version-bump review")                                                                                           | §H `trailofbits/differential-review`             | 2                                                   | follows §G (chained, when both apply)                                     |
| Create / modify / improve a skill, run skill evals, optimize skill description for triggering accuracy, benchmark skill performance, or package a skill (e.g., "turn this workflow into a skill", "evaluate this skill", "improve skill X's description") | §D `anthropics/skill-creator`                    | 2 (with intra-skill Tier-3 escalation on 3 scripts) | may pair with §F when the create-a-skill request is itself underspecified |

Policy-gates column intentionally omitted from the trigger table; gates live in §4.5.3 (Policy Gates Index) — per-skill, with explicit cite-backs to source doctrine.

#### 4.5.2 Invocation pattern (canonical, both agents)

1. **Recognize trigger** (per §4.5.1 table). Multiple triggers can fire in a single session — invoke each named skill at the moment the trigger condition is met, not in a batch at session start (see §4.5.6 anti-pattern 1).
2. **Fetch** via `mcp__forge-skills__get_skill(<slug>)`. (Or, under the §4.5 lead-in Codex exception, Read the vendored `.skills/<vendor>/<slug>/` files directly.)
3. **Read** the returned SKILL.md guidance + follow any relative companion-file references it directs (e.g., §G's `resources/*.md`, §H's sibling `methodology.md` / `adversarial.md` / `patterns.md` / `reporting.md`). Worst-case archive load is metered per `AGENT_SKILLS.md` §3B.
4. **Apply** the skill's workflow by tier:
   - **Tier 1** (§F, §AF, §G in current adoption set): advisory only — no tool calls beyond Read/Grep equivalents. No user confirmation gate required (Tier 1 has no shell-execute, no repo-write, no network).
   - **Tier 2** (§H in current adoption set): split into two phases by the inputs available at invocation time.
     - **Phase A (no gate)** applies ONLY when the inputs the skill needs (e.g., for §H: a diff, a file list, a commit range) are ALREADY in session context — e.g., the user pasted the diff inline, or a prior session step ran `git diff` and the output is captured. In that case, the agent can apply the skill's analysis without further shell-execute or file-write.
     - **Phase B (gated by in-session user confirmation)** applies whenever the agent needs to COLLECT inputs via the skill's declared shell binaries (`git`, `gh`, `find`, `grep` for §H) OR produce a tool-write artifact (e.g., `DIFFERENTIAL_REVIEW_REPORT.md` for §H). **In practice, most §H invocations are Phase B from step 1** — §H's Phase 0 triage starts with `git diff <base>..<head>`, so the gate fires at the first command unless the diff is pre-supplied.
     - **Phase A vs Phase B boundary — distinguishing skill-content reads from workload reads:** "inputs already in session context" refers to the **workload inputs** — the data the skill operates on (for §H: the diff content, the file list, the commit range). Reading the SKILL'S OWN CONTENT (via `mcp__forge-skills__get_skill` or via the §4.5 lead-in Codex-exception fallback to Read `.skills/<vendor>/<slug>/` files) is admin-level loading of instructions, NOT Phase B execution — it does not count as a workload read. A new Read-tool open of a workload-input file (e.g., the agent Reads `src/auth.py` to apply §H's analysis because the diff isn't already in session) IS Phase B and triggers the gate. The distinguishing test: "is this file the skill's INSTRUCTIONS, or the DATA the skill is meant to operate on?"
     - Confirmation MUST use a neutral choice prompt, not a yes-leaning question. Example for §H:
       > How would you like §H to proceed on PR #N?
       > (1) Phase A only — read-only summary using diff content already in session context, NO shell commands.
       > (2) Phase B — run `git`/`gh` commands to collect inputs and write `DIFFERENTIAL_REVIEW_REPORT.md`.
       > (3) Cancel — skip §H invocation.
     - **Ambiguous-response handling:** if the user's response does not explicitly select 1/2/3 (e.g., "yes", "sure", "go ahead"), the agent MUST ask a single clarification question (e.g., "To confirm: Phase A only, Phase B, or Cancel?") and MUST NOT execute either phase until the selection is explicit. This prevents ungated execution-path drift from interpretation variance.
     - The agent proceeds only on an explicit affirmative choice. This satisfies §3.2 advisory-only at the Tier-2 boundary.
5. **Honor policy gates** from §4.5.3 (Policy Gates Index). Gates **override** the upstream's prescriptive language where they conflict — example: §H's vendored SKILL.md L137-139 gives a concrete `issue-writer --input ... --format audit-report` command, but the §H Gates Index entry gates that invocation behind per-instance user approval until `issue-writer` is adopted.
6. **Log invocation** in the session transcript per §4.4.5 telemetry-light observation. Specifically: cite which skill fired, on what trigger, and (for Tier 2) which phases the user approved.

**Codex review-profile constraint (re-stated from lead-in for discoverability):** `codex exec --profile review` cannot invoke `mcp__forge-skills__*` calls. The agent in that path Reads the vendored skill files directly from `.skills/<vendor>/<slug>/`, cites the file paths used, and applies the workflow inline. Interactive Claude Code and interactive `codex` TUI sessions invoke normally.

#### 4.5.3 Policy Gates Index

Per-skill gates that supersede the upstream's prescriptive content. The trigger table (§4.5.1) routes the agent to a skill; this index routes the agent to the constraints on how that skill is invoked. Absence of a skill from this index after adoption is a doctrine breach catchable at §4.4.3 step 3 review.

**§F `trailofbits/ask-questions-if-underspecified`** — no policy gates beyond standard Tier-1 advisory rules (§3.2).

**§AF `obra/verification-before-completion`** — no policy gates beyond standard Tier-1 advisory rules (§3.2). Reinforces §3.6.

**§G `trailofbits/audit-context-building`** — policy gates:

1. `function-analyzer` subagent referenced in upstream §8: covered by `AGENT_SKILLS.md` §2E same-model bounded-subagent carve-out (same Claude model family, child tool grants ⊆ parent, no external API/network, fail-closed if not installed in `~/.claude/agents/`). Spawning the subagent is in-set delegation, NOT cross-agent per the carve-out.

**§H `trailofbits/differential-review`** — policy gates:

1. **Tier-2 user-confirmation gate** — Phase A (read-only critique on inputs already in session context) requires no gate; Phase B (shell-execute and/or repo-write) requires in-session user confirmation via the §4.5.2 step 4 neutral 3-option prompt. In practice §H is usually Phase B from step 1; do not pretend a no-shell Phase A precedes the gate when shell access is needed to collect inputs.
2. **`issue-writer` forward-reference gate (Tier-3 default)** — upstream SKILL.md L137-139 + reporting.md L344/L349-354 include prescriptive `issue-writer --input ... --format audit-report` command syntax under an "Integration" heading. The skill is NOT adopted in our loader; per `AGENT_SKILLS.md` §2E "Conditional load of an UN-adopted target" clause, the agent MUST NOT invoke `issue-writer` without per-invocation user approval (Tier 3) until/unless `issue-writer` is itself adopted via §4.4.3. See `research/agents/evaluation_list.md` §H Notes for full rationale.
3. **`shell-execute` binary list is observed-not-enforced** — upstream `allowed-tools: Read Write Grep Glob Bash` gives the agent the full Bash tool grant at runtime; the binary list (`git`, `gh`, `find`, `grep`) recorded in `evaluation_list.md` §H is observed-in-upstream documentation, NOT a runtime allowlist (Phase 1 forge-skills loader provides no per-binary enforcement). Runtime restriction relies on §3.2 + §6 no-destructive-ops doctrine. See `AGENT_SKILLS.md` §2E "observed vs. enforced" note.
4. **`adversarial-modeler` subagent (upstream SKILL.md L81, L100)** — same-model bounded-subagent carve-out per `AGENT_SKILLS.md` §2E (Claude family; child tool grants `Read Grep Glob Bash` ⊆ parent grants `Read Write Grep Glob Bash`; no external API; fail-closed if not installed). Same treatment as §G's `function-analyzer`.

**§D `anthropics/skill-creator`** — policy gates:

1. **Tier-2 user-confirmation gate (overall skill)** — same §4.5.2 step 4 Phase A / Phase B split as §H. Phase A (read-only: drafting a SKILL.md, reviewing existing skill text, explaining the workflow) requires no gate; Phase B (shell-execute / repo-write: running any of the 8 vendored Python scripts, launching the eval-viewer HTTP server, writing eval/feedback/benchmark files, packaging into `.skill` archive) requires in-session user confirmation via the neutral 3-option prompt.
2. **Intra-skill Tier-3 escalation for `claude -p` subprocess scripts (per `AGENT_SKILLS.md` §2E "Bundled-script same-model self-invocation" clause, added Round-6)** — three vendored scripts invoke `subprocess.Popen(["claude", "-p", ...])` or equivalent: `.skills/anthropics/skill-creator/scripts/run_eval.py` (L71-85), `.skills/anthropics/skill-creator/scripts/improve_description.py` (L26-45), `.skills/anthropics/skill-creator/scripts/run_loop.py` (orchestrates the other two). The nested `claude` CLI session loads tool grants from `~/.claude/settings.json` — NOT bounded by parent's scope — so the §2E same-model bounded-subagent carve-out condition 3 (`child grants ⊆ parent`) fails. **Agents applying §D MUST NOT invoke any of these three scripts without per-invocation user approval (Tier 3)**, even though the rest of the skill is Tier 2. The §4.5.2 step 4 gate prompt for these scripts MUST cite this gate explicitly so the user knows the higher Tier applies.

   **Gate sequencing — when Gate 1 (Tier-2 Phase-B confirmation) and Gate 2 (Tier-3 per-script approval) both apply** (added 2026-05-17 per Codex Round-1 Finding R1-3): the agent obtains the Tier-2 Phase-B confirmation FIRST (per §4.5.2 step 4 3-option prompt: `Phase A only / Phase B / Cancel`), then a distinct per-script Tier-3 approval IMMEDIATELY BEFORE each escalated script invocation (e.g., "About to run `scripts/run_loop.py`. This spawns a fresh Claude session with unbounded tool grants per §2E. Approve / Cancel?"). Approval for one Tier-3-escalated script does NOT carry to another in the same session — each invocation is its own gate. Ambiguous replies to either gate require re-prompt per §4.5.2 step 4's ambiguous-response handling rule.

3. **Bundled same-model subagents** — `agents/{grader,comparator,analyzer}.md` in the vendored copy are bundled subagent definitions (NOT in `~/.claude/agents/` registry — they ship inside the skill). Spawned via the host's Task tool with child grants ⊆ parent → satisfies the §2E same-model bounded-subagent carve-out with the bundled-not-registry delta noted in `evaluation_list.md` §D Notes. Same treatment as §G's `function-analyzer` and §H's `adversarial-modeler`. Fail-closed semantics: if the parent's Task tool is unavailable, the workflow degrades to inline grading by the parent (no privilege escalation).
4. **`shell-execute` binary list is observed-not-enforced** — same doctrine as §H. Upstream SKILL.md declares NO `allowed-tools` frontmatter, so the agent receives whatever Bash grants the parent session has. Observed binaries in upstream content: `python` (multiple `python -m scripts.<name>` invocations), `nohup`, `kill`, `cp`, `open` (macOS-only), `lsof` (via `generate_review.py`). Not a runtime allowlist — host doctrine (§3.2 + §6 no-destructive-ops) bounds. See `AGENT_SKILLS.md` §2E "observed vs. enforced" note.
5. **Local HTTP server (loopback only)** — `eval-viewer/generate_review.py` launches a loopback HTTP server (default opens in user's browser). Loopback-only; NOT external network for Tier classification. Documented for transparency.

#### 4.5.4 Pairing doctrine

Two pairing patterns are recognized:

**Chained pairing — §G → §H:** §G builds a baseline mental model of the codebase under review (call graphs, trust boundaries, invariants, validation patterns). §H consumes that context to evaluate a specific diff. Running §H without prior §G context produces shallower reviews — §G is the Pre-Analysis phase §H's `methodology.md` explicitly recommends. The composition is governed by `AGENT_SKILLS.md` §2E "Cross-skill composition carve-out": §G is already adopted in our loader, so calling it from §H's workflow is in-set delegation, not supply-chain expansion (and §H's "if `audit-context-building` skill is available... if NOT available, manually perform..." conditional satisfies the carve-out's graceful-degradation condition). When the user triggers both — e.g., "security-review PR #123" on a file touching auth — the agent runs §G first (Pre-Analysis), then §H (Phases 0-6) consuming §G's output.

**Lifecycle bookend pairing — §F + §AF:** §F triggers when a task's requirements are underspecified at task start; §AF triggers before declaring the task complete. The pair forms an honesty bookend across the AGENTS.md §4.1 lifecycle (plan → implementation → validation). Unlike §G → §H, the pair is **not chained** (§F's output doesn't feed §AF); both apply opportunistically at their respective lifecycle moments. For trivially small tasks where neither trigger fires, neither is invoked — the doctrine is not "invoke both on every task" but "invoke the start-bookend if ambiguity at start, invoke the end-bookend if non-trivial work preceded the completion claim."

#### 4.5.5 Update procedure (atomic with §4.4.3 / §4.4.6)

This trigger table + Gates Index are **co-edited atomically** with `research/agents/evaluation_list.md` in the SAME PR as any adoption (§4.4.3 step 3) or removal (§4.4.6). The §4.4.3 step 3 substep "add §4.5.1 row + §4.5.3 entry" and the §4.4.6 procedure step 3 "remove §4.5.1 row + §4.5.3 entry" make this enforceable — both callsite edits landed atomically with §4.5 in the PR that introduced this section.

The per-adoption Codex review of `evaluation_list.md` (existing per-PR pattern) is the deterministic drift check — the reviewer compares the §4.5.1 table against `evaluation_list.md`'s "active adopted" count + tier mix and flags any mismatch as a HIGH finding.

**Audit-gap acknowledgment (per Codex Round-2 Finding 3):** the "MUST cite the unavailability in session transcript" rule (§4.5 lead-in) and the §4.5.2 step 6 transcript-logging rule are observance-based: the doctrine demands citation but the per-adoption Codex review of `evaluation_list.md` is a STATIC artifact review and does NOT include session transcripts. Verification depends on first-run audit per §4.4.5 (where the adopter watches the skill's first 3 invocations) and ad-hoc post-hoc spot checks. A future telemetry mechanism (suggested: a session-transcript log file under `research/skill_invocations/<timestamp>/`) could close this audit gap; **filed as backlog AB-025** (gitignored). Until then, treat the MUST as agent-discipline best-effort + adopter spot-checks.

#### 4.5.6 Anti-patterns (do NOT do)

- **Auto-loading every adopted skill into context at session start.** Loading all 5 currently-adopted skills' SKILL.md content as a block consumes ~13.0K tokens (884 §F + 987 §AF + 2133 §G + 1668 §H + 7252 §D); auto-loading worst-case read-into-context archives (SKILL.md + all read-by-Claude companion files for multi-file skills) consumes ~36.2K tokens (adds 7549 §G worst-case + 8087 §H worst-case + 18659 §D worst-case read-into-context). §D's full archive INCLUDING executable scripts that don't load into Claude's context window is 50312 tokens. Per `AGENT_SKILLS.md` §3B, individual skills > 5K are flagged and > 10K require justification; the full set crosses both thresholds many times over with zero corresponding work performed. Selective invocation per §4.5.1 triggers is the budget-honest path.
- **Skipping discovery when triggers fire.** The user shouldn't have to type "use skill X" every time. If a trigger condition listed in §4.5.1 fires, the agent MUST proactively call `get_skill` (the lead-in exception covers the only acceptable skip path — Codex review-profile sandbox unavailability with explicit citation + direct vendored-file read).
- **Treating upstream's prescriptive language as the final policy.** Decision Records in `research/agents/evaluation_list.md` carry policy gates that supersede the vendored SKILL.md content (the §4.5.3 Gates Index lifts the load-bearing gates into AGENTS.md for discoverability; the eval_list Notes carry the full rationale). When the SKILL.md and the Decision Record disagree, the Decision Record wins.
- **Listing not-yet-adopted skills in the trigger table.** Only skills with a full §4.4.3 Decision Record + active adoption status belong in §4.5.1. Forward references (skills mentioned by an adopted skill but not themselves adopted) belong in the referring skill's §4.5.3 Gates Index entry as forward-reference gates (e.g., §H's `issue-writer` gate), with the full rationale in `evaluation_list.md` Notes.
- **Executing Tier-2 actions (shell-execute, repo-write) without in-session user confirmation.** Tier-2 invocation is split into read-only critique (Phase A, no gate) and the declared tool-scope phases (Phase B, gated). Even if the skill's upstream content describes Phase B as a default execution path, the §3.2 advisory-only doctrine + the §4.5.2 step 4 gate override. Note: for §H specifically, the Tier-2 gate fires at step 1 of Phase 0 triage. Do not pretend a no-shell Phase A precedes the gate when shell access is needed to collect inputs.
- **Invoking a triggered skill while bypassing its §4.5.3 Policy Gates Index entry.** The trigger table routes the agent to a skill; the Gates Index routes the agent to constraints on HOW that skill is invoked. Running §H's Phase B without honoring the `issue-writer` Tier-3 gate, or treating §H's `Bash` grant as a binary allowlist instead of the full shell surface, are bypass patterns — they invoke the skill correctly but ignore the policy layer that overrides upstream prescription.
- **Executing a §2E bundled-script same-model self-invocation path without per-invocation Tier-3 user approval** (added 2026-05-17 per Codex Round-1 Finding R1-4). Even when the parent skill is Tier 2 (e.g., §D `anthropics/skill-creator` is Tier 2 overall), the `AGENT_SKILLS.md` §2E "Bundled-script same-model self-invocation" clause escalates specific scripts to Tier 3 because the nested same-model session does not provably inherit the parent's tool/permission envelope. The §4.5.3 Gates Index entry for the skill enumerates the script paths (§D's three: `scripts/run_loop.py`, `scripts/run_eval.py`, `scripts/improve_description.py`). Running any of them without a fresh per-invocation user approval — NOT just the Tier-2 Phase-B confirmation — violates §2E + §4.5.3. Phase-B approval does NOT cascade to Gate 2 per §4.5.3 §D gate-sequencing doctrine.
- **Citing AGENT_SKILLS.md as the equivalent-doctrine source under the Codex review-profile exception when the skill's actual content lives in vendored companion files.** `AGENT_SKILLS.md` is the selection framework, not per-skill workflow content. Under the §4.5 lead-in exception, Read the vendored `.skills/<vendor>/<slug>/` files directly via the agent's Read tool and cite the file paths used.
- **Assuming Claude / Codex symmetric MCP invocation.** Codex 0.130.0 under `codex exec --profile review` auto-cancels `mcp__forge-skills__*` calls. The agent in that path cites the constraint per §4.5 lead-in exception and Reads the vendored files directly. Treating both agents as symmetric in this context misstates the runtime.

---

## 5. Critical references

| Topic                                          | File                                                |
| ---------------------------------------------- | --------------------------------------------------- |
| Action evaluation framework                    | `research/github_actions/GITHUB_ACTIONS.md`         |
| Action evaluation list (with Decision Records) | `research/github_actions/evaluation_list.md`        |
| App evaluation framework                       | `research/github_apps/GITHUB_APPS.md`               |
| App evaluation list                            | `research/github_apps/evaluation_list.md`           |
| MCP server framework                           | `research/mcp/MCP_SERVERS.md`                       |
| MCP server evaluation list                     | `research/mcp/evaluation_list.md`                   |
| Agent skills framework                         | `research/agents/AGENT_SKILLS.md`                   |
| Agent skills evaluation list                   | `research/agents/evaluation_list.md`                |
| Codex feedback loop convention                 | `research/feedback_loops/README.md`                 |
| Codex finding schema                           | `research/feedback_loops/codex-finding-schema.json` |
| Release tooling decision                       | `docs/decisions/RELEASE_TOOLING.md`                 |
| Auth architecture                              | `docs/decisions/AUTH_ARCHITECTURE.md`               |
| SDLC strategy                                  | `docs/decisions/SDLC_STRATEGY.md`                   |
| Pre-commit hooks rationale                     | `docs/PRE_COMMIT_EVALUATION.md`                     |
| Changelog                                      | `CHANGELOG.md`                                      |
| Naming conventions                             | `docs/NAMING_CONVENTION.md`                         |
| Domain vocabulary                              | `docs/DOMAIN_VOCABULARY.md`                         |
| Renovate config                                | `.github/renovate.json5`                            |
| Labels source-of-truth                         | `.github/labels.yml`                                |
| AB backlog (gitignored)                        | `roadmap/AUTOMATIONS_BACKLOG.md`                    |

---

## 6. Anti-patterns — don't do these

- **Don't auto-commit, auto-merge, or modify `.github/workflows/**` without a human review gate.\*\* AI tools are advisory; workflow modifications need PR review.
- **Don't use Marketplace SaaS Apps when an OSS CLI variant exists.** Same scanner, no data egress, no permission grant. Checkov is the canonical example (Bridgecrew App skipped, OSS CLI adopted).
- **Don't add Marketplace listings without a Decision Record.** Every third-party tool earns its slot per §1 goals + §7 template.
- **Don't use `--no-verify`, `--no-gpg-sign`, `-c commit.gpgsign=false`, or any flag that bypasses pre-commit/signing hooks.** Investigate hook failures and fix the underlying issue.
- **Don't run destructive git operations on shared state** (`reset --hard`, `push --force`, `branch -D`, etc.) without explicit per-instance user approval.
- **Don't write multi-paragraph docstrings or comment-blocks.** One short line max. Default to no comments.
- **Don't create documentation files (`*.md`, READMEs) unless explicitly requested.** Prefer editing existing files.
- **Don't add features, refactors, or abstractions beyond what the task requires.** A bug fix doesn't need surrounding cleanup; a one-shot operation doesn't need a helper. Three similar lines beats a premature abstraction.
- **Don't infer missing requirements beyond documented scope.** If the external design workspace + this file don't specify it, ask. Especially for architecture, ML posture, or platform-boundary changes (§3.6).
- **Don't copy external doc content into the repo.** Reference and cite. Copies rot; the external workspace is canonical (§3.6).
- **Don't describe in-progress work as shipped, or demos as production-grade.** Match the artifact's actual maturity (§3.6 warn-on-overclaim).

---

## 7. Provenance

- **Created:** 2026-05-14 — driven by Codex CLI adoption + the establishment of the `/codex-review` feedback loop. Doctrine codification was identified as the highest-leverage Codex setup item (alongside `[profile.review]` and `codex-finding-schema.json`).
- **Updated:** 2026-05-15 — folded the platform-doctrine content from the (Codex-invisible) repo `.codex/config.toml` into §1 (intent + scope denials), §3.5 (ML posture), §3.6 (external authoritative docs), and §6 (3 new anti-patterns). Repo `.codex/config.toml` deleted in the same change; user-level `[profile.review]` remains the only Codex CLI config.
- **Updated:** 2026-05-15 (later same day) — added §4.4 codifying the skill adoption / integration process (best practices · requirements · 7-step procedure · adopt/defer/skip criteria · post-adoption validation · removal). Worked example threaded through: `trailofbits/ask-questions-if-underspecified`. Added agent-skills framework + eval-list to §5 references. Follows `research/agents/AGENT_SKILLS.md` and `research/agents/evaluation_list.md` landing earlier the same day.
- **Updated:** 2026-05-15 (final pass) — §4.4 made dual-agent. Skills are now delivered to both Claude Code and Codex CLI via `claude-skills-mcp` registered in both MCP configs (Claude's + `~/.codex/config.toml` `[mcp_servers.claude-skills]`). Vendored canonical path migrated from `.claude/skills/` to `.skills/` (agent-neutral). §4.4 preamble, best-practice #1, and step-4 adoption all updated; dual-agent verification step added. Hierarchy clarified: Claude senior on implementation/analysis, Codex independent reviewer, user decision authority. Driven by user clarification that the agents-evaluation skills should serve both agents identically and that the Codex feedback loop is part of the broader dev workflow (not isolated to skill evaluation).
- **Updated:** 2026-05-16 — §4.4 swapped `claude-skills-mcp` → in-house `forge-skills` loader (AB-022 Phase 1; upstream `claude-skills-mcp` v1.0.0 broken). Phase 1 is file-vendored only — runtime fetch deferred to Phase 3. Added Codex sandbox constraint note: MCP tool calls auto-cancel under `codex exec --profile review` (read-only sandbox + approval=never); skills work in Claude Code and interactive Codex TUI but not in the non-interactive review loop. Verification step changed from `codex exec --profile review` probe to interactive TUI probe. Removal procedure simplified (Phase 1 is file-only, no runtime registration to deregister).
- **Maintenance:** any doctrine change here should also update `research/github_actions/GITHUB_ACTIONS.md`, `research/github_apps/GITHUB_APPS.md`, `research/mcp/MCP_SERVERS.md`, and auto-memory entries as applicable. Sister-doc propagation is non-negotiable per §4.2 quality bar.
