# src/app.py
import os
from flask import Flask, render_template
from flask_login import LoginManager, login_required
from core.models import db, User
from auth import auth as auth_blueprint
from api.endpoints import api as api_blueprint, motor
from registros import registros_bp
from admin import admin_bp
from core.models import db, User

# En src/app.py
# ... (imports) ...
app = Flask(__name__)

# --- CONFIGURACIÓN ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///ppam.db' # Usa la de Render o la local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-de-respaldo')
# ... (el resto del archivo se mantiene igual) ...

# Inicialización
db.init_app(app)
motor.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(registros_bp)
app.register_blueprint(admin_bp)

# Ruta Principal
@app.route('/')
@login_required
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)