#!/usr/bin/env bash
# ForgeWorks Secrets Creation Script
# Run this script to create all required secrets
# Usage: ./create-secrets.sh [--dry-run]
set -euo pipefail

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN="--dry-run=client -o yaml"
  echo "=== DRY RUN MODE ==="
fi

# Generate random passwords if not set
POSTGRES_PASSWORD="${FORGE_POSTGRES_PASSWORD:-$(openssl rand -base64 24)}"
REDIS_PASSWORD="${FORGE_REDIS_PASSWORD:-$(openssl rand -base64 24)}"
APP_SECRET_KEY="${FORGE_APP_SECRET_KEY:-$(openssl rand -base64 32)}"
JWT_SECRET="${FORGE_JWT_SECRET:-$(openssl rand -base64 32)}"

echo "=== Creating ForgeWorks Secrets ==="

# --- forge-engine namespace ---
echo ""
echo "--- forge-engine namespace ---"

kubectl create secret generic forge-postgres-credentials \
  --namespace forge-engine \
  --from-literal=username=forgeworks \
  --from-literal=password="${POSTGRES_PASSWORD}" \
  --from-literal=host=forge-postgres.forge-engine.svc \
  --from-literal=port=5432 \
  --from-literal=database=forgeworks \
  $DRY_RUN || echo "  (already exists)"

kubectl create secret generic forge-redis-credentials \
  --namespace forge-engine \
  --from-literal=host=forge-redis.forge-engine.svc \
  --from-literal=port=6379 \
  --from-literal=password="${REDIS_PASSWORD}" \
  $DRY_RUN || echo "  (already exists)"

# --- forge-works namespace ---
echo ""
echo "--- forge-works namespace ---"

kubectl create secret generic forge-postgres-credentials \
  --namespace forge-works \
  --from-literal=username=forgeworks \
  --from-literal=password="${POSTGRES_PASSWORD}" \
  --from-literal=host=forge-postgres.forge-engine.svc \
  --from-literal=port=5432 \
  --from-literal=database=forgeworks \
  $DRY_RUN || echo "  (already exists)"

kubectl create secret generic forge-redis-credentials \
  --namespace forge-works \
  --from-literal=host=forge-redis.forge-engine.svc \
  --from-literal=port=6379 \
  --from-literal=password="${REDIS_PASSWORD}" \
  $DRY_RUN || echo "  (already exists)"

kubectl create secret generic forge-app-config \
  --namespace forge-works \
  --from-literal=secret-key="${APP_SECRET_KEY}" \
  --from-literal=jwt-secret="${JWT_SECRET}" \
  $DRY_RUN || echo "  (already exists)"

# --- forge-ml namespace ---
echo ""
echo "--- forge-ml namespace ---"

kubectl create secret generic forge-ml-config \
  --namespace forge-ml \
  --from-literal=model-registry-url=s3://fw-models-dev/ \
  $DRY_RUN || echo "  (already exists)"

echo ""
echo "=== Secrets Created ==="
echo ""
echo "IMPORTANT: Save these credentials securely!"
echo "  PostgreSQL password: ${POSTGRES_PASSWORD}"
echo "  Redis password:      ${REDIS_PASSWORD}"
echo ""
echo "Verify: kubectl get secrets -A -l app.kubernetes.io/part-of=forgeworks"
