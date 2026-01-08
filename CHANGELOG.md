# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- TurboRepo + PNPM monorepo architecture
- Service Catalog API with full CRUD operations
- Template API with ML-powered recommendations (rule-based Phase 1)
- Database schema with Alembic migrations
- Seed data for demo purposes
- Health check endpoints with adapter status
- Mock adapters for GitHub and ArgoCD integrations
- Comprehensive documentation (MONOREPO_SETUP.md, LOCAL_DEV.md)
- Project configuration files (LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md)

### Infrastructure
- FastAPI backend structure
- PostgreSQL database schema
- GitHub adapter with mock mode for repositories, branches, commits, PRs, and workflows
- ArgoCD adapter with mock mode for applications, sync operations, and deployment status
- Docker Compose for local development
- PNPM workspaces for frontend/backend/shared packages

## [0.1.0] - 2025-01-07

### Added
- Initial project scaffold
- Phase 1: Foundation implementation
- Core API endpoints for services and templates
- Database models: Team, Service, Template, Anomaly, Recommendation, Action
- Async SQLAlchemy with PostgreSQL support
- Pydantic schemas for request/response validation
- Integration tests with pytest-asyncio
