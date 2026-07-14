import enum
from datetime import datetime, timezone

from models import db


class StatusCarrinho(str, enum.Enum):
    ABERTO = "ABERTO"
    FINALIZADO = "FINALIZADO"
    ABANDONADO = "ABANDONADO"


class Carrinho(db.Model):
    __tablename__ = "carrinhos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    status = db.Column(
        db.Enum(StatusCarrinho), nullable=False, default=StatusCarrinho.ABERTO
    )

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    ultimo_acesso = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    itens = db.relationship(
        "ItemCarrinho", backref="carrinho", lazy=True, cascade="all, delete-orphan"
    )
    email_logs = db.relationship("EmailLog", backref="carrinho", lazy=True)

    def to_dict(self, incluir_itens=True):
        data = {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ultimo_acesso": self.ultimo_acesso.isoformat()
            if self.ultimo_acesso
            else None,
        }
        if incluir_itens:
            data["itens"] = [item.to_dict() for item in self.itens]
            data["total"] = sum(
                item.quantidade * item.produto.preco for item in self.itens
            )
        return data