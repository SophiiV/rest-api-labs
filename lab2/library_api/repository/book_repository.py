
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.book import Book


class BookRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_books(
        self,
        limit: int,
        offset: int,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[Book], int]:

        query = select(Book)

        if status is not None:
            query = query.where(Book.status == status)

        if author is not None:
            query = query.where(func.lower(Book.author).contains(author.lower()))

        if sort_by == "title":
            query = query.order_by(func.lower(Book.title))
        elif sort_by == "year":
            query = query.order_by(Book.year)
        else:

            query = query.order_by(Book.created_at)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        books = list(result.scalars().all())

        return books, total

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        """Знайти одну книгу за UUID. Повертає None якщо нема."""
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, book: Book) -> Book:
        """Додати нову книгу, повернути її з заповненим id/created_at."""
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: str) -> None:
        """
        Видалити книгу. Ідемпотентна операція:
        якщо книги нема — просто нічого не робимо, без помилки.
        """
        book = await self.get_by_id(book_id)
        if book is not None:
            await self.session.delete(book)
            await self.session.commit()
