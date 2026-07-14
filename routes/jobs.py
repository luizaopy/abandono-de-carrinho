from flask import Blueprint

from services.carrinho_service import verificar_carrinhos_abandonados
from utils.responses import success_response

jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")


@jobs_bp.route("/verificar-carrinhos", methods=["POST"])
def executar_verificacao_manual():
    resumo = verificar_carrinhos_abandonados()
    return success_response(resumo, "Verificação de carrinhos executada com sucesso")