#!/usr/bin/env bash
# ForgeWorks IRSA Setup Script
# Creates IAM roles (fw-admin) and annotates K8s service accounts (fw-infra)
# Split-profile approach: fw-admin for IAM, fw-infra for kubectl
# Usage: ./setup-irsa.sh [--dry-run]
set -euo pipefail

# Disable AWS CLI pager to prevent blocking on output
export AWS_PAGER=""

CLUSTER_NAME="${CLUSTER_NAME:-forge-works-dev}"
REGION="${REGION:-us-east-1}"
IAM_PROFILE="${IAM_PROFILE:-fw-admin}"      # IAM policy/role creation
K8S_PROFILE="${K8S_PROFILE:-fw-infra}"      # kubectl / EKS cluster access

# Auto-detect Account ID and OIDC ID from AWS (no hardcoded secrets)
echo "Detecting AWS Account ID..."
ACCOUNT_ID="${ACCOUNT_ID:-$(aws sts get-caller-identity --profile "${IAM_PROFILE}" --query 'Account' --output text)}"
if [[ -z "${ACCOUNT_ID}" || "${ACCOUNT_ID}" == "None" ]]; then
  echo "ERROR: Could not detect AWS Account ID. Ensure '${IAM_PROFILE}' profile is authenticated."
  exit 1
fi

echo "Detecting OIDC provider for cluster ${CLUSTER_NAME}..."
OIDC_URL="${OIDC_URL:-$(aws eks describe-cluster --name "${CLUSTER_NAME}" --region "${REGION}" --profile "${K8S_PROFILE}" --query 'cluster.identity.oidc.issuer' --output text)}"
if [[ -z "${OIDC_URL}" || "${OIDC_URL}" == "None" ]]; then
  echo "ERROR: Could not detect OIDC URL. Ensure cluster '${CLUSTER_NAME}' exists and '${K8S_PROFILE}' is authenticated."
  exit 1
fi
OIDC_ID="${OIDC_URL##*/}"
OIDC_PROVIDER="oidc.eks.${REGION}.amazonaws.com/id/${OIDC_ID}"
POLICY_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/iam/policies"
TRUST_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/iam/trust-policies"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN MODE ==="
fi

echo "=== ForgeWorks IRSA Setup ==="
echo "Cluster:     ${CLUSTER_NAME}"
echo "Region:      ${REGION}"
echo "Account:     ${ACCOUNT_ID}"
echo "IAM Profile: ${IAM_PROFILE}"
echo "K8s Profile: ${K8S_PROFILE}"
echo "OIDC:        ${OIDC_PROVIDER}"
echo ""

# --- Step 1: Create IAM Policies (if not exists) ---
echo "--- Step 1: Creating IAM Policies ---"

create_policy() {
  local name=$1
  local file=$2
  local arn="arn:aws:iam::${ACCOUNT_ID}:policy/${name}"

  if aws iam get-policy --policy-arn "${arn}" --profile "${IAM_PROFILE}" &>/dev/null; then
    echo "  Policy ${name} already exists"
  else
    if [[ "${DRY_RUN}" == "true" ]]; then
      echo "  [DRY RUN] Would create policy: ${name}"
    else
      aws iam create-policy \
        --policy-name "${name}" \
        --policy-document "file://${file}" \
        --profile "${IAM_PROFILE}" \
        --output text --query 'Policy.Arn'
      echo "  Created policy: ${name}"
    fi
  fi
}

create_policy "fw-engine-s3-access" "${POLICY_DIR}/fw-engine-s3-policy.json"
create_policy "fw-ml-s3-access" "${POLICY_DIR}/fw-ml-s3-policy.json"
create_policy "fw-ml-inference-s3-access" "${POLICY_DIR}/fw-ml-inference-s3-policy.json"

echo ""

# --- Step 2: Create trust policies and IAM roles ---
echo "--- Step 2: Creating IAM Roles ---"

mkdir -p "${TRUST_DIR}"

