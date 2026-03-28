import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Disable webhook secret requirement for tests
os.environ["FW_REQUIRE_WEBHOOK_SECRETS"] = "false"

from app.main import app  # noqa: E402


@pytest.fixture
def mock_kafka_publish():
    """Mock the Kafka producer so tests don't need a broker."""
    with patch("app.producer._producer") as mock_prod, \
         patch("app.producer.publish", new_callable=AsyncMock, return_value=True), \
         patch("app.producer.is_connected", return_value=True):
        mock_prod._closed = False
        yield


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
