from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    available = "available"
    issued = "issued"


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: BookStatus = Field(BookStatus.available)
    year: int = Field(..., ge=1000, le=2100)


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int

    model_config = {"from_attributes": True}


class CursorPaginatedBooks(BaseModel):
    """
    Відповідь з cursor-пагінацією.
    next_cursor=None означає, що це остання сторінка.
    """
    items: List[BookResponse]
    limit: int
    next_cursor: Optional[str] = None
    has_more: bool
