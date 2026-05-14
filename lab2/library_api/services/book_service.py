
from typing import List, Optional, Tuple

from models.book import Book
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookStatus


class BookService:

    def __init__(self, repository: BookRepository) -> None:
        self.repository = repository

    async def get_all_books(
        self,
        limit: int,
        offset: int,
        status: Optional[BookStatus] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[Book], int]:

        status_value = status.value if status is not None else None
        return await self.repository.list_books(
            limit=limit,
            offset=offset,
            status=status_value,
            author=author,
            sort_by=sort_by,
        )

    async def get_book_by_id(self, book_id: str) -> Optional[Book]:
        return await self.repository.get_by_id(book_id)

    async def create_book(self, data: BookCreate) -> Book:
        book = Book(
            title=data.title,
            author=data.author,
            description=data.description,
            status=data.status.value,
            year=data.year,
        )
        return await self.repository.add(book)

    async def delete_book(self, book_id: str) -> None:
        await self.repository.delete(book_id)
