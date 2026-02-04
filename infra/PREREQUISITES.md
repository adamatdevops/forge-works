# ForgeWorks Infrastructure Prerequisites

> **Status:** 📋 CHECKLIST
> **Version:** 2.0.0
> **Last Updated:** 2025-01-24
> **Philosophy:** "Bring Your Own Stack" - ForgeWorks deploys ON customer infrastructure

---

## Core Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER PROVIDES                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Kubernetes Cluster (EKS/GKE/AKS/OpenShift)             │   │
│  │  Network (VPC, Subnets, NAT/Endpoints)                  │   │
│  │  Secret Store (Vault, AWS SM, K8s Secrets)              │   │
│  │  Container Registry (GHCR, Harbor, ECR, ACR)            │   │
│  │  Storage Classes (gp3, EBS, etc.)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│               ┌────────────────────────────────┐                │
│               │   FORGEWORKS DEPLOYS           │                │
│               │   ┌──────────────────────────┐ │                │
│               │   │ Kafka (Strimzi)          │ │                │
│               │   │ Flink (Operator)         │ │                │
│               │   │ Airflow (Helm)           │ │                │
│               │   │ PostgreSQL (in-cluster)  │ │                │
│               │   │ Redis (caching)          │ │                │
│               │   │ ForgeWorks App           │ │                │
│               │   └──────────────────────────┘ │                │
│               └────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

**ForgeWorks does NOT provision:** VPC, subnets, NAT gateways, secret stores, container registries, EKS clusters.

---

## Quick Checklist

```
PRE-DEPLOYMENT CHECKLIST
═══════════════════════════════════════════════════════════════

CUSTOMER-PROVIDED INFRASTRUCTURE
[ ] Kubernetes cluster available (EKS/GKE/AKS/OpenShift)
[ ] kubectl access to cluster confirmed
[ ] Network egress available (or proxy configured)
[ ] Storage class available (default or gp3)
[ ] Namespace creation permissions

NETWORK SCENARIO (pick one)
[ ] Scenario A: Standard (has NAT/Internet Gateway)
[ ] Scenario B: Private-Only (VPC Endpoints, no NAT)
[ ] Scenario C: Air-Gapped (proxy required for images)

CONTAINER REGISTRY
[ ] Default: ghcr.io/forge-works (internet access required)
[ ] Or: Customer registry (Harbor, ECR, ACR, etc.)
[ ] Registry pull credentials configured

SECRETS BACKEND (pick one)
[ ] Option A: Kubernetes Secrets (simplest)
[ ] Option B: External Secrets Operator + Vault
[ ] Option C: External Secrets Operator + AWS SM
[ ] Option D: Sealed Secrets

OPERATOR WORKSTATION
[ ] kubectl installed and configured
[ ] Helm >= 3.12 installed
[ ] kustomize >= 5.0 installed (optional)
[ ] Access to create CRDs (Strimzi, Flink Operator)

═══════════════════════════════════════════════════════════════
```

---

## Part 1: Customer-Provided Infrastructure

These components must exist BEFORE ForgeWorks deployment.

### 1.1 Kubernetes Cluster

| Requirement | Specification | Validation |
|-------------|---------------|------------|
| Kubernetes Version | >= 1.28 | `kubectl version` |
| Node Count (min) | 3 nodes | `kubectl get nodes` |
| Total vCPUs | >= 16 vCPUs | Node capacity |
| Total Memory | >= 32 GB | Node capacity |
| CRD Creation | Allowed | RBAC permissions |
| PV Provisioning | Dynamic | StorageClass exists |

**Validation Commands:**

```bash
# Verify cluster access
kubectl cluster-info

# Check Kubernetes version
kubectl version --short

# List nodes
kubectl get nodes -o wide

# Verify StorageClass exists
kubectl get storageclass

# Check if you can create CRDs (needed for Strimzi/Flink)
kubectl auth can-i create customresourcedefinitions
```

### 1.2 Network Configuration

ForgeWorks supports three network scenarios:

#### Scenario A: Standard (NAT/Internet Gateway)

Most common setup. Nodes can reach the internet.

| Requirement | Why Needed |
|-------------|------------|
| Egress to ghcr.io | Pull ForgeWorks images |
| Egress to Helm repos | Install operators |
| Internal pod networking | Service-to-service communication |

**Validation:**
```bash
# From a pod, verify internet access
kubectl run test --rm -it --image=busybox -- wget -qO- https://ghcr.io -T 5 || echo "No internet access"
```

