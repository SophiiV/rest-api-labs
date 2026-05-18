import uvicorn
from fastapi import FastAPI

from api.books import router as books_router

app = FastAPI(
    title="Library API",
    description="REST API для бібліотеки книг. Лабораторна робота №1.",
    version="1.0.0",
)

app.include_router(books_router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root() -> dict:
    return {
        "status": "ok",
        "service": "Library API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
