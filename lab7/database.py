import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# формат: postgresql+asyncpg://<user>:<password>@<host>:<port>/<db_name>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://library_user:library_pass@db:5432/library_db",
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# expire_on_commit=False — щоб об'єкти залишались доступними після commit
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    # імпорти тут, щоб SQLAlchemy побачила всі моделі перед create_all
    from models.book import Book  # noqa: F401
    from models.user import RefreshToken, User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
