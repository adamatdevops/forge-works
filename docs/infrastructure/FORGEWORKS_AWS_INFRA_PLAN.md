# ForgeWorks AWS Infrastructure Action Plan

> **Project:** ForgeWorks - Internal Developer Platform
> **Duration:** 45 Days
> **Budget:** ~$150-155 USD
> **Status:** Planning

---

## Executive Summary

This document outlines the infrastructure architecture and implementation plan for deploying ForgeWorks on AWS EKS. ForgeWorks serves as "The Glue" between DevOps tools, and the infrastructure must support its core capabilities: webhook ingestion, cross-tool correlation, ML analysis, and real-time event broadcasting.

---

## Objectives

### Primary Objectives

| # | Objective | Success Indicator |
|---|-----------|-------------------|
| 1 | Deploy ForgeWorks on production-like EKS | Application accessible via HTTPS |
| 2 | Establish GitOps-driven deployment pipeline | All changes via Git, no kubectl applies |
| 3 | Validate Forge Adapters in cloud environment | GitHub → K8s correlation working |
| 4 | Implement cost-aware, ephemeral infrastructure | Spot instances, scale-to-zero capability |
| 5 | Create repeatable infrastructure-as-code | Single command cluster provisioning |

### Secondary Objectives

- Practice Day-2 operations (upgrades, scaling, recovery)
- Document architecture decisions for portfolio
- Establish baseline metrics and observability
- Test ForgeWorks under realistic network conditions

---

## Criteria

### Infrastructure Criteria

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| **Cost Efficiency** | < $160/45 days | Budget constraint |
| **Availability** | Single-AZ acceptable | Dev/test environment |
| **Scalability** | 0-3 nodes dynamic | Scale-to-zero when idle |
| **Security** | Private app, public ingress | Protect internal services |
| **Recoverability** | < 30 min full rebuild | Ephemeral mindset |
| **Observability** | Metrics + Logs + Traces | Debug and monitor ForgeWorks |

### ForgeWorks-Specific Criteria

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| **Webhook Ingestion** | Public endpoint with TLS | GitHub/external webhooks |
| **Database** | Managed PostgreSQL | ForgeWorks data persistence |
| **Real-time Events** | WebSocket support | Dashboard live updates |
| **ML Workloads** | CPU-based inference | No GPU required for MVP |
| **Secrets Management** | Vault + GitHub Secrets | Secure credential handling |

---

## Stack

### Infrastructure Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **IaC** | OpenTofu | 1.6+ | Infrastructure provisioning |
| **IaC Wrapper** | Terragrunt | 0.55+ | DRY configuration |
| **Kubernetes** | AWS EKS | 1.29+ | Container orchestration |
| **Compute** | EC2 Spot | t3a.medium | Cost-optimized workers |
| **Database** | RDS PostgreSQL | 15+ | ForgeWorks persistence |
| **Container Registry** | AWS ECR | - | Image storage |
| **DNS** | Route53 or sslip.io | - | Service discovery |
| **Secrets (CI/CD)** | GitHub Secrets | - | Pipeline credentials |
| **Secrets (Runtime)** | HashiCorp Vault | 1.15+ | Application secrets |

### Kubernetes Platform Stack

| Component | Technology | Required | Purpose |
|-----------|------------|----------|---------|
| **Ingress** | AWS ALB Controller | ✓ MVP | Load balancing + TLS |
| **Certificates** | cert-manager + ACM | ✓ MVP | TLS automation |
| **Secrets** | HashiCorp Vault | ✓ MVP | Runtime secret injection |
| **Scaling** | Karpenter | ✓ MVP | Node auto-provisioning |
| **GitOps** | ArgoCD | ○ Optional | Enhanced deployment tracking (K8s Native Adapter is fallback) |
| **Metrics** | Prometheus + Grafana | ○ Optional | External monitoring (ForgeWorks exposes /metrics) |
| **Logs** | Loki + Promtail | ○ Optional | External log aggregation (ForgeWorks outputs structured JSON) |
| **Policy** | Kyverno | ○ Optional | Admission control |

> **Design Principle**: ForgeWorks provides **adapters** to integrate with your existing tools. It **never requires** you to adopt new tools. Optional components enhance capabilities but are not dependencies.

### Secrets Management Strategy

ForgeWorks uses a hybrid approach for secrets management:

| Secret Type | Storage | Use Case | Example |
|-------------|---------|----------|---------|
| **CI/CD Secrets** | GitHub Secrets | Pipeline credentials | AWS_ACCESS_KEY_ID, DOCKER_PASSWORD |
| **Runtime Secrets** | HashiCorp Vault | Application secrets | DB_PASSWORD, JWT_SECRET, WEBHOOK_SECRET |

**Why This Separation:**
- **GitHub Secrets**: Free, native integration with GitHub Actions, sufficient for CI/CD workflows
- **Vault**: Self-hosted in K8s, zero egress cost, Vault Agent sidecar injects secrets directly into pods

**Secret Injection Flow:**
```
GitHub Actions (CI)           ForgeWorks Pods (Runtime)
       │                              │
       ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│ GitHub Secrets  │          │   Vault Agent       │
│ - ECR push creds│          │   Sidecar Injector  │
│ - Terraform vars│          └─────────┬───────────┘
└─────────────────┘                    │
                                       ▼
                              ┌─────────────────────┐
                              │    Vault Server     │
                              │  - DB credentials   │
                              │  - JWT secret       │
                              │  - GitHub webhook   │
                              └─────────────────────┘
```

**MVP Secrets Inventory:**
| Secret | Storage | Purpose |
|--------|---------|---------|
| `DB_USER` | Vault | PostgreSQL username |
| `DB_PASSWORD` | Vault | PostgreSQL password |
| `JWT_SECRET_KEY` | Vault | API authentication |
| `GITHUB_WEBHOOK_SECRET` | Vault | Webhook validation |
| `AWS_ACCESS_KEY_ID` | GitHub Secrets | ECR push access |
| `AWS_SECRET_ACCESS_KEY` | GitHub Secrets | ECR push access |

### Adapter-First Architecture

ForgeWorks follows an **Adapter-First Pattern**: it integrates with your existing tools rather than forcing new dependencies.

#### Core Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FORGEWORKS ADAPTER PATTERN                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User's Environment              ForgeWorks                                │
│   ─────────────────              ──────────                                 │
│                                                                             │
│   ┌─────────────┐                ┌─────────────────────────────────────┐   │
│   │   ArgoCD    │───Webhook────► │  ArgoCD Adapter (optional)          │   │
│   └─────────────┘                └─────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────┐                ┌─────────────────────────────────────┐   │
│   │    Flux     │───Webhook────► │  Flux Adapter (optional)            │   │
│   └─────────────┘                └─────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────┐                ┌─────────────────────────────────────┐   │
│   │ Kubernetes  │───K8s API────► │  K8s Native Adapter (DEFAULT)       │   │
│   │   Events    │                │  Zero external dependencies          │   │
│   └─────────────┘                └─────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────┐                ┌─────────────────────────────────────┐   │
│   │ Prometheus  │◄──/metrics──── │  Metrics Endpoint (built-in)        │   │
│   └─────────────┘                └─────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────┐                ┌─────────────────────────────────────┐   │
│   │  Datadog /  │◄──/metrics──── │  Same endpoint, standard format     │   │
│   │ CloudWatch  │                └─────────────────────────────────────┘   │
│   └─────────────┘                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Adapter Categories

| Category | Default (Zero-Dep) | Optional Adapters | User Provides |
|----------|-------------------|-------------------|---------------|
| **Deployment Detection** | K8s Native Adapter (watches Deployment/Pod events) | ArgoCD, Flux, Spinnaker | Webhook endpoint |
| **CI/CD Events** | GitHub Forge (webhook) | GitLab, Bitbucket, Jenkins | Webhook endpoint |
| **Observability** | /metrics endpoint + /health + JSON logs | Prometheus, Datadog, CloudWatch templates | Scraper/Agent |
| **Secrets** | Vault Adapter (MVP) | AWS SM, Azure KV, GCP SM | Secret provider |

#### Deployment Detection Flow

