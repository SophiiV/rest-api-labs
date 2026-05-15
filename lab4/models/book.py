from datetime import datetime
from typing import Optional


def build_book_document(
    title: str,
    author: str,
    year: int,
    status: str = "available",
    description: Optional[str] = None,
) -> dict:
    return {
        "title": title,
        "author": author,
        "description": description,
        "status": status,
        "year": year,
        "created_at": datetime.utcnow(),
    }


def book_doc_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "author": doc["author"],
        "description": doc.get("description"),
        "status": doc["status"],
        "year": doc["year"],
    }
