from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.books import router as books_router
from database import close_mongo_connection, connect_to_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and close MongoDB connection."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Library API",
    version="4.0.0",
    description="REST API for books library (pagination, MongoDB, motor, Docker).",
    lifespan=lifespan,
)

app.include_router(books_router, prefix="/api/v1", tags=["Books"])


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "docs": "/docs"}