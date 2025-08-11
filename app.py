import os
from flask import Flask, render_template
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from core.models import db, User

# --- Instancias de Extensiones (se definen fuera de la función) ---
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    """Función que Flask-Login usa para cargar un usuario en cada petición."""
    return db.session.get(User, int(user_id))

def create_app():
    """Crea y configura la instancia de la aplicación Flask (Patrón Factory)."""
    app = Flask(__name__)

    # --- CONFIGURACIÓN ---
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f"sqlite:///{os.path.join(BASE_DIR, 'ppam.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-definitiva-ppam')

    # --- INICIALIZACIÓN DE COMPONENTES ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- BLUEPRINTS (Importados dentro para evitar errores de importación circular) ---
    from auth import auth as auth_blueprint
    from api.endpoints import api as api_blueprint, motor
    from registros import registros_bp
    from admin import admin_bp
    # --- REGISTRAR COMANDOS DE CLI ---
    from commands import seed
    app.cli.add_command(seed)
    
    # REGISTRO DE TODOS LOS MÓDULOS
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(registros_bp)
    app.register_blueprint(admin_bp)

    # --- INICIALIZACIÓN DEL MOTOR (Después de que todo esté listo) ---
    with app.app_context():
        motor.init_app(app)

    # --- RUTA PRINCIPAL ---
    @app.route('/')
    @login_required
    def home():
        return render_template('index.html')

    # LA LÍNEA 'return app' DEBE ESTAR AL FINAL DE LA FUNCIÓN
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)