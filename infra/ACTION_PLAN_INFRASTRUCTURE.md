# Action Plan: ForgeWorks Infrastructure Deployment

> **Status:** 📋 READY TO EXECUTE
> **Version:** 2.1.0
> **Duration:** 5-7 Days
> **Last Updated:** 2025-01-26
> **Philosophy:** "Bring Your Own Stack"
> **Prerequisite:** [PREREQUISITES.md](PREREQUISITES.md)
> **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Core Principle

ForgeWorks deploys **onto the customer's existing Kubernetes cluster**. This action plan assumes:
- Customer provides a Kubernetes cluster (EKS, GKE, AKS, or on-prem)
- Customer provides secret management (Vault, cloud secrets, etc.)
- Customer provides container registry access (GHCR, internal registry)
- Customer provides storage class (gp3, standard, etc.)

**ForgeWorks does NOT provision:** VPC, subnets, NAT gateways, secret stores, container registries.

---

## Pre-Deployment: Network Scenario Selection

Before starting, identify which network scenario matches the customer environment:

| Scenario | Public Subnets | NAT Gateway | Internet Egress | Typical Environment |
|----------|----------------|-------------|-----------------|---------------------|
| **A: Standard** | Yes | Yes | Yes | Development, startups |
| **B: Private-Only** | No | No | VPC Endpoints | Enterprise secure |
| **C: Air-Gapped** | No | No | Proxy only | Regulated industries |

**Select scenario:** ______ (A, B, or C)

---

## Sprint Overview

| Sprint | Focus | Duration | Depends On |
|--------|-------|----------|------------|
| **I-(-1)** | AWS Foundation (IAM, CLI, EKS) | Day 0-1 | AWS Account |
| **I-0** | Prerequisites & Configuration | Day 1 | I-(-1) |
| **I-1** | Namespaces & RBAC | Day 2 | I-0 |
| **I-2** | Operators (Strimzi, Flink) | Day 2-3 | I-1 |
| **I-3** | Storage & Secrets Integration | Day 3 | I-1 |
| **I-4** | ForgeWorks Engine Deployment | Day 4-5 | I-2, I-3 |
| **I-5** | Validation | Day 5-6 | I-4 |

---

## Sprint I-(-1): AWS Foundation (Day 0-1)

**Goal:** Set up AWS access with proper IAM users, policies, and provision EKS cluster

### Why This Sprint Exists

Before deploying ForgeWorks, we need:
1. Proper IAM users with least-privilege access (not admin account)
2. Updated AWS CLI with configured credentials
3. An EKS cluster to deploy onto

**Status:** ✅ COMPLETE (2025-02-01)

### Task Checklist

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T-I(-1).1 | Update AWS CLI to latest version | CRITICAL | ✅ |
| T-I(-1).2 | Create IAM user: `fw-infra` (infrastructure) | CRITICAL | ✅ |
| T-I(-1).3 | Create IAM user: `fw-deploy` (deployment) | CRITICAL | ✅ |
| T-I(-1).4 | Create IAM user: `fw-ci` (CI/CD automation) | HIGH | ✅ |
| T-I(-1).5 | Create IAM policies with least-privilege | CRITICAL | ✅ |
| T-I(-1).6 | Attach policies to users | CRITICAL | ✅ |
| T-I(-1).7 | Generate access keys for `fw-infra` | CRITICAL | ✅ |
| T-I(-1).8 | Configure AWS CLI profile for `fw-infra` | CRITICAL | ✅ |
| T-I(-1).9 | Validate AWS access | CRITICAL | ✅ |
| T-I(-1).10 | Provision EKS cluster (or validate existing) | CRITICAL | ✅ |
| T-I(-1).11 | Configure kubectl for EKS | CRITICAL | ✅ |

> **Note:** IAM Identity Center (SSO) was used instead of legacy IAM users.
> Profiles: fw-admin (IAM management), fw-infra (infrastructure), fw-deploy (deployments)

---

### T-I(-1).1: Update AWS CLI

```bash
# Check current version
aws --version

# macOS - Update via Homebrew
brew upgrade awscli

# Or download latest installer
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --update

# Verify
aws --version
# Expected: aws-cli/2.x.x or higher
```

