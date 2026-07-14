from flask import Blueprint, request
from marshmallow import ValidationError

from models import db
from models.produto import Produto
from schemas.produto_schema import ProdutoSchema, ProdutoUpdateSchema
from utils.responses import success_response, error_response

produtos_bp = Blueprint("produtos", __name__, url_prefix="/produtos")

produto_schema = ProdutoSchema()
produto_update_schema = ProdutoUpdateSchema()


@produtos_bp.route("", methods=["GET"])
def listar_produtos():
    produtos = Produto.query.order_by(Produto.id).all()
    return success_response([p.to_dict() for p in produtos])


@produtos_bp.route("/<int:produto_id>", methods=["GET"])
def obter_produto(produto_id):
    produto = Produto.query.get(produto_id)
    if not produto:
        return error_response("Produto não encontrado", status_code=404)
    return success_response(produto.to_dict())


@produtos_bp.route("", methods=["POST"])
def criar_produto():
    try:
        dados = produto_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    produto = Produto(nome=dados["nome"], preco=dados["preco"], estoque=dados["estoque"])
    db.session.add(produto)
    db.session.commit()

    print(f"[PRODUTO] Criado: {produto.nome}")
    return success_response(produto.to_dict(), "Produto criado com sucesso", 201)


@produtos_bp.route("/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    produto = Produto.query.get(produto_id)
    if not produto:
        return error_response("Produto não encontrado", status_code=404)

    try:
        dados = produto_update_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    if "nome" in dados:
        produto.nome = dados["nome"]
    if "preco" in dados:
        produto.preco = dados["preco"]
    if "estoque" in dados:
        produto.estoque = dados["estoque"]

    db.session.commit()
    return success_response(produto.to_dict(), "Produto atualizado com sucesso")


@produtos_bp.route("/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    produto = Produto.query.get(produto_id)
    if not produto:
        return error_response("Produto não encontrado", status_code=404)

    db.session.delete(produto)
    db.session.commit()
    return success_response(message="Produto removido com sucesso")