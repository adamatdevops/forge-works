---
name: scaffold-tests
description: Generate test boilerplate for a ForgeWorks service — unit tests, integration tests, or API tests. Adapts to Python (pytest) or Java (JUnit) based on the target service.
argument-hint: '[service-name: webhook-gateway|job-dispatcher|event-router|pattern-matcher|insight-generator]'
disable-model-invocation: true
allowed-tools: Read Glob Write Bash(python3 *)
---

Scaffold tests for service: **$ARGUMENTS**

## Service Detection

Determine the service type by checking the source directory:

- `src/webhook-gateway/` → Python (pytest + httpx)
- `src/job-dispatcher/` → Python (pytest + httpx)
- `src/flink-jobs/event-router/` → Java (JUnit 5)
- `src/flink-jobs/pattern-matcher/` → Java (JUnit 5)
- `src/flink-jobs/insight-generator/` → Java (JUnit 5)

## Python Test Scaffold (FastAPI services)

### Structure

```
src/$ARGUMENTS/tests/
├── __init__.py
├── conftest.py          # fixtures (mock Kafka, mock K8s)
├── test_health.py       # /health, /ready, /status endpoints
├── test_<core>.py       # core business logic
└── test_integration.py  # integration with Kafka/K8s (mocked)
```

### Approach

1. Read the service's route files and core modules
2. Identify all endpoints and public functions
3. Generate tests covering:
   - Happy path (expected input → expected output)
   - Error cases (invalid input, missing data, service unavailable)
   - Edge cases (empty payload, boundary values, auth failures)
4. Mock external dependencies (Kafka, K8s API, MLflow)
5. Use existing test patterns from `src/webhook-gateway/tests/` as reference

### Reference Pattern

```python
@pytest.mark.asyncio
async def test_endpoint(client, mock_kafka):
    resp = await client.post("/endpoint", json={...})
    assert resp.status_code == 200
```

## Java Test Scaffold (Flink jobs)

### Structure

```
src/flink-jobs/$ARGUMENTS/src/test/java/dev/forgeworks/engine/.../
├── <Job>Test.java           # job pipeline test
├── <Serializer>Test.java    # serialization round-trip
└── <Function>Test.java      # operator unit tests
```

### Approach

1. Read the job's main class and operators
2. Generate tests covering:
   - Serialization round-trip (serialize → deserialize → equals)
   - Operator logic (filter, process function behavior)
   - Edge cases (null fields, empty payloads)
3. Use Flink's `MiniClusterExtension` for integration tests
4. Add JUnit 5 + Flink test dependencies to pom.xml if not present

## Output

- Create all test files
- Run the tests to verify they pass
- Report coverage summary
