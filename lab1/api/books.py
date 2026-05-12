
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from schemas.book import BookCreateSchema, BookSchema
from services.book_service import book_service


books_bp = Blueprint("books", __name__)


book_create_schema = BookCreateSchema()
book_response_schema = BookSchema()
books_response_schema = BookSchema(many=True)


@books_bp.get("/books")
def list_books():
    books = book_service.list_books()
    return jsonify(books_response_schema.dump(books)), 200


@books_bp.post("/books")
def create_book():
    json_data = request.get_json(silent=True) or {}
    try:
        data = book_create_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    book = book_service.create_book(data)
    return jsonify(book_response_schema.dump(book)), 201


@books_bp.get("/books/<int:book_id>")
def get_book(book_id: int):
    book = book_service.get_book(book_id)
    if book is None:
        return jsonify({"message": f"Book with id={book_id} not found"}), 404
    return jsonify(book_response_schema.dump(book)), 200


@books_bp.put("/books/<int:book_id>")
def update_book(book_id: int):
    json_data = request.get_json(silent=True) or {}
    try:
        data = book_create_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    updated = book_service.update_book(book_id, data)
    if updated is None:
        return jsonify({"message": f"Book with id={book_id} not found"}), 404
    return jsonify(book_response_schema.dump(updated)), 200


@books_bp.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    deleted = book_service.delete_book(book_id)
    if not deleted:
        return jsonify({"message": f"Book with id={book_id} not found"}), 404
    return "", 204