---

### T-I(-1).2 to T-I(-1).4: Create IAM Users

#### IAM User Strategy

| User | Purpose | When Used |
|------|---------|-----------|
| `fw-infra` | Provision infrastructure (VPC, EKS, S3) | Initial setup, infrastructure changes |
| `fw-deploy` | Deploy workloads to EKS | Day-to-day deployments |
| `fw-ci` | CI/CD pipeline automation | GitHub Actions, automated deployments |

#### Create Users (Console or CLI)

```bash
# Using existing admin credentials temporarily
# Create users (no console access - programmatic only)

aws iam create-user --user-name fw-infra
aws iam create-user --user-name fw-deploy
aws iam create-user --user-name fw-ci

# Verify
aws iam list-users --query 'Users[?starts_with(UserName, `fw-`)].UserName'
```

---

### T-I(-1).5: Create IAM Policies

#### Policy: fw-infra-policy (Infrastructure Provisioning)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSFullAccess",
      "Effect": "Allow",
      "Action": [
        "eks:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribeInternetGateways",
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:DescribeNatGateways",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:DescribeAddresses",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:DescribeRouteTables",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateTags",
        "ec2:DescribeTags",
        "ec2:DescribeAvailabilityZones"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMForEKS",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:CreateOpenIDConnectProvider",
        "iam:DeleteOpenIDConnectProvider",
        "iam:GetOpenIDConnectProvider",
        "iam:TagOpenIDConnectProvider",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:PutBucketPolicy",
        "s3:GetBucketPolicy",
        "s3:PutBucketVersioning",
        "s3:GetBucketVersioning",
        "s3:PutEncryptionConfiguration",
        "s3:GetEncryptionConfiguration",
        "s3:PutBucketTagging",
        "s3:GetBucketTagging"
      ],
      "Resource": "arn:aws:s3:::fw-*"
    },
    {
      "Sid": "CloudFormationForEKS",
      "Effect": "Allow",
      "Action": [
        "cloudformation:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AutoScalingForEKS",
      "Effect": "Allow",
      "Action": [
        "autoscaling:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Policy: fw-deploy-policy (Deployment)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSReadAndConnect",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:AccessKubernetesApi"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::fw-*",
        "arn:aws:s3:::fw-*/*"
      ]
    },
    {
      "Sid": "ECRPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Policy: fw-ci-policy (CI/CD)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSConnect",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetAuthorizationToken",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Artifacts",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::fw-*",
        "arn:aws:s3:::fw-*/*"
      ]
    }
  ]
}
```

#### Create Policies via CLI

```bash
# Save policies to files first, then:

aws iam create-policy \
  --policy-name fw-infra-policy \
  --policy-document file://policies/fw-infra-policy.json

aws iam create-policy \
  --policy-name fw-deploy-policy \
  --policy-document file://policies/fw-deploy-policy.json

aws iam create-policy \
  --policy-name fw-ci-policy \
  --policy-document file://policies/fw-ci-policy.json
```

---

### T-I(-1).6: Attach Policies to Users

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Attach policies
aws iam attach-user-policy \
  --user-name fw-infra \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-infra-policy

aws iam attach-user-policy \
  --user-name fw-deploy \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-deploy-policy

aws iam attach-user-policy \
  --user-name fw-ci \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-ci-policy

# Verify
aws iam list-attached-user-policies --user-name fw-infra
aws iam list-attached-user-policies --user-name fw-deploy
aws iam list-attached-user-policies --user-name fw-ci
```

---

### T-I(-1).7: Generate Access Keys

```bash
# Generate access keys for fw-infra (you'll use this for EKS setup)
aws iam create-access-key --user-name fw-infra

# SAVE THE OUTPUT SECURELY!
# {
#   "AccessKey": {
#     "UserName": "fw-infra",
#     "AccessKeyId": "AKIA...",
#     "SecretAccessKey": "...",
#     "Status": "Active"
#   }
# }

# Generate for fw-deploy (for day-to-day work)
aws iam create-access-key --user-name fw-deploy

# Generate for fw-ci (store in GitHub Secrets later)
aws iam create-access-key --user-name fw-ci
```

