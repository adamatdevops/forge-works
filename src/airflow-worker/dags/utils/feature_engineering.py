"""
Feature engineering for model training.

Transforms raw event data (from Kafka extraction) into numeric feature vectors
suitable for scikit-learn model training.

Feature categories:
1. Temporal — event frequency, time-of-day, day-of-week patterns
2. Behavioral — author patterns, repo activity levels
3. Correlation — events that co-occur (e.g., merge + no tests)
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

S3_BUCKET = "fw-models-dev"


def load_events_from_s3(s3_path: str) -> list[dict]:
    """Load newline-delimited JSON events from S3."""
    import boto3
    s3 = boto3.client("s3")
    bucket = s3_path.split("/")[2]
    key = "/".join(s3_path.split("/")[3:])

    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return [json.loads(line) for line in body.strip().split("\n") if line]


def extract_features(events: list[dict]) -> list[dict]:
    """
    Transform raw events into feature vectors for training.

    Each output row represents a time window (10 min) for a group key,
    with numeric features extracted from the events in that window.
    """
    # Group events by group_key (source:repo or source:namespace)
    groups = defaultdict(list)
    for event in events:
        source = event.get("source", "unknown")
        metadata = event.get("metadata", {})
        repo = metadata.get("repository", "")
        ns = metadata.get("namespace", "")
        name = metadata.get("name", "")

        if repo:
            key = f"{source}:{repo}"
        elif ns and name:
            key = f"{source}:{ns}/{name}"
        else:
            key = f"{source}:default"

        groups[key].append(event)

    # Extract features per group
    feature_rows = []
    for group_key, group_events in groups.items():
        features = _compute_group_features(group_key, group_events)
        feature_rows.append(features)

    return feature_rows


def _compute_group_features(group_key: str, events: list[dict]) -> dict:
    """Compute numeric features for a group of events."""
    source = group_key.split(":")[0]
    event_count = len(events)
    types = Counter(e.get("type", "unknown") for e in events)

    # Temporal features
    timestamps = []
    for e in events:
        ts = e.get("timestamp", "")
        try:
            timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        except (ValueError, AttributeError):
            pass

    time_span_minutes = 0
    if len(timestamps) >= 2:
        time_span_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60

    # Behavioral features
    authors = set()
    for e in events:
        meta = e.get("metadata", {})
        sender = meta.get("sender")
        if sender:
            authors.add(sender)

    # Source-specific features
    merge_count = sum(1 for e in events if "merged" in (e.get("type") or ""))
    push_count = sum(1 for e in events if "push" in (e.get("type") or ""))
    sync_count = sum(1 for e in events if "sync" in (e.get("type") or ""))
    crash_count = sum(1 for e in events if any(
        k in (e.get("type") or "") for k in ("crash", "restart", "backoff", "failed")
    ))
    test_count = sum(1 for e in events if any(
        k in (e.get("type") or "") for k in ("check_run", "check_suite", "workflow_run")
    ))

    # Label — was a pattern alert generated for this group?
    # This comes from forge.learning.outcomes (insights with pattern matches)
    has_alert = any(e.get("pattern_id") is not None for e in events)

    return {
        "group_key": group_key,
        "source": source,
        "event_count": event_count,
        "unique_types": len(types),
        "time_span_minutes": round(time_span_minutes, 2),
        "unique_authors": len(authors),
        "merge_count": merge_count,
        "push_count": push_count,
        "sync_count": sync_count,
        "crash_count": crash_count,
        "test_count": test_count,
        "events_per_minute": round(event_count / max(time_span_minutes, 1), 2),
        "author_concentration": round(1.0 / max(len(authors), 1), 4),
        "has_alert": 1 if has_alert else 0,
    }


def save_features_to_s3(features: list[dict], s3_prefix: str) -> str:
    """Save feature vectors to S3 as newline-delimited JSON."""
    import boto3
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"{s3_prefix}/features/{timestamp}.jsonl"

    s3 = boto3.client("s3")
    body = "\n".join(json.dumps(f) for f in features)
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=body.encode("utf-8"))

    s3_path = f"s3://{S3_BUCKET}/{s3_key}"
    logger.info("Saved %d feature rows → %s", len(features), s3_path)
    return s3_path
