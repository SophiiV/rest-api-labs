 
import base64
import json
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from models.book import Book


 
class InvalidCursorError(Exception):
    """Поганий cursor (неможливо декодувати)."""


def encode_cursor(sort_value, book_id: str) -> str:
    """Закодувати (sort_value, id) у base64-рядок."""
    # datetime -> ISO-рядок для серіалізації в JSON
    if isinstance(sort_value, datetime):
        sort_value = sort_value.isoformat()
    payload = json.dumps({"v": sort_value, "id": book_id}, ensure_ascii=False)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> Tuple[object, str]:
    """Розкодувати cursor назад у (sort_value, id). Кидає InvalidCursorError."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        return data["v"], data["id"]
    except Exception as exc:  # noqa: BLE001
        raise InvalidCursorError(f"Некоректний cursor: {cursor!r}") from exc


class BookRepository:
    """CRUD-операції над таблицею books з cursor-based пагінацією."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    async def list_books(
        self,
        limit: int,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[Book], Optional[str]]:

        # 1) Визначаємо поле сортування.
        if sort_by == "title":
            sort_column = Book.title
            get_sort_value = lambda b: b.title  # noqa: E731
        elif sort_by == "year":
            sort_column = Book.year
            get_sort_value = lambda b: b.year  # noqa: E731
        else:
            sort_column = Book.created_at
            get_sort_value = lambda b: b.created_at  # noqa: E731
 
        query = select(Book).order_by(sort_column.asc(), Book.id.asc())

        # 3) Фільтри (status/author)
        if status is not None:
            query = query.where(Book.status == status)
        if author is not None:
            query = query.where(func.lower(Book.author).contains(author.lower()))

        # 4) Застосовуємо cursor — "покажи все, що ПІСЛЯ (cursor_value, cursor_id)".
        if cursor:
            last_value, last_id = decode_cursor(cursor)
            # Якщо сортуємо по created_at — перетворюємо ISO-рядок назад у datetime
            if sort_by is None and isinstance(last_value, str):
                try:
                    last_value = datetime.fromisoformat(last_value)
                except ValueError as exc:
                    raise InvalidCursorError("Cursor містить нечитабельну дату") from exc

            query = query.where(tuple_(sort_column, Book.id) > tuple_(last_value, last_id))

        # 5) Беремо на 1 запис більше, щоб визначити чи є наступна сторінка.
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        # 6) Формуємо next_cursor.
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = encode_cursor(get_sort_value(last), last.id)
        else:
            next_cursor = None

        return rows, next_cursor

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        """Знайти одну книгу за UUID. Повертає None якщо нема."""
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # WRITE

    async def add(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: str) -> None:
        book = await self.get_by_id(book_id)
        if book is not None:
            await self.session.delete(book)
            await self.session.commit()
