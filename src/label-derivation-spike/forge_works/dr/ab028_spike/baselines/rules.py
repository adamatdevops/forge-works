"""Rules baseline (RFC §5.1 v0.2) — 5-rule list with empirical-rate probability mapping (F7).

Rule constants (Rule 5's P90 threshold) are computed on the training cohort only, then frozen.
Match / no-match rows are mapped to the empirical positive rate observed on the training cohort
under that condition — so the baseline produces calibration-comparable probabilities, not
handicapped 0.9 / 0.1 pseudo-scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

APPLY_FAILED_6H_COL = "apply_failed_last_6h"
SLO_BURNING_1H_COL = "slo_burning_last_1h"
MONITOR_WARNING_COL = "monitor_state__warning"
MONITOR_ALERT_COL = "monitor_state__alert"
SENSITIVE_COL = "sensitive_resource_touched"
APPLY_FAILED_168H_COL = "apply_failed_last_168h"
PLAN_DIFF_COL = "plan_diff_size"


@dataclass
class RulesBaseline:
    p90_plan_diff: float = 0.0
    p_match: float = 0.5
    p_no_match: float = 0.5
    fitted: bool = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> RulesBaseline:
        self.p90_plan_diff = float(X[PLAN_DIFF_COL].quantile(0.90))
        self.fitted = True
        matches = self._match_vector(X)
        y_arr = y.to_numpy()
        n_match = int(matches.sum())
        n_no_match = int(len(matches) - n_match)
        pos_match = int(y_arr[matches].sum()) if n_match else 0
        pos_no_match = int(y_arr[~matches].sum()) if n_no_match else 0
        self.p_match = _empirical_rate(pos_match, n_match, fallback=float(y_arr.mean()))
        self.p_no_match = _empirical_rate(pos_no_match, n_no_match, fallback=float(y_arr.mean()))
        return self

    def _match_vector(self, X: pd.DataFrame) -> np.ndarray:
        if not self.fitted:
            msg = "RulesBaseline.fit() must be called before matching"
            raise RuntimeError(msg)
        rule_1 = X[APPLY_FAILED_6H_COL].to_numpy() >= 1
        rule_2 = X[SLO_BURNING_1H_COL].to_numpy() >= 1
        rule_3 = X[MONITOR_WARNING_COL].to_numpy().astype(bool) | X[
            MONITOR_ALERT_COL
        ].to_numpy().astype(bool)
        rule_4 = X[SENSITIVE_COL].to_numpy().astype(bool) & (
            X[APPLY_FAILED_168H_COL].to_numpy() >= 1
        )
        rule_5 = X[PLAN_DIFF_COL].to_numpy() > self.p90_plan_diff
        return rule_1 | rule_2 | rule_3 | rule_4 | rule_5

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        matches = self._match_vector(X)
        prob = np.where(matches, self.p_match, self.p_no_match)
        return np.column_stack([1.0 - prob, prob])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._match_vector(X).astype(np.int8)


def _empirical_rate(positives: int, total: int, *, fallback: float) -> float:
    if total == 0:
        return fallback
    return positives / total