```
WITHOUT GitOps Tool (K8s Native Adapter):
─────────────────────────────────────────
kubectl apply / Helm install / CI deploy
              │
              ▼
┌─────────────────────────────────────┐
│   Kubernetes API Server             │
│   (Deployment created/updated)      │
└──────────────┬──────────────────────┘
               │ Watch stream
               ▼
┌─────────────────────────────────────┐
│   ForgeWorks K8s Native Adapter     │
│   - Extracts: image tag, labels     │
│   - Correlates: commit SHA from     │
│     app.kubernetes.io/version       │
└──────────────┬──────────────────────┘
               │
               ▼
        Smart Log Correlation
        (Same as ArgoCD flow)


WITH GitOps Tool (ArgoCD Adapter - Enhanced):
─────────────────────────────────────────────
Git Push → ArgoCD Sync
              │
              ├──► ArgoCD Webhook ──► ForgeWorks ArgoCD Adapter
              │                              │
              │                              ▼
              │                       Enhanced metadata:
              │                       - Sync status
              │                       - Health status
              │                       - Sync wave info
              │
              └──► K8s Deployment ──► K8s Native Adapter (backup)
```

#### Built-in Observability (Zero Dependencies)

ForgeWorks includes minimal observability that works without external tools:

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `GET /metrics` | Prometheus text format | Standard metrics export |
| `GET /health` | JSON | Kubernetes probes + detailed status |
| `GET /api/v1/status` | JSON | Built-in status dashboard data |
| `stdout/stderr` | Structured JSON | Log aggregation compatible |

**Built-in Status Dashboard** (No Grafana Required):
```
┌─────────────────────────────────────────────────────────────┐
│  ForgeWorks Status                          [Live Updates]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  System Health: ● Healthy         Events/hr: 1,247         │
│  Uptime: 14d 3h 22m               Correlations: 892        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Recent Activity                                     │   │
│  │  ────────────────                                    │   │
│  │  • PR #142 → Deploy backend:v1.2.3 → ✓ Success      │   │
│  │  • PR #141 → Deploy frontend:v2.0.1 → ✗ Failed      │   │
│  │  • PR #140 → Deploy backend:v1.2.2 → ✓ Success      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Adapter Status                                      │   │
│  │  ──────────────                                      │   │
│  │  GitHub Forge      ● Connected    Events: 523       │   │
│  │  K8s Native        ● Watching     Events: 412       │   │
│  │  ArgoCD            ○ Not Configured                 │   │
│  │  Prometheus        ○ Not Configured (/metrics ready)│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Future Work: Adapter Configuration Layer

> **TODO**: Backend mechanism & UI configuration layer for adapter management
>
> - **Backend**: Adapter registry, health checks, configuration API
> - **UI**: Adapter marketplace, one-click enable/disable, connection wizards
> - **Config**: YAML/UI-based adapter configuration
> - **Discovery**: Auto-detect available tools in cluster

### ForgeWorks Application Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python/FastAPI | API + Forge Adapters |
| **Frontend** | Next.js | Dashboard UI (includes built-in status page) |
| **ML Layer** | scikit-learn | Template recommendations |
| **Database** | PostgreSQL | Service catalog, events, Smart Log |
| **K8s Native Adapter** | Python + kubernetes client | Default deployment detection |
| **Metrics Endpoint** | prometheus-fastapi-instrumentator | /metrics for any scraper |
| **Cache** | Redis (optional) | Session/cache (Phase 2) |
| **Queue** | Redis/SQS (optional) | Async processing (Phase 2) |

#### Built-in vs Optional Components

| Capability | Built-in (Zero-Dep) | Optional Enhancement |
|------------|---------------------|---------------------|
| **Deployment Tracking** | K8s Native Adapter | ArgoCD/Flux Adapter |
| **CI/CD Correlation** | GitHub Forge | GitLab/Jenkins Adapter |
| **Metrics** | /metrics endpoint | Grafana dashboards (templates provided) |
| **Logging** | Structured JSON stdout | Loki/ELK integration |
| **Status Dashboard** | Built-in UI page | External Grafana |

---

## ForgeWorks Platform Architecture

### How Infrastructure Fits ForgeWorks

ForgeWorks is "The Glue" that bridges DevOps tools. The infrastructure must support:

```
                                    ┌─────────────────────────┐
                                    │    External Webhooks    │
                                    │  (GitHub, ArgoCD, etc)  │
                                    └───────────┬─────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         VPC (10.0.0.0/16)                           │  │
