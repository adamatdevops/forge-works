"""
ForgeWorks Pattern Consolidation DAG.

Schedule: Weekly on Sundays at 02:00 UTC
Pipeline: Load Alerts → Compute Similarity → Group → Generate Proposals

This DAG analyzes historical pattern alerts to find recurring patterns
that could be consolidated into new rules or model features.

Example: If "PR merged without tests" fires 50 times for repos A, B, C
but never for repos D, E, F — this suggests a team-level CI configuration
gap, not individual incidents. The consolidation proposal would recommend
adding branch protection at the org level.
"""

from collections import Counter
from datetime import datetime, timedelta

from airflow.decorators import dag, task

CONSOLIDATION_S3_PREFIX = "consolidation"


@dag(
    dag_id="pattern_consolidation",
    description="Weekly pattern analysis — find recurring patterns and generate consolidation proposals",
    schedule="0 2 * * 0",  # Sundays 02:00 UTC
    start_date=datetime(2026, 3, 29),
    catchup=False,
    default_args={
        "owner": "forgeworks",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["ml", "consolidation", "weekly"],
)
def pattern_consolidation():

    @task()
    def load_recent_alerts() -> dict:
        """Load the last 7 days of pattern alerts from Kafka."""
        from utils.kafka_extract import extract_topic_to_s3
        return extract_topic_to_s3(
            topic="forge.jobs.pending",
            s3_prefix=CONSOLIDATION_S3_PREFIX,
            max_messages=50000,
            timeout_ms=30000,
        )

    @task()
    def analyze_patterns(alerts_result: dict) -> dict:
        """Analyze alert distribution and find recurring patterns."""
        import json
        from collections import Counter, defaultdict

        import boto3

        if not alerts_result.get("s3_path"):
            return {"status": "no_data", "proposals": []}

        s3 = boto3.client("s3")
        bucket = alerts_result["s3_path"].split("/")[2]
        key = "/".join(alerts_result["s3_path"].split("/")[3:])
        response = s3.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read().decode("utf-8")
        alerts = [json.loads(line) for line in body.strip().split("\n") if line]

        if not alerts:
            return {"status": "no_alerts", "proposals": []}

        # Group by pattern_id
        pattern_groups = defaultdict(list)
        for alert in alerts:
            pid = alert.get("pattern_id", "unknown")
            pattern_groups[pid].append(alert)

        # Analyze each pattern
        proposals = []
        for pattern_id, group_alerts in pattern_groups.items():
            group_keys = Counter(a.get("group_key", "unknown") for a in group_alerts)
            total_alerts = len(group_alerts)

            if total_alerts >= 5:
                proposals.append({
                    "pattern_id": pattern_id,
                    "pattern_name": group_alerts[0].get("pattern_name", "Unknown"),
                    "total_alerts": total_alerts,
                    "affected_groups": len(group_keys),
                    "top_groups": group_keys.most_common(5),
                    "recommendation": _generate_recommendation(pattern_id, total_alerts, group_keys),
                })

        return {
            "status": "success",
            "total_alerts": len(alerts),
            "patterns_found": len(pattern_groups),
            "proposals": proposals,
        }

    @task()
    def save_proposals(analysis: dict) -> str:
        """Save consolidation proposals to S3."""
        import json

        import boto3

        proposals = analysis.get("proposals", [])
        if not proposals:
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"{CONSOLIDATION_S3_PREFIX}/proposals/{timestamp}.json"

        s3 = boto3.client("s3")
        s3.put_object(
            Bucket="fw-models-dev",
            Key=s3_key,
            Body=json.dumps(analysis, indent=2).encode("utf-8"),
        )

        return f"s3://fw-models-dev/{s3_key}"

    # DAG pipeline
    alerts = load_recent_alerts()
    analysis = analyze_patterns(alerts)
    save_proposals(analysis)


def _generate_recommendation(pattern_id: str, total: int, group_keys: Counter) -> str:
    """Generate human-readable recommendation based on pattern analysis."""
    top_group = group_keys.most_common(1)[0] if group_keys else ("unknown", 0)
    concentration = top_group[1] / total if total > 0 else 0

    if pattern_id == "PAT-CI-001":
        if len(group_keys) > 3:
            return f"CI gap affects {len(group_keys)} repos — consider org-level branch protection"
        return f"CI gap concentrated in {top_group[0]} — add branch protection to this repo"

    if pattern_id == "PAT-DEPLOY-001":
        if concentration > 0.5:
            return f"Rapid deploys concentrated in {top_group[0]} ({top_group[1]} alerts) — investigate deployment process"
        return f"Rapid deploys across {len(group_keys)} apps — review deployment cadence policies"

    if pattern_id == "PAT-K8S-001":
        return f"Crash loops in {len(group_keys)} workloads ({total} total) — prioritize stability review"

    return f"Pattern {pattern_id} fired {total} times across {len(group_keys)} groups"


pattern_consolidation()
