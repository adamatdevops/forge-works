# Load Testing Suite

ForgeWorks API load testing using [k6](https://k6.io/).

## Prerequisites

Install k6:

```bash
# macOS
brew install k6

# Docker
docker pull grafana/k6
```

## Test Types

### 1. Baseline Test (`k6-api-baseline.js`)

Standard load test to establish performance baselines.

**Stages:**
- 30s: Warm up to 5 users
- 1m: Ramp up to 10 users
- 2m: Steady state at 10 users
- 30s: Ramp down

**Thresholds:**
- 95th percentile response time < 500ms
- 99th percentile response time < 1000ms
- Error rate < 1%

```bash
# Run baseline test
k6 run tests/load/k6-api-baseline.js

# With custom settings
k6 run --vus 20 --duration 5m tests/load/k6-api-baseline.js
```

### 2. Stress Test (`k6-stress-test.js`)

Tests system behavior under extreme load to find breaking points.

**Stages:**
- Ramps from 10 to 50 VUs over 9 minutes
- Maintains stress load for 3 minutes
- 2 minute recovery period

**Thresholds:**
- 95th percentile response time < 2000ms
- Error rate < 10%

```bash
# Run stress test
k6 run tests/load/k6-stress-test.js

# With custom max VUs
k6 run --env MAX_VUS=100 tests/load/k6-stress-test.js
```

### 3. Spike Test (`k6-spike-test.js`)

Tests system behavior under sudden traffic spikes.

**Stages:**
- Normal load (3 VUs) for 30s
- Sudden spike to 30 VUs over 10s
- Maintain spike for 1 minute
- Scale down to 3 VUs over 10s
- Recovery period

**Thresholds:**
- 95th percentile response time < 3000ms
- Error rate < 20%

```bash
# Run spike test
k6 run tests/load/k6-spike-test.js

# With custom spike size
k6 run --env SPIKE_VUS=100 tests/load/k6-spike-test.js
```

## Running Against Different Environments

```bash
# Local development
k6 run --env BASE_URL=http://localhost:8000 tests/load/k6-api-baseline.js

# Staging
k6 run --env BASE_URL=https://staging-api.example.com tests/load/k6-api-baseline.js

# Production (be careful!)
k6 run --env BASE_URL=https://api.example.com tests/load/k6-api-baseline.js
```

## Docker Usage

```bash
# Run baseline test with Docker
docker run -i grafana/k6 run - < tests/load/k6-api-baseline.js

# With environment variables
docker run -i -e BASE_URL=http://host.docker.internal:8000 \
  grafana/k6 run - < tests/load/k6-api-baseline.js
```

## Output Formats

```bash
# JSON output
k6 run --out json=results.json tests/load/k6-api-baseline.js

# InfluxDB (for Grafana dashboards)
k6 run --out influxdb=http://localhost:8086/k6 tests/load/k6-api-baseline.js

# Cloud (k6 Cloud)
k6 cloud tests/load/k6-api-baseline.js
```

## Endpoints Tested

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed component health |
| `/api/v1/services` | GET | List all services |
| `/api/v1/services/stats` | GET | Service statistics |
| `/api/v1/templates` | GET | List all templates |
| `/api/v1/ml/recommend` | POST | ML template recommendations |
| `/api/v1/ml/health` | GET | ML service health |
| `/api/v1/metrics` | GET | Metrics dashboard |
| `/api/v1/metrics/dora` | GET | DORA metrics |
| `/api/v1/anomalies` | GET | List anomalies |
| `/api/v1/anomalies/stats` | GET | Anomaly statistics |

## Performance Baselines

Expected baseline performance (local development):

| Metric | Target | Description |
|--------|--------|-------------|
| `/health` p95 | < 100ms | Health check |
| `/api/v1/services` p95 | < 300ms | Services list |
| `/api/v1/templates` p95 | < 300ms | Templates list |
| `/api/v1/ml/recommend` p95 | < 1000ms | ML recommendations |
| Error rate | < 1% | All endpoints |

## Interpreting Results

k6 outputs include:

- **VUs**: Virtual users active during the test
- **http_req_duration**: Response time statistics
  - `avg`: Average response time
  - `min/max`: Min/max response times
  - `p(95)`: 95th percentile
  - `p(99)`: 99th percentile
- **http_reqs**: Total requests made
- **http_req_failed**: Failed requests rate
- **iterations**: Completed test iterations

### Success Criteria

✅ All thresholds pass (green output)
❌ Any threshold fails (red output with exit code 99)

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Run load tests
  run: |
    docker run -i grafana/k6 run - < tests/load/k6-api-baseline.js
  env:
    BASE_URL: ${{ secrets.STAGING_API_URL }}
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Ensure the API is running
   - Check BASE_URL is correct

2. **High error rates**
   - Check API logs for errors
   - Reduce VUs if server is overloaded

3. **Threshold failures**
   - May indicate performance regression
   - Check for database issues
   - Review recent code changes
