"""Drift fixes — F1 actions.metadata rename + F4/F6 redundant-index drops

Revision ID: 20260901_000001
Revises: 20250114_000001
Create Date: 2026-09-01

Fixes surfaced by research/db_audit/ALEMBIC_DRIFT_RECON.md v0.1 (post-Codex round-1):

- F1: rename ``actions.metadata`` → ``actions.extra_metadata`` to match the
  ``Action.extra_metadata`` model attribute. The original initial-schema
  migration used ``metadata`` (Python-reserved attribute name conflicting
  with SQLAlchemy's ``Base.metadata``); commit ``0a8db1d`` fixed the
  ``services`` table's rename but missed ``actions``. Any ORM read or
  write of ``Action`` would fail against the current DB — dormant only
  because ``Action`` has no active call sites in ``src/backend/app/``.

- F4: drop the redundant non-unique ``ix_users_email`` index. The
  ``users.email`` column has a UNIQUE constraint (from the auth migration's
  ``sa.Column("email", ..., unique=True, ...)``) whose auto-generated
  backing index already handles equality lookups. The extra non-unique
  named index is duplicate storage; the paired model change removes
  ``index=True`` from ``User.email`` so the two representations align.

- F6: drop the redundant non-unique ``ix_refresh_tokens_token_hash``
  index for the same reason. The paired model change tightens
  ``RefreshToken.token_hash`` to ``String(64), unique=True`` (previously
  drifted as ``String(255), index=True``, no UNIQUE).

Loop audit trail: research/feedback_loops/db_audit-ALEMBIC_DRIFT_RECON/20260901T081525Z/

Note: no DDL is needed for F5 (ENUM value/name drift) — the paired model
changes add ``values_callable=`` so SQLAlchemy sends the correct lowercase
values that already exist in the DB's ENUM types. Same rationale for
F6's length dimension: the DB is already VARCHAR(64); only the model was
declared as VARCHAR(255).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260901_000001"
down_revision: str = "20250114_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # F1 — rename actions.metadata → actions.extra_metadata.
    # PostgreSQL preserves data + column-level server_default across ALTER RENAME.
    op.alter_column("actions", "metadata", new_column_name="extra_metadata")

    # F4 — drop redundant non-unique ix_users_email.
    # The users.email UNIQUE constraint's auto-index continues to enforce
    # uniqueness AND handle equality lookups.
    op.drop_index("ix_users_email", table_name="users")

    # F6 — drop redundant non-unique ix_refresh_tokens_token_hash.
    # The refresh_tokens.token_hash UNIQUE constraint's auto-index continues
    # to enforce uniqueness AND handle equality lookups.
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")


def downgrade() -> None:
    # Reverse in reverse order to restore the pre-fix state exactly.
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_users_email", "users", ["email"])
    op.alter_column("actions", "extra_metadata", new_column_name="metadata")
