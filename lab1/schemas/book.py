from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.book import BookStatus


class BookBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Назва книги",
        examples=["1984"],
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Автор книги",
        examples=["George Orwell"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Короткий опис книги (опційно)",
        examples=["Антиутопія про тоталітарне суспільство."],
    )
    year: int = Field(
        ...,
        ge=1450,
        le=2100,
        description="Рік випуску книги",
        examples=[1949],
    )
    status: BookStatus = Field(
        default=BookStatus.AVAILABLE,
        description="Статус книги: 'available' або 'borrowed'",
    )


class BookCreate(BookBase):
    pass


class BookRead(BookBase):
    id: UUID = Field(
        ...,
        description="Унікальний ідентифікатор книги (UUID)",
    )

    model_config = ConfigDict(from_attributes=True)
