"""Report formatters for the AB-028 metadata pass.

Produces a markdown pre-read the scoping-approval meeting can attach to its agenda,
and a JSON dump for machine consumption / provenance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forge_works.dr.ab028_spike.metadata_window import MetadataPass, MetadataPassConfig


def to_json(pass_result: MetadataPass, config: MetadataPassConfig) -> str:
    pass_payload = _jsonify(pass_result)
    if isinstance(pass_payload, dict):
        pass_payload["ready_for_scoping_approval"] = pass_result.ready_for_scoping_approval
        proj = pass_payload.get("projected_modeling_window")
        if isinstance(proj, dict):
            proj["all_floors_met"] = pass_result.projected_modeling_window.all_floors_met
    payload = {
        "metadata_pass": pass_payload,
        "config": _jsonify(config),
    }
    return json.dumps(payload, indent=2, default=str)


def to_markdown(pass_result: MetadataPass, config: MetadataPassConfig) -> str:
    return "\n".join(_render_markdown(pass_result, config)) + "\n"


def _render_markdown(pass_result: MetadataPass, config: MetadataPassConfig) -> list[str]:
    lines: list[str] = []
    lines.extend(_header_lines(pass_result))
    lines.extend(_volume_lines(pass_result))
    lines.extend(_base_rate_lines(pass_result, config))
    lines.extend(_projection_lines(pass_result, config))
    lines.extend(_warnings_lines(pass_result))
    lines.extend(_readiness_lines(pass_result))
    lines.append("")
    lines.append(
        f"_Report generated at {datetime.now().astimezone().isoformat()}_ "
        "(computed against metadata window only; modeling window not accessed)."
    )
    lines.append("")
    return lines


def _header_lines(pass_result: MetadataPass) -> list[str]:
    return [
        "# AB-028 Pre-Scoping Metadata Window Pass",
        "",
        f"**Window:** {pass_result.metadata_window_start.isoformat()} "
        f"→ {pass_result.metadata_window_end.isoformat()} "
        f"({pass_result.metadata_days} days)",
        "",
        "> Aggregate counts only. No feature values inspected. No label values inspected. "
        "The modeling window is untouched per RFC §4.4.",
        "",
    ]


def _volume_lines(pass_result: MetadataPass) -> list[str]:
    return [
        "## Volume + rates",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Deploys | {pass_result.deploys} |",
        f"| Deploys per day | {pass_result.deploys_per_day:.2f} |",
        f"| SLO breaches | {pass_result.slo_breaches} |",
        f"| Base rate | {pass_result.base_rate:.4f} |",
        f"| Censoring rate | {pass_result.censoring_rate:.4f} |",
        f"| Missing-data rate | {pass_result.missing_data_rate:.4f} |",
        f"| Eligibility rate | {pass_result.eligibility_rate:.4f} |",
        f"| Apply failures | {pass_result.apply_failures} |",
        f"| Incidents | {pass_result.incidents} |",
        f"| Monitor muted events | {pass_result.monitor_muted_events} |",
        "",
    ]


def _base_rate_lines(pass_result: MetadataPass, config: MetadataPassConfig) -> list[str]:
    status = "PASS" if pass_result.base_rate_in_bounds else "FAIL"
    return [
        "## Base-rate check (§4.4)",
        "",
        f"Base rate {pass_result.base_rate:.4f} vs. acceptable window "
        f"[{config.base_rate_lower}, {config.base_rate_upper}] — **{status}**.",
        "",
    ]


def _projection_lines(pass_result: MetadataPass, config: MetadataPassConfig) -> list[str]:
    proj = pass_result.projected_modeling_window
    return [
        "## Prospective power projection",
        "",
        f"Extrapolated to a {proj.modeling_days}-day modeling window at the current "
        "deploy rate + base rate + eligibility rate:",
        "",
        "| Split | Projected positives | Floor | Met? |",
        "|---|---|---|---|",
        f"| Train ({config.train_fraction:.0%}) | {proj.projected_train_positives} "
        f"| {config.train_positive_floor} | {'✔' if proj.train_floor_met else '✘'} |",
        f"| Validation ({config.val_fraction:.0%}) | {proj.projected_val_positives} "
        f"| {config.val_positive_floor} | {'✔' if proj.val_floor_met else '✘'} |",
        f"| Test ({config.test_fraction:.0%}) | {proj.projected_test_positives} "
        f"| {config.test_positive_floor} | {'✔' if proj.test_floor_met else '✘'} |",
        "",
        f"Projected total: {proj.projected_deploys} deploys → "
        f"{proj.projected_eligible} eligible → {proj.projected_positives} positives.",
        "",
    ]


def _warnings_lines(pass_result: MetadataPass) -> list[str]:
    lines: list[str] = ["## Warnings", ""]
    if pass_result.warnings:
        lines.extend(f"- {w}" for w in pass_result.warnings)
    else:
        lines.append("_None._")
    lines.append("")
    return lines


def _readiness_lines(pass_result: MetadataPass) -> list[str]:
    if pass_result.ready_for_scoping_approval:
        body = (
            "**READY** — base rate in bounds, projected per-split floors met, no warnings. "
            "Scoping-approval meeting may lock thresholds per RFC §B without further data-side blockers."
        )
    else:
        body = (
            "**NOT READY** — resolve the warnings above before the scoping-approval meeting can lock §B1-§B3. "
            "Escalation options per RFC §4.4: extend modeling window, reconsider slice, or file AB-NNN for a "
            "longer-history variant."
        )
    return ["## Scoping-approval readiness", "", body]


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
