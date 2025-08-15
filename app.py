import os
from flask import Flask, render_template
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from core.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app():
    app = Flask(__name__)

    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f"sqlite:///{os.path.join(BASE_DIR, 'ppam.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-definitiva-ppam')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from auth import auth as auth_blueprint
    from api.endpoints import api as api_blueprint
    from registros import registros_bp
    from admin import admin_bp

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(registros_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    @login_required
    def home():
        return render_template('index.html')

    return app


# Instancia global para WSGI (Render, Gunicorn)
app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)