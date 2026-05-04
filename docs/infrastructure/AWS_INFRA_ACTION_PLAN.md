# Kubernetes Cloud Best-Practices — Development Action Plan

## 🎯 Primary Goal

**Forge deep, practical understanding of Kubernetes best practices in a cloud environment**, focusing on *how real production platforms are designed, provisioned, operated, and evolved* — not just “how to deploy a cluster”.

## Core principle

Each cluster is a purpose-built environment with:

- a clear mission
- a bounded toolset
- a defined flow strategy
- and predictable cost controls

---

Alright — let’s level it up into a **multi-cluster training + platform engineering roadmap** that’s still **realistic, cloud-native, and cost-aware**.

What you’re describing is basically a **progressive maturity model**: each cluster has a different job, different blast radius, and different tooling depth.

Below is a **next-level architecture + action plan** with clear boundaries, flows, and what each cluster should include.

---

# Next-Level Kubernetes Cloud Training Plan (Multi-Cluster)

## Core principle

Each cluster is a **purpose-built environment** with:

* a *clear mission*
* a *bounded toolset*
* a *defined flow strategy*
* and *predictable cost controls*

You’ll end up with a **repeatable “cluster factory”**: provision → bootstrap → run lessons/tests → teardown or scale-to-zero.

---

# Cluster 1 — “Three Environments” Cluster (Dev / Stage / Preview)

### Mission

Host 3 basic environments in one cluster to practice:

* namespace isolation
* environment promotion
* network segmentation
* RBAC + quota governance

### Implementation model

**Single EKS cluster** with:

* Namespaces: `dev`, `stage`, `preview`
* Each environment has:

  * ResourceQuota + LimitRange
  * NetworkPolicies (if using Cilium/Calico)
  * Ingress routing rules
  * Optional: dedicated node group (if you want hard isolation)

### Tooling (minimal but production-shaped)

* NGINX Ingress
* cert-manager
* metrics-server
* Argo CD (optional here, but recommended to establish GitOps early)

### Flow Strategy

* Git branch → environment mapping (simple)

  * `dev` branch deploys to `dev`
  * `release/*` deploys to `stage`
  * `preview/*` deploys to `preview`
* Promotion = Git merge + tag

### Best-practices focus

* isolation, guardrails, predictable deployments

✅ This becomes our “foundation cluster”.

---

# Cluster 2 — “Internal Developer Platform” Cluster (IDP Platform Cluster)

### Mission

Host and test an **internal developer platform** itself.

This is where we learn:

* platform operators
* productization of infra
* golden paths
* self-service workflows

### Implementation model

A dedicated cluster, because:

* platform components are cluster-wide and noisy
* you want controlled upgrades/testing
* you don’t want platform experiments breaking app environments

### Tooling (platform-grade)

* Argo CD (mandatory here)
* External Secrets Operator (if cloud secret manager)
* Policy engine: Kyverno or OPA Gatekeeper
* Observability: Prometheus + Grafana + logs (Loki)
* Ingress + cert-manager
* Optional: service mesh only if it serves a clear lesson objective

### IDP Components (examples)

Pick one “core IDP” path:

* **Backstage** + Kubernetes plugin + templates
* Or **Crossplane** for infrastructure provisioning
* Or both, but start with one

### Flow Strategy

* GitOps repo = source of truth for platform
* Platform upgrades via PR + validation pipeline
* “Golden path” templates published and versioned

✅ This becomes your “platform product lab”.

---

# Cluster 3 — “Integration Lab” Cluster (Chaos & Connectivity)

### Mission

Test integrations as part of development/training:

* security scanners
* CI runners
* external systems
* identity providers
* logging sinks
* policy enforcement
* traffic routing variants

This cluster is allowed to be messy — it’s your sandbox.

### Implementation model

Separate cluster because:

* integrations often require cluster-wide privileges
* you’ll be installing/removing lots of CRDs
* you’ll break stuff constantly (which is good)

### Tooling (integration-focused)

* Argo CD optional (nice, but not required)
* Observability minimal (just enough to debug)
* Strong cleanup/teardown automation

### Integration categories (what to test)

