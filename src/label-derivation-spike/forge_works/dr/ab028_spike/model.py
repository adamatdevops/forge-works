"""GBT model (RFC §5.3 v0.2).

sklearn's `HistGradientBoostingClassifier` — no external dep on xgboost/lightgbm, standard-of-care
for tabular scale of ~1000 rows. class_weight=balanced via sample_weight; isotonic calibration
wrapper (F8) fits on a disjoint held-out fold within training; TimeSeriesSplit CV over the
small grid (F13).
"""

from __future__ import annotations

from itertools import product

from forge_works.dr.ab028_spike.calibration import CalibratedTemporalClassifier
from sklearn.ensemble import HistGradientBoostingClassifier

_MAX_DEPTHS = (3, 5, 7)
_LEARNING_RATES = (0.05, 0.1)
_MAX_ITER = (100, 300)

GBT_GRID = [
    {"max_depth": depth, "learning_rate": lr, "max_iter": mi}
    for depth, lr, mi in product(_MAX_DEPTHS, _LEARNING_RATES, _MAX_ITER)
]


def build_gbt_model() -> CalibratedTemporalClassifier:
    def factory() -> HistGradientBoostingClassifier:
        return HistGradientBoostingClassifier(
            max_depth=5,
            learning_rate=0.1,
            max_iter=100,
            class_weight="balanced",
            l2_regularization=0.0,
            random_state=20260728,
        )

    return CalibratedTemporalClassifier(estimator_factory=factory, param_grid=GBT_GRID)