#### Scenario B: Private-Only (VPC Endpoints)

Enterprise environments without NAT Gateway.

| Requirement | Why Needed |
|-------------|------------|
| VPC Endpoint: S3 | State storage, model artifacts |
| VPC Endpoint: ECR (if using) | Pull images |
| VPC Endpoint: STS | IRSA authentication |
| Internal registry | Pre-pulled images (Harbor, etc.) |

**Validation:**
```bash
# Verify S3 endpoint works (from pod)
aws s3 ls --region us-east-1 --no-cli-pager

# Verify internal registry is accessible
kubectl run test --rm -it --image=harbor.internal.company.com/library/busybox -- echo "Registry works"
```

#### Scenario C: Air-Gapped (Proxy Required)

Highly secure environments with explicit proxy for egress.

| Requirement | Why Needed |
|-------------|------------|
| HTTP/HTTPS Proxy | All egress traffic |
| Proxy allowlist | ghcr.io, *.amazonaws.com |
| Internal registry | All images pre-mirrored |
| Internal Helm repos | Charts pre-mirrored |

**Configuration:**
```yaml
# Pod environment variables (handled by ForgeWorks config)
env:
  - name: HTTP_PROXY
    value: "http://proxy.company.com:8080"
  - name: HTTPS_PROXY
    value: "http://proxy.company.com:8080"
  - name: NO_PROXY
    value: "10.0.0.0/8,172.16.0.0/12,.svc,.cluster.local"
```

### 1.3 Storage Classes

ForgeWorks requires dynamic volume provisioning.

| Storage Class | Purpose | Minimum Size |
|---------------|---------|--------------|
| Default or gp3 | Kafka data, PostgreSQL | 100 GB |
| gp3-throughput (optional) | High-throughput Kafka | 200 GB |

**Validation:**
```bash
# List storage classes
kubectl get storageclass

# Verify default exists
kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

### 1.4 Namespaces

ForgeWorks requires the following namespaces (will be created if not exist):

| Namespace | Purpose |
|-----------|---------|
| `kafka` | Strimzi operator |
| `forge-engine` | Kafka cluster, Flink, Airflow |
| `forge-works` | Application workloads |
| `monitoring` | Prometheus/Grafana (optional) |

---

## Part 2: ForgeWorks Configuration

These are choices you make for the ForgeWorks deployment.

### 2.1 Container Registry

ForgeWorks images need to be accessible from your cluster.

| Option | Registry | Configuration |
|--------|----------|---------------|
| **Default** | ghcr.io/forge-works | Requires internet egress |
| Enterprise | harbor.company.com | Mirror images, update config |
| AWS | ECR (xxx.dkr.ecr.region.amazonaws.com) | Configure ECR pull-through or mirror |
| Azure | ACR (xxx.azurecr.io) | Configure ACR credentials |

**Default Configuration (GHCR):**
```yaml
# forgeworks-config.yaml
images:
  registry: ghcr.io/forge-works
  pullPolicy: IfNotPresent
  # No pull secret needed for public GHCR
```

**Enterprise Registry Configuration:**
```yaml
# forgeworks-config.yaml
images:
  registry: harbor.company.com/forgeworks
  pullPolicy: Always
  pullSecretName: harbor-credentials

# Create pull secret
kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.company.com \
  --docker-username=robot$forgeworks \
  --docker-password=xxx \
  -n forge-engine
```

### 2.2 Secrets Backend

ForgeWorks needs access to secrets (database passwords, API keys, etc.).

#### Option A: Kubernetes Secrets (Simplest)

```yaml
# forgeworks-config.yaml
secrets:
  backend: kubernetes
```

Create secrets directly:
```bash
# Generate and store PostgreSQL password
kubectl create secret generic postgres-credentials \
  --from-literal=username=forgeworks \
  --from-literal=password=$(openssl rand -base64 32) \
  -n forge-engine

# Generate webhook secret
kubectl create secret generic github-webhook \
  --from-literal=secret=$(openssl rand -hex 32) \
  -n forge-works
```

#### Option B: External Secrets Operator + HashiCorp Vault

```yaml
# forgeworks-config.yaml
secrets:
  backend: external-secrets
  provider: vault
  vault:
    server: https://vault.company.com
    path: secret/data/forgeworks
```

Prerequisites:
```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# Create ClusterSecretStore for Vault
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: "secret"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "forgeworks"
EOF
```

#### Option C: External Secrets Operator + AWS Secrets Manager

```yaml
# forgeworks-config.yaml
secrets:
  backend: external-secrets
  provider: aws-secrets-manager
  aws:
    region: us-east-1
    secretPrefix: /forgeworks/
