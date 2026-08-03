"""8 benchmark dimensions + Measurement value type (RFC §4).

Dimensions and default weights are locked at RFC scoping-approval. Placeholders here
match RFC v0.2 §6.2 proposals. The scoping-approval meeting locks the real weights
by constructing a WeightedScoreRubric with an overriding weights dict.

v0.2 (Codex round-1 loop, 2026-08-03): added D8 evidence integrity + operability per
RFC v0.2 §4. Added `FROZEN` and `NOT_MEASURED` MeasurementStatus values per RFC v0.2
§8 R1 scoring freeze + §6.2.1 absolute-anchor discipline (missing data ≠ successful
measurement).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MeasurementStatus(str, Enum):
    """Where a measurement came from — separates real measurements from stub / placeholder.

    v0.2 additions (Codex round-1 loop, 2026-08-03):

    - ``FROZEN`` — measurement WOULD produce a value, but scoring is frozen per RFC §8 R1
      (Option A pre-implementation asymmetry — see RFC v0.2 §8 R1 rewrite). Freeze lifts
      when B-F prototypes reach effort parity OR a blinded reviewer runs.

    - ``NOT_MEASURED`` — measurement path exists in the methodology but has not produced
      a value yet (e.g., requires a run against real infrastructure). Distinct from
      NOT_APPLICABLE (where the methodology itself cannot apply) and NOT_IMPLEMENTED
      (where the stub has no measurement code at all). Per RFC v0.2 §6.2.1, missing data
      scores 0 — a NOT_MEASURED value does NOT count as an OK measurement.
    """

    OK = "ok"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"
    NOT_MEASURED = "not_measured"
    FROZEN = "frozen"
    FAILED = "failed"


@dataclass(frozen=True)
class Dimension:
    """One of the 8 benchmark dimensions (RFC §4)."""

    code: str
    name: str
    unit: str
    higher_is_better: bool
    default_weight: int
    description: str


D1_REPLAY = Dimension(
    code="D1",
    name="Historical reproducibility",
    unit="seconds + completion %",
    higher_is_better=False,
    default_weight=3,
    description=(
        "Time to reproduce the last 30 days of predictions from each option's canonical "
        "retained source. Common correctness threshold: byte-identical predictions on "
        "≥99.9% of replayed events. Retraining + audit-window reconstruction require "
        "bounded recomputation time."
    ),
)

D2_BACKPRESSURE = Dimension(
    code="D2",
    name="Backpressure handling",
    unit="qualitative + max sustainable QPS",
    higher_is_better=True,
    default_weight=2,
    description=(
        "Behavior at 10x §2.4 baseline input rate (500 events/sec) — does it queue, drop, "
        "block upstream, or degrade gracefully? Weight=2 unless §2.4 envelope invalidates."
    ),
)

D3_MODEL_ROLLOUT = Dimension(
    code="D3",
    name="Model rollout mechanics",
    unit="ordered steps + wall-clock",
    higher_is_better=False,
    default_weight=4,
    description=(
        "Steps + time from 'new model artifact in MLflow registry' to 'predictions using new model'. "
        "We WILL iterate on models; friction here compounds."
    ),
)

D4_FAILURE_ISOLATION = Dimension(
    code="D4",
    name="Failure isolation",
    unit="qualitative severity 1-5",
    higher_is_better=True,
    default_weight=4,
    description=(
        "Impact of predictor crash on (a) other Flink jobs / co-located jobs, "
        "(b) Kafka backlog, (c) upstream data producers. Explicitly measures blast radius "
        "when the predictor faults; operability sub-checks (telemetry / MTTR / rollback / "
        "abstention) live in D8."
    ),
)

D5_COST = Dimension(
    code="D5",
    name="Cost per prediction",
    unit="USD per 1M predictions",
    higher_is_better=False,
    default_weight=2,
    description=(
        "Fully-loaded infra cost for 1M predictions (compute + storage + network) at representative "
        "on-demand pricing. v0 volumes small; cost is v1 concern unless >10x more expensive than others."
    ),
)

D6_LATENCY = Dimension(
    code="D6",
    name="Latency envelope",
    unit="p50 / p95 / p99 milliseconds",
    higher_is_better=False,
    default_weight=3,
    description=(
        "Wall-clock time from source event committed to Kafka to prediction available to consumer. "
        "Deploy-SLO-breach estimand is ~60min horizon; latency <60s is more than sufficient."
    ),
)

D7_COGNITIVE_LOAD = Dimension(
    code="D7",
    name="Cognitive load on platform team",
    unit="qualitative 1-5 + new-concept list",
    higher_is_better=True,
    default_weight=3,
    description=(
        "New concepts, tools, or runbooks required. Baseline: existing Flink stack. "
        "Real cost paid every day; underweighting this leads to abandoned tech."
    ),
)

D8_EVIDENCE_INTEGRITY = Dimension(
    code="D8",
    name="Evidence integrity + operability",
    unit="qualitative + coverage % per sub-check",
    higher_is_better=True,
    default_weight=4,
    description=(
        "Composite dimension covering: (a) replay determinism, (b) prediction identity "
        "stability under retry, (c) full PC §3 field-conformance emission, (d) lifecycle "
        "event delivery per PC §5, (e) label-join viability per GT §7 join key, "
        "(f) audit-sink completeness under retry and crash, (g) operability: telemetry, "
        "alerting, MTTR envelope, rollback, model fallback/abstention, runbook, ownership. "
        "Corpus non-negotiable per README §Graduation criteria."
    ),
)


DIMENSIONS: tuple[Dimension, ...] = (
    D1_REPLAY,
    D2_BACKPRESSURE,
    D3_MODEL_ROLLOUT,
    D4_FAILURE_ISOLATION,
    D5_COST,
    D6_LATENCY,
    D7_COGNITIVE_LOAD,
    D8_EVIDENCE_INTEGRITY,
)

DEFAULT_WEIGHTS: dict[str, int] = {d.code: d.default_weight for d in DIMENSIONS}


@dataclass(frozen=True)
class Measurement:
    """A single dimension measurement for one placement option."""

    dimension_code: str
    status: MeasurementStatus
    value: float | None = None
    qualitative: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.dimension_code not in DEFAULT_WEIGHTS:
            msg = f"unknown dimension code: {self.dimension_code}"
            raise ValueError(msg)
        if self.status is MeasurementStatus.OK and self.value is None and not self.qualitative:
            msg = "measurement with status=OK must carry a value or qualitative note"
            raise ValueError(msg)
        # v0.2: FROZEN and NOT_MEASURED explicitly MUST NOT carry a value — the whole
        # point is to prevent laundering a static assertion as a valid score.
        no_value_statuses = {MeasurementStatus.FROZEN, MeasurementStatus.NOT_MEASURED}
        if self.status in no_value_statuses and self.value is not None:
            msg = (
                f"measurement with status={self.status.value} MUST NOT carry a value "
                "— use qualitative + note to document"
            )
            raise ValueError(msg)

    @property
    def is_real(self) -> bool:
        return self.status is MeasurementStatus.OK


def dimension_by_code(code: str) -> Dimension:
    for d in DIMENSIONS:
        if d.code == code:
            return d
    msg = f"unknown dimension code: {code}"
    raise ValueError(msg)
