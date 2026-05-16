import json


def test_health(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_root_redirects_to_swagger(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/apidocs/" in response.headers["Location"]


def test_apispec_json_is_served(client):
    response = client.get("/apispec.json")
    assert response.status_code == 200
    spec = response.get_json()
    assert spec["swagger"] == "2.0"
    assert spec["info"]["title"] == "Library API"
    assert "/api/v1/books" in spec["paths"]
    assert "/api/v1/books/{book_id}" in spec["paths"]


def test_list_books_empty(client):
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_book_success(client):
    payload = {
        "title": "Кобзар",
        "author": "Тарас Шевченко",
        "year": 1840,
        "description": "Збірка поезій",
    }
    response = client.post(
        "/api/v1/books",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == 1
    assert body["title"] == "Кобзар"
    assert body["author"] == "Тарас Шевченко"
    assert body["year"] == 1840


def test_create_book_validation_error_year(client):
    payload = {"title": "X", "author": "Y", "year": 1000}
    response = client.post(
        "/api/v1/books",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = response.get_json()
    assert "errors" in body
    assert "year" in body["errors"]


def test_create_book_validation_error_missing_required(client):
    payload = {"title": "Тільки назва"}
    response = client.post(
        "/api/v1/books",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    body = response.get_json()
    assert "errors" in body
    assert set(body["errors"].keys()) >= {"author", "year"}


def test_get_book_by_id(client):
    client.post(
        "/api/v1/books",
        data=json.dumps({"title": "1984", "author": "Orwell", "year": 1949}),
        content_type="application/json",
    )
    response = client.get("/api/v1/books/1")
    assert response.status_code == 200
    assert response.get_json()["title"] == "1984"


def test_get_book_not_found(client):
    response = client.get("/api/v1/books/999")
    assert response.status_code == 404
    assert "not found" in response.get_json()["message"].lower()


def test_update_book(client):
    client.post(
        "/api/v1/books",
        data=json.dumps({"title": "Old", "author": "A", "year": 2000}),
        content_type="application/json",
    )
    response = client.put(
        "/api/v1/books/1",
        data=json.dumps(
            {"title": "New", "author": "B", "year": 2010, "description": "upd"}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["title"] == "New"
    assert body["description"] == "upd"


def test_update_book_not_found(client):
    response = client.put(
        "/api/v1/books/42",
        data=json.dumps({"title": "X", "author": "Y", "year": 2000}),
        content_type="application/json",
    )
    assert response.status_code == 404


def test_delete_book(client):
    client.post(
        "/api/v1/books",
        data=json.dumps({"title": "T", "author": "A", "year": 2000}),
        content_type="application/json",
    )
    response = client.delete("/api/v1/books/1")
    assert response.status_code == 204
    response = client.get("/api/v1/books/1")
    assert response.status_code == 404


def test_delete_book_not_found(client):
    response = client.delete("/api/v1/books/777")
    assert response.status_code == 404


def test_list_books_after_creates(client):
    for i, title in enumerate(["A", "B", "C"], start=1):
        client.post(
            "/api/v1/books",
            data=json.dumps({"title": title, "author": "X", "year": 2000 + i}),
            content_type="application/json",
        )
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 3
    assert [b["title"] for b in items] == ["A", "B", "C"]
