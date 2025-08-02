# src/app.py
import os
from flask import Flask
from flask_login import LoginManager
from core.models import db, User

# Importamos las extensiones desde fuera de la función
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app():
    """Crea y configura la instancia de la aplicación Flask."""
    app = Flask(__name__)
    
    # --- CONFIGURACIÓN ---
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ppam.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-para-un-desarrollo-seguro')

    # --- INICIALIZACIÓN DE COMPONENTES ---
    db.init_app(app)
    login_manager.init_app(app) # La migración ya no se inicializa aquí

    # --- BLUEPRINTS ---
    from auth import auth as auth_blueprint
    from api.endpoints import api as api_blueprint, motor
    from registros import registros_bp
    from admin import admin_bp
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(registros_bp)
    app.register_blueprint(admin_bp)

    # El motor aprende DESPUÉS de que todo está configurado
    with app.app_context():
        motor.init_app(app)

    # --- RUTA PRINCIPAL ---
    from flask_login import login_required
    from flask import render_template

    @app.route('/')
    @login_required
    def home():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)