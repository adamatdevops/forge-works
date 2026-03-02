#!/usr/bin/env bash
# ForgeWorks Infrastructure Validation — Sprint I-8
# Usage: bash infra/scripts/validate-infrastructure.sh
# Requires: kubectl configured with cluster access
# Read-only — no destructive actions

set -uo pipefail

PASS=0 FAIL=0 WARN=0

pass() { echo "  ✅ $1"; ((PASS++)); }
fail() { echo "  ❌ $1"; ((FAIL++)); }
warn() { echo "  ⚠️  $1"; ((WARN++)); }

section() { printf '\n══════ %s ══════\n' "$1"; }

check() {
  local label="$1"; shift
  if eval "$@" &>/dev/null; then pass "$label"; else fail "$label"; fi
}

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     ForgeWorks Infrastructure Validation — Sprint I-8   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""

# ── 1. Cluster Connectivity ──
section "Cluster Connectivity"
check "kubectl can reach API server" "kubectl cluster-info"
check "Nodes are Ready" "kubectl get nodes --no-headers | grep -v NotReady | grep Ready"

NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
echo "  ℹ️  Node count: ${NODE_COUNT}"

# ── 2. Namespaces ──
section "Namespaces"
for NS in forge-engine forge-works forge-ml; do
  check "Namespace ${NS} exists" "kubectl get ns ${NS}"
done

check "forge-engine PSS: baseline" \
  "kubectl get ns forge-engine -o jsonpath='{.metadata.labels.pod-security\\.kubernetes\\.io/enforce}' | grep -q baseline"
check "forge-works PSS: restricted" \
  "kubectl get ns forge-works -o jsonpath='{.metadata.labels.pod-security\\.kubernetes\\.io/enforce}' | grep -q restricted"
check "forge-ml PSS: baseline" \
  "kubectl get ns forge-ml -o jsonpath='{.metadata.labels.pod-security\\.kubernetes\\.io/enforce}' | grep -q baseline"

# ── 3. Service Accounts ──
section "Service Accounts"
for SA in kafka-sa flink-sa airflow-sa; do
  check "SA ${SA} in forge-engine" "kubectl get sa ${SA} -n forge-engine"
done
for SA in backend-sa frontend-sa webhook-gateway-sa; do
  check "SA ${SA} in forge-works" "kubectl get sa ${SA} -n forge-works"
done
for SA in ml-inference-sa ml-runner-sa; do
  check "SA ${SA} in forge-ml" "kubectl get sa ${SA} -n forge-ml"
done

# ── 4. Operators ──
section "Operators"
check "Strimzi operator running" \
  "kubectl get pods -l strimzi.io/kind=cluster-operator -n forge-engine --field-selector=status.phase=Running --no-headers | grep -q ."
check "Flink operator running" \
  "kubectl get pods -l app.kubernetes.io/name=flink-kubernetes-operator -n forge-engine --field-selector=status.phase=Running --no-headers | grep -q ."
check "Cert-Manager controller running" \
  "kubectl get pods -l app.kubernetes.io/component=controller -n cert-manager --field-selector=status.phase=Running --no-headers | grep -q ."
check "Cert-Manager webhook running" \
  "kubectl get pods -l app.kubernetes.io/component=webhook -n cert-manager --field-selector=status.phase=Running --no-headers | grep -q ."

# ── 5. Kafka Cluster ──
section "Kafka Cluster"
check "Kafka CR exists" "kubectl get kafka forge-kafka -n forge-engine"
check "Kafka CR Ready" \
  "kubectl get kafka forge-kafka -n forge-engine -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}' | grep -q True"

TOPIC_COUNT=$(kubectl get kafkatopic -n forge-engine --no-headers 2>/dev/null | wc -l | tr -d ' ')
echo "  ℹ️  Kafka topics: ${TOPIC_COUNT}"
check "At least 10 Kafka topics exist" "[ ${TOPIC_COUNT} -ge 10 ]"

