"""
Налаштування підключення до MongoDB через motor (асинхронний драйвер).

Тут ми:
  - Створюємо асинхронний клієнт Mongo (AsyncIOMotorClient)
  - Віддаємо конкретну колекцію books через dependency FastAPI
  - Тримаємо з'єднання живим на весь час життя застосунку

Чому motor, а не pymongo?
  pymongo — синхронний драйвер (блокує event loop FastAPI).
  motor — офіційна async-обгортка Mongo від MongoDB Inc.
  API майже ідентичне, тільки await перед викликами.
"""
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


# ------------------------------------------------------------------
# URL підключення до Mongo беремо зі змінної оточення MONGO_URL.
# Якщо її нема (наприклад, запустили локально без Docker) —
# використовуємо значення для docker-compose.
#
# Формат: mongodb://<user>:<password>@<host>:<port>
# ------------------------------------------------------------------
MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mongo_admin:password@mongo:27017",
)

# Назва бази даних та колекції.
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "library_db")
BOOKS_COLLECTION = "books"


# ------------------------------------------------------------------
# Глобальний клієнт — один на весь застосунок.
# AsyncIOMotorClient сам тримає пул з'єднань, тому плодити клієнтів
# не треба. Ініціалізуємо у lifespan-хуці FastAPI.
# ------------------------------------------------------------------
class _MongoState:
    """Простенький контейнер для клієнта та бази (щоб не було глобальних змінних)."""
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


_state = _MongoState()


async def connect_to_mongo() -> None:
    """
    Під'єднатися до Mongo. Викликається один раз при старті застосунку.

    AsyncIOMotorClient не робить реального коннекту тут — він ліниво
    відкриє його під час першої операції. Це нормально і швидко.
    """
    _state.client = AsyncIOMotorClient(MONGO_URL)
    _state.db = _state.client[MONGO_DB_NAME]


async def close_mongo_connection() -> None:
    """Закрити клієнт при завершенні застосунку."""
    if _state.client is not None:
        _state.client.close()
        _state.client = None
        _state.db = None


def get_books_collection() -> AsyncIOMotorCollection:
    """
    Dependency для FastAPI — віддає колекцію books.

    Використання в ендпоінті / фабриці репозиторію:
        def get_repo(col: AsyncIOMotorCollection = Depends(get_books_collection)):
            return BookRepository(col)
    """
    if _state.db is None:
        raise RuntimeError(
            "MongoDB не ініціалізовано. Переконайся, що lifespan-хук "
            "у main.py викликає connect_to_mongo()."
        )
    return _state.db[BOOKS_COLLECTION]