---

### T-I(-1).8: Configure AWS CLI Profiles

```bash
# Configure fw-infra profile
aws configure --profile fw-infra
# AWS Access Key ID: <from step above>
# AWS Secret Access Key: <from step above>
# Default region: us-east-1 (or your region)
# Default output format: json

# Configure fw-deploy profile
aws configure --profile fw-deploy
# ... same process

# Verify profiles exist
cat ~/.aws/credentials

# Test each profile
aws sts get-caller-identity --profile fw-infra
aws sts get-caller-identity --profile fw-deploy
```

---

### T-I(-1).9: Validate AWS Access

```bash
# Validation script
echo "=== Validating fw-infra permissions ==="
aws eks list-clusters --profile fw-infra
aws ec2 describe-vpcs --profile fw-infra --query 'Vpcs[].VpcId'

echo "=== Validating fw-deploy permissions ==="
aws eks list-clusters --profile fw-deploy
aws s3 ls --profile fw-deploy 2>/dev/null || echo "No S3 buckets yet (expected)"

echo "=== All validations passed ==="
```

---

### T-I(-1).10: Provision EKS Cluster

#### Option A: eksctl (Recommended for simplicity)

```bash
# Install eksctl if not present
brew install eksctl  # macOS
# or
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster using fw-infra profile
export AWS_PROFILE=fw-infra

eksctl create cluster \
  --name forge-works-dev \
  --region us-east-1 \
  --version 1.29 \
  --nodegroup-name fw-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed \
  --with-oidc \
  --ssh-access \
  --ssh-public-key ~/.ssh/id_rsa.pub \
  --tags "Project=ForgeWorks,Environment=dev"

# This takes 15-20 minutes
```

#### Option B: Terraform/Pulumi (More control)

See `infra/terraform/eks/` or `infra/pulumi/eks/` for IaC approach.

---

### T-I(-1).11: Configure kubectl for EKS

```bash
# Update kubeconfig (using fw-deploy for day-to-day)
export AWS_PROFILE=fw-deploy

aws eks update-kubeconfig \
  --region us-east-1 \
  --name forge-works-dev \
  --alias fw-dev

# Verify
kubectl cluster-info
kubectl get nodes

# Expected output:
# NAME                             STATUS   ROLES    AGE   VERSION
# ip-10-0-1-xxx.ec2.internal       Ready    <none>   5m    v1.29.x
# ip-10-0-2-xxx.ec2.internal       Ready    <none>   5m    v1.29.x
# ip-10-0-3-xxx.ec2.internal       Ready    <none>   5m    v1.29.x
```

---

### Sprint I-(-1) Completion Checklist

```
AWS FOUNDATION CHECKLIST
═══════════════════════════════════════════════════════════════

AWS CLI
[ ] AWS CLI version >= 2.x confirmed

IAM USERS CREATED
[ ] fw-infra user exists
[ ] fw-deploy user exists
[ ] fw-ci user exists

IAM POLICIES CREATED & ATTACHED
[ ] fw-infra-policy attached to fw-infra
[ ] fw-deploy-policy attached to fw-deploy
[ ] fw-ci-policy attached to fw-ci

ACCESS KEYS GENERATED
[ ] fw-infra access key saved securely
[ ] fw-deploy access key saved securely
[ ] fw-ci access key saved (for GitHub Secrets)

AWS CLI PROFILES CONFIGURED
[ ] ~/.aws/credentials has fw-infra profile
[ ] ~/.aws/credentials has fw-deploy profile

AWS ACCESS VALIDATED
[ ] aws sts get-caller-identity --profile fw-infra works
[ ] aws sts get-caller-identity --profile fw-deploy works

EKS CLUSTER
[ ] EKS cluster forge-works-dev provisioned
[ ] kubectl configured and connected
[ ] kubectl get nodes shows 3 ready nodes

═══════════════════════════════════════════════════════════════
```

---

## Sprint I-0: Prerequisites & Configuration (Day 1)

