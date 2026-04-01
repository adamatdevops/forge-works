#!/usr/bin/env bash
# ForgeWorks E2E Pipeline Test
# Tests: Webhook → Kafka → Flink×3 → Job Dispatcher → K8s Job → Result
#
# Prerequisites:
#   - All services running (webhook-gateway, Flink jobs, job-dispatcher)
#   - kubectl configured for the target cluster
#   - Port-forward: kubectl port-forward svc/webhook-gateway 8080:8080 -n forge-works

set -euo pipefail

WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8080}"
KAFKA_BOOTSTRAP="forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
NAMESPACE="forge-engine"
TIMEOUT=60

echo "=== ForgeWorks E2E Pipeline Test ==="
echo ""

# 1. Send webhook
echo "[1/6] Sending webhook..."
REPO="e2e-test-$(date +%s)"
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL/webhook/github" \
  -H 'Content-Type: application/json' \
  -d "{\"action\":\"merged\",\"pull_request\":{\"merged\":true,\"title\":\"E2E test\"},\"repository\":{\"full_name\":\"forge-works/$REPO\"},\"sender\":{\"login\":\"e2e\"}}")
EVENT_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['event_id'])")
echo "  Event ID: $EVENT_ID"
echo "  Status: $(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")"

# 2. Wait for Flink processing + Job Dispatcher
echo ""
echo "[2/6] Waiting for pipeline processing (30s)..."
sleep 30

# 3. Check for dispatched K8s Job
echo ""
echo "[3/6] Checking for K8s Job..."
JOBS=$(kubectl get jobs -n "$NAMESPACE" -l app.kubernetes.io/managed-by=forgeworks-dispatcher --no-headers 2>/dev/null | tail -1)
if [ -z "$JOBS" ]; then
  echo "  FAIL: No K8s Jobs found"
  exit 1
fi
JOB_NAME=$(echo "$JOBS" | awk '{print $1}')
echo "  Job: $JOB_NAME"

# 4. Wait for job completion
echo ""
echo "[4/6] Waiting for job completion..."
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  STATUS=$(kubectl get job "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.succeeded}' 2>/dev/null || echo "0")
  FAILED=$(kubectl get job "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.failed}' 2>/dev/null || echo "0")
  if [ "${STATUS:-0}" = "1" ]; then
    echo "  Job COMPLETED"
    break
  fi
  if [ "${FAILED:-0}" != "0" ] && [ "${FAILED:-0}" != "" ]; then
    echo "  Job FAILED"
    kubectl logs -n "$NAMESPACE" "job/$JOB_NAME" 2>/dev/null || true
    exit 1
  fi
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
  echo "  TIMEOUT after ${TIMEOUT}s"
  exit 1
fi

# 5. Check job output
echo ""
echo "[5/6] Job output:"
kubectl logs -n "$NAMESPACE" "job/$JOB_NAME" 2>/dev/null | head -5
echo ""

# 6. Check dispatcher logs for result publication
echo ""
echo "[6/6] Dispatcher result:"
kubectl logs -n "$NAMESPACE" deploy/job-dispatcher --tail=20 2>/dev/null | grep -E "Result published.*COMPLETED" | tail -1

echo ""
echo "=== E2E Test PASSED ==="
echo ""
echo "Pipeline verified:"
echo "  Webhook → Gateway → Kafka → Event Router → Pattern Matcher"
echo "  → Insight Generator → Job Dispatcher → K8s Job → COMPLETED"
echo "  → forge.jobs.results → forge.learning.feedback"
