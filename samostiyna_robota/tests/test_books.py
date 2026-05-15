"""
Юніт-тести для API книг (Лаб4 — MongoDB).

Покриваємо:
  - CRUD (POST / GET / DELETE)
  - Limit-Offset пагінацію (limit, offset, total)
  - Фільтри (status, author)
  - Сортування (title, year)
  - Валідацію (422) і некоректний ObjectId (400)
  - 404 для неіснуючих
  - Ідемпотентність DELETE

База — in-memory mongomock-motor (див. conftest.py). Запускати без Docker.
"""
import pytest
from httpx import AsyncClient

BASE_URL = "/api/v1/books"


def sample_book(
    title: str = "Кобзар",
    author: str = "Тарас Шевченко",
    year: int = 1840,
    status: str = "available",
    description: str = "Збірка поезій",
) -> dict:
    """Допоміжний генератор тіла запиту для POST /books."""
    return {
        "title": title,
        "author": author,
        "description": description,
        "status": status,
        "year": year,
    }


# ----------------------------------------------------------------------
# POST /books
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_book_returns_201(client: AsyncClient):
    response = await client.post(BASE_URL, json=sample_book())
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Кобзар"
    assert data["author"] == "Тарас Шевченко"
    assert data["status"] == "available"
    # ObjectId у рядковому вигляді — 24 hex-символи
    assert "id" in data and len(data["id"]) == 24


@pytest.mark.asyncio
async def test_create_book_invalid_year_returns_422(client: AsyncClient):
    response = await client.post(BASE_URL, json=sample_book(year=99))  # < 1000
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_book_missing_title_returns_422(client: AsyncClient):
    body = sample_book()
    del body["title"]
    response = await client.post(BASE_URL, json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_book_invalid_status_returns_422(client: AsyncClient):
    response = await client.post(BASE_URL, json=sample_book(status="lost"))
    assert response.status_code == 422


# ----------------------------------------------------------------------
# GET /books — пагінація Limit-Offset та формат відповіді
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all_books_empty_returns_envelope(client: AsyncClient):
    response = await client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    # Пусто → items порожні, total=0, limit/offset за замовчуванням.
    assert data == {"items": [], "total": 0, "limit": 10, "offset": 0}


@pytest.mark.asyncio
async def test_pagination_first_page(client: AsyncClient):
    # Створюємо 15 книг
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    # Перша сторінка: limit=5, offset=0
    r = await client.get(BASE_URL, params={"limit": 5, "offset": 0})
    data = r.json()
    assert r.status_code == 200
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert data["total"] == 15
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_pagination_traverses_all_pages(client: AsyncClient):
    """Проходимо всі 15 книг сторінками по 5 через offset."""
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    collected_ids: list[str] = []
    offset = 0
    limit = 5
    pages = 0
    while True:
        r = await client.get(BASE_URL, params={"limit": limit, "offset": offset})
        assert r.status_code == 200
        data = r.json()
        collected_ids.extend(b["id"] for b in data["items"])
        pages += 1
        offset += limit
        # Зупиняємось, коли пройшли всі елементи.
        if offset >= data["total"]:
            break
        # Страховка від нескінченного циклу в разі бага
        assert pages < 10

    # Всі 15 книг зібрано, жодного повторного id
    assert len(collected_ids) == 15
    assert len(set(collected_ids)) == 15
    # Три повні сторінки по 5
    assert pages == 3


@pytest.mark.asyncio
async def test_pagination_last_page_partial(client: AsyncClient):
    """Остання сторінка — часткова (4 з 15, limit=5, offset=12)."""
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}"))

    r = await client.get(BASE_URL, params={"limit": 5, "offset": 12})
    data = r.json()
    assert data["total"] == 15
    assert data["limit"] == 5
    assert data["offset"] == 12
    # 15 - 12 = 3 елементи
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_pagination_offset_beyond_total_returns_empty(client: AsyncClient):
    """offset > total → items=[], але total показує реальну кількість."""
    for i in range(3):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i}"))

    r = await client.get(BASE_URL, params={"limit": 10, "offset": 100})
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 3
    assert data["offset"] == 100


