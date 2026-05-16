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
