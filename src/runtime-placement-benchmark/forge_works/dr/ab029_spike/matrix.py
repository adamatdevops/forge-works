"""Comparison-matrix data model + JSON/markdown report generators (RFC §6.1 + §7)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from forge_works.dr.ab029_spike.dimensions import (
    DIMENSIONS,
    MeasurementStatus,
    dimension_by_code,
)
from forge_works.dr.ab029_spike.rubric import (
    WeightedScoreRubric,
    check_disqualification,
    weighted_score,
    within_fallback_range,
)

if TYPE_CHECKING:
    from forge_works.dr.ab029_spike.dimensions import Measurement
    from forge_works.dr.ab029_spike.rubric import DisqualificationResult


@dataclass(frozen=True)
class OptionResult:
    """Per-option row in the comparison matrix."""

    option_code: str
    option_name: str
    measurements: dict[str, Measurement]
    scores: dict[str, int]
    weighted_score: int
    disqualification: DisqualificationResult
    contract_implications: list[str]
    rationale_per_dimension: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparisonMatrix:
    """6-option x 8-dimension matrix + per-option weighted totals."""

    generated_at: str
    rubric: WeightedScoreRubric
    options: list[OptionResult]

    def qualified_options(self) -> list[OptionResult]:
        return [o for o in self.options if not o.disqualification.disqualified]

    def ranked(self) -> list[OptionResult]:
        return sorted(self.qualified_options(), key=lambda o: o.weighted_score, reverse=True)


@dataclass(frozen=True)
class PlacementDecision:
    """Final recommendation drawn from the matrix (RFC §6.2 primary + fallback rule)."""

    primary: OptionResult | None
    fallback: OptionResult | None
    all_options_disqualified: bool
    matrix: ComparisonMatrix
    notes: list[str] = field(default_factory=list)

    @property
    def has_primary(self) -> bool:
        return self.primary is not None


def build_placement_decision(matrix: ComparisonMatrix) -> PlacementDecision:
    ranked = matrix.ranked()
    if not ranked:
        return PlacementDecision(
            primary=None,
            fallback=None,
            all_options_disqualified=True,
            matrix=matrix,
            notes=[
                "All 6 options disqualified per RFC §6.3 — recommendation is to spike a 7th option (RFC §8 R5)."
            ],
        )
    primary = ranked[0]
    fallback = None
    if len(ranked) >= 2 and within_fallback_range(primary.weighted_score, ranked[1].weighted_score):
        fallback = ranked[1]
    return PlacementDecision(
        primary=primary,
        fallback=fallback,
        all_options_disqualified=False,
        matrix=matrix,
    )


def to_json(matrix: ComparisonMatrix, decision: PlacementDecision | None = None) -> str:
    payload = {
        "generated_at": matrix.generated_at,
        "rubric": _jsonify(matrix.rubric),
        "options": [_jsonify(opt) for opt in matrix.options],
    }
    if decision is not None:
        payload["decision"] = {
            "primary": decision.primary.option_code if decision.primary else None,
            "fallback": decision.fallback.option_code if decision.fallback else None,
            "all_options_disqualified": decision.all_options_disqualified,
            "notes": list(decision.notes),
        }
    return json.dumps(payload, indent=2, default=str)


def to_markdown(matrix: ComparisonMatrix, decision: PlacementDecision | None = None) -> str:
    lines: list[str] = []
    lines.extend(_header(matrix))
    lines.extend(_rubric_table(matrix))
    lines.extend(_measurements_table(matrix))
    lines.extend(_scores_table(matrix))
    lines.extend(_disqualification_section(matrix))
    if decision is not None:
        lines.extend(_decision_section(decision))
    lines.extend(_footer())
    return "\n".join(lines) + "\n"


def _header(matrix: ComparisonMatrix) -> list[str]:
    return [
        "# AB-029 Runtime Placement Comparison Matrix",
        "",
        f"_Generated: {matrix.generated_at}_",
        "",
        "> 6 options x 8 dimensions per RFC §4-§6. Cells reporting `NOT_IMPLEMENTED` come "
        "from stub prototypes — real prototypes replace them via `PlacementPrototype`.",
        "",
    ]


def _rubric_table(matrix: ComparisonMatrix) -> list[str]:
    lines = ["## Weights (RFC §6.2)", "", "| Dimension | Weight |", "|---|---|"]
    lines.extend(f"| {code} | {weight} |" for code, weight in matrix.rubric.weights.items())
    lines.append("")
    return lines


def _measurements_table(matrix: ComparisonMatrix) -> list[str]:
    lines = ["## Measurements", "", "| Option | " + " | ".join(d.code for d in DIMENSIONS) + " |"]
    lines.append("|---" + "|---" * len(DIMENSIONS) + "|")
    for opt in matrix.options:
        cells = [f"**{opt.option_code} {opt.option_name}**"]
        for d in DIMENSIONS:
            m = opt.measurements.get(d.code)
            cells.append(_format_measurement(m))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _format_measurement(m: Measurement | None) -> str:
    if m is None:
        return "_—_"
    if m.status is MeasurementStatus.NOT_IMPLEMENTED:
        return "_(pending)_"
    if m.status is MeasurementStatus.NOT_APPLICABLE:
        return "_n/a_"
    if m.status is MeasurementStatus.FAILED:
        return f"**FAIL** ({m.note})"
    if m.value is not None:
        return f"{m.value}"
    return m.qualitative or "_(no data)_"


def _scores_table(matrix: ComparisonMatrix) -> list[str]:
    lines = [
        "## Scores + weighted totals",
        "",
        "| Option | " + " | ".join(d.code for d in DIMENSIONS) + " | Weighted total |",
        "|---" + "|---" * len(DIMENSIONS) + "|---|",
    ]
    for opt in matrix.options:
        cells = [f"**{opt.option_code}**"]
        for d in DIMENSIONS:
            s = opt.scores.get(d.code)
            cells.append(str(s) if s is not None else "_—_")
        cells.append(f"**{opt.weighted_score}**")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _disqualification_section(matrix: ComparisonMatrix) -> list[str]:
    lines = ["## Disqualification (RFC §6.3)", ""]
    any_dq = False
    for opt in matrix.options:
        if opt.disqualification.disqualified:
            any_dq = True
            lines.append(f"- **{opt.option_code} {opt.option_name}** — DISQUALIFIED")
            lines.extend(f"  - {r}" for r in opt.disqualification.reasons)
    if not any_dq:
        lines.append("_No options disqualified._")
    lines.append("")
    return lines


def _decision_section(decision: PlacementDecision) -> list[str]:
    lines = ["## Recommendation (RFC §6.2)", ""]
    if decision.all_options_disqualified:
        lines.append("**NONE** — all 6 options disqualified. RFC §8 R5: spike a 7th option.")
    elif decision.primary is not None:
        lines.append(
            f"**Primary:** {decision.primary.option_code} {decision.primary.option_name} "
            f"(weighted score {decision.primary.weighted_score})"
        )
        if decision.fallback is not None:
            lines.append(
                f"**Fallback:** {decision.fallback.option_code} {decision.fallback.option_name} "
                f"(weighted score {decision.fallback.weighted_score}; within 10% of primary)"
            )
        else:
            lines.append("**Fallback:** none within 10% of primary — primary stands alone.")
    lines.extend(f"- {n}" for n in decision.notes)
    lines.append("")
    return lines


def _footer() -> list[str]:
    return [
        "---",
        "",
        f"_Report generated at {datetime.now().astimezone().isoformat()}_",
        "",
    ]


def _jsonify(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonify(asdict(value))
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonify(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_matrix(
    options: list[OptionResult],
    *,
    rubric: WeightedScoreRubric | None = None,
    generated_at: str | None = None,
) -> ComparisonMatrix:
    return ComparisonMatrix(
        generated_at=generated_at or datetime.now().astimezone().isoformat(),
        rubric=rubric or WeightedScoreRubric(),
        options=list(options),
    )


def build_option_result(
    *,
    option_code: str,
    option_name: str,
    measurements: dict[str, Measurement],
    scores: dict[str, int],
    contract_implications: list[str] | None = None,
    contract_breaking_flags: list[str] | None = None,
    rubric: WeightedScoreRubric | None = None,
    rationale_per_dimension: dict[str, str] | None = None,
) -> OptionResult:
    rubric = rubric or WeightedScoreRubric()
    dq = check_disqualification(
        option_code, scores, contract_breaking_flags=contract_breaking_flags, rubric=rubric
    )
    total = weighted_score(scores, rubric)
    _ = dimension_by_code  # keep import used for consumers
    return OptionResult(
        option_code=option_code,
        option_name=option_name,
        measurements=dict(measurements),
        scores=dict(scores),
        weighted_score=total,
        disqualification=dq,
        contract_implications=list(contract_implications or []),
        rationale_per_dimension=dict(rationale_per_dimension or {}),
    )
