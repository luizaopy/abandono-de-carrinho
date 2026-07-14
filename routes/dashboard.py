from flask import Blueprint

from models.cliente import Cliente
from models.produto import Produto
from models.carrinho import Carrinho, StatusCarrinho
from models.email_log import EmailLog
from utils.responses import success_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("", methods=["GET"])
def obter_dashboard():
    total_clientes = Cliente.query.count()
    total_produtos = Produto.query.count()

    carrinhos_abertos = Carrinho.query.filter_by(status=StatusCarrinho.ABERTO).count()
    carrinhos_abandonados = Carrinho.query.filter_by(
        status=StatusCarrinho.ABANDONADO
    ).count()
    carrinhos_finalizados = Carrinho.query.filter_by(
        status=StatusCarrinho.FINALIZADO
    ).count()

    emails_enviados = EmailLog.query.filter_by(status_envio="SUCESSO").count()

    # Uma "compra recuperada" é um carrinho FINALIZADO que já teve pelo menos
    # um e-mail de abandono registrado (ou seja, foi abandonado e depois
    # finalizado após o contato).
    carrinhos_com_email = {log.carrinho_id for log in EmailLog.query.all()}
    compras_recuperadas = Carrinho.query.filter(
        Carrinho.status == StatusCarrinho.FINALIZADO,
        Carrinho.id.in_(carrinhos_com_email) if carrinhos_com_email else False,
    ).count()

    data = {
        "total_clientes": total_clientes,
        "total_produtos": total_produtos,
        "carrinhos_abertos": carrinhos_abertos,
        "carrinhos_abandonados": carrinhos_abandonados,
        "carrinhos_finalizados": carrinhos_finalizados,
        "emails_enviados": emails_enviados,
        "compras_recuperadas": compras_recuperadas,
    }
    return success_response(data)