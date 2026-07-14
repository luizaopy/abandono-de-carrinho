"""
Configura o APScheduler para executar a verificação de carrinhos
abandonados automaticamente, em background.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from services.carrinho_service import verificar_carrinhos_abandonados

scheduler = BackgroundScheduler()


def iniciar_scheduler(app):
    """
    Registra e inicia o job periódico. Recebe a instância do app para
    poder abrir o app_context dentro do job (necessário para acessar o DB).
    """
    intervalo = app.config["SCHEDULER_INTERVAL_MINUTES"]

    def job_verificar_carrinhos():
        with app.app_context():
            verificar_carrinhos_abandonados()

    scheduler.add_job(
        func=job_verificar_carrinhos,
        trigger="interval",
        minutes=intervalo,
        id="verificar_carrinhos_abandonados",
        replace_existing=True,
    )

    scheduler.start()
    print(f"[SCHEDULER] Scheduler iniciado — execução a cada {intervalo} minuto(s).")