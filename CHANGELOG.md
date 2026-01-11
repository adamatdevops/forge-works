# Changelog

All notable changes to ForgeWorks are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Phase 3: Experience - In Progress (Started 2025-01-12)

#### Added
- Layers Architecture concept - revolutionary Figma-like UI paradigm
- Phase 3 Action Plan (`roadmap/ACTION_PLAN_PHASE3.md`)
- Layers Architecture specification (`docs/features/LAYERS_ARCHITECTURE.md`)

#### Documentation Updates (2025-01-11)
- Updated PHASE.md: Synced Phase 1 & 2 to COMPLETE status
- Updated TASKS.md: Introduced dynamic task schema
  - Priority: OPTIONAL | LOW | MEDIUM | HIGH | CRITICAL
  - Relevancy: TRUE | FALSE
  - Recommendation: DELETE | SKIP | RE-WRITE | MOVE | EXECUTE
  - Status: TODO | ON_PROGRESS | SKIPPED | FAILED | SUCCESS
- Added Phase 3 task backlog: 38 tasks across 8 epics

#### Planned - Phase 3
- Next.js 14+ frontend with TypeScript
- Tailwind CSS + shadcn/ui component library
- Layer Panel UI with visibility toggles
- Glue Bus (shared data context)
- Services Layer
- Templates Layer
- Anomalies Layer
- Pipeline Layer
- Dashboard composition with all layers

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

## Roadmap Updates Log

### 2025-01-11 - Documentation Sync & Layers Architecture

| Change | File | Description |
|--------|------|-------------|
| UPDATE | `roadmap/PHASE.md` | Phase 1 & 2 marked COMPLETE, Phase 3 updated with Layers Architecture |
| UPDATE | `roadmap/TASKS.md` | New dynamic task schema, 38 Phase 3 tasks added |
| CREATE | `roadmap/ACTION_PLAN_PHASE3.md` | Sprint-based action plan for frontend |
| CREATE | `docs/features/LAYERS_ARCHITECTURE.md` | Revolutionary Layers Architecture spec |

#### New Architecture Concept: Layers
- **Paradigm Shift:** Tabs -> Layers (Figma-like composition)
- **The Glue:** Shared identifiers connecting layers (service_id, commit_sha, etc.)
- **Performance:** Lazy rendering, shared data bus, selective updates
- **Differentiation:** No other IDP offers this visualization approach

---

## Version History Summary

| Version | Phase | Status | Date |
|---------|-------|--------|------|
| 0.3.0 | Phase 3: Experience | In Progress | 2025-01-12 |
| 0.2.0 | Phase 2: Intelligence | Complete | 2025-01-08 |
| 0.1.0 | Phase 1: Foundation | Complete | 2025-01-08 |
| 0.0.1 | Phase 0: Planning | Complete | 2025-01-06 |

---

## Links

- [Phase Definitions](roadmap/PHASE.md)
- [Task Management](roadmap/TASKS.md)
- [Phase 3 Action Plan](roadmap/ACTION_PLAN_PHASE3.md)
- [Layers Architecture](docs/features/LAYERS_ARCHITECTURE.md)
- [Prioritization Framework](roadmap/PRIORITIZATION.md)
