---
name: error-codes-audit
description: Audit FW-* error codes across all services for consistency, duplicates, and missing codes. Use to ensure error taxonomy is maintained as services evolve.
disable-model-invocation: true
allowed-tools: Grep Glob Read
---

Audit ForgeWorks error codes (FW-*) across all services.

## Scan All Services

### 1. Find all FW-* error codes in Python services
```
Grep for pattern: FW-[A-Z]{2}-[A-Z]{3,}-\d{3}
Paths: src/webhook-gateway/, src/job-dispatcher/
```

### 2. Find all FW-* error codes in Java services
```
Grep for pattern: FW-[A-Z]{2}-[A-Z]{3,}-\d{3}
Paths: src/flink-jobs/
```

### 3. Find documented error codes in roadmap/action plans
```
Grep for pattern: FW-
Paths: roadmap/
```

## Validation Rules

### A. Namespace Convention
Error codes follow: `FW-{SERVICE}-{CATEGORY}-{NUMBER}`

| Prefix | Service |
|--------|---------|
| FW-IN- | Webhook Gateway (Ingestion) |
| FW-FL- | Flink jobs |
| FW-KF- | Kafka operations |
| FW-ML- | ML/Model operations |
| FW-TR- | Training pipeline |
| FW-AD- | Adapter/Dispatcher |
| FW-DP- | Dispatcher routing |
| FW-E2E- | End-to-end pipeline |
| FW-AF- | Airflow |
| FW-REG- | Model registry |
| FW-PT- | Pattern matching |

### B. Check for:
1. **Duplicates**: Same code used with different meanings
2. **Gaps**: Sequential gaps in numbering
3. **Orphans**: Codes in docs but not in code (or vice versa)
4. **Inconsistent format**: Codes that don't match the convention

## Report Format

| Code | Location | Description | Status |
|------|----------|-------------|--------|
| FW-IN-AUTH-001 | webhooks.py:L42 | Auth failed | OK |
| FW-IN-AUTH-002 | webhooks.py:L55 | Signature mismatch | OK |
| ... | ... | ... | ... |

Summary:
- Total codes found: N
- Duplicates: N
- Orphans: N
- Recommendations: ...
