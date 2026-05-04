# Workflow & Process Guidelines

Lessons learned and best practices from portfolio project development.

---

## 1) Project Initialization Checklist

Before starting a new project:

- [ ] Create GitHub repo with proper name (see NAMING_CONVENTION.md)
- [ ] Copy templates from `/templates/` directory
- [ ] Customize .gitignore, .editorconfig, linters for project type
- [ ] **CRITICAL:** Ensure `.gitignore` includes `CONTEXT.md` and `PROMPT.md`
- [ ] Set up initial README.md structure
- [ ] Create `docs/diagrams/` directory
- [ ] Create `docs/project/` directory with project management docs
- [ ] Initialize CHANGELOG.md
- [ ] Plan GitHub Topics (add after project completion - see section below)
- [ ] **Verify:** Run `git ls-files | grep -E "CONTEXT|PROMPT"` - must return nothing

### Project Management Docs

Copy templates from `templates/project/` to your repo's `docs/project/`:

```bash
cp -r templates/project/ your-repo/docs/project/
```

This creates:
```
docs/project/
├── PROJECT.md              # Master overview with links
├── ACCEPTANCE_CRITERIA.md  # Completion conditions
├── CONSTRAINTS.md          # Boundaries and limitations
└── DELIVERABLES.md         # Expected outputs tracking
```

**Why `docs/project/` instead of root?**
- Keeps root directory clean
- Groups project management docs together
- Links from PROJECT.md provide easy navigation
- Professional structure for enterprise-style repos

---

## 1.1) GitHub Topics Planning

Plan topics at project start, add them to GitHub repo settings after completion.

### Topic Categories

| Category | Example Topics |
|----------|----------------|
| **Domain** | `devops`, `platform-engineering`, `devsecops`, `mlops`, `fintech` |
| **Technology** | `kubernetes`, `terraform`, `github-actions`, `docker`, `aws` |
| **Patterns** | `ci-cd`, `gitops`, `infrastructure-as-code`, `policy-as-code` |
| **Security** | `supply-chain-security`, `sbom`, `container-security`, `sast` |
| **Purpose** | `portfolio`, `reference-implementation`, `best-practices` |

### Recommended Topics by Project Type

**CI/CD Pipeline Projects:**
```
devops, ci-cd, github-actions, pipeline, automation,
security-scanning, devsecops, portfolio
```

**Supply Chain Security Projects:**
```
supply-chain-security, sbom, cosign, sigstore, container-security,
policy-as-code, opa, devsecops, slsa, portfolio
```

**Infrastructure Projects:**
```
infrastructure-as-code, terraform, aws, kubernetes,
platform-engineering, gitops, portfolio
```

**MLOps Projects:**
```
mlops, mlflow, machine-learning, feature-store,
model-deployment, ai, fintech, portfolio
```

### Topic Limits
- GitHub allows **max 20 topics** per repo
- Use 8-12 well-chosen topics for best discoverability
- Always include: `portfolio`, primary domain, key technologies

### When to Add Topics
Add topics **after project completion** when:
- [ ] All pipelines are green
- [ ] Documentation is complete
- [ ] README has architecture diagram
- [ ] CHANGELOG is finalized

**How:** Repository → Settings → Topics (or click "Add topics" on repo page)

---

## 1.2) Sample Application Documentation

If your project includes a sample app or validation workload, **document its purpose** in the README.

### Why This Matters
Without explanation, reviewers may see:
> "a sophisticated collection of pipelines and tools"

With proper framing, they see:
> "a real governance pattern, validated using a workload designed for platform-level testing"

### Required README Section

Add a section called **"Sample Application (Pipeline Validation Workload)"** that includes:

1. Path to the sample app
2. Explanation of its purpose (validation workload, not product code)
3. List of pipeline functions it enables
4. Emphasis on end-to-end operational flow

### Template

```markdown
## Sample Application (Pipeline Validation Workload)

This repository includes a sample service located at:

\`\`\`
src/app/
\`\`\`

The application serves as a **realistic workload** to exercise the pipeline end-to-end. It enables validation of:

- **SAST scanning** (Semgrep)
- **Dependency & container scanning** (Snyk)
- **SBOM generation** (Syft/CycloneDX)
- **Image signing & attestation** (Cosign/Sigstore)
- **Policy-as-Code evaluation** (OPA/Conftest)

The purpose of this sample app is not to act as a product service, but to provide a **controlled execution surface** for demonstrating a secure software supply-chain flow in a way that mirrors real enterprise environments.

This ensures the project showcases a **true operational pipeline** — not just a collection of tools, but a complete end-to-end security governance pattern.
```

