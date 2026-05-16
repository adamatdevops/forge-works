"""MCP server bootstrap + tool handlers.

Tools exposed (per ACTION_PLAN_SKILL_LOADERS.md §3.3):
  list_skills   — summary list with optional tier_max filter
  get_skill     — full SKILL.md content + frontmatter for a slug
  find_skills   — substring match on name + body (no LLM; pure string match)
  loader_health — version, skills_count, .skills path, last_scan_at
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__
from .audit import log_call, log_refusal
from .frontmatter import is_categorically_rejected
from .scanner import LoadedSkill, ScanResult, scan


def _skill_summary(s: LoadedSkill) -> dict[str, Any]:
    fm = s.frontmatter
    return {
        "slug": fm.slug,
        "vendor": fm.vendor,
        "name": fm.name,
        "tier": fm.tier,
        "tool_scope": fm.tool_scope,
        "context_cost_tokens": fm.context_cost_tokens,
        "source_sha": fm.source_sha,
    }


class SkillsState:
    """Holds the most recent scan; rescans on every list call (Phase 1 simplicity)."""

    def __init__(self, skills_root: Path) -> None:
        self.skills_root = skills_root
        self.last_scan: ScanResult | None = None
        self.last_scan_at: str | None = None

    def rescan(self) -> ScanResult:
        self.last_scan = scan(self.skills_root)
        self.last_scan_at = datetime.now(UTC).isoformat()
        return self.last_scan


def build_server(skills_root: Path) -> FastMCP:
    """Construct the MCP server with tools bound to a given .skills/ root."""
    state = SkillsState(skills_root=skills_root)
    server = FastMCP("forge-skills")

    @server.tool()
    def list_skills(tier_max: int | None = None) -> dict[str, Any]:
        """List vendored skills under `.skills/`, optionally filtered by tier ceiling.

        Args:
            tier_max: If set, only include skills with `tier <= tier_max`.

        Returns:
            {"skills": [...summary...], "errors": [{path, reason}, ...], "count": N}
        """
        log_call("list_skills", {"tier_max": tier_max})
        result = state.rescan()
        summaries = [_skill_summary(s) for s in result.skills]
        if tier_max is not None:
            summaries = [s for s in summaries if s["tier"] <= tier_max]
        errors = [{"path": str(e.path), "reason": e.reason} for e in result.errors]
        return {"skills": summaries, "errors": errors, "count": len(summaries)}

    @server.tool()
    def get_skill(slug: str) -> dict[str, Any]:
        """Return full SKILL.md content + frontmatter for a slug.

        Returns `{error: "not-found" | "categorically-rejected", ...}` on refusal.
        """
        log_call("get_skill", {"slug": slug})
        result = state.rescan()
        for s in result.skills:
            if s.frontmatter.slug == slug:
                if is_categorically_rejected(s.frontmatter.tool_scope):
                    log_refusal("get_skill", slug, "categorically-rejected tool-scope")
                    return {
                        "error": "categorically-rejected",
                        "reason": (
                            f"tool-scope {s.frontmatter.tool_scope!r} rejected per "
                            f"AGENT_SKILLS.md §2E (git-write and workflow-write)"
                        ),
                    }
                return {
                    "frontmatter": s.frontmatter.model_dump(by_alias=True),
                    "body": s.body,
                    "path": str(s.path),
                }
        log_refusal("get_skill", slug, "not-found")
        return {"error": "not-found", "slug": slug}

    @server.tool()
    def find_skills(query: str, tier_max: int | None = None) -> dict[str, Any]:
        """Substring search across skill name + body. No LLM ranking — pure string match.

        Args:
            query: Substring to search (case-insensitive).
            tier_max: Optional tier ceiling.

        Returns:
            {"matches": [...summary...], "count": N}
        """
        log_call("find_skills", {"query": query, "tier_max": tier_max})
        result = state.rescan()
        q = query.lower()
        matches: list[dict[str, Any]] = []
        for s in result.skills:
            if tier_max is not None and s.frontmatter.tier > tier_max:
                continue
            haystack = f"{s.frontmatter.name}\n{s.body}".lower()
            if q in haystack:
                matches.append(_skill_summary(s))
        return {"matches": matches, "count": len(matches)}

    @server.tool()
    def loader_health() -> dict[str, Any]:
        """Smoke-test endpoint — version, skills count, root path, last scan timestamp."""
        log_call("loader_health")
        if state.last_scan is None:
            state.rescan()
        assert state.last_scan is not None
        return {
            "version": __version__,
            "skills_count": len(state.last_scan.skills),
            "skills_errors_count": len(state.last_scan.errors),
            "skills_root": str(state.skills_root),
            "last_scan_at": state.last_scan_at,
        }

    return server
