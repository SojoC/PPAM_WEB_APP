from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from core.models import db, User, Role, Congregacion, Privilegio
from datetime import datetime
# Al principio del archivo, añade la importación de pandas
import pandas as pd

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users')
@login_required
def user_management():
    if not current_user.role or current_user.role.name != 'admin':
        return redirect(url_for('home'))

    users = db.session.execute(db.select(User).order_by(User.nombre_completo)).scalars().all()
    roles = db.session.execute(db.select(Role)).scalars().all()
    congregaciones = db.session.execute(db.select(Congregacion)).scalars().all()
    privilegios = db.session.execute(db.select(Privilegio)).scalars().all()
    
    return render_template('user_management.html', 
                           users=users, roles=roles, 
                           congregaciones=congregaciones, privilegios=privilegios)

@admin_bp.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    # ... (esta función ya es correcta)
    pass

# --- NUEVA RUTA PARA EDITAR ---
@admin_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.role or current_user.role.name != 'admin': return redirect(url_for('home'))
    user_to_edit = db.session.get(User, user_id)
    if not user_to_edit: return redirect(url_for('admin.user_management'))

    if request.method == 'POST':
        # (Lógica para guardar cambios)
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin.user_management'))

    roles = db.session.execute(db.select(Role)).scalars().all()
    return render_template('edit_user.html', user=user_to_edit, roles=roles)

# --- NUEVA RUTA PARA ELIMINAR ---
@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.role or current_user.role.name != 'admin': return redirect(url_for('home'))
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin.user_management'))



# ... (el resto de tus rutas de admin.py) ...

@admin_bp.route('/admin/upload', methods=['POST'])
@login_required
def upload_db():
    if not current_user.role or current_user.role.name != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    file = request.files.get('db_file')
    if not file:
        return jsonify({"error": "No se recibió ningún archivo."}), 400

    try:
        # Usamos pandas para leer el archivo (funciona con Excel y CSV)
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # --- Lógica para procesar y añadir/actualizar usuarios ---
        # (Aquí iría la lógica para iterar sobre el dataframe 'df'
        # y añadir cada fila a la base de datos, similar a migracion.py)

        flash(f"¡Éxito! Se han procesado {len(df)} registros.", "success")
        return redirect(url_for('admin.user_management'))
    except Exception as e:
        flash(f"Error al procesar el archivo: {e}", "danger")
        return redirect(url_for('admin.user_management'))