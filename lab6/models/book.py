import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="available")
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Перетворює ORM-об'єкт у dict для зручної серіалізації."""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "status": self.status,
            "year": self.year,
        }
