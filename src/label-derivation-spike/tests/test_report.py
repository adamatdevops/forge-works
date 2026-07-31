from __future__ import annotations

import json

from forge_works.dr.ab028_spike.adapters import SyntheticEventLoader
from forge_works.dr.ab028_spike.metadata_window import (
    MetadataPassConfig,
    default_anchor,
    run_metadata_pass_via_loader,
)
from forge_works.dr.ab028_spike.report import to_json, to_markdown


def _sample_pass():
    loader = SyntheticEventLoader(
        seed=42,
        base_rate=0.03,
        deploys_per_day=5.0,
        modeling_days=60,
        metadata_days=30,
    )
    config = MetadataPassConfig(
        train_positive_floor=10, val_positive_floor=3, test_positive_floor=3
    )
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=config)
    return result, config


def test_json_report_roundtrips() -> None:
    result, config = _sample_pass()
    payload = json.loads(to_json(result, config))
    assert "metadata_pass" in payload
    assert "config" in payload
    assert payload["metadata_pass"]["deploys"] == result.deploys


def test_markdown_report_includes_headings() -> None:
    result, config = _sample_pass()
    md = to_markdown(result, config)
    assert "# AB-028 Pre-Scoping Metadata Window Pass" in md
    assert "## Volume + rates" in md
    assert "## Base-rate check (§4.4)" in md
    assert "## Prospective power projection" in md
    assert "## Warnings" in md
    assert "## Scoping-approval readiness" in md


def test_markdown_report_flags_ready_or_not() -> None:
    result, config = _sample_pass()
    md = to_markdown(result, config)
    if result.ready_for_scoping_approval:
        assert "**READY**" in md
    else:
        assert "**NOT READY**" in md
