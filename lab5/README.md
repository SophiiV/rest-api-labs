# Library API — Лабораторна №5

REST API для керування книгами, побудований на Flask + Flask-RESTful.
Swagger документація генерується автоматично через flasgger.

## Стек

- Flask 3.x + Flask-RESTful — веб-фреймворк і CBV для ресурсів
- flasgger — Swagger UI з YAML-описів у docstring
- marshmallow — валідація
- pytest — тести

## Структура проєкту

```
library_api/
├── main.py                  # точка входу, конфіг Swagger
├── api/books.py             # ендпоінти (BookListResource, BookResource)
├── schemas/book.py          # marshmallow схеми
├── services/book_service.py # логіка
├── repository/book_repository.py  # in-memory сховище
├── models/book.py           # модель Book
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Як запустити

**Через Docker (рекомендую, бо з локальним pip були проблеми на mac):**
```bash
docker compose up --build
```

Порт 5000 на mac зайнятий системою, тому в docker-compose змінила на 5001.

Swagger UI: http://localhost:5001/apidocs  
API: http://localhost:5001/api/v1/books

**Локально:**
```bash
python -m venv .venv
source .venv/bin/activate
bash install.sh
python main.py
```

## Тести

```bash
python3 -m pytest -v
```

або через docker:
```bash
docker compose run --rm api pytest -v
```

## Ендпоінти

| Метод | URL | Опис |
|-------|-----|------|
| GET | `/api/v1/books` | всі книги |
| POST | `/api/v1/books` | додати книгу |
| GET | `/api/v1/books/<id>` | книга за id |
| PUT | `/api/v1/books/<id>` | оновити |
| DELETE | `/api/v1/books/<id>` | видалити |
