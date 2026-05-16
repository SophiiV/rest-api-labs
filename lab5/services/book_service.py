from typing import Optional

from models.book import Book
from repository.book_repository import book_repository


class BookService:

    def __init__(self, repo=book_repository) -> None:
        self._repo = repo

    def list_books(self) -> list[Book]:
        return self._repo.list_all()

    def get_book(self, book_id: int) -> Optional[Book]:
        return self._repo.get(book_id)

    def create_book(self, data: dict) -> Book:
        return self._repo.add(
            title=data["title"],
            author=data["author"],
            year=data["year"],
            description=data.get("description"),
        )

    def update_book(self, book_id: int, data: dict) -> Optional[Book]:
        return self._repo.update(
            book_id=book_id,
            title=data["title"],
            author=data["author"],
            year=data["year"],
            description=data.get("description"),
        )

    def delete_book(self, book_id: int) -> bool:
        return self._repo.delete(book_id)


book_service = BookService()
