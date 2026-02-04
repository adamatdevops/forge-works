# ForgeWorks Infrastructure Architecture

> **Status:** 📋 REFERENCE DOCUMENT
> **Version:** 2.0.0
> **Last Updated:** 2025-01-24
> **Philosophy:** "Bring Your Own Stack" - ForgeWorks adapts to customer infrastructure
> **Aligned With:** Engine Phases 1-4, P0-P2 Decisions, GLUE_LAYER_EVOLUTION.md

---

## Core Philosophy: Bring Your Own Stack

ForgeWorks is designed to **live ON the customer's existing infrastructure**, NOT to replace or force dependencies. This architecture document reflects that principle.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SEPARATION OF CONCERNS                                    │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  USER'S STACK (Customer Controls)                                        │   │
│   │                                                                          │   │
│   │   • Source Control     GitHub / GitLab / Bitbucket                      │   │
│   │   • Control Plane      ArgoCD / Tekton / FluxCD / Kubernetes            │   │
│   │   • Secret Store       Vault / AWS Secrets Manager / Azure Key Vault    │   │
│   │   • Container Registry GHCR / Harbor / Artifactory / ECR               │   │
│   │   • Observability      Prometheus / Datadog / NewRelic / Splunk        │   │
│   │   • Network            Their VPC, subnets, security policies           │   │
│   │                                                                          │   │
│   │   ForgeWorks does NOT provision or replace these.                       │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  FORGEWORKS CORE (We Control)                                            │   │
│   │                                                                          │   │
│   │   • Kafka (Strimzi)    Event bus - runs in customer's cluster           │   │
│   │   • Flink              Stream processing - runs in customer's cluster   │   │
│   │   • Airflow            Batch/training - runs in customer's cluster      │   │
│   │   • Backend (FastAPI)  API server                                       │   │
│   │   • Frontend (Next.js) Dashboard                                        │   │
│   │   • Webhook Gateway    Event ingestion                                  │   │
│   │                                                                          │   │
│   │   Exposed: /health, /metrics, /api/v1/status (standard interfaces)     │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Network Topology Scenarios

ForgeWorks must support customer environments with varying security postures. We define three network scenarios:

### Scenario A: Standard (Public + Private Subnets)

For development and less restrictive production environments.

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIO A: Standard Networking                                 │
│                                                                  │
│   Internet                                                       │
│       │                                                          │
│       ▼                                                          │
│   ┌──────────┐                                                   │
│   │   ALB    │  ◄── Public subnet (webhooks, dashboard)         │
│   └────┬─────┘                                                   │
│        │                                                         │
│   ┌────┴────────────────────────────────────────────────────┐   │
│   │  Private Subnets                                         │   │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│   │  │ Kafka  │  │ Flink  │  │Airflow │  │Backend │        │   │
│   │  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│   │                    │                                     │   │
│   │                    ▼                                     │   │
│   │               NAT Gateway → Internet (egress)           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Requirements:                                                  │
│   • Public subnets for ALB/Ingress                              │
│   • NAT Gateway for outbound (pulling images, etc.)             │
│   • Internet egress allowed                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario B: Private-Only (VPC Endpoints)

For secure production environments with no public internet exposure.

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIO B: Private-Only (Highly Secure)                        │
│                                                                  │
│   NO INTERNET EXPOSURE                                           │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Private Subnets ONLY                                    │   │
│   │                                                          │   │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│   │  │ Kafka  │  │ Flink  │  │Airflow │  │Backend │        │   │
│   │  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│   │                                                          │   │
│   │       │              │              │                    │   │
│   │       ▼              ▼              ▼                    │   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │           VPC ENDPOINTS (PrivateLink)            │    │   │
│   │  │  • S3 Gateway Endpoint                           │    │   │
│   │  │  • Container Registry Interface Endpoint         │    │   │
│   │  │  • STS Interface Endpoint (for IRSA)            │    │   │
│   │  │  • Logs Interface Endpoint (optional)            │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Webhooks: Internal NLB or VPN-accessible endpoint             │
│   Dashboard: Internal only or VPN-accessible                    │
│                                                                  │
│   Requirements:                                                  │
│   • NO NAT Gateway                                              │
│   • NO public subnets                                           │
│   • VPC Endpoints for all external dependencies                 │
│   • Internal ALB/NLB for ingress (VPN access)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario C: Air-Gapped / Proxy

