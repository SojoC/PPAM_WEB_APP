from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import asyncio

api = Blueprint('api', __name__)
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

# ... (ruta /api/buscar se mantiene igual)

@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resultado = loop.run_until_complete(ws_service.conectar_whatsapp())
    loop.close()
    return jsonify(resultado)

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logueado = loop.run_until_complete(ws_service.esta_logueado())
    loop.close()
    return jsonify({"status": "logueado" if logueado else "desconectado"})

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')

    async def tarea_envio():
        for usuario in usuarios:
            await ws_service.enviar_mensaje(usuario['telefono'], mensaje)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tarea_envio())
    loop.close()
    return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})