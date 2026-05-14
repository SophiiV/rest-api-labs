
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
    assert "id" in data and len(data["id"]) == 36  # UUID


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
# GET /books — cursor-пагінація та формат відповіді
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all_books_empty_returns_cursor_envelope(client: AsyncClient):
    response = await client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    # Пусто → items порожні, next_cursor відсутній, has_more=False.
    assert data == {"items": [], "limit": 10, "next_cursor": None, "has_more": False}


@pytest.mark.asyncio
async def test_cursor_pagination_first_page_has_cursor(client: AsyncClient):
    # Створюємо 15 книг
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    # Перша сторінка: limit=5, без cursor
    r = await client.get(BASE_URL, params={"limit": 5})
    data = r.json()
    assert r.status_code == 200
    assert data["limit"] == 5
    assert len(data["items"]) == 5
    # Оскільки всього 15 і запитали 5 — має бути next_cursor і has_more=True
    assert data["next_cursor"] is not None
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_cursor_pagination_traverses_all_pages(client: AsyncClient):
    """Проходимо всі 15 книг сторінками по 5, ідучи за next_cursor."""
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    collected_ids: list[str] = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 5}
        if cursor:
            params["cursor"] = cursor
        r = await client.get(BASE_URL, params=params)
        assert r.status_code == 200
        data = r.json()
        collected_ids.extend(b["id"] for b in data["items"])
        pages += 1
        if not data["has_more"]:
            break
        cursor = data["next_cursor"]
        assert cursor is not None
        # Страховка від нескінченного циклу в разі бага
        assert pages < 10

    # Всі 15 книг зібрано, жодного повторного id
    assert len(collected_ids) == 15
    assert len(set(collected_ids)) == 15
    # Три повні сторінки по 5
    assert pages == 3


@pytest.mark.asyncio
async def test_cursor_pagination_last_page_has_no_cursor(client: AsyncClient):
    """Остання сторінка має next_cursor=None, has_more=False."""
    for i in range(4):  # 4 книги, limit=5 → одразу остання сторінка
        await client.post(BASE_URL, json=sample_book(title=f"Book {i}"))

    r = await client.get(BASE_URL, params={"limit": 5})
    data = r.json()
    assert len(data["items"]) == 4
    assert data["next_cursor"] is None
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_cursor_pages_do_not_overlap(client: AsyncClient):
    """Сторінки не перетинаються — жоден id не з'являється двічі."""
    for i in range(10):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}"))

    # Перша сторінка
    r1 = await client.get(BASE_URL, params={"limit": 4})
    data1 = r1.json()
    # Друга сторінка по cursor-у з першої
    r2 = await client.get(BASE_URL, params={"limit": 4, "cursor": data1["next_cursor"]})
    data2 = r2.json()

    ids1 = {b["id"] for b in data1["items"]}
    ids2 = {b["id"] for b in data2["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_pagination_invalid_limit_returns_422(client: AsyncClient):
    r = await client.get(BASE_URL, params={"limit": 0})
    assert r.status_code == 422
    r = await client.get(BASE_URL, params={"limit": 1000})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_cursor_returns_400(client: AsyncClient):
    """Битий cursor → 400 Bad Request."""
    r = await client.get(BASE_URL, params={"cursor": "this-is-not-valid-base64-json"})
    assert r.status_code == 400


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
    assert len(data["items"]) == 2
    assert all(b["status"] == "available" for b in data["items"])


@pytest.mark.asyncio
async def test_filter_by_author_case_insensitive(client: AsyncClient):
    # Латинські символи — SQLite-ний LOWER() коректно працює тільки з ASCII.
    # У prod (PostgreSQL) Unicode-lowercasing працює для будь-яких алфавітів.
    await client.post(BASE_URL, json=sample_book(title="A", author="Shakespeare"))
    await client.post(BASE_URL, json=sample_book(title="B", author="Dickens"))

    r = await client.get(BASE_URL, params={"author": "shake"})
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "Shakespeare"


@pytest.mark.asyncio
async def test_sort_by_year_with_cursor(client: AsyncClient):
    """Перевіряємо, що cursor-пагінація з sort_by=year віддає сторінки у правильному порядку."""
    await client.post(BASE_URL, json=sample_book(title="C", year=2020))
    await client.post(BASE_URL, json=sample_book(title="A", year=1900))
    await client.post(BASE_URL, json=sample_book(title="B", year=2000))
    await client.post(BASE_URL, json=sample_book(title="D", year=1950))

    # Сторінка 1: перші 2 за роком
    r1 = await client.get(BASE_URL, params={"sort_by": "year", "limit": 2})
    data1 = r1.json()
    years1 = [b["year"] for b in data1["items"]]
    assert years1 == [1900, 1950]
    assert data1["has_more"] is True

    # Сторінка 2 — по cursor-у
    r2 = await client.get(
        BASE_URL, params={"sort_by": "year", "limit": 2, "cursor": data1["next_cursor"]}
    )
    data2 = r2.json()
    years2 = [b["year"] for b in data2["items"]]
    assert years2 == [2000, 2020]
    assert data2["has_more"] is False


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
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = await client.get(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 404


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
    fake_id = "00000000-0000-0000-0000-000000000000"
    # Видалення неіснуючої книги — теж 204 (ідемпотентність)
    r = await client.delete(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 204

    # Повторне видалення — теж 204
    r2 = await client.delete(f"{BASE_URL}/{fake_id}")
    assert r2.status_code == 204
