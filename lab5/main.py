from flask import Flask, redirect
from flask_restful import Api
from flasgger import Swagger

from api.books import BookListResource, BookResource


swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Library API",
        "description": (
            "REST API для бібліотеки книг. Лабораторна №5: реалізація API "
            "на Flask + Flask-RESTful із автогенерованою Swagger-документацією "
            "через flasgger."
        ),
        "version": "5.0.0",
        "contact": {"name": "Vladyslav", "email": "muzikaeng@gmail.com"},
    },
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "tags": [
        {"name": "Books", "description": "Операції з книгами бібліотеки"},
    ],
    "definitions": {
        "Book": {
            "type": "object",
            "required": ["id", "title", "author", "year"],
            "properties": {
                "id": {"type": "integer", "example": 1},
                "title": {"type": "string", "example": "Кобзар"},
                "author": {"type": "string", "example": "Тарас Шевченко"},
                "year": {"type": "integer", "example": 1840},
                "description": {
                    "type": "string",
                    "example": "Збірка поезій українського поета",
                    "x-nullable": True,
                },
            },
        },
        "BookCreate": {
            "type": "object",
            "required": ["title", "author", "year"],
            "properties": {
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200,
                    "example": "1984",
                },
                "author": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 120,
                    "example": "George Orwell",
                },
                "year": {
                    "type": "integer",
                    "minimum": 1450,
                    "maximum": 2100,
                    "example": 1949,
                },
                "description": {
                    "type": "string",
                    "maxLength": 1000,
                    "example": "Антиутопія",
                },
            },
        },
        "ValidationError": {
            "type": "object",
            "properties": {
                "errors": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "example": {"year": ["Must be greater than or equal to 1450."]},
                },
            },
        },
        "NotFound": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Book with id=42 not found"},
            },
        },
    },
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def create_app() -> Flask:
    app = Flask(__name__)

    Swagger(app, template=swagger_template, config=swagger_config)

    api = Api(app)
    api.add_resource(BookListResource, "/api/v1/books")
    api.add_resource(BookResource, "/api/v1/books/<int:book_id>")

    @app.get("/")
    def index():
        return redirect("/apidocs/")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
