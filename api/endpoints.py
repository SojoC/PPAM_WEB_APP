from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import asyncio
import threading
import time

api = Blueprint('api', __name__)
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

# ... (la ruta /api/buscar se mantiene igual)

# --- RUTAS PARA WHATSAPP (CORREGIDAS PARA ASYNCIO) ---
@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    try:
        resultado = asyncio.run(ws_service.conectar_whatsapp())
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    try:
        logueado = asyncio.run(ws_service.esta_logueado())
        return jsonify({"status": "logueado" if logueado else "desconectado"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')

    def tarea_envio():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for usuario in usuarios:
            loop.run_until_complete(ws_service.enviar_mensaje(usuario['telefono'], mensaje))
            time.sleep(5) # Pausa entre mensajes
        loop.close()
    
    thread = threading.Thread(target=tarea_envio)
    thread.start()
    return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})

@api.route('/api/whatsapp/cerrar', methods=['POST'])
def whatsapp_cerrar():
    try:
        asyncio.run(ws_service.cerrar())
        return jsonify({"status": "cerrado", "mensaje": "Sesión de WhatsApp cerrada."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500