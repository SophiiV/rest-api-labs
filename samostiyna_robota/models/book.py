"""
Документна модель книги для MongoDB.

На відміну від Лаб3 (де був ORM-клас SQLAlchemy), тут у нас просто
документ — звичайний словник у колекції `books`. Для зручності ми
описуємо його структуру у вигляді допоміжної функції, яка формує dict
для insert_one().

MongoDB сам додає поле `_id` (ObjectId) при вставці, якщо ми його не
вказуємо. Саме це `_id` ми будемо віддавати клієнту як рядок.
"""
from datetime import datetime
from typing import Optional


def build_book_document(
    title: str,
    author: str,
    year: int,
    status: str = "available",
    description: Optional[str] = None,
) -> dict:
    """
    Побудувати dict для вставки в Mongo.

    Поля документа:
      _id         — ObjectId (додасть Mongo сам при insert_one)
      title       — назва книги
      author      — автор
      description — опис (опційно, може бути None)
      status      — "available" або "issued"
      year        — рік видання
      created_at  — час створення (для стабільного сортування)
    """
    return {
        "title": title,
        "author": author,
        "description": description,
        "status": status,
        "year": year,
        "created_at": datetime.utcnow(),
    }


def book_doc_to_dict(doc: dict) -> dict:
    """
    Перетворити Mongo-документ у dict, придатний для BookResponse.

    Конвертуємо `_id` (ObjectId) у рядкове представлення — саме його
    віддаємо клієнту як `id`.
    """
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "author": doc["author"],
        "description": doc.get("description"),
        "status": doc["status"],
        "year": doc["year"],
    }
