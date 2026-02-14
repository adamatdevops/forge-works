# ForgeWorks IRSA (IAM Roles for Service Accounts)

IRSA allows Kubernetes pods to assume IAM roles for AWS API access without storing credentials.

## Architecture

```
Pod (SA: flink-sa) --> OIDC Provider --> IAM Role --> S3 Buckets
```

## IAM Policies

| Policy | Buckets | Access | Used By |
|--------|---------|--------|---------|
| `fw-engine-s3-access` | `fw-state-dev`, `fw-logs-dev` | Read/Write | flink-sa, airflow-sa |
| `fw-ml-s3-access` | `fw-models-dev`, `fw-logs-dev` | Read/Write | ml-runner-sa |
| `fw-ml-inference-s3-access` | `fw-models-dev` | Read-Only | ml-inference-sa |

## Service Account Mappings

| Service Account | Namespace | IAM Policy | S3 Access |
|----------------|-----------|------------|-----------|
| `flink-sa` | forge-engine | fw-engine-s3-access | State + Logs (RW) |
| `airflow-sa` | forge-engine | fw-engine-s3-access | State + Logs (RW) |
| `ml-runner-sa` | forge-ml | fw-ml-s3-access | Models + Logs (RW) |
| `ml-inference-sa` | forge-ml | fw-ml-inference-s3-access | Models (RO) |

## S3 Buckets

| Bucket | Purpose | Versioning |
|--------|---------|------------|
| `fw-state-dev` | Flink checkpoints, savepoints, HA state | Enabled |
| `fw-models-dev` | ML model artifacts registry | - |
| `fw-logs-dev` | Application and pipeline logs | - |

## Setup

Run: `./setup-irsa.sh`

## Verification

```bash
# Check SA annotations
kubectl get sa flink-sa -n forge-engine -o yaml | grep eks.amazonaws.com

# Test S3 access from a pod
kubectl run s3-test --rm -it --image=amazon/aws-cli \
  --serviceaccount=flink-sa -n forge-engine \
  -- s3 ls s3://fw-state-dev/
```
