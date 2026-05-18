from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.books import router as books_router
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan-хук FastAPI:
      - перед стартом: створюємо таблиці  
      - після зупинки: cleanup 
    """
    await init_db()
    yield


app = FastAPI(
    title="Library API",
    version="6.0.0",
    description=(
        "REST API для бібліотеки книг. Лабораторна №6: автентифікація та "
        "авторизація через JWT (access + refresh tokens), refresh token "
        "rotation. Усі ендпоінти /books захищені — щоб ними скористатись, "
        "треба отримати access-токен через /auth/login і додати в кожен "
        "запит заголовок `Authorization: Bearer <access_token>`."
    ),
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1", tags=["Books"])


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """ health-check на кореневому шляху."""
    return {"status": "ok", "docs": "/docs"}
