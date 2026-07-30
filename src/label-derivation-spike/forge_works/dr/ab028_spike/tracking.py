"""MLflow tracking wrapper with a local-JSON fallback.

The real spike will use MLflow (per RFC §4 / AB-032). The scaffold ships a fallback so tests
and offline runs don't need an MLflow server. Import contract is stable — swap the backend
without touching call sites.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class LocalJSONTracker:
    """Fallback tracker — writes each run to a single JSON file under run_dir."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.params: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self.artifacts: dict[str, Any] = {}
        self.tags: dict[str, str] = {"created_at": datetime.now(tz=UTC).isoformat()}

    def log_param(self, key: str, value: Any) -> None:
        self.params[key] = _jsonify(value)

    def log_metric(self, key: str, value: float) -> None:
        self.metrics[key] = float(value)

    def log_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = _jsonify(value)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value

    def finalize(self) -> Path:
        payload = {
            "params": self.params,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "tags": self.tags,
        }
        out = self.run_dir / "run.json"
        out.write_text(json.dumps(payload, indent=2, default=str))
        return out


def open_tracker(run_dir: Path) -> LocalJSONTracker:
    """Return a tracker. Prefer this over instantiating directly — the real spike swaps in MLflow here."""
    return LocalJSONTracker(run_dir)


def _jsonify(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonify(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value
