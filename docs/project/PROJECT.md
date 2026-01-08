# Project Overview

## ForgeWorks - Dynamic Reliability

**Version:** 0.1.0
**Status:** Active Development
**Last Updated:** January 2025

## Executive Summary

ForgeWorks is an Internal Developer Platform (IDP) that provides a Golden Path Orchestrator for standardizing service creation, deployment, and governance. The platform enables development teams to focus on business logic while automatically inheriting production-ready infrastructure patterns.

## Problem Statement

Organizations scaling from small to mid-size engineering teams face common challenges:

1. **Inconsistent Service Architecture** - Each team creates services differently, leading to maintenance burden and knowledge silos
2. **Slow Developer Onboarding** - New engineers spend weeks understanding infrastructure before becoming productive
3. **Manual Compliance Enforcement** - Security and governance policies are checked manually, often too late in the development cycle
4. **Poor Visibility** - No central view of service health, ownership, and deployment patterns
5. **Repeated Infrastructure Work** - Teams solve the same problems (CI/CD, monitoring, security) independently

## Solution

ForgeWorks addresses these challenges through:

- **Service Catalog** - Central registry providing visibility into all services, ownership, and health status
- **Golden Path Templates** - Production-ready blueprints that encode best practices and compliance requirements
- **ML-Powered Recommendations** - Intelligent template suggestions based on workload characteristics
- **Anomaly Detection** - Surface deployment patterns that indicate potential issues
- **Self-Service Provisioning** - Developers create new services through guided workflows

## Target Users

| Role | Primary Use Case |
|------|------------------|
| Platform Engineers | Configure templates, define golden paths, monitor platform health |
| Developers | Create services, view catalog, understand deployment status |
| Engineering Managers | Review service ownership, track team metrics |
| Security/Compliance | Ensure governance policies are embedded in templates |

## Success Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Time to First Deploy | < 30 minutes | New services should be production-ready quickly |
| Template Adoption | > 80% | Most services should use golden paths |
| Developer Satisfaction | > 4.0/5.0 | Platform should improve developer experience |
| Security Compliance | 100% | All services inherit security controls |

## Project Timeline

### Phase 1: Foundation (Current)
- Service Catalog API
- Template API with recommendations
- Mock adapters for GitHub/ArgoCD
- Database schema and seed data

### Phase 2: Integration
- Real GitHub/ArgoCD integration
- Frontend dashboard
- Anomaly detection engine

### Phase 3: Intelligence
- ML model training on deployment patterns
- Advanced recommendations
- Self-healing capabilities

## Related Documents

- [Acceptance Criteria](./ACCEPTANCE_CRITERIA.md)
- [Constraints](./CONSTRAINTS.md)
- [Deliverables](./DELIVERABLES.md)
- [Architecture](../architecture.md)
