from __future__ import annotations

import pytest
from forge_works.dr.ab029_spike.rubric import (
    DisqualificationResult,
    WeightedScoreRubric,
    check_disqualification,
    weighted_score,
    within_fallback_range,
)


def test_default_rubric_uses_default_weights() -> None:
    r = WeightedScoreRubric()
    assert r.weights["D1"] == 3
    assert r.weights["D3"] == 4


def test_rubric_rejects_missing_weight() -> None:
    with pytest.raises(ValueError, match="missing"):
        WeightedScoreRubric(weights={"D1": 3, "D2": 2})


def test_rubric_rejects_unknown_weight() -> None:
    weights = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"), 3)
    with pytest.raises(ValueError, match="unknown dimension"):
        WeightedScoreRubric(weights=weights)


def test_weighted_score_matches_expected_math() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 5)
    r = WeightedScoreRubric()
    expected = 5 * sum(r.weights.values())
    assert weighted_score(scores, r) == expected


def test_weighted_score_rejects_out_of_range() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 3)
    scores["D3"] = 10
    with pytest.raises(ValueError, match="outside"):
        weighted_score(scores)


def test_weighted_score_rejects_missing_scores() -> None:
    scores = {"D1": 3}
    with pytest.raises(ValueError, match="missing"):
        weighted_score(scores)


def test_disqualification_fires_on_min_score_high_weight() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 3)
    scores["D3"] = 1
    dq = check_disqualification("A", scores)
    assert dq.disqualified
    assert any("D3" in r for r in dq.reasons)


def test_disqualification_ignores_min_score_low_weight() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 3)
    scores["D2"] = 1
    dq = check_disqualification("A", scores)
    assert not dq.disqualified


def test_disqualification_fires_on_contract_breaking_flag() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 3)
    dq = check_disqualification("D", scores, contract_breaking_flags=["PC §3 estimand semantics"])
    assert dq.disqualified
    assert any("contract-breaking" in r for r in dq.reasons)


def test_disqualification_result_is_falsy_when_ok() -> None:
    scores = dict.fromkeys(("D1", "D2", "D3", "D4", "D5", "D6", "D7"), 3)
    dq = check_disqualification("A", scores)
    assert not dq
    assert isinstance(dq, DisqualificationResult)


def test_within_fallback_range() -> None:
    assert within_fallback_range(100, 95)
    assert within_fallback_range(100, 90)
    assert not within_fallback_range(100, 89)
    assert not within_fallback_range(0, 0)
