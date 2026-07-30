from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
from forge_works.dr.ab028_spike.metrics import (
    GateConfig,
    bootstrap_ci_of_difference,
    choose_threshold_by_expected_loss,
    compute_c1_expected_loss,
    constant_predictor_brier,
    evaluate_predictions,
    operating_point_report,
)


def _perfect_scores(y: np.ndarray) -> np.ndarray:
    return y.astype(float)


def test_evaluate_perfect_predictor() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, size=200)
    report = evaluate_predictions(y, _perfect_scores(y))
    assert report.aucpr == 1.0
    assert report.brier == 0.0
    assert report.ece < 0.01


def test_ece_reflects_miscalibration() -> None:
    y = np.zeros(200, dtype=int)
    y[:20] = 1
    y_score = np.full(200, 0.5)
    report = evaluate_predictions(y, y_score)
    assert report.ece > 0.35


def test_constant_predictor_brier_formula() -> None:
    assert abs(constant_predictor_brier(0.1) - 0.09) < 1e-9


def test_c1_loss_asymmetric() -> None:
    weights = {"critical": 3.0, "major": 2.0, "warning": 1.0, "none": 1.0}
    y = np.array([1, 1, 0, 0])
    y_pred = np.array([0, 0, 1, 1])
    sev = ["critical", "major", "none", "none"]
    loss = compute_c1_expected_loss(
        y, y_pred, severities=sev, weights=weights, fn_over_fp_cost_ratio=10.0
    )
    assert loss == 10.0 * (3.0 + 2.0) + 2.0


def test_choose_threshold_returns_valid_grid_value() -> None:
    y = np.array([0, 0, 1, 1, 0, 1, 0])
    y_score = np.array([0.05, 0.2, 0.9, 0.7, 0.3, 0.6, 0.1])
    sev = ["none", "none", "warning", "warning", "none", "warning", "none"]
    thr = choose_threshold_by_expected_loss(
        y,
        y_score,
        sev,
        weights={"none": 1.0, "warning": 1.0},
        fn_over_fp_cost_ratio=10.0,
    )
    assert 0.0 <= thr <= 1.0


def test_operating_point_report_math() -> None:
    y = np.array([1, 1, 0, 0])
    y_score = np.array([0.9, 0.4, 0.6, 0.1])
    span = timedelta(days=7)
    op = operating_point_report(y, y_score, threshold=0.5, span=span)
    assert op.precision == 0.5
    assert op.recall == 0.5
    assert op.fpr == 0.5
    assert abs(op.warnings_per_week - 2.0) < 1e-6


def test_bootstrap_ci_returns_ordered_bounds() -> None:
    rng = np.random.default_rng(0)
    n = 200
    y = rng.integers(0, 2, size=n)
    a = rng.random(n)
    b = rng.random(n)
    times = [datetime(2026, 6, 1, tzinfo=UTC) + timedelta(minutes=5 * i) for i in range(n)]

    def metric(y_arr, s_arr) -> float:
        return float(np.mean(s_arr[y_arr == 1])) if (y_arr == 1).any() else 0.0

    lower, upper = bootstrap_ci_of_difference(
        metric,
        y_true=y,
        y_score_a=a,
        y_score_b=b,
        times=times,
        resamples=100,
        seed=1,
        alpha=0.05,
    )
    assert lower <= upper


def test_gate_config_bonferroni() -> None:
    gate = GateConfig(alpha=0.05, bonferroni_across=4)
    assert abs(gate.per_test_alpha - 0.0125) < 1e-9
