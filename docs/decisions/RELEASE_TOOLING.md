# ADR: Release Tooling — Conventional Commits + release-please over Changesets

- **Status:** Accepted
- **Date:** 2026-05-10
- **Decision drivers:** flow methodology, branch strategy, semver, deployment cadence,
  industry standards, stack composition, overall vision
- **Supersedes:** the Changesets-based release flow scaffolded into the repo at init

## Context

forge-works was scaffolded with [Changesets](https://github.com/changesets/changesets)
release tooling (`.changeset/`, `pnpm changeset:*` scripts, `release.yml`,
`changeset-check.yml`, `needs-changeset`/`skip-changeset` labels). In parallel we
adopted a different convention: one-sentence Conventional Commits subjects with
narrative captured in `CHANGELOG.md` and SHA references.

The two systems duplicate the same job (release-note authoring) using
incompatible mechanisms:

- **Changesets:** the developer runs `pnpm changeset` per PR and commits a
  `.changeset/*.md` file describing the change. At release time, `changesets`
  consumes those markdown files and produces a "Version Packages" PR.
- **Conventional Commits + release-please:** commit messages are the source of
  truth. At release time, [release-please](https://github.com/googleapis/release-please)
  parses commit history and produces a release PR with version bumps + changelog.

The conflict surfaced when Renovate's first PR (`renovate/npm-next-vulnerability`)
failed `Changeset Check` five times: Renovate doesn't author changeset files,
and our convention now treats commit messages as the source of release notes
anyway.

This ADR captures the decision and the reasoning, evaluated against eight
factors the team uses to size release-tooling decisions.

## Factors

### 1. Flow methodology — GitHub Flow

We operate trunk-based with short-lived feature branches and tag-driven
promotion (`v0.8.0` is the latest example). No `develop`/`release/*` branches.

Both tools support GitHub Flow. **Neutral.**

### 2. Branch strategy — trunk-based, not yet codified

Discussed but not yet written down (see task #23). De facto: `main` is the
working trunk; Renovate creates short-lived `renovate/*` branches; humans cut
release tags from main. No release branches.

Both tools support trunk-based. **Neutral.**

### 3. Semantic versioning — single global today, per-service tomorrow

Today the repo carries one global version (`v0.8.0`) covering everything.
Phase 4 (ArgoCD per-namespace) will let services release on independent
cadences — `forge-works-normalizer@1.3.0`, `forge-works-frontend@2.0.0`,
`forge-engine-event-router@0.5.1` — each with its own semver clock.

Per-service semver in a polyglot stack requires a tool that can bump versions
in `pyproject.toml`, `pom.xml`, `package.json`, and Helm `Chart.yaml`.

- **Changesets:** only `package.json`.
- **release-please:** `python`, `java`, `node`, `helm`, `terraform`, `dart`, …

**Verdict: release-please.**

### 4. Deployment rate vs release rate vs commit rate

- Commit rate: high (many small commits per day)
- Release rate: low (`v0.4.0 → v0.8.0` over weeks)
- Deploy rate: manual today, continuous in Phase 4 (ArgoCD)

When commit-rate ≫ release-rate, the right release tool **batches without
per-PR human work**. Changesets requires `pnpm changeset` per PR; release-please
consumes commit messages we already write.

**Verdict: release-please.**

### 5. Industry standards

- **Changesets:** dominant in JS-only monorepos that publish libraries to npm —
  Turborepo, Astro, Remix, pnpm itself, Cloudflare Wrangler. The common thread
  is _libraries_, not platforms.
- **Conventional Commits + release-please / semantic-release:** dominant in
  polyglot projects and app monorepos. Google's release-please is used heavily
  across the kubernetes ecosystem. Conventional Commits is a standard
  ([conventionalcommits.org](https://conventionalcommits.org)) widely adopted
  outside the JS world.

Our shape (polyglot platform deployable as services) aligns with the
release-please userbase.

**Verdict: release-please.**

### 6. Best practices

- Single source of truth for release notes
- Automation that doesn't depend on memory (commit messages are universal;
  remembering `pnpm changeset` per PR is extra cognitive load)
- Avoid running two systems that do the same job

**Verdict: pick one and remove the other.**

### 7. Our stack

| Component                         | Format           | Changesets supports? | release-please supports? |
| --------------------------------- | ---------------- | -------------------- | ------------------------ |
| `src/frontend/`                   | `package.json`   | yes                  | yes                      |
| `src/backend/`, `src/normalizer/` | `pyproject.toml` | no                   | yes                      |
| `src/flink-jobs/*/pom.xml`        | Maven            | no                   | yes                      |
| `infra/charts/*/Chart.yaml`       | Helm             | no                   | yes                      |
| Global repo tag                   | `git tag`        | no                   | yes                      |

**Coverage: Changesets ~15%, release-please ~100%.**

**Verdict: release-please.**

### 8. Overall vision

forge-works is an IDP / data-intelligence platform with multiple deployable
services. Services release independently. The frontend is an app shell, not a
library installed via `npm install`. We will publish container images to GHCR
and Helm charts to a chart registry — never npm.

Changesets' core value-prop (npm publishing automation) is irrelevant to our
deployment model.

**Verdict: release-please.**

## Decision

**Adopt Conventional Commits + release-please. Remove all Changesets infrastructure.**

This is a two-step move:

1. **Now (this commit):** delete the Changesets workflows, config, scripts,
   labels, and docs. The repo continues to use the convention already adopted
   in `feedback_commit_changelog_style` memory: one-sentence Conventional
   Commits subjects, narrative committed to `CHANGELOG.md` with SHA
   references, manual `git tag` until release-please lands.
2. **Task #23 (next sprint):** wire release-please via
   `googleapis/release-please-action`. Multi-package config:
   - `src/frontend` → `node`
   - `src/backend`, `src/normalizer` → `python`
   - `src/flink-jobs/*` → `maven`
   - `infra/charts/*` → `helm`
   - root → aggregate / `simple`
     Output: per-service tag + per-service `CHANGELOG.md` entry + a global
     aggregate tag.

## Consequences

### Positive

- Single convention across the polyglot stack.
- No per-PR friction (`pnpm changeset` step removed).
- Renovate PRs stop tripping `Changeset Check`.
- Path opens to per-service release cadence in Phase 4.
- Reduced npm dependency surface (`@changesets/cli`, `@changesets/changelog-github` removed).

### Negative / accepted

- **No automated frontend npm publishing.** We don't currently publish to npm;
  if that becomes a requirement, release-please supports npm publishing too.
- **Manual tagging until task #23 lands.** Acceptable given the low release
  cadence (weeks between tags).
- **Existing `RELEASE.md` rewrite.** Rewritten to describe the interim manual
  process; will be rewritten again when release-please is wired.

### Migration

- Removed: `.changeset/`, `.github/workflows/release.yml`,
  `.github/workflows/changeset-check.yml`, `package.json` `changeset:*` scripts,
  `@changesets/*` devDependencies, `needs-changeset` + `skip-changeset` labels.
- Updated: `RELEASE.md` (interim manual process), `README.md` (versioning row),
  `.github/labels.yml` (removed two labels, rewrote "Semver Labels" comment).

## Alternatives considered

### Keep Changesets, auto-label Renovate PRs with `skip-changeset`

Rejected. Treats the symptom (Renovate failure) without addressing the root
cause (two release systems disagreeing). The 15%-coverage problem remains, and
the per-PR friction stays for human-authored PRs.

### Keep Changesets but make it advisory (warn-only)

Rejected. A perpetually-failing-but-non-blocking check becomes noise. Better
to remove it than to teach contributors to ignore it.

### Adopt `semantic-release` instead of release-please

Rejected for now. `semantic-release` is opinionated about npm publishing and
runs as a CI step that publishes immediately on merge. release-please's
PR-then-merge model is a better fit for our review-before-tag preference and
its polyglot manifest support is broader.

## References

- Conventional Commits: <https://conventionalcommits.org>
- release-please: <https://github.com/googleapis/release-please>
- release-please-action: <https://github.com/googleapis/release-please-action>
- Changesets: <https://github.com/changesets/changesets>
- forge-works task #23: SDLC strategy + automations backlog (where release-please lands)
- Memory: `feedback_commit_changelog_style` — one-sentence Conventional Commits convention