@pytest.mark.asyncio
async def test_pages_do_not_overlap(client: AsyncClient):
    """Сторінки не перетинаються — жоден id не з'являється двічі."""
    for i in range(10):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}"))

    r1 = await client.get(BASE_URL, params={"limit": 4, "offset": 0})
    r2 = await client.get(BASE_URL, params={"limit": 4, "offset": 4})

    ids1 = {b["id"] for b in r1.json()["items"]}
    ids2 = {b["id"] for b in r2.json()["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_pagination_invalid_limit_returns_422(client: AsyncClient):
    r = await client.get(BASE_URL, params={"limit": 0})
    assert r.status_code == 422
    r = await client.get(BASE_URL, params={"limit": 1000})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_pagination_invalid_offset_returns_422(client: AsyncClient):
    r = await client.get(BASE_URL, params={"offset": -1})
    assert r.status_code == 422


# ----------------------------------------------------------------------
# GET /books — фільтрація і сортування
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    await client.post(BASE_URL, json=sample_book(title="A", status="available"))
    await client.post(BASE_URL, json=sample_book(title="B", status="issued"))
    await client.post(BASE_URL, json=sample_book(title="C", status="available"))

    r = await client.get(BASE_URL, params={"status": "available"})
    data = r.json()
    assert data["total"] == 2
    assert all(b["status"] == "available" for b in data["items"])


@pytest.mark.asyncio
async def test_filter_by_author_case_insensitive(client: AsyncClient):
    await client.post(BASE_URL, json=sample_book(title="A", author="Shakespeare"))
    await client.post(BASE_URL, json=sample_book(title="B", author="Dickens"))

    r = await client.get(BASE_URL, params={"author": "shake"})
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["author"] == "Shakespeare"


@pytest.mark.asyncio
async def test_sort_by_year(client: AsyncClient):
    await client.post(BASE_URL, json=sample_book(title="C", year=2020))
    await client.post(BASE_URL, json=sample_book(title="A", year=1900))
    await client.post(BASE_URL, json=sample_book(title="B", year=2000))
    await client.post(BASE_URL, json=sample_book(title="D", year=1950))

    r = await client.get(BASE_URL, params={"sort_by": "year"})
    years = [b["year"] for b in r.json()["items"]]
    assert years == [1900, 1950, 2000, 2020]


@pytest.mark.asyncio
async def test_sort_by_title(client: AsyncClient):
    await client.post(BASE_URL, json=sample_book(title="Cherry"))
    await client.post(BASE_URL, json=sample_book(title="Apple"))
    await client.post(BASE_URL, json=sample_book(title="Banana"))

    r = await client.get(BASE_URL, params={"sort_by": "title"})
    titles = [b["title"] for b in r.json()["items"]]
    assert titles == ["Apple", "Banana", "Cherry"]


# ----------------------------------------------------------------------
# GET /books/{id}
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_book_by_id_returns_200(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()
    r = await client.get(f"{BASE_URL}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_book_by_id_not_found_returns_404(client: AsyncClient):
    # Валідний формат ObjectId, але такої книги нема
    fake_id = "507f1f77bcf86cd799439011"
    r = await client.get(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_book_invalid_id_returns_400(client: AsyncClient):
    """Битий ObjectId (не 24 hex-символи) → 400 Bad Request."""
    r = await client.get(f"{BASE_URL}/not-a-valid-oid")
    assert r.status_code == 400


# ----------------------------------------------------------------------
# DELETE /books/{id}
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_book_returns_204(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()
    r = await client.delete(f"{BASE_URL}/{created['id']}")
    assert r.status_code == 204

    # Після видалення GET повертає 404
    r2 = await client.get(f"{BASE_URL}/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_is_idempotent(client: AsyncClient):
    fake_id = "507f1f77bcf86cd799439011"
    # Видалення неіснуючої книги — теж 204 (ідемпотентність)
    r = await client.delete(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 204

    # Повторне видалення — теж 204
    r2 = await client.delete(f"{BASE_URL}/{fake_id}")
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_delete_invalid_id_returns_400(client: AsyncClient):
    """Битий ObjectId на видалення → 400 Bad Request."""
    r = await client.delete(f"{BASE_URL}/not-a-valid-oid")
    assert r.status_code == 400