For highly regulated environments with proxy-based egress.

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIO C: Air-Gapped with Proxy                               │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Private Subnets                                         │   │
│   │                                                          │   │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│   │  │ Kafka  │  │ Flink  │  │Airflow │  │Backend │        │   │
│   │  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│   │       │                                                  │   │
│   │       ▼                                                  │   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │           CORPORATE PROXY                        │    │   │
│   │  │  HTTP_PROXY=proxy.corp.internal:3128            │    │   │
│   │  │  NO_PROXY=.cluster.local,.svc                   │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   │                    │                                     │   │
│   │                    ▼                                     │   │
│   │       ┌─────────────────────────┐                       │   │
│   │       │   Internal Registry     │  (Harbor, Artifactory)│   │
│   │       │   Pre-pulled images     │                       │   │
│   │       └─────────────────────────┘                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Requirements:                                                  │
│   • Internal container registry with pre-synced images          │
│   • Proxy configuration for all pods                            │
│   • No external network access                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Pluggable Components

ForgeWorks integrates with the customer's existing infrastructure through pluggable adapters.

### 2.1 Secrets Management (User's Choice)

ForgeWorks uses **External Secrets Operator** or **Kubernetes Secrets** synchronized from the customer's secret store.

```yaml
# ForgeWorks Configuration - secrets backend
forgeworks:
  secrets:
    # Option A: Kubernetes Secrets (direct)
    backend: kubernetes

    # Option B: External Secrets Operator
    backend: external-secrets
    provider: vault  # or aws-secrets-manager, azure-key-vault, gcp-secret-manager

    # Option C: Sealed Secrets
    backend: sealed-secrets
```

**Supported Secret Stores:**

| Provider | Integration Method | Notes |
|----------|-------------------|-------|
| HashiCorp Vault | External Secrets Operator | Most common in enterprise |
| AWS Secrets Manager | External Secrets Operator | If customer uses AWS |
| Azure Key Vault | External Secrets Operator | If customer uses Azure |
| GCP Secret Manager | External Secrets Operator | If customer uses GCP |
| Kubernetes Secrets | Direct | Simplest, for dev/small envs |
| Sealed Secrets | Bitnami controller | GitOps-friendly |

**ForgeWorks does NOT create or manage secrets directly. It consumes them.**

### 2.2 Container Registry (User's Choice)

ForgeWorks images are published to **GHCR** (GitHub Container Registry) as the default. Customers can mirror to their internal registry.

```yaml
# ForgeWorks Configuration - container registry
forgeworks:
  images:
    # Default: Pull from GHCR
    registry: ghcr.io/forge-works

    # Option: Customer's internal registry
    registry: harbor.corp.internal/forge-works
    pullSecret: regcred  # Pre-configured pull secret
```

**Supported Registries:**

| Registry | Default | Notes |
|----------|---------|-------|
| GHCR | ✅ Yes | Official ForgeWorks images |
| Harbor | Supported | Common enterprise choice |
| Artifactory | Supported | JFrog users |
| ECR | Supported | AWS customers |
| GCR/Artifact Registry | Supported | GCP customers |
| ACR | Supported | Azure customers |

### 2.3 Observability (User's Choice)

ForgeWorks exposes standard interfaces. Customers connect their existing observability stack.

