from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from forge_works.dr.ab028_spike.events import SyntheticEventStream
from forge_works.dr.ab028_spike.features import (
    MONITOR_STATES,
    ROLLING_WINDOWS_HOURS,
    assert_no_lookahead_for,
    build_feature_matrix,
)
from forge_works.dr.ab028_spike.labels import derive_labels

if TYPE_CHECKING:
    from forge_works.dr.label_schema_validator import EstimandCatalog


def test_feature_matrix_shape(spike_stream: SyntheticEventStream, catalog: EstimandCatalog) -> None:
    metadata_end = spike_stream.start + timedelta(days=30)
    labels = derive_labels(
        spike_stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=spike_stream.end,
    )
    fm = build_feature_matrix(spike_stream, labels)
    eligible_labels = [dl for dl in labels if dl.eligibility == "eligible"]
    assert fm.n_rows == len(eligible_labels)
    for hours in ROLLING_WINDOWS_HOURS:
        assert f"apply_failed_last_{hours}h" in fm.X.columns
    for state in MONITOR_STATES:
        assert f"monitor_state__{state}" in fm.X.columns


def test_no_lookahead(spike_stream: SyntheticEventStream, catalog: EstimandCatalog) -> None:
    metadata_end = spike_stream.start + timedelta(days=30)
    labels = derive_labels(
        spike_stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=spike_stream.end,
    )
    fm = build_feature_matrix(spike_stream, labels)
    if not fm.deploy_times:
        return
    t0 = fm.deploy_times[0]
    filtered_stream = SyntheticEventStream(
        start=spike_stream.start,
        end=t0,
        deploys=[d for d in spike_stream.deploys if d.deployed_at < t0],
        slo_breaches=[b for b in spike_stream.slo_breaches if b.event_time < t0],
        apply_failures=[a for a in spike_stream.apply_failures if a.event_time < t0],
        monitor_events=[m for m in spike_stream.monitor_events if m.event_time < t0],
        incidents=[i for i in spike_stream.incidents if i.event_time < t0],
    )
    assert_no_lookahead_for(filtered_stream, t0)
