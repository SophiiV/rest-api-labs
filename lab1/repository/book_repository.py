
from itertools import count
from threading import Lock
from typing import Optional


class BookRepository:
 
    def __init__(self) -> None:
        self._books: dict[int, dict] = {}
        self._id_counter = count(start=1)
        self._lock = Lock()


    def list_all(self) -> list[dict]:
      
        with self._lock:
            return list(self._books.values())

    def get_by_id(self, book_id: int) -> Optional[dict]:
        
        with self._lock:
            return self._books.get(book_id)


    def create(self, data: dict) -> dict:
        """Створити нову книгу."""
        with self._lock:
            new_id = next(self._id_counter)
            book = {"id": new_id, **data}
            self._books[new_id] = book
            return book

    def update(self, book_id: int, data: dict) -> Optional[dict]:
        """Повністю замінити поля книги
        """
        with self._lock:
            if book_id not in self._books:
                return None
            updated = {"id": book_id, **data}
            self._books[book_id] = updated
            return updated

    def delete(self, book_id: int) -> bool:
        """Видалити книгу. Повертає True якщо видалено, False якщо її не було.

        Видалення за id ідемпотентне: повторний DELETE поверне 404,
        стан системи при цьому не змінюється — як і вимагає REST.
        """
        with self._lock:
            return self._books.pop(book_id, None) is not None


# імітує "базу" впродовж життя процесу.
book_repository = BookRepository()
