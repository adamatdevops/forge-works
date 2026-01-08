# Project Constraints

## Overview

This document outlines the technical, organizational, and resource constraints that shape ForgeWorks development decisions.

## Technical Constraints

### TC-001: Language & Runtime Versions

| Technology | Minimum Version | Rationale |
|------------|-----------------|-----------|
| Python | 3.11+ | Type hints, performance improvements, async enhancements |
| Node.js | 18+ | LTS support, native fetch, improved ESM |
| PostgreSQL | 14+ | JSON improvements, performance |
| Redis | 7+ | Functions, improved clustering |

### TC-002: Framework Choices

| Layer | Choice | Constraint Rationale |
|-------|--------|---------------------|
| Backend API | FastAPI | Async-first, OpenAPI generation, type safety |
| Frontend | Next.js 14+ | App router, server components, React ecosystem |
| ORM | SQLAlchemy 2.0 | Async support, type hints, mature ecosystem |
| Monorepo | TurboRepo + PNPM | Build caching, workspace management |

### TC-003: Infrastructure Dependencies

| Service | Purpose | Constraint |
|---------|---------|------------|
| GitHub | Source control, CI/CD | API rate limits apply |
| ArgoCD | GitOps deployments | Requires Kubernetes cluster |
| Kubernetes | Container orchestration | 1.28+ for gateway API |

### TC-004: API Design

- RESTful API design following OpenAPI 3.1 specification
- JSON request/response bodies
- UUID primary keys for external references
- Pagination required for list endpoints (max 100 items)
- Rate limiting: 100 requests/minute per client

## Organizational Constraints

### OC-001: Development Process

- All changes require pull request review
- Main branch protection enabled
- Conventional commits required
- Semantic versioning for releases

### OC-002: Documentation Requirements

- All public APIs must have OpenAPI documentation
- Architecture decisions recorded in ADRs
- README maintained for each package
- Inline code documentation for complex logic

### OC-003: Quality Standards

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Test Coverage | > 80% | CI gate |
| Type Coverage | 100% | mypy strict mode |
| Linting | Zero errors | Ruff + ESLint |
| Security Scan | Zero high/critical | Snyk + Gitleaks |

## Resource Constraints

### RC-001: Development Resources

- Single developer (portfolio project)
- Limited to open-source tooling
- No paid cloud services for demo
- Local development focus

### RC-002: Runtime Resources

| Resource | Development | Production Target |
|----------|-------------|-------------------|
| Memory | 4GB | 8GB per service |
| CPU | 2 cores | 4 cores per service |
| Storage | 10GB | 50GB database |

## Security Constraints

### SC-001: Authentication & Authorization

- API authentication via JWT tokens
- Role-based access control (RBAC)
- Service-to-service auth via mTLS (production)

### SC-002: Data Protection

- No PII in logs
- Secrets managed via environment variables
- Database encryption at rest (production)
- TLS for all external communication

### SC-003: Compliance

- OWASP Top 10 addressed
- Dependency vulnerability scanning
- Container image scanning
- No hardcoded credentials

## Performance Constraints

### PC-001: Response Time SLOs

| Endpoint Type | P50 | P99 |
|---------------|-----|-----|
| Health checks | 10ms | 50ms |
| List operations | 100ms | 500ms |
| CRUD operations | 50ms | 200ms |
| Recommendations | 200ms | 1000ms |

### PC-002: Throughput Targets

- 1000 requests/second (API gateway)
- 100 concurrent WebSocket connections
- 10,000 services in catalog

## Compatibility Constraints

### CC-001: Browser Support

- Chrome 90+
- Firefox 90+
- Safari 14+
- Edge 90+

### CC-002: API Versioning

- Breaking changes require new API version
- Deprecated endpoints supported for 6 months
- Version in URL path (/api/v1/)

## Constraint Exceptions

Exceptions to constraints require:
1. Documented justification
2. Risk assessment
3. Mitigation plan
4. Stakeholder approval

Track exceptions in GitHub Issues with `constraint-exception` label.
