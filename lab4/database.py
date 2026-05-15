import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mongo_admin:password@mongo:27017",
)

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "library_db")
BOOKS_COLLECTION = "books"


class _MongoState:
    """Holds Mongo client and database instance."""
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


_state = _MongoState()


async def connect_to_mongo() -> None:
    """Initialize Mongo connection on app startup."""
    _state.client = AsyncIOMotorClient(MONGO_URL)
    _state.db = _state.client[MONGO_DB_NAME]


async def close_mongo_connection() -> None:
    """Close Mongo connection on shutdown."""
    if _state.client is not None:
        _state.client.close()
        _state.client = None
        _state.db = None


def get_books_collection() -> AsyncIOMotorCollection:
    """FastAPI dependency that returns books collection."""
    if _state.db is None:
        raise RuntimeError("MongoDB is not initialized.")
    return _state.db[BOOKS_COLLECTION]