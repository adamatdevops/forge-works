"""Test fixtures for ForgeWorks. See research/db_audit/ALEMBIC_DRIFT_RECON.md v0.2 §"Post-execution retrospective" (AB-038)."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from app.db.base import get_db
from app.main import app

# Repo layout: this file lives at src/backend/tests/conftest.py; alembic.ini +
# alembic/ sit next to tests/ under src/backend/.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Overridable via env for container-image pinning discipline.
_POSTGRES_IMAGE = os.environ.get("FORGE_TEST_PG_IMAGE", "postgres:14")


def _to_asyncpg_url(url: str) -> str:
    """Normalize a PG URL to the asyncpg driver."""
    # AB-038 CF6 (2026-09-02 Codex loop): explicit ?sslmode= rejection —
    # asyncpg's parameter is `ssl=`, not `sslmode=`; silently forwarding a
    # libpq-style value produces confusing runtime errors far from the URL
    # site. Fail loudly at the boundary and let the caller translate.
    if "sslmode=" in url:
        raise ValueError(
            f"URL contains libpq-style ?sslmode=; asyncpg expects ?ssl=. "
            f"Translate before setting FORGE_TEST_DATABASE_URL. Got: {url!r}"
        )
    for old, new in (
        ("postgresql+psycopg2://", "postgresql+asyncpg://"),
        ("postgresql+psycopg://", "postgresql+asyncpg://"),  # psycopg v3
        ("postgresql://", "postgresql+asyncpg://"),
    ):
        if url.startswith(old):
            return url.replace(old, new, 1)
    if url.startswith("postgresql+asyncpg://"):
        return url
    raise ValueError(f"Unsupported DB URL scheme for AB-038 test fixtures: {url!r}")


@pytest.fixture(scope="session")
def _pg_url() -> Generator[str, None, None]:
    """Session-scoped PG source: FORGE_TEST_DATABASE_URL env, else testcontainers."""
    # AB-038 CF2 (2026-09-02 Codex loop): dedicated env var so pytest never
    # silently touches the developer's actual dev database via the app's own
    # DATABASE_URL. FORGE_TEST_DATABASE_URL is opt-in and set explicitly in CI.
    env_url = os.environ.get("FORGE_TEST_DATABASE_URL")
    if env_url:
        yield _to_asyncpg_url(env_url)
        return
    # Import inside the branch so environments that never hit it (i.e., CI)
    # don't pay the import cost or fail if testcontainers isn't installed.
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError as exc:  # pragma: no cover - install-time check
        raise RuntimeError(
            "AB-038: `testcontainers[postgres]` required for the local-dev "
            "fixture path. Install via `pip install -e .[dev]`, or set "
            "FORGE_TEST_DATABASE_URL to point at an empty test-only PG."
        ) from exc
    with PostgresContainer(_POSTGRES_IMAGE) as pg:
        yield _to_asyncpg_url(pg.get_connection_url())


@pytest.fixture(scope="session")
def _migrated_pg_url(_pg_url: str) -> str:
    """Apply Alembic migrations once to _pg_url; return same URL."""
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    # alembic.ini uses `script_location = alembic` — that path is relative to
    # CWD, which pytest doesn't guarantee is src/backend. Force absolute.
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    # AB-038 CF5 (2026-09-02 Codex loop): Alembic Config uses ConfigParser
    # interpolation on set_main_option; percent-encoded URL chars (e.g.
    # p%40ss for p@ss) trigger `ValueError: invalid interpolation syntax`.
    # Escape by doubling. Verified empirically in the loop's reconciled.md.
    cfg.set_main_option("sqlalchemy.url", _pg_url.replace("%", "%%"))
    command.upgrade(cfg, "head")
    return _pg_url


@pytest_asyncio.fixture(scope="session")
async def test_engine(_migrated_pg_url: str) -> AsyncGenerator:
    """Session-scoped async engine over the migrated PG (NullPool: no cross-loop reuse)."""
    # AB-038 CF1 (2026-09-02 Codex loop): NullPool prevents pooled asyncpg
    # connections from being reused across pytest-asyncio 1.x function-scoped
    # event loops — every connect opens fresh on the caller's loop and closes
    # on release. Slower per checkout than a real pool, but the correct default
    # for pytest fixtures. See SQLAlchemy docs §"Using an Asyncio Event Loop
    # with the Same Engine".
    engine = create_async_engine(_migrated_pg_url, echo=False, future=True, poolclass=NullPool)
    yield engine
    await engine.dispose()


@asynccontextmanager
async def isolated_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """SAVEPOINT-rollback session: outer trans never commits; SAVEPOINTs discarded on exit."""
    # Extracted from the test_session fixture so smoke tests can drive multiple
    # sequential isolated sessions inside a single test without depending on
    # cross-test source-ordering (AB-038 CF4, 2026-09-02 Codex loop).
    async with engine.connect() as conn:
        outer = await conn.begin()
        try:
            session = AsyncSession(
                bind=conn,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )
            try:
                yield session
            finally:
                await session.close()
        finally:
            await outer.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test AsyncSession with SAVEPOINT rollback isolation."""
    async with isolated_session(test_engine) as s:
        yield s


@pytest_asyncio.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client whose Depends(get_db) yields the isolated session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# Sample data factories (unchanged from pre-AB-038 conftest).
def create_team_data(
    name: str = "Test Team",
    slug: str | None = None,
    email: str = "team@test.com",
):
    """Test team payload."""
    return {
        "id": str(uuid4()),
        "name": name,
        "slug": slug or name.lower().replace(" ", "-"),
        "description": f"Test team: {name}",
        "email": email,
        "slack_channel": "#test-team",
    }


def create_template_data(
    name: str = "Test Template",
    slug: str | None = None,
    workload_type: str = "api",
    language: str = "python",
):
    """Test template payload."""
    return {
        "id": str(uuid4()),
        "name": name,
        "slug": slug or name.lower().replace(" ", "-"),
        "description": f"Test template: {name}",
        "version": "1.0.0",
        "workload_type": workload_type,
        "language": language,
        "capabilities": ["api", "crud"],
        "ideal_for": ["low_latency", "rest_api"],
        "stack": {"framework": "fastapi", "db": "postgresql"},
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "is_active": True,
        "is_recommended": True,
    }


def create_service_data(
    name: str = "Test Service",
    team_id: str | None = None,
    template_id: str | None = None,
):
    """Test service payload."""
    return {
        "name": name,
        "description": f"Test service: {name}",
        "team_id": team_id or str(uuid4()),
        "template_id": template_id,
        "tier": "standard",
        "repository_url": "https://github.com/test/test-service",
        "repository_branch": "main",
        "tags": ["test", "demo"],
        "metadata": {"env": "test"},
    }
