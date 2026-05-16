# Library API — Лабораторна №5

REST API для бібліотеки книг на **Flask + Flask-RESTful** з автогенерованою
**Swagger / OpenAPI 2.0** документацією через **flasgger**.

## Технологічний стек

| Компонент | Призначення |
|-----------|-------------|
| Flask 3.x | Мікро веб-фреймворк |
| Flask-RESTful | Class-Based Views для REST-ресурсів (`Resource`) |
| flasgger | Автогенерація Swagger UI з YAML-описів у docstring |
| marshmallow | Валідація вхідних даних |
| pytest | Тестування |

## Структура

```
library_api/
├── main.py                  # Entry point: Flask app + Swagger config
├── api/books.py             # Flask-RESTful Resources + flasgger docstrings
├── schemas/book.py          # marshmallow-схеми для валідації
├── services/book_service.py # Бізнес-логіка
├── repository/              # In-memory сховище
│   └── book_repository.py
├── models/book.py           # Доменна модель Book (dataclass)
├── tests/                   # pytest тести
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Запуск локально

```bash
cd library_api
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Відкрити:
- **Swagger UI:** http://127.0.0.1:5000/apidocs/
- **OpenAPI JSON:** http://127.0.0.1:5000/apispec.json
- **API base:** http://127.0.0.1:5000/api/v1/books

## Запуск через Docker

```bash
docker compose up --build
```

## Тести

```bash
pytest
```

## Ендпоінти

| Метод | URL | Опис |
|-------|-----|------|
| GET | `/api/v1/books` | Список усіх книг |
| POST | `/api/v1/books` | Створити книгу |
| GET | `/api/v1/books/<id>` | Отримати книгу за id |
| PUT | `/api/v1/books/<id>` | Повне оновлення книги |
| DELETE | `/api/v1/books/<id>` | Видалити книгу |

Усі ендпоінти описані прямо в Swagger UI з прикладами запитів і відповідей.
