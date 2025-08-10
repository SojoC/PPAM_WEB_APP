from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import asyncio
import threading
import time

# Se crea el "plano" de la API
api = Blueprint('api', __name__)

# Se crean las instancias de nuestros servicios
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

@api.route('/api/buscar', methods=['POST'])
def buscar():
    """
    Ruta principal para que el frontend busque contactos.
    """
    try:
        termino = request.get_json().get('termino', '')
        resultados = motor.buscar_contactos(termino)
        return jsonify({"usuarios": resultados})
    except Exception as e:
        print(f"❌ ERROR en /api/buscar: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# --- RUTAS PARA WHATSAPP ---
@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    # ... (esta lógica ya es correcta)
    pass

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    # ... (esta lógica ya es correcta) ...
    pass

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    """
    Ruta para enviar mensajes masivos.
    """
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')

    def tarea_envio():
        print(f"📦 Iniciando envío a {len(usuarios)} usuarios...")
        for usuario in usuarios:
            asyncio.run(ws_service.enviar_mensaje(usuario['telefono'], mensaje))
            time.sleep(5) # Pausa entre mensajes
        print("📦✅ Proceso de envío finalizado.")
    
    thread = threading.Thread(target=tarea_envio)
    thread.start()

    return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})

@api.route('/whatsapp/enviar', methods=['POST'])
def enviar_whatsapp():
    try:
        data = request.get_json()
        telefono = data.get('telefono')
        mensaje = data.get('mensaje')
        if not telefono or not mensaje:
            return jsonify({"status": "error", "error": "Faltan datos"}), 400

        ws = WhatsAppServicio()
        resultado = asyncio.run(ws.enviar_mensaje(telefono, mensaje))
        if resultado:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "error": "No se pudo enviar el mensaje"}), 500
    except Exception as e:
        print(f"❌ Error en endpoint WhatsApp: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500