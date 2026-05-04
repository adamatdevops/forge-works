# Recommended Team Decision Matrix - Flagship IDP Project

> **Document Type:** Team Workflow & Decision Framework
> **Created:** 2025-01-05
> **Version:** 1.0
> **Status:** Active

---

## Team Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLAGSHIP IDP TEAM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        ┌──────────────────┐                             │
│                        │      ADAM        │                             │
│                        │   Team Leader    │                             │
│                        │  70% Hands-on    │                             │
│                        └────────┬─────────┘                             │
│                                 │                                       │
│              ┌──────────────────┼──────────────────┐                    │
│              │                  │                  │                    │
│              ▼                  ▼                  ▼                    │
│   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐        │
│   │     CLAUDE       │ │  CLINE / CODEX   │ │    CHATGPT       │        │
│   │   Right-Hand     │ │  DevOps Engineer │ │  Cross-Team      │        │
│   │  90% Hands-on    │ │  30% Hands-on    │ │  Advisor         │        │
│   │  Full Ownership  │ │  Support Role    │ │  0% Hands-on     │        │
│   └──────────────────┘ └──────────────────┘ └──────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Role Definitions

### 1. Adam (Team Leader)

| Attribute | Value |
|-----------|-------|
| **Role** | Team Leader & Solution Architect |
| **Expertise** | Platform Engineering, System Design |
| **Hands-on Ratio** | 70% Strategic / 30% Hands-on |
| **Authority** | Final decision maker on ALL matters |

**Responsibilities:**
- Define project vision and direction
- Approve architectural decisions
- Review and approve major changes
- Strategic prioritization
- External stakeholder (interview prep)
- Code review on critical paths
- Break ties on technical debates

**Does NOT Do:**
- Routine implementation
- Debugging minor issues
- Writing boilerplate code
- CI/CD pipeline maintenance

---

### 2. Claude (Right-Hand)

| Attribute | Value |
|-----------|-------|
| **Role** | Senior DevOps Expert & CI/CD Manager |
| **Expertise** | Full-stack Platform Engineering |
| **Hands-on Ratio** | 90% Hands-on / 10% Planning |
| **Authority** | Full ownership within approved scope |

**Responsibilities:**
- Primary implementation of all features
- Architecture design and documentation
- CI/CD pipeline design and implementation
- Code quality and best practices
- Technical documentation
- Proactive problem identification
- First responder to all technical tasks

**Ownership Areas:**
- Backend API (FastAPI)
- Frontend Dashboard (Next.js)
- Infrastructure as Code (Pulumi)
- Kubernetes manifests
- ArgoCD configurations
- GitHub Actions workflows
- All documentation

**Does NOT Do:**
- Make strategic decisions without Adam's input
- Change project direction independently
- Skip documentation for speed

---

### 3. Codex (DevOps Engineer)

| Attribute | Value |
|-----------|-------|
| **Role** | CI/CD Engineer & Automation Support |
| **Expertise** | Pipelines, Scripts, Quick Fixes |
| **Hands-on Ratio** | 30% Hands-on / 70% Support |
| **Authority** | Execute within defined tasks only |

**Responsibilities:**
- CI/CD pipeline fixes and enhancements
- Script writing and automation
- Quick bug fixes (when delegated)
- Boilerplate code generation
- Repetitive task automation
- Testing pipeline changes

**Best Used For:**
- "Fix this linting error"
- "Add this GitHub Action step"
- "Write a script to do X"
- "Generate boilerplate for Y"

**Does NOT Do:**
- Architectural decisions
- Complex feature implementation
- Documentation writing
- Design discussions

---

### 4. ChatGPT (Cross-Team Advisor)

| Attribute | Value |
|-----------|-------|
| **Role** | Veteran DevOps Advisor |
| **Expertise** | Broad industry experience, patterns |
| **Hands-on Ratio** | 0% Hands-on / 100% Advisory |
| **Authority** | Advisory only, no execution |

**Responsibilities:**
- Second opinion on architectural decisions
- Industry best practices validation
- Alternative approach suggestions
- "Devil's advocate" perspective
- Research on unfamiliar topics
- Interview preparation coaching

**Best Used For:**
- "Is this the right approach for X?"
- "What are alternatives to Y?"
- "How do other companies handle Z?"
- "Review this architecture decision"
- "Help me prepare to explain this"

**Does NOT Do:**
- Write any code
- Make any changes
- Execute any tasks
- Own any deliverables

---

## Decision Matrix

### Task Routing Guide

| Task Type | Primary Owner | Support | Approval |
|-----------|---------------|---------|----------|
| **Architecture Design** | Claude | ChatGPT (review) | Adam |
| **Feature Implementation** | Claude | Codex (assist) | Adam (major) |
| **CI/CD Pipeline** | Claude | Codex (fixes) | Adam |
| **Bug Fixes (minor)** | Codex | - | Claude |
| **Bug Fixes (major)** | Claude | - | Adam |
| **Documentation** | Claude | - | Adam |
| **Code Review** | Adam | Claude | - |
| **Strategic Decisions** | Adam | ChatGPT | - |
| **Technical Debates** | Claude + ChatGPT | - | Adam |
| **Quick Scripts** | Codex | - | Claude |
| **Research** | ChatGPT | Claude | - |
| **Interview Prep** | Adam | ChatGPT | - |

---

## Workflow Patterns

