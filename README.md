# ForgeWorks - Internal Developer Platform (IDP)

> **"An Internal Developer Platform that acts as a Golden Path Orchestrator — providing opinionated, production-ready service templates that standardize architecture, improve developer velocity, and enforce platform governance through design instead of policy."**

---

## Status: Phase 1 - Foundation 🚀

| Milestone | Status |
|-----------|--------|
| Planning & Brainstorming | ✅ Complete |
| Scope Finalization | ✅ Complete |
| Tech Stack Selection | ✅ Complete |
| Architecture Design | ✅ Complete |
| Documentation Structure | ✅ Complete |
| Phase 1: Foundation | 🔄 In Progress |
| Phase 2: Intelligence | ⏳ Not Started |
| Phase 3: Experience | ⏳ Not Started |
| Phase 4: Polish | ⏳ Not Started |

---

## Core Identity

**Golden Path Orchestrator** - The platform that defines how software is built across the organization.

| Principle | Description |
|-----------|-------------|
| Tools execute | The platform makes them work together |
| Governance by design | Standards encoded in templates, not policies |
| ML as advisor | Recommendations, not mandates |
| Agentless | All connectivity via APIs |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  EXPERIENCE LAYER     │  Next.js Dashboard + ML Recommender    │
├───────────────────────┼─────────────────────────────────────────┤
│  ML ORCHESTRATION     │  Template Recommender + Anomaly Panel  │
├───────────────────────┼─────────────────────────────────────────┤
│  API GLUE LAYER       │  FastAPI + Adapters + State Store      │
├───────────────────────┼─────────────────────────────────────────┤
│  TOOL APIS            │  GitHub, ArgoCD, Prometheus, K8s       │
└───────────────────────┴─────────────────────────────────────────┘
         NO AGENTS - ALL API CONNECTIONS
```

---

## Portfolio Context

```
Portfolio Projects:
├── ledger-supply-chain-security    ✅ Complete (DevSecOps)
│   └── Provides: Security scanning, SBOM, compliance
│
├── mlifecycle-orchestrator         ✅ Complete (MLOps)
│   └── Provides: ML model serving, zero-touch deployment
│
└── flagship-idp                    🔄 Planning → Implementation
    └── Consumes: Security + ML models as orchestration brain