│  │                                                                      │  │
│  │   ┌──────────────────────────────────────────────────────────────┐  │  │
│  │   │                    Public Subnets (2 AZs)                    │  │  │
│  │   │                                                              │  │  │
│  │   │   ┌────────────────┐         ┌────────────────────────┐     │  │  │
│  │   │   │   ALB Ingress  │         │      NAT Gateway       │     │  │  │
│  │   │   │   (HTTPS:443)  │         │   (if private nodes)   │     │  │  │
│  │   │   └───────┬────────┘         └────────────────────────┘     │  │  │
│  │   └───────────┼──────────────────────────────────────────────────┘  │  │
│  │               │                                                      │  │
│  │   ┌───────────┼──────────────────────────────────────────────────┐  │  │
│  │   │           │         Private/Public Subnets                   │  │  │
│  │   │           ▼                                                  │  │  │
│  │   │   ┌─────────────────────────────────────────────────────┐   │  │  │
│  │   │   │                   EKS Cluster                        │   │  │  │
│  │   │   │                                                      │   │  │  │
│  │   │   │  ┌─────────────────────────────────────────────┐    │   │  │  │
│  │   │   │  │            Spot Node Group                   │    │   │  │  │
│  │   │   │  │              (t3a.medium)                    │    │   │  │  │
│  │   │   │  │                                              │    │   │  │  │
│  │   │   │  │  ┌──────────────┐  ┌──────────────────────┐ │    │   │  │  │
│  │   │   │  │  │  forgeworks  │  │      platform        │ │    │   │  │  │
│  │   │   │  │  │   namespace  │  │      namespace       │ │    │   │  │  │
│  │   │   │  │  │              │  │                      │ │    │   │  │  │
│  │   │   │  │  │ ┌──────────┐ │  │ ┌──────┐ ┌────────┐ │ │    │   │  │  │
│  │   │   │  │  │ │ Backend  │ │  │ │ArgoCD│ │Prometheus│ │    │   │  │  │
│  │   │   │  │  │ │ (FastAPI)│ │  │ └──────┘ └────────┘ │ │    │   │  │  │
│  │   │   │  │  │ ├──────────┤ │  │ ┌──────┐ ┌────────┐ │ │    │   │  │  │
│  │   │   │  │  │ │ Frontend │ │  │ │Grafana│ │  Loki  │ │ │    │   │  │  │
│  │   │   │  │  │ │ (Next.js)│ │  │ └──────┘ └────────┘ │ │    │   │  │  │
│  │   │   │  │  │ └──────────┘ │  │ ┌──────────────────┐│ │    │   │  │  │
│  │   │   │  │  │              │  │ │  Vault Server    ││ │    │   │  │  │
│  │   │   │  │  └──────────────┘  │ └──────────────────┘│ │    │   │  │  │
│  │   │   │  │                    └──────────────────────┘ │    │   │  │  │
│  │   │   │  └─────────────────────────────────────────────┘    │   │  │  │
│  │   │   │                         │                            │   │  │  │
│  │   │   └─────────────────────────┼────────────────────────────┘   │  │  │
│  │   └─────────────────────────────┼────────────────────────────────┘  │  │
│  │                                 │                                    │  │
│  │   ┌─────────────────────────────┼────────────────────────────────┐  │  │
│  │   │                             ▼                                │  │  │
│  │   │   ┌──────────────────┐                                      │  │  │
│  │   │   │  RDS PostgreSQL  │     (Secrets managed by Vault        │  │  │
│  │   │   │   (db.t3.micro)  │      in platform namespace +         │  │  │
│  │   │   │                  │      GitHub Secrets for CI/CD)       │  │  │
│  │   │   │  ForgeWorks DB   │                                      │  │  │
│  │   │   │  - Services      │                                      │  │  │
│  │   │   │  - Templates     │                                      │  │  │
│  │   │   │  - Events        │                                      │  │  │
│  │   │   │  - Anomalies     │                                      │  │  │
│  │   │   └──────────────────┘         ┌──────────────────┐         │  │  │
│  │   │                                │       ECR        │         │  │  │
│  │   │                                │  forgeworks-be   │         │  │  │
│  │   │                                │  forgeworks-fe   │         │  │  │
│  │   │                                └──────────────────┘         │  │  │
│  │   └──────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Forge Adapter Network Requirements

| Forge Adapter | Direction | Protocol | Requirement |
|---------------|-----------|----------|-------------|
| **GitHub Forge** | Inbound | HTTPS | Public webhook endpoint |
| **GitHub Forge** | Outbound | HTTPS | GitHub API access |
| **Kubernetes Forge** | Internal | HTTPS | K8s API via ServiceAccount |
| **ArgoCD Forge** | Internal | HTTPS | ArgoCD API (in-cluster) |

