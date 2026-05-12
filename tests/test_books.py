
from itertools import count

import pytest

from main import create_app
from repository.book_repository import book_repository


@pytest.fixture(autouse=True)
def reset_repo():
    book_repository._books.clear()
    book_repository._id_counter = count(start=1)
    yield


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()

 
def test_get_books_empty(client):
    resp = client.get("/api/v1/books")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_book_ok(client):
    payload = {"title": "1984", "author": "George Orwell", "year": 1949}
    resp = client.post("/api/v1/books", json=payload)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["id"] == 1
    assert body["title"] == "1984"


def test_create_book_validation_error(client):
    payload = {"title": "Bad", "author": "X", "year": 1000}
    resp = client.post("/api/v1/books", json=payload)
    assert resp.status_code == 400
    assert "errors" in resp.get_json()


def test_create_book_missing_required(client):
    resp = client.post("/api/v1/books", json={"author": "X", "year": 2000})
    assert resp.status_code == 400


def test_get_book_by_id_not_found(client):
    resp = client.get("/api/v1/books/999")
    assert resp.status_code == 404


def test_get_book_by_id_ok(client):
    client.post(
        "/api/v1/books",
        json={"title": "Кобзар", "author": "Тарас Шевченко", "year": 1840},
    )
    resp = client.get("/api/v1/books/1")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Кобзар"


def test_put_book_ok(client):
    client.post(
        "/api/v1/books",
        json={"title": "Old", "author": "Author", "year": 2000},
    )
    resp = client.put(
        "/api/v1/books/1",
        json={"title": "New", "author": "Author", "year": 2001},
    )
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "New"


def test_put_book_not_found(client):
    resp = client.put(
        "/api/v1/books/42",
        json={"title": "X", "author": "Y", "year": 2020},
    )
    assert resp.status_code == 404


def test_delete_book_ok(client):
    client.post(
        "/api/v1/books",
        json={"title": "Old", "author": "Author", "year": 2000},
    )
    resp = client.delete("/api/v1/books/1")
    assert resp.status_code == 204


def test_delete_book_idempotent_returns_404(client):
    """DELETE за id — ідемпотентний: повторний виклик повертає 404."""
    client.post(
        "/api/v1/books",
        json={"title": "Old", "author": "Author", "year": 2000},
    )
    assert client.delete("/api/v1/books/1").status_code == 204
    assert client.delete("/api/v1/books/1").status_code == 404
