
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



@pytest.mark.asyncio
async def test_get_all_books_empty_returns_pagination_envelope(client: AsyncClient):
    response = await client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "total": 0, "limit": 10, "offset": 0}


@pytest.mark.asyncio
async def test_pagination_limit_and_offset(client: AsyncClient):

    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    r = await client.get(BASE_URL, params={"limit": 5, "offset": 0})
    data = r.json()
    assert r.status_code == 200
    assert data["total"] == 15
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) == 5


    r2 = await client.get(BASE_URL, params={"limit": 5, "offset": 5})
    data2 = r2.json()
    assert len(data2["items"]) == 5

    ids_page1 = {b["id"] for b in data["items"]}
    ids_page2 = {b["id"] for b in data2["items"]}
    assert ids_page1.isdisjoint(ids_page2)

    r3 = await client.get(BASE_URL, params={"limit": 5, "offset": 10})
    assert len(r3.json()["items"]) == 5

    r4 = await client.get(BASE_URL, params={"limit": 5, "offset": 15})
    assert r4.json()["items"] == []


@pytest.mark.asyncio
async def test_pagination_invalid_limit_returns_422(client: AsyncClient):
    r = await client.get(BASE_URL, params={"limit": 0})
    assert r.status_code == 422
    r = await client.get(BASE_URL, params={"limit": 1000})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_pagination_negative_offset_returns_422(client: AsyncClient):
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

    r = await client.get(BASE_URL, params={"sort_by": "year"})
    years = [b["year"] for b in r.json()["items"]]
    assert years == [1900, 2000, 2020]


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
