"""End-to-end evaluation harness + GO/no-GO verdict (RFC §6.4).

Pipeline: catalog → synthetic stream → label derivation (AB-030) → feature matrix →
temporal train/val/test split → per-split floor check → fit rules + LR + GBT → operating-threshold
selection on validation → frozen-threshold test evaluation → block-bootstrap CIs → verdict.

The verdict object is the "spike report" data — the human-facing markdown report is downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import numpy as np
from forge_works.dr.ab028_spike.baselines.lr import build_lr_baseline
from forge_works.dr.ab028_spike.baselines.rules import RulesBaseline
from forge_works.dr.ab028_spike.events import generate_stream, stream_summary
from forge_works.dr.ab028_spike.features import FeatureMatrix, build_feature_matrix
from forge_works.dr.ab028_spike.labels import derive_labels
from forge_works.dr.ab028_spike.metrics import (
    GateConfig,
    bootstrap_ci_of_difference,
    choose_threshold_by_expected_loss,
    compute_c1_expected_loss,
    constant_predictor_brier,
    evaluate_predictions,
    operating_point_report,
)
from forge_works.dr.ab028_spike.model import build_gbt_model
from forge_works.dr.label_schema_validator import CatalogEntry, EstimandCatalog
from sklearn.metrics import average_precision_score, brier_score_loss

if TYPE_CHECKING:
    from datetime import datetime

    from forge_works.dr.ab028_spike.metrics import MetricReport


DEFAULT_TRAIN_FRACTION = 0.70
DEFAULT_VAL_FRACTION = 0.15
POSITIVE_FLOORS = {"train": 50, "val": 15, "test": 30}


@dataclass(frozen=True)
class MetadataWindowReport:
    """§4.4 pre-scoping metadata window: aggregate counts only, no label / feature values."""

    days: int
    deploys: int
    slo_breaches: int
    base_rate_estimate: float
    censoring_rate_estimate: float
    missing_data_rate_estimate: float
    deploys_per_day: float


@dataclass(frozen=True)
class SplitReport:
    positives_train: int
    positives_val: int
    positives_test: int
    floors_pass: bool
    floor_failures: list[str]


@dataclass(frozen=True)
class Verdict:
    outcome: str
    reasons: list[str]
    metadata_window: MetadataWindowReport
    split_report: SplitReport
    rules: dict[str, Any] = field(default_factory=dict)
    lr: dict[str, Any] = field(default_factory=dict)
    gbt: dict[str, Any] = field(default_factory=dict)
    per_metric_comparisons: dict[str, Any] = field(default_factory=dict)
    stream_summary: dict[str, Any] = field(default_factory=dict)


def build_default_catalog() -> EstimandCatalog:
    return EstimandCatalog(
        entries={
            "deploy_slo_breach_60m_association_v0": CatalogEntry(
                estimand_id="deploy_slo_breach_60m_association_v0",
                outcome_vocabulary=("slo_breach_occurred", "slo_breach_absent"),
                version="v0",
                owner="dynamic-reliability",
                notes="AB-028 spike v0 estimand — observational-association form per AB-033.",
            )
        },
    )


def run_spike(
    *,
    modeling_days: int = 60,
    metadata_days: int = 30,
    seed: int = 20260728,
    base_rate: float = 0.05,
    deploys_per_day: float = 12.0,
    catalog: EstimandCatalog | None = None,
    gate: GateConfig | None = None,
) -> Verdict:
    catalog = catalog or build_default_catalog()
    gate = gate or GateConfig()

    stream = generate_stream(
        modeling_days=modeling_days,
        metadata_days=metadata_days,
        seed=seed,
        base_rate=base_rate,
        deploys_per_day=deploys_per_day,
    )
    metadata_end = stream.start + timedelta(days=metadata_days)
    modeling_start = metadata_end
    modeling_end = stream.end

    metadata_report = _metadata_window_report(stream, stream.start, metadata_end)

    labels = derive_labels(
        stream,
        catalog=catalog,
        modeling_window_start=modeling_start,
        modeling_window_end=modeling_end,
    )
    if not labels:
        return _incomplete_verdict(
            outcome="inconclusive",
            reasons=["no labels derived on modeling window"],
            metadata=metadata_report,
            stream_summary=stream_summary(stream),
        )

    fm = build_feature_matrix(stream, labels)
    split_report, splits = _temporal_split(fm)
    if not split_report.floors_pass:
        return _incomplete_verdict(
            outcome="inconclusive",
            reasons=[
                f"per-split positive floor failed: {failure}"
                for failure in split_report.floor_failures
            ],
            metadata=metadata_report,
            split_report=split_report,
            stream_summary=stream_summary(stream),
        )

    train, val, test = splits
    rules = RulesBaseline().fit(train.X, train.y)
    lr = build_lr_baseline().fit(train.X, train.y)
    gbt = build_gbt_model().fit(train.X, train.y)

    val_severities = [train.severity_map.get(did, "none") for did in val.deploy_ids]
    test_severities = [train.severity_map.get(did, "none") for did in test.deploy_ids]

    rules_val_score = rules.predict_proba(val.X)[:, 1]
    lr_val_score = lr.predict_proba(val.X)[:, 1]
    gbt_val_score = gbt.predict_proba(val.X)[:, 1]

    rules_thr = choose_threshold_by_expected_loss(
        val.y.to_numpy(),
        rules_val_score,
        val_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )
    lr_thr = choose_threshold_by_expected_loss(
        val.y.to_numpy(),
        lr_val_score,
        val_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )
    gbt_thr = choose_threshold_by_expected_loss(
        val.y.to_numpy(),
        gbt_val_score,
        val_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )

    rules_test_score = rules.predict_proba(test.X)[:, 1]
    lr_test_score = lr.predict_proba(test.X)[:, 1]
    gbt_test_score = gbt.predict_proba(test.X)[:, 1]

    rules_report = evaluate_predictions(test.y.to_numpy(), rules_test_score)
    lr_report = evaluate_predictions(test.y.to_numpy(), lr_test_score)
    gbt_report = evaluate_predictions(test.y.to_numpy(), gbt_test_score)

    test_span = (
        test.deploy_times[-1] - test.deploy_times[0]
        if len(test.deploy_times) > 1
        else timedelta(days=1)
    )
    rules_op = operating_point_report(
        test.y.to_numpy(), rules_test_score, threshold=rules_thr, span=test_span
    )
    lr_op = operating_point_report(
        test.y.to_numpy(), lr_test_score, threshold=lr_thr, span=test_span
    )
    gbt_op = operating_point_report(
        test.y.to_numpy(), gbt_test_score, threshold=gbt_thr, span=test_span
    )

    rules_loss = compute_c1_expected_loss(
        test.y.to_numpy(),
        (rules_test_score >= rules_thr).astype(int),
        severities=test_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )
    lr_loss = compute_c1_expected_loss(
        test.y.to_numpy(),
        (lr_test_score >= lr_thr).astype(int),
        severities=test_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )
    gbt_loss = compute_c1_expected_loss(
        test.y.to_numpy(),
        (gbt_test_score >= gbt_thr).astype(int),
        severities=test_severities,
        weights=gate.severity_weights,
        fn_over_fp_cost_ratio=gate.fn_over_fp_cost_ratio,
    )

    comparisons = _evaluate_comparisons(
        gate=gate,
        y_test=test.y.to_numpy(),
        times=test.deploy_times,
        rules_score=rules_test_score,
        lr_score=lr_test_score,
        gbt_score=gbt_test_score,
        rules_report=rules_report,
        lr_report=lr_report,
        gbt_report=gbt_report,
        rules_loss=rules_loss,
        lr_loss=lr_loss,
        gbt_loss=gbt_loss,
        gbt_op=gbt_op,
    )

    outcome, reasons = _decide(gate, gbt_report, comparisons, gbt_op)

    return Verdict(
        outcome=outcome,
        reasons=reasons,
        metadata_window=metadata_report,
        split_report=split_report,
        rules=_pack(rules_report, rules_op, rules_loss, threshold=rules_thr),
        lr=_pack(lr_report, lr_op, lr_loss, threshold=lr_thr),
        gbt=_pack(gbt_report, gbt_op, gbt_loss, threshold=gbt_thr),
        per_metric_comparisons=comparisons,
        stream_summary=stream_summary(stream),
    )


def _pack(report: MetricReport, op: Any, loss: float, *, threshold: float) -> dict[str, Any]:
    return {
        "aucpr": report.aucpr,
        "brier": report.brier,
        "ece": report.ece,
        "mce": report.mce,
        "prevalence": report.prevalence,
        "threshold": threshold,
        "expected_loss": loss,
        "precision": op.precision,
        "recall": op.recall,
        "fpr": op.fpr,
        "warnings_per_week": op.warnings_per_week,
    }


def _metadata_window_report(stream: Any, start: datetime, end: datetime) -> MetadataWindowReport:
    total_days = max((end - start).days, 1)
    _ = start  # named for clarity; window is bounded by end for the metadata cohort
    deploys = [d for d in stream.deploys if start <= d.deployed_at < end]
    breaches = [b for b in stream.slo_breaches if start <= b.event_time < end]
    n_deploys = len(deploys)
    n_breaches = len(breaches)
    base_rate = n_breaches / n_deploys if n_deploys else 0.0

    censoring = 0
    missing = 0
    for i, deploy in enumerate(deploys):
        window_end = deploy.deployed_at + timedelta(minutes=60)
        if i + 1 < len(deploys) and deploys[i + 1].deployed_at < window_end:
            censoring += 1
        elif _muted_between(stream.monitor_events, deploy.deployed_at, window_end):
            missing += 1
    return MetadataWindowReport(
        days=total_days,
        deploys=n_deploys,
        slo_breaches=n_breaches,
        base_rate_estimate=base_rate,
        censoring_rate_estimate=censoring / n_deploys if n_deploys else 0.0,
        missing_data_rate_estimate=missing / n_deploys if n_deploys else 0.0,
        deploys_per_day=n_deploys / total_days,
    )


def _muted_between(monitor_events: list[Any], start: datetime, end: datetime) -> bool:
    del start  # baseline state derived by scanning up to end; start bounds the caller's cohort
    state = "ok"
    for e in monitor_events:
        if e.event_time >= end:
            break
        state = e.state
    return state in {"muted", "unknown"}


def _temporal_split(
    fm: FeatureMatrix,
) -> tuple[SplitReport, tuple[FeatureMatrix, FeatureMatrix, FeatureMatrix]]:
    n = fm.n_rows
    if n == 0:
        report = SplitReport(0, 0, 0, floors_pass=False, floor_failures=["no rows"])
        return report, (fm, fm, fm)
    train_end = int(n * DEFAULT_TRAIN_FRACTION)
    val_end = train_end + int(n * DEFAULT_VAL_FRACTION)
    train = _slice_fm(fm, 0, train_end)
    val = _slice_fm(fm, train_end, val_end)
    test = _slice_fm(fm, val_end, n)
    failures = []
    if int(train.y.sum()) < POSITIVE_FLOORS["train"]:
        failures.append(f"train positives {int(train.y.sum())} < floor {POSITIVE_FLOORS['train']}")
    if int(val.y.sum()) < POSITIVE_FLOORS["val"]:
        failures.append(f"val positives {int(val.y.sum())} < floor {POSITIVE_FLOORS['val']}")
    if int(test.y.sum()) < POSITIVE_FLOORS["test"]:
        failures.append(f"test positives {int(test.y.sum())} < floor {POSITIVE_FLOORS['test']}")
    report = SplitReport(
        positives_train=int(train.y.sum()),
        positives_val=int(val.y.sum()),
        positives_test=int(test.y.sum()),
        floors_pass=not failures,
        floor_failures=failures,
    )
    return report, (train, val, test)


def _slice_fm(fm: FeatureMatrix, start: int, end: int) -> FeatureMatrix:
    return FeatureMatrix(
        X=fm.X.iloc[start:end].reset_index(drop=True),
        y=fm.y.iloc[start:end].reset_index(drop=True),
        deploy_ids=fm.deploy_ids[start:end],
        deploy_times=fm.deploy_times[start:end],
        severity_map=fm.severity_map,
    )


def _evaluate_comparisons(
    *,
    gate: GateConfig,
    y_test: np.ndarray,
    times: list[datetime],
    rules_score: np.ndarray,
    lr_score: np.ndarray,
    gbt_score: np.ndarray,
    rules_report: MetricReport,
    lr_report: MetricReport,
    gbt_report: MetricReport,
    rules_loss: float,
    lr_loss: float,
    gbt_loss: float,
    gbt_op: Any,
) -> dict[str, Any]:
    del gbt_op

    def ap_metric(y: np.ndarray, s: np.ndarray) -> float:
        if len(np.unique(y)) < 2:
            return 0.0
        return float(average_precision_score(y, s))

    def brier_metric(y: np.ndarray, s: np.ndarray) -> float:
        return float(brier_score_loss(y, s))

    m1_lower_vs_rules, _ = bootstrap_ci_of_difference(
        ap_metric,
        y_true=y_test,
        y_score_a=gbt_score,
        y_score_b=rules_score,
        times=times,
        resamples=gate.bootstrap_resamples,
        seed=gate.seed,
        alpha=gate.per_test_alpha,
    )
    m1_lower_vs_lr, _ = bootstrap_ci_of_difference(
        ap_metric,
        y_true=y_test,
        y_score_a=gbt_score,
        y_score_b=lr_score,
        times=times,
        resamples=gate.bootstrap_resamples,
        seed=gate.seed + 1,
        alpha=gate.per_test_alpha,
    )
    m1_absolute_lift_vs_max_baseline = gbt_report.aucpr - max(rules_report.aucpr, lr_report.aucpr)

    def neg_brier_metric(y: np.ndarray, s: np.ndarray) -> float:
        return -brier_metric(y, s)

    m3_lower_vs_rules, _ = bootstrap_ci_of_difference(
        neg_brier_metric,
        y_true=y_test,
        y_score_a=gbt_score,
        y_score_b=rules_score,
        times=times,
        resamples=gate.bootstrap_resamples,
        seed=gate.seed + 2,
        alpha=gate.per_test_alpha,
    )
    m3_lower_vs_lr, _ = bootstrap_ci_of_difference(
        neg_brier_metric,
        y_true=y_test,
        y_score_a=gbt_score,
        y_score_b=lr_score,
        times=times,
        resamples=gate.bootstrap_resamples,
        seed=gate.seed + 3,
        alpha=gate.per_test_alpha,
    )

    return {
        "m1_lower_vs_rules": m1_lower_vs_rules,
        "m1_lower_vs_lr": m1_lower_vs_lr,
        "m1_absolute_lift_vs_max_baseline": m1_absolute_lift_vs_max_baseline,
        "m1_normalized_lift_over_prevalence": gbt_report.aucpr - gbt_report.prevalence,
        "m2_ece": gbt_report.ece,
        "m3_gbt_brier": gbt_report.brier,
        "m3_constant_predictor_brier": constant_predictor_brier(gbt_report.prevalence),
        "m3_lower_vs_rules": m3_lower_vs_rules,
        "m3_lower_vs_lr": m3_lower_vs_lr,
        "c1_gbt_loss": gbt_loss,
        "c1_lr_loss": lr_loss,
        "c1_rules_loss": rules_loss,
        "c1_reduction_vs_rules": (rules_loss - gbt_loss) / rules_loss if rules_loss else 0.0,
        "c1_reduction_vs_lr": (lr_loss - gbt_loss) / lr_loss if lr_loss else 0.0,
    }


def _decide(
    gate: GateConfig,
    gbt_report: MetricReport,
    comp: dict[str, Any],
    gbt_op: Any,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    reasons.extend(_check_m1(gate, comp))
    reasons.extend(_check_m2(gate, gbt_report))
    reasons.extend(_check_m3(comp))
    reasons.extend(_check_c1(gate, comp))
    reasons.extend(_check_operating_point(gate, gbt_op))
    if not reasons:
        return "go", ["all §6 gates passed"]
    return "no-go", reasons


def _check_m1(gate: GateConfig, comp: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if comp["m1_lower_vs_rules"] < gate.m1_absolute_lift:
        out.append(
            f"M1 lower CI vs rules = {comp['m1_lower_vs_rules']:.4f} < {gate.m1_absolute_lift}"
        )
    if comp["m1_lower_vs_lr"] < gate.m1_absolute_lift:
        out.append(f"M1 lower CI vs LR = {comp['m1_lower_vs_lr']:.4f} < {gate.m1_absolute_lift}")
    if comp["m1_normalized_lift_over_prevalence"] < gate.m1_normalized_lift_over_prevalence:
        out.append(
            f"M1 normalized lift {comp['m1_normalized_lift_over_prevalence']:.4f} < "
            f"{gate.m1_normalized_lift_over_prevalence}"
        )
    return out


def _check_m2(gate: GateConfig, gbt_report: MetricReport) -> list[str]:
    if gbt_report.ece > gate.m2_ece_ceiling:
        return [f"M2 ECE {gbt_report.ece:.4f} > ceiling {gate.m2_ece_ceiling}"]
    return []


def _check_m3(comp: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if comp["m3_gbt_brier"] >= comp["m3_constant_predictor_brier"]:
        out.append(
            f"M3 Brier {comp['m3_gbt_brier']:.4f} >= constant-predictor "
            f"{comp['m3_constant_predictor_brier']:.4f}"
        )
    if comp["m3_lower_vs_rules"] <= 0:
        out.append(f"M3 lower CI vs rules {comp['m3_lower_vs_rules']:.4f} <= 0")
    if comp["m3_lower_vs_lr"] <= 0:
        out.append(f"M3 lower CI vs LR {comp['m3_lower_vs_lr']:.4f} <= 0")
    return out


def _check_c1(gate: GateConfig, comp: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if comp["c1_reduction_vs_rules"] < gate.c1_reduction_bar:
        out.append(
            f"C1 reduction vs rules {comp['c1_reduction_vs_rules']:.4f} < {gate.c1_reduction_bar}"
        )
    if comp["c1_reduction_vs_lr"] < gate.c1_reduction_bar:
        out.append(f"C1 reduction vs LR {comp['c1_reduction_vs_lr']:.4f} < {gate.c1_reduction_bar}")
    return out


def _check_operating_point(gate: GateConfig, gbt_op: Any) -> list[str]:
    out: list[str] = []
    if gbt_op.precision < gate.precision_floor:
        out.append(f"precision {gbt_op.precision:.4f} < floor {gate.precision_floor}")
    if gbt_op.warnings_per_week > gate.warnings_per_week_ceiling:
        out.append(
            f"warnings/week {gbt_op.warnings_per_week:.2f} > ceiling "
            f"{gate.warnings_per_week_ceiling}"
        )
    if gbt_op.fpr > gate.fpr_ceiling:
        out.append(f"FPR {gbt_op.fpr:.4f} > ceiling {gate.fpr_ceiling}")
    return out


def _incomplete_verdict(
    *,
    outcome: str,
    reasons: list[str],
    metadata: MetadataWindowReport,
    split_report: SplitReport | None = None,
    stream_summary: dict[str, Any] | None = None,
) -> Verdict:
    return Verdict(
        outcome=outcome,
        reasons=reasons,
        metadata_window=metadata,
        split_report=split_report
        or SplitReport(0, 0, 0, floors_pass=False, floor_failures=reasons),
        stream_summary=stream_summary or {},
    )
