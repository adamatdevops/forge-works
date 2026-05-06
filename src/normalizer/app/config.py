from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "normalizer"
    app_version: str = "0.1.0"
    debug: bool = False
    port: int = 8095

    # Kafka
    kafka_bootstrap_servers: str = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
    kafka_consumer_group: str = "forgeworks-normalizer"
    kafka_input_topic: str = "forge.events.kubernetes"
    kafka_output_topic: str = "forge.config.normalized"
    kafka_dlq_topic: str = "forge.dlq.events"

    # Per-source pod isolation. Empty = no enforcement (backward-compat).
    expected_source: str = ""

    # Redis (DB 1 — separate from model cache DB 0)
    redis_host: str = "forge-redis.forge-engine.svc"
    redis_password: str = ""
    redis_db: int = 1
    redis_ttl_seconds: int = 1800  # 30 min

    # S3
    s3_bucket: str = "fw-state-dev"
    s3_prefix: str = "normalizer/configs"

    # Security
    internal_api_token: str = ""

    model_config = {"env_prefix": "FW_", "env_file": ".env"}


settings = Settings()
