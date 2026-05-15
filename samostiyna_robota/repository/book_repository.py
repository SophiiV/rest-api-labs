"""
Repository шар — інкапсулює всі операції з колекцією MongoDB через motor.

Ключові відмінності від Лаб3 (SQLAlchemy → Mongo):
  - Немає таблиць/моделей ORM — ми працюємо з dict-документами
  - Немає SQL — ми викликаємо методи колекції (insert_one, find, delete_one тощо)
  - Ідентифікатор — ObjectId (Mongo генерує автоматично)
  - `find()` — СИНХРОННИЙ (повертає курсор), а `find_one()`, `insert_one()`,
    `delete_one()`, `count_documents()` — АСИНХРОННІ
  - Пагінація — Limit-Offset через методи .skip(n).limit(m) на курсорі

ObjectId — це 12-байтовий ідентифікатор Mongo. Ми отримуємо його як рядок
з клієнта, валідуємо через ObjectId(...) і шукаємо по _id.
"""
from typing import List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from models.book import build_book_document


class InvalidBookIdError(Exception):
    """Клієнт передав рядок, який не є валідним ObjectId."""


def _parse_object_id(book_id: str) -> ObjectId:
    """Перетворити рядок у ObjectId. Кидає InvalidBookIdError, якщо рядок битий."""
    try:
        return ObjectId(book_id)
    except (InvalidId, TypeError) as exc:
        raise InvalidBookIdError(f"Некоректний id книги: {book_id!r}") from exc


class BookRepository:
    """CRUD-операції над колекцією books з Limit-Offset пагінацією."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        # Кожен екземпляр Repository тримає посилання на колекцію Mongo.
        # Сама колекція приходить з FastAPI-dependency get_books_collection.
        self.collection = collection

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    async def list_books(
        self,
        limit: int,
        offset: int,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """
        Повертає (список_документів, total).

        Logic Limit-Offset:
          1. Будуємо Mongo-фільтр (dict)
          2. Рахуємо total через count_documents()
          3. Беремо курсор із сортуванням, пропускаємо offset, беремо limit
          4. Збираємо всі документи цього курсора у список
        """
        # 1) Формуємо фільтр для Mongo. Пустий dict → без фільтрів.
        query: dict = {}
        if status is not None:
            query["status"] = status
        if author is not None:
            # $regex + $options: "i" — регістронезалежний пошук по підрядку,
            # як функція "contains" у SQL.
            # re.escape потрібен, щоб спецсимволи в імені автора (типу '.')
            # не тлумачились як regex-метасимволи.
            import re
            query["author"] = {"$regex": re.escape(author), "$options": "i"}

        # 2) Рахуємо загальну кількість (з урахуванням фільтрів).
        total = await self.collection.count_documents(query)

        # 3) Визначаємо поле сортування.
        #    За замовчуванням — created_at (час вставки), як у Лаб3.
        if sort_by == "title":
            sort_field = "title"
        elif sort_by == "year":
            sort_field = "year"
        else:
            sort_field = "created_at"

        # 4) Курсор. УВАГА: find() — синхронний метод! Він повертає курсор,
        #    який ми налаштовуємо через .sort().skip().limit() і лише потім
        #    перебираємо асинхронно.
        cursor = (
            self.collection.find(query)
            .sort([(sort_field, 1), ("_id", 1)])  # 1 = ASC; _id як tie-breaker
            .skip(offset)
            .limit(limit)
        )

        # to_list() — асинхронний метод motor, що вичерпує курсор у список.
        # None як аргумент = "без обмеження кількості" (ми і так обмежили limit-ом).
        docs = await cursor.to_list(length=None)
        return docs, total

    async def get_by_id(self, book_id: str) -> Optional[dict]:
        """Знайти одну книгу за id (рядок → ObjectId). Повертає None якщо нема."""
        oid = _parse_object_id(book_id)
        # find_one — АСИНХРОННИЙ, треба await.
        doc = await self.collection.find_one({"_id": oid})
        return doc

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------
    async def add(
        self,
        title: str,
        author: str,
        year: int,
        status: str,
        description: Optional[str],
    ) -> dict:
        """
        Додати нову книгу. Повертає документ з уже згенерованим _id.

        insert_one() — асинхронний; повертає InsertOneResult з inserted_id.
        Далі дочитуємо документ, щоб мати повний dict для відповіді клієнту.
        """
        doc = build_book_document(
            title=title,
            author=author,
            year=year,
            status=status,
            description=description,
        )
        result = await self.collection.insert_one(doc)
        # Mongo поклав _id сам; кладемо його назад у документ, щоб повернути.
        doc["_id"] = result.inserted_id
        return doc

    async def delete(self, book_id: str) -> bool:
        """
        Видалити книгу. Повертає True якщо видалили, False якщо такої не було.

        Метод delete_one повертає об'єкт з атрибутом deleted_count:
          1 — документ знайдено й видалено
          0 — документа не існувало
        Ми не вважаємо 0 помилкою — робимо операцію ідемпотентною на рівні сервісу.
        """
        oid = _parse_object_id(book_id)
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0
