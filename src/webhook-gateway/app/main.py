import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import producer
from app.config import settings
from app.middleware import CorrelationIDMiddleware
from app.routes import health, webhooks

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _validate_secrets():
    """Fail-closed: refuse to start without webhook secrets unless explicitly disabled."""
    if not settings.require_webhook_secrets:
        logger.warning("Webhook secret validation DISABLED (dev mode)")
        return
    missing = []
    if not settings.github_webhook_secret:
        missing.append("FW_GITHUB_WEBHOOK_SECRET")
    if not settings.argocd_webhook_secret:
        missing.append("FW_ARGOCD_WEBHOOK_SECRET")
    if not settings.kubernetes_webhook_token:
        missing.append("FW_KUBERNETES_WEBHOOK_TOKEN")
    if missing:
        raise RuntimeError(
            f"Webhook secrets required but not set: {', '.join(missing)}. "
            "Set FW_REQUIRE_WEBHOOK_SECRETS=false to disable (dev only)."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop Kafka producer with the application lifecycle."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    _validate_secrets()
    await producer.start_producer()
    yield
    await producer.stop_producer()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(CorrelationIDMiddleware)
app.include_router(health.router)
app.include_router(webhooks.router)
