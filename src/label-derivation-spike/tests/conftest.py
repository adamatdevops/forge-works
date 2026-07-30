from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from forge_works.dr.ab028_spike.evaluate import build_default_catalog
from forge_works.dr.ab028_spike.events import generate_stream
from forge_works.dr.label_schema_validator import CatalogEntry, EstimandCatalog

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.events import SyntheticEventStream


@pytest.fixture(scope="session")
def catalog() -> EstimandCatalog:
    return build_default_catalog()


@pytest.fixture(scope="session")
def small_stream() -> SyntheticEventStream:
    return generate_stream(modeling_days=20, metadata_days=10, seed=20260728, base_rate=0.08)


@pytest.fixture(scope="session")
def spike_stream() -> SyntheticEventStream:
    return generate_stream(modeling_days=60, metadata_days=30, seed=20260728, base_rate=0.08)


@pytest.fixture(scope="session")
def modeling_bounds(spike_stream: SyntheticEventStream) -> tuple:
    metadata_end = spike_stream.start + timedelta(days=30)
    return metadata_end, spike_stream.end


@pytest.fixture(scope="session")
def custom_catalog_missing_v0() -> EstimandCatalog:
    return EstimandCatalog(entries={})


@pytest.fixture(scope="session")
def catalog_with_v0() -> EstimandCatalog:
    return EstimandCatalog(
        entries={
            "deploy_slo_breach_60m_association_v0": CatalogEntry(
                estimand_id="deploy_slo_breach_60m_association_v0",
                outcome_vocabulary=("slo_breach_occurred", "slo_breach_absent"),
                version="v0",
                owner="dynamic-reliability",
            )
        },
    )
