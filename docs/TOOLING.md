# ForgeWorks Development Tooling

> Opinionated tooling choices for code quality, formatting, and development workflow.

## Overview

| Category           | Frontend (TypeScript) | Backend (Python) | Repo-Wide           |
| ------------------ | --------------------- | ---------------- | ------------------- |
| Linting            | ESLint                | Ruff             | -                   |
| Formatting         | Prettier              | Ruff (formatter) | -                   |
| Type Checking      | TypeScript            | mypy             | -                   |
| Git Hooks          | -                     | -                | Husky + lint-staged |
| Commit Linting     | -                     | -                | commitlint          |
| Security           | Snyk, Socket.dev      | bandit, Snyk     | Trivy               |
| Dependency Updates | -                     | -                | Dependabot          |
| Testing            | Vitest                | pytest           | -                   |
| Coverage           | v8                    | pytest-cov       | -                   |

---

## Linters

### ESLint (Frontend)

**Purpose:** Static analysis for JavaScript/TypeScript to find problems and enforce code style.

**Why:** Industry standard for JS/TS. Integrates with Next.js out of the box. Catches bugs, enforces best practices, and ensures consistent code style.

**Status:** Already installed via `eslint-config-next`

```bash
pnpm lint              # Run ESLint
pnpm lint --fix        # Auto-fix issues
```

### Ruff (Backend)

**Purpose:** Extremely fast Python linter written in Rust. Replaces Flake8, isort, pyupgrade, and more.

**Why:** 10-100x faster than traditional Python linters. Single tool replaces multiple. Used by major projects (FastAPI, Pandas, Airflow).

**Status:** To be configured

```bash
ruff check .           # Run linter
ruff check . --fix     # Auto-fix issues
```

---

## Formatters

### Prettier (Frontend)

**Purpose:** Opinionated code formatter for JavaScript, TypeScript, JSON, CSS, Markdown.

**Why:** Industry standard. Eliminates style debates. Consistent formatting across the team. Integrates with all major editors.

**Status:** To be installed

```bash
pnpm format            # Format all files
pnpm format --check    # Check without writing
```

### Ruff Formatter (Backend)

**Purpose:** Fast Python formatter (Black-compatible) built into Ruff.

**Why:** Same speed benefits as Ruff linter. Drop-in replacement for Black. Single tool for linting + formatting.

**Status:** To be configured

```bash
ruff format .          # Format all Python files
ruff format --check .  # Check without writing
```

---

## Type Checking

### TypeScript (Frontend)

**Purpose:** Static type checking for JavaScript/TypeScript.

**Why:** Catches type errors at compile time. Improves IDE support. Self-documenting code. Already part of Next.js.

**Status:** Already installed

```bash
pnpm typecheck         # Run type checking
```

### mypy (Backend)

**Purpose:** Static type checker for Python.

**Why:** Catches type errors before runtime. Works with Python type hints. Used by major Python projects.

**Status:** To be installed

```bash
mypy app/              # Check types
```

---

## Git Hooks

### Husky

**Purpose:** Modern Git hooks manager. Runs scripts on git events (pre-commit, pre-push, etc.).

**Why:** Industry standard for Git hooks in JS/Node projects. Easy setup. Works with any scripting language.

**Status:** To be installed

```bash
# Automatically runs on git commit/push
# Configured in .husky/
```

### lint-staged

**Purpose:** Run linters only on staged git files.

**Why:** Fast feedback loop. Only checks files you're committing. Works with Husky.

**Status:** To be installed

```bash
# Runs automatically via Husky pre-commit hook
# Configured in package.json or .lintstagedrc
```

---

## Commit Standards

### commitlint

**Purpose:** Lint commit messages against Conventional Commits specification.

