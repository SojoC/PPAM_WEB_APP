from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from core.models import db, User, AsignacionVisita
from whatsapp_servicio import WhatsAppServicio
import threading

visitas_bp = Blueprint('visitas', __name__)
ws_service = WhatsAppServicio() # Usaremos la misma instancia de WhatsApp

@visitas_bp.route('/visitas/asignar/<int:publicador_id>', methods=['GET', 'POST'])
@login_required
def asignar_visita(publicador_id):
    """
    Muestra el formulario S-43 para asignar una visita a un publicador específico.
    """
    if not current_user.role or current_user.role.name != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('home'))

    publicador = db.session.get(User, publicador_id)
    if not publicador:
        flash('Publicador no encontrado.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Recolectar datos del formulario S-43
        nombre_interesado = request.form.get('nombre_interesado')
        direccion = request.form.get('direccion')
        telefono_interesado = request.form.get('telefono_interesado')
        observaciones = request.form.get('observaciones')

        # Crear la nueva asignación en la base de datos
        nueva_asignacion = AsignacionVisita(
            nombre_interesado=nombre_interesado,
            direccion=direccion,
            telefono_interesado=telefono_interesado,
            observaciones=observaciones,
            publicador_id=publicador.id
        )
        db.session.add(nueva_asignacion)
        db.session.commit()

        # Preparar y enviar el mensaje por WhatsApp
        mensaje = f"""*Nueva Asignación de Visita (S-43)*
----------------------------------
Hola {publicador.nombre_completo.split()[0]},
Se te ha asignado una nueva visita de parte de la congregación.

*Persona Interesada:* {nombre_interesado}
*Dirección:* {direccion}
*Teléfono:* {telefono_interesado}
*Observaciones:* {observaciones}
----------------------------------
_Por favor, responde a este mensaje con la palabra 'Acepto' para confirmar._
"""
        # Usamos un hilo para no bloquear la página mientras se envía el mensaje
        def tarea_envio():
            ws_service.enviar_mensaje(publicador.telefono, mensaje)

        thread = threading.Thread(target=tarea_envio)
        thread.start()

        flash(f'Visita asignada a {publicador.nombre_completo} y notificación enviada por WhatsApp.', 'success')
        return redirect(url_for('home'))

    return render_template('s43_form.html', publicador=publicador)