from __future__ import annotations

import json

from forge_works.dr.ab029_spike.dimensions import DIMENSIONS, Measurement, MeasurementStatus
from forge_works.dr.ab029_spike.matrix import (
    build_matrix,
    build_option_result,
    build_placement_decision,
    to_json,
    to_markdown,
)


def _stub_measurements(code: str) -> dict[str, Measurement]:
    return {
        d.code: Measurement(dimension_code=d.code, status=MeasurementStatus.NOT_IMPLEMENTED)
        for d in DIMENSIONS
    }


def _make_option(code: str, name: str, scores: dict[str, int], **kw):
    return build_option_result(
        option_code=code,
        option_name=name,
        measurements=_stub_measurements(code),
        scores=scores,
        **kw,
    )


def test_build_matrix_ranks_qualified_options() -> None:
    opts = [
        _make_option("A", "A", {d.code: 3 for d in DIMENSIONS}),
        _make_option("B", "B", {d.code: 4 for d in DIMENSIONS}),
        _make_option("C", "C", {d.code: 5 for d in DIMENSIONS}),
    ]
    m = build_matrix(opts)
    ranked = m.ranked()
    assert [o.option_code for o in ranked] == ["C", "B", "A"]


def test_placement_decision_picks_primary_and_fallback() -> None:
    c_scores = {d.code: 5 for d in DIMENSIONS}
    b_scores = {d.code: 5 for d in DIMENSIONS}
    b_scores["D2"] = 4
    opts = [
        _make_option("A", "A", {d.code: 3 for d in DIMENSIONS}),
        _make_option("B", "B", b_scores),
        _make_option("C", "C", c_scores),
    ]
    d = build_placement_decision(build_matrix(opts))
    assert d.primary.option_code == "C"
    assert d.fallback is not None
    assert d.fallback.option_code == "B"


def test_placement_decision_no_fallback_when_gap_too_large() -> None:
    opts = [
        _make_option("A", "A", {d.code: 5 for d in DIMENSIONS}),
        _make_option("B", "B", {d.code: 1 for d in DIMENSIONS}),
        _make_option("C", "C", {d.code: 1 for d in DIMENSIONS}),
    ]
    d = build_placement_decision(build_matrix(opts))
    assert d.primary.option_code == "A"
    if d.fallback is not None:
        assert (
            d.fallback.weighted_score >= d.primary.weighted_score - d.primary.weighted_score // 10
        )


def test_all_disqualified_yields_no_primary() -> None:
    def worst_scores() -> dict[str, int]:
        return {d.code: 1 for d in DIMENSIONS}

    opts = [_make_option(c, c, worst_scores()) for c in ("A", "B", "C")]
    d = build_placement_decision(build_matrix(opts))
    assert d.all_options_disqualified
    assert d.primary is None
    assert d.fallback is None
    # Post-v0.2 escalation semantic: Option F is the 6th (added in v0.2 as the
    # resolution of v0.1 §8 R5's original "spike a 6th"), so all-disqualified now
    # escalates to a 7th option, not repeat of Option F.
    assert any("7th option" in n for n in d.notes)


def test_json_roundtrips() -> None:
    opts = [_make_option("A", "A", {d.code: 3 for d in DIMENSIONS})]
    m = build_matrix(opts)
    d = build_placement_decision(m)
    payload = json.loads(to_json(m, d))
    assert "options" in payload
    assert "rubric" in payload
    assert payload["decision"]["primary"] == "A"


def test_markdown_report_has_all_sections() -> None:
    opts = [_make_option("A", "A", {d.code: 3 for d in DIMENSIONS})]
    m = build_matrix(opts)
    d = build_placement_decision(m)
    md = to_markdown(m, d)
    assert "# AB-029 Runtime Placement Comparison Matrix" in md
    assert "## Weights (RFC §6.2)" in md
    assert "## Measurements" in md
    assert "## Scores + weighted totals" in md
    assert "## Disqualification (RFC §6.3)" in md
    assert "## Recommendation (RFC §6.2)" in md


def test_disqualified_option_removed_from_ranking() -> None:
    good = _make_option("A", "A", {d.code: 5 for d in DIMENSIONS})
    bad_scores = {d.code: 5 for d in DIMENSIONS}
    bad_scores["D3"] = 1
    bad = _make_option("B", "B", bad_scores)
    m = build_matrix([good, bad])
    ranked = m.ranked()
    assert [o.option_code for o in ranked] == ["A"]
    assert bad.disqualification.disqualified