**Goal:** Gather customer environment details and configure ForgeWorks

**Status:** ✅ COMPLETE (2025-02-01)

### Task Checklist

| ID | Task | Priority | Status | Result |
|----|------|----------|--------|--------|
| T-I0.1 | Confirm Kubernetes cluster access (kubectl works) | CRITICAL | ✅ | fw-infra profile |
| T-I0.2 | Identify network scenario (A, B, or C) | CRITICAL | ✅ | **Scenario A (Standard)** |
| T-I0.3 | Identify storage class name | CRITICAL | ✅ | **gp3 (default)** + EBS CSI Driver |
| T-I0.4 | Identify secret store type (Vault, K8s Secrets, etc.) | CRITICAL | ✅ | **K8s Secrets** |
| T-I0.5 | Identify container registry (GHCR or internal) | HIGH | ✅ | **GHCR** (pull verified) |
| T-I0.6 | Create ForgeWorks configuration file | CRITICAL | ✅ | **forgeworks-config.yaml** |
| T-I0.7 | Verify Helm >= 3.12 installed | HIGH | ✅ | helm v3.x installed |

### Sprint I-0 Results

```
CONFIGURATION SUMMARY
═══════════════════════════════════════════════════════════════
Cluster:        forge-works-dev (EKS 1.31)
Region:         us-east-1
Network:        Scenario A (Standard) - Public endpoint
Storage:        gp3 (EBS CSI Driver) - Default StorageClass
Secrets:        Kubernetes Secrets (Option A)
Registry:       ghcr.io/forge-works
Config File:    infra/forgeworks-config.yaml
═══════════════════════════════════════════════════════════════
```

### Configuration Template

Create `forgeworks-config.yaml`:

```yaml
# ForgeWorks Installation Configuration
# Aligned with "Bring Your Own Stack" philosophy

cluster:
  # Customer's Kubernetes cluster details
  provider: eks  # eks, gke, aks, openshift, on-prem
  version: "1.29"

network:
  # Select scenario: A (standard), B (private-only), C (air-gapped)
  scenario: A

  # Scenario A: Standard (public subnets, NAT gateway)
  # Scenario B: Private-only (VPC endpoints, no NAT)
  # Scenario C: Air-gapped (internal proxy, internal registry)

  # For Scenario B/C: proxy configuration
  proxy:
    enabled: false
    httpProxy: ""
    httpsProxy: ""
    noProxy: ".cluster.local,.svc"

images:
  # Container registry configuration
  registry: ghcr.io/forge-works  # Or customer's internal registry
  pullPolicy: IfNotPresent
  # pullSecret: regcred  # Uncomment if using private registry

storage:
  # Storage class for persistent volumes
  class: gp3  # Or customer's storage class name
  highIopsClass: gp3-high-iops  # For Kafka (optional)

secrets:
  # Secret management integration
  # Options: kubernetes, external-secrets, sealed-secrets
  backend: kubernetes

  # If using external-secrets:
  # backend: external-secrets
  # provider: vault  # or aws-secrets-manager, azure-key-vault
  # secretStore: cluster-secret-store  # Name of ClusterSecretStore

s3:
  # S3-compatible storage for state, models, logs
  endpoint: s3.amazonaws.com  # or minio.internal:9000
  region: us-east-1
  buckets:
    state: forge-works-state
    models: forge-works-models
    logs: forge-works-logs
  # If using IRSA (EKS):
  # useIRSA: true
  # If using static credentials:
  # credentialsSecret: forge-s3-credentials
```

### Verification Commands

```bash
# T-I0.1: Cluster access
kubectl cluster-info
kubectl get nodes

# T-I0.3: List storage classes
kubectl get sc

# T-I0.7: Helm version
helm version
```

---

## Sprint I-1: Namespaces & RBAC (Day 1)

**Goal:** Create ForgeWorks namespaces with proper security policies

**Status:** ✅ COMPLETE (2025-02-04)

### Task Checklist

