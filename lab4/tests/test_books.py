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
    """Helper for POST /books payload."""
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
    assert "id" in data and len(data["id"]) == 24


@pytest.mark.asyncio
async def test_create_book_invalid_year_returns_422(client: AsyncClient):
    response = await client.post(BASE_URL, json=sample_book(year=99))
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
# GET /books
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all_books_empty_returns_envelope(client: AsyncClient):
    response = await client.get(BASE_URL)
    data = response.json()
    assert response.status_code == 200
    assert data == {"items": [], "total": 0, "limit": 10, "offset": 0}


@pytest.mark.asyncio
async def test_pagination_first_page(client: AsyncClient):
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    r = await client.get(BASE_URL, params={"limit": 5, "offset": 0})
    data = r.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert data["total"] == 15
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_pagination_traverses_all_pages(client: AsyncClient):
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}", year=2000 + i))

    collected_ids: list[str] = []
    offset = 0
    limit = 5
    pages = 0

    while True:
        r = await client.get(BASE_URL, params={"limit": limit, "offset": offset})
        data = r.json()

        collected_ids.extend(b["id"] for b in data["items"])
        pages += 1
        offset += limit

        if offset >= data["total"]:
            break

        assert pages < 10  # safety guard

    assert len(collected_ids) == 15
    assert len(set(collected_ids)) == 15
    assert pages == 3


@pytest.mark.asyncio
async def test_pagination_last_page_partial(client: AsyncClient):
    for i in range(15):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}"))

    r = await client.get(BASE_URL, params={"limit": 5, "offset": 12})
    data = r.json()

    assert data["total"] == 15
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_pagination_offset_beyond_total_returns_empty(client: AsyncClient):
    for i in range(3):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i}"))

    r = await client.get(BASE_URL, params={"limit": 10, "offset": 100})
    data = r.json()

    assert data["items"] == []
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_pages_do_not_overlap(client: AsyncClient):
    for i in range(10):
        await client.post(BASE_URL, json=sample_book(title=f"Book {i:02d}"))

    r1 = await client.get(BASE_URL, params={"limit": 4, "offset": 0})
    r2 = await client.get(BASE_URL, params={"limit": 4, "offset": 4})

    ids1 = {b["id"] for b in r1.json()["items"]}
    ids2 = {b["id"] for b in r2.json()["items"]}

    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_pagination_invalid_limit_returns_422(client: AsyncClient):
    assert (await client.get(BASE_URL, params={"limit": 0})).status_code == 422
    assert (await client.get(BASE_URL, params={"limit": 1000})).status_code == 422


@pytest.mark.asyncio
async def test_pagination_invalid_offset_returns_422(client: AsyncClient):
    assert (await client.get(BASE_URL, params={"offset": -1})).status_code == 422


# ----------------------------------------------------------------------
# Filters & sorting
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
    await client.post(BASE_URL, json=sample_book(author="Shakespeare"))
    await client.post(BASE_URL, json=sample_book(author="Dickens"))

    r = await client.get(BASE_URL, params={"author": "shake"})
    data = r.json()

    assert data["total"] == 1


@pytest.mark.asyncio
async def test_sort_by_year(client: AsyncClient):
    await client.post(BASE_URL, json=sample_book(year=2020))
    await client.post(BASE_URL, json=sample_book(year=1900))
    await client.post(BASE_URL, json=sample_book(year=2000))

    r = await client.get(BASE_URL, params={"sort_by": "year"})
    years = [b["year"] for b in r.json()["items"]]

    assert years == [1900, 2000, 2020]


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
    r = await client.get(f"{BASE_URL}/507f1f77bcf86cd799439011")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_book_invalid_id_returns_400(client: AsyncClient):
    r = await client.get(f"{BASE_URL}/not-a-valid-oid")
    assert r.status_code == 400


# ----------------------------------------------------------------------
# PUT /books/{id}
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_book_returns_200(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()

    r = await client.put(
        f"{BASE_URL}/{created['id']}",
        json=sample_book(title="Updated", status="issued"),
    )

    data = r.json()

    assert data["id"] == created["id"]
    assert data["title"] == "Updated"
    assert data["status"] == "issued"


@pytest.mark.asyncio
async def test_update_book_persists(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()

    await client.put(
        f"{BASE_URL}/{created['id']}",
        json=sample_book(title="Changed"),
    )

    r = await client.get(f"{BASE_URL}/{created['id']}")
    assert r.json()["title"] == "Changed"


@pytest.mark.asyncio
async def test_update_book_not_found_returns_404(client: AsyncClient):
    r = await client.put(
        f"{BASE_URL}/507f1f77bcf86cd799439011",
        json=sample_book(),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_book_invalid_id_returns_400(client: AsyncClient):
    r = await client.put(f"{BASE_URL}/bad-id", json=sample_book())
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_update_book_invalid_body_returns_422(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()

    r = await client.put(
        f"{BASE_URL}/{created['id']}",
        json=sample_book(year=99),
    )
    assert r.status_code == 422


# ----------------------------------------------------------------------
# DELETE /books/{id}
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_book_returns_204(client: AsyncClient):
    created = (await client.post(BASE_URL, json=sample_book())).json()

    r = await client.delete(f"{BASE_URL}/{created['id']}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_is_idempotent(client: AsyncClient):
    fake_id = "507f1f77bcf86cd799439011"

    assert (await client.delete(f"{BASE_URL}/{fake_id}")).status_code == 204
    assert (await client.delete(f"{BASE_URL}/{fake_id}")).status_code == 204


@pytest.mark.asyncio
async def test_delete_invalid_id_returns_400(client: AsyncClient):
    assert (await client.delete(f"{BASE_URL}/bad-id")).status_code == 400