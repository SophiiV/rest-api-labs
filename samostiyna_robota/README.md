# Library API — Самостійна робота

REST API для управління бібліотекою книг, **задеплоєне** на безкоштовному хостингу.

**Стек:** FastAPI + motor (async MongoDB) + Render.com (web-хостинг) + MongoDB Atlas (БД).

## Що нового порівняно з Лаб4

- Додано **продакшн-деплой** на Render.com (публічна HTTPS-адреса)
- База даних винесена у **MongoDB Atlas** — хмарний MongoDB-cluster (free tier M0)
- Замість `localhost:27017` у Docker тепер **`mongodb+srv://`** connection string до Atlas
- Додано `render.yaml` (Infrastructure-as-Code) і `Procfile` (запасний варіант)
- Додано **CORS-middleware** у `main.py` — щоб API можна було викликати з іншого origin
- Розширено `/` health-check — повертає `environment` (щоб одразу бачити «local» / Render hostname)
- Docker більше **не обов'язковий** для продакшн-запуску — Render сам ставить Python і залежності
- Версія API піднята: `4.0.0` → `5.0.0`

## Структура проекту

```
library_api/
├── api/            # Ендпоінти (роути)
├── schemas/        # Pydantic схеми
├── services/       # Бізнес-логіка
├── repository/     # Операції з колекцією MongoDB через motor
├── models/         # Допоміжні функції для документа
├── tests/          # Юніт-тести (mongomock-motor, in-memory)
├── database.py     # Ініціалізація Mongo-клієнта
├── main.py         # Точка входу FastAPI + CORS
├── Dockerfile      # Docker-образ (для локального запуску)
├── docker-compose.yml  # Локальний dev-стек (api + mongo)
├── render.yaml     # НОВЕ: конфіг Render.com (Blueprint)
├── Procfile        # НОВЕ: fallback-конфіг для PaaS
├── runtime.txt     # НОВЕ: фіксує версію Python для Render
├── .env.example    # НОВЕ: шаблон для локальних секретів
├── .gitignore      # НОВЕ
└── requirements.txt
```

## Швидкий старт — продакшн (Render.com)

Повна покрокова інструкція — у файлі `../ПОКРОКОВИЙ_ГАЙД.md` (від "склонуй репо" до "відкрий публічний Swagger"). Коротко:

1. Зареєструватись на [render.com](https://render.com) через GitHub.
2. Створити безкоштовний MongoDB Atlas cluster (M0) і забрати `mongodb+srv://...` connection string.
3. У Render Dashboard: **New → Web Service** → вибрати свій GitHub-репо → Render підтягне `render.yaml`.
4. Додати env-змінну `MONGO_URL` у Dashboard (вручну — щоб не запушити секрет у Git).
5. Deploy → дочекатись "Live" → відкрити `https://<your-name>.onrender.com/docs`.

## Локальний запуск (через Docker)

```bash
docker compose up --build
```
Swagger: http://localhost:8000/docs.

## Локальний запуск (без Docker)

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Варіант А — локальний Mongo через Docker (лише БД):
docker compose up -d mongo
export MONGO_URL="mongodb://mongo_admin:password@localhost:27017/?authSource=admin"
export MONGO_DB_NAME="library_db"

# Варіант Б — MongoDB Atlas (як на проді):
# скопіюй .env.example у .env, постав свій connection string
export $(cat .env | xargs)

uvicorn main:app --reload
```

## Тести

```bash
pytest tests/ -v
```

Тести працюють на **mongomock-motor** (in-memory) — їм не потрібен ні Docker, ні Atlas.

## Ендпоінти

| Метод  | URL                | Опис                          | Коди            |
|--------|--------------------|-------------------------------|-----------------|
| GET    | /                  | Health-check + метадані       | 200             |
| GET    | /api/v1/books      | Список книг (limit/offset)    | 200 / 422       |
| GET    | /api/v1/books/{id} | Книга за ID                   | 200 / 400 / 404 |
| POST   | /api/v1/books      | Створити книгу                | 201 / 422       |
| DELETE | /api/v1/books/{id} | Видалити книгу (ідемпотентно) | 204 / 400       |

### Формат відповіді `GET /books`
```json
{
  "items": [ { "id": "507f1f77bcf86cd799439011", "title": "...", ... } ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

## Змінні оточення

| Змінна          | Обов'язкова | Опис                                                        |
|-----------------|-------------|-------------------------------------------------------------|
| `MONGO_URL`     | так         | Connection string до Mongo (локальна або Atlas `mongodb+srv://...`) |
| `MONGO_DB_NAME` | так         | Назва БД. За замовчуванням `library_db`                     |
| `PORT`          | авто        | Render виставляє сам — uvicorn слухає саме `$PORT`          |
| `RENDER`        | авто        | Render виставляє сам — по ній розуміємо, що ми на проді     |