| ID | Task | Priority | Status | Result |
|----|------|----------|--------|--------|
| T-I1.1 | Create forge-engine namespace | CRITICAL | ✅ | PSS: baseline |
| T-I1.2 | Create forge-works namespace | CRITICAL | ✅ | PSS: restricted |
| T-I1.3 | Create forge-ml namespace | HIGH | ✅ | PSS: baseline |
| T-I1.4 | Apply Pod Security Standards | HIGH | ✅ | enforce + warn |
| T-I1.5 | Create service accounts | CRITICAL | ✅ | 8 accounts |
| T-I1.6 | Create RBAC roles and bindings | CRITICAL | ✅ | Least privilege |
| T-I1.7 | Create NetworkPolicies (default deny) | HIGH | ✅ | Default deny + allow |

### Sprint I-1 Results

**Manifests:** `infra/k8s/base/`
```
├── kustomization.yaml
├── namespaces.yaml
├── service-accounts.yaml
├── rbac.yaml
└── network-policies.yaml
```

**Apply:** `kubectl apply -k infra/k8s/base/`

### Namespace Creation

```bash
# Create namespaces with Pod Security Standards
for ns in forge-engine forge-works forge-ml; do
  kubectl create namespace $ns --dry-run=client -o yaml | kubectl apply -f -
  kubectl label namespace $ns \
    pod-security.kubernetes.io/enforce=baseline \
    pod-security.kubernetes.io/audit=restricted \
    pod-security.kubernetes.io/warn=restricted \
    --overwrite
done
```

### Service Accounts

```yaml
# infra/base/service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: forge-backend
  namespace: forge-works
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: forge-webhook-gateway
  namespace: forge-works
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flink-job-sa
  namespace: forge-engine
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: airflow-worker
  namespace: forge-engine
```

### RBAC

```yaml
# infra/base/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: forge-backend-role
  namespace: forge-works
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "get", "list", "watch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: forge-backend-binding
  namespace: forge-works
subjects:
  - kind: ServiceAccount
    name: forge-backend
roleRef:
  kind: Role
  name: forge-backend-role
  apiGroup: rbac.authorization.k8s.io
```

### NetworkPolicy (Default Deny)

```yaml
# infra/base/network-policy-default.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: forge-engine
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: forge-works
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

---

## Sprint I-2: Operators (Day 1-2)

**Goal:** Install Kubernetes operators for Kafka and Flink

**Status:** ✅ COMPLETE (2025-02-04)

### Task Checklist

| ID | Task | Priority | Status | Result |
|----|------|----------|--------|--------|
| T-I2.1 | Install Strimzi Kafka Operator | CRITICAL | ✅ | v0.50.0 |
| T-I2.2 | Verify Strimzi CRDs available | CRITICAL | ✅ | 10 CRDs |
| T-I2.3 | Install Flink Kubernetes Operator | HIGH | ✅ | v1.10.0 |
| T-I2.4 | Verify Flink CRDs available | HIGH | ✅ | 3 CRDs |
| T-I2.5 | Install Cert-Manager (Flink dependency) | HIGH | ✅ | v1.16.2 |

### Sprint I-2 Results

**Operators Installed:**
```bash
# Strimzi
helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
  --namespace forge-engine

# Flink (requires cert-manager)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  --namespace forge-engine
```

**Verification:**
```bash
kubectl get pods -n forge-engine
kubectl get crd | grep -E 'strimzi|flink'
```

### Strimzi Installation

```bash
# Create Strimzi namespace
kubectl create namespace kafka

# Option 1: Install via Helm (recommended)
helm repo add strimzi https://strimzi.io/charts/
helm repo update

helm install strimzi-cluster-operator strimzi/strimzi-kafka-operator \
  --namespace kafka \
  --set watchNamespaces="{forge-engine}" \
  --set featureGates="" \
  --version 0.40.0

# Option 2: Install via YAML
# kubectl apply -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Verify
kubectl get pods -n kafka
kubectl get crd | grep strimzi
```

### Flink Operator Installation

```bash
# Install Flink Kubernetes Operator via Helm
helm repo add flink-operator https://downloads.apache.org/flink/flink-kubernetes-operator-1.8.0/
helm repo update