```

Prerequisites:
```bash
# Install External Secrets Operator (same as Option B)

# Create ClusterSecretStore for AWS SM
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
EOF
```

#### Option D: Sealed Secrets

```yaml
# forgeworks-config.yaml
secrets:
  backend: sealed-secrets
```

Prerequisites:
```bash
# Install Sealed Secrets controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system

# Install kubeseal CLI
brew install kubeseal  # macOS
```

### 2.3 Required Secrets Inventory

Regardless of backend, these secrets must be created:

| Secret Name | Keys | Purpose |
|-------------|------|---------|
| `postgres-credentials` | username, password | PostgreSQL access |
| `github-webhook` | secret | Webhook signature verification |
| `grafana-admin` | username, password | Grafana UI (if monitoring enabled) |

**Generate Values:**
```bash
# PostgreSQL password (32 chars)
openssl rand -base64 32

# GitHub webhook secret (64 hex chars)
openssl rand -hex 32

# Grafana password (16 chars)
openssl rand -base64 16
```

---

## Part 3: Operator Workstation Requirements

The machine running deployment commands needs:

### 3.1 CLI Tools

| Tool | Minimum Version | Check Command |
|------|-----------------|---------------|
| kubectl | 1.28.0 | `kubectl version --client` |
| Helm | 3.12.0 | `helm version` |
| kustomize | 5.0.0 | `kustomize version` |
| jq | 1.6 | `jq --version` |
| yq | 4.0.0 | `yq --version` |

**Installation (macOS):**
```bash
brew install kubectl helm kustomize jq yq
```

**Installation (Linux):**
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/

# jq & yq
sudo apt install jq
sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq && sudo chmod +x /usr/local/bin/yq
```

### 3.2 Cluster Access

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Verify you can create resources
kubectl auth can-i create deployments -n forge-engine
kubectl auth can-i create customresourcedefinitions
```

### 3.3 AWS CLI (If Using AWS)

Only required if:
- Using AWS Secrets Manager backend
- Using ECR as container registry
- Need IRSA for S3 access

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Verify
aws sts get-caller-identity
```

---

## Part 4: Pre-Flight Check Script

Run this script before starting deployment:

```bash
#!/bin/bash
# pre-flight-check.sh

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           ForgeWorks Pre-Flight Check v2.0                    ║"
echo "║           Philosophy: Bring Your Own Stack                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0
WARN=0

check() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ((PASS++))
  else
    echo "❌ $1"
    ((FAIL++))
  fi
}

warn() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ((PASS++))
  else
    echo "⚠️  $1 (optional)"
    ((WARN++))
  fi
}

echo "=== Operator Workstation ==="
check "kubectl installed" "kubectl version --client"
check "Helm installed" "helm version"
warn "kustomize installed" "kustomize version"
warn "jq installed" "jq --version"
warn "yq installed" "yq --version"

echo ""
echo "=== Kubernetes Cluster ==="
check "Cluster accessible" "kubectl cluster-info"
check "Can list nodes" "kubectl get nodes"
check "Can create deployments" "kubectl auth can-i create deployments --all-namespaces"
check "Can create CRDs" "kubectl auth can-i create customresourcedefinitions"

echo ""
echo "=== Storage ==="
check "StorageClass exists" "kubectl get storageclass -o name | head -1"
check "Default StorageClass set" "kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class==\"true\")].metadata.name}' | grep -q ."

echo ""
echo "=== Network Connectivity ==="
echo "   Testing egress (run one of these from a pod if this fails):"
warn "Can reach ghcr.io" "curl -s --connect-timeout 5 https://ghcr.io > /dev/null"
warn "Can reach helm repos" "curl -s --connect-timeout 5 https://charts.bitnami.com > /dev/null"

echo ""
echo "══════════════════════════════════════════════"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo "Warnings: $WARN"
echo "══════════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  echo ""
  echo "❌ Please resolve failed checks before proceeding."
  echo "   See PREREQUISITES.md for guidance."
  exit 1
elif [ $WARN -gt 0 ]; then
  echo ""
  echo "⚠️  Some optional checks failed. Review warnings above."
  echo "   You may proceed if you understand the implications."
  exit 0
else
  echo ""
  echo "✅ All checks passed! Ready for ForgeWorks deployment."
  exit 0
fi
```

---

## Part 5: ForgeWorks Configuration Template

Create this file before deployment:

```yaml
# forgeworks-config.yaml
# ForgeWorks Deployment Configuration
# Version: 2.0.0

# Network Scenario
# A = Standard (NAT/IGW exists)
# B = Private-Only (VPC Endpoints)
# C = Air-Gapped (proxy required)
network:
  scenario: A
  proxy:
    enabled: false
    httpProxy: ""
    httpsProxy: ""
    noProxy: "10.0.0.0/8,172.16.0.0/12,.svc,.cluster.local"

# Container Images
images:
  registry: ghcr.io/forge-works  # Default: GHCR
  pullPolicy: IfNotPresent
  pullSecretName: ""  # Only if private registry

# Secrets Backend
secrets:
  backend: kubernetes  # kubernetes | external-secrets | sealed-secrets

  # If backend: external-secrets
  externalSecrets:
    provider: ""  # vault | aws-secrets-manager | azure-key-vault

    # Vault configuration
    vault:
      server: ""
      path: "secret/data/forgeworks"

    # AWS Secrets Manager configuration
    aws:
      region: us-east-1
      secretPrefix: /forgeworks/

# Component Settings
components:
  kafka:
    enabled: true
    brokers: 3  # 1 for dev, 3 for prod
    storage: 100Gi

  flink:
    enabled: true
    taskManager:
      replicas: 2

  airflow:
    enabled: true
    executor: kubernetes

  postgres:
    enabled: true
    storage: 50Gi

  redis:
    enabled: true
    storage: 10Gi

  monitoring:
    enabled: true
    grafana:
      enabled: true

# Resource Profile
profile: standard  # minimal | standard | production

# Namespaces
namespaces:
  engine: forge-engine
  app: forge-works
  monitoring: monitoring
```

---

## Part 6: Cost Estimation

Since ForgeWorks deploys ON customer infrastructure, costs are:

### ForgeWorks Components Only (Additional to Existing Cluster)

| Component | Dev Resources | Prod Resources | Notes |
|-----------|---------------|----------------|-------|
| Kafka (Strimzi) | 1 broker, 2 vCPU, 4 GB | 3 brokers, 6 vCPU, 12 GB | + storage |
| Flink Operator | 0.5 vCPU, 512 MB | 1 vCPU, 1 GB | + TaskManagers |
| Airflow | 2 vCPU, 4 GB | 4 vCPU, 8 GB | + workers |
| PostgreSQL | 1 vCPU, 2 GB | 2 vCPU, 4 GB | + storage |
| Redis | 0.5 vCPU, 1 GB | 1 vCPU, 2 GB | + storage |
| ForgeWorks App | 2 vCPU, 4 GB | 4 vCPU, 8 GB | Backend + Frontend |

**Total Additional Resources:**
- **Dev:** ~8 vCPU, 16 GB RAM, 150 GB storage
- **Prod:** ~18 vCPU, 36 GB RAM, 500 GB storage

### Storage Requirements

| Type | Dev | Prod |
|------|-----|------|
| Kafka Data | 100 GB | 300 GB |
| PostgreSQL | 20 GB | 100 GB |
| Redis | 5 GB | 20 GB |
| Flink Checkpoints | 20 GB (S3) | 100 GB (S3) |
| Model Artifacts | 10 GB (S3) | 50 GB (S3) |

---

## Quick Reference

### Key Commands

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Check storage classes
kubectl get storageclass

# Check CRD permissions
kubectl auth can-i create customresourcedefinitions

# Create namespace (if needed)
kubectl create namespace forge-engine

# Apply ForgeWorks
kubectl apply -k infra/kafka/overlays/dev
```

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Image pull fails | Registry not accessible | Configure pull secret or mirror images |
| PVC pending | No StorageClass | Create StorageClass or set default |
| CRD creation fails | Insufficient permissions | Request cluster-admin or CRD permissions |
| Pods can't reach external | Scenario B/C, missing endpoints | Configure VPC endpoints or proxy |
| Secrets not found | Wrong backend config | Verify secrets backend configuration |

---

## Next Steps

1. **Complete Pre-Flight Check:** `./pre-flight-check.sh`
2. **Create Configuration:** Copy and customize `forgeworks-config.yaml`
3. **Create Secrets:** Using your chosen backend (K8s Secrets, Vault, etc.)
4. **Start Deployment:** Follow [ACTION_PLAN_INFRASTRUCTURE.md](ACTION_PLAN_INFRASTRUCTURE.md)

---

*Prerequisites Document v2.0.0*
*Updated: 2025-01-24*
*Philosophy: Bring Your Own Stack*
