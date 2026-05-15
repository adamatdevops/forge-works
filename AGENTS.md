# AGENTS.md — forge-works doctrine for AI agents

> **Audience.** Any AI agent operating inside this repository (Codex, Claude Code, future agents). Codex reads this file automatically per session. Treat the rules below as binding unless explicitly overridden by the user in the current session.
>
> **Companion file:** `CLAUDE.md` (not present at root yet — Claude Code currently loads guidance from `.claude/` and auto-memory). The two files agree on doctrine; this one is the source of truth.

---

## 1. What this repo is

**forge-works** is an Internal Developer Platform (IDP) that orchestrates service creation through ML-guided golden-path templates and provides visibility into a service ecosystem. It is NOT a deployment tool, NOT a Kubernetes replacement, NOT a full PaaS.

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

---

## 7. Provenance

- **Created:** 2026-05-14 — driven by Codex CLI adoption + the establishment of the `/codex-review` feedback loop. Doctrine codification was identified as the highest-leverage Codex setup item (alongside `[profile.review]` and `codex-finding-schema.json`).
- **Maintenance:** any doctrine change here should also update `research/github_actions/GITHUB_ACTIONS.md`, `research/github_apps/GITHUB_APPS.md`, `research/mcp/MCP_SERVERS.md`, and auto-memory entries as applicable. Sister-doc propagation is non-negotiable per §4.2 quality bar.
