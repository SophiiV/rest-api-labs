from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_book_service, get_current_user
from models.user import User
from repository.book_repository import InvalidCursorError
from schemas.book import BookCreate, BookResponse, BookStatus, CursorPaginatedBooks
from services.book_service import BookService

router = APIRouter()


# ----------------------------------------------------------------------
# GET /books — список книг з CURSOR-пагінацією, фільтрами та сортуванням.
# Захищено JWT.
# ----------------------------------------------------------------------
@router.get(
    "/books",
    response_model=CursorPaginatedBooks,
    status_code=status.HTTP_200_OK,
    summary="Отримати список книг (захищено JWT)",
)
async def get_all_books(
    limit: int = Query(10, ge=1, le=100, description="Скільки елементів повернути (1-100)"),
    cursor: Optional[str] = Query(
        None,
        description="Токен наступної сторінки. Не передавай для першої сторінки.",
    ),
    status_filter: Optional[BookStatus] = Query(None, alias="status", description="Фільтр по статусу"),
    author: Optional[str] = Query(None, description="Фільтр по автору (часткове співпадіння)"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$", description="Сортування: title або year"),
    service: BookService = Depends(get_book_service),
    _current_user: User = Depends(get_current_user),
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return CursorPaginatedBooks(
        items=[BookResponse.model_validate(b) for b in books],
        limit=limit,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


# ----------------------------------------------------------------------
# GET /books/{book_id} — отримати одну книгу за ID. Захищено JWT.
# ----------------------------------------------------------------------
@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати книгу за ID (захищено JWT)",
)
async def get_book_by_id(
    book_id: str,
    service: BookService = Depends(get_book_service),
    _current_user: User = Depends(get_current_user),
) -> BookResponse:
    book = await service.get_book_by_id(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книгу з id={book_id} не знайдено",
        )
    return BookResponse.model_validate(book)


# ----------------------------------------------------------------------
# POST /books — створити нову книгу. Захищено JWT.
# ----------------------------------------------------------------------
@router.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову книгу (захищено JWT)",
)
async def create_book(
    book_data: BookCreate,
    service: BookService = Depends(get_book_service),
    _current_user: User = Depends(get_current_user),
) -> BookResponse:
    book = await service.create_book(book_data)
    return BookResponse.model_validate(book)


# ----------------------------------------------------------------------
# DELETE /books/{book_id} — видалити книгу (ідемпотентно). Захищено JWT.
# ----------------------------------------------------------------------
@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити книгу (ідемпотентно, захищено JWT)",
)
async def delete_book(
    book_id: str,
    service: BookService = Depends(get_book_service),
    _current_user: User = Depends(get_current_user),
) -> None:
    await service.delete_book(book_id)
    return None
