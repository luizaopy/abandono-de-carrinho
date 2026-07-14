"""
Testes básicos de fumaça (smoke tests) da API.
Executar com: pytest tests/ -v
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    test_app = create_app()
    test_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        }
    )

    with test_app.app_context():
        db.drop_all()
        db.create_all()

    yield test_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


def test_criar_cliente(client):
    resp = client.post("/clientes", json={"nome": "João Silva", "email": "joao@teste.com"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == "joao@teste.com"


def test_criar_cliente_email_invalido(client):
    resp = client.post("/clientes", json={"nome": "João", "email": "email-invalido"})
    assert resp.status_code == 422
    assert resp.get_json()["success"] is False


def test_criar_produto(client):
    resp = client.post("/produtos", json={"nome": "Camiseta", "preco": 49.9, "estoque": 10})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["nome"] == "Camiseta"


def test_criar_produto_preco_invalido(client):
    resp = client.post("/produtos", json={"nome": "Camiseta", "preco": -1, "estoque": 10})
    assert resp.status_code == 422


def test_fluxo_completo_carrinho(client):
    cliente = client.post(
        "/clientes", json={"nome": "Maria", "email": "maria@teste.com"}
    ).get_json()["data"]
    produto = client.post(
        "/produtos", json={"nome": "Mouse", "preco": 100.0, "estoque": 5}
    ).get_json()["data"]

    carrinho = client.post("/carrinhos", json={"cliente_id": cliente["id"]}).get_json()[
        "data"
    ]
    assert carrinho["status"] == "ABERTO"

    resp_item = client.post(
        f"/carrinhos/{carrinho['id']}/produto",
        json={"produto_id": produto["id"], "quantidade": 2},
    )
    assert resp_item.status_code == 200
    assert resp_item.get_json()["data"]["total"] == 200.0

    resp_checkout = client.post(f"/carrinhos/{carrinho['id']}/checkout")
    assert resp_checkout.status_code == 200
    assert resp_checkout.get_json()["data"]["status"] == "FINALIZADO"


def test_dashboard(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "total_clientes" in data
    assert "compras_recuperadas" in data


def test_job_manual(client):
    resp = client.post("/jobs/verificar-carrinhos")
    assert resp.status_code == 200
    assert "carrinhos_processados" in resp.get_json()["data"]
