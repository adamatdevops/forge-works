"""AB-028 offline replay harness.

Implements the feasibility spike per docs/decisions/dynamic-reliability/AB-028_FEASIBILITY_SPIKE.md.
Ships with placeholder thresholds (§6) — real thresholds locked at scoping-approval and passed in
via the GateConfig object.
"""

from forge_works.dr.ab028_spike.evaluate import Verdict, run_spike
from forge_works.dr.ab028_spike.metrics import GateConfig, MetricReport

__all__ = ["GateConfig", "MetricReport", "Verdict", "run_spike"]
