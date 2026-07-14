"""
Padroniza o formato de todas as respostas JSON da API.
"""

from flask import jsonify


def success_response(data=None, message="Operação realizada com sucesso", status_code=200):
    return (
        jsonify({"success": True, "message": message, "data": data if data is not None else {}}),
        status_code,
    )


def error_response(message="Erro ao processar a requisição", errors=None, status_code=400):
    return (
        jsonify({"success": False, "message": message, "errors": errors or []}),
        status_code,
    )