READY_TOPICS=$(kubectl get kafkatopic -n forge-engine -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' 2>/dev/null | grep -c True || echo 0)
check "All topics Ready" "[ ${READY_TOPICS} -ge 10 ]"

# ── 6. Flink Cluster ──
section "Flink Cluster"
check "FlinkDeployment exists" "kubectl get flinkdeployment forge-flink -n forge-engine"
check "FlinkDeployment STABLE" \
  "kubectl get flinkdeployment forge-flink -n forge-engine -o jsonpath='{.status.lifecycleState}' | grep -q STABLE"

# ── 7. Redis ──
section "Redis"
check "Redis pod running" \
  "kubectl get pods -l app.kubernetes.io/name=redis -n forge-engine --field-selector=status.phase=Running --no-headers | grep -q ."

REDIS_PASS=$(kubectl get secret forge-redis-credentials -n forge-engine -o jsonpath='{.data.password}' 2>/dev/null | base64 -d 2>/dev/null)
check "Redis PING → PONG" \
  "kubectl exec -n forge-engine forge-redis-master-0 -- redis-cli -a '${REDIS_PASS}' PING 2>/dev/null | grep -q PONG"

# ── 8. PostgreSQL ──
section "PostgreSQL"
check "PostgreSQL pod running" \
  "kubectl get pods -l app.kubernetes.io/name=postgresql -n forge-engine --field-selector=status.phase=Running --no-headers | grep -q ."

PG_PASS=$(kubectl get secret forge-postgres-credentials -n forge-engine -o jsonpath='{.data.password}' 2>/dev/null | base64 -d 2>/dev/null)
check "PostgreSQL SELECT 1" \
  "kubectl exec -n forge-engine forge-postgres-postgresql-0 -- env PGPASSWORD='${PG_PASS}' psql -U forgeworks -d forgeworks -tAc 'SELECT 1' 2>/dev/null | grep -q 1"

# ── 9. Secrets ──
section "Secrets"
for SECRET in forge-postgres-credentials forge-redis-credentials; do
  check "Secret ${SECRET} in forge-engine" "kubectl get secret ${SECRET} -n forge-engine"
done
for SECRET in forge-postgres-credentials forge-redis-credentials forge-app-config; do
  check "Secret ${SECRET} in forge-works" "kubectl get secret ${SECRET} -n forge-works"
done
check "Secret forge-ml-config in forge-ml" "kubectl get secret forge-ml-config -n forge-ml"

# ── 10. IRSA Annotations ──
section "IRSA Annotations"
for SA_NS in "flink-sa:forge-engine" "airflow-sa:forge-engine" "ml-runner-sa:forge-ml" "ml-inference-sa:forge-ml"; do
  SA="${SA_NS%%:*}"
  NS="${SA_NS##*:}"
  check "IRSA annotation on ${SA} (${NS})" \
    "kubectl get sa ${SA} -n ${NS} -o jsonpath='{.metadata.annotations.eks\\.amazonaws\\.com/role-arn}' | grep -q arn:aws:iam"
done

# ── 11. Persistent Volume Claims ──
section "Persistent Volume Claims"
PVC_TOTAL=$(kubectl get pvc -n forge-engine --no-headers 2>/dev/null | wc -l | tr -d ' ')
PVC_BOUND=$(kubectl get pvc -n forge-engine --no-headers 2>/dev/null | grep -c Bound || echo 0)
echo "  ℹ️  PVCs: ${PVC_BOUND}/${PVC_TOTAL} Bound"
check "All PVCs Bound" "[ ${PVC_BOUND} -eq ${PVC_TOTAL} ] && [ ${PVC_TOTAL} -gt 0 ]"

kubectl get pvc -n forge-engine --no-headers 2>/dev/null | while read -r line; do
  PVC_NAME=$(echo "$line" | awk '{print $1}')
  PVC_STATUS=$(echo "$line" | awk '{print $2}')
  PVC_SIZE=$(echo "$line" | awk '{print $4}')
  echo "  ℹ️  ${PVC_NAME}: ${PVC_STATUS} (${PVC_SIZE})"
done

# ── 12. Envoy Gateway ──
section "Envoy Gateway"
check "Envoy Gateway controller running" \
  "kubectl get pods -l control-plane=envoy-gateway -n envoy-gateway-system --field-selector=status.phase=Running --no-headers | grep -q ."
check "GatewayClass 'eg' exists" "kubectl get gatewayclass eg"
check "GatewayClass Accepted" \
  "kubectl get gatewayclass eg -o jsonpath='{.status.conditions[?(@.type==\"Accepted\")].status}' | grep -q True"

# ── 13. Gateway ──
section "Gateway"
check "Gateway forgeworks-gateway exists" "kubectl get gateway forgeworks-gateway -n envoy-gateway-system"
check "Gateway Programmed: True" \
  "kubectl get gateway forgeworks-gateway -n envoy-gateway-system -o jsonpath='{.status.conditions[?(@.type==\"Programmed\")].status}' | grep -q True"

LB_HOSTNAME=$(kubectl get gateway forgeworks-gateway -n envoy-gateway-system -o jsonpath='{.status.addresses[0].value}' 2>/dev/null)
if [ -n "${LB_HOSTNAME}" ]; then
  pass "LoadBalancer endpoint assigned"
  echo "  ℹ️  LB: ${LB_HOSTNAME}"
else
  fail "LoadBalancer endpoint assigned"
fi

# ── 14. HTTPRoutes ──
section "HTTPRoutes"
for ROUTE in backend-api frontend webhook-gateway; do
  check "HTTPRoute ${ROUTE} exists" "kubectl get httproute ${ROUTE} -n forge-works"
done

ROUTE_COUNT=$(kubectl get httproute -n forge-works --no-headers 2>/dev/null | wc -l | tr -d ' ')
echo "  ℹ️  HTTPRoute count: ${ROUTE_COUNT}"

# ── 15. NetworkPolicies ──
section "NetworkPolicies"
for NS in forge-engine forge-works forge-ml; do
  NP_COUNT=$(kubectl get networkpolicy -n "${NS}" --no-headers 2>/dev/null | wc -l | tr -d ' ')
  echo "  ℹ️  ${NS}: ${NP_COUNT} NetworkPolicies"
  check "NetworkPolicies exist in ${NS}" "[ ${NP_COUNT} -gt 0 ]"
done

check "allow-backend-ingress references envoy-gateway-system" \
  "kubectl get networkpolicy allow-backend-ingress -n forge-works -o yaml | grep -q envoy-gateway-system"

# ── 16. Helm Releases ──
section "Helm Releases"
for RELEASE_NS in "strimzi-kafka-operator:forge-engine" "flink-kubernetes-operator:forge-engine" "forge-redis:forge-engine" "forge-postgres:forge-engine" "envoy-gateway:envoy-gateway-system"; do
  RELEASE="${RELEASE_NS%%:*}"
  NS="${RELEASE_NS##*:}"
  check "Helm release ${RELEASE} deployed" "helm status ${RELEASE} -n ${NS}"
done

# ══════ Summary ══════
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
printf "║  Results: ✅ %-3d passed  ❌ %-3d failed  ⚠️  %-3d warnings ║\n" "$PASS" "$FAIL" "$WARN"
echo "╚══════════════════════════════════════════════════════════╝"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "❌ VALIDATION FAILED — Review failures above before proceeding to Engine Phase 1"
  exit 1
else
  echo ""
  echo "✅ ALL CHECKS PASSED — Infrastructure ready for Engine Phase 1"
  exit 0
fi
