"""
EmailService: responsável exclusivamente pelo envio de e-mails via SMTP.
Não conhece models nem regras de negócio — apenas envia o que recebe.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


class EmailService:
    ASSUNTO_CARRINHO_ABANDONADO = "Você esqueceu produtos no seu carrinho"

    @staticmethod
    def _montar_corpo_html(nome: str) -> str:
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <p>Olá {nome},</p>
            <p>percebemos que você deixou produtos no carrinho. Eles ainda estão
            disponíveis. Volte e finalize sua compra.</p>
          </body>
        </html>
        """

    @classmethod
    def enviar_email_carrinho_abandonado(cls, destinatario: str, nome: str) -> None:
        """
        Envia o e-mail de recuperação de carrinho abandonado.
        Lança exceção em caso de falha — quem chama decide como tratar/logar.
        """
        smtp_server = current_app.config["SMTP_SERVER"]
        smtp_port = current_app.config["SMTP_PORT"]
        smtp_user = current_app.config["SMTP_USER"]
        smtp_password = current_app.config["SMTP_PASSWORD"]

        mensagem = MIMEMultipart("alternative")
        mensagem["Subject"] = cls.ASSUNTO_CARRINHO_ABANDONADO
        mensagem["From"] = smtp_user
        mensagem["To"] = destinatario

        corpo_html = cls._montar_corpo_html(nome)
        mensagem.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as servidor:
            servidor.starttls()
            servidor.login(smtp_user, smtp_password)
            servidor.sendmail(smtp_user, destinatario, mensagem.as_string())