### Placement
Add this section after "Repository Structure" and before "Quick Start".

---

## 2) Required Files for Every Project

| File | Purpose | When to Create |
|------|---------|----------------|
| `README.md` | Main documentation | Day 1 |
| `CHANGELOG.md` | Development history | Day 1, update continuously |
| `LICENSE` | MIT license | Day 1 |
| `CONTRIBUTING.md` | Engineering standards | Day 1 |
| `SECURITY.md` | Security policy | Day 1 |
| `docs/architecture.md` | Detailed architecture | Before completion |
| `docs/diagrams/*.svg` | Visual architecture | Before completion |
| `docs/project/PROJECT.md` | Project overview | Day 1 |
| `docs/project/ACCEPTANCE_CRITERIA.md` | Completion conditions | Day 1 |
| `docs/project/CONSTRAINTS.md` | Boundaries & limits | Day 1 |
| `docs/project/DELIVERABLES.md` | Output tracking | Day 1, update continuously |

---

## 3) CHANGELOG.md Standards

Every project must have a CHANGELOG documenting:

- Version milestones
- Phase-by-phase development history
- Commit references with descriptions
- Differentiation between components/workflows
- Configuration reference tables

**Template structure:**
```markdown
# Changelog

## [1.0.0] - YYYY-MM-DD

### Project Milestone
Summary of what was achieved.

---

## Development History

### Phase N: Phase Name

#### feat/fix: Description (commit-hash)
- What changed
- Why it changed
- Impact
```

---

## 4) Architecture Diagrams

### Tools
- **Excalidraw** - Primary diagramming tool
- Export formats:
  - `.excalidraw.json` - Editable source (commit this)
  - `.svg` - GitHub README display
  - `.png` - LinkedIn/social sharing (2x scale)

### Diagram Location
```
docs/diagrams/
├── pipeline-architecture.excalidraw.json  # Source
├── pipeline-architecture.svg               # GitHub
└── pipeline-architecture.png               # LinkedIn
```

### README Integration
```markdown
## Architecture Overview

![Pipeline Architecture](docs/diagrams/pipeline-architecture.svg)
```

---

## 5) Pipeline Status Badges

Add live GitHub Actions status badges at top of README:

```markdown
[![Pipeline Name](https://github.com/USERNAME/REPO/actions/workflows/WORKFLOW.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/WORKFLOW.yml)
```

Place immediately after the title, before any descriptive text.

---

## 6) Local Config Files (CONTEXT.md, PROMPT.md)

### CRITICAL: These Files Must NEVER Be Tracked

`CONTEXT.md` and `PROMPT.md` are **local configuration files** for AI assistance.
They must be:
1. Listed in `.gitignore`
2. **Not tracked** by git (even if in .gitignore)

### Problem: .gitignore Doesn't Remove Already-Tracked Files

If a file was committed before being added to `.gitignore`, it remains tracked!

```bash
# Check if these files are tracked (BAD if they appear)
git ls-files | grep -E "CONTEXT|PROMPT"
```

### Required Steps for EVERY New Project

**Step 1:** Add to `.gitignore` immediately (Day 1):
```gitignore
# Local AI configuration (never commit)
PROMPT.md
CONTEXT.md
```

**Step 2:** Verify files aren't tracked:
```bash
git ls-files | grep -E "CONTEXT|PROMPT"
```

**Step 3:** If files ARE tracked, remove from git (keeps local copy):
```bash
git rm --cached CONTEXT.md PROMPT.md
git commit -m "chore: remove local config files from tracking"
git push
```

### Add to Project Initialization Checklist

Before first commit:
- [ ] `.gitignore` includes `CONTEXT.md` and `PROMPT.md`
- [ ] Verify: `git ls-files | grep -E "CONTEXT|PROMPT"` returns nothing

After any commit:
- [ ] Re-verify no local config files are tracked

---

## 7) Git Commit Standards

### Message Format
```
type(scope): description

Body explaining what and why.
```

### AI Attribution Policy
**Do NOT include AI attribution in commits:**
- ❌ `Co-Authored-By: Claude ...`
- ❌ `🤖 Generated with [Claude Code]`
- ✅ Standard commit messages only

