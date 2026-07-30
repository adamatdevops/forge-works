from __future__ import annotations

import json

from forge_works.dr.ab028_spike.tracking import open_tracker


def test_local_tracker_round_trip(tmp_path) -> None:
    tracker = open_tracker(tmp_path)
    tracker.log_param("model", "gbt")
    tracker.log_metric("aucpr", 0.42)
    tracker.log_artifact("bins", [1, 2, 3])
    tracker.set_tag("run_kind", "test")
    out = tracker.finalize()
    payload = json.loads(out.read_text())
    assert payload["params"] == {"model": "gbt"}
    assert payload["metrics"] == {"aucpr": 0.42}
    assert payload["artifacts"] == {"bins": [1, 2, 3]}
    assert payload["tags"]["run_kind"] == "test"
