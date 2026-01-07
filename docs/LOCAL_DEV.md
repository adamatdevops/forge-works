# Local Development Setup

> **Status:** Active
> **Last Updated:** 2025-01-06
> **Purpose:** Guide for setting up ForgeWorks local development environment

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Python | 3.11+ | Backend development |
| Node.js | 20 LTS | Frontend development |
| Git | 2.40+ | Version control |

### Verify Installation

```bash
# Check versions
docker --version          # Docker version 24.x.x
docker compose version    # Docker Compose version v2.x.x
python3 --version         # Python 3.11.x
node --version            # v20.x.x
git --version             # git version 2.x.x
```

---

## Quick Start

### 1. Clone and Navigate

```bash
cd /path/to/forge-works
```

### 2. Environment Setup

```bash
# Copy environment template
cp src/backend/.env.example src/backend/.env

# Edit if needed (defaults work for local dev)
```

### 3. Start All Services

```bash
# Start everything with Docker Compose
docker compose up -d

# View logs
docker compose logs -f
```

### 4. Verify Services

| Service | URL | Expected |
|---------|-----|----------|
| Backend API | http://localhost:8000/health | `{"status": "healthy"}` |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Frontend | http://localhost:3000 | Dashboard (Phase 3) |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |

```bash
# Quick health check
curl http://localhost:8000/health
```

---

## Development Workflows

### Backend Development (Python/FastAPI)

#### Option A: Docker (Recommended)

```bash
# Start services
docker compose up -d

# View backend logs
docker compose logs -f backend

# Restart after code changes (auto-reload enabled)
# Changes in src/backend/ are automatically detected
```

#### Option B: Local Python Environment

```bash
# Navigate to backend
cd src/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and Redis via Docker
docker compose up -d postgres redis

# Run FastAPI locally
uvicorn app.main:app --reload --port 8000
```

### Frontend Development (Next.js)

```bash
# Navigate to frontend
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Database Management

### Access PostgreSQL

```bash
# Via Docker
docker compose exec postgres psql -U postgres -d forgedb

# Via local psql (if installed)
psql -h localhost -U postgres -d forgedb
```

### Run Migrations (Alembic)

```bash
# Generate new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback
docker compose exec backend alembic downgrade -1
```

### Reset Database

```bash
# Stop services
docker compose down

# Remove volume
docker volume rm forge-works_postgres_data

# Restart (fresh database)
docker compose up -d
```

---

## Testing

### Run Backend Tests

```bash
# Via Docker
docker compose exec backend pytest

# With coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Specific test file
docker compose exec backend pytest tests/unit/test_health.py -v
```

### Run Frontend Tests

```bash
cd src/frontend
npm test
```

---

## Code Quality

### Linting & Formatting

```bash
# Backend - Format with Black
docker compose exec backend black app tests

# Backend - Lint with Ruff
docker compose exec backend ruff check app tests

# Backend - Type check with MyPy
docker compose exec backend mypy app
```

### Pre-commit Checks

```bash
# Run all checks
docker compose exec backend black --check app tests
docker compose exec backend ruff check app tests
docker compose exec backend mypy app
docker compose exec backend pytest
```

---

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # or :3000, :5432, :6379

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Docker Build Issues

```bash
# Rebuild without cache
docker compose build --no-cache

# Remove all containers and volumes
docker compose down -v

# Fresh start
docker compose up -d --build
```

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development Stack                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Browser                                                    │
│      │                                                       │
│      ▼                                                       │
│   ┌─────────────┐       ┌─────────────┐                     │
│   │  Frontend   │──────▶│   Backend   │                     │
│   │  Next.js    │       │   FastAPI   │                     │
│   │  :3000      │       │   :8000     │                     │
│   └─────────────┘       └─────────────┘                     │
│                               │                              │
│                    ┌──────────┴──────────┐                  │
│                    ▼                      ▼                  │
│              ┌──────────┐          ┌──────────┐             │
│              │ PostgreSQL│          │   Redis  │             │
│              │   :5432   │          │   :6379  │             │
│              └──────────┘          └──────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

### Backend (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | ForgeWorks | Application name |
| `DEBUG` | true | Debug mode |
| `ENVIRONMENT` | development | Environment name |
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL connection |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `CORS_ORIGINS` | ["http://localhost:3000"] | Allowed origins |

### Frontend (.env.local)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend API URL |

---

## Useful Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f [service]

# Restart a service
docker compose restart [service]

# Execute command in container
docker compose exec [service] [command]

# Build/rebuild services
docker compose build [service]

# Remove everything (including volumes)
docker compose down -v --rmi all
```

---

## Next Steps

After local setup is working:

1. [ ] Run health check: `curl http://localhost:8000/health`
2. [ ] Explore API docs: http://localhost:8000/docs
3. [ ] Check database connection: `docker compose exec postgres psql -U postgres -d forgedb`
4. [ ] Run tests: `docker compose exec backend pytest`

---

*Local development guide created: 2025-01-06*
