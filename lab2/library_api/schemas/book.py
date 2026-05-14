
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    available = "available"
    issued = "issued"


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    description: Optional[str] = Field(None, max_length=1000, description="Опис (необов'язково)")
    status: BookStatus = Field(BookStatus.available, description="Статус: available або issued")
    year: int = Field(..., ge=1000, le=2100, description="Рік видання")


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int

    model_config = {"from_attributes": True}


class PaginatedBooks(BaseModel):

    items: List[BookResponse]
    total: int = Field(..., description="Загальна кількість книг (після фільтрів)")
    limit: int = Field(..., description="Максимальна кількість елементів на сторінці")
    offset: int = Field(..., description="Кількість пропущених елементів (з якої позиції почали)")
