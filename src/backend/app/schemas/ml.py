"""ML schemas for template recommendation system."""

from enum import Enum

from pydantic import BaseModel, Field


class WorkloadType(str, Enum):
    """Type of workload for template recommendation."""

    API = "api"
    WORKER = "worker"
    CRON = "cron"
    ML_PIPELINE = "ml-pipeline"
    FRONTEND = "frontend"
    BATCH = "batch"


class ProgrammingLanguage(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"
    MYSQL = "mysql"
    NONE = "none"


class TemplateType(str, Enum):
    """Available golden path templates."""

    MICROSERVICE_PYTHON = "microservice-python"
    MICROSERVICE_NODE = "microservice-node"
    WORKER_SERVICE = "worker-service"
    ML_PIPELINE = "ml-pipeline"
    FRONTEND_APP = "frontend-app"


# =============================================================================
# Input Schemas
# =============================================================================


class WorkloadFeatures(BaseModel):
    """Input features for template recommendation."""

    # Language and framework
    language: ProgrammingLanguage = Field(description="Primary programming language")
    framework: str | None = Field(
        default=None,
        description="Framework if applicable (fastapi, express, nextjs, etc.)",
    )

    # Workload characteristics
    workload_type: WorkloadType = Field(description="Type of workload")
    service_name: str | None = Field(
        default=None,
        description="Name of the service being created",
    )

    # Infrastructure requirements
    needs_database: bool = Field(
        default=False,
        description="Whether the service needs a database",
    )
    database_type: DatabaseType = Field(
        default=DatabaseType.NONE,
        description="Type of database needed",
    )
    needs_queue: bool = Field(
        default=False,
        description="Whether the service needs a message queue",
    )
    needs_cache: bool = Field(
        default=False,
        description="Whether the service needs caching (Redis)",
    )
    needs_gpu: bool = Field(
        default=False,
        description="Whether the service needs GPU resources",
    )

    # Scale expectations
    expected_rps: int = Field(
        default=100,
        ge=0,
        le=1000000,
        description="Expected requests per second",
    )
    expected_memory_mb: int = Field(
        default=512,
        ge=128,
        le=65536,
        description="Expected memory usage in MB",
    )

    # Team and compliance
    team_size: int = Field(
        default=5,
        ge=1,
        le=1000,
        description="Size of the development team",
    )
    compliance_required: bool = Field(
        default=False,
        description="Whether compliance features are required (SOC2, HIPAA, etc.)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "framework": "fastapi",
                "workload_type": "api",
                "service_name": "user-service",
                "needs_database": True,
                "database_type": "postgresql",
                "needs_queue": False,
                "needs_cache": True,
                "needs_gpu": False,
                "expected_rps": 500,
                "expected_memory_mb": 1024,
                "team_size": 8,
                "compliance_required": True,
            }
        }


# =============================================================================
# Output Schemas
# =============================================================================


class TemplateRecommendation(BaseModel):
    """Single template recommendation with confidence score."""

    template: TemplateType = Field(description="Recommended template type")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for this recommendation",
    )


class RecommendationResponse(BaseModel):
    """Response containing template recommendations."""

    primary: TemplateRecommendation = Field(description="Primary (best) recommendation")
    alternatives: list[TemplateRecommendation] = Field(
        default_factory=list,
        description="Alternative recommendations ranked by confidence",
    )
    input_summary: dict = Field(
        default_factory=dict,
        description="Summary of input features used",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "primary": {
                    "template": "microservice-python",
                    "confidence": 0.92,
                    "reasons": [
                        "Python language selected",
                        "FastAPI framework matches template",
                        "PostgreSQL database support included",
                    ],
                },
                "alternatives": [
                    {
                        "template": "worker-service",
                        "confidence": 0.45,
                        "reasons": ["Could work for async processing"],
                    }
                ],
                "input_summary": {
                    "language": "python",
                    "workload_type": "api",
                    "needs_database": True,
                },
            }
        }


# =============================================================================
# Feedback Schema
# =============================================================================


class RecommendationFeedback(BaseModel):
    """Feedback on a template recommendation."""

    recommendation_id: str | None = Field(
        default=None,
        description="ID of the recommendation (if tracked)",
    )
    selected_template: TemplateType = Field(
        description="Template the user actually selected",
    )
    was_primary: bool = Field(
        description="Whether the user selected the primary recommendation",
    )
    feedback_text: str | None = Field(
        default=None,
        description="Optional text feedback",
    )


# =============================================================================
# Training Data Schema
# =============================================================================


class TrainingExample(BaseModel):
    """Single training example for model training."""

    features: WorkloadFeatures = Field(description="Input features")
    label: TemplateType = Field(description="Correct template (ground truth)")
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Sample weight for training",
    )


class TrainingDataset(BaseModel):
    """Collection of training examples."""

    examples: list[TrainingExample] = Field(description="List of training examples")
    version: str = Field(
        default="1.0.0",
        description="Dataset version",
    )
    description: str | None = Field(
        default=None,
        description="Dataset description",
    )

    @property
    def size(self) -> int:
        """Number of examples in dataset."""
        return len(self.examples)

    def label_distribution(self) -> dict[str, int]:
        """Get distribution of labels."""
        dist: dict[str, int] = {}
        for ex in self.examples:
            label = ex.label.value
            dist[label] = dist.get(label, 0) + 1
        return dist