create_irsa_role() {
  local sa_name=$1
  local namespace=$2
  local policy_name=$3
  local role_name="fw-${namespace}-${sa_name}"
  local policy_arn="arn:aws:iam::${ACCOUNT_ID}:policy/${policy_name}"
  local role_arn="arn:aws:iam::${ACCOUNT_ID}:role/${role_name}"

  echo ""
  echo "  Role: ${role_name} -> SA: ${sa_name} (${namespace})"

  # Generate trust policy for this SA
  local trust_file="${TRUST_DIR}/${role_name}-trust.json"
  cat > "${trust_file}" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER}:aud": "sts.amazonaws.com",
          "${OIDC_PROVIDER}:sub": "system:serviceaccount:${namespace}:${sa_name}"
        }
      }
    }
  ]
}
EOF
  echo "    Trust policy: ${trust_file}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "    [DRY RUN] Would create role: ${role_name}"
    echo "    [DRY RUN] Would attach policy: ${policy_name}"
    return
  fi

  # Create IAM role (or skip if exists)
  if aws iam get-role --role-name "${role_name}" --profile "${IAM_PROFILE}" &>/dev/null; then
    echo "    Role ${role_name} already exists, updating trust policy..."
    aws iam update-assume-role-policy \
      --role-name "${role_name}" \
      --policy-document "file://${trust_file}" \
      --profile "${IAM_PROFILE}"
  else
    aws iam create-role \
      --role-name "${role_name}" \
      --assume-role-policy-document "file://${trust_file}" \
      --tags Key=forge-works,Value=irsa Key=namespace,Value="${namespace}" Key=service-account,Value="${sa_name}" \
      --profile "${IAM_PROFILE}" \
      --output text --query 'Role.Arn'
    echo "    Created role: ${role_name}"
  fi

  # Attach S3 policy to role
  aws iam attach-role-policy \
    --role-name "${role_name}" \
    --policy-arn "${policy_arn}" \
    --profile "${IAM_PROFILE}"
  echo "    Attached policy: ${policy_name}"
}

create_irsa_role "flink-sa" "forge-engine" "fw-engine-s3-access"
create_irsa_role "airflow-sa" "forge-engine" "fw-engine-s3-access"
create_irsa_role "ml-runner-sa" "forge-ml" "fw-ml-s3-access"
create_irsa_role "ml-inference-sa" "forge-ml" "fw-ml-inference-s3-access"

echo ""

# --- Step 3: Annotate K8s service accounts (uses fw-infra for kubectl) ---
echo "--- Step 3: Annotating K8s Service Accounts ---"

annotate_sa() {
  local sa_name=$1
  local namespace=$2
  local role_name="fw-${namespace}-${sa_name}"
  local role_arn="arn:aws:iam::${ACCOUNT_ID}:role/${role_name}"

  echo ""
  echo "  SA: ${sa_name} (${namespace}) -> ${role_arn}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "    [DRY RUN] Would annotate SA with eks.amazonaws.com/role-arn"
    return
  fi

  kubectl annotate serviceaccount "${sa_name}" \
    --namespace "${namespace}" \
    --overwrite \
    eks.amazonaws.com/role-arn="${role_arn}"
  echo "    Annotated successfully"
}

annotate_sa "flink-sa" "forge-engine"
annotate_sa "airflow-sa" "forge-engine"
annotate_sa "ml-runner-sa" "forge-ml"
annotate_sa "ml-inference-sa" "forge-ml"

echo ""
echo "=== IRSA Setup Complete ==="
echo ""
echo "Verify annotations:"
echo "  kubectl get sa flink-sa -n forge-engine -o jsonpath='{.metadata.annotations}'"
echo "  kubectl get sa airflow-sa -n forge-engine -o jsonpath='{.metadata.annotations}'"
echo "  kubectl get sa ml-runner-sa -n forge-ml -o jsonpath='{.metadata.annotations}'"
echo "  kubectl get sa ml-inference-sa -n forge-ml -o jsonpath='{.metadata.annotations}'"
echo ""
echo "Verify IAM roles:"
echo "  aws iam list-roles --profile ${IAM_PROFILE} --query 'Roles[?starts_with(RoleName, \`fw-\`)].RoleName' --output table"
