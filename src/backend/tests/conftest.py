"""Pytest fixtures for ForgeWorks tests."""

import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base, get_db
from app.main import app

# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Sample data factories
def create_team_data(
    name: str = "Test Team",
    slug: str | None = None,
    email: str = "team@test.com",
):
    """Create test team data."""
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
    """Create test template data."""
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
    """Create test service data."""
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
