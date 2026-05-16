"""Entry point — `python -m forge_skills_mcp`.

Resolves the `.skills/` root by walking up from $CWD until a directory
containing `.skills/` is found (or `--skills-root` is passed). This matches
the dual-agent invocation pattern: Claude/Codex launch the server with
`--directory <repo>/tools/forge-skills-mcp`, and the repo root is the parent
of that directory (or further up if invoked from a different CWD).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import configure_logging
from .server import build_server


def _find_skills_root(start: Path) -> Path | None:
    """Walk upward from `start` looking for a `.skills/` directory."""
    current = start.resolve()
    while True:
        candidate = current / ".skills"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forge-skills-mcp",
        description="Dual-agent skill loader for forge-works (Claude + Codex CLI).",
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=None,
        help="Path to .skills/ directory (default: walk up from CWD)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug-level audit logging"
    )
    args = parser.parse_args(argv)

    configure_logging(verbose=args.verbose)

    skills_root = args.skills_root or _find_skills_root(Path.cwd())
    if skills_root is None:
        print(
            "forge-skills-mcp: could not locate .skills/ directory; pass --skills-root.",
            file=sys.stderr,
        )
        return 2

    server = build_server(skills_root=skills_root)
    # FastMCP.run() handles stdio transport setup.
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