### Data Flow Architecture

```
┌─────────────┐     Webhook      ┌─────────────────────────────────────────┐
│   GitHub    │ ───────────────► │              ForgeWorks                 │
│   Actions   │                  │                                         │
└─────────────┘                  │  ┌─────────────────────────────────┐   │
                                 │  │     Python Casting Layer        │   │
┌─────────────┐     Events       │  │  (Extract: commit_sha, status,  │   │
│  Kubernetes │ ───────────────► │  │   workflow_id, pod_name, etc)   │   │
│   Events    │                  │  └───────────────┬─────────────────┘   │
└─────────────┘                  │                  │                      │
                                 │                  ▼                      │
┌─────────────┐     Sync Status  │  ┌─────────────────────────────────┐   │
│   ArgoCD    │ ───────────────► │  │      Shared State (Smart Log)   │   │
│             │                  │  │   PostgreSQL: unified events    │   │
└─────────────┘                  │  └───────────────┬─────────────────┘   │
                                 │                  │                      │
                                 │                  ▼                      │
                                 │  ┌─────────────────────────────────┐   │
                                 │  │       ML Analysis Layer         │   │
                                 │  │  (Correlate, classify, alert)   │   │
                                 │  └───────────────┬─────────────────┘   │
                                 │                  │                      │
                                 │                  ▼                      │
                                 │  ┌─────────────────────────────────┐   │
                                 │  │    WebSocket Broadcast Layer    │───┼──► Dashboard
                                 │  │    (Real-time to frontend)      │   │
                                 │  └─────────────────────────────────┘   │
                                 └─────────────────────────────────────────┘
```

---

## EKS Platform Tools & Add-ons

### Core Platform Components (Day 1) - Required

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **AWS VPC CNI** | latest | Pod networking | EKS managed |
| **CoreDNS** | latest | Service discovery | EKS managed |
| **kube-proxy** | latest | Service routing | EKS managed |
| **AWS ALB Controller** | 2.7+ | Ingress + Load Balancing | Helm |
| **cert-manager** | 1.14+ | TLS certificate automation | Helm |
| **HashiCorp Vault** | 1.15+ | Runtime secrets for K8s pods | Helm |
| **metrics-server** | 0.7+ | HPA metrics source | Helm |

### Optional Platform Components (User's Choice)

> These components **enhance** ForgeWorks but are **not required**. ForgeWorks provides built-in alternatives.

| Tool | Version | Purpose | ForgeWorks Alternative |
|------|---------|---------|------------------------|
| **ArgoCD** | 2.10+ | GitOps deployment tracking | K8s Native Adapter (built-in) |
| **Prometheus** | 2.50+ | Metrics collection | /metrics endpoint (built-in) |
| **Grafana** | 10+ | Visualization | Built-in status dashboard |
| **Loki** | 2.9+ | Log aggregation | Structured JSON logs (built-in) |
| **Promtail** | 2.9+ | Log shipping | stdout/stderr (K8s native) |

**Decision Guide:**
- **Install ArgoCD** if: You want enhanced sync status, health checks, and GitOps workflow
- **Install Prometheus/Grafana** if: You need historical metrics, alerting, or custom dashboards
- **Skip both** if: You want minimal footprint; ForgeWorks works standalone

### Advanced Platform Components (Day 2+)

| Tool | Version | Purpose | When to Add |
|------|---------|---------|-------------|
| **Karpenter** | 0.35+ | Intelligent node scaling | After initial stability |
| **Kyverno** | 1.11+ | Policy enforcement | Before production |
| **Velero** | 1.13+ | Backup/restore | If persistent data critical |
| **Goldilocks** | 4.0+ | Resource recommendations | After baseline metrics |

### Tools NOT Needed (MVP)

| Tool | Reason to Skip |
|------|----------------|
| **Istio/Linkerd** | Over-engineering for single-app platform |
| **AWS Secrets Manager** | Using Vault + GitHub Secrets instead |
| **External Secrets Operator** | Vault Agent handles secret injection |
| **Crossplane** | Not provisioning external infra from K8s |
| **Backstage** | ForgeWorks IS the IDP |

---

## Required Structure (High-Level)

### Repository Structure

