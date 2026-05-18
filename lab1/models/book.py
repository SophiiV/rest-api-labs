from enum import Enum


class BookStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"


class BookSortField(str, Enum):
    TITLE = "title"
    YEAR = "year"
