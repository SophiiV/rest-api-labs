from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.books import router as books_router
from core.redis_client import create_redis_client
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.redis = create_redis_client()
    try:
        yield
    finally:
        await app.state.redis.close()


app = FastAPI(
    title="Library API",
    version="7.0.0",
    description=(
        "Лабораторна №7:"
        "Rate Limiter (Redis, метод фіксованого вікна). Авторизованим юзерам — "
        "10 запитів/хв, анонімним — 2 запити/хв."
    ),
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1", tags=["Books"])


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"status": "ok", "docs": "/docs"}
