# Monorepo Setup - TurboRepo + PNPM

> **Purpose:** Document the monorepo architecture and tooling decisions for ForgeWorks IDP.

---

## Overview

ForgeWorks uses a **monorepo architecture** managed by:

| Tool | Purpose |
|------|---------|
| **PNPM** | Package manager with workspace support |
| **TurboRepo** | Build system and task orchestration |
| **package.json wrappers** | Unified commands for Python backend |

### Why This Stack?

| Requirement | Solution |
|-------------|----------|
| Unified commands across languages | TurboRepo task pipeline |
| Fast dependency installation | PNPM with hoisting |
| Task caching | TurboRepo local cache |
| Parallel execution | TurboRepo parallel tasks |
| Python + TypeScript | package.json wrappers for Python |

---

## Directory Structure

```
forge-works/
├── package.json              # Root - workspace scripts
├── pnpm-workspace.yaml       # PNPM workspace definition
├── turbo.json                # TurboRepo pipeline config
├── pnpm-lock.yaml            # Lockfile (auto-generated)
├── node_modules/             # Root dependencies (turbo)
│
├── src/
│   ├── backend/              # Python FastAPI
│   │   ├── package.json      # Turbo wrapper (calls Python tools)
│   │   ├── pyproject.toml    # Python dependencies
│   │   ├── app/              # Application code
│   │   └── tests/            # Python tests
│   │
│   ├── frontend/             # Next.js (Phase 3)
│   │   ├── package.json      # Native pnpm/turbo
│   │   └── ...
│   │
│   └── shared/               # Shared utilities
│       ├── package.json      # Shared types/utils
│       └── ...
│
├── docs/                     # Documentation
├── scripts/                  # Development scripts
└── docker-compose.yml        # Local infrastructure
```

---

## Configuration Files

### 1. Root `package.json`

Defines workspace-level scripts that TurboRepo orchestrates:

```json
{
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "format": "turbo run format"
  }
}
```

**Key points:**
- All scripts delegate to TurboRepo
- Filter specific packages: `pnpm test --filter=@forge-works/backend`
- Convenience scripts: `pnpm dev:backend`, `pnpm test:frontend`

### 2. `pnpm-workspace.yaml`

Defines which directories are workspace packages:

```yaml
packages:
  - "src/backend"
  - "src/frontend"
  - "src/shared"
```

### 3. `turbo.json`

Defines the task pipeline and caching:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Key concepts:**
- `dependsOn: ["^build"]` - Run dependency builds first
- `outputs` - Directories to cache
- `cache: false` - Don't cache (for dev servers)
- `persistent: true` - Keep running (for dev servers)

### 4. Backend `package.json` (Wrapper)

Wraps Python commands for TurboRepo integration:

```json
{
  "name": "@forge-works/backend",
  "scripts": {
    "dev": "uvicorn app.main:app --reload",
    "test": "pytest -v --cov=app",
    "lint": "ruff check . && ruff format --check .",
    "format": "ruff format ."
  }
}
```

**How it works:**
1. TurboRepo sees `@forge-works/backend` as a workspace
2. TurboRepo calls `pnpm run test` in that directory
3. The script executes `pytest` (Python tool)
4. TurboRepo caches the results

---

## Commands Reference

### Development

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all dev servers |
| `pnpm dev:backend` | Start only backend |
| `pnpm dev:frontend` | Start only frontend |

### Testing

| Command | Description |
|---------|-------------|
| `pnpm test` | Run all tests |
| `pnpm test:backend` | Run backend tests |
| `pnpm test:frontend` | Run frontend tests |

### Linting & Formatting

| Command | Description |
|---------|-------------|
| `pnpm lint` | Lint all packages |
| `pnpm format` | Format all packages |
| `pnpm lint:backend` | Lint backend only |

### Database (Backend)

| Command | Description |
|---------|-------------|
| `pnpm --filter @forge-works/backend migrate` | Run migrations |
| `pnpm --filter @forge-works/backend seed` | Seed database |
| `pnpm --filter @forge-works/backend db:setup` | Migrate + seed |

### Cleanup

