"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "ForgeWorks"
    app_version: str = "0.4.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_prefix: str = "/api"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/forgedb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security / JWT
    secret_key: str = "change-me-in-production-use-secrets-for-real-key"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # ML Model
    ml_model_path: str = "models/template_recommender.pkl"
    ml_confidence_threshold: float = 0.7

    # GitHub Integration
    github_token: str | None = None
    github_org: str = "forge-org"
    github_adapter_mode: str = "mock"  # "mock" or "live"
    github_api_url: str = "https://api.github.com"

    # ArgoCD Integration
    argocd_server: str | None = None
    argocd_token: str | None = None
    argocd_adapter_mode: str = "mock"  # "mock" or "live"

    # Kubernetes Integration
    kubernetes_adapter_mode: str = "mock"  # "mock" or "live"
    kubernetes_kubeconfig: str | None = None  # Path to kubeconfig file
    kubernetes_context: str | None = None  # Kubernetes context to use
    kubernetes_in_cluster: bool = False  # Whether running inside K8s cluster


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    if s.environment != "development" and s.secret_key == "change-me-in-production-use-secrets-for-real-key":
        raise ValueError(
            "SECRET_KEY must be set via environment variable in non-development environments. "
            "Do not use the default value in production."
        )
    return s


settings = get_settings()
