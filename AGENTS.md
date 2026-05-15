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

**Worked example threaded through this section:** `trailofbits/ask-questions-if-underspecified` — highest-scoring adopt in `evaluation_list.md`; Tier 1; first-party; runtime-fetched via `claude-skills-mcp`. Vendored Tier 2/3 examples diverge only at §4.4.3 step 4.

#### 4.4.1 Best practices / standards

1. **Vendored is the default.** SHA-pinned local copy under `.claude/skills/<vendor>/<slug>/SKILL.md`. Runtime-fetched is acceptable only for first-party Tier-1 skills loaded via a trusted loader (today: `claude-skills-mcp`).
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

   _Example:_ `git clone github.com/trailofbits/skills /tmp/audit-trailofbits` → SHA `<40-char>`; `ask-questions-if-underspecified/SKILL.md` is plain prose, ~900 tokens, no shell, no transitive refs, no cross-agent. Proceed.

2. **Tier confirmation.** Observed tool scope (read-only / shell-execute / repo-write / network / cross-agent / external-write) → `AGENT_SKILLS.md` §4 Tier. If the observed Tier differs from the eval-list Tier, update the Decision Record and re-justify before proceeding.

   _Example:_ Tier 1 (read-only). Matches the eval-list assignment.

3. **Decision Record completion.** Replace every placeholder in the `AGENT_SKILLS.md` §7 14-field template with measured values: real `Source SHA`, real `Context cost` (count tokens with `tiktoken` or the loader's counter — don't ship the eval-list rough estimate), real `Tool scope`, real `Removal procedure`. No `<verify at adoption review>` markers may survive into the recorded artifact.

   _Example:_ `Source SHA: <sha>` · `Context cost: ~900 tokens (measured via tiktoken cl100k_base)` · `Adoption mode: runtime-fetched via claude-skills-mcp` · `Removal: deregister slug from claude-skills-mcp allow-list`.

4. **Adoption.** Branch by mode:
   - **Tier 1, first-party, runtime-fetched:** add the skill's slug to the `claude-skills-mcp` allow-list (per its docs). No file copy.
   - **Anything else (vendored):** create `.claude/skills/<vendor>/<slug>/`, copy the audited SKILL.md + any companion files verbatim, prepend a header comment `<!-- Source: <canonical URL> · SHA: <40-char> · Audited: <YYYY-MM-DD> -->`. Register the directory path in the agent's skill loader.

   _Example:_ Add `trailofbits/ask-questions-if-underspecified` to `claude-skills-mcp` config; no file copy.

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

1. **Runtime-fetched:** deregister the slug from `claude-skills-mcp` config.
2. **Vendored:** `git rm -r .claude/skills/<vendor>/<slug>/`.
3. Update `CHANGELOG.md` under `### Removed` with reason + SHA refs.
4. If credentials were associated with the skill, rotate them; record rotation in the same commit.

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
- **Maintenance:** any doctrine change here should also update `research/github_actions/GITHUB_ACTIONS.md`, `research/github_apps/GITHUB_APPS.md`, `research/mcp/MCP_SERVERS.md`, and auto-memory entries as applicable. Sister-doc propagation is non-negotiable per §4.2 quality bar.
