import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from database import get_books_collection
from main import app


mock_client = AsyncMongoMockClient()
mock_db = mock_client["test_library"]


def override_get_books_collection():
    """Dependency override: in-memory Mongo collection."""
    return mock_db["books"]


app.dependency_overrides[get_books_collection] = override_get_books_collection


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def reset_collection():
    """Clear collection before each test."""
    await mock_db["books"].delete_many({})
    yield
    await mock_db["books"].delete_many({})


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c