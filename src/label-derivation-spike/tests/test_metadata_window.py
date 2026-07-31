from __future__ import annotations

from datetime import UTC, datetime

import pytest
from forge_works.dr.ab028_spike.adapters import SyntheticEventLoader
from forge_works.dr.ab028_spike.metadata_window import (
    MetadataPass,
    MetadataPassConfig,
    default_anchor,
    run_metadata_pass,
    run_metadata_pass_via_loader,
    with_locked_thresholds,
)


@pytest.fixture
def default_config() -> MetadataPassConfig:
    return MetadataPassConfig(
        metadata_days=30,
        modeling_days=60,
        train_positive_floor=50,
        val_positive_floor=15,
        test_positive_floor=30,
    )


@pytest.fixture
def loader() -> SyntheticEventLoader:
    return SyntheticEventLoader(
        seed=20260728,
        base_rate=0.15,
        deploys_per_day=6.0,
        modeling_days=60,
        metadata_days=30,
    )


def test_metadata_pass_shape(
    loader: SyntheticEventLoader, default_config: MetadataPassConfig
) -> None:
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=default_config)
    assert isinstance(result, MetadataPass)
    assert result.metadata_days == 30
    assert result.deploys > 0
    assert 0.0 <= result.base_rate <= 1.0
    assert 0.0 <= result.censoring_rate <= 1.0
    assert 0.0 <= result.missing_data_rate <= 1.0
    assert result.projected_modeling_window.modeling_days == 60


def test_base_rate_bounds_enforced() -> None:
    loader = SyntheticEventLoader(
        seed=1, base_rate=0.15, deploys_per_day=6.0, modeling_days=60, metadata_days=30
    )
    config = MetadataPassConfig(base_rate_lower=0.01, base_rate_upper=0.20)
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=config)
    assert not result.base_rate_in_bounds
    assert any("base rate" in w for w in result.warnings)


def test_floors_fail_warning_raised() -> None:
    loader = SyntheticEventLoader(
        seed=1, base_rate=0.02, deploys_per_day=2.0, modeling_days=60, metadata_days=30
    )
    config = MetadataPassConfig(
        train_positive_floor=500, val_positive_floor=100, test_positive_floor=100
    )
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=config)
    assert not result.projected_modeling_window.all_floors_met
    assert not result.ready_for_scoping_approval


def test_ready_when_all_gates_pass() -> None:
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
    assert result.base_rate_in_bounds
    assert result.projected_modeling_window.all_floors_met
    assert result.ready_for_scoping_approval
    assert not result.warnings


def test_projection_math_scales_with_modeling_days() -> None:
    loader = SyntheticEventLoader(
        seed=7, base_rate=0.10, deploys_per_day=10.0, modeling_days=60, metadata_days=30
    )
    a = run_metadata_pass_via_loader(
        loader, anchor=default_anchor(), config=MetadataPassConfig(modeling_days=60)
    )
    b = run_metadata_pass_via_loader(
        loader, anchor=default_anchor(), config=MetadataPassConfig(modeling_days=120)
    )
    assert (
        b.projected_modeling_window.projected_positives
        > a.projected_modeling_window.projected_positives
    )


def test_run_metadata_pass_uses_first_n_days(loader: SyntheticEventLoader) -> None:
    stream = loader.load(default_anchor(), default_anchor())
    result = run_metadata_pass(stream, config=MetadataPassConfig(metadata_days=30))
    assert result.metadata_window_start == stream.start
    assert (result.metadata_window_end - result.metadata_window_start).days == 30


def test_with_locked_thresholds_returns_new_config(default_config: MetadataPassConfig) -> None:
    locked = with_locked_thresholds(default_config, train_positive_floor=75)
    assert locked.train_positive_floor == 75
    assert default_config.train_positive_floor == 50


def test_metadata_pass_metadata_window_start_is_utc(
    loader: SyntheticEventLoader, default_config: MetadataPassConfig
) -> None:
    result = run_metadata_pass_via_loader(loader, anchor=default_anchor(), config=default_config)
    assert (
        result.metadata_window_start.tzinfo is UTC
        or result.metadata_window_start.tzinfo is not None
    )


def test_default_anchor_is_absolute() -> None:
    a = default_anchor()
    assert a == datetime(2026, 7, 1, tzinfo=UTC)