* CI: GitHub Actions Runner Controller (ARC)
* Security: Snyk/Trivy admission controls
* IAM: IRSA patterns
* Networking: different ingress controllers, ALB controller
* DNS: ExternalDNS
* Secrets: Vault, AWS Secrets Manager
* Artifact storage: ECR flows

✅ This becomes your “I want to plug in X and see what explodes” cluster.

---

# Cluster 4 — “Real Platform Integration” Cluster (Connected to your existing Platform Project)

### Mission

Integrate Kubernetes into the **existing platform engineering project** as a real target.

This is where training turns into **product engineering**.

### Implementation model

This cluster should look like “real org production-like staging”:

* strict GitOps
* strict policies
* clean separation of platform vs apps
* integration into your IDP workflows

### Key design decision

This cluster becomes your **reference implementation**:

* the one you can demo
* the one you can onboard others onto
* the one that matches your platform’s docs

### Tooling (production-like)

* GitOps: Argo CD
* Policy engine: Kyverno/OPA
* Secrets: External Secrets or Vault
* Observability full stack
* Ingress + cert-manager
* Minimal but intentional add-ons only

### Flow Strategy

* Developers interact through the **platform**:

  * templates / golden paths
  * PRs / automation pipelines
  * self-service flows

No one “kubectl applies” into this cluster except platform ops.

✅ This becomes your “platform reference cluster”.

---

# Recommended operating model (saves money + maximizes realism)

## One “Cluster Factory” repo

A single repo that can provision any of the 4 clusters with:

* `cluster_type = env | idp | integration | platform`
* modules:

  * `eks-core`
  * `nodegroups`
  * `addons`
  * `policies`
  * `gitops-bootstrap`

## Node groups strategy (cost + functionality)

* each cluster has node groups per mission
* default node groups at 0 unless needed
* for big stacks (observability), scale up only when required

---

# Deliverables to create next (concrete)

Here’s what we should produce next:

1. **Cluster Catalog** (1 page)

   * cluster name
   * mission
   * namespaces
   * add-ons
   * node groups
   * teardown policy

2. **Repo Structure**

   * `infra/` (tofu)
   * `platform/` (argo apps)
   * `apps/` (sample apps)
   * `docs/` (training)

3. **Lesson Matrix**

   * which lesson runs in which cluster
   * what node size required
   * expected cost per session

---

This order gives you:

* early results
* minimal risk
* and no over-engineering too soon

---

We’ll also need to write:

* a **Cluster Catalog table** (all 4 clusters, very detailed)
* plus the **Cluster Factory repo skeleton** (module layout + naming + variables)
* and a **cost guardrails policy** (what we never enable unless needed: NAT, ALB, etc.)

---

## 🧭 Development Philosophy (important framing)

* **Cloud-native, not local-only**: Decisions should map to managed Kubernetes (EKS first).
* **Best practices over defaults**: Every choice must answer *why this way*.
* **Cost-aware by design**: Ephemeral infra, scoped workers, no idle waste.
* **Day-0 → Day-2 mindset**: Provisioning is the beginning, not the end.
* **Lesson-isolated execution**: Each lesson owns its workers and tooling.

---

## 🧱 High-Level Development Structure

The Development is split into **layers**, each building on the previous one:

1. **Cluster Architecture & Provisioning (Day-0)**
2. **Node Architecture & Networking**
3. **Flow Strategy (Traffic, Deployments, Promotion)**
4. **Workers & Operators (Platform Internals)**
5. **Integrations (CI/CD, Security, Observability)**
6. **Cluster Management (Day-2 Operations)**

Each layer includes:

* *Concepts*
* *Design decisions*
* *Hands-on execution*
* *Failure & tradeoff discussion*

---

## 1️⃣ Cluster Architecture & Provisioning

### Objectives

* Understand how a **production-grade managed Kubernetes cluster** is structured in the cloud.
* Learn what the cloud manages vs what *you* own.

### Topics

* Managed control plane (EKS responsibility boundaries)
* VPC design for Kubernetes

  * Public vs private subnets (Development vs production)
  * Multi-AZ tradeoffs
