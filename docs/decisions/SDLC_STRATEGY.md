# SDLC Strategy — Branching, Environments, Promotion

- **Status:** Accepted (target architecture; phased migration)
- **Date:** 2026-05-13
- **Decision drivers:** trunk-based flow, polyglot stack, solo → small-team scale,
  K8s deployment, image promotion, release automation
- **Supersedes:** ad-hoc tag-from-main flow described in `RELEASE.md` (interim)
- **Related:** `docs/decisions/RELEASE_TOOLING.md`, `roadmap/AUTOMATIONS_BACKLOG.md`

## Purpose

This document defines the software-delivery lifecycle for forge-works:
how code moves from a developer's branch through review, CI, build,
promotion, and deployment into production. It captures the **target
architecture** and the **phased migration** from the current single-cluster
manual-tag state.

It does NOT cover:

- Project methodology (sprint cadence, ticket states) → `docs/project/WORKFLOW.md`
- Release tooling choice → `docs/decisions/RELEASE_TOOLING.md` (already accepted)
- Per-component architecture → `docs/architecture.md`, `docs/components/*`

## Current state (2026-05-13)

- **Branching:** GitHub Flow on `main`; `renovate/*` and ad-hoc topic branches
- **Versioning:** Single global semver (`v0.8.0`); per-service deferred to Phase 4
- **Release:** Manual `git tag vX.Y.Z` on main; release-please target (task #23)
- **Environments:** One EKS cluster (`forge-works-dev`, `us-east-1`); staging + prod
  are aspirational (placeholder overlays exist in `infra/flink/overlays/prod/`)
- **Image lifecycle:** Normalizer builds + pushes to GHCR on main; backend image
  is built in `ci.yml` but **not pushed**; Helm charts are versioned in-repo but
  not published to any chart registry
- **Quality gates:** 18-hook pre-commit suite + 11-job CI + `CI Success` aggregate
  required on `main` (`strict: true`)
- **Auto-merge:** Enabled at repo level (2026-05-13); `delete_branch_on_merge: true`

---

## Target architecture

### 1. Branching model — trunk-based on `main`

**`main` is the only long-lived branch.** All work happens on short-lived
topic branches that merge back via squash + delete.

**Branch naming:** `<type>/<short-slug>` where `<type>` mirrors Conventional
Commits subjects:

| Prefix      | When                                                |
| ----------- | --------------------------------------------------- |
| `feat/`     | New feature                                         |
| `fix/`      | Bug fix                                             |
| `chore/`    | Dependency bumps, refactors with no behavior change |
| `docs/`     | Documentation only                                  |
| `refactor/` | Code restructure, no behavior change                |
| `test/`     | Test-only changes                                   |
| `renovate/` | Reserved for Renovate (do not create manually)      |

**Lifecycle:** `branch → push → PR → CI green → squash-merge → branch auto-deleted`.
No merge commits to `main`. No rebase-merge (loses Conventional Commits
subject coherence with PR title). No release branches.

**PR labels** drive bot visibility and lifecycle (handled by
`pr-status-labeler.yml`): exactly one of `pr status:{opened,review,merged,closed}`,
plus orthogonal `status:blocked` if applicable.

### 2. Environments — three EKS clusters

| Env         | Cluster                      | AWS account     | Purpose                                       |
| ----------- | ---------------------------- | --------------- | --------------------------------------------- |
| **dev**     | `forge-works-dev` (existing) | dev             | Per-PR + per-merge dev validation             |
| **staging** | `forge-works-staging` (new)  | dev or pre-prod | Release candidates; SRE rehearsal, soak tests |
| **prod**    | `forge-works-prod` (new)     | prod            | End-user traffic                              |

**Rationale:** strongest isolation; clean RBAC boundary; image promotion
maps to cluster move (not just namespace tag); independent IAM scoping.

**Cost envelope** (control planes only): ~$216/mo (3 × $72). Node-group
auto-scaling per cluster — dev/staging scale to 0 when idle (continues the
pattern documented in `docs/EKS_OPERATIONS.md`).

**Namespace pattern within each cluster:** one namespace per logical
service group (`forge-works`, `forge-engine`, etc.), not per env.

### 3. Image lifecycle

```
PR push → ci.yml builds image (no push)        [validation only]
main merge → image build + push @ <sha> + @ latest-dev      → dev cluster auto-pulls
git tag vX.Y.Z (release-please) → re-tag image as vX.Y.Z      → staging cluster pulls
manual promote / ArgoCD sync (post-soak) → prod cluster pulls
```

**Tag taxonomy:**

- `@sha-<7char>` — immutable per-commit (current normalizer pattern)
- `@latest-dev` — moving pointer for dev cluster (auto-deploys)
- `@vX.Y.Z` — release-please-cut tags; staging + prod consume only these
- No `@latest` on prod — explicit version every time

**Registry:** GHCR (`ghcr.io/adamatdevops/forge-works/<service>`). Same
registry hosts Helm OCI charts (`ghcr.io/adamatdevops/forge-works/charts/<chart>`).

### 4. Release automation — release-please across 4 ecosystems

Per `RELEASE_TOOLING.md`, release-please consumes Conventional Commits on
`main` and authors a `release-please-bot/release-X.Y.Z` PR that bumps
versions in:

| Ecosystem | Files                                                              |
| --------- | ------------------------------------------------------------------ |
| python    | `src/backend/pyproject.toml`, `src/normalizer/pyproject.toml`, ... |
| node      | `package.json`, `src/frontend/package.json`                        |
| maven     | `src/flink-jobs/*/pom.xml`                                         |
| helm      | `infra/charts/*/Chart.yaml`                                        |

**Phase 4 cutover:** monorepo manifest with per-package versioning. Until
then, single global version bumps all in lockstep.

Merging the release-please PR fires the `release.yml` workflow which:

1. Creates the GitHub release with auto-generated changelog
2. Pushes the immutable `vX.Y.Z` image tags
3. (Phase 4) Triggers ArgoCD sync to staging

### 5. Quality gates — defense-in-depth

```
1. Local: pre-commit (18 hooks)         ← fast formatters, secrets, schemas
2. PR open: ci.yml (11 jobs)            ← lint, test, security, build, IaC scan
3. PR review: CodeRabbit (advisory)     ← semantic/architectural feedback
4. Branch protection: CI Success        ← aggregate; required for merge
5. Post-merge: image push + cluster sync ← integration verification
6. Phase 4: ArgoCD sync to staging      ← release-train validation
```

**Promote to Required (branch protection):** after baselines stabilize (~2 weeks),
add to `required_status_checks`: `codecov/patch`, `codecov/project`,
`checkov` (after `soft_fail: false`), `Snyk` (after migration completes).

### 6. Promotion model

| Stage   | Trigger                             | Target          | Approval            |
| ------- | ----------------------------------- | --------------- | ------------------- |
| Build   | Push to `main`                      | image @ sha     | None (CI gates)     |
| Dev     | image @ sha pushed                  | dev cluster     | None (auto-pull)    |
| Release | release-please PR merged            | image @ vX.Y.Z  | Human merges PR     |
| Staging | vX.Y.Z tag created                  | staging cluster | None (auto-promote) |
| Prod    | post-soak (e.g. 24h staging stable) | prod cluster    | Human ArgoCD sync   |

**Rollback:** ArgoCD sync to prior `vX.Y.Z` tag. No hotfix branches —
revert commit on `main` → release-please cuts vX.Y.Z+1 → forward-fix.

---

## Migration phases

### Phase A — Codify + foundations (now, this sprint)

- [ ] **A1.** Adopt this strategy doc; reference from `RELEASE.md`
- [ ] **A2.** Wire release-please MVP (single global semver, all 4 ecosystems)
- [ ] **A3.** Add `backend-image.yml` workflow (mirror `normalizer-image.yml`)
- [ ] **A4.** Add `frontend-image.yml` workflow (Next.js build → GHCR)
- [ ] **A5.** Helm chart publish to GHCR OCI (`helm push` in CI)
- [ ] **A6.** Codify branch-name conventions in CONTRIBUTING (or NAMING_CONVENTION)

**Exit criteria:** release-please cuts `v0.9.0` end-to-end without manual
intervention; all 3 service images pushed to GHCR on main.

### Phase B — Staging cluster + image promotion (Phase 5 of engine roadmap)

- [ ] **B1.** Provision `forge-works-staging` EKS cluster (Terraform module
      reused from dev)
- [ ] **B2.** ArgoCD install on staging (Phase 4 of engine roadmap kicks here)
- [ ] **B3.** Auto-promote `vX.Y.Z` images: staging cluster syncs on tag push
- [ ] **B4.** Soak harness — synthetic events + canary metrics; gate prod promotion
- [ ] **B5.** Codecov + Checkov + Snyk Check Runs promoted to Required

**Exit criteria:** A `vX.Y.Z` release lands in staging within 5 minutes of
the release PR merge; staging cluster passes soak harness for ≥24h before
prod promotion is allowed.

### Phase C — Prod cluster + per-service semver (Phase 6 of engine roadmap)

- [ ] **C1.** Provision `forge-works-prod` EKS cluster (separate AWS account)
- [ ] **C2.** ArgoCD install on prod (read from `infra/` repo path)
- [ ] **C3.** Per-service semver via release-please monorepo manifest
- [ ] **C4.** Image promotion gates: prod requires manual ArgoCD sync (no
      auto-sync); staging is auto-sync
- [ ] **C5.** Production-grade observability (Prometheus alerts → on-call)
- [ ] **C6.** Per-service Helm value overlays per env

**Exit criteria:** A `forge-works-normalizer@1.4.0` release can deploy to
prod without affecting `forge-engine-event-router@0.5.2`'s clock; on-call
gets paged on staging-only failures before prod is touched.

### Phase D — Full GitOps + merge queue (post-Phase-6)

- [ ] **D1.** GitHub merge queue evaluation (resolves `strict: true` serial dance)
- [ ] **D2.** Renovate `automergeStrategy: squash` adjusted for merge queue
- [ ] **D3.** Branch-protection rule: forbid direct push to `main` (even
      admin bypass)
- [ ] **D4.** ArgoCD ApplicationSets for multi-tenant repo paths
- [ ] **D5.** Deployment SLOs + automatic rollback on SLI regression

---

## Open decisions

These are intentionally left open until the relevant phase begins:

1. **Staging AWS account:** new account (clean IAM boundary) vs reuse dev
   account with new IAM role. Decide at start of Phase B.
2. **Prod AWS account:** separate account is the default; revisit at Phase C
   if cost or ops complexity demands otherwise.
3. **Per-service version bump cadence:** release-please can group all
   monorepo bumps into one release PR or fan-out into per-package PRs.
   Pick at Phase C.
4. **Frontend image runtime:** Next.js standalone export vs server-side
   container. Trade-off with edge-deploy posture. Decide before A4.
5. **Helm chart consumers:** are external consumers expected? If yes, the
   OCI publish needs a public/signed flow. Default: internal-only, no
   signing in Phase A.
6. **Merge queue or strict:false:** Phase D will revisit; for now `strict:true`
   produces the serial-rebase dance acceptable for solo-dev cadence.

---

## References

- `RELEASE.md` — interim manual release process (to be retired post-A2)
- `docs/decisions/RELEASE_TOOLING.md` — Conventional Commits + release-please ADR
- `docs/PRE_COMMIT_EVALUATION.md` — pre-commit hooks rationale
- `docs/EKS_OPERATIONS.md` — dev cluster ops; staging/prod will follow same shape
- `roadmap/AUTOMATIONS_BACKLOG.md` — concrete sequenced work items
- `.github/renovate.json5` — dependency-bump cadence
- `.github/workflows/ci.yml` — main CI gate
- `.github/workflows/normalizer-image.yml` — reference image-push pattern
