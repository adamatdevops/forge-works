"""CLI entrypoint for the AB-028 metadata-window pass.

Runs against the synthetic loader by default (safe for CI + local dev). Real Terraform +
DataDog adapters swap into `--loader` when they exist. Emits both JSON (for archival /
provenance) and markdown (for meeting pre-read).

Usage:
    python -m forge_works.dr.ab028_spike.cli --out-dir ./out
    python -m forge_works.dr.ab028_spike.cli --metadata-days 30 --modeling-days 60 --seed 42
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forge_works.dr.ab028_spike.adapters import SyntheticEventLoader
from forge_works.dr.ab028_spike.metadata_window import (
    MetadataPassConfig,
    default_anchor,
    run_metadata_pass_via_loader,
)
from forge_works.dr.ab028_spike.report import to_json, to_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ab028-metadata-pass",
        description="AB-028 pre-scoping metadata-window pass (RFC §A3 + §4.4).",
    )
    p.add_argument("--metadata-days", type=int, default=30)
    p.add_argument("--modeling-days", type=int, default=60)
    p.add_argument("--seed", type=int, default=20260728)
    p.add_argument("--base-rate", type=float, default=0.08)
    p.add_argument("--deploys-per-day", type=float, default=8.0)
    p.add_argument("--train-floor", type=int, default=50)
    p.add_argument("--val-floor", type=int, default=15)
    p.add_argument("--test-floor", type=int, default=30)
    p.add_argument("--base-rate-lower", type=float, default=0.01)
    p.add_argument("--base-rate-upper", type=float, default=0.20)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write metadata-pass.json + metadata-pass.md to this directory (default: stdout only).",
    )
    p.add_argument(
        "--json-only",
        action="store_true",
        help="Emit only JSON to stdout (no markdown). Useful for machine consumption.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    loader = SyntheticEventLoader(
        seed=args.seed,
        base_rate=args.base_rate,
        deploys_per_day=args.deploys_per_day,
        modeling_days=args.modeling_days,
        metadata_days=args.metadata_days,
    )
    config = MetadataPassConfig(
        metadata_days=args.metadata_days,
        modeling_days=args.modeling_days,
        train_positive_floor=args.train_floor,
        val_positive_floor=args.val_floor,
        test_positive_floor=args.test_floor,
        base_rate_lower=args.base_rate_lower,
        base_rate_upper=args.base_rate_upper,
    )
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=config)

    json_out = to_json(result, config)
    md_out = to_markdown(result, config)

    if args.out_dir is not None:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "metadata-pass.json").write_text(json_out)
        (args.out_dir / "metadata-pass.md").write_text(md_out)
        sys.stdout.write(f"wrote {args.out_dir / 'metadata-pass.json'}\n")
        sys.stdout.write(f"wrote {args.out_dir / 'metadata-pass.md'}\n")
    elif args.json_only:
        sys.stdout.write(json_out + "\n")
    else:
        sys.stdout.write(md_out)
        sys.stdout.write("\n---\n\n")
        sys.stdout.write(json_out + "\n")

    return 0 if result.ready_for_scoping_approval else 1


if __name__ == "__main__":
    raise SystemExit(main())
