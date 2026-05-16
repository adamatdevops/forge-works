"""Shared fixtures: build a `.skills/` tree on disk for scanner + server tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

VALID_FRONTMATTER = dedent(
    """\
    ---
    name: ask-questions-if-underspecified
    vendor: trailofbits
    slug: trailofbits/ask-questions-if-underspecified
    source-url: https://officialskills.sh/trailofbits/skills/ask-questions-if-underspecified
    source-canonical: https://github.com/trailofbits/skills/tree/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/ask-questions-if-underspecified
    source-sha: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    audited: 2026-05-15
    goal: 1
    tier: 1
    tool-scope: read-only
    target-agents: [claude-code, codex]
    context-cost-tokens: 900
    owner: adamatdevops
    ---
    """
)

VALID_BODY = (
    "When the user's request is underspecified, ask up to 3 clarifying questions before acting.\n"
)

CATEGORICALLY_REJECTED_SKILL = dedent(
    """\
    ---
    name: dangerous-skill
    vendor: malicious
    slug: malicious/dangerous-skill
    source-url: https://example.com
    source-canonical: https://github.com/malicious/skills/tree/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/dangerous
    source-sha: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    audited: 2026-05-15
    goal: 4
    tier: 3
    tool-scope: git-write
    target-agents: [claude-code]
    context-cost-tokens: 500
    owner: adamatdevops
    ---

    This skill would auto-commit to git. The loader must categorically refuse.
    """
)

MISSING_SHA_SKILL = dedent(
    """\
    ---
    name: incomplete
    vendor: trailofbits
    slug: trailofbits/incomplete
    source-url: https://example.com
    source-canonical: https://github.com/trailofbits/skills/tree/HEAD/incomplete
    source-sha: not-a-real-sha
    audited: 2026-05-15
    goal: 1
    tier: 1
    tool-scope: read-only
    target-agents: [claude-code]
    context-cost-tokens: 200
    owner: adamatdevops
    ---

    Bad sha format.
    """
)


@pytest.fixture
def skills_tree(tmp_path: Path) -> Path:
    """Create a `.skills/` tree with one valid skill and return the root path."""
    root = tmp_path / ".skills"
    skill_dir = root / "trailofbits" / "ask-questions-if-underspecified"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(VALID_FRONTMATTER + "\n" + VALID_BODY)
    return root


@pytest.fixture
def skills_tree_with_errors(tmp_path: Path) -> Path:
    """A `.skills/` tree containing one valid skill + one categorically-rejected
    skill + one with malformed SHA. Used to test error reporting and refusal."""
    root = tmp_path / ".skills"

    valid_dir = root / "trailofbits" / "ask-questions-if-underspecified"
    valid_dir.mkdir(parents=True)
    (valid_dir / "SKILL.md").write_text(VALID_FRONTMATTER + "\n" + VALID_BODY)

    rejected_dir = root / "malicious" / "dangerous-skill"
    rejected_dir.mkdir(parents=True)
    (rejected_dir / "SKILL.md").write_text(CATEGORICALLY_REJECTED_SKILL)

    bad_dir = root / "trailofbits" / "incomplete"
    bad_dir.mkdir(parents=True)
    (bad_dir / "SKILL.md").write_text(MISSING_SHA_SKILL)

    return root
