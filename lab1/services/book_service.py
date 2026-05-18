from __future__ import annotations

from typing import Optional
from uuid import UUID

from models.book import BookStatus
from repository.book_repository import BookRepository, book_repository


class BookService:
    def __init__(self, repo: BookRepository = book_repository) -> None:
        self._repo = repo

    async def list_books(
        self,
        *,
        author: Optional[str] = None,
        status: Optional[BookStatus] = None,
        sort_by: Optional[str] = None,
        order: str = "asc",
    ) -> list[dict]:
        return await self._repo.list_all(
            author=author,
            status=status,
            sort_by=sort_by,
            order=order,
        )

    async def get_book(self, book_id: UUID) -> Optional[dict]:
        return await self._repo.get_by_id(book_id)

    async def create_book(self, data: dict) -> dict:
        return await self._repo.create(data)

    async def delete_book(self, book_id: UUID) -> bool:
        return await self._repo.delete(book_id)


book_service = BookService()
