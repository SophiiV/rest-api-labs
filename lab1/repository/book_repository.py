from __future__ import annotations

import asyncio
from typing import Optional
from uuid import UUID, uuid4

from models.book import BookStatus


class BookRepository:
    def __init__(self) -> None:
        self._books: list[dict] = []
        self._lock = asyncio.Lock()

    async def list_all(
        self,
        *,
        author: Optional[str] = None,
        status: Optional[BookStatus] = None,
        sort_by: Optional[str] = None,
        order: str = "asc",
    ) -> list[dict]:
        async with self._lock:
            result = list(self._books)

        if author is not None:
            author_lower = author.strip().lower()
            result = [b for b in result if b["author"].lower() == author_lower]

        if status is not None:
            status_value = status.value if isinstance(status, BookStatus) else status
            result = [b for b in result if b["status"] == status_value]

        if sort_by in {"title", "year"}:
            reverse = order == "desc"
            key = (lambda b: b[sort_by].lower()) if sort_by == "title" else (lambda b: b[sort_by])
            result.sort(key=key, reverse=reverse)

        return result

    async def get_by_id(self, book_id: UUID) -> Optional[dict]:
        async with self._lock:
            for book in self._books:
                if book["id"] == book_id:
                    return dict(book)
        return None

    async def create(self, data: dict) -> dict:
        async with self._lock:
            new_book = {
                "id": uuid4(),
                "title": data["title"],
                "author": data["author"],
                "description": data.get("description"),
                "year": data["year"],
                "status": data.get("status", BookStatus.AVAILABLE.value),
            }
            if isinstance(new_book["status"], BookStatus):
                new_book["status"] = new_book["status"].value
            self._books.append(new_book)
            return dict(new_book)

    async def delete(self, book_id: UUID) -> bool:
        async with self._lock:
            for i, book in enumerate(self._books):
                if book["id"] == book_id:
                    del self._books[i]
                    return True
        return False

    async def _reset(self) -> None:
        async with self._lock:
            self._books.clear()


book_repository = BookRepository()
