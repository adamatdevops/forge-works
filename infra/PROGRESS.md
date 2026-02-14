# ForgeWorks Infrastructure - Progress Tracker

> **Last Updated:** 2026-02-14
> **Current Phase:** Sprint I-6 (ForgeWorks Engine Deploy)

---

## Overall Progress

```
INFRASTRUCTURE DEPLOYMENT PROGRESS
═══════════════════════════════════════════════════════════════

✅ Sprint I-(-1): AWS Foundation              COMPLETE
   └── IAM Identity Center, EKS Cluster, kubectl configured

✅ Sprint I-0: Prerequisites & Config         COMPLETE
   └── Network A, gp3 storage, K8s Secrets, GHCR verified

✅ Sprint I-1: Namespaces & RBAC              COMPLETE
   └── 3 namespaces, 8 service accounts, RBAC, NetworkPolicies

✅ Sprint I-2: Operators                      COMPLETE
   └── Strimzi, Flink Operator, Cert-Manager installed

✅ Sprint I-3: Deploy Kafka Cluster           COMPLETE
   └── KRaft 4.1.1, 1 broker (dev), 10 topics, produce/consume ✓

✅ Sprint I-4: Deploy Flink Cluster           COMPLETE
   └── Flink 1.20.3, session cluster, STABLE

✅ Sprint I-5: Storage & Secrets              COMPLETE
   └── 6 secrets, 3 S3 buckets, IRSA (4 roles), verified

➡️ Sprint I-6: ForgeWorks Engine Deploy       NEXT
⬜ Sprint I-7: Validation                     PENDING

═══════════════════════════════════════════════════════════════
```

---

## Sprint Details

### Sprint I-(-1): AWS Foundation ✅

**Completed:** 2025-02-01

| Task | Status | Notes |
|------|--------|-------|
| AWS CLI update | ✅ | v2.19.2 |
| IAM Identity Center | ✅ | fw-admin, fw-infra, fw-deploy |
| Permission sets | ✅ | Least-privilege policies |
| EKS cluster | ✅ | forge-works-dev (1.31) |
| kubectl access | ✅ | Using fw-infra profile |

**Key Decisions:**
- Used IAM Identity Center (SSO) instead of legacy IAM users
- fw-infra profile has cluster admin (created cluster)
- fw-deploy needs RBAC mapping (pending)

---

### Sprint I-0: Prerequisites & Configuration ✅

**Completed:** 2025-02-01

| Task | Status | Result |
|------|--------|--------|
| kubectl access | ✅ | Working with fw-infra |
| Network scenario | ✅ | Scenario A (Standard) |
| Storage class | ✅ | gp3 (default) + EBS CSI Driver |
| Secrets backend | ✅ | K8s Secrets |
| Container registry | ✅ | GHCR (pull verified) |
| Config file | ✅ | forgeworks-config.yaml |

**Key Configurations:**
```yaml
Network:    Scenario A (Standard)
Storage:    gp3 (EBS CSI Driver)
Secrets:    Kubernetes Secrets
Registry:   ghcr.io/forge-works
```

---

### Sprint I-1: Namespaces & RBAC ✅

**Completed:** 2025-02-04

| Task | Status | Result |
|------|--------|--------|
| Create forge-engine namespace | ✅ | PSS: baseline |
| Create forge-works namespace | ✅ | PSS: restricted |
| Create forge-ml namespace | ✅ | PSS: baseline |
| Apply Pod Security Standards | ✅ | enforce + warn labels |
| Create service accounts | ✅ | 8 service accounts |
| Create RBAC roles and bindings | ✅ | Least-privilege |
| Create NetworkPolicies | ✅ | Default deny + allow rules |

**Manifests Created:**
```
infra/k8s/base/
├── kustomization.yaml
├── namespaces.yaml
├── service-accounts.yaml
├── rbac.yaml
└── network-policies.yaml
```

**Namespaces:**
| Namespace | Purpose | PSS Level |
|-----------|---------|-----------|
| forge-engine | Kafka, Flink, Airflow | baseline |
| forge-works | Backend, Frontend, Webhook | restricted |
| forge-ml | ML training/inference | baseline |

---

