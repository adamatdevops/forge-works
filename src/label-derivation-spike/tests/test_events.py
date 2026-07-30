from __future__ import annotations

from forge_works.dr.ab028_spike.events import generate_stream, stream_summary


def test_stream_is_deterministic() -> None:
    a = generate_stream(modeling_days=30, metadata_days=15, seed=7)
    b = generate_stream(modeling_days=30, metadata_days=15, seed=7)
    assert [d.deploy_id for d in a.deploys] == [d.deploy_id for d in b.deploys]
    assert [b1.event_time for b1 in a.slo_breaches] == [b1.event_time for b1 in b.slo_breaches]


def test_different_seeds_diverge() -> None:
    a = generate_stream(modeling_days=15, metadata_days=5, seed=1)
    b = generate_stream(modeling_days=15, metadata_days=5, seed=2)
    assert (
        len(a.deploys) != len(b.deploys)
        or a.deploys[0].plan_diff_size != b.deploys[0].plan_diff_size
    )


def test_events_are_sorted() -> None:
    stream = generate_stream(modeling_days=20, metadata_days=10, seed=42)
    for lst in (stream.deploys, stream.slo_breaches, stream.apply_failures, stream.monitor_events):
        times = [e.event_time if hasattr(e, "event_time") else e.deployed_at for e in lst]
        assert times == sorted(times)


def test_summary_reports_counts() -> None:
    stream = generate_stream(modeling_days=30, metadata_days=15, seed=42)
    summary = stream_summary(stream)
    assert summary["days"] == 45
    assert summary["deploys"] > 0
    assert summary["monitor_events"] >= 1
