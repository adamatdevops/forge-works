"""Shared training + isotonic-calibration wrapper (RFC §5.2 + §5.3 F8).

Both LR (baseline 2) and GBT (model) go through the same wrapper so the ECE comparison
in §6 is apples-to-apples. Calibration fits on a disjoint held-out fold *within* the
training cohort — never on validation/test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import TimeSeriesSplit

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd


CALIBRATION_FOLD_FRACTION = 0.15


@dataclass
class CalibratedTemporalClassifier:
    """Estimator + isotonic-calibration wrapper with time-respecting CV.

    - Splits training into (main, calibration) chronologically.
    - Fits estimator on the main portion.
    - Fits isotonic on estimator predictions over the calibration portion.
    - `predict_proba(X)` returns (n, 2) probabilities calibrated end-to-end.
    """

    estimator_factory: Callable[[], Any]
    param_grid: list[dict[str, Any]] = field(default_factory=list)
    n_cv_splits: int = 3
    cv_gap: int = 10
    calibration_fold_fraction: float = CALIBRATION_FOLD_FRACTION
    estimator: Any = None
    isotonic: IsotonicRegression | None = None
    best_params: dict[str, Any] = field(default_factory=dict)
    calibration_cutoff_idx: int = -1

    def fit(self, X: pd.DataFrame, y: pd.Series) -> CalibratedTemporalClassifier:
        n = len(X)
        if n < 20:
            msg = f"training cohort too small for calibration wrapper (got {n} rows)"
            raise ValueError(msg)
        cal_n = max(1, round(n * self.calibration_fold_fraction))
        main_end = n - cal_n
        X_main, y_main = X.iloc[:main_end], y.iloc[:main_end]
        X_cal, y_cal = X.iloc[main_end:], y.iloc[main_end:]

        best_score = -np.inf
        best_params: dict[str, Any] = {}
        for params in self.param_grid or [{}]:
            score = self._cv_score(X_main, y_main, params)
            if score > best_score:
                best_score = score
                best_params = params

        self.best_params = best_params
        self.estimator = self.estimator_factory()
        self.estimator.set_params(**best_params)
        self.estimator.fit(X_main, y_main)

        cal_scores = self._raw_scores(X_cal)
        self.isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self.isotonic.fit(cal_scores, y_cal.to_numpy())
        self.calibration_cutoff_idx = main_end
        return self

    def _cv_score(self, X: pd.DataFrame, y: pd.Series, params: dict[str, Any]) -> float:
        splits = min(self.n_cv_splits, max(2, len(X) // 40))
        cv = TimeSeriesSplit(n_splits=splits, gap=self.cv_gap)
        scores: list[float] = []
        for tr_idx, va_idx in cv.split(X):
            est = self.estimator_factory()
            est.set_params(**params)
            est.fit(X.iloc[tr_idx], y.iloc[tr_idx])
            proba = _raw_positive_scores(est, X.iloc[va_idx])
            score = _average_precision(y.iloc[va_idx].to_numpy(), proba)
            scores.append(score)
        return float(np.mean(scores)) if scores else 0.0

    def _raw_scores(self, X: pd.DataFrame) -> np.ndarray:
        if self.estimator is None:
            msg = "estimator not fit yet"
            raise RuntimeError(msg)
        return _raw_positive_scores(self.estimator, X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raw = self._raw_scores(X)
        if self.isotonic is None:
            msg = "isotonic calibrator not fit yet"
            raise RuntimeError(msg)
        calibrated = self.isotonic.transform(raw)
        return np.column_stack([1.0 - calibrated, calibrated])


def _raw_positive_scores(estimator: Any, X: pd.DataFrame) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(X)[:, 1]
    if hasattr(estimator, "decision_function"):
        raw = estimator.decision_function(X)
        return 1.0 / (1.0 + np.exp(-raw))
    msg = (
        f"estimator {type(estimator).__name__} exposes neither predict_proba nor decision_function"
    )
    raise TypeError(msg)


def _average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return 0.0
    return float(average_precision_score(y_true, y_score))
