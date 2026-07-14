from marshmallow import Schema, fields, validate


class ClienteSchema(Schema):
    nome = fields.String(required=True, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=True)


class ClienteUpdateSchema(Schema):
    nome = fields.String(required=False, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=False)