* IAM & OIDC integration
* Cluster versioning & lifecycle strategy
* Cost model of managed Kubernetes

### Hands-On

* Provision EKS using **IaC (OpenTofu/Terraform)**:

  * Cluster only (no workers yet)
  * Minimal addons (VPC CNI, CoreDNS, kube-proxy)
* Validate cluster health and access patterns

### Best Practices Emphasized

* No “click-ops”
* Version pinning
* Explicit lifecycle ownership
* Ephemeral cluster mindset

---

## 2️⃣ Node Architecture & Networking

### Objectives

* Understand **what worker nodes really are** and how traffic reaches pods.
* Learn how Kubernetes networking maps to cloud networking.

### Topics

* Managed Node Groups vs Self-Managed
* Instance types by workload (cost vs capability)
* Scaling node groups to zero
* Kubernetes networking model (Pod IPs, Services)
* Cloud CNI behavior (AWS VPC CNI)
* Security Groups vs Network Policies

### Hands-On

* Create **lesson-scoped node groups**:

  * Each lesson has its own node group
  * Default desired size = 0
* Bring up a node group only when required
* Deploy a sample workload and trace traffic:

  * Node → Pod → Service → Ingress (if enabled)

### Best Practices Emphasized

* No always-on workers
* Clear node responsibility
* Cost-driven sizing decisions
* Network visibility

---

## 3️⃣ Flow Strategy (Traffic, Deployments, Promotion)

### Objectives

* Learn how **code flows into the cluster** and how traffic flows inside it.
* Understand deployment and promotion strategies.

### Topics

* Deployment strategies:

  * Rolling
  * Blue/Green
  * Canary (conceptual)
* Namespace strategy
* Environment separation patterns
* Ingress patterns (cloud LB vs internal routing)
* Git-driven promotion models

### Hands-On

* Deploy a sample app with:

  * Proper resource requests/limits
  * Health checks
* Expose traffic using:

  * Port-forward (baseline)
  * Ingress (when needed)
* Promote versions via Git changes, not kubectl

### Best Practices Emphasized

* Git as the source of truth
* Explicit promotion
* Zero-trust defaults
* Avoiding manual drift

---

## 4️⃣ Workers & Operators (Platform Internals)

### Objectives

* Understand **how Kubernetes extends itself** via controllers and operators.
* Learn what belongs in the “platform layer” vs application layer.

### Topics

* Controllers, CRDs, operators
* Helm vs raw manifests vs Kustomize
* Add-on lifecycle ownership
* Cluster-wide vs namespace-scoped components

### Hands-On

* Install platform operators via GitOps:

  * Ingress Controller
  * cert-manager
  * Metrics Server
* Observe reconciliation loops
* Break and recover an operator intentionally

### Best Practices Emphasized

* Controllers manage state, humans don’t
* Clear separation of concerns
* Reconciliation over imperative fixes

---

## 5️⃣ Integrations (CI/CD, Security, Observability)

### Objectives

* Connect Kubernetes to the **real platform ecosystem**.
* Understand supply chain security and visibility.

### Topics

* CI pipelines (build, scan, push)
* GitOps CD (Argo CD / Flux)
* Image scanning & policy enforcement
* Secrets management
* Metrics, logs, alerts

### Hands-On

* CI pipeline:

  * Build image
  * Scan (Trivy/Snyk)
  * Push to registry
* GitOps:

  * App deployed via Argo CD
* Observability:

  * Prometheus + Grafana
  * Logs via Loki or equivalent

### Best Practices Emphasized

* No kubectl deploys
* Policy before production
* Observability is not optional

---

## 6️⃣ Cluster Management (Day-2 Operations)

### Objectives

* Learn what **actually consumes time in real clusters**.
* Practice safe change, recovery, and upgrades.

### Topics

* Cluster upgrades (control plane vs nodes)
* Node rotation and draining
* Certificate rotation
* Cost monitoring
* Incident-style debugging

### Hands-On

* Upgrade Kubernetes minor version
* Replace a node group
* Kill nodes and observe recovery
* Enforce policies that block bad deployments

### Best Practices Emphasized

* Planned change
* Automation over heroics
* Predictable failure recovery

