"""
Unit tests for GitHubActionsNormalizer.

Covers:
- workflow_run webhook → Pipeline (no stages, trigger captured)
- workflow_job webhook → Pipeline (one stage with steps + status + conclusion)
- Distinct resource_ref format for runs vs jobs
- Missing required fields → None
- Unknown payload → None
"""

import pytest

from app.normalizers.github_actions import GitHubActionsNormalizer


@pytest.fixture
def normalizer():
    return GitHubActionsNormalizer()


# ---------------------------------------------------------------------------
# workflow_run
# ---------------------------------------------------------------------------


class TestWorkflowRun:

    def test_workflow_run_completed_normalizes_to_pipeline(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "action": "completed",
                "repository": {"full_name": "adamatdevops/forge-works"},
                "workflow_run": {
                    "id": 17120000001,
                    "name": "CI",
                    "event": "push",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "abc1234",
                },
                "workflow": {
                    "id": 88,
                    "name": "CI",
                    "path": ".github/workflows/ci.yml",
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.source == "github-actions"
        assert result.resource_type == "pipeline"
        assert result.resource_ref == "github-actions:adamatdevops/forge-works/17120000001"

        pipe = result.resource
        assert pipe["name"] == "CI"
        assert pipe["repository"] == "adamatdevops/forge-works"
        assert pipe["trigger"] == ["push"]
        assert pipe["stages"] == []
        assert pipe["source"] == "github-actions"

    def test_workflow_run_missing_run_id_returns_none(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_run": {"name": "CI", "event": "push"},  # no id
            },
        }
        assert normalizer.normalize(event) is None

    def test_workflow_run_missing_repo_returns_none(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "workflow_run": {"id": 1, "name": "CI", "event": "push"},
            },
        }
        assert normalizer.normalize(event) is None

    def test_workflow_run_falls_back_to_workflow_name(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_run": {"id": 42, "event": "pull_request"},  # no name on run
                "workflow": {"name": "Lint Workflow"},
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource["name"] == "Lint Workflow"
        assert result.resource["trigger"] == ["pull_request"]


# ---------------------------------------------------------------------------
# workflow_job
# ---------------------------------------------------------------------------


class TestWorkflowJob:

    def test_workflow_job_normalizes_to_pipeline_with_one_stage(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "action": "completed",
                "repository": {"full_name": "adamatdevops/forge-works"},
                "workflow_job": {
                    "id": 99000000001,
                    "run_id": 17120000001,
                    "name": "Test Backend",
                    "status": "completed",
                    "conclusion": "success",
                    "labels": ["ubuntu-latest"],
                    "steps": [
                        {"name": "Set up job", "number": 1},
                        {"name": "Checkout", "number": 2},
                        {"name": "Run pytest", "number": 3},
                    ],
                },
                "workflow": {"name": "CI"},
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource_type == "pipeline"
        assert (
            result.resource_ref
            == "github-actions:adamatdevops/forge-works/17120000001/jobs/99000000001"
        )

        pipe = result.resource
        assert pipe["name"] == "CI"
        assert pipe["repository"] == "adamatdevops/forge-works"
        assert pipe["trigger"] == []
        assert len(pipe["stages"]) == 1

        stage = pipe["stages"][0]
        assert stage["name"] == "Test Backend"
        assert stage["image"] == "ubuntu-latest"
        assert stage["steps"] == ["Set up job", "Checkout", "Run pytest"]
        assert stage["status"] == "completed"
        assert stage["conclusion"] == "success"

    def test_workflow_job_missing_ids_returns_none(self, normalizer):
        event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_job": {"name": "Test"},  # no id, no run_id
            },
        }
        assert normalizer.normalize(event) is None

    def test_workflow_job_run_and_job_have_distinct_refs(self, normalizer):
        run_event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_run": {"id": 1, "name": "CI", "event": "push"},
            },
        }
        job_event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_job": {
                    "id": 999, "run_id": 1, "name": "Test", "status": "completed",
                    "conclusion": "success", "steps": [],
                },
                "workflow": {"name": "CI"},
            },
        }
        run_res = normalizer.normalize(run_event)
        job_res = normalizer.normalize(job_event)
        assert run_res is not None and job_res is not None
        assert run_res.resource_ref != job_res.resource_ref
        assert run_res.resource_ref == "github-actions:owner/repo/1"
        assert job_res.resource_ref == "github-actions:owner/repo/1/jobs/999"


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


class TestMisc:

    def test_unknown_payload_returns_none(self, normalizer):
        event = {"source": "github-actions", "payload": {"action": "ping"}}
        assert normalizer.normalize(event) is None

    def test_normalizer_source_property(self, normalizer):
        assert normalizer.source == "github-actions"
