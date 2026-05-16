from marshmallow import Schema, fields, validate


class BookCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200),
        metadata={"description": "Назва книги"},
    )
    author = fields.String(
        required=True,
        validate=validate.Length(min=1, max=120),
        metadata={"description": "Автор книги"},
    )
    year = fields.Integer(
        required=True,
        validate=validate.Range(min=1450, max=2100),
        metadata={"description": "Рік видання (1450..2100)"},
    )
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
        metadata={"description": "Опис книги (опційно)"},
    )


class BookUpdateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    author = fields.String(required=True, validate=validate.Length(min=1, max=120))
    year = fields.Integer(required=True, validate=validate.Range(min=1450, max=2100))
    description = fields.String(required=False, allow_none=True,
                                validate=validate.Length(max=1000))


class BookResponseSchema(Schema):
    id = fields.Integer()
    title = fields.String()
    author = fields.String()
    year = fields.Integer()
    description = fields.String(allow_none=True)
