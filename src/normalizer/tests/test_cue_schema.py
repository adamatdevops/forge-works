"""
CUE↔Pydantic schema fidelity tests.

For each normalizer, generate a representative event, normalize it, dump the
NormalizedConfig as JSON, and validate against the canonical CUE schema using
`cue vet`. Catches any field-name drift, type drift, or schema_version drift
between the two representations.

Requires the `cue` CLI to be available in PATH. CI installs it; local dev can
`brew install cue` (macOS) or grab a release tarball.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from app.normalizers.github_actions import GitHubActionsNormalizer
from app.normalizers.kubernetes import KubernetesNormalizer
from app.normalizers.terraform import TerraformNormalizer

CUE_FILE = Path(__file__).parent.parent / "cue" / "forgeworks.cue"

pytestmark = pytest.mark.skipif(
    shutil.which("cue") is None,
    reason="cue CLI not available; install with `brew install cue` or see CI workflow",
)


def cue_vet(payload: dict, definition: str = "#NormalizedConfig") -> None:
    """Validate a Python dict against a CUE definition. Raise AssertionError on mismatch.

    `cue vet` reads stdin permissively (no constraint enforcement observed in 0.16),
    so we materialize to a temp file with a `.json` suffix to force JSON parsing
    and full constraint evaluation.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(payload, f)
        tmp_path = f.name
    try:
        proc = subprocess.run(
            ["cue", "vet", "-d", definition, str(CUE_FILE), tmp_path],
            capture_output=True,
            timeout=15,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if proc.returncode != 0:
        raise AssertionError(
            f"CUE validation failed (definition={definition}):\n"
            f"stdout: {proc.stdout.decode()}\n"
            f"stderr: {proc.stderr.decode()}\n"
            f"payload: {json.dumps(payload, indent=2)}"
        )


# ---------------------------------------------------------------------------
# Kubernetes — workload + service paths
# ---------------------------------------------------------------------------


class TestKubernetesSchemaFidelity:

    def test_kubernetes_deployment_validates(self):
        normalizer = KubernetesNormalizer()
        event = {
            "source": "kubernetes",
            "metadata": {"namespace": "web", "name": "api"},
            "payload": {
                "kind": "Deployment",
                "metadata": {"name": "api", "namespace": "web", "labels": {"app": "api"}},
                "spec": {
                    "replicas": 3,
                    "template": {
                        "spec": {
                            "containers": [{
                                "image": "nginx:1.25",
                                "resources": {"requests": {"cpu": "250m", "memory": "256Mi"}},
                                "livenessProbe": {"httpGet": {"path": "/health"}},
                                "readinessProbe": {"httpGet": {"path": "/ready"}},
                            }],
                        },
                    },
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))

    def test_kubernetes_service_validates(self):
        normalizer = KubernetesNormalizer()
        event = {
            "source": "kubernetes",
            "metadata": {"namespace": "web", "name": "api-svc"},
            "payload": {
                "kind": "Service",
                "metadata": {"name": "api-svc", "namespace": "web"},
                "spec": {
                    "type": "ClusterIP",
                    "selector": {"app": "api"},
                    "ports": [{"port": 80, "protocol": "TCP"}],
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# Terraform — workload + service paths
# ---------------------------------------------------------------------------


class TestTerraformSchemaFidelity:

    def test_ecs_task_definition_validates(self):
        normalizer = TerraformNormalizer()
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_ecs_task_definition",
                "values": {
                    "family": "fw-api",
                    "cpu": 1024,
                    "memory": 2048,
                    "container_definitions": [{"name": "api", "image": "fw/api:1"}],
                    "tags": {"team": "platform"},
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))

    def test_aws_lb_listener_validates(self):
        normalizer = TerraformNormalizer()
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_lb_listener",
                "values": {"name": "api-listener", "port": 443, "protocol": "TCP"},
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# GitHub Actions — pipeline (workflow_run + workflow_job)
# ---------------------------------------------------------------------------


class TestGitHubActionsSchemaFidelity:

    def test_workflow_run_validates(self):
        normalizer = GitHubActionsNormalizer()
        event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_run": {"id": 1, "name": "CI", "event": "push"},
                "workflow": {"name": "CI"},
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))

    def test_workflow_job_validates(self):
        normalizer = GitHubActionsNormalizer()
        event = {
            "source": "github-actions",
            "payload": {
                "repository": {"full_name": "owner/repo"},
                "workflow_job": {
                    "id": 9, "run_id": 1, "name": "Test", "status": "completed",
                    "conclusion": "success", "labels": ["ubuntu-latest"],
                    "steps": [{"name": "Setup"}],
                },
                "workflow": {"name": "CI"},
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        cue_vet(result.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# Negative tests — ensure the schema actually catches drift
# ---------------------------------------------------------------------------


class TestSchemaNegative:

    def test_old_schema_version_rejected(self):
        """A schema_version=1 payload (pre-rename) must fail validation."""
        bad = {
            "config_id": "cfg_x", "resource_ref": "kubernetes:web/api",
            "schema_version": 1,  # was valid pre-E5.1c, now must fail
            "observed_at": "2026-05-06T10:00:00+00:00", "source": "kubernetes",
            "resource_type": "workload",
            "resource": {
                "name": "api", "namespace": "web", "replicas": 1, "image": "x",
                "resources": {"cpu_millicores": 0, "memory_mib": 0},
                "labels": {}, "source": "kubernetes",
            },
            "raw_hash": "x",
        }
        with pytest.raises(AssertionError, match="schema_version"):
            cue_vet(bad)

    def test_camelcase_workload_field_rejected(self):
        """Old camelCase field names must fail validation now that CUE uses snake_case."""
        bad = {
            "config_id": "cfg_x", "resource_ref": "kubernetes:web/api",
            "schema_version": 2,
            "observed_at": "2026-05-06T10:00:00+00:00", "source": "kubernetes",
            "resource_type": "workload",
            "resource": {
                "name": "api", "namespace": "web", "replicas": 1, "image": "x",
                "resources": {"cpu_millicores": 0, "memory_mib": 0},
                "labels": {}, "source": "kubernetes",
                "crashLoops": 0,  # camelCase — should be rejected
            },
            "raw_hash": "x",
        }
        with pytest.raises(AssertionError):
            cue_vet(bad)

    def test_unknown_resource_type_rejected(self):
        """resource_type is now a closed enum in CUE."""
        bad = {
            "config_id": "cfg_x", "resource_ref": "kubernetes:web/api",
            "schema_version": 2,
            "observed_at": "2026-05-06T10:00:00+00:00", "source": "kubernetes",
            "resource_type": "secret",  # not in enum
            "resource": {
                "name": "api", "namespace": "web", "replicas": 1, "image": "x",
                "resources": {"cpu_millicores": 0, "memory_mib": 0},
                "labels": {}, "source": "kubernetes",
            },
            "raw_hash": "x",
        }
        with pytest.raises(AssertionError, match="resource_type"):
            cue_vet(bad)
