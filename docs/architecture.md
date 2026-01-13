# Architecture Overview

## System Architecture

ForgeWorks follows a layered architecture with clear separation of concerns between the API layer, business logic, data access, and external integrations.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                   Dashboard / Service Catalog UI                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│            /api/v1/services  /api/v1/templates  /health         │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Service CRUD │     │  Template API   │     │  ML Recommender │
│     Layer     │     │    + Matching   │     │   (Rule-based)  │
└───────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Layer (SQLAlchemy)               │
│               Services | Templates | Teams | Anomalies           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     External Adapters                            │
│         GitHub API  │  ArgoCD API  │  Kubernetes API             │
│         (Mock/Live) │  (Mock/Live) │    (Planned)                │
└─────────────────────────────────────────────────────────────────┘
```

## Component Overview

### API Layer

The API layer is built with FastAPI and provides RESTful endpoints for all platform operations.

| Component | Responsibility |
|-----------|----------------|
| `api/routes/services.py` | Service catalog CRUD operations |
| `api/routes/templates.py` | Template listing and recommendations |
| `api/routes/anomalies.py` | Anomaly detection and management |
| `api/routes/metrics.py` | Platform metrics and DORA |
| `api/routes/health.py` | Health checks and system status |

### Business Logic Layer

| Component | Responsibility |
|-----------|----------------|
| `crud/service.py` | Service business logic and data operations |
| `crud/template.py` | Template matching and scoring algorithms |
| `ml/recommender.py` | ML-powered template recommendations |

### Data Layer

| Component | Responsibility |
|-----------|----------------|
| `db/models/` | SQLAlchemy ORM models |
| `db/base.py` | Database session management |
| `schemas/` | Pydantic validation schemas |

### Adapter Layer

| Adapter | Purpose | Mode |
|---------|---------|------|
| `adapters/github.py` | Repository and CI/CD integration | Mock/Live |
| `adapters/argocd.py` | GitOps deployment management | Mock/Live |
| `adapters/base.py` | Base adapter interface | - |

## Data Model

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│     Team     │       │   Service    │       │   Template   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id           │◄──────│ team_id      │       │ id           │
│ name         │       │ template_id  │──────►│ name         │
│ slug         │       │ name         │       │ workload_type│
│ email        │       │ status       │       │ language     │
│ slack_channel│       │ tier         │       │ capabilities │
└──────────────┘       │ repository   │       │ ideal_for    │
                       │ namespace    │       │ stack        │
                       │ tags         │       └──────────────┘
                       │ anomalies[]  │
                       └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Anomaly    │
                       ├──────────────┤
                       │ id           │
                       │ service_id   │
                       │ type         │
                       │ severity     │
                       │ is_active    │
                       └──────────────┘
```

### Key Relationships

- **Team → Services**: One-to-many (team owns multiple services)
- **Template → Services**: One-to-many (template used by multiple services)
- **Service → Anomalies**: One-to-many (service can have multiple anomalies)

## Request Flow

### Service Creation Flow

```
1. Client POST /api/v1/services
                │
2. Validate request (Pydantic schema)
                │
3. Generate slug from name
                │
4. Verify team exists
                │
5. Verify template exists (optional)
                │
6. Create database record
                │
7. Return ServiceResponse with relations
```

### Template Recommendation Flow

```
1. Client POST /api/v1/templates/recommend
                │
2. Parse requirements (workload_type, language, etc.)
                │
3. Query matching templates
                │
4. Score each template:
   - workload_type match: 40 points
   - language match: 30 points
   - capability overlap: 20 points
   - ideal_for match: 10 points
                │
5. Sort by score descending
                │
6. Return top N with explanations
```

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.109+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | Validation |
| Alembic | 1.13+ | Migrations |
| asyncpg | 0.29+ | PostgreSQL driver |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14+ | React framework |
| TypeScript | 5+ | Type safety |
| Tailwind CSS | 3+ | Styling |
| TanStack Query | 5+ | Data fetching |
| Zustand | 4+ | State management |
| shadcn/ui | - | UI components |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 14+ | Primary database |
| Redis | 7+ | Caching (planned) |
| Docker | 24+ | Containerization |
| Kubernetes | 1.28+ | Orchestration |
| ArgoCD | 2.9+ | GitOps |

## Security Architecture

### Authentication (Planned)

```
Client → API Gateway → JWT Validation → Route Handler
                           │
                           ▼
                    Token Claims:
                    - user_id
                    - roles[]
                    - team_id
```

### Authorization Model

| Role | Permissions |
|------|-------------|
| Admin | Full access to all resources |
| Platform Engineer | Manage templates, view all services |
| Developer | CRUD own team's services, view templates |
| Viewer | Read-only access |

## Deployment Architecture

### Local Development

```
Docker Compose
├── backend (FastAPI)
├── frontend (Next.js)
├── postgres (Database)
└── redis (Cache)
```

### Production (Target)

```
Kubernetes Cluster
├── Ingress Controller
├── Backend Deployment (3 replicas)
├── Frontend Deployment (2 replicas)
├── PostgreSQL (Managed/StatefulSet)
├── Redis (Managed/StatefulSet)
└── ArgoCD (GitOps)
```

## Diagrams

Comprehensive architecture diagrams are available in [`docs/diagrams/SYSTEM_DIAGRAMS.md`](./diagrams/SYSTEM_DIAGRAMS.md) using Mermaid format.

| Diagram | Description |
|---------|-------------|
| System Context (C4 L1) | High-level system and external actors |
| Container (C4 L2) | Technical containers (Frontend, Backend, DB) |
| Component - Backend (C4 L3) | Backend API, CRUD, Adapters |
| Component - Frontend (C4 L3) | Layer architecture, state management |
| Data Flow | How data moves through the system |
| Deployment | Local (Docker) and Production (K8s) |
| Sequence Diagrams | Service creation, anomaly detection, recommendations |
| ERD | Database entity relationships |
| Layer Architecture | ForgeWorks unique UI pattern |
| Adapter Pattern | Mock/Live switching mechanism |

## Related Documents

- [Project Overview](./project/PROJECT.md)
- [Constraints](./project/CONSTRAINTS.md)
- [Local Development](./LOCAL_DEV.md)
