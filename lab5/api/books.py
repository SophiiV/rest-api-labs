from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from schemas.book import BookCreateSchema, BookUpdateSchema, BookResponseSchema
from services.book_service import book_service

book_create_schema = BookCreateSchema()
book_update_schema = BookUpdateSchema()
book_response_schema = BookResponseSchema()


class BookListResource(Resource):

    def get(self):
        """
        Отримати список усіх книг
        ---
        tags:
          - Books
        summary: Список книг
        description: Повертає масив усіх книг, що збережені в бібліотеці.
        responses:
          200:
            description: Успішна відповідь зі списком книг
            schema:
              type: array
              items:
                $ref: '#/definitions/Book'
            examples:
              application/json:
                - id: 1
                  title: "Кобзар"
                  author: "Тарас Шевченко"
                  year: 1840
                  description: "Збірка поезій"
        """
        books = book_service.list_books()
        return book_response_schema.dump(books, many=True), 200

    def post(self):
        """
        Створити нову книгу
        ---
        tags:
          - Books
        summary: Створення книги
        description: |
          Створює новий запис книги. Повертає створену книгу разом із
          автогенерованим `id`.
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            description: Дані нової книги
            schema:
              $ref: '#/definitions/BookCreate'
        responses:
          201:
            description: Книгу створено
            schema:
              $ref: '#/definitions/Book'
          400:
            description: Помилка валідації (некоректні дані запиту)
            schema:
              $ref: '#/definitions/ValidationError'
        """
        json_data = request.get_json(silent=True) or {}
        try:
            data = book_create_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        book = book_service.create_book(data)
        return book_response_schema.dump(book), 201


class BookResource(Resource):

    def get(self, book_id: int):
        """
        Отримати книгу за id
        ---
        tags:
          - Books
        summary: Отримання книги
        parameters:
          - in: path
            name: book_id
            type: integer
            required: true
            description: Ідентифікатор книги
        responses:
          200:
            description: Книгу знайдено
            schema:
              $ref: '#/definitions/Book'
          404:
            description: Книгу з таким id не знайдено
            schema:
              $ref: '#/definitions/NotFound'
        """
        book = book_service.get_book(book_id)
        if book is None:
            return {"message": f"Book with id={book_id} not found"}, 404
        return book_response_schema.dump(book), 200

    def put(self, book_id: int):
        """
        Повністю оновити книгу
        ---
        tags:
          - Books
        summary: Оновлення книги (PUT)
        description: |
          Замінює всі поля книги новими значеннями.
          Якщо книги з таким id не існує — повертається 404.
        consumes:
          - application/json
        parameters:
          - in: path
            name: book_id
            type: integer
            required: true
            description: Ідентифікатор книги
          - in: body
            name: body
            required: true
            schema:
              $ref: '#/definitions/BookCreate'
        responses:
          200:
            description: Книгу оновлено
            schema:
              $ref: '#/definitions/Book'
          400:
            description: Помилка валідації
            schema:
              $ref: '#/definitions/ValidationError'
          404:
            description: Книгу не знайдено
            schema:
              $ref: '#/definitions/NotFound'
        """
        json_data = request.get_json(silent=True) or {}
        try:
            data = book_update_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        updated = book_service.update_book(book_id, data)
        if updated is None:
            return {"message": f"Book with id={book_id} not found"}, 404
        return book_response_schema.dump(updated), 200

    def delete(self, book_id: int):
        """
        Видалити книгу
        ---
        tags:
          - Books
        summary: Видалення книги
        parameters:
          - in: path
            name: book_id
            type: integer
            required: true
            description: Ідентифікатор книги
        responses:
          204:
            description: Книгу видалено (без тіла відповіді)
          404:
            description: Книгу не знайдено
            schema:
              $ref: '#/definitions/NotFound'
        """
        ok = book_service.delete_book(book_id)
        if not ok:
            return {"message": f"Book with id={book_id} not found"}, 404
        return "", 204
