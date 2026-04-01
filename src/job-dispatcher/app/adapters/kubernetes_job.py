"""
Kubernetes Job Adapter — translates ForgeWorks JobSpecs into K8s Jobs.

How it works:
1. Receives a JobSpec (pattern alert → actionable task)
2. Translates to a K8s Job manifest with:
   - ForgeWorks labels for tracking (job_id, correlation_id, pattern_id)
   - Task container with input data as env vars
   - Resource limits from the spec
   - TTL for auto-cleanup after completion
3. Submits via K8s API
4. Polls status until completion or timeout
5. Returns JobResult with exit code, logs, duration

Why K8s Jobs (not Pods):
- Built-in retry logic (backoffLimit)
- TTL-based cleanup (ttlSecondsAfterFinished)
- Status tracking (succeeded/failed/active)
- Works with RBAC and PodSecurity policies
"""

import asyncio
import logging
import time

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.adapters.base import ControlPlaneAdapter
from app.config import settings
from app.schemas import JobResult, JobSpec, JobStatus

logger = logging.getLogger(__name__)


class KubernetesJobAdapter(ControlPlaneAdapter):

    def __init__(self):
        self._batch_v1: client.BatchV1Api | None = None
        self._core_v1: client.CoreV1Api | None = None
        self._connected = False
        self._job_id_map: dict[str, str] = {}  # native_name → original_job_id

    @property
    def name(self) -> str:
        return "kubernetes-job"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def connect(self) -> bool:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        self._batch_v1 = client.BatchV1Api()
        self._core_v1 = client.CoreV1Api()
        self._connected = True
        logger.info("K8s Job Adapter connected (namespace: %s)", settings.k8s_namespace)
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def health_check(self) -> bool:
        if not self._connected or not self._batch_v1:
            return False
        try:
            self._batch_v1.list_namespaced_job(settings.k8s_namespace, limit=1)
            return True
        except ApiException:
            return False

    async def submit(self, spec: JobSpec) -> str:
        """Create a K8s Job from a ForgeWorks JobSpec."""
        job_name = f"fw-{spec.job_id.replace('_', '-')}"

        env_vars = [
            client.V1EnvVar(name="FORGE_JOB_ID", value=spec.job_id),
            client.V1EnvVar(name="FORGE_CORRELATION_ID", value=spec.correlation_id),
            client.V1EnvVar(name="FORGE_PATTERN_ID", value=spec.pattern_id),
            client.V1EnvVar(name="FORGE_GROUP_KEY", value=spec.group_key),
        ]
        for key, value in spec.input_data.items():
            env_vars.append(
                client.V1EnvVar(name=f"INPUT_{key.upper()}", value=str(value))
            )

        container = client.V1Container(
            name="task",
            image=spec.task_image or "busybox:latest",
            command=["sh", "-c", self._task_command(spec)],
            env=env_vars,
            resources=client.V1ResourceRequirements(
                requests={"cpu": spec.cpu, "memory": spec.memory},
                limits={"cpu": spec.cpu, "memory": spec.memory},
            ),
            security_context=client.V1SecurityContext(
                allow_privilege_escalation=False,
                capabilities=client.V1Capabilities(drop=["ALL"]),
            ),
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=settings.k8s_namespace,
                labels={
                    "app.kubernetes.io/managed-by": "forgeworks-dispatcher",
                    "forgeworks.io/job-id": spec.job_id.replace("_", "-"),
                    "forgeworks.io/pattern-id": spec.pattern_id,
                },
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=settings.k8s_job_ttl_seconds,
                backoff_limit=1,
                active_deadline_seconds=spec.timeout_seconds,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "forgeworks.io/job-id": spec.job_id.replace("_", "-"),
                        },
                    ),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        image_pull_secrets=[client.V1LocalObjectReference(name="ghcr-pull-secret")],
                        containers=[container],
                        security_context=client.V1PodSecurityContext(
                            run_as_non_root=True,
                            run_as_user=1000,
                            seccomp_profile=client.V1SeccompProfile(
                                type="RuntimeDefault"
                            ),
                        ),
                    ),
                ),
            ),
        )

        result = self._batch_v1.create_namespaced_job(
            namespace=settings.k8s_namespace, body=job
        )
        self._job_id_map[result.metadata.name] = spec.job_id
        logger.info("K8s Job submitted: %s (pattern: %s)", job_name, spec.pattern_id)
        return result.metadata.name

    async def get_status(self, native_job_id: str) -> JobStatus:
        try:
            job = self._batch_v1.read_namespaced_job_status(
                name=native_job_id, namespace=settings.k8s_namespace
            )
            if job.status.succeeded and job.status.succeeded > 0:
                return JobStatus.COMPLETED
            if job.status.failed and job.status.failed > 0:
                return JobStatus.FAILED
            if job.status.active and job.status.active > 0:
                return JobStatus.RUNNING
            return JobStatus.PENDING
        except ApiException as e:
            logger.error("Failed to get job status for %s: %s", native_job_id, e.reason)
            return JobStatus.FAILED

    async def get_result(self, native_job_id: str) -> JobResult:
        status = await self.get_status(native_job_id)

        # Get pod logs
        output = None
        try:
            pods = self._core_v1.list_namespaced_pod(
                namespace=settings.k8s_namespace,
                label_selector=f"forgeworks.io/job-id={native_job_id.replace('fw-', '')}",
            )
            if pods.items:
                output = self._core_v1.read_namespaced_pod_log(
                    name=pods.items[0].metadata.name,
                    namespace=settings.k8s_namespace,
                    tail_lines=100,
                )
        except ApiException:
            pass

        return JobResult(
            job_id=self._job_id_map.get(native_job_id, native_job_id),
            status=status,
            adapter=self.name,
            output=output,
        )

    async def cancel(self, native_job_id: str) -> bool:
        try:
            self._batch_v1.delete_namespaced_job(
                name=native_job_id,
                namespace=settings.k8s_namespace,
                propagation_policy="Background",
            )
            return True
        except ApiException:
            return False

    def _task_command(self, spec: JobSpec) -> str:
        """Generate task command based on task type."""
        commands = {
            "create-github-issue": (
                'echo "Would create GitHub issue for pattern: $FORGE_PATTERN_ID, '
                'group: $FORGE_GROUP_KEY" && echo "RESULT:success"'
            ),
            "send-slack-alert": (
                'echo "Would send Slack alert for pattern: $FORGE_PATTERN_ID, '
                'severity: $INPUT_SEVERITY" && echo "RESULT:success"'
            ),
            "run-security-scan": (
                'echo "Would run security scan for: $INPUT_REPOSITORY" '
                '&& echo "RESULT:success"'
            ),
        }
        return commands.get(
            spec.task_type,
            f'echo "Executing task: {spec.task_type} for job: $FORGE_JOB_ID" '
            '&& echo "RESULT:success"',
        )
