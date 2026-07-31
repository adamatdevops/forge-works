"""AB-029 runtime placement benchmark framework.

Implements the scoring rubric + disqualification rules + comparison matrix per
`docs/decisions/dynamic-reliability/AB-029_RUNTIME_PLACEMENT_SPIKE.md`. Prototype
implementations are stubs — real prototypes swap in via the `PlacementPrototype`
Protocol as they get built.
"""

from forge_works.dr.ab029_spike.dimensions import (
    DEFAULT_WEIGHTS,
    DIMENSIONS,
    Dimension,
    Measurement,
    MeasurementStatus,
)
from forge_works.dr.ab029_spike.matrix import (
    ComparisonMatrix,
    PlacementDecision,
    to_json,
    to_markdown,
)
from forge_works.dr.ab029_spike.prototypes import (
    ALL_STUB_PROTOTYPES,
    BatchMaterializedStub,
    DedicatedInferenceStub,
    InsightGeneratorExtensionStub,
    PatternMatcherExtensionStub,
    PlacementPrototype,
    SiblingFlinkStub,
)
from forge_works.dr.ab029_spike.rubric import (
    DisqualificationResult,
    WeightedScoreRubric,
    check_disqualification,
    weighted_score,
)
from forge_works.dr.ab029_spike.runner import BenchmarkRunner

__all__ = [
    "ALL_STUB_PROTOTYPES",
    "DEFAULT_WEIGHTS",
    "DIMENSIONS",
    "BatchMaterializedStub",
    "BenchmarkRunner",
    "ComparisonMatrix",
    "DedicatedInferenceStub",
    "Dimension",
    "DisqualificationResult",
    "InsightGeneratorExtensionStub",
    "Measurement",
    "MeasurementStatus",
    "PatternMatcherExtensionStub",
    "PlacementDecision",
    "PlacementPrototype",
    "SiblingFlinkStub",
    "WeightedScoreRubric",
    "check_disqualification",
    "to_json",
    "to_markdown",
    "weighted_score",
]
