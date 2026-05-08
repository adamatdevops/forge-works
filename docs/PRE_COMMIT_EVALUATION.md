# Pre-commit Hooks Evaluation

Evaluation of which checks belong in pre-commit (run locally, on staged files,
before each commit) versus CI (run on every push/PR against the full tree).

Pre-commit's value is fast feedback — issues caught at commit-time cost seconds
to fix, the same issues caught in CI cost minutes (queue + runner spin-up + full
suite). The trade-off is that pre-commit must stay fast (target: <5s median
commit) or developers will bypass it with `--no-verify`.

## Decision framework

A check is a good fit for pre-commit if **all** of:

1. Runs in <2s on the typical staged-file set
2. Operates on individual files (not the whole project)
3. Has a stable, low false-positive rate
4. Can be auto-fixed or has a quick manual fix

Defer to CI when any of:

- Needs a full project install or build graph (mypy, tsc, full eslint with type-checking)
- Needs services (Postgres, Redis) or secrets to run
- Runs end-to-end / integration / image-build flows
- Is heavy enough that running it on every commit would slow the loop

## Repo composition

| Tree                          | Tooling                       |
| ----------------------------- | ----------------------------- |
| `src/backend/`                | Python (FastAPI)              |
| `src/normalizer/`             | Python (Kafka consumer)       |
| `src/webhook-gateway/`        | Python (FastAPI)              |
| `src/job-dispatcher/`         | Python                        |
| `src/frontend/`               | TypeScript / React            |
| `infra/`                      | YAML (K8s, Terraform-as-code) |
| `.github/workflows/`          | YAML (GitHub Actions)         |
| `infra/iam/scripts/`          | Bash                          |
| `src/normalizer/cue/`         | CUE schemas                   |
| Service Dockerfiles           | Dockerfile                    |
| `docs/`, `infra/CHANGELOG.md` | Markdown                      |

## Hook-by-hook verdict

| #   | Hook                    | Tier | Verdict     | Rationale                                                               |
| --- | ----------------------- | ---- | ----------- | ----------------------------------------------------------------------- |
| 1   | trailing-whitespace     | 1    | use         | <100ms, auto-fix, prevents diff churn                                   |
| 2   | end-of-file-fixer       | 1    | use         | <100ms, auto-fix, POSIX correctness                                     |
| 3   | check-yaml              | 1    | use         | Catches malformed YAML before yamllint, instant                         |
| 4   | check-json              | 1    | use         | IAM policies are JSON; instant syntax gate                              |
| 5   | check-toml              | 1    | use         | pyproject.toml correctness, instant                                     |
| 6   | check-merge-conflict    | 1    | use         | Catches accidental `<<<<<<<` markers                                    |
| 7   | check-added-large-files | 1    | use         | Block accidental large blobs (>500KB)                                   |
| 8   | check-case-conflict     | 1    | use         | macOS/Linux case-sensitivity drift                                      |
| 9   | check-symlinks          | 1    | use         | Broken symlinks, fast                                                   |
| 10  | mixed-line-ending       | 1    | use         | Force LF, catches Windows line endings                                  |
| 11  | ruff (lint)             | 1    | use         | Mirrors CI exactly. Auto-fixes most issues. ~200ms staged               |
| 12  | ruff-format             | 1    | use         | Mirrors `ruff format --check` in CI; auto-applies                       |
| 13  | prettier (frontend)     | 1    | use         | Auto-format TS/TSX/CSS/MD/YAML/JSON; fast on staged files               |
| 14  | yamllint                | 2    | use         | Already configured in `.yamllint`; matches CI                           |
| 15  | markdownlint-cli2       | 2    | use         | Already configured in `.markdownlint.jsonc`; matches CI                 |
| 16  | shellcheck              | 2    | use         | `infra/iam/scripts/diff-iam.sh` and others; fast                        |
| 17  | hadolint                | 2    | use         | Dockerfile-only; runs only on changed Dockerfiles; matches CI           |
| 18  | detect-secrets          | 2    | use         | Token leak prevention; baseline file checked into repo                  |
| 19  | mypy                    | —    | defer to CI | Slow (needs full install); strict mode is CI-only by design             |
| 20  | eslint (full)           | —    | defer to CI | Type-aware lint needs `tsc` references; PR-level fine                   |
| 21  | tsc / typecheck         | —    | defer to CI | 30-90s on cold cache; not commit-time friendly                          |
| 22  | pytest                  | —    | defer to CI | Tests don't belong in pre-commit; brittle, slow                         |
| 23  | gitleaks                | —    | defer to CI | Already in CI; detect-secrets is the lighter local equivalent           |
| 24  | snyk                    | —    | defer to CI | Network call + token; CI-only                                           |
| 25  | cue vet                 | —    | optional    | Could add later for `src/normalizer/cue/`; defer until first regression |
| 26  | terraform fmt           | —    | optional    | No `.tf` files yet; revisit after Terraform module work lands           |
| 27  | pretty-format-java      | 1    | use         | Wraps google-java-format JAR (AOSP style); auto-formats staged `.java`  |

