"""
Конфігурація pytest:
- БД підмінена на SQLite in-memory (через aiosqlite)
- Rate-limiter за замовчуванням вимкнений (тестує test_rate_limit.py)
- Між тестами таблиці скидаються і створюються заново
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import database as db_module  # noqa: F401
from api.dependencies import rate_limit
from database import Base, get_session
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


async def _noop_rate_limit() -> None:
    return None


app.dependency_overrides[rate_limit] = _noop_rate_limit


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    from models.book import Book  # noqa: F401
    from models.user import RefreshToken, User  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_tokens(client: AsyncClient) -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert r.status_code == 201, f"Register failed: {r.json()}"

    r = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert r.status_code == 200, f"Login failed: {r.json()}"
    return r.json()


@pytest_asyncio.fixture
async def auth_headers(auth_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest_asyncio.fixture
async def authed_client(
    client: AsyncClient, auth_headers: dict
) -> AsyncGenerator[AsyncClient, None]:
    client.headers.update(auth_headers)
    yield client
