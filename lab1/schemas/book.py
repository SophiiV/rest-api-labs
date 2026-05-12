"""
ми перевіряємо:
  - title: обовʼязкове, рядок 1..200 символів
  - author: обовʼязкове, рядок 1..120 символів
  - year: обовʼязкове, ціле число у діапазоні [1450; 2100]
  - description: необовʼязкове, рядок до 1000 символів
"""
from marshmallow import Schema, fields, validate


class BookCreateSchema(Schema):
    """Схема для створення/повного оновлення книги (POST і PUT)."""

    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200),
        error_messages={"required": "Поле 'title' є обовʼязковим."},
    )
    author = fields.String(
        required=True,
        validate=validate.Length(min=1, max=120),
        error_messages={"required": "Поле 'author' є обовʼязковим."},
    )
    year = fields.Integer(
        required=True,
        validate=validate.Range(min=1450, max=2100),
        error_messages={"required": "Поле 'year' є обовʼязковим."},
    )
    description = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=1000),
    )


class BookSchema(Schema):
    """Схема відповіді (вихідне представлення книги)."""

    id = fields.Integer()
    title = fields.String()
    author = fields.String()
    year = fields.Integer()
    description = fields.String(allow_none=True)
