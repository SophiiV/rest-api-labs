from typing import List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from models.book import build_book_document


class InvalidBookIdError(Exception):
    """Клієнт передав рядок, який не є валідним ObjectId."""


def _parse_object_id(book_id: str) -> ObjectId:
    """Перетворити рядок у ObjectId."""
    try:
        return ObjectId(book_id)
    except (InvalidId, TypeError) as exc:
        raise InvalidBookIdError(f"Некоректний id книги: {book_id!r}") from exc


class BookRepository:
    """CRUD-операції над колекцією books."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    async def list_books(
        self,
        limit: int,
        offset: int,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[dict], int]:

        query: dict = {}

        if status is not None:
            query["status"] = status

        if author is not None:
            import re

            query["author"] = {
                "$regex": re.escape(author),
                "$options": "i"
            }

        total = await self.collection.count_documents(query)

        if sort_by == "title":
            sort_field = "title"
        elif sort_by == "year":
            sort_field = "year"
        else:
            sort_field = "created_at"

        cursor = (
            self.collection.find(query)
            .sort([(sort_field, 1), ("_id", 1)])
            .skip(offset)
            .limit(limit)
        )

        docs = await cursor.to_list(length=None)

        return docs, total

    async def get_by_id(self, book_id: str) -> Optional[dict]:
        """Знайти одну книгу за id."""
        oid = _parse_object_id(book_id)

        doc = await self.collection.find_one({"_id": oid})

        return doc

    async def add(
        self,
        title: str,
        author: str,
        year: int,
        status: str,
        description: Optional[str],
    ) -> dict:
        """Додати нову книгу."""

        doc = build_book_document(
            title=title,
            author=author,
            year=year,
            status=status,
            description=description,
        )

        result = await self.collection.insert_one(doc)

        doc["_id"] = result.inserted_id

        return doc

    async def update(
        self,
        book_id: str,
        title: str,
        author: str,
        year: int,
        status: str,
        description: Optional[str],
    ) -> Optional[dict]:
        """Повністю оновити книгу."""

        oid = _parse_object_id(book_id)

        updated_doc = await self.collection.find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    "title": title,
                    "author": author,
                    "description": description,
                    "status": status,
                    "year": year,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        return updated_doc

    async def delete(self, book_id: str) -> bool:
        """Видалити книгу."""

        oid = _parse_object_id(book_id)

        result = await self.collection.delete_one({"_id": oid})

        return result.deleted_count > 0