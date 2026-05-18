import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://library_user:library_pass@db:5432/library_db",
)


engine = create_async_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовий клас для всіх ORM-моделей (таблиць)."""
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI — віддає сесію БД і автоматично закриває її.

    Використання в ендпоінті:
        async def endpoint(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Створює всі таблиці з ORM-моделей (якщо їх ще нема).
    Викликається один раз при старті застосунку.
    """
    from models.book import Book  # noqa: F401
    from models.user import RefreshToken, User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
