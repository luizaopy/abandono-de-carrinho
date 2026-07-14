"""
CarrinhoService: regra de negócio de detecção e recuperação de carrinhos
abandonados. Orquestra Model + EmailService, mas não sabe nada de HTTP/rotas.
"""

from datetime import datetime, timedelta, timezone

from flask import current_app

from models import db
from models.carrinho import Carrinho, StatusCarrinho
from models.email_log import EmailLog
from services.email_service import EmailService


def verificar_carrinhos_abandonados() -> dict:
    """
    Busca carrinhos ABERTOS cujo ultimo_acesso ultrapassou o timeout
    configurado, marca como ABANDONADO, envia e-mail e registra o log.

    Retorna um resumo da execução para uso em logs/endpoint manual.
    """
    timeout_minutos = current_app.config["CARRINHO_TIMEOUT_MINUTOS"]
    limite = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutos)

    carrinhos_abertos = Carrinho.query.filter(
        Carrinho.status == StatusCarrinho.ABERTO,
        Carrinho.ultimo_acesso < limite,
    ).all()

    total_processados = 0
    total_emails_enviados = 0
    total_erros = 0

    for carrinho in carrinhos_abertos:
        carrinho.status = StatusCarrinho.ABANDONADO
        total_processados += 1

        cliente = carrinho.cliente
        status_envio = "SUCESSO"
        erro_detalhe = None

        try:
            EmailService.enviar_email_carrinho_abandonado(
                destinatario=cliente.email, nome=cliente.nome
            )
            total_emails_enviados += 1
            print(f"[EMAIL] Enviado com sucesso para {cliente.email} (carrinho {carrinho.id})")
        except Exception as exc:  # não deve interromper o processamento dos demais
            status_envio = "ERRO"
            erro_detalhe = str(exc)
            total_erros += 1
            print(f"[EMAIL] Falha ao enviar para {cliente.email} (carrinho {carrinho.id}): {exc}")

        log = EmailLog(
            cliente_id=cliente.id,
            carrinho_id=carrinho.id,
            email=cliente.email,
            status_envio=status_envio,
            erro_detalhe=erro_detalhe,
        )
        db.session.add(log)

    db.session.commit()

    resumo = {
        "carrinhos_processados": total_processados,
        "emails_enviados": total_emails_enviados,
        "emails_com_erro": total_erros,
    }
    print(f"[SCHEDULER] Execução concluída: {resumo}")
    return resumo