## Java tooling (Flink jobs in `src/flink-jobs/{event-router,insight-generator,pattern-matcher}/`)

Java's quality tooling splits cleanly into source-level (commit-time) and
bytecode-level (build-time). Pre-commit can only handle the former; the rest
runs as Maven plugins via `mvn verify`.

| Tool               | Layer        | Phase              | Verdict                                           | Rationale                                                                                                                                                                                      |
| ------------------ | ------------ | ------------------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| google-java-format | source       | pre-commit + Maven | use (via `pretty-format-java` + Spotless)         | De-facto Google formatter, no config debate                                                                                                                                                    |
| Spotless           | source       | `mvn verify`       | use (each pom.xml)                                | Wraps google-java-format + import order + EOL; build-time gate                                                                                                                                 |
| SpotBugs           | bytecode     | `mvn verify`       | use (each pom.xml, `failOnError=false` initially) | Catches real bugs (resource leaks, threading, NPE) post-compile                                                                                                                                |
| ErrorProne         | compile-time | `mvn compile`      | **defer** to E5.2                                 | Java 11 needs `--add-exports` JVM args; first integration surfaces fixes that need per-check triage. Spotless+SpotBugs cover 80% of value with less risk. Re-evaluate after the cleanup sprint |
| Checkstyle         | source       | -                  | skip                                              | Subsumed by Spotless+google-java-format                                                                                                                                                        |
| PMD                | source       | -                  | skip                                              | High false-positive rate; tuning cost > value                                                                                                                                                  |
| SonarQube/Cloud    | both         | -                  | skip                                              | Requires server; CI integration friction                                                                                                                                                       |

### Spotless config (in each pom.xml)

```xml
<plugin>
    <groupId>com.diffplug.spotless</groupId>
    <artifactId>spotless-maven-plugin</artifactId>
    <version>2.46.1</version>
    <configuration>
        <java>
            <googleJavaFormat>
                <version>1.22.0</version>
                <style>AOSP</style>
            </googleJavaFormat>
            <removeUnusedImports/>
            <importOrder/>
            <trimTrailingWhitespace/>
            <endWithNewline/>
        </java>
    </configuration>
    <executions>
        <execution>
            <phase>verify</phase>
            <goals><goal>check</goal></goals>
        </execution>
    </executions>
</plugin>
```

`mvn spotless:apply` to auto-fix; `mvn spotless:check` (or `mvn verify`) to gate.
The pre-commit `pretty-format-java` hook uses the same google-java-format AOSP style — they stay in sync.

### SpotBugs posture during rollout

Set `failOnError=false` initially so SpotBugs runs on every build but doesn't
break it. Findings are written to `target/spotbugsXml.xml` for review. After
the first triage pass (E5.2), flip to `failOnError=true`.

### ErrorProne deferral rationale

ErrorProne adds high-signal compile-time checks (e.g., `EqualsIncompatibleType`,
`FutureReturnValueIgnored`, `MissingOverride`, `BoxedPrimitiveEquality`) that
would catch real bugs the JVM accepts. Reasons it's deferred from this rollout:

1. **JVM module export friction.** Java 9+ requires `--add-exports` for the
   internal `jdk.compiler` packages ErrorProne hooks into. The flag list has
   to be passed via `<compilerArgs>` and is fragile across `maven-compiler-plugin`
   versions and JDK distributions
2. **First-run noise.** With no prior gating, expect 10-30 findings across the
   3 jobs. Each must be triaged: real bug, intentional, or `@SuppressWarnings`
3. **Work scoping.** This commit's purpose is unblock CI lint + bootstrap
   pre-commit; ErrorProne wants its own focused PR with the triage attached

