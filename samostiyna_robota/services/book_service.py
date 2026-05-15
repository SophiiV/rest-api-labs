"""
Service шар — бізнес-логіка застосунку.

Відокремлений від API й від Repository, щоб:
  - API-шар не знав нічого про MongoDB
  - Repository не знав нічого про HTTP / Pydantic
  - Можна було легко підмінити MongoDB на іншу БД і переписати лише repository
"""
from typing import List, Optional, Tuple

from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookStatus


class BookService:
    """Бізнес-логіка роботи з книгами."""

    def __init__(self, repository: BookRepository) -> None:
        self.repository = repository

    async def get_all_books(
        self,
        limit: int,
        offset: int,
        status: Optional[BookStatus] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """
        Отримати сторінку книг (Limit-Offset).

        Повертає пару (список_документів, total).
        """
        status_value = status.value if status is not None else None
        return await self.repository.list_books(
            limit=limit,
            offset=offset,
            status=status_value,
            author=author,
            sort_by=sort_by,
        )

    async def get_book_by_id(self, book_id: str) -> Optional[dict]:
        """Знайти одну книгу або None."""
        return await self.repository.get_by_id(book_id)

    async def create_book(self, data: BookCreate) -> dict:
        """Створити нову книгу з валідованих даних."""
        return await self.repository.add(
            title=data.title,
            author=data.author,
            year=data.year,
            status=data.status.value,
            description=data.description,
        )

    async def delete_book(self, book_id: str) -> bool:
        """
        Видалити книгу. Повертає True якщо щось видалили, False якщо не було.
        Операція ідемпотентна — викликаючий завжди отримає успіх (204) незалежно від результату.
        """
        return await self.repository.delete(book_id)