helm install flink-kubernetes-operator flink-operator/flink-kubernetes-operator \
  --namespace forge-engine \
  --set watchNamespaces="{forge-engine}" \
  --version 1.8.0

# Verify
kubectl get pods -n forge-engine -l app.kubernetes.io/name=flink-kubernetes-operator
kubectl get crd | grep flink
```

### Network Scenario Configuration

For **Scenario B/C** (private networks), configure operators with proxy:

```yaml
# Strimzi with proxy (Scenario B/C)
helm upgrade strimzi-cluster-operator strimzi/strimzi-kafka-operator \
  --namespace kafka \
  --set "env[0].name=HTTP_PROXY" \
  --set "env[0].value=http://proxy.corp.internal:3128" \
  --set "env[1].name=HTTPS_PROXY" \
  --set "env[1].value=http://proxy.corp.internal:3128" \
  --set "env[2].name=NO_PROXY" \
  --set "env[2].value=.cluster.local,.svc,.kafka"
```

---

## Sprint I-3: Storage & Secrets Integration (Day 2)

**Goal:** Configure storage and connect to customer's secret management

### Task Checklist

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T-I3.1 | Verify storage class exists | CRITICAL | ⬜ |
| T-I3.2 | Create high-IOPS storage class (if needed) | HIGH | ⬜ |
| T-I3.3 | Configure secret backend (Vault/K8s/ESO) | CRITICAL | ⬜ |
| T-I3.4 | Create secrets for ForgeWorks | CRITICAL | ⬜ |
| T-I3.5 | Configure S3 access (IRSA or credentials) | CRITICAL | ⬜ |

### Storage Class Verification

```bash
# List available storage classes
kubectl get sc

# Check if default exists
kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

### Create High-IOPS Storage Class (if not exists)

```yaml
# infra/base/storage-class-high-iops.yaml
# Only if customer doesn't have equivalent
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-high-iops
provisioner: ebs.csi.aws.com  # Or customer's CSI driver
parameters:
  type: gp3
  iops: "10000"
  throughput: "500"
  encrypted: "true"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Secrets Configuration

#### Option A: Kubernetes Secrets (Simplest)

```bash
# Create secrets directly in Kubernetes
# (Customer provides these values)

kubectl create secret generic forge-postgres-credentials \
  --namespace forge-engine \
  --from-literal=username=forgeworks \
  --from-literal=password="${POSTGRES_PASSWORD}"

kubectl create secret generic forge-s3-credentials \
  --namespace forge-engine \
  --from-literal=access-key="${AWS_ACCESS_KEY}" \
  --from-literal=secret-key="${AWS_SECRET_KEY}"
```

#### Option B: External Secrets Operator (Enterprise)

```bash
# Install External Secrets Operator (if not already installed)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace

# Create ClusterSecretStore pointing to customer's Vault
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.corp.internal:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "forgeworks"
          serviceAccountRef:
            name: "external-secrets"
            namespace: "external-secrets"
EOF

# Create ExternalSecret to sync from Vault
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: forge-postgres-credentials
  namespace: forge-engine
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: forge-postgres-credentials
  data:
    - secretKey: username
      remoteRef:
        key: secret/data/forgeworks/postgres
        property: username
    - secretKey: password
      remoteRef:
        key: secret/data/forgeworks/postgres
        property: password
EOF
```

### S3 Access Configuration

#### Option A: IRSA (EKS)

```yaml
# Service account with IAM role annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flink-job-sa
  namespace: forge-engine
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/ForgeFlinkRole
```

#### Option B: Static Credentials

```yaml
# Already created above: forge-s3-credentials
# Reference in Flink/Airflow configurations
```

#### Option C: MinIO (On-Prem)

```yaml
# MinIO credentials secret
kubectl create secret generic forge-s3-credentials \
  --namespace forge-engine \
  --from-literal=access-key=minio-admin \
  --from-literal=secret-key="${MINIO_SECRET}"