**Why:** GitHub Contributors sidebar shows co-authors, which may create hiring bias.

**Fix existing commits (if needed):**
```bash
git filter-branch --msg-filter 'sed "/Co-Authored-By:/d; /Generated with \[Claude/d"' --force HEAD~N..HEAD
git push --force
```

---

## 8) GitHub Actions Best Practices

### Job Dependencies & Outputs
Jobs can **only** access outputs from jobs in their `needs` array:

```yaml
# ❌ WRONG - deploy-prod can't access build.outputs
deploy-prod:
  needs: [deploy-staging]  # Missing 'build'
  steps:
    - run: echo ${{ needs.build.outputs.digest }}  # UNDEFINED!

# ✅ CORRECT
deploy-prod:
  needs: [build, deploy-staging]  # Include 'build'
  steps:
    - run: echo ${{ needs.build.outputs.digest }}  # Works!
```

### Hybrid Enforcement Pattern
Use `ENFORCE_SECURITY` toggle for gradual security adoption:

```yaml
env:
  ENFORCE_SECURITY: 'false'  # 'false' = report-only, 'true' = blocking

jobs:
  security-scan:
    steps:
      - name: Run scan
        continue-on-error: ${{ env.ENFORCE_SECURITY != 'true' }}
```

### Downstream Jobs with `if: always()`
When using `if: always()`, add conditions to prevent running when dependencies failed:

```yaml
deploy:
  needs: [build]
  if: always() && needs.build.result == 'success'
```

---

## 9) Security Tool Configuration

### Semgrep - Exclude Test Fixtures
Create `.semgrepignore` to exclude intentional vulnerabilities:

```
examples/invalid/
tests/fixtures/vulnerable/
```

### Gitleaks - False Positive Allowlist
Create `.gitleaks.toml` with allowlist:

```toml
[allowlist]
description = "Allowlist for false positives"
regexes = [
    '''localhost''',
    '''example\.com'''
]
paths = [
    '''tests/.*''',
    '''examples/.*'''
]
```

---

## 10) OPA/Rego Policy Standards

### Use v0.46+ Syntax
Always use modern Rego syntax from the start:

```rego
package policy

import rego.v1  # Required for new syntax

default allow := false  # Use := not =

# Use 'if' before rule bodies
allow if {
    condition
}

# Use 'contains' for partial sets
deny contains msg if {
    condition
    msg := "Error message"
}

# Use 'some' for iteration
deny contains msg if {
    some container in input.containers
    container.privileged
    msg := sprintf("Container %s is privileged", [container.name])
}
```

### Test Locally Before Pushing
```bash
opa test src/policies/ -v
```

---

## 11) Docker Build Configuration

### Always Specify Paths
When Dockerfile isn't in root, specify both context and file:

```yaml
- uses: docker/build-push-action@v5
  with:
    context: src/app           # Build context directory
    file: src/app/Dockerfile   # Explicit Dockerfile path
    push: true
```

---

## 12) Multi-Language Security Scanning

When creating security scanning pipelines, include sample files for each language:

```
src/
├── app/              # Node.js (package.json)
├── python-service/   # Python (requirements.txt)
├── go-service/       # Go (go.mod)
terraform/            # Terraform (*.tf)
pulumi/               # Pulumi (Pulumi.yaml)
```

This ensures:
- Language detection works correctly
- Security scanners have files to scan
- Pipeline demonstrates multi-language capability

---

## 13) Project Naming Consistency

Before publishing:
- [ ] Search for old/placeholder names in all files
- [ ] Replace with final project name
- [ ] Check: README, docs, configs, comments, tests

```bash
# Find stale references
grep -ri "old-name" --include="*.md" --include="*.yml" --include="*.yaml"
```

---

## 14) Pre-Publish Checklist

Before considering a project complete:

- [ ] All pipelines green
- [ ] CHANGELOG.md complete with development history
- [ ] Architecture diagram (SVG) in README
- [ ] Pipeline status badges at top of README
- [ ] No AI attribution in git history (or removed)
- [ ] No stale project names in docs
- [ ] Templates customized (removed generic placeholders)
- [ ] README "Production Considerations" section filled
- [ ] LICENSE file present
- [ ] **CRITICAL:** `CONTEXT.md` and `PROMPT.md` NOT tracked (run: `git ls-files | grep -E "CONTEXT|PROMPT"`)
