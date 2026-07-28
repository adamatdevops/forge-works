---
name: e2e-test
description: Run the full ForgeWorks E2E pipeline test — Webhook to K8s Job completion. Use to verify the entire pipeline is working after changes or deployments.
disable-model-invocation: true
allowed-tools: Bash(kubectl *) Bash(curl *)
---

Run the ForgeWorks End-to-End Pipeline Test.

## Prerequisites Check

```bash
# Verify core services
kubectl get pods -n forge-works -l app.kubernetes.io/name=webhook-gateway --no-headers
kubectl get flinkdeployments -n forge-engine --no-headers
kubectl get pods -n forge-engine -l app.kubernetes.io/name=job-dispatcher --no-headers
```

## Test Execution

### 1. Start port-forward (if not already running)

```bash
kubectl port-forward svc/webhook-gateway 8080:8080 -n forge-works &
sleep 3
```

### 2. Send test webhook

```bash
REPO="e2e-$(date +%s)"
BEFORE=$(python3 -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).isoformat())")
RESPONSE=$(curl -s -X POST localhost:8080/webhook/github \
  -H 'Content-Type: application/json' \
  -d "{\"action\":\"merged\",\"pull_request\":{\"merged\":true,\"title\":\"E2E test\"},\"repository\":{\"full_name\":\"forge-works/$REPO\"},\"sender\":{\"login\":\"e2e\"}}")
echo "Sent at: $BEFORE"
echo "Response: $RESPONSE"
```

### 3. Wait for pipeline processing (30s)

```bash
sleep 30
```

### 4. Verify Job Dispatcher processed it

```bash
kubectl logs -n forge-engine deploy/job-dispatcher --tail=10 2>&1 | grep -iE "dispatched|Result published|COMPLETED"
```

### 5. Check K8s Job

```bash
kubectl get jobs -n forge-engine -l app.kubernetes.io/managed-by=forgeworks-dispatcher --no-headers | tail -3
```

### 6. Measure latency

Report the time from webhook send to "Result published" log entry.

## Expected Results

- Webhook returns 200 with event_id
- Flink processes through Event Router → Pattern Matcher → Insight Generator
- Job Dispatcher creates K8s Job
- K8s Job completes
- Result published to forge.jobs.results
- Feedback published to forge.learning.feedback
- Target: <10s full E2E (insight <1s + job scheduling ~5s)
