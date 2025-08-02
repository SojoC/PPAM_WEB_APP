from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from core.models import db, User, Role

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users')
@login_required
def user_management():
    # --- Protección por Rol ---
    if current_user.role.name != 'admin':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('home'))

    users = User.query.all()
    roles = Role.query.all()
    return render_template('user_management.html', users=users, roles=roles)

@admin_bp.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    # --- Protección por Rol ---
    if current_user.role.name != 'admin':
        return redirect(url_for('home'))

    # --- Recolectar datos del formulario ---
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role_id = request.form.get('role_id')

    # --- Validación ---
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe.', 'danger')
        return redirect(url_for('admin.user_management'))

    # --- Crear y guardar el nuevo usuario ---
    new_user = User(username=username, email=email, role_id=role_id)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash('Nuevo usuario creado exitosamente.', 'success')
    return redirect(url_for('admin.user_management'))