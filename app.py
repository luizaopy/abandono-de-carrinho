import os

from flask import Flask

from config import Config
from models import db

from models import cliente, produto, carrinho, item_carrinho, email_log 

from routes.clientes import clientes_bp
from routes.produtos import produtos_bp
from routes.carrinhos import carrinhos_bp
from routes.dashboard import dashboard_bp
from routes.jobs import jobs_bp

from services.scheduler import iniciar_scheduler
from utils.responses import error_response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(os.path.dirname(__file__), "database"), exist_ok=True)

    db.init_app(app)

    app.register_blueprint(clientes_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(carrinhos_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)

    @app.errorhandler(404)
    def not_found(_e):
        return error_response("Recurso não encontrado", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error_response("Método não permitido", status_code=405)

    @app.errorhandler(500)
    def internal_error(_e):
        return error_response("Erro interno do servidor", status_code=500)

    with app.app_context():
        db.create_all()
        print("[APP] Banco de dados inicializado.")

    return app


app = create_app()

if __name__ == "__main__":
    iniciar_scheduler(app)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)