"""Unit tests for frontmatter parsing + validation."""

from __future__ import annotations

import pytest

from forge_skills_mcp.frontmatter import (
    FrontmatterError,
    is_categorically_rejected,
    parse_frontmatter,
)

from .conftest import (
    CATEGORICALLY_REJECTED_SKILL,
    MISSING_SHA_SKILL,
    VALID_BODY,
    VALID_FRONTMATTER,
)


def test_parses_valid_frontmatter() -> None:
    fm, body = parse_frontmatter(VALID_FRONTMATTER + "\n" + VALID_BODY)
    assert fm.slug == "trailofbits/ask-questions-if-underspecified"
    assert fm.tier == 1
    assert fm.tool_scope == "read-only"
    assert fm.source_sha == "a" * 40
    assert body.startswith("When the user's request")


def test_rejects_missing_frontmatter_block() -> None:
    with pytest.raises(FrontmatterError, match="missing YAML frontmatter"):
        parse_frontmatter("Just a body, no frontmatter.\n")


def test_rejects_malformed_sha() -> None:
    with pytest.raises(FrontmatterError, match="40-char lowercase hex"):
        parse_frontmatter(MISSING_SHA_SKILL)


def test_categorically_rejected_scope_helper() -> None:
    assert is_categorically_rejected("git-write")
    assert is_categorically_rejected("workflow-write")
    assert not is_categorically_rejected("read-only")
    assert not is_categorically_rejected("network")


def test_accepts_compound_shell_execute_repo_write_scope() -> None:
    # PR 5 §H (trailofbits/differential-review) declares both shell-execute
    # (git/gh/find/grep invocations) and repo-write (writes a markdown report
    # file). Tier 2 in both halves. Loader must accept the compound enum.
    compound = VALID_FRONTMATTER.replace(
        "tool-scope: read-only",
        "tool-scope: shell-execute+repo-write",
    )
    fm, _ = parse_frontmatter(compound + "\nbody\n")
    assert fm.tool_scope == "shell-execute+repo-write"
    assert not is_categorically_rejected(fm.tool_scope)


def test_categorically_rejected_skill_still_parses() -> None:
    """The dangerous skill should parse fine (so we can refuse explicitly with
    a descriptive error rather than dropping it silently)."""
    fm, _ = parse_frontmatter(CATEGORICALLY_REJECTED_SKILL)
    assert fm.tool_scope == "git-write"
    assert is_categorically_rejected(fm.tool_scope)


def test_slug_must_have_vendor_prefix() -> None:
    bad = VALID_FRONTMATTER.replace(
        "slug: trailofbits/ask-questions-if-underspecified",
        "slug: ask-questions-if-underspecified",
    )
    with pytest.raises(FrontmatterError, match="'<vendor>/<name>'"):
        parse_frontmatter(bad + "\nbody\n")
