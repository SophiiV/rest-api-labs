"""
Тести для API книг.

GET /books, GET /books/{id} — публічні (доступні анонімам).
POST /books, DELETE /books/{id} — лише авторизованим.

Rate-limit вимкнений у conftest.py — тестується окремо в test_rate_limit.py.
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
    return {
        "title": title,
        "author": author,
        "description": description,
        "status": status,
        "year": year,
    }


# --- Доступ ---

@pytest.mark.asyncio
async def test_get_books_anonymous_returns_200(client: AsyncClient):
    r = await client.get(BASE_URL)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_book_by_id_anonymous_returns_404(client: AsyncClient):
    r = await client.get(f"{BASE_URL}/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_post_book_without_token_returns_401(client: AsyncClient):
    r = await client.post(BASE_URL, json=sample_book())
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_book_without_token_returns_401(client: AsyncClient):
    r = await client.delete(f"{BASE_URL}/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_post_with_invalid_token_returns_401(client: AsyncClient):
    r = await client.post(
        BASE_URL,
        json=sample_book(),
        headers={"Authorization": "Bearer garbage"},
    )
    assert r.status_code == 401


# --- POST /books ---

@pytest.mark.asyncio
async def test_create_book_returns_201(authed_client: AsyncClient):
    response = await authed_client.post(BASE_URL, json=sample_book())
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Кобзар"
    assert data["author"] == "Тарас Шевченко"
    assert data["status"] == "available"
    assert "id" in data and len(data["id"]) == 36


@pytest.mark.asyncio
async def test_create_book_invalid_year_returns_422(authed_client: AsyncClient):
    response = await authed_client.post(BASE_URL, json=sample_book(year=99))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_book_missing_title_returns_422(authed_client: AsyncClient):
    body = sample_book()
    del body["title"]
    response = await authed_client.post(BASE_URL, json=body)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_book_invalid_status_returns_422(authed_client: AsyncClient):
    response = await authed_client.post(BASE_URL, json=sample_book(status="lost"))
    assert response.status_code == 422


# --- GET /books (cursor-пагінація) ---

@pytest.mark.asyncio
async def test_get_all_books_empty_returns_cursor_envelope(authed_client: AsyncClient):
    response = await authed_client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "limit": 10, "next_cursor": None, "has_more": False}


@pytest.mark.asyncio
async def test_cursor_pagination_first_page_has_cursor(authed_client: AsyncClient):
    for i in range(15):
        await authed_client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    r = await authed_client.get(BASE_URL, params={"limit": 5})
    data = r.json()
    assert r.status_code == 200
    assert data["limit"] == 5
    assert len(data["items"]) == 5
    assert data["next_cursor"] is not None
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_cursor_pagination_traverses_all_pages(authed_client: AsyncClient):
    for i in range(15):
        await authed_client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    collected_ids: list[str] = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 5}
        if cursor:
            params["cursor"] = cursor
        r = await authed_client.get(BASE_URL, params=params)
        assert r.status_code == 200
        data = r.json()
        collected_ids.extend(b["id"] for b in data["items"])
        pages += 1
        if not data["has_more"]:
            break
        cursor = data["next_cursor"]
        assert cursor is not None
        assert pages < 10

    assert len(collected_ids) == 15
    assert len(set(collected_ids)) == 15
    assert pages == 3


@pytest.mark.asyncio
async def test_pagination_invalid_limit_returns_422(authed_client: AsyncClient):
    r = await authed_client.get(BASE_URL, params={"limit": 0})
    assert r.status_code == 422
    r = await authed_client.get(BASE_URL, params={"limit": 1000})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_cursor_returns_400(authed_client: AsyncClient):
    r = await authed_client.get(BASE_URL, params={"cursor": "this-is-not-valid-base64-json"})
    assert r.status_code == 400


# --- Фільтрація і сортування ---

@pytest.mark.asyncio
async def test_filter_by_status(authed_client: AsyncClient):
    await authed_client.post(BASE_URL, json=sample_book(title="A", status="available"))
    await authed_client.post(BASE_URL, json=sample_book(title="B", status="issued"))
    await authed_client.post(BASE_URL, json=sample_book(title="C", status="available"))

    r = await authed_client.get(BASE_URL, params={"status": "available"})
    data = r.json()
    assert len(data["items"]) == 2
    assert all(b["status"] == "available" for b in data["items"])


@pytest.mark.asyncio
async def test_filter_by_author_case_insensitive(authed_client: AsyncClient):
    await authed_client.post(BASE_URL, json=sample_book(title="A", author="Shakespeare"))
    await authed_client.post(BASE_URL, json=sample_book(title="B", author="Dickens"))

    r = await authed_client.get(BASE_URL, params={"author": "shake"})
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "Shakespeare"


@pytest.mark.asyncio
async def test_sort_by_year_with_cursor(authed_client: AsyncClient):
    await authed_client.post(BASE_URL, json=sample_book(title="C", year=2020))
    await authed_client.post(BASE_URL, json=sample_book(title="A", year=1900))
    await authed_client.post(BASE_URL, json=sample_book(title="B", year=2000))
    await authed_client.post(BASE_URL, json=sample_book(title="D", year=1950))

    r1 = await authed_client.get(BASE_URL, params={"sort_by": "year", "limit": 2})
    data1 = r1.json()
    years1 = [b["year"] for b in data1["items"]]
    assert years1 == [1900, 1950]
    assert data1["has_more"] is True

    r2 = await authed_client.get(
        BASE_URL, params={"sort_by": "year", "limit": 2, "cursor": data1["next_cursor"]}
    )
    data2 = r2.json()
    years2 = [b["year"] for b in data2["items"]]
    assert years2 == [2000, 2020]
    assert data2["has_more"] is False


# --- GET /books/{id} ---

@pytest.mark.asyncio
async def test_get_book_by_id_returns_200(authed_client: AsyncClient):
    created = (await authed_client.post(BASE_URL, json=sample_book())).json()
    r = await authed_client.get(f"{BASE_URL}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_book_by_id_not_found_returns_404(authed_client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = await authed_client.get(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 404


# --- DELETE /books/{id} ---

@pytest.mark.asyncio
async def test_delete_book_returns_204(authed_client: AsyncClient):
    created = (await authed_client.post(BASE_URL, json=sample_book())).json()
    r = await authed_client.delete(f"{BASE_URL}/{created['id']}")
    assert r.status_code == 204

    r2 = await authed_client.get(f"{BASE_URL}/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_is_idempotent(authed_client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = await authed_client.delete(f"{BASE_URL}/{fake_id}")
    assert r.status_code == 204
    r2 = await authed_client.delete(f"{BASE_URL}/{fake_id}")
    assert r2.status_code == 204
