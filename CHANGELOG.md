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

### Changed

- **Release process: Changesets → Conventional Commits + manual `git tag` (interim) → release-please (target)** — `RELEASE.md` rewritten to describe the interim manual process; release-please wires in task #23
- **CI Success aggregate now gates on Security job** — `ci.yml` was silently passing CI Success when Snyk failed; added `needs.security.result` to the conditional

### Removed

- **Changesets infrastructure** — `.changeset/` directory, `.github/workflows/changeset-check.yml`, `.github/workflows/release.yml`, `pnpm changeset:*` / `pnpm release` scripts, `@changesets/cli` + `@changesets/changelog-github` devDependencies, `needs-changeset` + `skip-changeset` labels. Rationale in `docs/decisions/RELEASE_TOOLING.md`

### Security

- **Bumped `jackson-core` 2.15.3 → 2.18.7** across all 3 Flink modules — fixes 2 HIGH-severity Snyk findings (Allocation of Resources Without Limits / DoS, SNYK-JAVA-COMFASTERXMLJACKSONCORE-15907551 and -15365924)
- **Added dated `.snyk` ignores** for 8 HIGH transitive CVEs in `kafka-clients@3.4.0`, `commons-lang3@3.12.0`, and `lz4-java@1.8.0` — all require Flink 1.20 → 2.0 to remediate at the source. Each ignore carries a per-CVE rationale, in-context mitigation note, and an `expires: 2026-08-10` re-evaluation date. Tracked under task #24 (Flink 2.0 upgrade evaluation)

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
