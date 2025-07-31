import os
from flask import Flask, render_template
from core.models import db
from api.endpoints import api, motor # <-- Importamos también el motor

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'ppam.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'cambia-esto-por-una-clave-secreta-larga-y-aleatoria'

# --- INICIALIZACIÓN DE COMPONENTES ---
db.init_app(app) # Inicializamos la base de datos
motor.init_app(app) # <-- AHORA inicializamos el motor, con la app ya configurada

# --- REGISTRAR BLUEPRINTS ---
app.register_blueprint(api)

# --- RUTA PRINCIPAL ---
@app.route('/')
def home():
    return render_template('index.html')

# --- PUNTO DE ENTRADA ---
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)