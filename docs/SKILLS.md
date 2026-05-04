# ForgeWorks — AI Skills Catalog (SKILLS.md)

This document defines the **canonical skill set** used by the ForgeWorks AI team
(**Human + Codex + Claude**) to collaborate efficiently, safely, and without scope drift.

The goal of this file is **not automation**.
It is **alignment**.

Each skill is:

* purpose-built
* scope-bounded
* compatible with ForgeWorks doctrine (Glue, agentless, advisory ML)
* composable into real work without refactoring our workflow

This file is **tool-agnostic canon**.
Codex uses it for advising & review.
Claude uses it for implementation.
Humans use it to compile intent into action.

---

## Global Rules (Apply to ALL Skills)

**Non-negotiable constraints:**

* No control plane behavior
* No infrastructure automation
* No agents (runtime or sidecar)
* No autonomous ML decisions
* No scope inference beyond the skill
* Execution systems (GitHub, Terraform, EKS) remain external

**ML posture (where relevant):**

* Advisory only
* Explainable
* Overrideable
* Confidence-aware
* Never blocks execution

**Change discipline:**

* Small diffs
* Explicit allowlists
* Clear Definition of Done
* No refactors unless explicitly requested

---

# Skill Groups Overview

Skills are grouped by **intent**, not by tool.

1. **Foundation & Hygiene**
2. **Narrative & Documentation**
3. **Glue Modeling & Semantics**
4. **API & Domain Contracts**
5. **Data & State Modeling**
6. **ML Advisory Capabilities**
7. **Observability & Failure Understanding**
8. **Demo & Review Enablement**
9. **Engine Operations** (Post-MVP — added 2026-04-04)

---

## 1. Foundation & Hygiene Skills

### SKILL-01 — Repository Structure & Hygiene

**Purpose:**
Establish or refine repo structure without altering architecture.

**Used when:**

* Initial scaffolding
* Adding new bounded areas
* Improving clarity for reviewers

**Allowed actions:**

* Create/move directories
* Add README placeholders
* Naming normalization

**Forbidden:**

* Architectural refactors
* Tool additions

**DoD:**

* Structure is clearer
* No behavior changes
* No new dependencies

---

## 2. Narrative & Documentation Skills

### SKILL-10 — README Narrative & Positioning

**Purpose:**
Align README with ForgeWorks identity, scope, and honesty.

**Used when:**

* Updating title/tagline
* Clarifying “what this is / is not”
* Improving reviewer comprehension

**Allowed actions:**

* Edit README.md
* Add sections (status, scope, philosophy)

**Forbidden:**

* Claiming unimplemented features
* Marketing language

**DoD:**

* Accurate
* Senior tone
* Scope-safe

---

### SKILL-11 — Architecture Explanation (Non-Diagram)

**Purpose:**
Explain architecture in words (layers, responsibilities, boundaries).

**Used when:**

* Clarifying Glue
* Explaining agentless design
* Interview prep artifacts

**Allowed actions:**

* Docs only
* No code

**DoD:**

* Clear separation of concerns
* Control vs cooperation distinction explicit

---

## 3. Glue Modeling & Semantics Skills

### SKILL-20 — Cross-Tool Semantic Modeling

**Purpose:**
Define shared concepts across tools (pipelines, steps, resources, changes).

**Used when:**

* Designing Glue core
* Normalizing GitHub + Terraform signals

**Allowed actions:**

* Domain models
* Conceptual schemas
* Mapping tables

**Forbidden:**

* Execution logic
* Real-time control hooks

**DoD:**

* Concepts are tool-agnostic
* Supports correlation & explanation

---

### SKILL-21 — Failure & Causality Modeling

**Purpose:**
Model how failures propagate across systems.

**Used when:**

* Pipeline failure analysis
* Terraform apply errors
* Log correlation

**Allowed actions:**

* Failure taxonomies
* Cause/effect models

**DoD:**

* Human-readable causality
* Machine-consumable structure

---

## 4. API & Domain Contract Skills

### SKILL-30 — API Contract Definition

**Purpose:**
Define intended API shape without overclaiming implementation.

**Used when:**

* Designing backend surface
* Planning frontend consumption

**Allowed actions:**

* Route definitions
* Request/response schemas
* OpenAPI stubs

**Forbidden:**

* Implementing execution logic

**DoD:**

* Clear contracts
* Explicit “planned vs implemented”

---

### SKILL-31 — Service Catalog Slice

**Purpose:**
Implement or model a minimal service catalog.

**Used when:**

* MVP backend slice
* Demo preparation

**Allowed actions:**

* CRUD (read-first)
* Seed data
* Minimal persistence

**Forbidden:**

* Enforcement logic
* Policy blocking