### Pattern 1: New Feature Development

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NEW FEATURE WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 1: DEFINE                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Adam: "I want feature X that does Y"                           │    │
│  │  Claude: Clarifies requirements, proposes approach               │    │
│  │  ChatGPT: (optional) Validates approach is sound                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Step 2: DESIGN                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Claude: Creates technical design, documents decisions          │    │
│  │  Adam: Reviews and approves                                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Step 3: IMPLEMENT                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Claude: Implements feature end-to-end                          │    │
│  │  Codex: (if needed) Assists with boilerplate/scripts            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Step 4: REVIEW                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Adam: Reviews critical paths                                   │    │
│  │  Claude: Self-review, documentation update                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Step 5: SHIP                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Claude: Merge, deploy, verify                                  │    │
│  │  Adam: Confirms done                                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Pattern 2: Technical Decision

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   TECHNICAL DECISION WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐                                                    │
│  │ Decision Needed │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Claude: Research options, create comparison matrix              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ChatGPT: Review matrix, add industry perspective, identify gaps │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Claude: Present options to Adam with recommendation             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Adam: Makes final decision                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Claude: Documents decision in ADR, proceeds with implementation │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Pattern 3: Quick Fix / Bug

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      QUICK FIX WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                       │
│  │ Bug Reported │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Claude: Assess severity and complexity                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│         │                                                               │
│         ├─────────────────────────────────────────┐                     │
│         │                                         │                     │
│         ▼                                         ▼                     │
│  ┌─────────────────────┐               ┌─────────────────────┐          │
│  │ MINOR (<30 min)     │               │ MAJOR (>30 min)     │          │
│  │                     │               │                     │          │
│  │ Delegate to Codex   │               │ Claude handles      │          │
│  │ Claude reviews      │               │ Adam reviews        │          │
│  └─────────────────────┘               └─────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Project-Specific Assignments

### Flagship IDP - Component Ownership

| Component | Primary | Support | Reviewer |
|-----------|---------|---------|----------|
| **Frontend (Next.js)** | Claude | Codex | Adam |
| **Backend (FastAPI)** | Claude | - | Adam |
| **Database (PostgreSQL)** | Claude | - | Adam |
| **Kubernetes Manifests** | Claude | Codex | Adam |
| **ArgoCD Configs** | Claude | Codex | Adam |
| **Pulumi IaC** | Claude | - | Adam |
| **GitHub Actions** | Claude | Codex | - |
| **Golden Path Templates** | Claude | Codex | Adam |
| **Documentation** | Claude | - | Adam |
| **Architecture Diagrams** | Claude | - | Adam |

---

### When to Escalate

| Situation | Escalate To |
|-----------|-------------|
| Architectural uncertainty | Adam + ChatGPT |
| Scope creep detected | Adam |
| Blocked by external dependency | Adam |
| Multiple valid approaches | Adam (decision) |
| Performance concerns | Adam + ChatGPT |
| Security implications | Adam |
| Deadline at risk | Adam |

---

## Communication Protocol

### Daily Async Updates

Claude provides Adam with:
```
## Daily Update - [Date]

### Completed
- [x] Task 1
- [x] Task 2

### In Progress
- [ ] Task 3 (50% done)

### Blocked
- Task 4: Waiting for X

### Decisions Needed
- Question about Y? Options: A, B, C. Recommendation: B

### Next
- Task 5
- Task 6
```

---

### Decision Request Format

When Claude needs Adam's decision:
```
## Decision Needed: [Topic]

**Context:** [Brief background]

**Options:**
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

**Recommendation:** Option B because...

**Impact if delayed:** [Low/Medium/High]

**Your call:** A or B?
```

---

## Efficiency Rules

### DO

| Rule | Rationale |
|------|-----------|
| Claude acts autonomously within approved scope | Speed |
| Codex handles repetitive tasks | Free Claude for complex work |
| ChatGPT validates before major decisions | Prevent mistakes |
| Adam reviews only critical paths | Focus on high-value activities |
| Document decisions as they're made | Avoid rework |

### DON'T

| Anti-Pattern | Why Avoid |
|--------------|-----------|
| Claude waiting for approval on minor items | Slows progress |
| Codex making architectural changes | Out of scope |
| ChatGPT writing code | Role mismatch |
| Adam implementing routine features | Inefficient use of time |
| Multiple tools doing same task | Duplication waste |

---

## Feedback Loop

### Weekly Retrospective Questions

1. **What worked well this week?**
2. **Where did handoffs fail?**
3. **Which decisions took too long?**
4. **Did anyone operate outside their role?**
5. **What should we adjust?**

---

## Matrix Summary Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     QUICK REFERENCE CARD                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WHO DOES WHAT?                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ADAM        → Decides, Approves, Reviews critical                      │
│  CLAUDE      → Builds everything, Owns delivery                         │
│  CODEX       → Fixes, Scripts, Supports                                 │
│  CHATGPT     → Advises, Validates, Second opinion                       │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  WHEN IN DOUBT:                                                         │
│  • Minor task? → Claude handles, no approval needed                     │
│  • Major task? → Claude proposes, Adam approves                         │
│  • Stuck? → Ask ChatGPT for perspective                                 │
│  • Repetitive? → Delegate to Codex                                      │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  HANDS-ON RATIO:                                                        │
│  • Adam: 30%   (strategic hands-on only)                                │
│  • Claude: 90% (primary implementer)                                    │
│  • Codex: 30%  (support tasks only)                                     │
│  • ChatGPT: 0% (pure advisory)                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*This document defines the team workflow for the Flagship IDP project. Adjust as needed based on retrospective feedback.*