### Sprint I-2: Operators ✅

**Completed:** 2025-02-04

| Task | Status | Result |
|------|--------|--------|
| Install Strimzi Operator | ✅ | v0.50.0 |
| Install Flink Operator | ✅ | v1.10.0 |
| Install Cert-Manager | ✅ | v1.16.2 |
| Verify CRDs | ✅ | All CRDs registered |

**Operators Running:**
```
NAMESPACE       NAME                                        READY   STATUS
forge-engine   strimzi-cluster-operator-59889b9d49-g45l7   1/1     Running
forge-engine   flink-kubernetes-operator-6b55b4664-mhhrk   2/2     Running
cert-manager   cert-manager-74b56b6655-mhk8m               1/1     Running
cert-manager   cert-manager-cainjector-55d94dc4cc-hx4sb    1/1     Running
cert-manager   cert-manager-webhook-564f647c66-2dzjh       1/1     Running
```

**CRDs Installed:**
| Operator | CRDs |
|----------|------|
| Strimzi | kafkas, kafkatopics, kafkausers, kafkaconnects, kafkabridges, kafkamirrormaker2s, kafkanodepools, kafkarebalances, strimzipodsets |
| Flink | flinkdeployments, flinksessionjobs, flinkstatesnapshots |
| Cert-Manager | certificates, certificaterequests, issuers, clusterissuers, challenges, orders |

---

### Sprint I-3: Deploy Kafka Cluster ✅

**Completed:** 2025-02-12

| Task | Status | Result |
|------|--------|--------|
| Update manifests to KRaft mode | ✅ | Removed ZooKeeper |
| Fix API deprecation (v1beta2 → v1) | ✅ | All CRs on v1 |
| Deploy Kafka cluster (dev overlay) | ✅ | 1 broker, 10Gi gp3 |
| Add cluster labels to topics | ✅ | All 10 topics READY |
| Produce/consume test | ✅ | `hello-forgeworks` passed |

**Kafka Cluster:**
```
Name:           forge-kafka
Mode:           KRaft (no ZooKeeper)
Version:        4.1.1
Metadata:       4.1-IV1
Brokers:        1 (dev)
Storage:        10Gi gp3
Topics:         10 (all READY, RF=1, 2 partitions)
```

**Issues Resolved:**
- Kafka 3.9.0 unsupported → updated to 4.1.1
- Missing `strimzi.io/cluster` label on topics → added
- `v1beta2` API deprecated → migrated to `v1`
- `kubectl exec <<<` stdin issue → used `sh -c` with pipe

---

### Sprint I-4: Deploy Flink Cluster ✅

**Completed:** 2025-02-13

| Task | Status | Result |
|------|--------|--------|
| Create Flink session cluster manifests | ✅ | Base + dev/prod overlays |
| Deploy Flink cluster (dev overlay) | ✅ | 1 JM, 1 TM (on-demand) |
| Verify Flink cluster health | ✅ | STABLE, REST API responding |

**Flink Cluster:**
```
Name:           forge-flink
Mode:           Session Cluster
Version:        1.20.3
Lifecycle:      STABLE
JobManager:     1 (1g mem, 0.5 cpu)
TaskManagers:   On-demand (1g mem, 0.5 cpu)
Kafka:          forge-kafka-kafka-bootstrap:9092
Dashboard:      port-forward svc/forge-flink-rest 8081
```

---

### Sprint I-5: Storage & Secrets ✅

**Completed:** 2026-02-14

| Task | Status | Result |
|------|--------|--------|
| Verify storage class | ✅ | gp3 default (done in Sprint I-0) |
| Create K8s secrets | ✅ | 6 secrets across 3 namespaces |
| Create S3 buckets | ✅ | fw-state-dev, fw-models-dev, fw-logs-dev |
| Configure IRSA | ✅ | 3 IAM policies, 4 IAM roles, 4 SA annotations |
| Verify S3 access | ✅ | Write/read round-trip via flink-sa passed |

