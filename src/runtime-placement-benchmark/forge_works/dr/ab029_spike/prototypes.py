"""Placement prototype Protocol + stub implementations for all 6 RFC §3 options.

Each stub reports what its measurement WOULD produce (via `describe_capability`) but
returns `MeasurementStatus.NOT_IMPLEMENTED` for actual measurements. Real prototypes
swap in by implementing `PlacementPrototype` and overriding `measure(dimension)`.

Option A has a real-scaffold prototype at `SiblingFlinkPrototype`. Per RFC v0.2 §8 R1,
all Option A scores are FROZEN pending B-F effort parity OR a blinded reviewer. The
v0.1 static D4=5 / D7=5 assignments have been REMOVED in favor of `FROZEN` status.

v0.2 changes (Codex round-1 loop on this prototype code, 2026-08-03):

- **Registry aligned with RFC v0.2 §3.6** — added `StandalonePythonKafkaConsumerStub`
  (Option F). Registry count 5 → 6.
- **Scoring freeze per RFC v0.2 §8 R1 honored in code** — `SiblingFlinkPrototype`
  D4/D7 measurers return `FROZEN` (no value) instead of the v0.1 static 5.0.
- **D8 measurer added** — RFC v0.2 §4 added D8 (evidence integrity + operability).
  Handler returns `NOT_APPLICABLE` with dual-reason note (D8 sub-checks require MLflow
  audit sink + PC §5 lifecycle events + retry-idempotency tests that Option A prototype
  does NOT yet implement; even without §8 R1 freeze, D8 would not be measurable).
- **D1 / D3 measurers de-laundered** — v0.1 returned `OK` with qualitative descriptions
  of capability while admitting numeric measurement was absent. v0.2 returns
  `NOT_MEASURED` (RFC v0.2 §6.2.1 requires absolute anchors; unmeasured ≠ passed).
- **Gate-evaluation surface added** — `evaluate_gates()` returns per-gate G1-G10 status
  per RFC v0.2 §6.3. For scaffold-state Option A, every gate is `NOT_EVALUATED` with
  evidence pointer "requires RFC §5.1 model bundle lock + real implementation pass."

**Deferred to post-scoping-approval real-impl PR** (per reconciled loop artifact):
governance envelope propagation (H4), structured slice per PC §3.5 (H5), deterministic
prediction identity (H10), Kafka exactly-once (H11), PC §5 lifecycle events (H12),
MLflow audit sink (H13), real AB-028 §4.3 feature extraction (H16), DLQ (M20),
comprehensive Java test suite (M21 remainder). Each requires either the RFC §5.1
model-bundle lock or systemic Flink pipeline work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from forge_works.dr.ab029_spike.dimensions import DIMENSIONS, Measurement, MeasurementStatus

_UNIMPLEMENTED_NOTE = "stub prototype — real prototype must override measure()"


class GateStatus(str, Enum):
    """Per-gate evaluation status for RFC v0.2 §6.3 G1-G10.

    v0.2 addition (Codex round-1 loop, 2026-08-03) per H17 gate-evaluation surface.
    """

    PASS = "pass"  # noqa: S105  # not a password — RFC gate status enum value
    FAIL = "fail"
    CONDITIONAL = "conditional"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class GateResult:
    """One G1-G10 gate result."""

    gate_code: str  # e.g. "G1", "G8"
    status: GateStatus
    evidence: str


RFC_GATES: tuple[str, ...] = (
    "G1",  # score ≥ 3 on all weight-4 dimensions (D3, D4, D8)
    "G2",  # no breaking changes to PC §3 estimand semantics or GT §2.1 required fields
    "G3",  # T1/T2-only authority
    "G4",  # full PC §3 emission conformance
    "G5",  # governance envelope enforcement
    "G6",  # model-artifact immutability
    "G7",  # audit + lifecycle event delivery
    "G8",  # label-join viability
    "G9",  # abstention / fallback path exists
    "G10",  # MLflow-dependent options block on AB-032 verdict
)


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
    name: str = "Batch materialized-view (Airflow + Postgres)"
    description: str = (
        "Airflow scheduled DAG + in-cluster Postgres materialized view + lightweight Kafka "
        "change-notification topic. DAG runs every 60s (configurable); scores in Python; "
        "upserts predictions to Postgres. Pinned architecture per RFC v0.2 §3.4."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Freshness semantics covered by existing PC §3.3 fields; no new field required.",
        "SC §5 requires source-access-pattern annotation for batch reader.",
    )


@dataclass(frozen=True)
class DedicatedInferenceStub(_StubBase):
    """Option E — dedicated KServe inference service."""

    option_code: str = "E"
    name: str = "Dedicated inference service (KServe)"
    description: str = (
        "KServe InferenceService in the existing forge-works cluster, backed by sklearn-runtime "
        "pod pulling models from MLflow. Thin Flink job calls the endpoint via gRPC. Pinned "
        "architecture per RFC v0.2 §3.5. Blocks on AB-032 verdict per §6.3 G10."
    )
    contract_implication_notes: tuple[str, ...] = (
        "New service to run, monitor, on-call.",
        "Cross-service latency (Flink <-> KServe) is a new failure mode.",
        "AB-032 MLflow registry-governance verdict is a hard prerequisite.",
    )


@dataclass(frozen=True)
class StandalonePythonKafkaConsumerStub(_StubBase):
    """Option F — standalone Python Kafka consumer service (v0.2 addition per RFC §3.6)."""

    option_code: str = "F"
    name: str = "Standalone Python Kafka consumer"
    description: str = (
        "Python aiokafka consumer service deployed as a Kubernetes Deployment (3 replicas, "
        "consumer-group parallelism); reads forge.events.normalized.v1; scores in Python "
        "(sklearn / XGBoost); publishes predictions; state (windowed features) held in Redis; "
        "consumer-lag-driven autoscaling via keda. Pinned architecture per RFC v0.2 §3.6."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Consumer-group management, backpressure, state, exactly-once are all manual (no Flink primitives).",
        "Redis-for-state adds an operational surface.",
        "AB-032 MLflow verdict is a hard prerequisite if MLflow-loaded model is used.",
    )


ALL_STUB_PROTOTYPES: tuple[_StubBase, ...] = (
    SiblingFlinkStub(),
    PatternMatcherExtensionStub(),
    InsightGeneratorExtensionStub(),
    BatchMaterializedStub(),
    DedicatedInferenceStub(),
    StandalonePythonKafkaConsumerStub(),
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
    """Option A — real-scaffold prototype backed by `src/flink-jobs/dr-predictor/`.

    v0.2 (Codex round-1 loop, 2026-08-03): reframed from "real prototype" to
    "real-scaffold prototype." The Java module exists and the pipeline shape is
    production-ready, but per Codex Loop #4 findings (H1, H4, H5, H7, H10, H11, H12,
    H13, H16) the module does NOT yet satisfy RFC v0.2 §6.3 G1-G10 hard gates. Real
    measurement requires: RFC §5.1 model-bundle lock; AB-032 MLflow verdict; full PC §3
    field completeness; governance propagation; deterministic identity; PC §5 lifecycle;
    exactly-once Kafka; real feature extraction; MLflow audit sink. All deferred to a
    post-scoping-approval real-implementation PR.

    Per RFC v0.2 §8 R1: ALL measurements FROZEN pending B-F effort parity or blinded
    reviewer. D4 and D7 no longer emit static values.
    """

    option_code: str = "A"
    name: str = "Sibling Flink job (real scaffold — pre-freeze)"
    description: str = (
        "Real Flink module scaffold at src/flink-jobs/dr-predictor/ — placeholder "
        "ConstantPredictor model until AB-028 ships. Pipeline shape is production-ready but "
        "PC §3 field completeness, governance propagation, PC §5 lifecycle events, MLflow "
        "audit sink, and real feature extraction are deferred to real-implementation PR "
        "post RFC §5.1 gate resolution."
    )
    contract_implication_notes: tuple[str, ...] = (
        "Emits to forge.predictions.dynamic_reliability.v1 — new Kafka topic (needs provisioning).",
        "Placeholder ConstantPredictor scoring — real model requires AB-028 spike + AB-032 MLflow.",
        "Estimand_id fixed to deploy_slo_breach_60m_association_v0 in envelope factory methods.",
        "PC §3 field completeness DEFERRED to real-impl PR (Codex Loop #4 H1/H5).",
        "Governance envelope propagation DEFERRED (Codex Loop #4 H4).",
        "PC §5 lifecycle events NOT YET IMPLEMENTED (Codex Loop #4 H12).",
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
    """D1 historical reproducibility — v0.2: NOT_MEASURED per RFC §6.2.1 (was OK-with-caveats)."""
    if not (proto.predictor_dir / "pom.xml").is_file():
        return Measurement(
            dimension_code="D1",
            status=MeasurementStatus.FAILED,
            note=f"{proto.option_code}: predictor module missing at {proto.predictor_dir}",
        )
    return Measurement(
        dimension_code="D1",
        status=MeasurementStatus.NOT_MEASURED,
        qualitative=(
            "Capability documented: Flink-native replay via Kafka consumer OffsetsInitializer + "
            "savepoint restore. Wall-clock for a full 30-day replay would be proportional to "
            "(throughput * 30 days) / (job parallelism). Byte-identical correctness on ≥99.9% of "
            "events (RFC §6.2.1 anchor for score 3) is UNMEASURED — requires real Kafka cluster + "
            "instrumented replay run. v0.1 returned OK with qualitative only; v0.2 correctly "
            "returns NOT_MEASURED per RFC §6.2.1 (missing data ≠ successful measurement)."
        ),
        note="Capability confirmed by static inspection; measurement pending real infra.",
    )


def _measure_d3_rollout(proto: SiblingFlinkPrototype) -> Measurement:
    """D3 model rollout — v0.2: NOT_MEASURED (was OK-with-invented-numbers)."""
    _ = proto
    return Measurement(
        dimension_code="D3",
        status=MeasurementStatus.NOT_MEASURED,
        qualitative=(
            "Capability documented: 3-step rollout via savepoint + JAR swap: "
            "(1) `flink savepoint <job-id> <path>`, (2) `flink stop --savepointPath <path>`, "
            "(3) `flink run -s <path> dr-predictor-<version>.jar`. Model swap requires JAR rebuild "
            "unless a real MLflow-loaded ScoringModel is added (pattern from pattern-matcher/model/"
            "ModelLoader). Wall-clock not measured. v0.1's `~30s savepoint + ~15s restart` numbers "
            "were reviewer-invented, not observed; v0.2 correctly withholds numeric values."
        ),
        note="Mechanics documented; wall-clock measurement pending real cluster run.",
    )


def _measure_d4_isolation(proto: SiblingFlinkPrototype) -> Measurement:
    """D4 failure isolation — v0.2: FROZEN per RFC §8 R1 (was static value=5.0)."""
    _ = proto
    return Measurement(
        dimension_code="D4",
        status=MeasurementStatus.FROZEN,
        qualitative=(
            "Capability: standalone Flink job with dedicated JobManager + TaskManager slots — "
            "crash affects only this job; consumer group forgeworks-dr-predictor is distinct "
            "from sibling jobs. v0.1 asserted D4=5.0 as the reference for full isolation. "
            "RFC v0.2 §6.2.1 anchor for score 5 requires 'automatic recovery <30s' — NEVER "
            "MEASURED. RFC v0.2 §8 R1 also freezes all Option A scoring pending B-F effort "
            "parity or blinded reviewer. v0.2 correctly returns FROZEN with no value."
        ),
        note=(
            "Score 5.0 v0.1 assertion RESCINDED — recovery time not measured (RFC §6.2.1 "
            "anchor mismatch); scoring frozen (RFC §8 R1)."
        ),
    )


def _measure_d7_cognitive_load(proto: SiblingFlinkPrototype) -> Measurement:
    """D7 cognitive load — v0.2: FROZEN per RFC §8 R1 (was static value=5.0 justified by file count)."""
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
        status=MeasurementStatus.FROZEN,
        qualitative=(
            f"Capability: same conceptual footprint as existing Flink jobs (pattern-matcher, "
            f"event-router, insight-generator). Java file count: {file_count}. v0.1 asserted "
            f"D7=5.0 with rationale 'file count matches pattern-matcher's minimal-viable size.' "
            f"RFC v0.2 §6.2.1 anchor for score 5 requires '0 new concepts; all patterns exist "
            f"in current stack' — but Option A's real-impl PR (see contract_implications) will "
            f"introduce PC §5 lifecycle events, MLflow audit sink, governance propagation — "
            f"NEW patterns not yet in the current stack. File count is not proof of pattern "
            f"reuse. RFC §8 R1 also freezes scoring. v0.2 correctly returns FROZEN."
        ),
        note=(
            "Score 5.0 v0.1 assertion RESCINDED — file count ≠ concept-reuse evidence; "
            "real-impl PR will introduce new concepts (lifecycle, audit-sink, governance)."
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


def _measure_d8_evidence_integrity(proto: SiblingFlinkPrototype) -> Measurement:
    """D8 evidence integrity + operability — v0.2 NEW dimension per RFC §4."""
    _ = proto
    return _measure_na(
        "D8",
        (
            "D8 has TWO independent reasons it cannot score right now for Option A: "
            "(1) methodology gap — D8's 7 sub-checks (replay determinism, prediction identity "
            "stability under retry, full PC §3 emission conformance, PC §5 lifecycle event "
            "delivery, GT §7 label-join viability, audit-sink completeness, operability drills) "
            "each require infrastructure Option A does NOT yet have: MLflow audit sink (Codex "
            "Loop #4 H13), PC §5 lifecycle events (H12), Kafka exactly-once (H11), deterministic "
            "prediction identity (H10). (2) process gate — RFC v0.2 §8 R1 also freezes all "
            "Option A scoring. When BOTH reasons close (real-impl PR lands AND freeze lifts), "
            "D8 can be measured. Not currently applicable."
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
    "D8": _measure_d8_evidence_integrity,
}


def measure_all(prototype: PlacementPrototype) -> dict[str, Measurement]:
    """Convenience: measure every dimension for one prototype."""
    return {d.code: prototype.measure(d.code) for d in DIMENSIONS}


def evaluate_gates(prototype: PlacementPrototype) -> dict[str, GateResult]:
    """Return per-gate G1-G10 status for a prototype per RFC v0.2 §6.3.

    v0.2 addition (Codex round-1 loop, 2026-08-03) per H17. Real evaluation logic
    requires each gate's testing methodology to be implemented; for scaffold-state
    Option A + stub Options B-F, every gate is NOT_EVALUATED. Gate evaluation lands
    alongside the real-implementation PR that closes Codex Loop #4 deferred findings.
    """
    reason = (
        f"Option {prototype.option_code}: gate evaluation not yet implemented. Requires RFC "
        "§5.1 model bundle lock + real-implementation PR (Codex Loop #4 deferred H1/H4/H5/H7/"
        "H10/H11/H12/H13). For pure-stub options (B-F currently) no prototype code exists to "
        "evaluate. Contract surface exists here so future work can populate."
    )
    return {
        gate: GateResult(gate_code=gate, status=GateStatus.NOT_EVALUATED, evidence=reason)
        for gate in RFC_GATES
    }
