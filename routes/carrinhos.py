from datetime import datetime, timezone

from flask import Blueprint, request
from marshmallow import ValidationError

from models import db
from models.cliente import Cliente
from models.produto import Produto
from models.carrinho import Carrinho, StatusCarrinho
from models.item_carrinho import ItemCarrinho
from schemas.carrinho_schema import CarrinhoCreateSchema, ItemCarrinhoSchema
from utils.responses import success_response, error_response

carrinhos_bp = Blueprint("carrinhos", __name__, url_prefix="/carrinhos")

carrinho_create_schema = CarrinhoCreateSchema()
item_carrinho_schema = ItemCarrinhoSchema()


def _tocar_carrinho(carrinho: Carrinho):
    """Atualiza o timestamp de último acesso sempre que o carrinho é manipulado."""
    carrinho.ultimo_acesso = datetime.now(timezone.utc)


@carrinhos_bp.route("", methods=["POST"])
def criar_carrinho():
    try:
        dados = carrinho_create_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    cliente = Cliente.query.get(dados["cliente_id"])
    if not cliente:
        return error_response("Cliente não encontrado", status_code=404)

    carrinho = Carrinho(cliente_id=cliente.id, status=StatusCarrinho.ABERTO)
    db.session.add(carrinho)
    db.session.commit()

    print(f"[CARRINHO] Criado: id={carrinho.id} cliente_id={cliente.id}")
    return success_response(carrinho.to_dict(), "Carrinho criado com sucesso", 201)


@carrinhos_bp.route("", methods=["GET"])
def listar_carrinhos():
    status_filtro = request.args.get("status")
    query = Carrinho.query

    if status_filtro:
        try:
            status_enum = StatusCarrinho(status_filtro.upper())
            query = query.filter(Carrinho.status == status_enum)
        except ValueError:
            return error_response(
                "Status inválido. Use ABERTO, FINALIZADO ou ABANDONADO", status_code=422
            )

    carrinhos = query.order_by(Carrinho.id).all()
    return success_response([c.to_dict(incluir_itens=False) for c in carrinhos])


@carrinhos_bp.route("/<int:carrinho_id>", methods=["GET"])
def obter_carrinho(carrinho_id):
    carrinho = Carrinho.query.get(carrinho_id)
    if not carrinho:
        return error_response("Carrinho não encontrado", status_code=404)
    return success_response(carrinho.to_dict())


@carrinhos_bp.route("/<int:carrinho_id>/produto", methods=["POST"])
def adicionar_produto(carrinho_id):
    carrinho = Carrinho.query.get(carrinho_id)
    if not carrinho:
        return error_response("Carrinho não encontrado", status_code=404)

    if carrinho.status != StatusCarrinho.ABERTO:
        return error_response(
            f"Não é possível alterar um carrinho com status {carrinho.status.value}",
            status_code=409,
        )

    try:
        dados = item_carrinho_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    produto = Produto.query.get(dados["produto_id"])
    if not produto:
        return error_response("Produto não encontrado", status_code=404)

    if produto.estoque < dados["quantidade"]:
        return error_response("Estoque insuficiente para este produto", status_code=409)

    item_existente = ItemCarrinho.query.filter_by(
        carrinho_id=carrinho.id, produto_id=produto.id
    ).first()

    if item_existente:
        item_existente.quantidade += dados["quantidade"]
    else:
        item_existente = ItemCarrinho(
            carrinho_id=carrinho.id,
            produto_id=produto.id,
            quantidade=dados["quantidade"],
        )
        db.session.add(item_existente)

    _tocar_carrinho(carrinho)
    db.session.commit()

    return success_response(carrinho.to_dict(), "Produto adicionado ao carrinho")


@carrinhos_bp.route("/<int:carrinho_id>/produto/<int:produto_id>", methods=["DELETE"])
def remover_produto(carrinho_id, produto_id):
    carrinho = Carrinho.query.get(carrinho_id)
    if not carrinho:
        return error_response("Carrinho não encontrado", status_code=404)

    item = ItemCarrinho.query.filter_by(
        carrinho_id=carrinho.id, produto_id=produto_id
    ).first()
    if not item:
        return error_response("Produto não está no carrinho", status_code=404)

    db.session.delete(item)
    _tocar_carrinho(carrinho)
    db.session.commit()

    return success_response(carrinho.to_dict(), "Produto removido do carrinho")


@carrinhos_bp.route("/<int:carrinho_id>/checkout", methods=["POST"])
def checkout(carrinho_id):
    carrinho = Carrinho.query.get(carrinho_id)
    if not carrinho:
        return error_response("Carrinho não encontrado", status_code=404)

    # Permite finalizar tanto carrinhos ABERTOS quanto ABANDONADOS
    # (este último caracteriza uma "compra recuperada").
    if carrinho.status not in (StatusCarrinho.ABERTO, StatusCarrinho.ABANDONADO):
        return error_response(
            f"Não é possível finalizar um carrinho com status {carrinho.status.value}",
            status_code=409,
        )

    if not carrinho.itens:
        return error_response("Carrinho vazio não pode ser finalizado", status_code=422)

    for item in carrinho.itens:
        if item.produto.estoque < item.quantidade:
            return error_response(
                f"Estoque insuficiente para o produto '{item.produto.nome}'",
                status_code=409,
            )

    for item in carrinho.itens:
        item.produto.estoque -= item.quantidade

    carrinho.status = StatusCarrinho.FINALIZADO
    _tocar_carrinho(carrinho)
    db.session.commit()

    print(f"[CHECKOUT] Carrinho {carrinho.id} finalizado com sucesso")
    return success_response(carrinho.to_dict(), "Checkout realizado com sucesso")