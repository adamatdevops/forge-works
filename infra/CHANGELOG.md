# Changelog

All notable changes to ForgeWorks Infrastructure will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-02-12

### Added
- **Sprint I-3: Deploy Kafka Cluster**
  - Deployed Kafka in KRaft mode (no ZooKeeper) via Strimzi
  - Created `KafkaNodePool` CR for combined broker+controller roles
  - Deployed 10 ForgeWorks topics (events, jobs, insights, learning, DLQ)
  - Added KRaft-specific Prometheus metrics
  - Dev overlay: 1 broker, 10Gi storage, reduced resources

### Changed
- Upgraded Kafka version from 3.9.0 to **4.1.1** (Strimzi 0.50.0 requirement)
- Migrated all Strimzi CRs from `v1beta2` to **`v1`** API
- Updated `commonLabels` to `labels` in Kafka kustomization files
- Removed ZooKeeper configuration and metrics
- Added `strimzi.io/cluster` label to all KafkaTopic CRs

### Fixed
- Kafka version incompatibility: Strimzi 0.50.0 only supports Kafka 4.x
- Topics not reconciling due to missing cluster label
- Removed unused `namespace.yaml` from Kafka kustomization

### Infrastructure Components
| Component | Version | Namespace |
|-----------|---------|-----------|
| Kafka (KRaft) | 4.1.1 | forge-engine |
| Strimzi Operator | 0.50.0 | forge-engine |
| Flink Operator | 1.10.0 | forge-engine |
| Cert-Manager | 1.16.2 | cert-manager |

---

## [0.2.0] - 2025-02-04

### Added
- **Sprint I-1: Namespaces & RBAC**
  - Created 3 namespaces: `forge-engine`, `forge-works`, `forge-ml`
  - Applied Pod Security Standards (baseline/restricted)
  - Created 8 service accounts for all components
  - Implemented RBAC with least-privilege permissions
  - Added NetworkPolicies with default-deny and specific allow rules
  - Created Kustomize base manifests in `k8s/base/`

- **Sprint I-2: Operators**
  - Installed Strimzi Kafka Operator v0.50.0
  - Installed Flink Kubernetes Operator v1.10.0
  - Installed Cert-Manager v1.16.2 (Flink dependency)
  - Verified all CRDs registered and operators running

### Changed
- Updated `PROGRESS.md` to v1.1.0 with Sprint I-1 and I-2 completion
- Updated `ACTION_PLAN_INFRASTRUCTURE.md` with completed tasks

### Infrastructure Components
| Component | Version | Namespace |
|-----------|---------|-----------|
| Strimzi Operator | 0.50.0 | forge-engine |
| Flink Operator | 1.10.0 | forge-engine |
| Cert-Manager | 1.16.2 | cert-manager |

---

## [0.1.0] - 2025-02-01

### Added
- **Sprint I-(-1): AWS Foundation**
  - Configured IAM Identity Center with SSO profiles
  - Created permission sets: fw-admin, fw-infra, fw-deploy
  - Provisioned EKS cluster `forge-works-dev` (v1.31)
  - Configured kubectl access via fw-infra profile

- **Sprint I-0: Prerequisites & Configuration**
  - Identified network scenario: A (Standard)
  - Configured gp3 StorageClass with EBS CSI Driver
  - Selected Kubernetes Secrets as secrets backend
  - Verified GHCR container registry access
  - Created `forgeworks-config.yaml` configuration file

### Documentation
- Created `ARCHITECTURE.md` - System design
- Created `ACTION_PLAN_INFRASTRUCTURE.md` - Sprint task lists
- Created `PREREQUISITES.md` - Requirements checklist
- Created `EKS_OPERATIONS.md` - Cluster operations guide
- Created `PROGRESS.md` - Progress tracker
- Created `CHECKLIST_AWS_FOUNDATION.md` - AWS setup checklist

### Infrastructure
| Resource | Value |
|----------|-------|
| Cluster | forge-works-dev |
| Region | us-east-1 |
| K8s Version | 1.31 |
| Node Type | t3.large |
| Node Count | 3 (2-5) |

---

## [Unreleased]

### Planned
- Sprint I-4: Deploy Flink Cluster
- Sprint I-5: Storage & Secrets Integration
- Sprint I-6: ForgeWorks Engine Deployment
- Sprint I-7: Validation & Testing
