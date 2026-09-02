"""AB-038 smoke tests — prove the PG fixture chain works end-to-end."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import isolated_session

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def _head_revision() -> str:
    """Read the current Alembic head revision from disk (script directory)."""
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg).get_current_head()


class TestConftestInfrastructure:
    """AB-038 fixture-chain smoke tests."""

    @pytest.mark.asyncio
    async def test_engine_reachable(self, test_engine):
        """`test_engine` connects to a live PG."""
        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_migrations_at_head(self, test_session: AsyncSession):
        """DB is at the current Alembic head, and all expected tables exist."""
        # AB-038 CF9 (2026-09-02 Codex loop): version check catches
        # never-migrated / stuck-at-older-revision cases the table subset can't.
        expected_head = _head_revision()
        result = await test_session.execute(text("SELECT version_num FROM alembic_version"))
        actual_head = result.scalar()
        assert actual_head == expected_head, (
            f"DB at revision {actual_head!r}, expected head {expected_head!r} — "
            f"`command.upgrade(cfg, 'head')` in `_migrated_pg_url` did not run "
            f"or ran against a different DB."
        )
        # Diagnostic supplement: enumerate the concrete tables so a missing
        # migration produces a message pointing at which table is missing.
        expected_tables = {
            "actions",
            "alembic_version",
            "anomalies",
            "recommendations",
            "refresh_tokens",
            "services",
            "teams",
            "templates",
            "users",
        }
        result = await test_session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        actual_tables = {row[0] for row in result.all()}
        missing = expected_tables - actual_tables
        assert not missing, f"Tables missing after `alembic upgrade head`: {missing}"

    @pytest.mark.asyncio
    async def test_savepoint_isolation(self, test_engine):
        """SAVEPOINT proof: commit in session A, absence in session B — one atomic test."""
        # AB-038 CF4 (2026-09-02 Codex loop): use the isolated_session context
        # manager twice sequentially inside one test. Order-independent — no
        # cross-test source-ordering assumption; pytest-randomly-safe.
        probe_slug = "sp-isolation-probe"

        # Session A: write + commit inside the outer transaction (opens a SAVEPOINT
        # via join_transaction_mode='create_savepoint'). Row IS visible here.
        async with isolated_session(test_engine) as session_a:
            await session_a.execute(
                text(
                    "INSERT INTO teams (id, name, slug, description, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :n, :s, :d, NOW(), NOW())"
                ),
                {"n": probe_slug, "s": probe_slug, "d": "AB-038 SAVEPOINT probe"},
            )
            await session_a.commit()
            result = await session_a.execute(
                text("SELECT COUNT(*) FROM teams WHERE slug = :s"), {"s": probe_slug}
            )
            assert result.scalar() == 1, "commit inside outer trans should be visible in-session"

        # Session A exited; the outer transaction rolled back, discarding every
        # SAVEPOINT the test committed inside its scope.

        # Session B: fresh outer transaction — the probe row must NOT be here.
        async with isolated_session(test_engine) as session_b:
            result = await session_b.execute(
                text("SELECT COUNT(*) FROM teams WHERE slug = :s"), {"s": probe_slug}
            )
            assert result.scalar() == 0, (
                "SAVEPOINT rollback failed — probe row leaked across isolated_session boundaries"
            )
