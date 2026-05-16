"""Audit logger — Phase 1 stub.

Phase 2 (per ACTION_PLAN_SKILL_LOADERS.md §2) promotes this to a structured
append-only log with rotation. Phase 1 writes minimal stdout-only entries that
land in the MCP transport debug log if the parent agent captures it.
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime

_LOGGER = logging.getLogger("forge_skills_mcp.audit")


def configure_logging(verbose: bool = False) -> None:
    """Initialize the audit logger to write to stderr (stdout is reserved for stdio MCP)."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [forge-skills-mcp] %(levelname)s: %(message)s")
    )
    _LOGGER.handlers = [handler]
    _LOGGER.setLevel(level)
    _LOGGER.propagate = False


def log_call(tool: str, params: dict[str, object] | None = None) -> None:
    """Record a tool invocation for the Phase 2 audit trail."""
    ts = datetime.now(UTC).isoformat()
    params_str = "" if not params else f" params={params}"
    _LOGGER.info("call tool=%s ts=%s%s", tool, ts, params_str)


def log_refusal(tool: str, slug: str, reason: str) -> None:
    """Record that a request was categorically refused (e.g., git-write scope)."""
    _LOGGER.warning("refused tool=%s slug=%s reason=%s", tool, slug, reason)
