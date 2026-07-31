"""7 benchmark dimensions + Measurement value type (RFC §4).

Dimensions and default weights are locked at RFC scoping-approval. Placeholders here
match RFC v0.1 §6.2 proposals. The scoping-approval meeting locks the real weights
by constructing a WeightedScoreRubric with an overriding weights dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MeasurementStatus(str, Enum):
    """Where a measurement came from — separates real measurements from stub / placeholder."""

    OK = "ok"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


@dataclass(frozen=True)
class Dimension:
    """One of the 7 benchmark dimensions (RFC §4)."""

    code: str
    name: str
    unit: str
    higher_is_better: bool
    default_weight: int
    description: str


D1_REPLAY = Dimension(
    code="D1",
    name="Replay behavior",
    unit="seconds",
    higher_is_better=False,
    default_weight=3,
    description=(
        "Time to replay 30 days of events from Kafka offset zero to current tip. "
        "Critical for retraining + audit; missing this makes calibration impossible."
    ),
)

D2_BACKPRESSURE = Dimension(
    code="D2",
    name="Backpressure handling",
    unit="qualitative + max sustainable QPS",
    higher_is_better=True,
    default_weight=2,
    description=(
        "Behavior at 10x input rate — does it queue, drop, block upstream, or degrade gracefully? "
        "v0 is low-volume; matters more at v1."
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
        "Impact of predictor crash on (a) other Flink jobs, (b) Kafka backlog, "
        "(c) upstream data producers. Advisory-only means low blast radius, but engineer trust "
        "depends on isolation from deterministic paths."
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


DIMENSIONS: tuple[Dimension, ...] = (
    D1_REPLAY,
    D2_BACKPRESSURE,
    D3_MODEL_ROLLOUT,
    D4_FAILURE_ISOLATION,
    D5_COST,
    D6_LATENCY,
    D7_COGNITIVE_LOAD,
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

    @property
    def is_real(self) -> bool:
        return self.status is MeasurementStatus.OK


def dimension_by_code(code: str) -> Dimension:
    for d in DIMENSIONS:
        if d.code == code:
            return d
    msg = f"unknown dimension code: {code}"
    raise ValueError(msg)
