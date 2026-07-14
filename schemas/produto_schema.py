from marshmallow import Schema, fields, validate


class ProdutoSchema(Schema):
    nome = fields.String(required=True, validate=validate.Length(min=1, max=120))
    preco = fields.Float(required=True, validate=validate.Range(min=0.01))
    estoque = fields.Integer(required=True, validate=validate.Range(min=0))


class ProdutoUpdateSchema(Schema):
    nome = fields.String(required=False, validate=validate.Length(min=1, max=120))
    preco = fields.Float(required=False, validate=validate.Range(min=0.01))
    estoque = fields.Integer(required=False, validate=validate.Range(min=0))