from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from forge_works.dr.ab028_spike.baselines.lr import build_lr_baseline
from forge_works.dr.ab028_spike.features import build_feature_matrix
from forge_works.dr.ab028_spike.labels import derive_labels
from forge_works.dr.ab028_spike.model import build_gbt_model

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.events import SyntheticEventStream
    from forge_works.dr.label_schema_validator import EstimandCatalog


def _matrix(stream: SyntheticEventStream, catalog: EstimandCatalog):
    metadata_end = stream.start + timedelta(days=30)
    labels = derive_labels(
        stream,
        catalog=catalog,
        modeling_window_start=metadata_end,
        modeling_window_end=stream.end,
    )
    return build_feature_matrix(stream, labels)


def test_lr_fits_and_predicts(spike_stream: SyntheticEventStream, catalog: EstimandCatalog) -> None:
    fm = _matrix(spike_stream, catalog)
    train_end = int(fm.n_rows * 0.7)
    X_train = fm.X.iloc[:train_end].reset_index(drop=True)
    y_train = fm.y.iloc[:train_end].reset_index(drop=True)
    lr = build_lr_baseline().fit(X_train, y_train)
    assert lr.best_params
    proba = lr.predict_proba(fm.X.iloc[train_end:].reset_index(drop=True))
    assert proba.shape[1] == 2
    assert ((proba >= 0.0) & (proba <= 1.0)).all()


def test_gbt_fits_and_predicts(
    spike_stream: SyntheticEventStream, catalog: EstimandCatalog
) -> None:
    fm = _matrix(spike_stream, catalog)
    train_end = int(fm.n_rows * 0.7)
    X_train = fm.X.iloc[:train_end].reset_index(drop=True)
    y_train = fm.y.iloc[:train_end].reset_index(drop=True)
    gbt = build_gbt_model().fit(X_train, y_train)
    proba = gbt.predict_proba(fm.X.iloc[train_end:].reset_index(drop=True))
    assert proba.shape[1] == 2
    assert ((proba >= 0.0) & (proba <= 1.0)).all()
