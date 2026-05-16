"""Filesystem scanner for `.skills/<vendor>/<slug>/SKILL.md` files.

See ACTION_PLAN_SKILL_LOADERS.md §3.1 for the layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .frontmatter import FrontmatterError, SkillFrontmatter, parse_frontmatter


@dataclass(frozen=True)
class LoadedSkill:
    """A SKILL.md successfully discovered and parsed from .skills/."""

    path: Path
    frontmatter: SkillFrontmatter
    body: str


@dataclass(frozen=True)
class ScanError:
    """A SKILL.md discovered but rejected during parsing."""

    path: Path
    reason: str


@dataclass(frozen=True)
class ScanResult:
    skills: list[LoadedSkill]
    errors: list[ScanError]


def scan(skills_root: Path) -> ScanResult:
    """Walk `.skills/<vendor>/<slug>/SKILL.md`, return loaded skills + errors.

    Files outside the `<vendor>/<slug>/SKILL.md` pattern are ignored silently.
    Files matching the pattern but failing frontmatter validation land in
    `errors` (not `skills`) so the loader can surface them in `loader_health`.
    """
    skills: list[LoadedSkill] = []
    errors: list[ScanError] = []

    if not skills_root.is_dir():
        return ScanResult(skills=skills, errors=errors)

    for skill_md in sorted(skills_root.glob("*/*/SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(ScanError(path=skill_md, reason=f"read error: {exc}"))
            continue

        try:
            fm, body = parse_frontmatter(text)
        except FrontmatterError as exc:
            errors.append(ScanError(path=skill_md, reason=str(exc)))
            continue

        # Sanity: vendor/slug from filesystem path must match frontmatter declaration.
        expected_vendor = skill_md.parent.parent.name
        expected_slug_name = skill_md.parent.name
        expected_slug = f"{expected_vendor}/{expected_slug_name}"
        if fm.vendor != expected_vendor or fm.slug != expected_slug:
            errors.append(
                ScanError(
                    path=skill_md,
                    reason=(
                        f"path/frontmatter mismatch: path implies {expected_slug!r} "
                        f"but frontmatter has vendor={fm.vendor!r} slug={fm.slug!r}"
                    ),
                )
            )
            continue

        skills.append(LoadedSkill(path=skill_md, frontmatter=fm, body=body))

    return ScanResult(skills=skills, errors=errors)
