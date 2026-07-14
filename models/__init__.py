"""
Instância única do SQLAlchemy, compartilhada por todos os models.
Evita imports circulares entre app.py e os módulos de model.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
