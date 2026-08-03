"""Benchmark runner — orchestrates measurement collection across prototypes.

Given a list of `PlacementPrototype`s + optional per-option scoring input (from the
scoping-approval meeting or from live measurements), produces a `ComparisonMatrix`
+ `PlacementDecision`.

For stubs (all measurements NOT_IMPLEMENTED), scoring input is required — the meeting
scores from qualitative RFC §3 analysis. When real prototypes exist, scoring can be
derived from measurements via `score_from_measurements()` (out of scope for v0.1 —
consumers can plug in their own scoring function).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from forge_works.dr.ab029_spike.dimensions import DIMENSIONS
from forge_works.dr.ab029_spike.matrix import (
    build_matrix,
    build_option_result,
    build_placement_decision,
)
from forge_works.dr.ab029_spike.prototypes import ALL_STUB_PROTOTYPES, measure_all
from forge_works.dr.ab029_spike.rubric import WeightedScoreRubric

if TYPE_CHECKING:
    from forge_works.dr.ab029_spike.dimensions import Measurement
    from forge_works.dr.ab029_spike.matrix import ComparisonMatrix, PlacementDecision
    from forge_works.dr.ab029_spike.prototypes import PlacementPrototype


@dataclass(frozen=True)
class OptionInput:
    """Per-option scoring input for the runner. Scores come from the meeting or measurements."""

    option_code: str
    scores: dict[str, int]
    contract_breaking_flags: list[str] = field(default_factory=list)
    rationale_per_dimension: dict[str, str] = field(default_factory=dict)


@dataclass
class BenchmarkRunner:
    """Wires prototypes → measurements → scored options → matrix + decision."""

    prototypes: list[PlacementPrototype] = field(default_factory=lambda: list(ALL_STUB_PROTOTYPES))
    rubric: WeightedScoreRubric = field(default_factory=WeightedScoreRubric)

    def collect_measurements(self) -> dict[str, dict[str, Measurement]]:
        return {p.option_code: measure_all(p) for p in self.prototypes}

    def run(self, inputs: list[OptionInput]) -> tuple[ComparisonMatrix, PlacementDecision]:
        by_code = {i.option_code: i for i in inputs}
        missing_inputs = [p.option_code for p in self.prototypes if p.option_code not in by_code]
        if missing_inputs:
            msg = f"missing OptionInput for prototypes: {sorted(missing_inputs)}"
            raise ValueError(msg)

        options = []
        measurements = self.collect_measurements()
        for proto in self.prototypes:
            inp = by_code[proto.option_code]
            options.append(
                build_option_result(
                    option_code=proto.option_code,
                    option_name=proto.name,
                    measurements=measurements[proto.option_code],
                    scores=inp.scores,
                    contract_implications=proto.contract_implications(),
                    contract_breaking_flags=inp.contract_breaking_flags,
                    rubric=self.rubric,
                    rationale_per_dimension=inp.rationale_per_dimension,
                )
            )

        matrix = build_matrix(options, rubric=self.rubric)
        decision = build_placement_decision(matrix)
        return matrix, decision


def scoping_approval_placeholder_inputs() -> list[OptionInput]:
    """Placeholder scores for the 6 stub prototypes.

    Meant as an executable starting point for the scoping-approval meeting — the meeting
    replaces these with real per-option per-dimension scores after inspecting RFC §3
    analysis + any measured evidence.

    v0.2 (Codex Loop #4): added Option F (StandalonePythonKafkaConsumerStub) per RFC §3.6.
    Score dict includes D8 evidence-integrity + operability (also v0.2 addition).
    """
    neutral = {d.code: 3 for d in DIMENSIONS}
    return [
        OptionInput(option_code=code, scores=dict(neutral))
        for code in ("A", "B", "C", "D", "E", "F")
    ]
