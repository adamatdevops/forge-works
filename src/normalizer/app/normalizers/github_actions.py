"""
GitHub Actions event → NormalizedConfig normalizer.

Consumes `workflow_run` and `workflow_job` webhook payloads and converts them
to canonical Pipeline/Stage representations.

Resource refs:
  workflow_run → "github-actions:{repo}/{run_id}"
  workflow_job → "github-actions:{repo}/{run_id}/jobs/{job_id}"

Cross-correlation between runs and their jobs is left to a downstream stateful
processor; each event produces its own NormalizedConfig record.
"""

import json
import logging

from app.normalizers.base import ConfigNormalizer
from app.schemas import NormalizedConfig, Pipeline, Stage

logger = logging.getLogger(__name__)


class GitHubActionsNormalizer(ConfigNormalizer):

    @property
    def source(self) -> str:
        return "github-actions"

    def normalize(self, event: dict) -> NormalizedConfig | None:
        payload = event.get("payload", {}) or {}

        if "workflow_run" in payload:
            return self._normalize_workflow_run(payload)
        if "workflow_job" in payload:
            return self._normalize_workflow_job(payload)

        logger.info("Skipping github-actions event with no workflow_run/workflow_job key")
        return None

    def _normalize_workflow_run(self, payload: dict) -> NormalizedConfig | None:
        wf_run = payload.get("workflow_run", {}) or {}
        repo = self._repo_full_name(payload)
        run_id = wf_run.get("id")
        if not repo or not run_id:
            logger.info("workflow_run missing repo or run id — skipping")
            return None

        name = wf_run.get("name") or payload.get("workflow", {}).get("name", "unknown")
        trigger_event = wf_run.get("event")
        triggers = [trigger_event] if trigger_event else []

        pipeline = Pipeline(
            name=name,
            repository=repo,
            trigger=triggers,
            stages=[],
            source="github-actions",
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"github-actions:{repo}/{run_id}",
            source="github-actions",
            resource_type="pipeline",
            resource=pipeline.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    def _normalize_workflow_job(self, payload: dict) -> NormalizedConfig | None:
        wf_job = payload.get("workflow_job", {}) or {}
        repo = self._repo_full_name(payload)
        run_id = wf_job.get("run_id")
        job_id = wf_job.get("id")
        if not repo or not run_id or not job_id:
            logger.info("workflow_job missing repo / run_id / job_id — skipping")
            return None

        job_name = wf_job.get("name", "unknown")
        steps = [s.get("name", "") for s in (wf_job.get("steps") or []) if s.get("name")]
        labels = wf_job.get("labels") or []
        runner_image = labels[0] if labels else ""

        stage = Stage(
            name=job_name,
            image=runner_image,
            steps=steps,
            depends=[],
            status=wf_job.get("status") or "",
            conclusion=wf_job.get("conclusion") or "",
        )

        workflow_name = payload.get("workflow", {}).get("name", job_name)
        pipeline = Pipeline(
            name=workflow_name,
            repository=repo,
            trigger=[],
            stages=[stage],
            source="github-actions",
        )

        raw_bytes = json.dumps(payload, sort_keys=True).encode()
        return NormalizedConfig(
            resource_ref=f"github-actions:{repo}/{run_id}/jobs/{job_id}",
            source="github-actions",
            resource_type="pipeline",
            resource=pipeline.model_dump(),
            raw_hash=NormalizedConfig.compute_hash(raw_bytes),
        )

    @staticmethod
    def _repo_full_name(payload: dict) -> str:
        repo = payload.get("repository") or {}
        return repo.get("full_name") or ""
