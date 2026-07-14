from marshmallow import Schema, fields, validate


class CarrinhoCreateSchema(Schema):
    cliente_id = fields.Integer(required=True, validate=validate.Range(min=1))


class ItemCarrinhoSchema(Schema):
    produto_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantidade = fields.Integer(required=True, validate=validate.Range(min=1))