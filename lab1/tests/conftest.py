from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from repository.book_repository import book_repository


@pytest_asyncio.fixture(autouse=True)
async def reset_repo():
    await book_repository._reset()
    yield
    await book_repository._reset()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
