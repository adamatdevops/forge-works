from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "job-dispatcher"
    app_version: str = "0.1.0"
    debug: bool = False
    port: int = 8090

    # Kafka
    kafka_bootstrap_servers: str = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
    kafka_consumer_group: str = "forgeworks-job-dispatcher"
    kafka_input_topic: str = "forge.learning.outcomes"
    kafka_results_topic: str = "forge.jobs.results"
    kafka_feedback_topic: str = "forge.learning.feedback"

    # Kubernetes
    k8s_namespace: str = "forge-engine"
    k8s_job_ttl_seconds: int = 3600
    k8s_job_timeout_seconds: int = 300

    # Adapters
    default_adapter: str = "kubernetes-job"

    model_config = {"env_prefix": "FW_", "env_file": ".env"}


settings = Settings()
