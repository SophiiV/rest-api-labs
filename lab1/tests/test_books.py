from __future__ import annotations

import pytest

BASE = "/api/v1/books"


def _book(**overrides) -> dict:
    base = {
        "title": "1984",
        "author": "George Orwell",
        "description": "Антиутопія",
        "year": 1949,
        "status": "available",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_root_health(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "Library API"


@pytest.mark.asyncio
async def test_list_books_empty(client):
    resp = await client.get(BASE)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_book_ok(client):
    resp = await client.post(BASE, json=_book())
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "1984"
    assert body["author"] == "George Orwell"
    assert body["status"] == "available"
    assert len(body["id"]) == 36
    assert body["id"].count("-") == 4


@pytest.mark.asyncio
async def test_create_book_default_status_is_available(client):
    payload = _book()
    payload.pop("status")
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 201
    assert resp.json()["status"] == "available"


@pytest.mark.asyncio
async def test_create_book_validation_error_year(client):
    resp = await client.post(BASE, json=_book(year=1000))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_validation_error_missing_title(client):
    payload = _book()
    payload.pop("title")
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_validation_error_bad_status(client):
    resp = await client.post(BASE, json=_book(status="lost_in_space"))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_book_by_id_not_found(client):
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    resp = await client.get(f"{BASE}/{fake_uuid}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_book_by_id_bad_uuid(client):
    resp = await client.get(f"{BASE}/not-a-uuid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_book_by_id_ok(client):
    created = (await client.post(BASE, json=_book(title="Кобзар"))).json()
    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Кобзар"


@pytest.mark.asyncio
async def test_delete_book_ok(client):
    created = (await client.post(BASE, json=_book())).json()
    resp = await client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_book_idempotent_state_unchanged(client):
    created = (await client.post(BASE, json=_book())).json()
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 204
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 404
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 404
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_404(client):
    fake_uuid = "22222222-2222-2222-2222-222222222222"
    resp = await client.delete(f"{BASE}/{fake_uuid}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_author(client):
    await client.post(BASE, json=_book(title="A", author="Орвелл"))
    await client.post(BASE, json=_book(title="B", author="Шевченко"))
    await client.post(BASE, json=_book(title="C", author="Орвелл"))

    resp = await client.get(BASE, params={"author": "Орвелл"})
    assert resp.status_code == 200
    books = resp.json()
    assert len(books) == 2
    assert all(b["author"] == "Орвелл" for b in books)


@pytest.mark.asyncio
async def test_filter_by_author_case_insensitive(client):
    await client.post(BASE, json=_book(author="George Orwell"))
    resp = await client.get(BASE, params={"author": "george orwell"})
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_filter_by_status(client):
    await client.post(BASE, json=_book(title="A", status="available"))
    await client.post(BASE, json=_book(title="B", status="borrowed"))
    await client.post(BASE, json=_book(title="C", status="borrowed"))

    resp = await client.get(BASE, params={"status": "borrowed"})
    assert resp.status_code == 200
    books = resp.json()
    assert len(books) == 2
    assert all(b["status"] == "borrowed" for b in books)


@pytest.mark.asyncio
async def test_filter_combined(client):
    await client.post(BASE, json=_book(title="A", author="X", status="available"))
    await client.post(BASE, json=_book(title="B", author="X", status="borrowed"))
    await client.post(BASE, json=_book(title="C", author="Y", status="borrowed"))

    resp = await client.get(BASE, params={"author": "X", "status": "borrowed"})
    books = resp.json()
    assert len(books) == 1
    assert books[0]["title"] == "B"


@pytest.mark.asyncio
async def test_sort_by_title_asc(client):
    await client.post(BASE, json=_book(title="Beta"))
    await client.post(BASE, json=_book(title="Alpha"))
    await client.post(BASE, json=_book(title="Gamma"))

    resp = await client.get(BASE, params={"sort_by": "title", "order": "asc"})
    titles = [b["title"] for b in resp.json()]
    assert titles == ["Alpha", "Beta", "Gamma"]


@pytest.mark.asyncio
async def test_sort_by_year_desc(client):
    await client.post(BASE, json=_book(title="A", year=2001))
    await client.post(BASE, json=_book(title="B", year=1999))
    await client.post(BASE, json=_book(title="C", year=2010))

    resp = await client.get(BASE, params={"sort_by": "year", "order": "desc"})
    years = [b["year"] for b in resp.json()]
    assert years == [2010, 2001, 1999]


@pytest.mark.asyncio
async def test_sort_bad_field_returns_422(client):
    resp = await client.get(BASE, params={"sort_by": "author"})
    assert resp.status_code == 422