**Secrets Created:**
| Secret | Namespace | Keys |
|--------|-----------|------|
| forge-postgres-credentials | forge-engine | 5 (host, port, db, user, pass) |
| forge-redis-credentials | forge-engine | 3 (host, port, pass) |
| forge-postgres-credentials | forge-works | 5 |
| forge-redis-credentials | forge-works | 3 |
| forge-app-config | forge-works | 2 (jwt-secret, secret-key) |
| forge-ml-config | forge-ml | 1 (model-registry-url) |

**S3 Buckets:**
| Bucket | Purpose | Versioning |
|--------|---------|------------|
| fw-state-dev | Flink checkpoints, savepoints, HA | Enabled |
| fw-models-dev | ML model artifacts | - |
| fw-logs-dev | Application logs | - |

**IRSA Configuration:**
| Service Account | Namespace | IAM Role | S3 Access |
|----------------|-----------|----------|-----------|
| flink-sa | forge-engine | fw-forge-engine-flink-sa | State + Logs (RW) |
| airflow-sa | forge-engine | fw-forge-engine-airflow-sa | State + Logs (RW) |
| ml-runner-sa | forge-ml | fw-forge-ml-ml-runner-sa | Models + Logs (RW) |
| ml-inference-sa | forge-ml | fw-forge-ml-ml-inference-sa | Models (RO) |

**Issues Resolved:**
- `fw-infra` lacks IAM permissions → split-profile approach (fw-admin for IAM, fw-infra for kubectl)
- AWS CLI v2 pager blocks scripts → `export AWS_PAGER=""`
- `eksctl create iamserviceaccount` needs both IAM + EKS access → manual IAM roles + kubectl annotate
- `amazon/aws-cli` entrypoint overrides `sh -c` → use container command override in pod spec

**Manifests Created:**
```
infra/k8s/base/secrets/
├── create-secrets.sh          # Secret creation script
└── README.md                  # Secret documentation

infra/k8s/base/irsa/
├── setup-irsa.sh              # IRSA setup script (split-profile)
└── README.md                  # IRSA documentation

infra/iam/
├── policies/
│   ├── fw-engine-s3-policy.json
│   ├── fw-ml-s3-policy.json
│   └── fw-ml-inference-s3-policy.json
└── trust-policies/
    ├── fw-forge-engine-flink-sa-trust.json
    ├── fw-forge-engine-airflow-sa-trust.json
    ├── fw-forge-ml-ml-runner-sa-trust.json
    └── fw-forge-ml-ml-inference-sa-trust.json
```

---

## Cluster Information

| Property | Value |
|----------|-------|
| **Cluster Name** | forge-works-dev |
| **Region** | us-east-1 |
| **K8s Version** | 1.31 |
| **Node Group** | fw-workers |
| **Node Type** | t3.large |
| **Node Count** | 3 (min: 2, max: 5) |
| **VPC** | vpc-04eeb7b50bd45e731 |

---

## AWS Profiles

| Profile | Purpose | EKS Access |
|---------|---------|------------|
| fw-admin | IAM Identity Center management | No |
| fw-infra | Infrastructure provisioning | ✅ Cluster Admin |
| fw-deploy | Day-to-day deployments | ⚠️ Needs RBAC mapping |

---

## Files Reference

| File | Purpose |
|------|---------|
| `forgeworks-config.yaml` | Main configuration file |
| `k8s/base/` | Kubernetes base manifests |
| `EKS_OPERATIONS.md` | Cluster operations guide |
| `ACTION_PLAN_INFRASTRUCTURE.md` | Sprint task lists |
| `PREREQUISITES.md` | Requirements checklist |
| `ARCHITECTURE.md` | System design |
| `CHECKLIST_AWS_FOUNDATION.md` | AWS setup checklist |

---

## Cost Tracking

| State | Daily Cost | Monthly Cost |
|-------|------------|--------------|
| Running (3 nodes) | ~$8.40 | ~$252 |
| Scaled down (0 nodes) | ~$2.40 | ~$72 |
| Deleted | $0 | $0 |

**Cost-saving commands:**
```bash
# Scale down (saves ~$6/day)
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=0 \
  --profile fw-infra --region us-east-1

# Scale up
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=2,maxSize=5,desiredSize=3 \
  --profile fw-infra --region us-east-1
```

---

*Progress Tracker v1.4.0*
*Updated: 2026-02-14*
