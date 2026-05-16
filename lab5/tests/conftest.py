import pytest

from main import create_app
from repository.book_repository import book_repository


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app


@pytest.fixture()
def client(app):
    book_repository.clear()
    return app.test_client()