**Why:** Enforces consistent commit messages. Feeds release-please for automatic changelog generation and semver bumps (planned, task #23). See `docs/decisions/RELEASE_TOOLING.md`.

**Status:** To be installed

**Format:**

```
type(scope): description

feat(api): add template recommendation endpoint
fix(db): resolve connection pool exhaustion
docs(readme): update installation instructions
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

---

## Security Scanning

### Snyk (Frontend + Backend)

**Purpose:** Find and fix vulnerabilities in dependencies, containers, and code.

**Why:** Industry leader in security scanning. Better coverage than npm audit. CI/CD integration. Used by Fortune 500 companies.

**Status:** To be configured (Phase 2)

```bash
snyk test              # Scan for vulnerabilities
snyk monitor           # Monitor for new vulnerabilities
```

### Socket.dev (Frontend)

**Purpose:** Detect supply chain attacks and malicious npm packages.

**Why:** Goes beyond CVEs - detects typosquatting, malicious code, protestware. GitHub integration.

**Status:** To be configured (Phase 2)

### Trivy (Containers)

**Purpose:** Comprehensive vulnerability scanner for containers, filesystems, and git repos.

**Why:** Fast, accurate, supports multiple targets. Used by major cloud providers. Open source.

**Status:** To be configured (Phase 2)

```bash
trivy fs .             # Scan filesystem
trivy image <image>    # Scan container image
```

### bandit (Backend)

**Purpose:** Security-focused static analysis for Python code.

**Why:** Finds common security issues (SQL injection, hardcoded passwords, etc.). Used in enterprise Python projects.

**Status:** To be installed (Phase 2)

```bash
bandit -r app/         # Scan for security issues
```

### Dependabot / Renovate (Repo-Wide)

**Purpose:** Automated dependency updates via pull requests.

**Why:** Keeps dependencies current. Automatic security patches. Industry standard for GitHub repos.

**Status:** To be configured

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/src/frontend"
    schedule:
      interval: "weekly"
  - package-ecosystem: "pip"
    directory: "/src/backend"
    schedule:
      interval: "weekly"
```

---

## Testing

### Vitest (Frontend)

**Purpose:** Fast Vite-native testing framework for JavaScript/TypeScript.

**Why:** Blazing fast. Compatible with Jest API. Native ESM support. Works great with React.

**Status:** Already installed

```bash
pnpm test              # Run tests in watch mode
pnpm test:run          # Run tests once
pnpm test:coverage     # Run with coverage
```

### pytest (Backend)

**Purpose:** Python testing framework.

**Why:** Industry standard for Python. Simple yet powerful. Extensive plugin ecosystem.

**Status:** Already installed

```bash
pytest                 # Run all tests
pytest -v              # Verbose output
pytest --cov=app       # With coverage
```

---

## Code Coverage

### v8 (Frontend)

**Purpose:** Native V8 coverage provider for Vitest.

**Why:** Fast. Accurate. Built into Vitest.

**Status:** Configured in vitest.config.mts

### pytest-cov (Backend)

**Purpose:** Coverage plugin for pytest.

**Why:** Integrates with pytest. Supports multiple output formats. Can enforce coverage thresholds.

**Status:** To be configured

---

## Bundle Analysis (Frontend)

### @next/bundle-analyzer

**Purpose:** Visualize and analyze Next.js bundle sizes.

**Why:** Identify large dependencies. Optimize bundle size. Improve load times.

**Status:** To be installed (Phase 2)

```bash
ANALYZE=true pnpm build  # Generate bundle analysis
```

---

## Implementation Priority

### Phase 1: Core Quality (Now)

- [x] ESLint (frontend)
- [x] TypeScript (frontend)
- [x] Vitest (frontend)
- [ ] Prettier (frontend)
- [ ] Ruff (backend)
- [ ] Husky + lint-staged
- [ ] commitlint

### Phase 2: Security & Optimization (Later)

- [ ] bandit (backend)
- [ ] mypy (backend)
- [ ] Dependabot
- [ ] @next/bundle-analyzer
- [ ] pytest-cov thresholds

### Phase 3: Advanced (Future)

- [ ] CodeQL / Snyk
- [ ] SonarQube
- [ ] Lighthouse CI
- [ ] Performance budgets

---

## Configuration Files

| Tool        | Config File              |
| ----------- | ------------------------ |
| ESLint      | `eslint.config.mjs`      |
| Prettier    | `.prettierrc`            |
| Ruff        | `ruff.toml`              |
| TypeScript  | `tsconfig.json`          |
| Husky       | `.husky/`                |
| lint-staged | `.lintstagedrc`          |
| commitlint  | `commitlint.config.js`   |
| Dependabot  | `.github/dependabot.yml` |

---

## Scripts Summary

```json
{
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "format": "turbo run format",
    "typecheck": "turbo run typecheck",
    "clean": "turbo run clean && rm -rf node_modules",
    "dev:backend": "turbo run dev --filter=@forge-works/backend",
    "dev:frontend": "turbo run dev --filter=@forge-works/frontend"
  }
}
```

---

## Editor Integration

All tools have excellent VS Code / Cursor integration:

- **ESLint:** `dbaeumer.vscode-eslint`
- **Prettier:** `esbenp.prettier-vscode`
- **Ruff:** `charliermarsh.ruff`
- **Python:** `ms-python.python`

Recommended `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  }
}
```

---

_Last Updated: January 2025_