It belongs in Sprint E5.2 (CI hardening), where the lint debt + ErrorProne
adoption + SpotBugs `failOnError=true` flip can be triaged together.

## Python — additional considerations

Root `ruff.toml` already enables 30+ rule families. The remaining gaps:

| Tool / rule              | Layer     | Verdict                    | Rationale                                                                                                               |
| ------------------------ | --------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| ruff `S` (flake8-bandit) | source    | **add**                    | Security patterns: `eval`, `shell=True`, weak crypto, hardcoded passwords. Ported into ruff (Rust); zero new dependency |
| pip-audit                | deps      | optional                   | CVE scan on installed deps; CI-only; overlaps with Snyk if token configured                                             |
| bandit (standalone)      | source    | skip — covered by ruff `S` | Use only if a specific check is missing from ruff `S`                                                                   |
| mypy / pyright           | typing    | CI-only                    | Slow; needs full per-package install; doesn't fit pre-commit budget                                                     |
| vulture                  | dead-code | skip                       | High false-positive rate                                                                                                |
| interrogate              | docs      | skip                       | Docstring style is bikeshed; not a release-blocker                                                                      |

### Ruff `S` rollout note — backend has divergent config

`src/backend/pyproject.toml` has its own `[tool.ruff]` section that overrides
the root `ruff.toml` for backend files. Adding `"S"` to root only affects
`src/normalizer/`, `src/webhook-gateway/`, `src/job-dispatcher/` (which inherit
from root) — backend is unaffected. All three inheriting packages pass cleanly.

**Follow-up (E5.2):** consolidate ruff config into root `ruff.toml` only;
remove `[tool.ruff]` block from `src/backend/pyproject.toml` so backend
inherits the same rule set as the rest of the tree. Will surface ~1090 S
findings in backend (mostly S101 in tests — already covered by root's
per-file-ignore — and S105/S106/S311 to triage).

## Hooks selected for v1 rollout

Tier 1 (built-ins + ruff + prettier + java format): 14 hooks
Tier 2 (linters): 5 hooks
Total: **19 hooks**

Expected median commit overhead: 1–3 seconds for a typical 1–5 file change.

## TODO checklist — rollout

- [x] Patch root `ruff.toml` to ignore UP042 (unblock CI Lint job)
- [x] Run `ruff format src/backend/` to fix 3 stale-format files
- [x] Write `docs/PRE_COMMIT_EVALUATION.md` (this file)
- [x] Write `.pre-commit-config.yaml` with selected hooks
- [ ] Install hooks: `pre-commit install`
- [ ] Generate detect-secrets baseline: `pre-commit run detect-secrets --all-files` (creates `.secrets.baseline`)
- [ ] Dry-run on full tree: `pre-commit run --all-files` — fix or whitelist any new findings
- [ ] First commit through hooks (CI fix + this doc + config) — confirms hooks fire
- [ ] Document `--no-verify` policy in `CONTRIBUTING.md` (acceptable for: WIP local commits, never for shared branches)
- [ ] Optional follow-ups: cue vet hook, terraform fmt hook, mypy in CI-only `manual` stage
- [ ] Update `README.md` developer setup section: `pip install pre-commit && pre-commit install`
- [x] Add ruff `S` (flake8-bandit) security rules to root `ruff.toml`
- [x] Add `pretty-format-java` pre-commit hook (google-java-format AOSP)
- [x] Format-sweep all 24 Java files via google-java-format (one-time normalization)
- [x] Add Spotless + SpotBugs Maven plugins to all 3 Flink poms
- [x] Add `java-build` matrix job to `.github/workflows/ci.yml`
- [ ] **E5.2:** Wire ErrorProne with Java 11 `--add-exports` flags + per-check triage
- [ ] **E5.2:** Consolidate backend ruff config into root `ruff.toml` (delete `[tool.ruff]` from `src/backend/pyproject.toml`); triage backend `S` findings
- [ ] **E5.2:** Flip SpotBugs `failOnError=true` after first triage

## Maintenance

- Pin hook versions in `.pre-commit-config.yaml` and bump quarterly via
  `pre-commit autoupdate` to avoid silent rule changes
- Keep CI as the source of truth: any rule disabled in pre-commit must also be
  disabled in CI, and vice versa. Drift between the two is worse than missing
  one of them
- New language or tool in the repo? Update this file's "Repo composition" table
  and re-run the decision framework before adding a hook
