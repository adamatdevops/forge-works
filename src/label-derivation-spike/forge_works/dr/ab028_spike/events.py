"""Synthetic event stream generator for the AB-028 offline replay harness.

Simulates 90 days of Terraform + DataDog history — 30d pre-scoping metadata window +
60d modeling window per RFC §4.1/§4.4. The event stream is deliberately correlated with
outcomes so baselines and the model have real signal to learn (otherwise the harness
would just measure noise floor).

All timestamps are timezone-aware UTC. Seeded RNG — the same seed always yields the
same event stream, which is what the tests rely on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

SERVICE = "webhook-gateway"
ENVIRONMENT = "prod"
DEPLOYS_PER_DAY_MEAN = 12
RESOURCE_TYPES = (
    "aws_lambda_function",
    "aws_api_gateway_route",
    "aws_iam_role",
    "aws_security_group",
    "aws_route53_record",
    "aws_dynamodb_table",
    "aws_s3_bucket",
    "aws_cloudwatch_metric_alarm",
)
SENSITIVE_RESOURCE_TYPES = frozenset({"aws_iam_role", "aws_security_group", "aws_route53_record"})
AUTHOR_ROLES = ("engineer", "senior_engineer", "sre", "engineer", "engineer")


@dataclass(frozen=True)
class DeployRecord:
    deploy_id: str
    commit_sha: str
    service: str
    environment: str
    deployed_at: datetime
    author_role: str
    plan_diff_size: int
    resource_count: int
    resource_types_touched: tuple[str, ...]
    apply_outcome: str


@dataclass(frozen=True)
class SLOBreach:
    slice_id: str
    event_time: datetime
    severity: str


@dataclass(frozen=True)
class ApplyFailure:
    slice_id: str
    event_time: datetime
    error_type: str


@dataclass(frozen=True)
class MonitorStateChange:
    slice_id: str
    event_time: datetime
    state: str


@dataclass(frozen=True)
class Incident:
    slice_id: str
    event_time: datetime


@dataclass
class SyntheticEventStream:
    start: datetime
    end: datetime
    deploys: list[DeployRecord] = field(default_factory=list)
    slo_breaches: list[SLOBreach] = field(default_factory=list)
    apply_failures: list[ApplyFailure] = field(default_factory=list)
    monitor_events: list[MonitorStateChange] = field(default_factory=list)
    incidents: list[Incident] = field(default_factory=list)

    def slice_id(self) -> str:
        return f"{SERVICE}.{ENVIRONMENT}"


def generate_stream(
    *,
    modeling_days: int = 60,
    metadata_days: int = 30,
    seed: int = 20260728,
    base_rate: float = 0.05,
    deploys_per_day: float = DEPLOYS_PER_DAY_MEAN,
) -> SyntheticEventStream:
    """Generate a 90-day event stream (30d metadata + 60d modeling by default).

    base_rate: unconditional breach probability. Realized rate will differ per-deploy
    because feature-conditional probabilities skew high or low.
    deploys_per_day: mean deploys/day. Lower values reduce the censoring rate — useful for
    tests that need eligibility floors to pass.
    """
    rng = random.Random(seed)  # noqa: S311 — deterministic test fixture, not crypto
    total_days = modeling_days + metadata_days
    start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=UTC)
    end = start + timedelta(days=total_days)
    stream = SyntheticEventStream(start=start, end=end)
    slice_id = stream.slice_id()

    _seed_baseline_monitor_state(stream, start)
    apply_failure_times = _generate_apply_failures(stream, rng, start, total_days, slice_id)
    incident_times = _generate_incidents(stream, rng, start, total_days, slice_id)

    deploy_times = _generate_deploy_times(rng, start, total_days, deploys_per_day=deploys_per_day)
    for i, deployed_at in enumerate(deploy_times):
        deploy = _make_deploy(rng, i, deployed_at)
        stream.deploys.append(deploy)

        breach_prob = _breach_probability(
            deploy=deploy,
            base_rate=base_rate,
            recent_apply_failures=_recent_events(apply_failure_times, deployed_at, hours=24),
            recent_incidents=_recent_events(incident_times, deployed_at, hours=6),
        )
        if rng.random() < breach_prob:
            breach_delay = timedelta(minutes=rng.randint(3, 55))
            severity = rng.choices(("warning", "major", "critical"), weights=(0.5, 0.35, 0.15))[0]
            stream.slo_breaches.append(
                SLOBreach(
                    slice_id=slice_id, event_time=deployed_at + breach_delay, severity=severity
                )
            )
            _emit_monitor_state_after_breach(stream, deployed_at + breach_delay, severity)

    stream.deploys.sort(key=lambda d: d.deployed_at)
    stream.slo_breaches.sort(key=lambda b: b.event_time)
    stream.apply_failures.sort(key=lambda a: a.event_time)
    stream.monitor_events.sort(key=lambda m: m.event_time)
    stream.incidents.sort(key=lambda inc: inc.event_time)
    return stream


def _seed_baseline_monitor_state(stream: SyntheticEventStream, start: datetime) -> None:
    stream.monitor_events.append(
        MonitorStateChange(slice_id=stream.slice_id(), event_time=start, state="ok")
    )


def _generate_apply_failures(
    stream: SyntheticEventStream,
    rng: random.Random,
    start: datetime,
    total_days: int,
    slice_id: str,
) -> list[datetime]:
    times: list[datetime] = []
    for day in range(total_days):
        n_failures = rng.choices((0, 1, 2), weights=(0.85, 0.13, 0.02))[0]
        for _ in range(n_failures):
            t = start + timedelta(days=day, seconds=rng.randint(0, 86_399))
            stream.apply_failures.append(
                ApplyFailure(slice_id=slice_id, event_time=t, error_type="plan_diff_conflict")
            )
            times.append(t)
    return sorted(times)


def _generate_incidents(
    stream: SyntheticEventStream,
    rng: random.Random,
    start: datetime,
    total_days: int,
    slice_id: str,
) -> list[datetime]:
    times: list[datetime] = []
    for day in range(total_days):
        if rng.random() < 0.08:
            t = start + timedelta(days=day, seconds=rng.randint(0, 86_399))
            stream.incidents.append(Incident(slice_id=slice_id, event_time=t))
            times.append(t)
    return sorted(times)


def _generate_deploy_times(
    rng: random.Random, start: datetime, total_days: int, *, deploys_per_day: float
) -> list[datetime]:
    """Poisson-shaped deploy schedule biased to daytime hours."""
    times: list[datetime] = []
    for day in range(total_days):
        n = max(1, round(rng.gauss(deploys_per_day, deploys_per_day * 0.4)))
        for _ in range(n):
            hour = rng.choices(range(24), weights=_hourly_weights())[0]
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            times.append(start + timedelta(days=day, hours=hour, minutes=minute, seconds=second))
    return sorted(times)


def _hourly_weights() -> tuple[int, ...]:
    return (1, 1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 10, 9, 10, 10, 9, 8, 6, 4, 3, 2, 2, 1, 1)


def _make_deploy(rng: random.Random, i: int, deployed_at: datetime) -> DeployRecord:
    resource_count = max(1, round(rng.gauss(6, 4)))
    n_types = min(resource_count, rng.randint(1, 4))
    resource_types_touched = tuple(sorted(rng.sample(RESOURCE_TYPES, k=n_types)))
    plan_diff_size = max(50, round(rng.lognormvariate(mu=6.5, sigma=1.0)))
    author_role = rng.choice(AUTHOR_ROLES)
    apply_outcome = "success" if rng.random() > 0.02 else "apply_failed"
    return DeployRecord(
        deploy_id=f"dep_{i:05d}",
        commit_sha=f"{i:040x}",  # pragma: allowlist secret
        service=SERVICE,
        environment=ENVIRONMENT,
        deployed_at=deployed_at,
        author_role=author_role,
        plan_diff_size=plan_diff_size,
        resource_count=resource_count,
        resource_types_touched=resource_types_touched,
        apply_outcome=apply_outcome,
    )


def _breach_probability(
    *,
    deploy: DeployRecord,
    base_rate: float,
    recent_apply_failures: int,
    recent_incidents: int,
) -> float:
    """Learnable breach probability — features skew probability, so baselines + model can lift over noise floor."""
    prob = base_rate
    if deploy.plan_diff_size > 3000:
        prob *= 3.0
    elif deploy.plan_diff_size > 1500:
        prob *= 1.8
    if SENSITIVE_RESOURCE_TYPES.intersection(deploy.resource_types_touched):
        prob *= 1.7
    if recent_apply_failures >= 1:
        prob *= 2.5
    if recent_incidents >= 1:
        prob *= 1.5
    if deploy.deployed_at.hour in (17, 18, 19, 20, 21):
        prob *= 1.4
    if deploy.deployed_at.weekday() == 4 and deploy.deployed_at.hour >= 15:
        prob *= 1.3
    return min(prob, 0.75)


def _recent_events(times: list[datetime], t0: datetime, *, hours: int) -> int:
    lo = t0 - timedelta(hours=hours)
    return sum(1 for t in times if lo <= t < t0)


def _emit_monitor_state_after_breach(
    stream: SyntheticEventStream, breach_time: datetime, severity: str
) -> None:
    state = "alert" if severity in ("major", "critical") else "warning"
    stream.monitor_events.append(
        MonitorStateChange(slice_id=stream.slice_id(), event_time=breach_time, state=state)
    )
    stream.monitor_events.append(
        MonitorStateChange(
            slice_id=stream.slice_id(),
            event_time=breach_time + timedelta(minutes=30),
            state="ok",
        )
    )


def stream_summary(stream: SyntheticEventStream) -> dict[str, Any]:
    return {
        "start": stream.start.isoformat(),
        "end": stream.end.isoformat(),
        "days": (stream.end - stream.start).days,
        "deploys": len(stream.deploys),
        "slo_breaches": len(stream.slo_breaches),
        "apply_failures": len(stream.apply_failures),
        "monitor_events": len(stream.monitor_events),
        "incidents": len(stream.incidents),
    }
