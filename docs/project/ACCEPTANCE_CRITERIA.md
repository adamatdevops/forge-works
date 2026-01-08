# Acceptance Criteria

## Overview

This document defines the acceptance criteria for ForgeWorks features. Each criterion follows the Given-When-Then format for testability.

## Phase 1: Foundation

### AC-001: Service Catalog API

**Feature:** Service CRUD Operations

```gherkin
Given the Service Catalog API is running
When a user creates a service with valid data
Then the service is persisted to the database
And a unique ID and slug are generated
And the service appears in the catalog listing

Given a service exists in the catalog
When a user updates the service metadata
Then the changes are persisted
And the updated_at timestamp is refreshed

Given a service exists in the catalog
When a user deletes the service
Then the service is removed from the database
And related anomalies are cleaned up
```

**Status:** ✅ Implemented

### AC-002: Template API

**Feature:** Template Listing and Recommendations

```gherkin
Given templates are configured in the system
When a user requests template recommendations
And provides workload_type, language, and requirements
Then relevant templates are returned
And they are scored based on match quality
And the response explains why each template matches

Given a template exists
When a user views template details
Then all configuration options are displayed
And included capabilities are listed
And example usage is provided
```

**Status:** ✅ Implemented

### AC-003: Health Endpoints

**Feature:** System Health Monitoring

```gherkin
Given the application is running
When a user requests /health
Then a 200 response is returned
And basic status information is included

Given the application is running
When a user requests /health/detailed
Then component health status is returned
And adapter connectivity is verified
And overall system status is computed
```

**Status:** ✅ Implemented

### AC-004: Mock Adapters

**Feature:** GitHub and ArgoCD Mock Integration

```gherkin
Given the GitHub adapter is in mock mode
When repository operations are requested
Then realistic mock data is returned
And the response structure matches real API

Given the ArgoCD adapter is in mock mode
When application sync is triggered
Then the operation completes successfully
And application status is updated
```

**Status:** ✅ Implemented

## Phase 2: Integration

### AC-005: Frontend Dashboard

**Feature:** Service Catalog UI

```gherkin
Given the dashboard is loaded
When a user views the service catalog
Then all services are displayed in a table
And filtering by status/team/tier is available
And clicking a service shows details

Given the dashboard is loaded
When a user creates a new service
Then a guided form is presented
And template recommendations are shown
And validation errors are displayed inline
```

**Status:** 🔄 Planned

### AC-006: Anomaly Detection

**Feature:** Deployment Pattern Analysis

```gherkin
Given services have deployment history
When the anomaly detector runs
Then high deploy frequencies are flagged
And consecutive rollbacks are detected
And stale pipelines are identified
And anomalies appear in the dashboard
```

**Status:** 🔄 Planned

## Phase 3: Intelligence

### AC-007: ML Recommendations

**Feature:** Intelligent Template Matching

```gherkin
Given historical service data exists
When the ML model is trained
Then template recommendations improve
And prediction confidence is tracked
And model performance is monitored
```

**Status:** 📋 Future

## Verification Matrix

| ID | Feature | Unit Tests | Integration Tests | E2E Tests |
|----|---------|------------|-------------------|-----------|
| AC-001 | Service CRUD | ✅ | ✅ | 🔄 |
| AC-002 | Templates | ✅ | ✅ | 🔄 |
| AC-003 | Health | ✅ | ✅ | 🔄 |
| AC-004 | Adapters | ✅ | - | - |
| AC-005 | Dashboard | 🔄 | 🔄 | 🔄 |
| AC-006 | Anomalies | 🔄 | 🔄 | 🔄 |
| AC-007 | ML | 📋 | 📋 | 📋 |

**Legend:** ✅ Complete | 🔄 In Progress/Planned | 📋 Future | - N/A