```
forgeworks-infra/
├── README.md
├── Makefile                      # Common commands
│
├── terraform/                    # OpenTofu/Terraform
│   ├── terragrunt.hcl           # Root Terragrunt config
│   │
│   ├── modules/                  # Reusable modules
│   │   ├── vpc/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── eks/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── rds/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── ecr/
│   │   │   └── main.tf
│   │   └── github-secrets/
│   │       └── main.tf            # GitHub Secrets via gh CLI
│   │
│   └── environments/
│       └── dev/
│           ├── terragrunt.hcl   # Environment config
│           ├── vpc/
│           │   └── terragrunt.hcl
│           ├── eks/
│           │   └── terragrunt.hcl
│           ├── rds/
│           │   └── terragrunt.hcl
│           └── ecr/
│               └── terragrunt.hcl
│
├── kubernetes/                   # K8s manifests (GitOps or kubectl apply)
│   ├── bootstrap/               # Initial cluster setup
│   │   └── kustomization.yaml   # Required components only
│   │
│   ├── platform/                # Platform components
│   │   ├── required/            # Always installed
│   │   │   ├── cert-manager/
│   │   │   │   └── application.yaml
│   │   │   ├── vault/
│   │   │   │   ├── application.yaml
│   │   │   │   └── vault-config.yaml
│   │   │   └── alb-controller/
│   │   │       └── application.yaml
│   │   │
│   │   └── optional/            # User's choice - NOT required
│   │       ├── argocd/          # Optional: Enhanced GitOps
│   │       │   └── application.yaml
│   │       └── monitoring/      # Optional: External observability
│   │           ├── prometheus/
│   │           ├── grafana/
│   │           │   └── forgeworks-dashboard.json  # Pre-built dashboard
│   │           └── loki/
│   │
│   └── apps/                    # Application deployments
│       └── forgeworks/
│           ├── namespace.yaml
│           ├── backend/
│           │   ├── deployment.yaml
│           │   ├── service.yaml
│           │   ├── ingress.yaml
│           │   ├── vault-annotations.yaml  # Vault agent sidecar config
│           │   └── hpa.yaml
│           ├── frontend/
│           │   ├── deployment.yaml
│           │   ├── service.yaml
│           │   └── ingress.yaml
│           └── adapters/        # Adapter configurations
│               ├── k8s-native-adapter.yaml    # DEFAULT - always enabled
│               ├── github-forge.yaml          # Webhook config
│               └── argocd-adapter.yaml        # Optional - if ArgoCD installed
│
├── .github/
│   └── workflows/
│       ├── terraform-plan.yaml   # PR: plan infra changes
│       ├── terraform-apply.yaml  # Merge: apply infra
│       ├── build-backend.yaml    # Build + push backend image
│       └── build-frontend.yaml   # Build + push frontend image
│
└── docs/
    ├── ARCHITECTURE.md
    ├── RUNBOOK.md
    └── COST.md
```

### Namespace Strategy

| Namespace | Required | Purpose | Components |
|-----------|----------|---------|------------|
| `kube-system` | ✓ | K8s system | CoreDNS, kube-proxy, VPC CNI |
| `cert-manager` | ✓ | Certificates | cert-manager controller |
| `vault` | ✓ | Secrets management | Vault server + injector |
| `aws-system` | ✓ | AWS controllers | ALB controller |
| `forgeworks` | ✓ | Application | Backend, Frontend, K8s Native Adapter |
| `argocd` | ○ Optional | GitOps | ArgoCD server, repo-server |
| `monitoring` | ○ Optional | Observability | Prometheus, Grafana, Loki |

---

## Deliverables

### Phase 1: Foundation (Days 1-10)

| # | Deliverable | Acceptance Criteria |
|---|-------------|---------------------|
| 1.1 | Infrastructure repository | Terragrunt structure complete |
| 1.2 | VPC provisioned | 2 AZs, public subnets, IGW |
| 1.3 | EKS cluster running | kubectl access working |
| 1.4 | RDS PostgreSQL deployed | Connection from EKS verified |
| 1.5 | ECR repositories created | Push/pull working |
| 1.6 | GitHub Secrets configured | CI/CD credentials stored |

### Phase 2: Platform Bootstrap (Days 11-20)