**DoD:**

* Services listable
* Ownership & metadata visible

---

## 5. Data & State Modeling Skills

### SKILL-40 — Relational Data Modeling

**Purpose:**
Define Postgres schemas aligned with Glue concepts.

**Used when:**

* Persisting services, runs, templates, signals

**Allowed actions:**

* SQL schemas
* Migrations
* ORM models

**Forbidden:**

* Over-optimization
* Infra provisioning

**DoD:**

* Normalized
* Evolvable
* Minimal

---

### SKILL-41 — State & Snapshot Modeling

**Purpose:**
Model point-in-time representations (pipeline run, plan result).

**Used when:**

* Debugging flows
* Historical analysis

**DoD:**

* Reproducible
* Immutable snapshots

---

## 6. ML Advisory Skills

### SKILL-50 — Recommendation Logic (Rule-Based First)

**Purpose:**
Implement advisory recommendations without ML complexity.

**Used when:**

* MVP template suggestion
* Baseline scoring

**Allowed actions:**

* Deterministic scoring
* Feature weighting

**DoD:**

* Explainable output
* Human override explicit

---

### SKILL-51 — ML-Assisted Recommendation

**Purpose:**
Introduce ML models to enhance ranking or pattern detection.

**Used when:**

* After rule-based baseline exists

**Allowed actions:**

* scikit-learn models
* Offline training
* Confidence scoring

**Forbidden:**

* Autonomous decisions
* Real-time control

**DoD:**

* ML augments, not replaces logic
* Explanations included

---

## 7. Observability & Failure Understanding Skills

### SKILL-60 — Log & Signal Normalization

**Purpose:**
Convert raw logs/events into structured signals.

**Used when:**

* GitHub Actions logs
* Terraform outputs

**Allowed actions:**

* Parsing
* Tagging
* Structuring

**DoD:**

* Tool-agnostic representation
* No agent assumptions

---

### SKILL-61 — Failure Explanation Output

**Purpose:**
Produce a single, coherent failure explanation.

**Used when:**

* Demo flow
* UX narrative

**DoD:**

* Answers: what failed, why, what changed, what next
* Evidence-linked, not guessed

---

## 8. Demo & Review Enablement Skills

### SKILL-70 — MVP Demo Flow Assembly

**Purpose:**
Assemble a believable end-to-end demo slice.

**Used when:**

* Interview prep
* Milestone demos

**Allowed actions:**

* Mock data
* Static flows
* Read-only views

**DoD:**

* Story is clear
* Scope is honest

---

### SKILL-80 — Review & Alignment Check

**Purpose:**
Evaluate changes against skill contract and doctrine.

**Used when:**

* Post-implementation review

**Checks:**

* Scope creep
* Control plane leakage
* Overclaiming
* Doctrine violations

**DoD:**

* Explicit feedback
* No silent approvals

---

## 9. Engine Operations Skills (Post-MVP)

> Added 2026-04-04 after Engine Phases 1-4 completion.
> These skills cover the operational and review aspects of the running engine.

---

### SKILL-90 — Platform Health Review

**Purpose:**
Evaluate the health of all ForgeWorks Engine components and identify degraded services.

**Used when:**

* Pre-deployment verification
* Post-incident review
* Status check requests

**Checks:**

* Kafka broker + topics (10 expected)
* Flink jobs (event-router, pattern-matcher, insight-generator)
* Webhook Gateway readiness
* Job Dispatcher readiness + adapter health
* Airflow components (scheduler, dag-processor, triggerer, api-server)
* MLflow tracking server

**DoD:**

* Status table per component (healthy/degraded/down)
* Actionable next step for any degraded component

---

### SKILL-91 — Code Quality & Security Audit

**Purpose:**
Deep review of code quality, security vulnerabilities, and error handling across ForgeWorks services.

**Used when:**

* After feature completion (per phase)
* Before merging major changes
* Periodic security posture review

**Review prompts:**

* Architecture: `review/01_architecture_review.md`
* Security: `review/02_code_quality_security.md`
* Production: `review/03_production_readiness.md`

**Checks:**

* Authentication (HMAC, JWT, fail-closed)
* Input validation (size limits, JSON parsing)
* Serialization safety (no empty bytes, no raw payloads in logs)
* K8s PodSecurity compliance (runAsNonRoot, drop ALL, seccomp)
* RBAC least-privilege
* Error code consistency (FW-* taxonomy)
* Dependency versions (CVEs)

**Output:**

* Findings categorized by severity (CRITICAL/HIGH/MEDIUM/LOW)
* Each finding: file, line, issue, risk, fix
* Export to `/outputs/{AGENT_NAME}/`

**DoD:**

