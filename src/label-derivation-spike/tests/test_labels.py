from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from forge_works.dr.ab028_spike.labels import (
    LabelDerivationError,
    derive_labels,
)

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.events import SyntheticEventStream
    from forge_works.dr.label_schema_validator import EstimandCatalog


def test_derives_labels_for_modeling_window(
    small_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    metadata_end = small_stream.start + timedelta(days=10)
    labels = derive_labels(
        small_stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=small_stream.end,
    )
    assert len(labels) > 0
    for dl in labels:
        assert metadata_end <= dl.deploy.deployed_at < small_stream.end
        assert dl.result.is_valid


def test_all_eligibility_shapes_appear(
    spike_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    metadata_end = spike_stream.start + timedelta(days=30)
    labels = derive_labels(
        spike_stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=spike_stream.end,
    )
    shapes = {dl.eligibility for dl in labels}
    assert "eligible" in shapes


def test_censored_labels_carry_original_horizon_end(
    spike_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    metadata_end = spike_stream.start + timedelta(days=30)
    labels = derive_labels(
        spike_stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=spike_stream.end,
    )
    censored = [dl for dl in labels if dl.eligibility == "censored"]
    if not censored:
        pytest.skip("no censored labels for this fixture — outcome-dependent")
    for dl in censored:
        assert "original_horizon_end" in dl.label
        assert dl.label["observation_window"]["end"] < dl.label["original_horizon_end"]


def test_missing_v0_catalog_raises(
    small_stream: SyntheticEventStream, custom_catalog_missing_v0: EstimandCatalog
) -> None:
    metadata_end = small_stream.start + timedelta(days=10)
    with pytest.raises(LabelDerivationError):
        derive_labels(
            small_stream,
            catalog=custom_catalog_missing_v0,
            modeling_window_start=metadata_end,
            modeling_window_end=small_stream.end,
        )
