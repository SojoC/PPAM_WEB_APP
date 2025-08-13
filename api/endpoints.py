from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import asyncio

api = Blueprint('api', __name__)
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

# Utiliza un event loop global para evitar conflictos en Render
loop = asyncio.get_event_loop_policy().get_event_loop()

@api.route('/buscar', methods=['POST'])
def buscar():
    data = request.get_json()
    termino = data.get('termino', '')  # <-- tu JS envía 'termino'
    if not termino:
        return jsonify({"usuarios": []})
    try:
        resultados = motor.buscar_contactos(termino)
        return jsonify({"usuarios": resultados})
    except Exception as e:
        return jsonify({"resultados": [], "error": str(e)}), 500

@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    try:
        resultado = loop.run_until_complete(ws_service.conectar_whatsapp())
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    try:
        logueado = loop.run_until_complete(ws_service.esta_logueado())
        return jsonify({"status": "logueado" if logueado else "desconectado"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')

    async def tarea_envio():
        for usuario in usuarios:
            await ws_service.enviar_mensaje(usuario['telefono'], mensaje)

    try:
        loop.run_until_complete(tarea_envio())
        return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500