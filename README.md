# ForgeWorks - Dynamic Reliability

<!-- Quality Signals -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![ESLint 9+](https://img.shields.io/badge/ESLint-9+-4B32C3.svg?logo=eslint&logoColor=white)](https://eslint.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<!-- Security -->
[![Snyk](https://img.shields.io/badge/Snyk-protected-4C4A73.svg?logo=snyk&logoColor=white)](https://snyk.io/)
[![Gitleaks](https://img.shields.io/badge/protected%20by-gitleaks-blue.svg)](https://github.com/gitleaks/gitleaks)
[![Hadolint](https://img.shields.io/badge/Dockerfile%20linter-hadolint-40b5a4.svg)](https://github.com/hadolint/hadolint)

<!-- Stack -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript 5+](https://img.shields.io/badge/TypeScript-5+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Turborepo](https://img.shields.io/badge/built%20with-Turborepo-blue.svg)](https://turbo.build/)

> **A Platform Orchestrator that provides opinionated, production-ready service templates to standardize architecture, improve developer velocity, and enforce platform governance through design.**

## What ForgeWorks is NOT

Before diving in, let's clarify scope:

- **NOT a deployment tool** - ForgeWorks doesn't deploy your infrastructure. It provides templates and recommendations; actual provisioning is handled by your existing CI/CD (ArgoCD, GitHub Actions).
- **NOT a replacement for Kubernetes** - It's an orchestration layer that sits *above* your cluster, providing developer-facing workflows.
- **NOT a full PaaS** - It's a catalog + recommendation engine, not a Heroku-style managed platform.

**ForgeWorks IS:** An Internal Developer Platform (IDP) that standardizes service creation through ML-guided golden path templates and provides visibility into your service ecosystem.

## Overview

ForgeWorks is an Internal Developer Platform (IDP) that acts as an orchestration layer between development teams and infrastructure tooling. It provides:

- **Service Catalog** - Central registry of all microservices with health status, ownership, and deployment metrics
- **Golden Path Templates** - Production-ready service blueprints with built-in CI/CD, monitoring, and best practices
- **ML-Powered Recommendations** - Intelligent template suggestions based on workload type, language, and requirements
- **Anomaly Detection** - Surface deployment patterns that indicate potential issues (high deploy frequency, consecutive rollbacks)

## Project Status

### Implemented (Verifiable)

- [x] **Repository scaffolding** - [turbo.json](turbo.json), [pnpm-workspace.yaml](pnpm-workspace.yaml)
- [x] **Monorepo setup** - TurboRepo + PNPM workspace ([package.json](package.json))
- [x] **Database schema & migrations** - [Alembic migrations](src/backend/alembic/versions/)
- [x] **Service Catalog API** - [CRUD endpoints](src/backend/app/api/routes/services.py)
- [x] **Template API** - [Template routes](src/backend/app/api/routes/templates.py)
- [x] **ML Recommender** - [Rule-based engine](src/backend/app/ml/recommender.py)
- [x] **Seed data** - [Demo seeder](src/backend/app/db/seed.py)
- [x] **Mock adapters** - [GitHub](src/backend/app/adapters/github.py), [ArgoCD](src/backend/app/adapters/argocd.py)
- [x] **Anomaly API** - [Detection routes](src/backend/app/api/routes/anomalies.py)
- [x] **Metrics API** - [DORA metrics](src/backend/app/api/routes/metrics.py)
- [x] **API docs** - Auto-generated at `/docs` endpoint
- [x] **Versioning** - [Changesets config](.changeset/config.json)
- [x] **Unit tests** - 159 tests ([test suite](src/backend/tests/unit/))
- [x] **Auth backend** - [JWT security](src/backend/app/core/security.py), [Auth routes](src/backend/app/api/routes/auth.py)

### Demo-Ready (Run to See)

```bash
# Backend API with Swagger docs
cd src/backend && uvicorn app.main:app --reload
# Visit http://localhost:8000/docs

# Frontend dashboard
cd src/frontend && pnpm dev
# Visit http://localhost:3000
```

- [x] **Frontend Layers UI** - [Layer store](src/frontend/src/store/layers.ts), [GlueBus](src/frontend/src/store/glue.ts)
- [x] **Auth pages** - [Login](src/frontend/src/app/login/page.tsx), [Register](src/frontend/src/app/register/page.tsx)
- [x] **WebSocket** - [Real-time endpoint](src/backend/app/api/routes/websocket.py)

### Planned (Tracked)

- [ ] Auth frontend integration (token storage, protected routes)
- [ ] E2E tests with Playwright
- [ ] Docker Compose for one-command demo
- [ ] CI/CD pipeline (GitHub Actions)

## Architecture

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
              AGENTLESS - ALL API CONNECTIONS
```

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Agentless** | No agents deployed - all connectivity via REST APIs |
| **Governance by Design** | Standards encoded in templates, not policy documents |
| **ML as Advisor** | Recommendations to guide, not mandates to enforce |
| **Golden Paths** | Opinionated defaults that teams can extend |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | TypeScript / Next.js / Tailwind |
| Database | PostgreSQL |
| Cache | Redis |
| ML | scikit-learn |
| Container | Docker |

## Project Structure

```
forge-works/
├── src/
│   ├── backend/           # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/       # REST endpoints
│   │   │   ├── crud/      # Database operations
│   │   │   ├── db/        # Models & migrations
│   │   │   ├── schemas/   # Pydantic models
│   │   │   ├── adapters/  # External integrations
│   │   │   └── ml/        # ML components
│   │   ├── tests/
│   │   └── alembic/       # Database migrations
│   └── frontend/          # Next.js frontend
├── scripts/               # Development utilities
├── docs/                  # Documentation
└── docker-compose.yml     # Local development stack
```

## API Endpoints

The following endpoints are implemented and available in the current build.

### Services (`/api/v1/services`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List services (pagination, filtering, search) |
| GET | `/stats` | Service statistics for dashboard |
| GET | `/{id}` | Get service by ID |
| GET | `/slug/{slug}` | Get service by slug |
| POST | `/` | Create new service |
| PUT | `/{id}` | Update service |
| DELETE | `/{id}` | Delete service |

### Templates (`/api/v1/templates`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List templates (filter by workload/language) |
| GET | `/{id}` | Get template details |
| GET | `/slug/{slug}` | Get template by slug |
| POST | `/recommend` | Get ML-powered template recommendations |

### Anomalies (`/api/v1/anomalies`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List anomalies (filter by severity, type, status) |
| GET | `/stats` | Anomaly statistics |
| GET | `/{id}` | Get anomaly details |
| POST | `/` | Create anomaly (from detection systems) |
| PATCH | `/{id}` | Update anomaly |
| POST | `/{id}/acknowledge` | Acknowledge anomaly |
| POST | `/{id}/resolve` | Resolve anomaly |
| DELETE | `/{id}` | Delete anomaly |

### Metrics (`/api/v1/metrics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Comprehensive metrics dashboard |
| GET | `/dora` | DORA metrics only |
| GET | `/health` | Service health metrics |
| GET | `/deployment` | Deployment statistics |

### Health (`/health`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Component health status |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)

### Local Development

```bash
# Clone the repository
git clone https://github.com/adamatdevops/forge-works.git
cd forge-works

# Start infrastructure (PostgreSQL, Redis)
docker-compose up -d

# Backend setup
cd src/backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.db.seed

# Start the API server
uvicorn app.main:app --reload
```

API documentation available at `http://localhost:8000/docs`

```bash
# Frontend setup (new terminal)
cd src/frontend
pnpm install
pnpm dev
```

Frontend available at `http://localhost:3000`

See [LOCAL_DEV.md](docs/LOCAL_DEV.md) for detailed setup instructions.

## Key Features

### Frontend Dashboard (Layers Architecture)
A Figma-inspired composable UI built with:
- **Layer Panel** - Toggle visibility and reorder dashboard layers
- **GlueBus** - Pub/sub pattern for cross-layer communication
- **Service Catalog Layer** - Grid view with health indicators
- **Templates Layer** - ML-powered recommendation interface
- **Pipelines Layer** - CI/CD status with real-time updates
- **Anomalies Layer** - Deployment pattern alerts

### Service Catalog
Central registry showing all services with:
- Health status (healthy, degraded, unhealthy)
- Ownership (team assignment)
- Deployment metrics (deploys today, rollbacks this week)
- Links to documentation, dashboards, runbooks

### Golden Path Templates
Pre-configured service blueprints including:
- **Python API** - FastAPI + PostgreSQL + async
- **Go Microservice** - High-performance services
- **Stream Processor** - Kafka + event-driven
- **Data Pipeline** - Batch processing workflows
- **ML Service** - Model serving infrastructure

Each template is designed to include CI/CD pipelines, monitoring, tests, and documentation as part of the Golden Path standard.

### ML Template Recommender
Intelligent matching based on:
- Workload type (api, batch, stream, ml)
- Programming language preference
- Capability requirements
- Team usage patterns (future)

### Anomaly Detection Panel
Surfaces potential issues:
- High deploy frequency (>5 deploys/day)
- Consecutive rollbacks
- Pipeline failures
- Health degradation patterns

## For Reviewers

This repository is the **implementation surface** of an Internal Developer Platform concept:

- The focus is on demonstrating **platform engineering thinking**, governance-through-design, and ML-assisted guidance
- Architecture decisions and planning artifacts guide all implementation choices
- This is a portfolio demonstration, not a simulation of a full enterprise deployment

The codebase showcases real patterns used in production IDPs while remaining appropriately scoped for evaluation.

## License

MIT

---

*Built as a portfolio demonstration of Internal Developer Platform concepts and Platform Engineering practices.*
