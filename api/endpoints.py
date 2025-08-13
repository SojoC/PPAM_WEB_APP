from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import threading

api = Blueprint('api', __name__)
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

# ... (ruta /api/buscar se mantiene igual)

@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    resultado = ws_service.conectar_whatsapp()
    return jsonify(resultado)

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    logueado = ws_service.esta_logueado()
    return jsonify({"status": "logueado" if logueado else "desconectado"})

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')

    def tarea_envio():
        for usuario in usuarios:
            ws_service.enviar_mensaje(usuario['telefono'], mensaje)
    
    thread = threading.Thread(target=tarea_envio)
    thread.start()
    return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})