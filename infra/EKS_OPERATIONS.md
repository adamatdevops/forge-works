# EKS Operations Guide

> **Version:** 1.2.0
> **Created:** 2025-02-01
> **Cluster:** forge-works-dev
> **Region:** us-east-1

---

## Quick Reference

| Operation | Command |
|-----------|---------|
| Login to SSO | `aws sso login --sso-session forgeworks` |
| Scale up nodes | See [Scale Up](#scale-up-nodes) |
| Scale down nodes | See [Scale Down](#scale-down-nodes-cost-saving) |
| Delete cluster | See [Delete Cluster](#delete-cluster-full-cost-elimination) |
| Fix kubectl auth | See [Authentication](#authentication-troubleshooting) |

---

## Daily Operations

### Start of Day

```bash
# 1. Login to SSO (tokens expire after 8-12 hours)
aws sso login --sso-session forgeworks

# 2. Verify identity
aws sts get-caller-identity --profile fw-infra

# 3. Check cluster status
kubectl get nodes -o wide
```

---

## Cost Management

### Cluster Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| EKS Control Plane | ~$0.10/hr ($72/mo) | Always running |
| 3x t3.large nodes | ~$0.25/hr ($180/mo) | Can scale to 0 |
| **Total (running)** | **~$0.35/hr (~$8/day)** | |
| **Total (scaled down)** | **~$0.10/hr (~$2.40/day)** | Nodes at 0 |

### Scale Down Nodes (Cost Saving)

Scale nodes to 0 when not working (saves ~$6/day):

```bash
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=0 \
  --profile fw-infra \
  --region us-east-1
```

### Scale Up Nodes

Scale nodes back when ready to work:

```bash
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=2,maxSize=5,desiredSize=3 \
  --profile fw-infra \
  --region us-east-1
```

### Check Scaling Status

```bash
aws eks describe-nodegroup \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --profile fw-infra \
  --region us-east-1 \
  --query 'nodegroup.{Status:status,Desired:scalingConfig.desiredSize,Min:scalingConfig.minSize,Max:scalingConfig.maxSize}'
```

### Delete Cluster (Full Cost Elimination)

**Warning:** This deletes all resources in the cluster.

```bash
eksctl delete cluster \
  --name forge-works-dev \
  --region us-east-1 \
  --profile fw-infra
```

---

## Authentication Troubleshooting

### Issue: "the server has asked for the client to provide credentials"

**Root Cause:** The IAM principal (SSO role) is not mapped in EKS RBAC.

**Solution:** Use the cluster creator profile (fw-infra) for kubectl:

```bash
# Update kubeconfig to use fw-infra
aws eks update-kubeconfig \
  --region us-east-1 \
  --name forge-works-dev \
  --profile fw-infra \
  --alias fw-dev

# Verify
kubectl get nodes
```

### Issue: SSO Token Expired

**Symptoms:**
- `Error when retrieving token from sso: Token has expired`
- kubectl commands fail with auth errors

**Solution:**
```bash
aws sso login --sso-session forgeworks
```

### Granting Access to Other IAM Principals

To grant `fw-deploy` or other roles access to the cluster:

```bash
# 1. Get the role ARN
aws iam list-roles --profile fw-infra \
  --query "Roles[?contains(RoleName, 'fw-deploy')].Arn" \
  --output text

# 2. Create access entry
aws eks create-access-entry \
  --cluster-name forge-works-dev \
  --principal-arn <ROLE-ARN> \
  --profile fw-infra \
  --region us-east-1

# 3. Associate admin policy
aws eks associate-access-policy \
  --cluster-name forge-works-dev \
  --principal-arn <ROLE-ARN> \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --profile fw-infra \
  --region us-east-1
```

---

## Profiles Reference

| Profile | Purpose | Use For |
|---------|---------|---------|
| `fw-infra` | Infrastructure provisioning | EKS creation, scaling, IAM, kubectl (cluster creator) |
| `fw-deploy` | Day-to-day deployments | kubectl (after RBAC mapping), S3, ECR |
| `fw-admin` | IAM Identity Center management | Permission set changes only |

---

## Useful Commands

### Cluster Information

```bash
# Cluster details
aws eks describe-cluster \
  --name forge-works-dev \
  --profile fw-infra \
  --region us-east-1

# Node group details
aws eks describe-nodegroup \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --profile fw-infra \
  --region us-east-1

# List all clusters
aws eks list-clusters --profile fw-infra --region us-east-1
```

### kubectl Shortcuts

```bash
# Nodes with resource usage
kubectl top nodes

# All pods across namespaces
kubectl get pods -A

# Current context
kubectl config current-context

# Switch context
kubectl config use-context fw-dev
```

---

## Storage Configuration

### EBS CSI Driver

The cluster uses the AWS EBS CSI Driver for persistent volumes.

**Installed Components:**
- IAM Role: `AmazonEKS_EBS_CSI_DriverRole`
- Service Account: `ebs-csi-controller-sa` (kube-system)
- Add-on: `aws-ebs-csi-driver`

**Storage Classes:**

| Name | Provisioner | Default | Encryption | Expansion |
|------|-------------|---------|------------|-----------|
| gp2 | kubernetes.io/aws-ebs | No | No | No |
| **gp3** | ebs.csi.aws.com | **Yes** | **Yes** | **Yes** |

**Verify Storage:**
```bash
kubectl get storageclass
kubectl get pv
kubectl get pvc -A
```

---

## IRSA (IAM Roles for Service Accounts)

Pods access S3 via IRSA — no stored credentials needed.

**IAM Policies:**
| Policy | Buckets | Access |
|--------|---------|--------|
| fw-engine-s3-access | fw-state-dev, fw-logs-dev | Read/Write |
| fw-ml-s3-access | fw-models-dev, fw-logs-dev | Read/Write |
| fw-ml-inference-s3-access | fw-models-dev | Read-Only |

**Service Account → IAM Role Mapping:**
| Service Account | Namespace | IAM Role |
|----------------|-----------|----------|
| flink-sa | forge-engine | fw-forge-engine-flink-sa |
| airflow-sa | forge-engine | fw-forge-engine-airflow-sa |
| ml-runner-sa | forge-ml | fw-forge-ml-ml-runner-sa |
| ml-inference-sa | forge-ml | fw-forge-ml-ml-inference-sa |

**OIDC Provider:** `oidc.eks.us-east-1.amazonaws.com/id/39DA4641683A2882E9AE71BFEA689869`

**Setup Script:** `infra/k8s/base/irsa/setup-irsa.sh`
- Uses `fw-admin` for IAM operations, `fw-infra` for kubectl
- Supports `--dry-run` flag

**Test IRSA:**
```bash
kubectl run s3-test --rm -it \
  --image=amazon/aws-cli \
  --overrides='{"spec":{"serviceAccountName":"flink-sa","containers":[{"name":"s3-test","image":"amazon/aws-cli","command":["sh","-c","aws s3 ls s3://fw-state-dev/"]}]}}' \
  -n forge-engine
```

---

## S3 Buckets

| Bucket | Purpose | Versioning |
|--------|---------|------------|
| fw-state-dev | Flink checkpoints, savepoints, HA state | Enabled |
| fw-models-dev | ML model artifacts | - |
| fw-logs-dev | Application and pipeline logs | - |

---

## Redis

**Release:** forge-redis (Helm)
**Chart:** bitnami/redis 25.2.0 (App: 8.6.0)
**Mode:** Standalone
**Service:** `forge-redis-master.forge-engine.svc.cluster.local:6379`
**Auth:** `forge-redis-credentials` secret (key: `password`)

```bash
# Check status
kubectl get pods -n forge-engine -l app.kubernetes.io/name=redis

# PING test
kubectl exec -n forge-engine forge-redis-master-0 -- \
  redis-cli -a "$(kubectl get secret forge-redis-credentials -n forge-engine -o jsonpath='{.data.password}' | base64 -d)" PING

# Helm values used
helm get values forge-redis -n forge-engine
```

---

## PostgreSQL

**Release:** forge-postgres (Helm)
**Chart:** bitnami/postgresql 18.3.0 (App: 18.2)
**Service:** `forge-postgres-postgresql.forge-engine.svc.cluster.local:5432`
**Database:** forgeworks
**User:** forgeworks
**Auth:** `forge-postgres-credentials` secret (key: `password`)

```bash
# Check status
kubectl get pods -n forge-engine -l app.kubernetes.io/name=postgresql

# Connection test
kubectl exec -n forge-engine forge-postgres-postgresql-0 -- \
  env PGPASSWORD="$(kubectl get secret forge-postgres-credentials -n forge-engine -o jsonpath='{.data.password}' | base64 -d)" \
  psql -U forgeworks -d forgeworks -c "SELECT version();"

# Helm values used
helm get values forge-postgres -n forge-engine
```

---

## Lessons Learned

### 1. EKS RBAC vs IAM Permissions

**Issue:** Having IAM permissions (eks:DescribeCluster) doesn't grant Kubernetes RBAC access.

**Solution:** The cluster creator automatically has admin access. Other principals must be explicitly granted access via:
- EKS Access Entries (newer method, recommended)
- aws-auth ConfigMap (legacy method)

### 2. SSO Token Expiration

**Issue:** SSO tokens expire after 8-12 hours, breaking kubectl.

**Solution:** Run `aws sso login --sso-session forgeworks` at the start of each session.

### 3. Use fw-infra for kubectl

**Best Practice:** Use `fw-infra` profile for kubectl commands since it created the cluster and has automatic admin access.

### 4. Split-Profile for IRSA

**Issue:** `fw-infra` has EKS access but not IAM permissions. `fw-admin` has IAM access but not K8s RBAC.

**Solution:** Split operations: `fw-admin` for IAM roles/policies, `fw-infra` (kubectl) for SA annotations. See `setup-irsa.sh`.

### 5. AWS CLI v2 Pager

**Issue:** AWS CLI v2 pipes long output through `less`, blocking scripts.

**Solution:** Add `export AWS_PAGER=""` to scripts or `~/.aws/config`.

### 6. amazon/aws-cli Image Entrypoint

**Issue:** The `amazon/aws-cli` Docker image uses `aws` as entrypoint, so `sh -c` is treated as aws arguments.

**Solution:** Override the container command via `--overrides` with `"command":["sh","-c","..."]`.

### 7. Bitnami Helm Chart Service Account Naming

**Issue:** Setting `master.serviceAccount.create=false` and `master.serviceAccount.name=backend-sa` didn't take effect. StatefulSet looked for a non-existent SA named after the release.

**Solution:** Use top-level `serviceAccount.create=true` and `serviceAccount.name=<name>` for Bitnami charts. Or let the chart create its own SA — fighting chart SA naming conventions isn't worth it.

### 8. Bitnami Redis Architecture Flag

**Issue:** Omitting `--set architecture=standalone` deploys in replication mode, creating replica pods with no master pod.

**Solution:** Always explicitly set `architecture=standalone` for dev environments. The chart defaults to `replication`.

### 9. Strimzi Operator Pod Label

**Issue:** Strimzi operator pod uses `strimzi.io/kind=cluster-operator` label, not `app.kubernetes.io/name=strimzi-cluster-operator`.

**Solution:** Use the correct label for monitoring/validation:
```bash
kubectl get pods -l strimzi.io/kind=cluster-operator --all-namespaces
```

---

*EKS Operations Guide v1.2.0*
*Last Updated: 2026-02-15*
