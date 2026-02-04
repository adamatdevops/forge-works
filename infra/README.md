# ForgeWorks Infrastructure

> **Purpose:** AWS EKS-based infrastructure for ForgeWorks platform
> **Status:** 🔄 In Progress (Milestone 001)
> **Last Updated:** 2025-01-23

---

## Architecture Overview

ForgeWorks runs on AWS EKS with the following components:

```
infra/
├── README.md                 # This file
├── eks/                      # EKS cluster (Terraform)
├── kafka/                    # Kafka via Strimzi ✅ READY
├── flink/                    # Flink Kubernetes Operator
├── airflow/                  # Airflow via Helm
├── postgres/                 # PostgreSQL (in-cluster or RDS)
├── redis/                    # Redis for model caching
├── monitoring/               # Prometheus + Grafana
├── forge-works/              # Application deployments
└── scripts/                  # Deployment automation
```

---

## Component Status

| Component | Status | Manifests | Notes |
|-----------|--------|-----------|-------|
| **Kafka** | ✅ Ready | `kafka/` | Strimzi, 10 topics, dev/prod overlays |
| **EKS** | ⏳ Pending | `eks/` | Terraform modules needed |
| **Flink** | ⏳ Pending | `flink/` | Operator + JobManager |
| **Airflow** | ⏳ Pending | `airflow/` | Helm chart values |
| **PostgreSQL** | ⏳ Pending | `postgres/` | Bitnami Helm or RDS |
| **Redis** | ⏳ Pending | `redis/` | Model cache tier |
| **Monitoring** | ⏳ Pending | `monitoring/` | kube-prometheus-stack |
| **ForgeWorks App** | ⏳ Pending | `forge-works/` | Backend, Frontend, Gateway |

---

## Quick Start

### Prerequisites

```bash
# AWS CLI configured
aws sts get-caller-identity

# kubectl installed
kubectl version --client

# Helm installed
helm version

# Kustomize installed
kustomize version
```

### Deploy to Development

```bash
# 1. Deploy Kafka
kubectl apply -k infra/kafka/overlays/dev

# 2. Verify
kubectl get pods -n forge-engine
kubectl get kafkatopic -n forge-engine
```

### Deploy to Production

```bash
# 1. Deploy Kafka (3 brokers)
kubectl apply -k infra/kafka/overlays/prod

# 2. Verify
kubectl get pods -n forge-engine
```

---

## Environment Configuration

### Development (Dev Overlay)
- 1 Kafka broker (minimal)
- 2 partitions per topic
- Reduced resource requests
- Suitable for local testing

### Production (Prod Overlay)
- 3 Kafka brokers (HA)
- 6 partitions per topic
- Full resource allocation
- Multi-AZ deployment

---

## Namespace Strategy

| Namespace | Purpose | Components |
|-----------|---------|------------|
| `forge-engine` | Engine infrastructure | Kafka, Flink, Airflow |
| `forge-works` | Application layer | Backend, Frontend, Gateway |
| `monitoring` | Observability | Prometheus, Grafana |
| `kafka` | Strimzi Operator | Cluster operator only |

---

## Directory Details

### `/kafka` ✅ Complete
Strimzi-based Kafka deployment with:
- 3-broker production cluster
- 10 pre-defined topics with schemas
- JMX metrics for Prometheus
- Dev/Prod Kustomize overlays

### `/eks` (Planned)
Terraform modules for:
- EKS cluster
- VPC, subnets, security groups
- IAM roles (IRSA)
- Node groups (on-demand + spot)

### `/flink` (Planned)
Flink Kubernetes Operator with:
- FlinkDeployment CRDs
- RocksDB state backend
- S3 checkpoint storage
- Job definitions

### `/airflow` (Planned)
Apache Airflow via Helm:
- Celery executor
- S3 DAG sync
- PostgreSQL metadata
- MLflow integration

### `/monitoring` (Planned)
kube-prometheus-stack with:
- Prometheus
- Grafana dashboards
- AlertManager
- ServiceMonitors

---

## Deployment Order

```
1. Prerequisites
   ├── EKS cluster (infra/eks)
   ├── Storage classes (gp3)
   └── Secrets management

2. Data Layer
   ├── PostgreSQL (infra/postgres)
   └── Redis (infra/redis)

3. Engine Layer
   ├── Kafka (infra/kafka) ✅
   ├── Flink (infra/flink)
   └── Airflow (infra/airflow)

4. Application Layer
   ├── Backend (infra/forge-works)
   ├── Frontend (infra/forge-works)
   └── Webhook Gateway (infra/forge-works)

5. Observability
   └── Prometheus + Grafana (infra/monitoring)
```

---

## References

- [Milestone 001: Infrastructure Foundation](../roadmap/MILESTONE_001_INFRA_FOUNDATION.md)
- [ADR-007: Kafka Deployment](../adr/007-kafka-deployment.md)
- [ACTION_PLAN_PHASE-1.md](../roadmap/ACTION_PLAN_PHASE-1.md)

---

*Infrastructure setup initiated: 2025-01-23*
