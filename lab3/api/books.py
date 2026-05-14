"""
API шар — HTTP-ендпоінти.

Тут:
  - Декларуємо шляхи (URL)
  - Беремо параметри з URL / тіла запиту
  - Делегуємо роботу сервісу
  - Мапимо результат на HTTP-відповідь (коди 200/201/204/400/404)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repository.book_repository import BookRepository, InvalidCursorError
from schemas.book import BookCreate, BookResponse, BookStatus, CursorPaginatedBooks
from services.book_service import BookService

router = APIRouter()


# ----------------------------------------------------------------------
# Dependency-фабрика — будує сервіс для кожного запиту.
# ----------------------------------------------------------------------
def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    """Створити BookService з вже відкритою сесією БД."""
    return BookService(BookRepository(session))


# ----------------------------------------------------------------------
# GET /books — список книг з CURSOR-пагінацією, фільтрами та сортуванням.
# ----------------------------------------------------------------------
@router.get(
    "/books",
    response_model=CursorPaginatedBooks,
    status_code=status.HTTP_200_OK,
    summary="Отримати список книг (з Cursor-based пагінацією)",
)
async def get_all_books(
    # Пагінація
    limit: int = Query(10, ge=1, le=100, description="Скільки елементів повернути (1-100)"),
    cursor: Optional[str] = Query(
        None,
        description="Токен наступної сторінки. ",
    ),
    # Фільтри
    status_filter: Optional[BookStatus] = Query(None, alias="status", description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору (часткове співпадіння)"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$", description="Сортування: title або year"),
    service: BookService = Depends(get_book_service),
) -> CursorPaginatedBooks:
    try:
        books, next_cursor = await service.get_all_books(
            limit=limit,
            cursor=cursor,
            status=status_filter,
            author=author,
            sort_by=sort_by,
        )
    except InvalidCursorError as exc:
        # Некоректний cursor → 400 Bad Request (валідаційна помилка).
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return CursorPaginatedBooks(
        items=[BookResponse.model_validate(b) for b in books],
        limit=limit,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


# ----------------------------------------------------------------------
# GET /books/{book_id} — отримати одну книгу за ID.
# ----------------------------------------------------------------------
@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати книгу за ID",
)
async def get_book_by_id(
    book_id: str,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    book = await service.get_book_by_id(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книгу з id={book_id} не знайдено",
        )
    return BookResponse.model_validate(book)


# ----------------------------------------------------------------------
# POST /books — створити нову книгу.
# ----------------------------------------------------------------------
@router.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову книгу",
)
async def create_book(
    book_data: BookCreate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    book = await service.create_book(book_data)
    return BookResponse.model_validate(book)


# ----------------------------------------------------------------------
# DELETE /books/{book_id} — видалити книгу (ідемпотентно).
# ----------------------------------------------------------------------
@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити книгу (ідемпотентна операція)",
)
async def delete_book(
    book_id: str,
    service: BookService = Depends(get_book_service),
) -> None:
    await service.delete_book(book_id)
    return None
