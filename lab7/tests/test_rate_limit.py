"""
Тести для Rate Limiter-а.

Redis замокований через AsyncMock — реальний Redis не потрібен.
redis.incr() повертає поточний лічильник: якщо > ліміт → 429.

Кейси:
  1. Анонім, лічильник=1 (ліміт 2)  → 200
  2. Анонім, лічильник=3 (ліміт 2)  → 429
  3. Авторизований, лічильник=5 (ліміт 10) → 200
  4. Авторизований, лічильник=11 (ліміт 10) → 429
"""
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient

from api.dependencies import get_redis, rate_limit
from main import app

BASE_URL = "/api/v1/books"


@pytest_asyncio.fixture
async def with_rate_limit():
    """Тимчасово вмикає реальний rate_limit (у conftest він вимкнений)."""
    saved = app.dependency_overrides.pop(rate_limit, None)
    yield
    if saved is not None:
        app.dependency_overrides[rate_limit] = saved


def make_redis_mock(incr_returns: int) -> AsyncMock:
    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=incr_returns)
    redis_mock.expire = AsyncMock(return_value=True)
    return redis_mock


@pytest.mark.asyncio
async def test_anonymous_under_limit_returns_200(
    client: AsyncClient, with_rate_limit
):
    """Анонім, 1-й запит у вікні (ліміт 2) → 200."""
    redis_mock = make_redis_mock(incr_returns=1)
    app.dependency_overrides[get_redis] = lambda: redis_mock
    try:
        response = await client.get(BASE_URL)
        assert response.status_code == 200
        redis_mock.incr.assert_awaited_once()
        redis_mock.expire.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_redis, None)


@pytest.mark.asyncio
async def test_anonymous_over_limit_returns_429(
    client: AsyncClient, with_rate_limit
):
    """Анонім, 3-й запит у вікні (ліміт 2) → 429."""
    redis_mock = make_redis_mock(incr_returns=3)
    app.dependency_overrides[get_redis] = lambda: redis_mock
    try:
        response = await client.get(BASE_URL)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "2/хв" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_redis, None)


@pytest.mark.asyncio
async def test_authenticated_under_limit_returns_200(
    authed_client: AsyncClient, with_rate_limit
):
    """Авторизований, 5-й запит у вікні (ліміт 10) → 200."""
    redis_mock = make_redis_mock(incr_returns=5)
    app.dependency_overrides[get_redis] = lambda: redis_mock
    try:
        response = await authed_client.get(BASE_URL)
        assert response.status_code == 200
        redis_mock.incr.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_redis, None)


@pytest.mark.asyncio
async def test_authenticated_over_limit_returns_429(
    authed_client: AsyncClient, with_rate_limit
):
    """Авторизований, 11-й запит у вікні (ліміт 10) → 429."""
    redis_mock = make_redis_mock(incr_returns=11)
    app.dependency_overrides[get_redis] = lambda: redis_mock
    try:
        response = await authed_client.get(BASE_URL)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "10/хв" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_redis, None)
