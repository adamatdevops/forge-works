import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters import registry
from app.adapters.kubernetes_job import KubernetesJobAdapter
from app.config import settings
from app.dispatcher import JobDispatcher
from app.routes import health

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

dispatcher = JobDispatcher()
health.set_dispatcher(dispatcher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start dispatcher and adapters."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    # Register adapters
    k8s_adapter = KubernetesJobAdapter()
    registry.register(k8s_adapter)
    registry.set_default("kubernetes-job")

    # Start dispatcher
    await dispatcher.start()

    # Run dispatch loop in background
    dispatch_task = asyncio.create_task(dispatcher.run())

    yield

    # Shutdown
    await dispatcher.stop()
    dispatch_task.cancel()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health.router)
