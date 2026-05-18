from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from models.book import BookSortField, BookStatus
from schemas.book import BookCreate, BookRead
from services.book_service import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "",
    response_model=list[BookRead],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі книги",
    description=(
        "Повертає список усіх книг. "
        "Можна фільтрувати по `author` та `status`, "
        "сортувати по `title` або `year` у напрямку `asc` / `desc`."
    ),
)
async def list_books(
    author: Optional[str] = Query(
        default=None,
        description="Фільтр по автору (точний збіг, регістр не враховується).",
    ),
    book_status: Optional[BookStatus] = Query(
        default=None,
        alias="status",
        description="Фільтр по статусу: 'available' або 'borrowed'.",
    ),
    sort_by: Optional[BookSortField] = Query(
        default=None,
        description="Поле для сортування: 'title' або 'year'.",
    ),
    order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Напрямок сортування: 'asc' або 'desc'.",
    ),
) -> list[BookRead]:
    books = await book_service.list_books(
        author=author,
        status=book_status,
        sort_by=sort_by.value if sort_by else None,
        order=order,
    )
    return [BookRead(**b) for b in books]


@router.get(
    "/{book_id}",
    response_model=BookRead,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Книгу з таким ID не знайдено"}},
    summary="Отримати книгу за ID",
)
async def get_book(book_id: UUID) -> BookRead:
    book = await book_service.get_book(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книгу з id={book_id} не знайдено",
        )
    return BookRead(**book)


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Додати нову книгу",
    description=(
        "Створює нову книгу. ID генерується сервером як UUID4. "
        "Поле `status` опційне — за замовчуванням `available`."
    ),
)
async def create_book(payload: BookCreate) -> BookRead:
    data = payload.model_dump()
    if isinstance(data.get("status"), BookStatus):
        data["status"] = data["status"].value
    created = await book_service.create_book(data)
    return BookRead(**created)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Книгу з таким ID не знайдено"}},
    summary="Видалити книгу",
    description="Видаляє книгу за UUID. Повертає 204 при успіху, 404 якщо книги немає.",
)
async def delete_book(book_id: UUID) -> Response:
    deleted = await book_service.delete_book(book_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книгу з id={book_id} не знайдено",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
