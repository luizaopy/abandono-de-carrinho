from datetime import datetime, timezone

from models import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    carrinhos = db.relationship(
        "Carrinho", backref="cliente", lazy=True, cascade="all, delete-orphan"
    )
    email_logs = db.relationship(
        "EmailLog", backref="cliente", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }