"""
Base adapter interface for control plane integrations.

Each adapter translates a ForgeWorks JobSpec into a native resource
(K8s Job, Argo Workflow, etc), submits it, and tracks its status.
"""

from abc import ABC, abstractmethod

from app.schemas import JobResult, JobSpec, JobStatus


class ControlPlaneAdapter(ABC):
    """Base class for all control plane adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter identifier."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Adapter version."""

    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection to control plane."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the control plane is reachable."""

    @abstractmethod
    async def submit(self, spec: JobSpec) -> str:
        """Submit a job, return the native job ID."""

    @abstractmethod
    async def get_status(self, native_job_id: str) -> JobStatus:
        """Get current status of a submitted job."""

    @abstractmethod
    async def get_result(self, native_job_id: str) -> JobResult:
        """Get result after job completion."""

    @abstractmethod
    async def cancel(self, native_job_id: str) -> bool:
        """Cancel a running job."""
