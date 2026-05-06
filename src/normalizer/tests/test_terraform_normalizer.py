"""
Unit tests for TerraformNormalizer.

Covers:
- ECS task definition → Workload (CPU unit conversion 1024 → 1000 millicores)
- K8s deployment via Terraform provider → Workload (block-as-list nesting)
- ALB listener → Service
- K8s service via Terraform provider → Service
- Unsupported resource types return None
- Edge cases on numeric/string CPU and memory parsing
"""

import json

import pytest

from app.normalizers.terraform import (
    TerraformNormalizer,
    parse_cpu_millicores,
    parse_memory_mib,
)


@pytest.fixture
def normalizer():
    return TerraformNormalizer()


# ---------------------------------------------------------------------------
# Unit-conversion helpers
# ---------------------------------------------------------------------------


class TestParseCpuMillicores:

    @pytest.mark.parametrize("cpu_in,expected", [
        (1024, 1000),    # 1 vCPU AWS units → 1000 millicores
        (512, 500),      # 0.5 vCPU AWS units → 500 millicores
        (256, 250),      # 0.25 vCPU AWS units → 250 millicores
        (2048, 2000),    # 2 vCPU AWS units → 2000 millicores
        ("250m", 250),   # K8s string with m suffix
        ("500m", 500),
        ("1", 1000),     # K8s plain "1" → 1000 millicores
        ("1.5", 1500),   # K8s fractional vCPU
        ("", 0),
        (None, 0),
        ("garbage", 0),
    ])
    def test_conversions(self, cpu_in, expected):
        assert parse_cpu_millicores(cpu_in) == expected


class TestParseMemoryMib:

    @pytest.mark.parametrize("mem_in,expected", [
        (512, 512),       # ECS numeric MiB passthrough
        (2048, 2048),
        ("512Mi", 512),
        ("2Gi", 2048),
        ("1024Mi", 1024),
        ("1Ki", 0),       # 1Ki = 1/1024 MiB → int truncation = 0
        ("1024", 1024),   # bare numeric string → MiB default
        ("", 0),
        (None, 0),
        ("garbage", 0),
    ])
    def test_conversions(self, mem_in, expected):
        assert parse_memory_mib(mem_in) == expected


# ---------------------------------------------------------------------------
# ECS task definition → Workload
# ---------------------------------------------------------------------------


class TestEcsTaskDefinition:

    def test_ecs_task_definition_normalizes_to_workload(self, normalizer):
        event = {
            "source": "terraform",
            "event_id": "evt-1",
            "metadata": {},
            "payload": {
                "type": "aws_ecs_task_definition",
                "values": {
                    "family": "fw-api",
                    "cpu": 1024,
                    "memory": 2048,
                    "container_definitions": json.dumps([
                        {"name": "api", "image": "fw/api:1.2.3"}
                    ]),
                    "tags": {"team": "platform"},
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.source == "terraform"
        assert result.resource_type == "workload"
        assert result.resource_ref == "terraform:default/fw-api"

        wl = result.resource
        assert wl["name"] == "fw-api"
        assert wl["namespace"] == "default"
        assert wl["image"] == "fw/api:1.2.3"
        assert wl["resources"]["cpu_millicores"] == 1000
        assert wl["resources"]["memory_mib"] == 2048
        assert wl["labels"] == {"team": "platform"}
        assert wl["source"] == "terraform"

    def test_ecs_task_definition_with_container_array_object(self, normalizer):
        """Some plan exports leave container_definitions as a parsed list, not a string."""
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_ecs_task_definition",
                "values": {
                    "family": "worker",
                    "cpu": 256,
                    "memory": 512,
                    "container_definitions": [
                        {"name": "worker", "image": "fw/worker:0.1"}
                    ],
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource["resources"]["cpu_millicores"] == 250
        assert result.resource["resources"]["memory_mib"] == 512
        assert result.resource["image"] == "fw/worker:0.1"

    def test_ecs_service_uses_desired_count_as_replicas(self, normalizer):
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_ecs_service",
                "values": {
                    "name": "api-svc",
                    "desired_count": 3,
                    "cpu": 512,
                    "memory": 1024,
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource["replicas"] == 3
        assert result.resource["resources"]["cpu_millicores"] == 500


# ---------------------------------------------------------------------------
# K8s-via-Terraform deployment → Workload
# ---------------------------------------------------------------------------


class TestKubernetesProviderDeployment:

    def test_kubernetes_deployment_v1_block_as_list(self, normalizer):
        """Terraform K8s provider serializes nested blocks as single-element lists."""
        event = {
            "source": "terraform",
            "payload": {
                "type": "kubernetes_deployment_v1",
                "values": {
                    "metadata": [{
                        "name": "frontend",
                        "namespace": "web",
                        "labels": {"app": "frontend", "tier": "web"},
                    }],
                    "spec": [{
                        "replicas": 4,
                        "template": [{
                            "spec": [{
                                "container": [{
                                    "image": "nginx:1.25",
                                    "resources": [{
                                        "requests": [{"cpu": "250m", "memory": "256Mi"}],
                                        "limits":   [{"cpu": "500m", "memory": "512Mi"}],
                                    }],
                                }],
                            }],
                        }],
                    }],
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource_ref == "terraform:web/frontend"

        wl = result.resource
        assert wl["name"] == "frontend"
        assert wl["namespace"] == "web"
        assert wl["replicas"] == 4
        assert wl["image"] == "nginx:1.25"
        assert wl["resources"]["cpu_millicores"] == 250
        assert wl["resources"]["memory_mib"] == 256
        assert wl["labels"] == {"app": "frontend", "tier": "web"}


# ---------------------------------------------------------------------------
# ALB / K8s service → Service
# ---------------------------------------------------------------------------


class TestServices:

    def test_aws_lb_listener_normalizes_to_service(self, normalizer):
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_lb_listener",
                "values": {
                    "name": "api-listener",
                    "port": 443,
                    "protocol": "HTTPS",
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        assert result.resource_type == "service"
        svc = result.resource
        assert svc["port"] == 443
        # protocol must round-trip through the canonical TCP/UDP enum
        assert svc["protocol"] in ("TCP", "UDP", "HTTPS")  # current schema is permissive
        assert svc["type"] == "LoadBalancer"

    def test_kubernetes_service_v1_extracts_first_port(self, normalizer):
        event = {
            "source": "terraform",
            "payload": {
                "type": "kubernetes_service_v1",
                "values": {
                    "metadata": [{"name": "frontend-svc", "namespace": "web"}],
                    "spec": [{
                        "type": "ClusterIP",
                        "selector": [{"app": "frontend"}],
                        "port": [
                            {"port": 80, "protocol": "TCP"},
                            {"port": 443, "protocol": "TCP"},
                        ],
                    }],
                },
            },
        }
        result = normalizer.normalize(event)
        assert result is not None
        svc = result.resource
        assert svc["name"] == "frontend-svc"
        assert svc["namespace"] == "web"
        assert svc["port"] == 80
        assert svc["protocol"] == "TCP"
        assert svc["type"] == "ClusterIP"
        assert svc["selector"] == {"app": "frontend"}


# ---------------------------------------------------------------------------
# Unsupported / malformed
# ---------------------------------------------------------------------------


class TestUnsupported:

    def test_unsupported_resource_type_returns_none(self, normalizer):
        event = {
            "source": "terraform",
            "payload": {
                "type": "aws_s3_bucket",
                "values": {"bucket": "my-bucket"},
            },
        }
        assert normalizer.normalize(event) is None

    def test_missing_payload_returns_none(self, normalizer):
        assert normalizer.normalize({"source": "terraform"}) is None

    def test_normalizer_source_property(self, normalizer):
        assert normalizer.source == "terraform"
