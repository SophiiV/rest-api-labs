from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.books import router as books_router
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI): 
    await init_db()
    yield


app = FastAPI(
    title="Library API",
    version="3.0.0",
    description=(
        "REST API для бібліотеки книг. Лабораторна №3: Cursor-based пагінація "
        "(альтернатива до Limit-Offset з Лаби 2) поверх PostgreSQL та "
        "SQLAlchemy 2.0 (async)."
    ),
    lifespan=lifespan,
)
 
app.include_router(books_router, prefix="/api/v1", tags=["Books"])


@app.get("/", include_in_schema=False)
async def root() -> dict: 
    return {"status": "ok", "docs": "/docs"}
