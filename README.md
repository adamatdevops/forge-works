# ForgeWorks - Internal Developer Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![pnpm](https://img.shields.io/badge/pnpm-9+-orange.svg)](https://pnpm.io/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-purple.svg)](https://github.com/astral-sh/ruff)
[![Turborepo](https://img.shields.io/badge/built%20with-Turborepo-blue.svg)](https://turbo.build/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **A Golden Path Orchestrator that provides opinionated, production-ready service templates to standardize architecture, improve developer velocity, and enforce platform governance through design.**

## Overview

ForgeWorks is an Internal Developer Platform (IDP) that acts as an orchestration layer between development teams and infrastructure tooling. It provides:

- **Service Catalog** - Central registry of all microservices with health status, ownership, and deployment metrics
- **Golden Path Templates** - Production-ready service blueprints with built-in CI/CD, monitoring, and best practices
- **ML-Powered Recommendations** - Intelligent template suggestions based on workload type, language, and requirements
- **Anomaly Detection** - Surface deployment patterns that indicate potential issues (high deploy frequency, consecutive rollbacks)

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

### Services (`/api/v1/services`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List services (pagination, filtering, search) |
| GET | `/stats` | Service statistics for dashboard |
| GET | `/{id}` | Get service by ID |
| POST | `/` | Create new service |
| PUT | `/{id}` | Update service |
| DELETE | `/{id}` | Delete service |

### Templates (`/api/v1/templates`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List templates (filter by workload/language) |
| GET | `/{id}` | Get template details |
| POST | `/recommend` | Get ML-powered template recommendations |

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

See [LOCAL_DEV.md](docs/LOCAL_DEV.md) for detailed setup instructions.

## Key Features

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

Each template includes: CI/CD pipelines, monitoring, tests, documentation.

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

## License

MIT

---

*Built as a portfolio demonstration of Internal Developer Platform concepts and Platform Engineering practices.*
