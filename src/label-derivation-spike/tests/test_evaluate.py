from __future__ import annotations

import pytest
from forge_works.dr.ab028_spike.evaluate import run_spike
from forge_works.dr.ab028_spike.metrics import GateConfig


@pytest.mark.slow
def test_end_to_end_smoke() -> None:
    verdict = run_spike(
        modeling_days=90,
        metadata_days=30,
        seed=20260728,
        base_rate=0.20,
        deploys_per_day=6.0,
        gate=GateConfig(bootstrap_resamples=50),
    )
    assert verdict.outcome in ("go", "no-go")
    assert verdict.metadata_window.days == 30
    assert verdict.metadata_window.deploys > 0
    assert verdict.split_report.floors_pass
    assert isinstance(verdict.reasons, list)
    assert verdict.reasons
    assert "aucpr" in verdict.gbt
    assert "aucpr" in verdict.lr
    assert "aucpr" in verdict.rules


def test_inconclusive_when_positive_floors_fail() -> None:
    verdict = run_spike(
        modeling_days=15,
        metadata_days=10,
        seed=20260728,
        base_rate=0.02,
        gate=GateConfig(bootstrap_resamples=20),
    )
    assert verdict.outcome == "inconclusive"
    assert verdict.metadata_window.deploys > 0
    assert not verdict.split_report.floors_pass
    assert any("floor" in reason for reason in verdict.reasons)
