from datetime import datetime, timezone

from models import db


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    carrinho_id = db.Column(db.Integer, db.ForeignKey("carrinhos.id"), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status_envio = db.Column(db.String(20), nullable=False)  # SUCESSO / ERRO
    data_envio = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    erro_detalhe = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "carrinho_id": self.carrinho_id,
            "email": self.email,
            "status_envio": self.status_envio,
            "data_envio": self.data_envio.isoformat() if self.data_envio else None,
            "erro_detalhe": self.erro_detalhe,
        }