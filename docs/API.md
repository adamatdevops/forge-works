# ForgeWorks API Documentation

ForgeWorks provides a comprehensive REST API for managing the Internal Developer Platform (IDP). The API is built with FastAPI and follows OpenAPI 3.0 specifications.

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.forge-works.io/api/v1
```

## Interactive Documentation

- **Swagger UI**: `/docs` - Interactive API explorer
- **ReDoc**: `/redoc` - Alternative documentation viewer

## Authentication

> **Status: Planned** - Authentication is not yet implemented in the current version.

When implemented, the API will use bearer token authentication:

```bash
Authorization: Bearer <your-api-token>
```

Currently, all endpoints are accessible without authentication (development mode).

---

## Endpoints Overview

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| [Health](#health) | 2 | Health checks and readiness |
| [Services](#services) | 7 | Service catalog CRUD |
| [Templates](#templates) | 4 | Golden path templates |
| [Anomalies](#anomalies) | 8 | Anomaly detection and management |
| [Metrics](#metrics) | 4 | Platform metrics and DORA |

---

## Health

### GET /health

Health check endpoint for liveness probes.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "ForgeWorks",
  "version": "0.3.0",
  "environment": "development",
  "timestamp": "2025-01-12T10:30:00Z"
}
```

---

## Services

Service catalog management for all platform services.

### GET /api/v1/services

List all services with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| page_size | int | Items per page (default: 20, max: 100) |
| status | enum | Filter by status: `healthy`, `degraded`, `unhealthy`, `provisioning` |
| tier | enum | Filter by tier: `critical`, `standard`, `internal` |
| team_id | uuid | Filter by team |
| search | string | Search in name/description |

