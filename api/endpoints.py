from flask import Blueprint, request, jsonify
from core.motor_busqueda import motor
from whatsapp_servicio import WhatsAppServicio
import asyncio
import threading
import time

# Se crea el "plano" de la API
api = Blueprint('api', __name__)

# Se crean las instancias de nuestros servicios, incluyendo el motor

ws_service = WhatsAppServicio()

@api.route('/api/buscar', methods=['POST'])
def buscar():
    """
    Ruta para buscar contactos. Responde a la petición inicial para cargar la tabla.
    """
    termino = request.get_json().get('termino', '')
    resultados = motor.buscar_contactos(termino)
    return jsonify({"usuarios": resultados})

# --- RUTAS PARA WHATSAPP (CORREGIDAS Y ROBUSTAS) ---
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
            time.sleep(5)
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