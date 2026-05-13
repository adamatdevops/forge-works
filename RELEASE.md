# Release Process

forge-works uses **Conventional Commits + a hand-curated `CHANGELOG.md` +
manual `git tag`** as its current release process.

This is an **interim** process. The target state is automated tag + changelog
generation via [release-please](https://github.com/googleapis/release-please-action),
landing as part of task #23 (SDLC strategy + automations).

For the rationale behind moving away from Changesets, see
[`docs/decisions/RELEASE_TOOLING.md`](docs/decisions/RELEASE_TOOLING.md).

## How it works today

### Authoring changes

1. **Commit messages follow [Conventional Commits](https://conventionalcommits.org).**
   Subject lines are **one sentence** — no multi-line bodies.

   Examples:
   - `feat(normalizer): add Terraform source normalizer`
   - `fix(ci): include security job in CI Success aggregate`
   - `docs(release): rewrite for post-Changesets process`
   - `chore(deps): bump next to 16.2.3`
   - `ci(security): harden Snyk into a real PR gate`

2. **Narrative goes to `CHANGELOG.md`.** When you cut a release, add a section
   with the version, date, and grouped entries that reference the commit SHAs:

   ```markdown
   ## [0.8.0] - 2026-05-10

   ### Added

   - Terraform source normalizer with FW_EXPECTED_SOURCE isolation guard
     (`abc1234`)

   ### Fixed

   - Normalizer ModuleNotFoundError on dev cluster — switched pyproject.toml
     to setuptools `find` directive (`def5678`)
   ```

3. **Tag the release.** From `main`:

   ```bash
   git tag v0.9.0
   git push origin v0.9.0
   ```

### Versioning policy

- **Single global semver today** (`v0.8.0` covers everything).
- **Per-service semver in Phase 4** (ArgoCD per-namespace) — services will
  release independently. release-please will manage per-service version bumps
  in `pyproject.toml`, `pom.xml`, `package.json`, and Helm `Chart.yaml`.
- Bumping rules until then:
  - **MAJOR (`X.0.0`)** — breaking API/contract change for any user-facing
    surface (HTTP API, CUE schema, Kafka topic shape).
  - **MINOR (`0.X.0`)** — new feature, backwards-compatible.
  - **PATCH (`0.0.X`)** — bug fix, no behavior change.

### Branch strategy

GitHub Flow: short-lived feature branches → PR → squash-merge to `main`.
Releases are tagged from `main`. No `develop` or `release/*` branches.

To be codified in `docs/project/BRANCHING.md` (task #23).

## Future: release-please

When wired (task #23), release-please will:

1. Watch `main` for Conventional Commits.
2. Open a single "Release Please" PR with proposed version bumps and a
   pre-rendered `CHANGELOG.md` diff.
3. On merge of that PR, push tags and create GitHub Releases.

Multi-package config will cover:

- `src/frontend/` → `node`
- `src/backend/`, `src/normalizer/` → `python`
- `src/flink-jobs/*` → `maven`
- `infra/charts/*` → `helm`
- root → aggregate

## Reverting a release

Before the tag is pushed:

```bash
git tag -d v0.9.0
```

After the tag is pushed (rare; ask before doing this — published tags are
generally immovable):

```bash
git push origin :refs/tags/v0.9.0
```

Prefer fixing forward with a new patch release.

## See also

- [`docs/decisions/RELEASE_TOOLING.md`](docs/decisions/RELEASE_TOOLING.md) —
  full rationale for the Changesets → release-please decision.
- [`CHANGELOG.md`](CHANGELOG.md) — the canonical changelog.
- [Conventional Commits spec](https://conventionalcommits.org).
