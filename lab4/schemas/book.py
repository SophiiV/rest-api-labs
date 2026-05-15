from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    """Можливі статуси книги."""
    available = "available"
    issued = "issued"


class BookCreate(BaseModel):
    """Схема для створення книги."""
    title: str = Field(..., min_length=1, max_length=200, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    description: Optional[str] = Field(None, max_length=1000, description="Опис (необов'язково)")
    status: BookStatus = Field(BookStatus.available, description="Статус")
    year: int = Field(..., ge=1000, le=2100, description="Рік видання")


class BookUpdate(BaseModel):
    """Схема для оновлення книги."""
    title: str = Field(..., min_length=1, max_length=200, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    description: Optional[str] = Field(None, max_length=1000, description="Опис (необов'язково)")
    status: BookStatus = Field(BookStatus.available, description="Статус")
    year: int = Field(..., ge=1000, le=2100, description="Рік видання")


class BookResponse(BaseModel):
    """Схема відповіді для книги."""
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int


class PaginatedBooks(BaseModel):
    """Схема відповіді для пагінації."""
    items: List[BookResponse]
    total: int = Field(..., description="Загальна кількість записів")
    limit: int = Field(..., description="Кількість елементів на сторінці")
    offset: int = Field(..., description="Кількість пропущених елементів")