from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Book:
    id: int
    title: str
    author: str
    year: int
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
