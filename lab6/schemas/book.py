from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    """Можливі статуси книги."""
    available = "available"
    issued = "issued"


class BookCreate(BaseModel):
    """Схема для POST /books."""
    title: str = Field(..., min_length=1, max_length=200, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    description: Optional[str] = Field(None, max_length=1000, description="Опис (необов'язково)")
    status: BookStatus = Field(BookStatus.available, description="Статус: available або issued")
    year: int = Field(..., ge=1000, le=2100, description="Рік видання")


class BookResponse(BaseModel):
    """Схема відповіді — що віддаємо клієнту для однієї книги."""
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int

    model_config = {"from_attributes": True}


class CursorPaginatedBooks(BaseModel):
    """
    Схема відповіді для сторінки книг з CURSOR-пагінацією.
      - items       — книги цієї сторінки
      - limit       — скільки було запитано
      - next_cursor — непрозорий токен;  
    """
    items: List[BookResponse]
    limit: int = Field(..., description="Кількість запитаних елементів на сторінці")
    next_cursor: Optional[str] = Field(
        None,
        description="Токен для наступної сторінки; None якщо це остання сторінка",
    )
    has_more: bool = Field(..., description="Чи є ще сторінки після цієї")