* All HIGH+ findings have proposed fixes
* No silent approvals — every finding acknowledged

---

### SKILL-92 — Remediation Planning

**Purpose:**
Translate review findings into execution-ready remediation plans with phased priorities.

**Used when:**

* After SKILL-91 audit completes
* When Codex or other reviewer provides feedback

**Inputs:**

* Review output from SKILL-91
* Existing remediation plan (`codex/phase-1-2/REMEDIATION_PR_PLAN.md`)

**Allowed actions:**

* Categorize findings into Fix Now / Fix Before Production / Fix For Production
* Propose PR breakdown
* Define acceptance criteria per fix
* Track across review rounds

**DoD:**

* Each finding mapped to a phase and PR
* Done criteria defined
* No finding left unaddressed (even if verdict is "defer" or "disagree")

---

### SKILL-93 — Error Code Audit

**Purpose:**
Verify FW-* error code consistency across all services.

**Used when:**

* After adding new error codes
* Periodic consistency check

**Checks:**

* Namespace convention: `FW-{SERVICE}-{CATEGORY}-{NUMBER}`
* No duplicates (same code, different meanings)
* No orphans (documented but not in code, or vice versa)
* Sequential numbering (no gaps)

**Services to scan:**

* Python: `src/webhook-gateway/`, `src/job-dispatcher/`
* Java: `src/flink-jobs/event-router/`, `src/flink-jobs/pattern-matcher/`, `src/flink-jobs/insight-generator/`
* Docs: `roadmap/ACTION_PLAN_*.md`

**DoD:**

* Complete inventory table of all FW-* codes
* Duplicates and orphans flagged

---

### SKILL-94 — Schema Contract Validation

**Purpose:**
Verify that all implementations conform to canonical JSON Schemas.

**Used when:**

* After modifying EventEnvelope, PatternAlert, Insight, or JobSpec models
* Before merging cross-service changes

**Canonical schemas:**

* `schemas/event-envelope.schema.json`
* `schemas/pattern-alert.schema.json`

**Implementations to check:**

* Python: `src/webhook-gateway/app/schemas.py`, `src/job-dispatcher/app/schemas.py`
* Java: `src/flink-jobs/*/src/main/java/**/EventEnvelope.java`, `**/PatternAlert.java`

**Checks:**

* All required fields present
* Field types match
* `@schema` annotation present
* No undocumented fields added

**DoD:**

* Each implementation verified against canonical schema
* Drift flagged with specific field mismatches

---

### SKILL-95 — Test Coverage Analysis

**Purpose:**
Identify testing gaps across ForgeWorks services and recommend test additions.

**Used when:**

* Before production release
* After major feature additions

**Current state:**

* Webhook Gateway: 33 tests (body size limits)
* Job Dispatcher: 0 tests
* Flink Event Router: 0 tests
* Flink Pattern Matcher: 0 tests
* Flink Insight Generator: 0 tests
* E2E: `tests/e2e/test_full_pipeline.sh` (bash, manual)

**Checks:**

* List all public functions/endpoints without tests
* Identify critical paths with no coverage
* Recommend test types: unit, integration, E2E

**DoD:**

* Gap inventory per service
* Priority-ordered recommendations
* Effort estimate per test group

---

### SKILL-96 — Cost & Infrastructure Tradeoff Review

**Purpose:**
Evaluate cost-performance tradeoffs for infrastructure decisions.

**Used when:**

* Sizing compute (node types, replica counts)
* Choosing managed vs self-hosted (MSK vs Strimzi, RDS vs in-cluster Postgres)
* Storage tier decisions (S3 vs EBS vs emptyDir)

**Framework:**

* Cost axes: compute, storage, network, operations, licensing
* Performance axes: latency, throughput, durability, availability, scalability
* Break-even analysis: at what scale does option A beat option B?

**Past decisions (reference):**

* Strimzi over MSK (no vendor lock-in)
* RocksDB over hashmap (production durability)
* S3 over emptyDir (checkpoint persistence)
* t3.large × 4 (sufficient for dev)
* CPU over GPU training (small data, sklearn)

**DoD:**

* Decision matrix with scores
* Clear recommendation for dev vs production
* Trigger conditions to re-evaluate

---

## How This File Is Used (Operationally)

**Current team workflow (unchanged):**

1. Codex → MODE: ADVISE (recommends skills)
2. Human → compiles Skill Invocation Card
3. Claude → MODE: IMPLEMENT (executes skill)
4. Codex → MODE: REVIEW (validates against skill)

This file is the **shared language** that makes the workflow efficient.

---

## Final Note

If a task:

* does not map cleanly to an existing skill
* or requires bending constraints

→ **Stop. Define a new skill first.**

That is how ForgeWorks stays coherent.

---