```

---

## Documentation

### Planning Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [Vision](planning/VISION.md) | Core identity, value proposition | ✅ Finalized |
| [Scope](planning/SCOPE.md) | Feature scope and boundaries | ✅ Finalized |
| [Brainstorm](planning/BRAINSTORM.md) | Session notes (1-4) | ✅ Current |
| [Requirements](planning/REQUIREMENTS.md) | Detailed feature requirements | ⏳ Pending |

### Decision Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [Tech Stack](decisions/TECH_STACK.md) | Technology choices | ✅ Finalized |
| [Architecture](decisions/ARCHITECTURE.md) | System design, ML layer | ✅ Finalized |

### Pre-Implementation Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [MVP Definition](docs/MVP.md) | Minimum viable product scope | ✅ Finalized |
| [Golden Path Requirements](docs/GOLDEN_PATH_REQUIREMENTS.md) | Template standards | ✅ Finalized |
| [Success Criteria](docs/SUCCESS_CRITERIA.md) | Measurable outcomes | ✅ Finalized |
| [Industry Tools Analysis](docs/INDUSTRY_TOOLS_ANALYSIS.md) | Pain points mapping | ✅ Complete |
| [Documentation Roadmap](docs/DOCUMENTATION_ROADMAP.md) | All docs tracker | ✅ Created |

---

## Architecture Decision Records (ADRs)

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-001](adr/001-golden-path-identity.md) | Golden Path Orchestrator Identity | ✅ Accepted |
| [ADR-002](adr/002-agentless-architecture.md) | Agentless Architecture | ✅ Accepted |
| [ADR-003](adr/003-ml-advisory-layer.md) | ML as Advisory Layer | ✅ Accepted |
| [ADR-004](adr/004-asymmetric-ml-hybrid.md) | Asymmetric ML Hybrid | ✅ Accepted |
| [ADR-005](adr/005-tech-stack.md) | Technology Stack | ✅ Accepted |
| [ADR-006](adr/006-template-recommendation-primary.md) | Template Recommendation Primary | ✅ Accepted |

---

## Tech Stack Summary

### IDP Core

| Layer | Technology |
|-------|------------|
| Frontend | TypeScript + Next.js + Tailwind |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Cache/Queue | Redis |
| IaC | Pulumi (TypeScript) |
| GitOps | ArgoCD |
| Observability | Prometheus + Grafana |
| Build | Bazel |

### Golden Path Templates

| Template | Stack |
|----------|-------|
| Data Pipeline | Kafka + Airflow |
| Stream Processor | Kafka + Flink |
| ML Service | PyTorch + FastAPI |
| Go Microservice | Go + K8s |
| Python API | FastAPI + PostgreSQL |

---

## Key Features

| Feature | Description | ML Level |
|---------|-------------|----------|
| Service Catalog | Browse and manage services | - |
| Template Gallery | Golden path templates | - |
| ML Recommender | Template recommendations | **Full ML** |
| Anomaly Panel | Deployment anomaly surfacing | Rule-based |
| Self-Service Actions | Create, deploy, provision | - |

---

## Folder Structure

```
forge-works/
├── README.md                 # This file
├── docker-compose.yml        # Local development stack
├── planning/                 # Planning documents
│   ├── VISION.md
│   ├── SCOPE.md
│   ├── BRAINSTORM.md
│   └── REQUIREMENTS.md
├── decisions/                # Architecture decisions
│   ├── TECH_STACK.md
│   └── ARCHITECTURE.md
├── adr/                      # Architecture Decision Records
│   └── 001-006...
├── roadmap/                  # Execution planning
│   ├── PHASE.md
│   ├── TASKS.md
│   ├── PRIORITIZATION.md
│   └── ACTION_PLAN.md
├── docs/                     # Pre-implementation docs
│   ├── LOCAL_DEV.md          # Local development guide
│   ├── MVP.md
│   ├── SUCCESS_CRITERIA.md
│   └── ...
├── scripts/                  # Development scripts
│   └── init-db.sql
└── src/                      # Source code
    ├── backend/              # Python FastAPI
    │   ├── app/
    │   │   ├── api/routes/   # API endpoints
    │   │   ├── core/         # Configuration
    │   │   ├── db/           # Database models
    │   │   ├── adapters/     # External integrations
    │   │   └── ml/           # ML components
    │   ├── tests/
    │   └── pyproject.toml
    ├── frontend/             # Next.js (Phase 3)
    └── shared/               # Shared utilities
```

---

## Next Steps

### Phase 1: Foundation (Current) 🔄
- [x] MVP Definition
- [x] Golden Path Requirements
- [x] Success Criteria
- [x] Project scaffolding (monorepo structure)
- [x] Docker Compose setup
- [x] FastAPI backend structure
- [x] Health endpoint
- [x] Local Development Guide
- [ ] Database schema & migrations
- [ ] Service Catalog API (CRUD)
- [ ] Template API
- [ ] Mock adapters (GitHub, ArgoCD)

### Phase 2: Intelligence
- [ ] Training data generation
- [ ] ML model development
- [ ] Template recommendation endpoint
- [ ] Anti-pattern detection

### Phase 3: Experience
- [ ] Next.js frontend setup
- [ ] Dashboard page
- [ ] Service catalog UI
- [ ] Template gallery
- [ ] Create service wizard
- [ ] Anomaly panel

### Phase 4: Polish
- [ ] End-to-end integration
- [ ] Demo script
- [ ] Mock data refinement
- [ ] Interview prep

---

## Team

| Member | Role | Responsibility |
|--------|------|----------------|
| Adam | Team Leader | Architecture, decisions |
| Claude | Right-Hand | Implementation, docs |
| Codex | DevOps Engineer | CI/CD, scripts |
| ChatGPT | Advisor | Strategy, review |

---

## Related Resources

- [Comprehensive Overview](../feedback/FLAGSHIP_PROJECT_OVERVIEW.md)
- [Team Decision Matrix](../feedback/TEAM_DECISION_MATRIX.md)

---

*Last Updated: 2025-01-06*
