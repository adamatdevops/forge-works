#!/usr/bin/env bash
# diff-iam.sh — verify infra/iam/ matches live AWS IAM state.
#
# For every trust policy and managed policy under this directory, fetch the
# current document from AWS and diff it against the committed JSON. Exits
# non-zero on any drift; clean exit means repo is reproducible from cluster.
#
# Usage:  AWS_PROFILE=fw-admin ./infra/iam/scripts/diff-iam.sh
# Reqs:   awscli, jq, diff
#
# This script does NOT mutate anything in AWS. Read-only.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2; exit 2
fi
if [[ -z "${AWS_PROFILE:-}" ]]; then
  echo "AWS_PROFILE must be set (e.g., fw-admin)" >&2; exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TRUST_DIR="${REPO_ROOT}/iam/trust-policies"
POLICY_DIR="${REPO_ROOT}/iam/policies"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

drift_count=0

# Trust-policy filenames are {role-name}-trust.json
echo "==> Trust policies"
for f in "${TRUST_DIR}"/*.json; do
  name="$(basename "${f}" -trust.json)"
  live="$(aws iam get-role --role-name "${name}" \
    --query 'Role.AssumeRolePolicyDocument' --output json 2>/dev/null || echo '__MISSING__')"
  if [[ "${live}" == "__MISSING__" ]]; then
    echo "  MISSING in AWS: role=${name}"; drift_count=$((drift_count+1)); continue
  fi
  if ! diff -u <(jq -S . "${f}") <(echo "${live}" | jq -S .) > /dev/null; then
    echo "  DRIFT: ${name}"
    diff -u <(jq -S . "${f}") <(echo "${live}" | jq -S .) || true
    drift_count=$((drift_count+1))
  else
    echo "  OK    ${name}"
  fi
done

# Managed-policy filenames don't have a uniform suffix; AWS policy name is the
# bare basename minus .json (e.g. fw-engine-normalizer-s3-access.json → fw-engine-normalizer-s3-access).
# Legacy file fw-engine-s3-policy.json maps to AWS policy fw-engine-s3-access — handle the suffix mismatch
# by trying both: (1) basename-as-is, (2) basename with `-policy` swapped to `-access`.
echo "==> Managed policies"
for f in "${POLICY_DIR}"/*.json; do
  base="$(basename "${f}" .json)"
  for candidate in "${base}" "${base/-policy/-access}"; do
    arn="arn:aws:iam::${ACCOUNT_ID}:policy/${candidate}"
    if aws iam get-policy --policy-arn "${arn}" >/dev/null 2>&1; then
      version="$(aws iam get-policy --policy-arn "${arn}" --query 'Policy.DefaultVersionId' --output text)"
      live="$(aws iam get-policy-version --policy-arn "${arn}" --version-id "${version}" \
        --query 'PolicyVersion.Document' --output json)"
      if ! diff -u <(jq -S . "${f}") <(echo "${live}" | jq -S .) > /dev/null; then
        echo "  DRIFT: ${candidate}"
        diff -u <(jq -S . "${f}") <(echo "${live}" | jq -S .) || true
        drift_count=$((drift_count+1))
      else
        echo "  OK    ${candidate}"
      fi
      continue 2  # next file
    fi
  done
  echo "  MISSING in AWS: policy=${base} (tried ${base} and ${base/-policy/-access})"
  drift_count=$((drift_count+1))
done

echo
if [[ ${drift_count} -gt 0 ]]; then
  echo "DRIFT DETECTED: ${drift_count} item(s) differ between repo and AWS." >&2
  exit 1
fi
echo "All IAM artifacts match live AWS state."
