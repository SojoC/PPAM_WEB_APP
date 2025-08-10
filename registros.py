from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from core.models import db, RegistroActividad
from flask_login import login_required

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

# En src/registros.py

# ... (el código existente se mantiene igual arriba) ...

# --- NUEVA RUTA PARA VER LOS REGISTROS ---
@registros_bp.route('/registros')

@login_required # Protegemos la página para que solo usuarios logueados puedan verla
def ver_registros():
    """
    Muestra una lista de todos los registros de actividad guardados,
    ordenados por fecha más reciente primero.
    """
    # Consultamos todos los registros en la base de datos y los ordenamos
    todos_los_registros = db.session.execute(
        db.select(RegistroActividad).order_by(RegistroActividad.fecha.desc())
    ).scalars().all()

    # Le pasamos los registros a nuestra nueva plantilla HTML
    return render_template('ver_registros.html', registros=todos_los_registros)

# En src/registros.py, al final del archivo
from flask import Response
from fpdf import FPDF

@registros_bp.route('/registros/exportar/<string:formato>')
@login_required
def exportar_registros(formato):
    registros = db.session.execute(db.select(RegistroActividad).order_by(RegistroActividad.fecha.desc())).scalars().all()

    if formato == 'txt':
        # Generar TXT
        txt_output = "Informe de Actividad de Predicación Pública\n"
        txt_output += "="*40 + "\n\n"
        for r in registros:
            txt_output += f"Fecha: {r.fecha.strftime('%d/%m/%Y')}\n"
            txt_output += f"Lugar: {r.lugar}\n"
            txt_output += f"Hora: {r.hora}\n"
            txt_output += f"Participantes: {r.participantes}\n"
            txt_output += f"Resultados: {r.publicaciones_libros} Libros, {r.publicaciones_revistas} Revistas, {r.videos} Videos, {r.revisitas} Revisitas\n"
            txt_output += "-"*40 + "\n"
        
        return Response(
            txt_output,
            mimetype="text/plain",
            headers={"Content-disposition": "attachment; filename=informe_actividad.txt"}
        )

    elif formato == 'pdf':
        # Generar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Informe de Actividad de Predicación Pública', 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 10, 'Fecha', 1)
        pdf.cell(60, 10, 'Lugar', 1)
        pdf.cell(50, 10, 'Participantes', 1)
        pdf.cell(20, 10, 'L/R/V/R', 1)
        pdf.ln()

        pdf.set_font('Arial', '', 10)
        for r in registros:
            pdf.cell(30, 10, r.fecha.strftime('%d/%m/%Y'), 1)
            pdf.cell(60, 10, r.lugar, 1)
            pdf.cell(50, 10, r.participantes, 1)
            resultados = f"{r.publicaciones_libros}/{r.publicaciones_revistas}/{r.videos}/{r.revisitas}"
            pdf.cell(20, 10, resultados, 1)
            pdf.ln()
            
        return Response(
            pdf.output(dest='S').encode('latin-1'),
            mimetype='application/pdf',
            headers={'Content-disposition': 'attachment; filename=informe_actividad.pdf'}
        )
    
    return redirect(url_for('registros.ver_registros'))