```

---

## Sprint I-4: ForgeWorks Engine Deployment (Day 3-4)

**Goal:** Deploy Kafka, Flink, Redis, and PostgreSQL

### Task Checklist

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T-I4.1 | Deploy Kafka cluster (Strimzi) | CRITICAL | ⬜ |
| T-I4.2 | Create Kafka topics | CRITICAL | ⬜ |
| T-I4.3 | Deploy Redis (model cache) | HIGH | ⬜ |
| T-I4.4 | Deploy PostgreSQL (or connect to external) | HIGH | ⬜ |
| T-I4.5 | Verify all components healthy | CRITICAL | ⬜ |

### Deploy Kafka

```bash
# Apply Kafka manifests (already created)
kubectl apply -k infra/kafka/overlays/dev

# Wait for Kafka to be ready
kubectl wait kafka/forge-kafka --for=condition=Ready --timeout=300s -n forge-engine

# Verify topics
kubectl get kafkatopic -n forge-engine
```

### Deploy Redis

```bash
# Using Bitnami Helm chart
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install redis bitnami/redis \
  --namespace forge-engine \
  --set architecture=standalone \
  --set auth.enabled=true \
  --set auth.existingSecret=forge-redis-credentials \
  --set persistence.storageClass=gp3 \
  --set persistence.size=20Gi
```

### Deploy PostgreSQL

```bash
# Option A: In-cluster PostgreSQL (development)
helm install postgresql bitnami/postgresql \
  --namespace forge-engine \
  --set auth.existingSecret=forge-postgres-credentials \
  --set persistence.storageClass=gp3 \
  --set persistence.size=50Gi

# Option B: Use customer's external PostgreSQL
# Configure connection string in secrets
```

### Verify Deployment

```bash
# Check all pods in forge-engine
kubectl get pods -n forge-engine

# Check Kafka status
kubectl get kafka -n forge-engine

# Check topics
kubectl get kafkatopic -n forge-engine

# Test Kafka connectivity
kubectl run kafka-test --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  -n forge-engine \
  -- bin/kafka-topics.sh --bootstrap-server forge-kafka-kafka-bootstrap:9092 --list
```

---

## Sprint I-5: Validation (Day 4-5)

**Goal:** Validate complete infrastructure before Engine Phase 1

### Task Checklist

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T-I5.1 | Validate Kafka produce/consume | CRITICAL | ⬜ |
| T-I5.2 | Validate S3 access | CRITICAL | ⬜ |
| T-I5.3 | Validate secrets accessible | CRITICAL | ⬜ |
| T-I5.4 | Validate NetworkPolicies allow expected traffic | HIGH | ⬜ |
| T-I5.5 | Run integration smoke test | CRITICAL | ⬜ |
| T-I5.6 | Document infrastructure outputs | HIGH | ⬜ |

### Validation Script

```bash
#!/bin/bash
# infra/scripts/validate-infrastructure.sh

set -e
echo "=== ForgeWorks Infrastructure Validation ==="

PASS=0
FAIL=0

check() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ((PASS++))
  else
    echo "❌ $1"
    ((FAIL++))
  fi
}

# Namespaces
check "forge-engine namespace exists" "kubectl get ns forge-engine"
check "forge-works namespace exists" "kubectl get ns forge-works"
check "forge-ml namespace exists" "kubectl get ns forge-ml"

# Operators
check "Strimzi operator running" "kubectl get pods -n kafka -l name=strimzi-cluster-operator --field-selector=status.phase=Running"

# Kafka
check "Kafka cluster ready" "kubectl get kafka forge-kafka -n forge-engine -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}' | grep True"
check "Kafka topics created" "kubectl get kafkatopic -n forge-engine --no-headers | wc -l | grep -v '^0$'"

# Redis
check "Redis running" "kubectl get pods -n forge-engine -l app.kubernetes.io/name=redis --field-selector=status.phase=Running"

# PostgreSQL (if in-cluster)
check "PostgreSQL running" "kubectl get pods -n forge-engine -l app.kubernetes.io/name=postgresql --field-selector=status.phase=Running" || echo "  (Skipped if using external PostgreSQL)"

# Secrets
check "PostgreSQL credentials exist" "kubectl get secret forge-postgres-credentials -n forge-engine"

