import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from core.models import db, User

# --- Instancias de Extensiones ---
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    """Crea y configura la instancia de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Asegúrate de tener tu configuración

    # Inicializa extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # --- BLUEPRINTS ---
    from auth import auth as auth_blueprint
    from api.endpoints import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    from registros import registros_bp
    from admin import admin_bp

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(registros_bp)
    app.register_blueprint(admin_bp)

    @api.route('/buscar', methods=['POST'])
    def buscar():
        # Lógica para manejar la búsqueda
        pass

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)