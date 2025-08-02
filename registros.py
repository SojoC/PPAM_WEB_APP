from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from core.models import db, RegistroActividad

# Creamos un nuevo "plano" para las rutas relacionadas con los registros.
registros_bp = Blueprint('registros', __name__)

@registros_bp.route('/registros/nuevo', methods=['GET', 'POST'])
def nuevo_registro():
    """
    Muestra el formulario para añadir un nuevo registro de actividad
    y maneja el guardado de los datos.
    """
    if request.method == 'POST':
        # --- Recolectamos los datos del formulario ---
        fecha_str = request.form.get('fecha')
        lugar = request.form.get('lugar')
        hora = request.form.get('hora')
        participantes = request.form.get('participantes')
        libros = request.form.get('libros', 0, type=int)
        revistas = request.form.get('revistas', 0, type=int)
        videos = request.form.get('videos', 0, type=int)
        revisitas = request.form.get('revisitas', 0, type=int)

        # --- Validación ---
        if not fecha_str or not lugar or not hora or not participantes:
            flash('Fecha, Lugar, Hora y Participantes son campos obligatorios.', 'danger')
            return redirect(url_for('registros.nuevo_registro'))
        
        # Convertimos la fecha de texto a un objeto de fecha
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # --- Creamos el nuevo registro usando nuestro modelo ---
        nuevo_registro = RegistroActividad(
            fecha=fecha_obj,
            lugar=lugar,
            hora=hora,
            participantes=participantes,
            publicaciones_libros=libros,
            publicaciones_revistas=revistas,
            videos=videos,
            revisitas=revisitas
        )

        # --- Guardamos en la base de datos ---
        db.session.add(nuevo_registro)
        db.session.commit()

        flash('¡Registro de actividad guardado exitosamente!', 'success')
        return redirect(url_for('registros.nuevo_registro'))

    # Si el método es GET, simplemente mostramos el formulario
    return render_template('add_registro.html')