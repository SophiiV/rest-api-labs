"""
API шар — HTTP-ендпоінти для роботи з книгами.

Відповідальність:
  - Декларація URL і HTTP-методів
  - Валідація Query/Path/Body через Pydantic і FastAPI
  - Делегування логіки сервісу
  - Перетворення результатів на HTTP-відповіді (200/201/204/400/404/422)

Repository підкидається через FastAPI Depends — таким чином
це легко підмінити в тестах (див. tests/conftest.py).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorCollection

from database import get_books_collection
from models.book import book_doc_to_dict
from repository.book_repository import BookRepository, InvalidBookIdError
from schemas.book import BookCreate, BookResponse, BookStatus, PaginatedBooks
from services.book_service import BookService

router = APIRouter()


# ----------------------------------------------------------------------
# Dependency-фабрики — будують репозиторій і сервіс для кожного запиту.
#
# Depends(get_books_collection) підкинеться FastAPI-ем автоматично,
# а get_book_service — використовується прямо в ендпоінті.
# ----------------------------------------------------------------------
def get_book_repository(
    collection: AsyncIOMotorCollection = Depends(get_books_collection),
) -> BookRepository:
    """Створити BookRepository з уже готовою колекцією Mongo."""
    return BookRepository(collection)


def get_book_service(
    repository: BookRepository = Depends(get_book_repository),
) -> BookService:
    """Створити BookService поверх BookRepository."""
    return BookService(repository)


# ----------------------------------------------------------------------
# GET /books — список книг з Limit-Offset пагінацією, фільтрами та сортуванням.
# ----------------------------------------------------------------------
@router.get(
    "/books",
    response_model=PaginatedBooks,
    status_code=status.HTTP_200_OK,
    summary="Отримати список книг (з Limit-Offset пагінацією)",
)
async def get_all_books(
    # Пагінація
    limit: int = Query(10, ge=1, le=100, description="Скільки елементів повернути (1-100)"),
    offset: int = Query(0, ge=0, description="Скільки елементів пропустити з початку"),
    # Фільтри
    status_filter: Optional[BookStatus] = Query(None, alias="status", description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору (часткове співпадіння, регістронезалежно)"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$", description="Сортування: title або year"),
    service: BookService = Depends(get_book_service),
) -> PaginatedBooks:
    docs, total = await service.get_all_books(
        limit=limit,
        offset=offset,
        status=status_filter,
        author=author,
        sort_by=sort_by,
    )
    return PaginatedBooks(
        items=[BookResponse.model_validate(book_doc_to_dict(d)) for d in docs],
        total=total,
        limit=limit,
        offset=offset,
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
    try:
        doc = await service.get_book_by_id(book_id)
    except InvalidBookIdError as exc:
        # Некоректний формат id → 400, а не 404 (семантично правильніше).
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книгу з id={book_id} не знайдено",
        )
    return BookResponse.model_validate(book_doc_to_dict(doc))


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
    doc = await service.create_book(book_data)
    return BookResponse.model_validate(book_doc_to_dict(doc))


# ----------------------------------------------------------------------
# DELETE /books/{book_id} — видалити книгу (ідемпотентна).
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
    try:
        await service.delete_book(book_id)
    except InvalidBookIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # Ігноруємо deleted_count — ідемпотентність: двічі видалена книга → все одно 204.
    return None
