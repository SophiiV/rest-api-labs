"""
Pydantic-схеми для валідації вхідних даних і формування відповідей.

У Лаб4 (MongoDB) схеми майже такі самі, як у Лаб2/Лаб3 — інтерфейс API
не змінюється, змінюється лише база даних під капотом. Повернулись до
Limit-Offset пагінації (як у Лаб2).

ObjectId Mongo віддаємо клієнту як рядок — так простіше і JSON-сумісно.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    """Можливі статуси книги — обмежений перелік."""
    available = "available"
    issued = "issued"


class BookCreate(BaseModel):
    """Схема для POST /books — що очікуємо від клієнта при створенні."""
    title: str = Field(..., min_length=1, max_length=200, description="Назва книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")
    description: Optional[str] = Field(None, max_length=1000, description="Опис (необов'язково)")
    status: BookStatus = Field(BookStatus.available, description="Статус: available або issued")
    year: int = Field(..., ge=1000, le=2100, description="Рік видання")


class BookResponse(BaseModel):
    """
    Схема відповіді — що віддаємо клієнту для однієї книги.

    id — рядкове представлення ObjectId MongoDB (24 hex-символи).
    """
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int


class PaginatedBooks(BaseModel):
    """
    Схема відповіді для сторінки книг з Limit-Offset пагінацією.

    Поля:
      items  — книги поточної сторінки
      total  — загальна кількість книг у базі (з врахуванням фільтрів)
      limit  — скільки запитали
      offset — скільки пропустили
    """
    items: List[BookResponse]
    total: int = Field(..., description="Загальна кількість записів (для поточних фільтрів)")
    limit: int = Field(..., description="Скільки елементів на сторінці")
    offset: int = Field(..., description="Скільки елементів пропущено з початку")
