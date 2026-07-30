"""Logistic regression baseline (RFC §5.2 v0.2).

L2-regularized LR with StandardScaler, class_weight=balanced, isotonic calibration
wrapper (F8), and TimeSeriesSplit CV over C (F13).
"""

from __future__ import annotations

from forge_works.dr.ab028_spike.calibration import CalibratedTemporalClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

C_GRID = [{"lr__C": c} for c in (0.01, 0.1, 1.0, 10.0)]


def build_lr_baseline() -> CalibratedTemporalClassifier:
    def factory() -> Pipeline:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler(with_mean=True, with_std=True)),
                (
                    "lr",
                    LogisticRegression(
                        penalty="l2",
                        solver="lbfgs",
                        max_iter=1000,
                        class_weight="balanced",
                        C=1.0,
                    ),
                ),
            ]
        )

    return CalibratedTemporalClassifier(estimator_factory=factory, param_grid=C_GRID)
