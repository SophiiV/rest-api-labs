"""
Точка входу застосунку FastAPI.

Відповідальність:
  - Створити екземпляр FastAPI
  - При старті — під'єднатись до MongoDB (lifespan-хук)
  - При зупинці — закрити з'єднання
  - Підключити CORS-middleware (щоб API можна було викликати з будь-якого фронта)
  - Підключити роутер /api/v1/books
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.books import router as books_router
from database import close_mongo_connection, connect_to_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan-хук FastAPI:
      - перед стартом: ініціалізуємо Mongo-клієнт
      - після зупинки: коректно закриваємо з'єднання
    """
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Library API",
    version="5.0.0",
    description=(
        "REST API для бібліотеки книг. "
        "Самостійна робота: деплой на Render.com + MongoDB Atlas."
    ),
    lifespan=lifespan,
)

# ----------------------------------------------------------------------
# CORS — дозволяємо звертатись до API з будь-якого origin.
# Для навчального проєкту виставляємо "*", у реальному продакшні
# сюди пишуть список довірених доменів фронтенду.
# ----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Версіонування API — /api/v1/...
app.include_router(books_router, prefix="/api/v1", tags=["Books"])


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """
    Health-check на кореневому шляху.

    Render.com пінгуватиме саме цей endpoint (див. healthCheckPath у render.yaml).
    Якщо відповіді нема — Render вважатиме сервіс недоступним і рестартне контейнер.
    """
    return {
        "status": "ok",
        "service": "Library API",
        "version": "5.0.0",
        "docs": "/docs",
        "environment": os.getenv("RENDER", "local"),
    }