**Response:**
```json
{
  "services": [
    {
      "id": "uuid",
      "name": "payment-service",
      "slug": "payment-service",
      "description": "Payment processing service",
      "team_id": "uuid",
      "template_id": "uuid",
      "status": "healthy",
      "tier": "critical",
      "repository_url": "https://github.com/org/payment-service",
      "repository_branch": "main",
      "namespace": "production",
      "argocd_app_name": "payment-service",
      "deploys_today": 3,
      "rollbacks_this_week": 0,
      "last_deploy_at": "2025-01-12T09:00:00Z",
      "tags": ["payments", "fintech"],
      "metadata": {},
      "documentation_url": "https://docs.example.com/payment",
      "dashboard_url": "https://grafana.example.com/d/payment",
      "runbook_url": "https://runbooks.example.com/payment",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-12T10:00:00Z",
      "team": {
        "id": "uuid",
        "name": "Platform Team",
        "slug": "platform-team"
      },
      "template": {
        "id": "uuid",
        "name": "Python API",
        "slug": "python-api",
        "workload_type": "api",
        "language": "python"
      },
      "anomalies": []
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### GET /api/v1/services/stats

Get service catalog statistics.

**Response:**
```json
{
  "total_services": 42,
  "by_status": {
    "healthy": 35,
    "degraded": 5,
    "unhealthy": 2
  },
  "by_tier": {
    "critical": 10,
    "standard": 25,
    "internal": 7
  },
  "active_anomalies": 3,
  "deploys_today": 15,
  "rollbacks_this_week": 2
}
```

### GET /api/v1/services/{service_id}

Get a specific service by ID.

**Response:** Single service object (same schema as list item)

### GET /api/v1/services/slug/{slug}

Get a service by slug.

**Response:** Single service object

### POST /api/v1/services

Create a new service.

**Request Body:**
```json
{
  "name": "new-service",
  "description": "My new service",
  "team_id": "uuid",
  "template_id": "uuid",
  "tier": "standard",
  "repository_url": "https://github.com/org/new-service",
  "namespace": "development",
  "tags": ["backend"]
}
```

**Response:** Created service object (201)

### PUT /api/v1/services/{service_id}

Update an existing service.

**Request Body:** Partial service object (only include fields to update)

**Response:** Updated service object

### DELETE /api/v1/services/{service_id}

Delete a service.

**Response:** 204 No Content

---

## Templates

Golden path templates for service scaffolding.

### GET /api/v1/templates

List all templates.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| page_size | int | Items per page |
| workload_type | enum | Filter: `api`, `batch`, `stream`, `ml` |
| language | enum | Filter: `python`, `go`, `typescript`, `java` |
| is_active | bool | Filter by active status |

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "Python FastAPI",
      "slug": "python-fastapi",
      "description": "FastAPI microservice template",
      "version": "1.0.0",
      "workload_type": "api",
      "language": "python",
      "capabilities": ["rest-api", "async", "database"],
      "ideal_for": ["microservices", "backend-api"],
      "stack": {
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "cache": "Redis"
      },
      "repository_url": "https://github.com/org/template-python-fastapi",
      "documentation_url": "https://docs.example.com/templates/fastapi",
      "includes_ci": true,
      "includes_cd": true,
      "includes_monitoring": true,
      "includes_tests": true,
      "usage_count": 15,
      "is_active": true,
      "is_recommended": true,
      "created_at": "2024-06-01T00:00:00Z",
      "updated_at": "2025-01-10T00:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### GET /api/v1/templates/{template_id}

Get a specific template by ID.

**Response:** Single template object (same schema as list item)

### GET /api/v1/templates/slug/{slug}

Get a template by slug.

**Response:** Single template object

### POST /api/v1/templates/recommend

Get ML-powered template recommendations based on requirements.

**Request Body:**
```json
{
  "workload_type": "api",
  "language": "python",
  "requirements": ["low_latency", "high_throughput"]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "recommendations": [
    {
      "template": { /* full template object */ },
      "score": 0.95,
      "match_reasons": [
        "Exact workload type match: api",
        "Exact language match: python",
        "Includes: CI, CD, monitoring, tests"
      ],
      "warnings": []
    }
  ],
  "top_recommendation": { /* template object */ },
  "processing_time_ms": 12.5,
  "model_version": "1.0.0-rule-based"
}
```

> **Note:** Template creation and updates are not yet exposed via API. Templates are managed through database seeding.

---

## Anomalies

Anomaly detection and incident management.

### GET /api/v1/anomalies

List anomalies with filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| page_size | int | Items per page |
| service_id | uuid | Filter by service |
| severity | enum | `critical`, `warning`, `info` |
| type | enum | Anomaly type (see types below) |
| active | bool | Filter active anomalies |
| resolved | bool | Filter resolved anomalies |

**Anomaly Types:**
- `high_deploy_frequency` - Too many deploys in short time
- `consecutive_rollbacks` - Multiple rollbacks
- `pipeline_failing` - CI/CD pipeline stuck failing
- `health_degraded` - Service health declining
- `unusual_error_rate` - Error spike detected
- `resource_spike` - CPU/Memory spike
- `drift_detected` - Configuration drift from template

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "service_id": "uuid",
      "type": "high_deploy_frequency",
      "severity": "warning",
      "title": "High deployment frequency detected",
      "description": "12 deployments in the last hour exceeds normal pattern",
      "suggestion": "Review if all deployments are intentional",
      "detected_value": "12 deploys/hour",
      "expected_value": "2-3 deploys/hour",
      "detection_rule": "deploy_frequency > 5/hour",
      "context": {
        "commits": ["abc123", "def456"],
        "authors": ["dev1", "dev2"]
      },
      "is_active": true,
      "is_acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "is_resolved": false,
      "resolved_at": null,
      "resolution_note": null,
      "detected_at": "2025-01-12T10:30:00Z",
      "created_at": "2025-01-12T10:30:00Z",
      "updated_at": "2025-01-12T10:30:00Z",
      "service": {
        "id": "uuid",
        "name": "payment-service",
        "slug": "payment-service",
        "status": "healthy"
      }
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### GET /api/v1/anomalies/stats

Get anomaly statistics.

**Response:**
```json
{
  "total": 25,
  "by_severity": {
    "critical": 2,
    "warning": 8,
    "info": 15
  },
  "by_type": {
    "high_deploy_frequency": 3,
    "pipeline_failing": 2,
    "health_degraded": 5
  },
  "active": 10,
  "acknowledged": 5,
  "unresolved": 12
}
```

### GET /api/v1/anomalies/{anomaly_id}

Get a specific anomaly.

### POST /api/v1/anomalies

Create a new anomaly (typically called by detection systems).

**Request Body:**
```json
{
  "service_id": "uuid",
  "type": "high_deploy_frequency",
  "severity": "warning",
  "title": "High deployment frequency detected",
  "description": "Detailed description",
  "suggestion": "Recommended action",
  "detected_value": "12 deploys",
  "expected_value": "2-3 deploys",
  "detection_rule": "rule_name",
  "context": {}
}
```

### PATCH /api/v1/anomalies/{anomaly_id}

Update an anomaly.

### POST /api/v1/anomalies/{anomaly_id}/acknowledge

Acknowledge an anomaly.

**Request Body:**
```json
{
  "acknowledged_by": "user@example.com"
}
```

### POST /api/v1/anomalies/{anomaly_id}/resolve

Mark an anomaly as resolved.

**Request Body:**
```json
{
  "resolution_note": "Fixed by reverting commit abc123"
}
```

### DELETE /api/v1/anomalies/{anomaly_id}

Delete an anomaly (for false positives).

---

## Metrics

Platform engineering metrics including DORA metrics.

### GET /api/v1/metrics

Get comprehensive metrics dashboard.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| service_id | uuid | Filter by service |
| team_id | uuid | Filter by team |
| time_range | string | `24h`, `7d`, `30d`, `90d` |
| include_trends | bool | Include time series data |

**Response:**
```json
{
  "deployment": {
    "total_deploys": 156,
    "successful_deploys": 148,
    "failed_deploys": 8,
    "deploy_success_rate": 94.9,
    "deploys_today": 12,
    "deploys_this_week": 84,
    "avg_deploys_per_day": 12.0,
    "rollbacks_this_week": 3
  },
  "pipeline": {
    "total_runs": 320,
    "successful_runs": 295,
    "failed_runs": 25,
    "pending_runs": 3,
    "running_now": 2,
    "success_rate": 92.2,
    "avg_duration_seconds": 340,
    "p95_duration_seconds": 720
  },
  "service_health": {
    "total_services": 42,
    "healthy_services": 35,
    "degraded_services": 5,
    "unhealthy_services": 2,
    "provisioning_services": 0,
    "health_score": 85.7
  },
  "dora": {
    "deployment_frequency": "Multiple per day",
    "deployment_frequency_score": 100.0,
    "lead_time_for_changes": "< 1 hour",
    "lead_time_minutes": 45,
    "change_failure_rate": 5.1,
    "mean_time_to_recovery": "< 1 hour",
    "mttr_minutes": 30,
    "overall_score": "Elite"
  },
  "template": {
    "total_templates": 12,
    "active_templates": 10,
    "most_popular": "Python FastAPI",
    "adoption_rate": 92.5,
    "services_without_template": 3
  },
  "anomaly": {
    "total_anomalies": 25,
    "active_anomalies": 5,
    "critical_anomalies": 1,
    "warning_anomalies": 4,
    "resolved_today": 3,
    "avg_resolution_time_hours": 2.5
  },
  "team": {
    "total_teams": 8,
    "active_teams": 7,
    "services_per_team_avg": 5.25,
    "most_active_team": "Platform Team"
  },
  "deploy_trend": {
    "name": "Deployments",
    "data": [
      {"timestamp": "2025-01-06T00:00:00Z", "value": 10, "label": "Mon"},
      {"timestamp": "2025-01-07T00:00:00Z", "value": 12, "label": "Tue"}
    ],
    "unit": "deploys"
  },
  "generated_at": "2025-01-12T10:30:00Z",
  "data_freshness": "real-time"
}
```

### GET /api/v1/metrics/dora

Get DORA metrics only.

**Response:**
```json
{
  "deployment_frequency": "Multiple per day",
  "deployment_frequency_score": 100.0,
  "lead_time_for_changes": "< 1 hour",
  "lead_time_minutes": 45,
  "change_failure_rate": 5.1,
  "mean_time_to_recovery": "< 1 hour",
  "mttr_minutes": 30,
  "overall_score": "Elite"
}
```

### GET /api/v1/metrics/health

Get service health metrics.

### GET /api/v1/metrics/deployment

Get deployment metrics.

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource with ID 'uuid' not found"
}
```

### 409 Conflict
```json
{
  "detail": "Resource already exists"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

> **Status: Planned** - Rate limiting is not yet implemented.

When implemented, the following limits will apply:

| Endpoint | Rate Limit |
|----------|------------|
| GET endpoints | 100 req/min |
| POST/PUT/DELETE | 50 req/min |
| /health | Unlimited |

---

## Webhooks (Coming Soon)

ForgeWorks will support webhooks for:
- Service status changes
- Anomaly detection events
- Deployment notifications
- Pipeline status updates

---

## SDK Support

Official SDKs will be available for:
- Python (`forge-works-sdk`)
- TypeScript (`@forge-works/sdk`)
- Go (`github.com/forge-works/sdk-go`)

---

## Changelog

### v0.3.0 (2025-01-12)
- Complete API release with all core endpoints
- Services, Templates, Anomalies, Metrics endpoints
- DORA metrics support
- OpenAPI 3.0 documentation
- Mock/Live adapter support for GitHub and ArgoCD