| Command | Description |
|---------|-------------|
| `pnpm clean` | Clean all packages |
| `turbo clean` | Clear TurboRepo cache |

---

## Initial Setup

### Prerequisites

```bash
# Install Node.js 18+ and PNPM
brew install node pnpm

# Verify versions
node --version   # >= 18.0.0
pnpm --version   # >= 8.0.0
```

### Installation

```bash
# Clone and enter repo
git clone https://github.com/adamatdevops/forge-works.git
cd forge-works

# Install dependencies (installs turbo + workspace packages)
pnpm install

# Setup Python environment (backend)
cd src/backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cd ../..

# Start infrastructure
docker-compose up -d

# Setup database
pnpm --filter @forge-works/backend db:setup

# Start development
pnpm dev
```

---

## Caching

TurboRepo provides intelligent caching:

### Local Cache

```bash
# Cache stored in
node_modules/.cache/turbo

# Clear cache
turbo clean
```

### What Gets Cached

| Task | Cached Outputs |
|------|----------------|
| `build` | `dist/`, `.next/`, `*.egg-info/` |
| `test` | `coverage/`, `htmlcov/`, `.coverage` |
| `lint` | None (fast enough) |
| `typecheck` | None |

### Cache Behavior

```bash
# First run - executes all tasks
pnpm test
# Output: FULL execution, ~30s

# Second run - uses cache
pnpm test
# Output: FULL TURBO, ~0.5s (if no changes)

# After code change - partial execution
# Only re-runs affected packages
```

---

## Filtering

Run commands on specific packages:

```bash
# By package name
pnpm test --filter=@forge-works/backend
pnpm dev --filter=@forge-works/frontend

# By directory
pnpm test --filter=./src/backend

# Multiple packages
pnpm test --filter=@forge-works/backend --filter=@forge-works/shared

# Exclude packages
pnpm test --filter=!@forge-works/frontend
```

---

## Adding New Packages

### Adding a New Workspace Package

1. Create the directory:
```bash
mkdir -p src/new-package
```

2. Create `package.json`:
```json
{
  "name": "@forge-works/new-package",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "...",
    "build": "...",
    "test": "..."
  }
}
```

3. Add to `pnpm-workspace.yaml`:
```yaml
packages:
  - "src/backend"
  - "src/frontend"
  - "src/shared"
  - "src/new-package"  # Add this
```

4. Install dependencies:
```bash
pnpm install
```

---

## Troubleshooting

### Common Issues

**Issue:** `Command not found: turbo`
```bash
# Solution: Install dependencies
pnpm install
```

**Issue:** Backend Python commands fail
```bash
# Solution: Activate Python venv
cd src/backend
source venv/bin/activate
cd ../..
pnpm test:backend
```

**Issue:** Cache seems stale
```bash
# Solution: Clear turbo cache
turbo clean
pnpm test
```

**Issue:** Workspace package not found
```bash
# Solution: Check pnpm-workspace.yaml and run
pnpm install
```

---

## Design Decisions

### Why TurboRepo + PNPM?

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Bazel** | Too complex for portfolio project |
| **Nx** | More opinionated, larger footprint |
| **Lerna** | Deprecated, less maintained |
| **Pants** | Better for Python-only monorepos |
| **Just PNPM workspaces** | No task caching or orchestration |

### Why package.json Wrappers for Python?

- **Unified interface**: Same commands (`pnpm test`) for all languages
- **TurboRepo integration**: Caching, dependency graph, parallel execution
- **Developer experience**: Single entry point for all tasks
- **Trade-off accepted**: Python tools run under Node shell, minimal overhead

### Future Considerations

- **Remote caching**: TurboRepo supports remote cache (Vercel)
- **Pants migration**: If Python complexity grows significantly
- **CI optimization**: TurboRepo `--affected` for PR builds

---

## References

- [TurboRepo Documentation](https://turbo.build/repo/docs)
- [PNPM Workspaces](https://pnpm.io/workspaces)
- [TurboRepo + Python Discussion](https://github.com/vercel/turborepo/discussions/1077)

---

*Document created: 2025-01-07*
*Last updated: 2025-01-07*
