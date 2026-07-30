from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from forge_works.dr.ab028_spike.baselines.rules import RulesBaseline
from forge_works.dr.ab028_spike.features import build_feature_matrix
from forge_works.dr.ab028_spike.labels import derive_labels

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.events import SyntheticEventStream
    from forge_works.dr.label_schema_validator import EstimandCatalog


def _fitted(stream: SyntheticEventStream, catalog: EstimandCatalog) -> tuple:
    metadata_end = stream.start + timedelta(days=30)
    labels = derive_labels(
        stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=stream.end,
    )
    fm = build_feature_matrix(stream, labels)
    rules = RulesBaseline().fit(fm.X, fm.y)
    return rules, fm


def test_rules_fits_and_predicts(
    spike_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    rules, fm = _fitted(spike_stream, catalog)
    assert rules.fitted
    assert 0 <= rules.p_match <= 1
    assert 0 <= rules.p_no_match <= 1
    proba = rules.predict_proba(fm.X)
    assert proba.shape == (fm.n_rows, 2)
    assert (proba.sum(axis=1) > 0.999).all()


def test_match_rate_high_when_match_col_high(
    spike_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    """P(positive | any rule matches) >= P(positive | no rule matches) — signal must actually help."""
    rules, _ = _fitted(spike_stream, catalog)
    assert rules.p_match >= rules.p_no_match
