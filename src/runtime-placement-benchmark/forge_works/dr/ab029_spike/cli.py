"""CLI entrypoint for the AB-029 placement benchmark framework.

Runs the stub prototypes with placeholder scores by default (all-neutral 3s across the
board). Real scoring lands via a scores JSON file the scoping-approval meeting produces.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forge_works.dr.ab029_spike.matrix import to_json, to_markdown
from forge_works.dr.ab029_spike.runner import (
    BenchmarkRunner,
    OptionInput,
    scoping_approval_placeholder_inputs,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ab029-benchmark",
        description="AB-029 runtime placement benchmark framework (RFC §4-§7).",
    )
    p.add_argument(
        "--scores",
        type=Path,
        default=None,
        help="Path to a JSON file mapping option_code -> {dimension_code: score}. "
        "Defaults to all-3s across the board.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write matrix.json + matrix.md to this directory (default: stdout only).",
    )
    p.add_argument(
        "--json-only",
        action="store_true",
        help="Emit only JSON to stdout (no markdown).",
    )
    return p


def load_inputs(scores_path: Path | None) -> list[OptionInput]:
    if scores_path is None:
        return scoping_approval_placeholder_inputs()
    data = json.loads(scores_path.read_text())
    inputs = []
    for code, payload in data.items():
        scores = payload.get("scores", payload) if isinstance(payload, dict) else payload
        contract_flags = (
            payload.get("contract_breaking_flags", []) if isinstance(payload, dict) else []
        )
        rationale = payload.get("rationale", {}) if isinstance(payload, dict) else {}
        inputs.append(
            OptionInput(
                option_code=code,
                scores={str(k): int(v) for k, v in scores.items()},
                contract_breaking_flags=list(contract_flags),
                rationale_per_dimension={str(k): str(v) for k, v in rationale.items()},
            )
        )
    return inputs


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inputs = load_inputs(args.scores)
    runner = BenchmarkRunner()
    matrix, decision = runner.run(inputs)

    json_out = to_json(matrix, decision)
    md_out = to_markdown(matrix, decision)

    if args.out_dir is not None:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "matrix.json").write_text(json_out)
        (args.out_dir / "matrix.md").write_text(md_out)
        sys.stdout.write(f"wrote {args.out_dir / 'matrix.json'}\n")
        sys.stdout.write(f"wrote {args.out_dir / 'matrix.md'}\n")
    elif args.json_only:
        sys.stdout.write(json_out + "\n")
    else:
        sys.stdout.write(md_out)
        sys.stdout.write("\n---\n\n")
        sys.stdout.write(json_out + "\n")

    return 0 if decision.has_primary else 1


if __name__ == "__main__":
    raise SystemExit(main())
