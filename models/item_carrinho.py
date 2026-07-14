from models import db


class ItemCarrinho(db.Model):
    __tablename__ = "itens_carrinho"

    id = db.Column(db.Integer, primary_key=True)
    carrinho_id = db.Column(db.Integer, db.ForeignKey("carrinhos.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "carrinho_id": self.carrinho_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "preco_unitario": self.produto.preco if self.produto else None,
            "quantidade": self.quantidade,
        }