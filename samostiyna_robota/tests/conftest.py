"""
Спільна конфігурація pytest для всіх тестів Лаб4.

Підміна залежностей:
  Замість реальної MongoDB ми використовуємо mongomock-motor — in-memory
  симулятор MongoDB з тим самим API (motor-сумісний). Це дозволяє запускати
  тести миттєво, без Docker і без реального mongod.

Як це працює:
  1) Створюємо AsyncMongoMockClient у пам'яті
  2) Override dependency get_books_collection → повертаємо колекцію мок-клієнта
  3) Перед кожним тестом чистимо колекцію (drop), щоб тести не впливали один на одного
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from database import get_books_collection
from main import app


# ----------------------------------------------------------------------
# Mock-клієнт Mongo. Створюється ОДИН раз на всю сесію тестів.
# ----------------------------------------------------------------------
mock_client = AsyncMongoMockClient()
mock_db = mock_client["test_library"]


def override_get_books_collection():
    """Підміна реальної dependency: віддаємо колекцію з in-memory мок-Mongo."""
    return mock_db["books"]


# Підмінюємо залежність в FastAPI один раз на весь набір тестів.
app.dependency_overrides[get_books_collection] = override_get_books_collection


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю сесію тестів — вимога pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def reset_collection():
    """
    Перед кожним тестом дропаємо колекцію books.
    Це гарантує, що тести не впливають один на одного.
    """
    await mock_db["books"].delete_many({})
    yield
    await mock_db["books"].delete_many({})


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Асинхронний HTTP-клієнт, що ганяє запити прямо в ASGI-застосунок."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