echo ""
echo "=== Results ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [ $FAIL -gt 0 ]; then
  echo "⚠️  Some checks failed. Review before proceeding."
  exit 1
else
  echo "✅ All checks passed! Ready for Engine Phase 1."
fi
```

### Kafka Produce/Consume Test

```bash
# Produce test message
kubectl run kafka-producer --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  -n forge-engine \
  -- bin/kafka-console-producer.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap:9092 \
  --topic forge.events.github <<< '{"test": "hello"}'

# Consume test message
kubectl run kafka-consumer --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  -n forge-engine \
  -- bin/kafka-console-consumer.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap:9092 \
  --topic forge.events.github \
  --from-beginning \
  --max-messages 1
```

---

## Network Scenario-Specific Tasks

### Scenario A: Standard (No additional tasks)

Standard networking works out of the box.

### Scenario B: Private-Only

Additional tasks for private networking:

| ID | Task | Notes |
|----|------|-------|
| T-B.1 | Verify VPC endpoints exist | S3, ECR (or registry), STS |
| T-B.2 | Configure internal ingress | Internal ALB/NLB |
| T-B.3 | Update container image references | Use private registry if needed |

### Scenario C: Air-Gapped

Additional tasks for air-gapped:

| ID | Task | Notes |
|----|------|-------|
| T-C.1 | Mirror ForgeWorks images to internal registry | All GHCR images |
| T-C.2 | Configure HTTP_PROXY on all pods | Via Helm values |
| T-C.3 | Update image references in all manifests | Point to internal registry |
| T-C.4 | Verify proxy allows required egress | S3/MinIO, internal services |

---

## Dependency Graph

```
I-(-1) (AWS Foundation)
    │
    ├── Update AWS CLI
    ├── Create IAM Users (fw-infra, fw-deploy, fw-ci)
    ├── Create & Attach IAM Policies
    ├── Configure AWS CLI Profiles
    └── Provision EKS Cluster
           │
           ▼
    I-0 (Prerequisites)
           │
           ▼
    I-1 (Namespaces & RBAC)
           │
    ├──────┴──────┐
    ▼             ▼
I-2 (Operators)  I-3 (Storage)
    │             │
    └──────┬──────┘
           ▼
    I-4 (Engine Deploy)
           │
           ▼
    I-5 (Validation)
           │
           ▼
    ENGINE PHASE 1 (Kafka Topics)
```

---

## Post-Deployment: What's Next

After infrastructure validation passes:

1. **Deploy Kafka topics** (already done in Phase 1 manifests)
2. **Continue with ACTION_PLAN_PHASE-1.md** (Sprint 1.2: Webhook Gateway)
3. **Configure user's observability** to scrape ForgeWorks /metrics

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Kafka pods pending | No storage class | Verify storage class exists |
| Operators not starting | Image pull failed | Check registry access, proxy config |
| Secrets not found | ESO misconfigured | Check SecretStore configuration |
| NetworkPolicy blocking | Too restrictive | Add explicit allow rules |

### Debug Commands

```bash
# Check pod events
kubectl describe pod <pod-name> -n forge-engine

# Check operator logs
kubectl logs -n kafka -l name=strimzi-cluster-operator

# Check secret sync (ESO)
kubectl get externalsecret -n forge-engine
kubectl describe externalsecret <name> -n forge-engine
```

---

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) - Infrastructure design
- [PREREQUISITES.md](PREREQUISITES.md) - Required tools and access
- [EKS_OPERATIONS.md](EKS_OPERATIONS.md) - Cluster operations, scaling, troubleshooting
- [CHECKLIST_AWS_FOUNDATION.md](CHECKLIST_AWS_FOUNDATION.md) - AWS setup checklist
- [PROGRESS.md](PROGRESS.md) - Progress tracker and status
- [forgeworks-config.yaml](forgeworks-config.yaml) - Main configuration file
- [ACTION_PLAN_PHASE-1.md](../roadmap/ACTION_PLAN_PHASE-1.md) - Engine Phase 1

---

*Action Plan v2.0.0*
*Created: 2025-01-24*
*Revised: Aligned with "Bring Your Own Stack" philosophy*
