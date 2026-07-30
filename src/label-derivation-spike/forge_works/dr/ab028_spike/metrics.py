"""Metrics + statistical machinery for the AB-028 GO/no-GO gate (RFC §6).

Implements:
- M1 AUCPR — sklearn `average_precision_score`.
- M2 ECE  — equal-mass 10 bins with min-5-obs merging, plus MCE and reliability diagram.
- M3 Brier — plus the constant-predictor sanity floor.
- C1 expected loss — severity-weighted, with `k` FN:FP cost ratio.
- Temporal block bootstrap CIs (60-min blocks, 1000 resamples by default).
- Bonferroni correction across the four primary comparisons at alpha = 0.05.

Placeholder GateConfig thresholds mirror the RFC v0.2 proposals — the scoping-approval meeting
locks the real numbers via `GateConfig(...)` at run time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime, timedelta

BLOCK_MINUTES = 60
DEFAULT_BOOTSTRAP_RESAMPLES = 1000
DEFAULT_ALPHA = 0.05
N_PRIMARY_COMPARISONS = 4


@dataclass(frozen=True)
class GateConfig:
    """Threshold config for the GO/no-GO gate. Placeholders match RFC §6 v0.2 proposals."""

    m1_absolute_lift: float = 0.05
    m1_normalized_lift_over_prevalence: float = 0.10
    m2_ece_ceiling: float = 0.10
    c1_reduction_bar: float = 0.30
    precision_floor: float = 0.40
    warnings_per_week_ceiling: float = 5.0
    fpr_ceiling: float = 0.25
    severity_weights: dict[str, float] = field(
        default_factory=lambda: {"critical": 3.0, "major": 2.0, "warning": 1.0, "none": 1.0}
    )
    fn_over_fp_cost_ratio: float = 10.0
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES
    alpha: float = DEFAULT_ALPHA
    bonferroni_across: int = N_PRIMARY_COMPARISONS
    seed: int = 20260728

    @property
    def per_test_alpha(self) -> float:
        return self.alpha / self.bonferroni_across


@dataclass(frozen=True)
class CalibrationDiagram:
    bin_edges: list[float]
    bin_means_predicted: list[float]
    bin_observed_frequencies: list[float]
    bin_counts: list[int]


@dataclass(frozen=True)
class MetricReport:
    aucpr: float
    brier: float
    ece: float
    mce: float
    calibration_diagram: CalibrationDiagram
    prevalence: float


def evaluate_predictions(
    y_true: np.ndarray, y_score: np.ndarray, *, n_bins: int = 10, min_bin_obs: int = 5
) -> MetricReport:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    if len(y_true) != len(y_score):
        msg = f"length mismatch: y_true={len(y_true)}, y_score={len(y_score)}"
        raise ValueError(msg)
    prevalence = float(y_true.mean()) if len(y_true) else 0.0
    aucpr = float(average_precision_score(y_true, y_score)) if prevalence > 0 else 0.0
    brier = float(brier_score_loss(y_true, y_score))
    diagram = _equal_mass_calibration(y_true, y_score, n_bins=n_bins, min_bin_obs=min_bin_obs)
    ece = _ece_from_diagram(diagram, total=len(y_true))
    mce = _mce_from_diagram(diagram)
    return MetricReport(
        aucpr=aucpr,
        brier=brier,
        ece=ece,
        mce=mce,
        calibration_diagram=diagram,
        prevalence=prevalence,
    )


def constant_predictor_brier(prevalence: float) -> float:
    return prevalence * (1.0 - prevalence)


def compute_c1_expected_loss(
    y_true: np.ndarray,
    y_pred_binary: np.ndarray,
    *,
    severities: Sequence[str],
    weights: dict[str, float],
    fn_over_fp_cost_ratio: float,
) -> float:
    y_true = np.asarray(y_true).astype(int)
    y_pred_binary = np.asarray(y_pred_binary).astype(int)
    if len(severities) != len(y_true):
        msg = "severity vector must match label vector length"
        raise ValueError(msg)
    missed_positive_cost = 0.0
    false_positive_count = 0
    for truth, pred, sev in zip(y_true, y_pred_binary, severities, strict=True):
        if truth == 1 and pred == 0:
            missed_positive_cost += weights.get(sev, weights.get("none", 1.0))
        elif truth == 0 and pred == 1:
            false_positive_count += 1
    return fn_over_fp_cost_ratio * missed_positive_cost + false_positive_count


def choose_threshold_by_expected_loss(
    y_val: np.ndarray,
    y_score_val: np.ndarray,
    severities_val: Sequence[str],
    *,
    weights: dict[str, float],
    fn_over_fp_cost_ratio: float,
    grid_size: int = 101,
) -> float:
    """Select the threshold minimizing expected loss on validation (RFC §6.3 F4)."""
    y_val = np.asarray(y_val)
    y_score_val = np.asarray(y_score_val)
    grid = np.linspace(0.0, 1.0, grid_size)
    best_loss = math.inf
    best_thr = 0.5
    for thr in grid:
        y_pred = (y_score_val >= thr).astype(int)
        loss = compute_c1_expected_loss(
            y_val,
            y_pred,
            severities=severities_val,
            weights=weights,
            fn_over_fp_cost_ratio=fn_over_fp_cost_ratio,
        )
        if loss < best_loss:
            best_loss = loss
            best_thr = float(thr)
    return best_thr


@dataclass(frozen=True)
class OperatingPointReport:
    threshold: float
    precision: float
    recall: float
    fpr: float
    warnings_per_week: float


def operating_point_report(
    y_true: np.ndarray,
    y_score: np.ndarray,
    *,
    threshold: float,
    span: timedelta,
) -> OperatingPointReport:
    y_pred = (y_score >= threshold).astype(int)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    weeks = max(span.total_seconds() / (7 * 86_400), 1e-6)
    warnings_per_week = (tp + fp) / weeks
    return OperatingPointReport(
        threshold=threshold,
        precision=precision,
        recall=recall,
        fpr=fpr,
        warnings_per_week=warnings_per_week,
    )


def bootstrap_ci_of_difference(
    metric_fn,
    *,
    y_true: np.ndarray,
    y_score_a: np.ndarray,
    y_score_b: np.ndarray,
    times: list[datetime],
    resamples: int,
    seed: int,
    alpha: float,
) -> tuple[float, float]:
    """Temporal block bootstrap of (metric(a) - metric(b)); returns (lower, upper) CI."""
    y_true = np.asarray(y_true)
    y_score_a = np.asarray(y_score_a)
    y_score_b = np.asarray(y_score_b)
    blocks = _block_index(times, block_minutes=BLOCK_MINUTES)
    rng = np.random.default_rng(seed)
    diffs = np.empty(resamples, dtype=float)
    unique_blocks = np.unique(blocks)
    for i in range(resamples):
        drawn = rng.choice(unique_blocks, size=len(unique_blocks), replace=True)
        idx = np.concatenate([np.where(blocks == b)[0] for b in drawn])
        if len(np.unique(y_true[idx])) < 2:
            diffs[i] = 0.0
            continue
        diffs[i] = metric_fn(y_true[idx], y_score_a[idx]) - metric_fn(y_true[idx], y_score_b[idx])
    lower = float(np.quantile(diffs, alpha / 2))
    upper = float(np.quantile(diffs, 1.0 - alpha / 2))
    return lower, upper


def _block_index(times: list[datetime], *, block_minutes: int) -> np.ndarray:
    if not times:
        return np.array([], dtype=int)
    t0 = times[0]
    result = np.empty(len(times), dtype=int)
    for i, t in enumerate(times):
        offset_min = (t - t0).total_seconds() / 60.0
        result[i] = int(offset_min // block_minutes)
    return result


def _equal_mass_calibration(
    y_true: np.ndarray, y_score: np.ndarray, *, n_bins: int, min_bin_obs: int
) -> CalibrationDiagram:
    order = np.argsort(y_score, kind="stable")
    sorted_scores = y_score[order]
    sorted_truth = y_true[order]
    if len(sorted_scores) == 0:
        return CalibrationDiagram([], [], [], [])
    bin_edges_idx = _equal_mass_edges(len(sorted_scores), n_bins=n_bins)
    means_predicted: list[float] = []
    observed: list[float] = []
    counts: list[int] = []
    edges: list[float] = []
    merged_buffer_start: int | None = None
    for lo, hi in _iter_bins(bin_edges_idx):
        if merged_buffer_start is None:
            merged_buffer_start = lo
        current_lo = merged_buffer_start
        current_size = hi - current_lo
        if current_size < min_bin_obs:
            continue
        pred_mean = float(sorted_scores[current_lo:hi].mean())
        obs_mean = float(sorted_truth[current_lo:hi].mean())
        means_predicted.append(pred_mean)
        observed.append(obs_mean)
        counts.append(current_size)
        edges.append(float(sorted_scores[current_lo]))
        merged_buffer_start = None
    if merged_buffer_start is not None and merged_buffer_start < len(sorted_scores):
        lo = merged_buffer_start
        hi = len(sorted_scores)
        if means_predicted:
            total = counts[-1] + (hi - lo)
            means_predicted[-1] = (
                means_predicted[-1] * counts[-1] + float(sorted_scores[lo:hi].sum())
            ) / total
            observed[-1] = (observed[-1] * counts[-1] + float(sorted_truth[lo:hi].sum())) / total
            counts[-1] = total
        else:
            means_predicted.append(float(sorted_scores[lo:hi].mean()))
            observed.append(float(sorted_truth[lo:hi].mean()))
            counts.append(hi - lo)
            edges.append(float(sorted_scores[lo]))
    if edges:
        edges.append(float(sorted_scores[-1]))
    return CalibrationDiagram(
        bin_edges=edges,
        bin_means_predicted=means_predicted,
        bin_observed_frequencies=observed,
        bin_counts=counts,
    )


def _equal_mass_edges(n: int, *, n_bins: int) -> list[int]:
    base = n // n_bins
    remainder = n % n_bins
    edges = [0]
    idx = 0
    for i in range(n_bins):
        idx += base + (1 if i < remainder else 0)
        edges.append(idx)
    return edges


def _iter_bins(edges: list[int]):
    for i in range(len(edges) - 1):
        yield edges[i], edges[i + 1]


def _ece_from_diagram(diagram: CalibrationDiagram, *, total: int) -> float:
    if total == 0 or not diagram.bin_counts:
        return 0.0
    weighted = 0.0
    for pred, obs, count in zip(
        diagram.bin_means_predicted,
        diagram.bin_observed_frequencies,
        diagram.bin_counts,
        strict=True,
    ):
        weighted += (count / total) * abs(pred - obs)
    return weighted


def _mce_from_diagram(diagram: CalibrationDiagram) -> float:
    if not diagram.bin_counts:
        return 0.0
    return max(
        abs(p - o)
        for p, o in zip(diagram.bin_means_predicted, diagram.bin_observed_frequencies, strict=True)
    )
