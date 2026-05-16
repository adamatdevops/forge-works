"""Integration tests — call the server's tool functions directly.

stdio transport testing (full MCP roundtrip) lives outside this file because
it requires a child-process harness; smoke that via the README's manual
verification block instead.
"""

from __future__ import annotations

from pathlib import Path

from forge_skills_mcp.server import build_server


def _tools_by_name(server) -> dict[str, object]:
    """Extract registered tools from FastMCP for direct call in tests."""
    # FastMCP exposes tools via `server._tool_manager.tools` (private but stable).
    return {name: t.fn for name, t in server._tool_manager._tools.items()}


def test_list_skills_returns_valid_summaries(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["list_skills"]()
    assert result["count"] == 1
    assert result["skills"][0]["slug"] == "trailofbits/ask-questions-if-underspecified"
    assert result["skills"][0]["tier"] == 1
    assert result["errors"] == []


def test_list_skills_filters_by_tier_max(skills_tree_with_errors: Path) -> None:
    server = build_server(skills_root=skills_tree_with_errors)
    tools = _tools_by_name(server)
    # tier_max=1 should exclude the Tier-3 dangerous-skill
    result = tools["list_skills"](tier_max=1)
    slugs = {s["slug"] for s in result["skills"]}
    assert "trailofbits/ask-questions-if-underspecified" in slugs
    assert "malicious/dangerous-skill" not in slugs


def test_get_skill_returns_full_content(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["get_skill"](slug="trailofbits/ask-questions-if-underspecified")
    assert "frontmatter" in result
    assert "body" in result
    assert result["frontmatter"]["slug"] == "trailofbits/ask-questions-if-underspecified"
    assert "clarifying questions" in result["body"]


def test_get_skill_unknown_returns_not_found(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["get_skill"](slug="nonexistent/slug")
    assert result == {"error": "not-found", "slug": "nonexistent/slug"}


def test_get_skill_categorically_rejected_scope(skills_tree_with_errors: Path) -> None:
    server = build_server(skills_root=skills_tree_with_errors)
    tools = _tools_by_name(server)
    result = tools["get_skill"](slug="malicious/dangerous-skill")
    assert result["error"] == "categorically-rejected"
    assert "git-write" in result["reason"]


def test_find_skills_substring_match(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["find_skills"](query="clarifying")
    assert result["count"] == 1
    assert result["matches"][0]["slug"] == "trailofbits/ask-questions-if-underspecified"


def test_find_skills_no_match(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["find_skills"](query="zzz-no-match-zzz")
    assert result == {"matches": [], "count": 0}


def test_loader_health_returns_metadata(skills_tree: Path) -> None:
    server = build_server(skills_root=skills_tree)
    tools = _tools_by_name(server)
    result = tools["loader_health"]()
    assert result["version"] == "0.1.0"
    assert result["skills_count"] == 1
    assert result["skills_errors_count"] == 0
    assert result["skills_root"] == str(skills_tree)
    assert result["last_scan_at"] is not None
