from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse, BookStatus, PaginatedBooks
from services.book_service import BookService

router = APIRouter()


def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    """Створити BookService з вже відкритою сесією БД."""
    return BookService(BookRepository(session))


@router.get(
    "/books",
    response_model=PaginatedBooks,
    status_code=status.HTTP_200_OK,
    summary="Отримати список книг (з Limit-Offset пагінацією)",
)
async def get_all_books(
    # Пагінація
    limit: int = Query(10, ge=1, le=100, description="Скільки елементів повернути (1-100)"),
    offset: int = Query(0, ge=0, description="Скільки елементів пропустити (>= 0)"),
    # Фільтри
    status_filter: Optional[BookStatus] = Query(None, alias="status", description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору (часткове співпадіння)"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$", description="Сортування: title або year"),
    service: BookService = Depends(get_book_service),
) -> PaginatedBooks:
    books, total = await service.get_all_books(
        limit=limit,
        offset=offset,
        status=status_filter,
        author=author,
        sort_by=sort_by,
    )
    return PaginatedBooks(
        items=[BookResponse.model_validate(b) for b in books],
        total=total,
        limit=limit,
        offset=offset,
    )


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
