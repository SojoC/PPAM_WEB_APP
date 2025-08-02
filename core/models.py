# src/core/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

user_privilegios = db.Table('user_privilegios',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('privilegio_id', db.Integer, db.ForeignKey('privilegios.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    fecha_bautismo = db.Column(db.Date, nullable=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    congregacion_id = db.Column(db.Integer, db.ForeignKey('congregaciones.id'))
    privilegios = db.relationship('Privilegio', secondary=user_privilegios, backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

class Privilegio(db.Model):
    __tablename__ = 'privilegios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class Congregacion(db.Model):
    __tablename__ = 'congregaciones'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    circuito = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='congregacion', lazy=True)
    territorios = db.relationship('Territorio', backref='congregacion', lazy=True)

class Territorio(db.Model):
    __tablename__ = 'territorios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    congregacion_id = db.Column(db.Integer, db.ForeignKey('congregaciones.id'), nullable=False)

class RegistroActividad(db.Model):
    __tablename__ = 'registros_actividad'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    lugar = db.Column(db.String(150), nullable=False)
    hora = db.Column(db.String(50), nullable=False)
    participantes = db.Column(db.String(255), nullable=False)
    publicaciones_libros = db.Column(db.Integer, default=0)
    publicaciones_revistas = db.Column(db.Integer, default=0)
    videos = db.Column(db.Integer, default=0)
    revisitas = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))