```
┌─────────────────────────────────────────────────────────────────┐
│  FORGEWORKS OBSERVABILITY CONTRACT                               │
│                                                                  │
│  WHAT FORGEWORKS PROVIDES (Built-in):                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  /health         → Kubernetes liveness/readiness probes  │    │
│  │  /metrics        → Prometheus/OpenMetrics format         │    │
│  │  Structured logs → JSON to stdout                        │    │
│  │  Correlation IDs → X-Correlation-ID in all requests     │    │
│  │  Error codes     → Standardized FW-* codes              │    │
│  │  /api/v1/status  → Job, adapter, system status          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  WHAT USER BRINGS (Their Stack):                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Prometheus      → Scrapes /metrics                      │    │
│  │  Grafana         → Visualizes our metrics               │    │
│  │  Datadog/NewRelic→ Ingests our metrics                  │    │
│  │  ELK/Loki/Splunk → Ingests our logs                     │    │
│  │  PagerDuty       → Receives alerts from AlertManager    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  OPTIONAL ADD-ONS (Helm charts):                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  forgeworks-dashboards  → Pre-built Grafana dashboards   │    │
│  │  forgeworks-alerts      → Pre-built AlertManager rules   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. ForgeWorks Core Components

These are the components ForgeWorks deploys and manages.

### 3.1 Kubernetes Cluster Requirements

ForgeWorks requires a Kubernetes cluster (EKS, GKE, AKS, or on-prem). Minimum requirements:

| Requirement | Minimum | Recommended | Notes |
|-------------|---------|-------------|-------|
| Kubernetes Version | 1.27 | 1.29+ | For latest features |
| Nodes (Engine) | 2 | 3+ | For Kafka/Flink HA |
| Nodes (App) | 1 | 2+ | For backend/frontend |
| Node Memory | 8 GB | 16 GB | For Flink TaskManagers |
| Storage Class | gp3 or equivalent | gp3 with high IOPS | For Kafka persistence |

### 3.2 Namespace Strategy

```yaml
# ForgeWorks Namespaces
namespaces:
  forge-engine:
    purpose: Engine infrastructure (Kafka, Flink, Airflow)
    components:
      - strimzi-kafka
      - flink-operator
      - airflow
      - mlflow
      - redis (model cache)

  forge-works:
    purpose: Application layer
    components:
      - backend (FastAPI)
      - frontend (Next.js)
      - webhook-gateway
      - job-dispatcher

  forge-ml:
    purpose: ML workloads
    components:
      - training pods (ephemeral)
      - inference pods (if needed)
```

### 3.3 Component Specifications

#### Kafka (Strimzi)

```yaml
# forge-engine/kafka
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: forge-kafka
spec:
  kafka:
    version: 3.6.1
    replicas: 3  # HA
    resources:
      requests:
        memory: 4Gi
        cpu: 1000m
      limits:
        memory: 8Gi
        cpu: 2000m
    storage:
      type: persistent-claim
      size: 100Gi
      class: gp3-high-iops  # Or customer's equivalent
    config:
      auto.create.topics.enable: "false"
      default.replication.factor: 3
      min.insync.replicas: 2
```

#### Flink (Kubernetes Operator)

```yaml
# forge-engine/flink
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: forge-flink
spec:
  image: ghcr.io/forge-works/flink-job:latest  # Or internal registry
  flinkVersion: v1_18
  jobManager:
    resource:
      memory: 2Gi
      cpu: 1
  taskManager:
    replicas: 3
    resource:
      memory: 8Gi  # 6Gi for Flink heap
      cpu: 4
  job:
    state: running
    checkpointingMode: EXACTLY_ONCE
    checkpointInterval: 30000
```

#### Airflow (Helm)

```yaml
# forge-engine/airflow (values.yaml excerpt)
executor: KubernetesExecutor
webserver:
  replicas: 2
scheduler:
  replicas: 2
dags:
  persistence:
    enabled: true
    # Uses customer's storage class
logs:
  persistence:
    enabled: true
postgresql:
  enabled: false  # Use external PostgreSQL
externalDatabase:
  # Connects to customer's PostgreSQL
```

---

## 4. Storage Architecture

### 4.1 S3-Compatible Storage

ForgeWorks uses S3-compatible object storage for:
- Flink checkpoints
- Model artifacts
- Airflow logs
- Training data

**Options:**
- AWS S3
- MinIO (on-prem)
- Any S3-compatible storage

```yaml
forgeworks:
  storage:
    type: s3
    endpoint: s3.amazonaws.com  # or minio.internal:9000
    buckets:
      state: forge-works-state
      models: forge-works-models
      logs: forge-works-logs
```

### 4.2 Persistent Volumes

| Component | Storage Class | Size | Notes |
|-----------|---------------|------|-------|
| Kafka | gp3-high-iops | 100Gi/broker | High IOPS for throughput |
| Zookeeper | gp3 | 20Gi | Standard IOPS sufficient |
| PostgreSQL | gp3 | 50Gi | If in-cluster |
| Redis | gp3 | 20Gi | Model cache (warm tier) |

---

## 5. Security Architecture

### 5.1 No Assumed Trust

ForgeWorks operates with minimal assumptions about the network:

```yaml
# Network Policy: Default deny, explicit allow
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
  # All traffic blocked by default