---

## 📦 Deliverables of the Development

By the end, you will have:

* A **repeatable EKS Development platform**
* IaC templates for:

  * Cluster
  * Lesson-scoped node groups
  * Addons
* A **reference GitOps layout**
* A mental model aligned with **platform engineering reality**

---

## Cost Strategy (90-Day Plan) — Spot-First EKS Development

### Goal

Keep the Development platform **production-realistic** while maintaining a predictable **low budget** over a 90-day period. The cluster is **not 24/7**; it runs **4–8 hours/day** for lessons, provisioning drills, and integration testing.

---

## Cost Model (What we pay for)

### 1) EKS Control Plane (Fixed while cluster exists)

* EKS charges **$0.10 per cluster-hour** (standard support).
* Cost floor is driven primarily by “cluster exists time”.

**90-day estimate (example):**

* ~5–6h/day average → ~450–500 cluster-hours
* **Control plane ≈ $45–$50 over 90 days**

✅ Key rule: **delete the cluster when not needed** (or at least keep existence time bounded to Development hours).

---

### 2) Worker Nodes (Compute) — Spot-First

Worker nodes are the *main* variable cost — and also where we can save the most.

**Strategy:**

* Prefer **Spot instances** for the Development workloads.
* Run workers only during lesson time.
* Scale to zero when idle.

Spot typically provides **major discounts** vs On-Demand (commonly 60–90% depending on market). (We’ll treat interruptions as part of the Development realism.)

---

## Spot Node Architecture (Recommended)

### Node Groups

We use node groups to isolate stability vs experimentation:

1. `ng-Development-spot` (primary)

* Capacity: **SPOT**
* Purpose: standard lesson workloads (apps, controllers, GitOps, most add-ons)
* Default size: **0**
* Active size: **1–2** during lesson sessions
* Uses **multiple instance types** for better availability (reduces interruption probability)

2. `ng-lab-spot` (integration / chaos)

* Capacity: **SPOT**
* Purpose: aggressive integration testing (CRD churn, install/uninstall tools)
* Default size: **0**
* Active size: **1** when needed
* Treated as disposable

3. Optional `ng-system-ondemand` (stability anchor)

* Capacity: **On-Demand**
* Purpose: keep core services stable if desired (kube-system essentials)
* Default: can be omitted to stay ultra-cheap
* Add only if Spot interruptions become too annoying for baseline learning

---

## Operational Rules (Cost Guardrails)

### Scale-to-zero by default

* All Spot node groups default to `desired=0`
* A lesson “activates” a node group by scaling it up temporarily
* After the lesson, scale back to 0

### Avoid cost multipliers unless the lesson requires it

* **Avoid NAT Gateway** for Development unless a lesson explicitly focuses on private subnets/NAT patterns.
* **Avoid external Load Balancers** (ALB/NLB) unless the lesson is specifically “Ingress on AWS”.
* Prefer: `port-forward`, internal ingress, or minimal exposure patterns.

### Treat Spot interruptions as Development outcomes

Spot interruptions are not failures — they are a deliberate learning mechanism:

* validates readiness/liveness probes
* validates controller reconciliation (GitOps recovery)
* forces stateless design thinking
* teaches rescheduling + failure tolerance

---

## Expected 90-Day Price Range (Budget Target)

With:

* 1 EKS cluster
* 4–8h/day usage
* Spot-first workers
* minimal “always-on” components

**Target range:** **~$80–$120 total for 90 days**, depending mainly on:

* cluster uptime hours
* number of worker-hours
* any optional ALB usage
* persistent storage volumes kept around

(We’ll keep the plan designed so any cost spikes are *intentional* and tied to a lesson.)

---

## Implementation Deliverable

Add to the IaC templates:

* Spot node groups with a multi-instance-type mix
* per-lesson activation variables
* defaults set to zero
* tagging and labels to route workloads per lesson

---

If you want, next I’ll produce the **“Lesson → Node Group → Instance Size” matrix** so each lesson automatically selects the cheapest worker profile that still works (e.g., basic lessons on `t3a.small`, heavier ones on `t3.medium`).
