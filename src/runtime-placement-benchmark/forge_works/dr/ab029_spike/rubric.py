"""Scoring rubric + disqualification rules (RFC §6.2 + §6.3).

Per-dimension score: 1 (worst) to 5 (best), relative to other options. Ties allowed.
Weighted score = Σ(dimension_score x dimension_weight). Recommendation = highest score;
fallback = second-highest if within 10% of top.

Disqualification (§6.3):
- Any dimension score = 1 with weight ≥ 3
- Contract implication would require breaking changes to PC §3 estimand semantics or GT §2.1
  required fields

Disqualification MUST be documented with the specific failing dimension. Silent drops
are forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from forge_works.dr.ab029_spike.dimensions import DEFAULT_WEIGHTS, DIMENSIONS

MIN_SCORE = 1
MAX_SCORE = 5
DISQUALIFY_WEIGHT_THRESHOLD = 3
FALLBACK_WITHIN_PERCENT = 10.0


@dataclass(frozen=True)
class WeightedScoreRubric:
    """Per-dimension weights + score bounds. Placeholders match RFC v0.1 §6.2."""

    weights: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    min_score: int = MIN_SCORE
    max_score: int = MAX_SCORE
    disqualify_weight_threshold: int = DISQUALIFY_WEIGHT_THRESHOLD

    def __post_init__(self) -> None:
        expected = {d.code for d in DIMENSIONS}
        missing = expected - self.weights.keys()
        extra = self.weights.keys() - expected
        if missing:
            msg = f"weights missing for dimensions: {sorted(missing)}"
            raise ValueError(msg)
        if extra:
            msg = f"unknown dimension codes in weights: {sorted(extra)}"
            raise ValueError(msg)


def weighted_score(scores: dict[str, int], rubric: WeightedScoreRubric | None = None) -> int:
    """Σ(score x weight) across all dimensions. Missing scores raise ValueError."""
    rubric = rubric or WeightedScoreRubric()
    missing = rubric.weights.keys() - scores.keys()
    if missing:
        msg = f"scores missing for dimensions: {sorted(missing)}"
        raise ValueError(msg)
    total = 0
    for code, weight in rubric.weights.items():
        s = scores[code]
        if not rubric.min_score <= s <= rubric.max_score:
            msg = f"score for {code} = {s} outside [{rubric.min_score}, {rubric.max_score}]"
            raise ValueError(msg)
        total += s * weight
    return total


@dataclass(frozen=True)
class DisqualificationResult:
    """Outcome of applying §6.3 disqualification rules to one option."""

    option_code: str
    disqualified: bool
    reasons: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.disqualified


def check_disqualification(
    option_code: str,
    scores: dict[str, int],
    *,
    contract_breaking_flags: list[str] | None = None,
    rubric: WeightedScoreRubric | None = None,
) -> DisqualificationResult:
    """Apply §6.3 rules. Returns disqualified + reasons if any."""
    rubric = rubric or WeightedScoreRubric()
    contract_breaking_flags = contract_breaking_flags or []
    reasons: list[str] = []
    for code, weight in rubric.weights.items():
        s = scores.get(code)
        if s is None:
            continue
        if s == rubric.min_score and weight >= rubric.disqualify_weight_threshold:
            reasons.append(
                f"dimension {code} scored {s} (worst) with weight {weight} "
                f">= disqualification threshold {rubric.disqualify_weight_threshold}"
            )
    reasons.extend(f"contract-breaking implication: {flag}" for flag in contract_breaking_flags)
    return DisqualificationResult(
        option_code=option_code,
        disqualified=bool(reasons),
        reasons=tuple(reasons),
    )


def within_fallback_range(
    top_score: int, candidate_score: int, *, percent: float = FALLBACK_WITHIN_PERCENT
) -> bool:
    """RFC §6.2: fallback = second-highest if within `percent`% of top score."""
    if top_score <= 0:
        return False
    return (top_score - candidate_score) / top_score <= percent / 100.0
