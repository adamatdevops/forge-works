# Contributing to ForgeWorks

Thank you for your interest in contributing to ForgeWorks! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a new branch for your changes
5. Make your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Node.js 18+
- PNPM 8+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/forge-works.git
cd forge-works

# Install Node dependencies
pnpm install

# Set up Python environment
cd src/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
cd ../..

# Start infrastructure
docker-compose up -d

# Set up database
pnpm --filter @forge-works/backend db:setup

# Verify setup
pnpm lint
pnpm test
```

## Making Changes

### Branch Naming (Trunk-Based Development)

We use trunk-based development with short-lived feature branches.

| Type    | Pattern                          | Example                            |
| ------- | -------------------------------- | ---------------------------------- |
| Feature | `feature/<ticket>-<description>` | `feature/FW-123-add-metrics-layer` |
| Bug Fix | `fix/<ticket>-<description>`     | `fix/FW-456-button-alignment`      |
| Hotfix  | `hotfix/<ticket>-<description>`  | `hotfix/FW-789-security-patch`     |
| Docs    | `docs/<description>`             | `docs/update-api-docs`             |

**Rules:**

- Keep branches short-lived (< 2 days ideal)
- Squash merge to main
- Delete branches after merge

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting, no code change
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance tasks

Examples:

```
feat(api): add template recommendation endpoint
fix(db): resolve connection pool exhaustion
docs(readme): update installation instructions
```

## Release Notes

forge-works uses **Conventional Commits + a hand-curated `CHANGELOG.md`**.
Release-tooling rationale lives in
[`docs/decisions/RELEASE_TOOLING.md`](docs/decisions/RELEASE_TOOLING.md);
the day-to-day flow is in [`RELEASE.md`](RELEASE.md).

Short version:

- Commit subjects are **one sentence**, Conventional Commits format
  (e.g. `feat(api): add template recommendation endpoint`).
- Narrative for releases lives in [`CHANGELOG.md`](CHANGELOG.md), grouped by
  version with SHA references.
- Tags are cut manually from `main` for now; release-please will automate this
  in task #23.

You don't need to add changeset files — that tooling was removed in favor of
the convention above.

## Pull Request Process

1. **Update your branch** with the latest main:

   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all checks** before submitting:

   ```bash
   pnpm lint
   pnpm test
   ```

3. **Create the PR** with:
   - Clear title following commit conventions
   - Description of changes
   - Link to related issues
   - Screenshots for UI changes

4. **Address review feedback** promptly

5. **Squash commits** if requested

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New code has test coverage
- [ ] Commit messages follow Conventional Commits
- [ ] Documentation updated if needed
- [ ] No console.log or debug statements
- [ ] No hardcoded secrets or credentials

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for all functions
- Run `ruff check` and `ruff format` before committing
- Docstrings for public functions and classes

```python
async def get_service(
    db: AsyncSession,
    service_id: str,
) -> Service | None:
    """
    Retrieve a service by ID.

    Args:
        db: Database session
        service_id: UUID of the service

    Returns:
        Service if found, None otherwise
    """
    ...
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use named exports
- Run ESLint before committing

```typescript
interface ServiceCardProps {
  service: Service;
  onSelect: (id: string) => void;
}

export function ServiceCard({ service, onSelect }: ServiceCardProps) {
  ...
}
```

### General

- Keep functions small and focused
- Write self-documenting code
- Add comments for complex logic
- Avoid premature optimization

## Testing

### Backend Tests

```bash
# Run all backend tests
pnpm test:backend

# Run with coverage
pnpm --filter @forge-works/backend test:cov

# Run specific test file
cd src/backend
pytest tests/integration/test_api_services.py -v
```

### Frontend Tests

```bash
# Run all frontend tests
pnpm test:frontend

# Run in watch mode
cd src/frontend
pnpm test --watch
```

### Test Guidelines

- Write tests for new features
- Maintain existing test coverage
- Use descriptive test names
- Follow Arrange-Act-Assert pattern

```python
async def test_create_service_with_valid_data():
    # Arrange
    service_data = {"name": "test-service", ...}

    # Act
    response = await client.post("/api/v1/services", json=service_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "test-service"
```

## Documentation

- Update README.md for user-facing changes
- Add/update docstrings for code changes
- Update API documentation for endpoint changes
- Keep CHANGELOG.md updated

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep formatting consistent
- Test all code snippets

## Questions?

If you have questions about contributing, feel free to:

1. Check existing issues and discussions
2. Open a new issue with your question
3. Reach out to maintainers

Thank you for contributing to ForgeWorks!