| # | Deliverable | Required | Acceptance Criteria |
|---|-------------|----------|---------------------|
| 2.1 | ALB Controller running | ✓ | Ingress creates ALB |
| 2.2 | cert-manager configured | ✓ | Certificates auto-provisioned |
| 2.3 | Vault installed & configured | ✓ | Runtime secrets injection working |
| 2.4 | K8s Native Adapter working | ✓ | Deployment events captured |
| 2.5 | ForgeWorks /metrics endpoint | ✓ | Prometheus-format metrics exposed |
| 2.6 | ArgoCD installed | ○ Optional | UI accessible, Git repo connected |
| 2.7 | Monitoring stack deployed | ○ Optional | Grafana dashboards working |

### Phase 3: ForgeWorks Deployment (Days 21-35)

| # | Deliverable | Acceptance Criteria |
|---|-------------|---------------------|
| 3.1 | CI pipeline for backend | Build → Scan → Push to ECR |
| 3.2 | CI pipeline for frontend | Build → Push to ECR |
| 3.3 | ForgeWorks backend running | Health endpoint returns 200 |
| 3.4 | ForgeWorks frontend running | Dashboard loads |
| 3.5 | Database migrations applied | Schema matches codebase |
| 3.6 | HTTPS ingress working | Public URL with valid TLS |
| 3.7 | GitHub webhook configured | Events received by ForgeWorks |

### Phase 4: Validation & Documentation (Days 36-45)

| # | Deliverable | Acceptance Criteria |
|---|-------------|---------------------|
| 4.1 | K8s Native Adapter tested | Deployment → Smart Log correlation working |
| 4.2 | GitHub Forge tested | PR → Build → Deploy correlation working |
| 4.3 | Built-in status dashboard | /api/v1/status returns live data |
| 4.4 | Load testing completed | Baseline performance documented |
| 4.5 | Runbook documented | Common operations listed |
| 4.6 | Cost report generated | Actual vs budget comparison |
| 4.7 | Architecture documented | Diagrams and adapter patterns recorded |

---

## Expected Outcomes

### Technical Outcomes

| Outcome | Measure |
|---------|---------|
| ForgeWorks running on EKS | Application accessible via HTTPS |
| GitOps-driven deployments | 100% of changes via Git |
| Automated TLS certificates | Zero manual certificate management |
| Secrets managed by Vault | Zero secrets in Git or K8s manifests |
| Observable platform | Metrics, logs, and dashboards available |
| Cost-optimized infrastructure | < $160 for 45 days |

### Learning Outcomes

| Outcome | Evidence |
|---------|----------|
| EKS cluster management | Provisioned and operated production-like cluster |
| GitOps workflow | Implemented ArgoCD-based deployments |
| AWS-K8s integration | IRSA, ALB, Vault secret injection working |
| Infrastructure as Code | Repeatable provisioning via Terragrunt |
| Platform engineering | End-to-end IDP deployment |

### Portfolio Outcomes

| Outcome | Artifact |
|---------|----------|
| Working demo | ForgeWorks on AWS EKS |
| Architecture documentation | Diagrams and decision records |
| Infrastructure code | Public GitHub repository |
| Operational runbook | Day-2 operations documented |

---

## Metrics

### Infrastructure Metrics

| Metric | Target | Tool |
|--------|--------|------|
| Cluster provisioning time | < 20 min | Terraform output |
| Node scale-up time | < 3 min | Karpenter metrics |
| Deployment rollout time | < 2 min | ArgoCD metrics |
| Secret injection latency | < 5 sec | Vault metrics |

### Application Metrics

| Metric | Target | Tool |
|--------|--------|------|
| API response time (p95) | < 200ms | /metrics endpoint (any scraper) |
| Webhook processing time | < 500ms | /metrics endpoint (any scraper) |
| Error rate | < 1% | /metrics endpoint (any scraper) |
| WebSocket connections | Track count | Built-in status dashboard |

### Cost Metrics

| Metric | Target | Tool |
|--------|--------|------|
| Daily cost | < $4/day | AWS Cost Explorer |
| EKS control plane | ~$2.40/day | AWS Cost Explorer |
| Spot worker cost | < $0.50/day | AWS Cost Explorer |
| RDS cost | ~$0.50/day | AWS Cost Explorer |

### Availability Metrics

| Metric | Target | Tool |
|--------|--------|------|
| Cluster uptime | > 99% during work hours | /health endpoint or external monitor |
| Application uptime | > 99% during work hours | /health endpoint or external monitor |
| Spot interruption recovery | < 5 min | Karpenter metrics |

---

