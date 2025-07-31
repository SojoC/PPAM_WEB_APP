from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# --- MODELOS DE AUTENTICACIÓN ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

# --- MODELOS DE LA APLICACIÓN (PPAM) ---
class Congregacion(db.Model):
    """Modelo para la tabla de Congregaciones."""
    __tablename__ = 'Congregaciones'
    CongregacionID = db.Column(db.Integer, primary_key=True)
    NombreCongregacion = db.Column(db.String(100), nullable=False)
    Circuito = db.Column(db.String(100), nullable=False)
    
    # Relaciones: Una congregación tiene muchos contactos y territorios
    contactos = db.relationship('Contact', backref='congregacion', lazy=True)
    territorios = db.relationship('Territorio', backref='congregacion', lazy=True)

class Territorio(db.Model):
    """Modelo para la tabla de Territorios."""
    __tablename__ = 'Territorios'
    TerritorioID = db.Column(db.Integer, primary_key=True)
    NombreTerritorio = db.Column(db.String(100), nullable=False)
    CongregacionID_FK = db.Column(db.Integer, db.ForeignKey('Congregaciones.CongregacionID'), nullable=False)

class Contact(db.Model):
    """Modelo para la tabla de Contactos."""
    __tablename__ = 'Contactos'
    ContactoID = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(150), nullable=False)
    Telefono = db.Column(db.String(50), nullable=True)
    
    # Relación: Un contacto pertenece a una congregación
    CongregacionID_FK = db.Column(db.Integer, db.ForeignKey('Congregaciones.CongregacionID'), nullable=False)