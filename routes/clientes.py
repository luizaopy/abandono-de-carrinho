from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db
from models.cliente import Cliente
from schemas.cliente_schema import ClienteSchema, ClienteUpdateSchema
from utils.responses import success_response, error_response

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

cliente_schema = ClienteSchema()
cliente_update_schema = ClienteUpdateSchema()


@clientes_bp.route("", methods=["GET"])
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.id).all()
    return success_response([c.to_dict() for c in clientes])


@clientes_bp.route("/<int:cliente_id>", methods=["GET"])
def obter_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return error_response("Cliente não encontrado", status_code=404)
    return success_response(cliente.to_dict())


@clientes_bp.route("", methods=["POST"])
def criar_cliente():
    try:
        dados = cliente_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    cliente = Cliente(nome=dados["nome"], email=dados["email"])
    try:
        db.session.add(cliente)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("E-mail já cadastrado", status_code=409)

    print(f"[CLIENTE] Criado: {cliente.email}")
    return success_response(cliente.to_dict(), "Cliente criado com sucesso", 201)


@clientes_bp.route("/<int:cliente_id>", methods=["PUT"])
def atualizar_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return error_response("Cliente não encontrado", status_code=404)

    try:
        dados = cliente_update_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return error_response("Dados inválidos", errors=err.messages, status_code=422)

    if "nome" in dados:
        cliente.nome = dados["nome"]
    if "email" in dados:
        cliente.email = dados["email"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("E-mail já cadastrado", status_code=409)

    return success_response(cliente.to_dict(), "Cliente atualizado com sucesso")


@clientes_bp.route("/<int:cliente_id>", methods=["DELETE"])
def deletar_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return error_response("Cliente não encontrado", status_code=404)

    db.session.delete(cliente)
    db.session.commit()
    return success_response(message="Cliente removido com sucesso")