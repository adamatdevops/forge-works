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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop Kafka producer with the application lifecycle."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
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
