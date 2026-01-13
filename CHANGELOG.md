# Changelog

All notable changes to ForgeWorks are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Next Steps
- Add WebSocket real-time updates
- Kubernetes adapter integration
- User authentication (JWT)

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

| Version | Phase | Status | Date |
|---------|-------|--------|------|
| 0.4.0 | Phase 4: Operations | Planned | TBD |
| 0.3.0 | Phase 3: Experience | **Complete** | 2025-01-12 |
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
