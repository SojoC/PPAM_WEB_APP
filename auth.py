from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from core.models import db, User
from core.models import db, User 


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Buscamos al usuario en la base de datos
        user = User.query.filter_by(username=username).first()

        # Verificamos si el usuario existe y si la contraseña es correcta
        if not user or not user.check_password(password):
            flash('Usuario o contraseña incorrectos. Por favor, verifica tus datos.', 'danger')
            return redirect(url_for('auth.login'))

        # Si todo es correcto, iniciamos la sesión del usuario
        login_user(user)
        return redirect(url_for('home')) # Redirigimos a la página principal

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))