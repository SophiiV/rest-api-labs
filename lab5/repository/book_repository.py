from threading import Lock
from typing import Optional

from models.book import Book


class BookRepository:

    def __init__(self) -> None:
        self._items: dict[int, Book] = {}
        self._next_id: int = 1
        self._lock = Lock()

    def list_all(self) -> list[Book]:
        with self._lock:
            return [self._items[k] for k in sorted(self._items.keys())]

    def get(self, book_id: int) -> Optional[Book]:
        with self._lock:
            return self._items.get(book_id)

    def add(self, title: str, author: str, year: int,
            description: Optional[str] = None) -> Book:
        with self._lock:
            book = Book(
                id=self._next_id,
                title=title,
                author=author,
                year=year,
                description=description,
            )
            self._items[self._next_id] = book
            self._next_id += 1
            return book

    def update(self, book_id: int, title: str, author: str, year: int,
               description: Optional[str] = None) -> Optional[Book]:
        with self._lock:
            if book_id not in self._items:
                return None
            book = Book(
                id=book_id,
                title=title,
                author=author,
                year=year,
                description=description,
            )
            self._items[book_id] = book
            return book

    def delete(self, book_id: int) -> bool:
        with self._lock:
            return self._items.pop(book_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._next_id = 1


book_repository = BookRepository()
