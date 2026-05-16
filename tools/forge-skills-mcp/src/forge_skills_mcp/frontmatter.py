"""SKILL.md frontmatter parsing + validation.

See ACTION_PLAN_SKILL_LOADERS.md §3.2 for the frontmatter schema.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator

# AGENT_SKILLS.md §2E — tool-scope enum.
ToolScope = Literal[
    "read-only",
    "read-only+transform",
    "shell-execute",
    "repo-write",
    "network",
    "cross-agent",
    "external-write",
    # Categorically rejected (still parsed so we can refuse explicitly):
    "git-write",
    "workflow-write",
]

CATEGORICALLY_REJECTED_SCOPES: frozenset[str] = frozenset({"git-write", "workflow-write"})

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class FrontmatterError(ValueError):
    """Raised when a SKILL.md frontmatter block is missing or malformed."""


class SkillFrontmatter(BaseModel):
    """Validated frontmatter for a vendored SKILL.md."""

    name: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    source_url: str = Field(alias="source-url")
    source_canonical: str = Field(alias="source-canonical")
    source_sha: str = Field(alias="source-sha")
    audited: str  # ISO date string; Phase 2 will tighten to date
    goal: int = Field(ge=1, le=5)
    tier: int = Field(ge=1, le=3)
    tool_scope: ToolScope = Field(alias="tool-scope")
    target_agents: list[str] = Field(alias="target-agents", default_factory=list)
    context_cost_tokens: int = Field(alias="context-cost-tokens", ge=0)
    owner: str

    model_config = {"populate_by_name": True}

    @field_validator("audited", mode="before")
    @classmethod
    def _audited_to_str(cls, v: Any) -> str:
        # YAML auto-parses ISO dates → coerce back to string for stable
        # schema across vendored SKILL.md files.
        if isinstance(v, date):
            return v.isoformat()
        return v

    @field_validator("source_sha")
    @classmethod
    def _sha_is_40_hex(cls, v: str) -> str:
        if not SHA_RE.match(v):
            raise ValueError("source-sha must be a 40-char lowercase hex string")
        return v

    @field_validator("slug")
    @classmethod
    def _slug_has_vendor_prefix(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("slug must be of the form '<vendor>/<name>'")
        return v


def parse_frontmatter(skill_md_text: str) -> tuple[SkillFrontmatter, str]:
    """Parse SKILL.md text → (validated frontmatter, body).

    Raises FrontmatterError if the frontmatter block is missing, malformed,
    or fails schema validation.
    """
    match = FRONTMATTER_RE.match(skill_md_text)
    if not match:
        raise FrontmatterError("SKILL.md missing YAML frontmatter block (--- ... ---)")

    try:
        raw = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter YAML parse error: {exc}") from exc

    if not isinstance(raw, dict):
        raise FrontmatterError("frontmatter must be a YAML mapping")

    try:
        fm = SkillFrontmatter.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError → wrap
        raise FrontmatterError(f"frontmatter schema invalid: {exc}") from exc

    body = skill_md_text[match.end() :]
    return fm, body


def is_categorically_rejected(scope: str) -> bool:
    """AGENT_SKILLS.md §2E — git-write and workflow-write are categorically rejected."""
    return scope in CATEGORICALLY_REJECTED_SCOPES