## Cost Breakdown

### 45-Day Budget

| Component | Calculation | Cost |
|-----------|-------------|------|
| EKS Control Plane | 1,080h × $0.10 | $108.00 |
| Spot Workers (t3a.medium, 7h/day) | 630h × $0.015 | $9.45 |
| RDS PostgreSQL (db.t3.micro) | 1,080h × $0.017 | $18.36 |
| RDS Storage (20GB) | 20GB × 1.5mo × $0.115 | $3.45 |
| EBS Volumes (50GB) | 50GB × 1.5mo × $0.10 | $7.50 |
| ECR Storage (5GB) | 5GB × 1.5mo × $0.10 | $0.75 |
| Data Transfer | estimate | $5.00 |
| Vault (self-hosted) | In-cluster, no extra cost | $0.00 |
| Vault Storage (PVC 1GB) | 1GB × 1.5mo × $0.10 | $0.15 |
| **Total** | | **~$152** |

### Cost Guardrails

| Rule | Implementation |
|------|----------------|
| No NAT Gateway | Use public subnets for MVP |
| Spot-first compute | Managed node group with Spot |
| Scale-to-zero | Karpenter consolidation policy |
| RDS stop on weekends | Scheduled stop/start (optional) |
| Budget alerts | AWS Budgets at $50, $100, $150 |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Spot interruption | Medium | Low | Multi-instance-type node group, stateless design |
| Cost overrun | Low | Medium | Budget alerts, daily cost review |
| EKS upgrade issues | Low | Medium | Pin versions, test in isolation first |
| Secret exposure | Low | High | No secrets in Git, Vault injection only |
| Data loss | Low | High | RDS automated backups, GitOps = infra recovery |

---

## Timeline

```
Week 1 (Days 1-7)
├── Day 1-2: Set up infrastructure repo, Terragrunt structure
├── Day 3-4: Provision VPC + EKS cluster
├── Day 5-6: Provision RDS + ECR + Secrets
└── Day 7: Validate connectivity, document

Week 2 (Days 8-14)
├── Day 8-9: Install ArgoCD, configure Git repo
├── Day 10-11: Install ALB Controller + cert-manager
├── Day 12-13: Install Vault + monitoring stack
└── Day 14: Validate platform stack, document

Week 3 (Days 15-21)
├── Day 15-16: Create CI pipelines for ForgeWorks
├── Day 17-18: Deploy ForgeWorks backend
├── Day 19-20: Deploy ForgeWorks frontend
└── Day 21: Configure ingress + TLS, validate

Week 4 (Days 22-28)
├── Day 22-23: Configure GitHub webhook
├── Day 24-25: Test Forge Adapters end-to-end
├── Day 26-27: Performance testing
└── Day 28: Bug fixes, optimization

Week 5 (Days 29-35)
├── Day 29-30: Add Kyverno policies
├── Day 31-32: Day-2 operations testing
├── Day 33-35: Documentation, runbook

Week 6 (Days 36-45)
├── Day 36-38: Final validation, demo prep
├── Day 39-42: Buffer for issues
└── Day 43-45: Cost analysis, lessons learned
```

---

## Success Criteria

### MVP Complete When (Required):

- [ ] ForgeWorks accessible via HTTPS at public URL
- [ ] GitHub Forge receiving webhooks and processing events
- [ ] K8s Native Adapter detecting deployments
- [ ] Events correlated across GitHub → K8s (via Smart Log)
- [ ] Built-in status dashboard shows real-time updates
- [ ] /metrics endpoint exposing Prometheus-format metrics
- [ ] /health endpoint returning detailed status
- [ ] Secrets managed via Vault
- [ ] Total cost < $160 for 45 days
- [ ] Infrastructure reproducible from code

### Optional Enhancements (Not Required for MVP):

- [ ] ArgoCD integration for enhanced deployment tracking
- [ ] Grafana dashboards with ForgeWorks template
- [ ] Loki log aggregation configured
- [ ] GitOps workflow for deployments (kubectl apply is acceptable)

---

## References

- [ForgeWorks Architecture (ADR-007)](../../forge-works/adr/007-glue-architecture.md)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Karpenter Documentation](https://karpenter.sh/)

---

*Document Version: 1.1*
*Created: January 2025*
*Updated: January 2025 - Adapter-First Architecture Pattern*
*Author: Adam Keinan + Claude Code*
