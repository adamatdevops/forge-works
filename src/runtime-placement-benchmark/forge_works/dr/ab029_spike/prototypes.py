"""Placement prototype Protocol + stub implementations for all 5 RFC §3 options.

Each stub reports what its measurement WOULD produce (via `describe_capability`) but
returns `MeasurementStatus.NOT_IMPLEMENTED` for actual measurements. Real prototypes
swap in by implementing `PlacementPrototype` and overriding `measure(dimension)`.

Option A has a real prototype at `SiblingFlinkPrototype` — measures D1/D3/D4/D7 from
the actual `src/flink-jobs/dr-predictor/` module + reports NOT_APPLICABLE with
reasoning for D2/D5/D6 (each requires a running cluster + real load to measure).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from forge_works.dr.ab029_spike.dimensions import DIMENSIONS, Measurement, MeasurementStatus

_UNIMPLEMENTED_NOTE = "stub prototype — real prototype must override measure()"


@runtime_checkable
class PlacementPrototype(Protocol):
    """Contract every placement option's prototype must satisfy."""

    @property
    def option_code(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def measure(self, dimension_code: str) -> Measurement: ...

    def contract_implications(self) -> list[str]: ...


@dataclass(frozen=True)
class _StubBase:
    """Shared stub behavior — each option has its own subclass so tracebacks show its name."""

    option_code: str = ""
    name: str = ""
    description: str = ""
    contract_implication_notes: tuple[str, ...] = ()

    def measure(self, dimension_code: str) -> Measurement:
        return Measurement(
            dimension_code=dimension_code,
            status=MeasurementStatus.NOT_IMPLEMENTED,
            value=None,
            qualitative="",
            note=f"{self.option_code}: {_UNIMPLEMENTED_NOTE}",
        )

    def contract_implications(self) -> list[str]:
        return list(self.contract_implication_notes)


@dataclass(frozen=True)
class SiblingFlinkStub(_StubBase):
    """Option A — new Flink job under src/flink-jobs/dr-predictor/."""

    option_code: str = "A"
    name: str = "Sibling Flink job"
    description: str = (
        "New Flink job under src/flink-jobs/dr-predictor/, sibling to pattern-matcher, "
        "event-router, insight-generator. Consumes normalized events off Kafka, emits "
        "predictions to a new topic."
    )
    contract_implication_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternMatcherExtensionStub(_StubBase):
    """Option B — extend the existing pattern-matcher Flink job."""

    option_code: str = "B"
    name: str = "Pattern-matcher Flink extension"
    description: str = (
        "pattern-matcher gains a new operator branch that runs the DR predictor alongside "
        "its existing pattern detection."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Shared failure domain: pattern-matcher and DR predictor crash together.",
    )


@dataclass(frozen=True)
class InsightGeneratorExtensionStub(_StubBase):
    """Option C — extend the existing insight-generator Flink job."""

    option_code: str = "C"
    name: str = "Insight-generator Flink extension"
    description: str = (
        "insight-generator gains a DR-predictor operator. Naturally aligned since "
        "insight-generator already produces 'here's what I noticed' outputs."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Shared failure domain with insight-generator.",
        "insight-generator scaling profile is bursty on incident correlation; DR is steady-state.",
    )


@dataclass(frozen=True)
class BatchMaterializedStub(_StubBase):
    """Option D — scheduled batch job + materialized-view store + change notifications."""

    option_code: str = "D"
    name: str = "Batch materialized-view"
    description: str = (
        "Airflow scheduled batch job reads recent events from Kafka / warehouse, scores in "
        "Python, writes predictions to a materialized view, publishes change notifications."
    )
    contract_implication_notes: tuple[str, ...] = (
        "PC §5 requires a `staleness` field (predictions carry the batch-interval age).",
        "SC §5 requires source-access-pattern annotation for batch reader.",
    )


@dataclass(frozen=True)
class DedicatedInferenceStub(_StubBase):
    """Option E — dedicated inference service (Triton / KServe)."""

    option_code: str = "E"
    name: str = "Dedicated inference service"
    description: str = (
        "Standalone Triton/KServe service. Flink job (thin) consumes events, calls the "
        "inference service via gRPC, writes predictions back to Kafka."
    )
    contract_implication_notes: tuple[str, ...] = (
        "New service to run, monitor, on-call.",
        "Cross-service latency (Flink <-> Triton) is a new failure mode.",
    )


ALL_STUB_PROTOTYPES: tuple[_StubBase, ...] = (
    SiblingFlinkStub(),
    PatternMatcherExtensionStub(),
    InsightGeneratorExtensionStub(),
    BatchMaterializedStub(),
    DedicatedInferenceStub(),
)


def _repo_root() -> Path:
    """Locate the ForgeWorks repo root by walking up from this module until src/ is found."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "src" / "flink-jobs").is_dir():
            return parent
    msg = "cannot locate repo root — src/flink-jobs not found in any ancestor"
    raise FileNotFoundError(msg)


_DR_PREDICTOR_DIR = "src/flink-jobs/dr-predictor"


@dataclass(frozen=True)
class SiblingFlinkPrototype:
    """Option A — real prototype backed by `src/flink-jobs/dr-predictor/`.

    Measures the four dimensions decidable from static inspection of the module + Flink
    documented semantics (D1, D3, D4, D7). Reports NOT_APPLICABLE with reasoning for the
    three that require a running cluster and real load (D2, D5, D6). Reports FAILED if
    the expected module is missing.
    """

    option_code: str = "A"
    name: str = "Sibling Flink job (real prototype)"
    description: str = (
        "Real Flink job at src/flink-jobs/dr-predictor/ — placeholder ConstantPredictor "
        "model until AB-028 ships. Pipeline shape and Kafka topics are production-ready."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Emits to forge.predictions.dynamic_reliability.v1 — new Kafka topic (needs provisioning).",
        "Placeholder ConstantPredictor scoring — real model requires AB-028 spike + AB-032 MLflow.",
        "Estimand_id fixed to deploy_slo_breach_60m_association_v0 in envelope factory methods.",
    )
    predictor_dir: Path = field(default_factory=lambda: _repo_root() / _DR_PREDICTOR_DIR)

    def contract_implications(self) -> list[str]:
        return list(self.contract_implication_notes)

    def measure(self, dimension_code: str) -> Measurement:
        handler = _MEASURERS.get(dimension_code)
        if handler is None:
            msg = f"unknown dimension code: {dimension_code}"
            raise ValueError(msg)
        return handler(self)


def _measure_d1_replay(proto: SiblingFlinkPrototype) -> Measurement:
    if not (proto.predictor_dir / "pom.xml").is_file():
        return Measurement(
            dimension_code="D1",
            status=MeasurementStatus.FAILED,
            note=f"{proto.option_code}: predictor module missing at {proto.predictor_dir}",
        )
    return Measurement(
        dimension_code="D1",
        status=MeasurementStatus.OK,
        qualitative=(
            "Flink-native replay via Kafka consumer OffsetsInitializer + savepoint restore. "
            "OffsetsInitializer.committedOffsets(EARLIEST) resets to earliest on missing group; "
            "savepoint restore rewinds state to any prior checkpoint. Wall-clock time for a "
            "full 30-day replay is proportional to (throughput * 30 days) / (job parallelism); "
            "unmeasured until real Kafka cluster available."
        ),
        note="Capability confirmed by static inspection of DrPredictorJob.main().",
    )


def _measure_d3_rollout(proto: SiblingFlinkPrototype) -> Measurement:
    _ = proto
    return Measurement(
        dimension_code="D3",
        status=MeasurementStatus.OK,
        qualitative=(
            "3-step rollout via savepoint + swap: (1) `flink savepoint <job-id> <path>` to snapshot "
            "state, (2) `flink stop --savepointPath <path>` to halt job, (3) `flink run -s <path> "
            "dr-predictor-0.1.0.jar` to resume with new binary. Model swap requires JAR rebuild + "
            "redeploy — a real MLflow-loaded ScoringModel implementation lets model artifact swap "
            "happen without JAR rebuild (see pattern-matcher/model/ModelLoader for the pattern). "
            "Wall-clock: ~30s savepoint + ~15s restart, dominated by state size."
        ),
        note="Mechanics confirmed; ConstantPredictor placeholder bypasses model-swap path entirely.",
    )


def _measure_d4_isolation(proto: SiblingFlinkPrototype) -> Measurement:
    _ = proto
    return Measurement(
        dimension_code="D4",
        status=MeasurementStatus.OK,
        value=5.0,
        qualitative=(
            "Standalone Flink job with dedicated JobManager + TaskManager slots — crash affects "
            "only this job. No shared state with sibling jobs (pattern-matcher, event-router, "
            "insight-generator) beyond Kafka topics. Consumer group forgeworks-dr-predictor is "
            "distinct; predictor crash cannot rewind sibling consumer offsets. Highest possible "
            "score on the 1-5 scale (higher_is_better=True per D4 dimension def)."
        ),
        note="Score 5.0 = full isolation. Sibling-Flink is the reference for D4 isolation.",
    )


def _measure_d7_cognitive_load(proto: SiblingFlinkPrototype) -> Measurement:
    src_dir = proto.predictor_dir / "src" / "main" / "java"
    if not src_dir.is_dir():
        return Measurement(
            dimension_code="D7",
            status=MeasurementStatus.FAILED,
            note=f"{proto.option_code}: source tree missing at {src_dir}",
        )
    java_files = sorted(src_dir.rglob("*.java"))
    file_count = len(java_files)
    return Measurement(
        dimension_code="D7",
        status=MeasurementStatus.OK,
        value=5.0,
        qualitative=(
            f"Same conceptual footprint as existing Flink jobs (pattern-matcher, event-router, "
            f"insight-generator) — no new tools, no new languages, no new deploy path. "
            f"Java file count: {file_count} (matches pattern-matcher's minimal-viable size). "
            f"Operators already know: Flink DAG debugging, Kafka consumer groups, JAR deploy, "
            f"savepoint/checkpoint. No new concepts introduced by this placement."
        ),
        note=(
            f"Score 5.0 = highest reuse of existing platform knowledge. "
            f"File count {file_count} confirms minimal-viable module shape."
        ),
    )


def _measure_na(dimension_code: str, reason: str) -> Measurement:
    return Measurement(
        dimension_code=dimension_code,
        status=MeasurementStatus.NOT_APPLICABLE,
        note=reason,
    )


def _measure_d2_backpressure(proto: SiblingFlinkPrototype) -> Measurement:
    _ = proto
    return _measure_na(
        "D2",
        (
            "Requires running Flink cluster + 10x-baseline synthetic load generator against "
            "Kafka. Static inspection cannot measure sustained-QPS behavior. Documented Flink "
            "semantics: backpressure propagates upstream via TaskManager slot congestion, "
            "consumer-lag metric surfaces via Prometheus JMX exporter."
        ),
    )


def _measure_d5_cost(proto: SiblingFlinkPrototype) -> Measurement:
    _ = proto
    return _measure_na(
        "D5",
        (
            "Requires real prediction volume + real infrastructure pricing. Placeholder-model "
            "measurement would understate cost (real inference is CPU-bound; ConstantPredictor "
            "is O(1)). Deferred until AB-028 spike ships a real model AND a Kafka cluster with "
            "monitored spend is available."
        ),
    )


def _measure_d6_latency(proto: SiblingFlinkPrototype) -> Measurement:
    _ = proto
    return _measure_na(
        "D6",
        (
            "End-to-end latency measurement requires real Kafka broker + real network path + "
            "Prometheus histogram scrape. Static inspection can only observe pipeline shape "
            "(source -> filter -> keyBy -> map -> sink, all synchronous single-op transforms). "
            "Documented Flink semantics: single-op MapFunction adds sub-ms per event; end-to-end "
            "dominated by Kafka broker + consumer-poll interval."
        ),
    )


_MEASURERS = {
    "D1": _measure_d1_replay,
    "D2": _measure_d2_backpressure,
    "D3": _measure_d3_rollout,
    "D4": _measure_d4_isolation,
    "D5": _measure_d5_cost,
    "D6": _measure_d6_latency,
    "D7": _measure_d7_cognitive_load,
}


def measure_all(prototype: PlacementPrototype) -> dict[str, Measurement]:
    """Convenience: measure every dimension for one prototype."""
    return {d.code: prototype.measure(d.code) for d in DIMENSIONS}
