# src/manage.py
from flask_migrate import Migrate
from app import create_app
from core.models import db

# Creamos una instancia de la app usando nuestra función factory
app = create_app()

# Conectamos la herramienta de migración a nuestra app y base de datos
migrate = Migrate(app, db)

# Este archivo ahora es el centro de control para los comandos de la base de datos.