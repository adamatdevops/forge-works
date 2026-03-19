from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "webhook-gateway"
    app_version: str = "0.1.0"
    debug: bool = False
    port: int = 8080

    # Kafka
    kafka_bootstrap_servers: str = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092"
    kafka_client_id: str = "webhook-gateway"
    kafka_acks: str = "all"
    kafka_retries: int = 3
    kafka_request_timeout_ms: int = 10000

    # Topic mapping
    kafka_topic_github: str = "forge.events.github"
    kafka_topic_argocd: str = "forge.events.argocd"
    kafka_topic_kubernetes: str = "forge.events.kubernetes"
    kafka_topic_dlq: str = "forge.dlq.events"

    # Webhook secrets
    github_webhook_secret: str = ""
    argocd_webhook_secret: str = ""
    kubernetes_webhook_token: str = ""

    model_config = {"env_prefix": "FW_", "env_file": ".env"}

    def topic_for_source(self, source: str) -> str | None:
        mapping = {
            "github": self.kafka_topic_github,
            "argocd": self.kafka_topic_argocd,
            "kubernetes": self.kafka_topic_kubernetes,
        }
        return mapping.get(source)


settings = Settings()
