"""Seed data for ForgeWorks MVP demo.

Based on MVP.md requirements:
- 10-15 mock services
- 5 Golden Path templates
- Sample anomalies for demo
- Sample actions for audit log
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

# =============================================================================
# TEAMS (3 teams)
# =============================================================================
TEAMS = [
    {
        "id": str(uuid4()),
        "name": "Platform Team",
        "slug": "platform-team",
        "description": "Core platform engineering team - owns IDP and infrastructure",
        "email": "platform@forgeworks.dev",
        "slack_channel": "#platform-engineering",
    },
    {
        "id": str(uuid4()),
        "name": "Payments Team",
        "slug": "payments-team",
        "description": "Payment processing and financial services",
        "email": "payments@forgeworks.dev",
        "slack_channel": "#payments",
    },
    {
        "id": str(uuid4()),
        "name": "ML Team",
        "slug": "ml-team",
        "description": "Machine learning and AI/ML infrastructure",
        "email": "ml@forgeworks.dev",
        "slack_channel": "#ml-engineering",
    },
]

# Store IDs for reference
PLATFORM_TEAM_ID = TEAMS[0]["id"]
PAYMENTS_TEAM_ID = TEAMS[1]["id"]
ML_TEAM_ID = TEAMS[2]["id"]

# =============================================================================
# TEMPLATES (5 Golden Path templates)
# =============================================================================
TEMPLATES = [
    {
        "id": str(uuid4()),
        "name": "Python API",
        "slug": "python-api",
        "description": "Production-ready Python REST API with FastAPI, PostgreSQL, and full observability",
        "version": "1.0.0",
        "workload_type": "api",
        "language": "python",
        "capabilities": ["api", "crud", "async", "database"],
        "ideal_for": ["low_latency", "rest_api", "microservice"],
        "stack": {
            "framework": "fastapi",
            "database": "postgresql",
            "cache": "redis",
            "ci": "github-actions",
            "cd": "argocd",
        },
        "repository_url": "https://github.com/forgeworks/template-python-api",
        "documentation_url": "https://docs.forgeworks.dev/templates/python-api",
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "usage_count": 24,
        "is_active": True,
        "is_recommended": True,
    },
    {
        "id": str(uuid4()),
        "name": "Go Microservice",
        "slug": "go-service",
        "description": "High-performance Go microservice with Kubernetes-native deployment",
        "version": "1.0.0",
        "workload_type": "api",
        "language": "go",
        "capabilities": ["api", "grpc", "high_performance", "kubernetes"],
        "ideal_for": ["high_throughput", "low_latency", "grpc", "microservice"],
        "stack": {
            "framework": "gin",
            "database": "postgresql",
            "ci": "github-actions",
            "cd": "argocd",
        },
        "repository_url": "https://github.com/forgeworks/template-go-service",
        "documentation_url": "https://docs.forgeworks.dev/templates/go-service",
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "usage_count": 18,
        "is_active": True,
        "is_recommended": True,
    },
    {
        "id": str(uuid4()),
        "name": "Stream Processor",
        "slug": "stream-processor",
        "description": "Real-time stream processing with Kafka and Flink",
        "version": "1.0.0",
        "workload_type": "stream",
        "language": "python",
        "capabilities": ["streaming", "high_throughput", "event_driven", "kafka"],
        "ideal_for": ["stream", "event_driven", "real_time", "high_throughput"],
        "stack": {
            "framework": "flink",
            "messaging": "kafka",
            "ci": "github-actions",
            "cd": "argocd",
        },
        "repository_url": "https://github.com/forgeworks/template-stream-processor",
        "documentation_url": "https://docs.forgeworks.dev/templates/stream-processor",
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "usage_count": 8,
        "is_active": True,
        "is_recommended": True,
    },
    {
        "id": str(uuid4()),
        "name": "Data Pipeline",
        "slug": "data-pipeline",
        "description": "Batch data processing with Kafka and Airflow",
        "version": "1.0.0",
        "workload_type": "batch",
        "language": "python",
        "capabilities": ["batch", "etl", "scheduling", "data_processing"],
        "ideal_for": ["batch", "etl", "data_warehouse", "scheduled"],
        "stack": {
            "orchestrator": "airflow",
            "messaging": "kafka",
            "storage": "s3",
            "ci": "github-actions",
            "cd": "argocd",
        },
        "repository_url": "https://github.com/forgeworks/template-data-pipeline",
        "documentation_url": "https://docs.forgeworks.dev/templates/data-pipeline",
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "usage_count": 12,
        "is_active": True,
        "is_recommended": True,
    },
    {
        "id": str(uuid4()),
        "name": "ML Service",
        "slug": "ml-service",
        "description": "Production ML model serving with PyTorch and FastAPI",
        "version": "1.0.0",
        "workload_type": "ml",
        "language": "python",
        "capabilities": ["ml", "inference", "model_serving", "gpu"],
        "ideal_for": ["ml_inference", "model_serving", "ai", "gpu_workload"],
        "stack": {
            "framework": "fastapi",
            "ml_framework": "pytorch",
            "serving": "triton",
            "ci": "github-actions",
            "cd": "argocd",
        },
        "repository_url": "https://github.com/forgeworks/template-ml-service",
        "documentation_url": "https://docs.forgeworks.dev/templates/ml-service",
        "includes_ci": True,
        "includes_cd": True,
        "includes_monitoring": True,
        "includes_tests": True,
        "usage_count": 6,
        "is_active": True,
        "is_recommended": True,
    },
]

# Store template IDs for reference
PYTHON_API_ID = TEMPLATES[0]["id"]
GO_SERVICE_ID = TEMPLATES[1]["id"]
STREAM_PROCESSOR_ID = TEMPLATES[2]["id"]
DATA_PIPELINE_ID = TEMPLATES[3]["id"]
ML_SERVICE_ID = TEMPLATES[4]["id"]

# =============================================================================
# SERVICES (12 mock services)
# =============================================================================
now = datetime.now(UTC)

SERVICES = [
    # Payment services (triggers anomaly - high deploy frequency)
    {
        "id": str(uuid4()),
        "name": "payment-service",
        "slug": "payment-service",
        "description": "Core payment processing service",
        "team_id": PAYMENTS_TEAM_ID,
        "template_id": GO_SERVICE_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/payment-service",
        "namespace": "payments",
        "argocd_app_name": "payment-service",
        "deploys_today": 12,  # ANOMALY: High deploy frequency
        "rollbacks_this_week": 1,
        "last_deploy_at": now - timedelta(hours=1),
        "tags": ["payments", "critical", "pci"],
    },
    # User API (triggers anomaly - consecutive rollbacks)
    {
        "id": str(uuid4()),
        "name": "user-api",
        "slug": "user-api",
        "description": "User management and authentication API",
        "team_id": PLATFORM_TEAM_ID,
        "template_id": PYTHON_API_ID,
        "status": "degraded",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/user-api",
        "namespace": "platform",
        "argocd_app_name": "user-api",
        "deploys_today": 2,
        "rollbacks_this_week": 3,  # ANOMALY: Consecutive rollbacks
        "last_deploy_at": now - timedelta(hours=4),
        "tags": ["auth", "users", "critical"],
    },
    # ML Inference (triggers anomaly - pipeline failing)
    {
        "id": str(uuid4()),
        "name": "ml-inference",
        "slug": "ml-inference",
        "description": "Real-time ML model inference service",
        "team_id": ML_TEAM_ID,
        "template_id": ML_SERVICE_ID,
        "status": "unhealthy",
        "tier": "standard",
        "repository_url": "https://github.com/forgeworks/ml-inference",
        "namespace": "ml",
        "argocd_app_name": "ml-inference",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=3),  # ANOMALY: Pipeline failing 48+ hours
        "tags": ["ml", "inference", "gpu"],
        "metadata": {"pipeline_status": "failing", "pipeline_failed_hours": 52},
    },
    # Healthy services
    {
        "id": str(uuid4()),
        "name": "order-service",
        "slug": "order-service",
        "description": "Order management and fulfillment",
        "team_id": PAYMENTS_TEAM_ID,
        "template_id": PYTHON_API_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/order-service",
        "namespace": "orders",
        "argocd_app_name": "order-service",
        "deploys_today": 1,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(hours=8),
        "tags": ["orders", "payments"],
    },
    {
        "id": str(uuid4()),
        "name": "notification-service",
        "slug": "notification-service",
        "description": "Email and push notification delivery",
        "team_id": PLATFORM_TEAM_ID,
        "template_id": STREAM_PROCESSOR_ID,
        "status": "healthy",
        "tier": "standard",
        "repository_url": "https://github.com/forgeworks/notification-service",
        "namespace": "platform",
        "argocd_app_name": "notification-service",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=2),
        "tags": ["notifications", "email", "push"],
    },
    {
        "id": str(uuid4()),
        "name": "analytics-pipeline",
        "slug": "analytics-pipeline",
        "description": "Business analytics data pipeline",
        "team_id": ML_TEAM_ID,
        "template_id": DATA_PIPELINE_ID,
        "status": "healthy",
        "tier": "standard",
        "repository_url": "https://github.com/forgeworks/analytics-pipeline",
        "namespace": "data",
        "argocd_app_name": "analytics-pipeline",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=5),
        "tags": ["analytics", "etl", "data"],
    },
    {
        "id": str(uuid4()),
        "name": "search-service",
        "slug": "search-service",
        "description": "Full-text search and indexing",
        "team_id": PLATFORM_TEAM_ID,
        "template_id": GO_SERVICE_ID,
        "status": "healthy",
        "tier": "standard",
        "repository_url": "https://github.com/forgeworks/search-service",
        "namespace": "platform",
        "argocd_app_name": "search-service",
        "deploys_today": 1,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(hours=12),
        "tags": ["search", "elasticsearch"],
    },
    {
        "id": str(uuid4()),
        "name": "recommendation-engine",
        "slug": "recommendation-engine",
        "description": "Product recommendation ML service",
        "team_id": ML_TEAM_ID,
        "template_id": ML_SERVICE_ID,
        "status": "healthy",
        "tier": "standard",
        "repository_url": "https://github.com/forgeworks/recommendation-engine",
        "namespace": "ml",
        "argocd_app_name": "recommendation-engine",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=1),
        "tags": ["ml", "recommendations"],
    },
    {
        "id": str(uuid4()),
        "name": "inventory-service",
        "slug": "inventory-service",
        "description": "Inventory and stock management",
        "team_id": PAYMENTS_TEAM_ID,
        "template_id": PYTHON_API_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/inventory-service",
        "namespace": "inventory",
        "argocd_app_name": "inventory-service",
        "deploys_today": 2,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(hours=3),
        "tags": ["inventory", "stock"],
    },
    {
        "id": str(uuid4()),
        "name": "event-stream",
        "slug": "event-stream",
        "description": "Central event streaming platform",
        "team_id": PLATFORM_TEAM_ID,
        "template_id": STREAM_PROCESSOR_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/event-stream",
        "namespace": "platform",
        "argocd_app_name": "event-stream",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=7),
        "tags": ["events", "kafka", "streaming"],
    },
    {
        "id": str(uuid4()),
        "name": "fraud-detection",
        "slug": "fraud-detection",
        "description": "Real-time fraud detection ML model",
        "team_id": ML_TEAM_ID,
        "template_id": ML_SERVICE_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/fraud-detection",
        "namespace": "ml",
        "argocd_app_name": "fraud-detection",
        "deploys_today": 0,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(days=3),
        "tags": ["ml", "fraud", "security"],
    },
    {
        "id": str(uuid4()),
        "name": "api-gateway",
        "slug": "api-gateway",
        "description": "Central API gateway and routing",
        "team_id": PLATFORM_TEAM_ID,
        "template_id": GO_SERVICE_ID,
        "status": "healthy",
        "tier": "critical",
        "repository_url": "https://github.com/forgeworks/api-gateway",
        "namespace": "platform",
        "argocd_app_name": "api-gateway",
        "deploys_today": 1,
        "rollbacks_this_week": 0,
        "last_deploy_at": now - timedelta(hours=6),
        "tags": ["gateway", "routing", "critical"],
    },
]

# Store service IDs for anomalies
PAYMENT_SERVICE_ID = SERVICES[0]["id"]
USER_API_ID = SERVICES[1]["id"]
ML_INFERENCE_ID = SERVICES[2]["id"]

# =============================================================================
# ANOMALIES (3 demo anomalies)
# =============================================================================
ANOMALIES = [
    {
        "id": str(uuid4()),
        "service_id": PAYMENT_SERVICE_ID,
        "type": "high_deploy_frequency",
        "severity": "critical",
        "title": "Unusually high deploy frequency",
        "description": "12 deploys in the last 2 hours (normal: 2). This may indicate a hotfix loop or deployment issues.",
        "suggestion": "Review recent deployments and check for recurring failures that may be triggering automatic rollbacks.",
        "detected_value": "12 deploys",
        "expected_value": "2 deploys (avg)",
        "detection_rule": "deploy_frequency > 5x normal rate",
        "context": {
            "time_window": "2 hours",
            "deployers": ["ci-bot", "ci-bot", "jane.doe"],
        },
        "is_active": True,
        "is_acknowledged": False,
        "detected_at": now - timedelta(hours=1),
    },
    {
        "id": str(uuid4()),
        "service_id": USER_API_ID,
        "type": "consecutive_rollbacks",
        "severity": "warning",
        "title": "Consecutive rollbacks this week",
        "description": "3 consecutive rollbacks detected this week. This may indicate stability issues or problematic releases.",
        "suggestion": "Review the changes in recent releases and consider additional testing or staged rollouts.",
        "detected_value": "3 rollbacks",
        "expected_value": "0-1 rollbacks",
        "detection_rule": "rollbacks_this_week >= 3",
        "context": {
            "rollback_commits": ["abc123", "def456", "ghi789"],
            "last_stable_version": "v2.3.1",
        },
        "is_active": True,
        "is_acknowledged": False,
        "detected_at": now - timedelta(hours=12),
    },
    {
        "id": str(uuid4()),
        "service_id": ML_INFERENCE_ID,
        "type": "pipeline_failing",
        "severity": "warning",
        "title": "CI/CD pipeline failing for extended period",
        "description": "Pipeline has been failing in staging for 48+ hours. No successful deployments since failure.",
        "suggestion": "Check pipeline logs for errors. Common issues: failing tests, build errors, or infrastructure problems.",
        "detected_value": "52 hours",
        "expected_value": "< 4 hours",
        "detection_rule": "pipeline_failure_duration > 24 hours",
        "context": {
            "pipeline_url": "https://github.com/forgeworks/ml-inference/actions",
            "failure_reason": "Test failures in model validation",
            "last_success": (now - timedelta(hours=52)).isoformat(),
        },
        "is_active": True,
        "is_acknowledged": False,
        "detected_at": now - timedelta(hours=48),
    },
]


def get_seed_data() -> dict:
    """Return all seed data as a dictionary."""
    return {
        "teams": TEAMS,
        "templates": TEMPLATES,
        "services": SERVICES,
        "anomalies": ANOMALIES,
    }


if __name__ == "__main__":
    import json

    data = get_seed_data()
    print(json.dumps(data, indent=2, default=str))
