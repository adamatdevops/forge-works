# Changelog

All notable changes to ForgeWorks Infrastructure will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-05-06

### Breaking

- **`NormalizedConfig.schema_version` 1 → 2.** Three CUE `#Workload` fields renamed from camelCase to snake_case (`crashLoops` → `crash_loops`, `hasLivenessProbe` → `has_liveness_probe`, `hasReadinessProbe` → `has_readiness_probe`). `resource_type` is now a closed enum codified in CUE (`"workload" | "service" | "pipeline" | "deployment"`). All Pydantic serialization uses `exclude_none=True` so Python `None` aligns with CUE "field absent" — null values are no longer published.
- Image tag `:dev-v2` is no longer produced by CI. All Deployments reference `:main-latest` (rolling) and `:sha-<short>` (immutable) is also published.

### Added — Sprint E5.1c (Codex feedback close-out)

- **CUE↔Pydantic schema fidelity gate** — `tests/test_cue_schema.py` validates every normalizer's output against `cue vet -d '#NormalizedConfig'`. CI workflow installs CUE CLI v0.16.0 so any Pydantic ↔ CUE drift fails the build. (Codex Block #1)
- **DLQ pipeline** — every failure path publishes a structured `DLQEvent` envelope to `forge.dlq.events` *before* committing the consumer offset. New module `app/dlq.py` defines five error codes:
  - `FW-NL-PARSE-001` — JSON decode failure
  - `FW-NL-NORM-001` — normalizer raised
  - `FW-NL-S3-001` — cold-tier write failed
  - `FW-NL-REDIS-001` — hot-tier write failed
  - `FW-NL-SRC-001` — source mismatch (per-pod isolation breach)
  New metric `forgeworks_normalizer_dlq_published_total{error_code}`. `store.put` now raises `S3WriteError` / `RedisWriteError` instead of silently logging. (Codex Block #2)
- **Per-source isolation guard** — new env `FW_EXPECTED_SOURCE`. Each per-source pod rejects events whose `source` field does not match its expected value, routing them to DLQ with `FW-NL-SRC-001`. Empty default preserves backward-compat. (Codex Block #3)
  - `normalizer-config` → `FW_EXPECTED_SOURCE=kubernetes`
  - `normalizer-terraform-config` → `FW_EXPECTED_SOURCE=terraform`
  - `normalizer-github-actions-config` → `FW_EXPECTED_SOURCE=github-actions`
- **IAM codified in `infra/iam/`** — pulled live trust + managed policy JSON for the three new normalizer IRSA roles created in Sprint E5.1b. New `infra/iam/scripts/diff-iam.sh` reports drift between repo and AWS for every artifact under the directory; current run = zero drift across 7 trust policies + 6 managed policies. (Codex Should-fix #1)
- New `process_message` helper extracted from `consume_loop` for unit testability without spinning up Kafka.
- Normalizer pyproject bumped 0.1.0 → 0.2.0.

### Changed

- **Dockerfile single source-of-truth** — builder stage now copies `app/` before `pip install .` (so the package builds with `[tool.setuptools] packages = ["app"]`) and the runtime stage drops the redundant `COPY app/ ./app/`. Code now lives in exactly one location: `/usr/local/lib/python3.11/site-packages/app/`. (Codex Should-fix #5)
- All three normalizer Deployment ConfigMaps add `FW_KAFKA_DLQ_TOPIC: "forge.dlq.events"`.

### Tests

- `src/normalizer/tests/`: 67 passing — 39 unchanged + 9 schema-fidelity + 10 DLQ + 9 process-message.
- `src/webhook-gateway/tests/`: 38 unchanged, all passing (regression check).

### Verified (pre-commit)

- `cue vet` validation passes for every supported normalizer output type (kubernetes deployment + service, terraform ECS task + ALB listener, GHA workflow_run + workflow_job).
- Negative-path tests confirm CUE rejects: `schema_version=1`, camelCase resource fields, unknown `resource_type`.
- `store.put` propagates Redis and S3 failures (verified via mocked-boto3 tests).
- `process_message` routes every failure class to DLQ with the correct error code (5 paths × happy-path covered).
- `infra/iam/scripts/diff-iam.sh` clean — repo matches live AWS state for all IRSA artifacts.

### Deferred (explicitly out of scope, captured for follow-up)

- Terraform CPU heuristic at `f >= 16` boundary — to be replaced by producer-side `cpu_unit` envelope tag in E5.3 (producer simulator sprint). Codex Should-fix #3.
- GHA routing for `check_run` / `check_suite` / `workflow_dispatch` — defer until normalizer parsers exist for those payload shapes. Codex Should-fix #2.
- Image supply-chain (SBOM / provenance / cosign signing) — dedicated CI hardening sprint. Codex Should-fix #4.
- Per-source observability metric labels (latency / error taxonomy) — fold into E5.2 Pattern Matcher integration. Codex Worth-discussing #3.
- Cross-correlation contract for `workflow_run` ↔ `workflow_job` — design in E5.2 alongside the Pattern Matcher's stateful merge logic. Codex Worth-discussing #1.
- `query.py` Pattern Matcher integration docstring — fix during E5.2.

### Infrastructure Components (delta from 0.7.2)

| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| Normalizer (image) | `:main-latest`, `:sha-<short>` | forge-engine | Deployed (3 pods) |
| Normalizer (package) | 0.2.0 | n/a | Schema v2 |
| `infra/iam/` artifacts | 7 trust + 6 policies codified | n/a | Diff = 0 |

---

## [0.7.2] - 2026-05-06

### Added
- **Sprint E5.1b — Terraform + GitHub Actions normalizers.** The configuration normalization pipeline now supports two additional source systems alongside Kubernetes.
  - **Code**: `TerraformNormalizer` maps ECS task definitions / services and K8s-via-TF resources to canonical `#Workload` / `#Service` records (CPU unit conversion: AWS units → millicores; memory passthrough). `GitHubActionsNormalizer` maps `workflow_run` / `workflow_job` webhook payloads to canonical `#Pipeline` / `#Stage` records. Pydantic `Pipeline` + `Stage` models added to mirror the existing CUE schema.
  - **Webhook routing**: GitHub `workflow_run` / `workflow_job` events now route to a dedicated topic (`forge.events.github_actions`); other GitHub events keep going to `forge.events.github`.
  - **Topics**: New Strimzi `KafkaTopic` resources `forge.events.terraform` and `forge.events.github_actions` (6 partitions, 3 replicas, 7-day retention — same shape as existing event topics).
  - **IRSA — Terraform pod**: IAM role `fw-forge-engine-normalizer-terraform-sa` (OIDC trust scoped to `system:serviceaccount:forge-engine:normalizer-terraform-sa`) + dedicated policy `fw-engine-normalizer-terraform-s3-access` (least-privilege on `s3://fw-state-dev/normalizer/configs/terraform/*`).
  - **IRSA — GitHub Actions pod**: IAM role `fw-forge-engine-normalizer-github-actions-sa` + policy `fw-engine-normalizer-github-actions-s3-access` (scoped to `s3://fw-state-dev/normalizer/configs/github-actions/*`).
  - **K8s manifests**: Per-source pods (Path B) — separate ConfigMap + Deployment + Service + ServiceAccount for `normalizer-terraform` and `normalizer-github-actions`. Each pod consumes only its own input topic via `FW_KAFKA_INPUT_TOPIC` and uses a distinct consumer group.
  - **CI**: New GitHub Actions workflow `normalizer-image.yml` builds + pushes the normalizer image to GHCR on every push to `main` (publishes both `:sha-<short>` and `:main-latest` tags). Runs unit tests and Hadolint before pushing.

### Changed
- All three normalizer Deployments now reference `ghcr.io/adamatdevops/forge-works/normalizer:main-latest` (was `:dev-v2`). The new CI workflow publishes this tag automatically; `imagePullPolicy: Always` ensures `kubectl rollout restart` picks it up.
- Webhook gateway ConfigMap adds `FW_KAFKA_TOPIC_GITHUB_ACTIONS=forge.events.github_actions`.

### Verified
- 39 normalizer unit tests pass (30 Terraform + 9 GitHub Actions).
- 38 webhook-gateway tests pass (33 existing + 5 new GHA-routing assertions).
- IRSA round-trip from inside the Terraform normalizer pod confirms STS identity = `assumed-role/fw-forge-engine-normalizer-terraform-sa`; PutObject / GetObject / DeleteObject under the scoped prefix all 200.
- GitHub Actions pod IRSA verification deferred until the first CI run produces the `main-latest` image (pod currently in `ImagePullBackOff` — expected pre-publish).

### Notes
- Producer simulator for Terraform / GHA event sources captured as TODO for E5.3 (or later). Until then, end-to-end exercises rely on hand-crafted JSON published into the source topics.

### Infrastructure Components (delta from 0.7.1)
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| IRSA | 7 roles (was 5) | forge-engine, forge-ml | Active |
| KafkaTopics | +2 (`forge.events.terraform`, `forge.events.github_actions`) | forge-engine | Created |
| Normalizer Deployments | 3 (was 1) | forge-engine | Two new pods deployed |

---

## [0.7.1] - 2026-05-05

### Added
- **Normalizer IRSA — closes Sprint E5.1a open item.** The configuration normalizer can now write to S3 cold-tier.
  - New IAM role `fw-forge-engine-normalizer-sa` with OIDC trust scoped to `system:serviceaccount:forge-engine:normalizer-sa`.
  - New dedicated IAM policy `fw-engine-normalizer-s3-access` (least-privilege: `s3:PutObject`, `s3:GetObject`, `s3:AbortMultipartUpload` on `s3://fw-state-dev/normalizer/configs/*`, plus prefix-conditioned `s3:ListBucket`).
  - K8s ServiceAccount `normalizer-sa` in `forge-engine` with the IRSA annotation.
  - Deployment `normalizer` now uses `serviceAccountName: normalizer-sa`.

### Changed
- **`flink-sa` IRSA codified in repo.** The `eks.amazonaws.com/role-arn` annotation pointing to `fw-forge-engine-flink-sa` was previously applied directly to the live cluster. The manifest in `infra/k8s/base/service-accounts.yaml` now matches cluster state — no functional change, repo is reproducible from git.

### Verified
- STS round-trip from inside the normalizer pod returns the expected role ARN.
- `s3:ListBucket` (prefix-conditioned) and `s3:PutObject` / `s3:GetObject` succeed end-to-end against `s3://fw-state-dev/normalizer/configs/*`.
- IRSA smoke-test object created and removed during verification — bucket prefix left clean.

### Infrastructure Components (delta from 0.7.0)
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| IRSA | 5 roles (was 4) | forge-engine, forge-ml | Active |

---

## [0.7.0] - 2026-03-02

### Added
- **Sprint I-7: Envoy Gateway**
  - Installed Envoy Gateway v1.7.0 via Helm (CNCF Gateway API implementation)
  - Created GatewayClass `eg` with Envoy Gateway controller
  - Created Gateway resource `forgeworks-gateway` with HTTP listener on port 80
  - Created 3 HTTPRoutes: backend-api (/api/*), webhook-gateway (/webhook/*), frontend (/* catch-all)
  - AWS Classic Load Balancer auto-provisioned with external endpoint
  - Kustomize base/overlay structure for envoy-gateway manifests
  - Namespace label `forgeworks.io/gateway=enabled` for route attachment

### Changed
- Updated NetworkPolicies: `ingress-nginx` → `envoy-gateway-system` (3 policies)
  - `allow-backend-ingress`, `allow-frontend-ingress`, `allow-webhook-gateway-ingress`

### Fixed
- GatewayClass `eg` not auto-created by Helm chart → manual creation required
- Kustomize security policy blocks cross-directory file references → consolidated routes into base/

### Infrastructure Components
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| Envoy Gateway | 1.7.0 | envoy-gateway-system | Running |
| Gateway (forgeworks-gateway) | - | envoy-gateway-system | Programmed |
| Kafka (KRaft) | 4.1.1 | forge-engine | READY |
| Flink (Session) | 1.20.3 | forge-engine | STABLE |
| Redis (Standalone) | 8.6.0 | forge-engine | Running |
| PostgreSQL | 18.2 | forge-engine | Running |
| Strimzi Operator | 0.50.0 | forge-engine | Running |
| Flink Operator | 1.10.0 | forge-engine | Running |
| Cert-Manager | 1.16.2 | cert-manager | Running |
| IRSA | 4 roles | forge-engine, forge-ml | Active |
| S3 Buckets | 3 | us-east-1 | Created |
| K8s Secrets | 6 | all namespaces | Created |

---

## [0.6.0] - 2026-02-15

### Added
- **Sprint I-6: Data Layer Deploy**
  - Deployed Redis via Bitnami Helm chart (forge-redis, standalone mode, v8.6.0)
  - Deployed PostgreSQL via Bitnami Helm chart (forge-postgres, v18.2)
  - Both using existing K8s secrets from Sprint I-5 (existingSecret pattern)
  - Full infrastructure validation: all 7 sprints complete

### Fixed
- Wrong Helm release name for Redis (`forge-engine` → `forge-redis`) — uninstall/reinstall
- Missing `architecture=standalone` flag caused replication mode with no master pod
- Bitnami chart `master.serviceAccount` doesn't control pod SA — use top-level `serviceAccount.create=true`
- Strimzi operator pod label mismatch: uses `strimzi.io/kind=cluster-operator` not `app.kubernetes.io/name`

### Infrastructure Components
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| Kafka (KRaft) | 4.1.1 | forge-engine | READY |
| Flink (Session) | 1.20.3 | forge-engine | STABLE |
| Redis (Standalone) | 8.6.0 | forge-engine | Running |
| PostgreSQL | 18.2 | forge-engine | Running |
| Strimzi Operator | 0.50.0 | forge-engine | Running |
| Flink Operator | 1.10.0 | forge-engine | Running |
| Cert-Manager | 1.16.2 | cert-manager | Running |
| IRSA | 4 roles | forge-engine, forge-ml | Active |
| S3 Buckets | 3 | us-east-1 | Created |
| K8s Secrets | 6 | all namespaces | Created |

---

## [0.5.0] - 2026-02-14

### Added
- **Sprint I-5: Storage & Secrets**
  - Created 6 K8s secrets across 3 namespaces (postgres, redis, app-config, ml-config)
  - Created 3 S3 buckets: fw-state-dev (versioned), fw-models-dev, fw-logs-dev
  - Configured OIDC provider for EKS IRSA
  - Created 3 IAM policies (fw-engine-s3-access, fw-ml-s3-access, fw-ml-inference-s3-access)
  - Created 4 IAM roles with OIDC trust policies for IRSA
  - Annotated 4 service accounts with IAM role ARNs
  - Created `create-secrets.sh` script with dry-run support
  - Created `setup-irsa.sh` script with split-profile approach (fw-admin + fw-infra)
  - Verified full IRSA chain: Pod → SA → OIDC → IAM Role → S3 (write/read round-trip)

### Fixed
- AWS CLI v2 pager blocking script output → added `export AWS_PAGER=""`
- `fw-infra` lacks IAM permissions → split-profile approach for IRSA setup
- `eksctl create iamserviceaccount` unauthorized → manual IAM roles + kubectl annotate
- `amazon/aws-cli` entrypoint blocks `sh -c` → container command override in pod spec

### Infrastructure Components
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| Kafka (KRaft) | 4.1.1 | forge-engine | READY |
| Flink (Session) | 1.20.3 | forge-engine | STABLE |
| Strimzi Operator | 0.50.0 | forge-engine | Running |
| Flink Operator | 1.10.0 | forge-engine | Running |
| Cert-Manager | 1.16.2 | cert-manager | Running |
| IRSA | 4 roles | forge-engine, forge-ml | Active |
| S3 Buckets | 3 | us-east-1 | Created |
| K8s Secrets | 6 | all namespaces | Created |

---

## [0.4.0] - 2025-02-13

### Added
- **Sprint I-4: Deploy Flink Cluster**
  - Created FlinkDeployment CR for session cluster mode
  - Configured checkpointing, HA, restart strategy, Kafka integration
  - Dev overlay: 1 JobManager (1g), TaskManagers on-demand (1g)
  - Prod overlay: 1 JobManager (2g), 2 TaskManagers (2g)

### Infrastructure Components
| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| Kafka (KRaft) | 4.1.1 | forge-engine | READY |
| Flink (Session) | 1.20.3 | forge-engine | STABLE |
| Strimzi Operator | 0.50.0 | forge-engine | Running |
| Flink Operator | 1.10.0 | forge-engine | Running |
| Cert-Manager | 1.16.2 | cert-manager | Running |

---

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
- Sprint I-6: ForgeWorks Engine Deployment
- Sprint I-7: Validation & Testing
