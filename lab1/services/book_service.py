
from typing import Optional

from repository.book_repository import BookRepository, book_repository


class BookService:

    def __init__(self, repo: BookRepository = book_repository) -> None:
        self._repo = repo

    def list_books(self) -> list[dict]:
        return self._repo.list_all()

    def get_book(self, book_id: int) -> Optional[dict]:
        return self._repo.get_by_id(book_id)

    def create_book(self, data: dict) -> dict:
        return self._repo.create(data)

    def update_book(self, book_id: int, data: dict) -> Optional[dict]:
        return self._repo.update(book_id, data)

    def delete_book(self, book_id: int) -> bool:
        return self._repo.delete(book_id)


book_service = BookService()
