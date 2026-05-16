"""Unit tests for the .skills/ scanner."""

from __future__ import annotations

from pathlib import Path

from forge_skills_mcp.scanner import scan


def test_scan_finds_valid_skill(skills_tree: Path) -> None:
    result = scan(skills_tree)
    assert len(result.skills) == 1
    assert len(result.errors) == 0
    s = result.skills[0]
    assert s.frontmatter.slug == "trailofbits/ask-questions-if-underspecified"
    assert s.body.strip().startswith("When the user's request")


def test_scan_missing_root_returns_empty(tmp_path: Path) -> None:
    result = scan(tmp_path / "does-not-exist")
    assert result.skills == []
    assert result.errors == []


def test_scan_ignores_files_outside_pattern(skills_tree: Path) -> None:
    # Stray files at the wrong nesting level should be ignored, not error.
    (skills_tree / "stray.md").write_text("not a skill\n")
    (skills_tree / "trailofbits" / "stray-at-vendor-level.md").write_text("nope\n")
    result = scan(skills_tree)
    assert len(result.skills) == 1
    assert len(result.errors) == 0


def test_scan_reports_errors_separately(skills_tree_with_errors: Path) -> None:
    result = scan(skills_tree_with_errors)
    # Two parseable skills (valid + categorically-rejected), one error (bad SHA).
    assert len(result.skills) == 2
    assert len(result.errors) == 1
    slugs = {s.frontmatter.slug for s in result.skills}
    assert "trailofbits/ask-questions-if-underspecified" in slugs
    assert "malicious/dangerous-skill" in slugs
    assert "40-char lowercase hex" in result.errors[0].reason


def test_scan_rejects_path_frontmatter_mismatch(tmp_path: Path) -> None:
    """If the filesystem path implies a different vendor/slug than the
    frontmatter declares, that's an error."""
    root = tmp_path / ".skills"
    wrong_dir = root / "wrong-vendor" / "ask-questions-if-underspecified"
    wrong_dir.mkdir(parents=True)
    from .conftest import VALID_BODY, VALID_FRONTMATTER

    (wrong_dir / "SKILL.md").write_text(VALID_FRONTMATTER + "\n" + VALID_BODY)

    result = scan(root)
    assert len(result.skills) == 0
    assert len(result.errors) == 1
    assert "path/frontmatter mismatch" in result.errors[0].reason