```

### 5.2 Required RBAC

ForgeWorks service accounts need minimal permissions:

```yaml
# ForgeWorks Backend - minimal RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: forgeworks-backend
  namespace: forge-works
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "get", "list", "delete"]  # For job adapter
```

### 5.3 Pod Security

```yaml
# All ForgeWorks pods run as non-root
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

---

## 6. Deployment Configurations

### 6.1 Development (Minimal Resources)

```yaml
# dev profile
kafka:
  replicas: 1
  storage: 20Gi
  resources:
    memory: 2Gi
flink:
  taskManager:
    replicas: 1
    memory: 4Gi
airflow:
  executor: LocalExecutor  # Single pod
```

### 6.2 Production (High Availability)

```yaml
# prod profile
kafka:
  replicas: 3
  storage: 100Gi
  resources:
    memory: 8Gi
flink:
  taskManager:
    replicas: 3
    memory: 8Gi
  highAvailability: true
airflow:
  executor: KubernetesExecutor
  webserver:
    replicas: 2
  scheduler:
    replicas: 2
```

---

## 7. Cost Considerations

### Development Environment (~$300-400/month on AWS)

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| EKS Control Plane | 1 cluster | $72 |
| Nodes (3x t3.large) | Engine + App | $180 |
| Storage (200GB gp3) | Kafka + PVCs | $20 |
| S3 (50GB) | State, models | $2 |
| **Total** | | **~$275/month** |

### Production Environment (~$800-1200/month on AWS)

| Component | Spec | Monthly Cost |
|-----------|------|--------------|
| EKS Control Plane | 1 cluster | $72 |
| Nodes (6x m5.large) | Engine + App | $420 |
| Storage (1TB gp3) | Kafka + PVCs | $80 |
| S3 (200GB) | State, models | $5 |
| NAT Gateway (if needed) | 1-3 | $32-96 |
| **Total** | | **~$600-680/month** |

*Note: Costs vary significantly based on network scenario (Scenario B/C may have lower NAT costs but higher VPC endpoint costs)*

---

## 8. Integration Points

### 8.1 Webhook Ingestion

```
Customer's Source Control (GitHub/GitLab)
              │
              │ Webhook POST
              ▼
    ┌──────────────────┐
    │  Webhook Gateway │  ← ForgeWorks component
    │  /webhook/github │
    │  /webhook/argocd │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │      Kafka       │  ← ForgeWorks component
    │ forge.events.*   │
    └──────────────────┘
```

### 8.2 Control Plane Output

```
    ┌──────────────────┐
    │  Job Dispatcher  │  ← ForgeWorks component
    └────────┬─────────┘
             │ Generic Job Spec
             ▼
    ┌──────────────────┐
    │  Control Plane   │  ← Customer's (ArgoCD, Tekton, K8s Jobs)
    │     Adapter      │
    └────────┬─────────┘
             │
             ▼
    Customer's Kubernetes (Job execution)
```

---

## 9. Decision Alignment

This architecture implements the P0-P2 decisions:

| Decision | Implementation |
|----------|----------------|
| **P0-1:** Kafka Events | Strimzi Kafka in forge-engine namespace |
| **P0-2:** Generic Spec + Adapters | Job Dispatcher → Control Plane Adapters |
| **P0-3:** Airflow triggers training | Airflow with KubernetesExecutor |
| **P1-1:** Hybrid control plane discovery | Adapter Registry with user approval |
| **P1-2:** Tiered model loading | Hot (Flink) + Warm (Redis) + Cold (S3) |
| **P2-2:** Bring Your Own Stack observability | /health, /metrics, structured logs |

---

## References

- [BRAINSTORM.md](../planning/BRAINSTORM.md) - P0-P2 Decisions
- [GLUE_LAYER_EVOLUTION.md](../planning/GLUE_LAYER_EVOLUTION.md) - "Bring Your Own Stack" philosophy
- [TECH_STACK.md](../decisions/TECH_STACK.md) - Technology choices (GHCR, etc.)
- [ACTION_PLAN_PHASE-1.md](../roadmap/ACTION_PLAN_PHASE-1.md) - Engine Phase 1

---

*Architecture Document v2.0.0*
*Created: 2025-01-24*
*Revised: Aligned with "Bring Your Own Stack" philosophy*
