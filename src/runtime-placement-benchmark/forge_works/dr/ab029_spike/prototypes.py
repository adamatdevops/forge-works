"""Placement prototype Protocol + stub implementations for all 5 RFC §3 options.

Each stub reports what its measurement WOULD produce (via `describe_capability`) but
returns `MeasurementStatus.NOT_IMPLEMENTED` for actual measurements. Real prototypes
swap in by implementing `PlacementPrototype` and overriding `measure(dimension)`.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def measure_all(prototype: PlacementPrototype) -> dict[str, Measurement]:
    """Convenience: measure every dimension for one prototype."""
    return {d.code: prototype.measure(d.code) for d in DIMENSIONS}
