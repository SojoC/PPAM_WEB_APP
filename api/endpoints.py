from flask import Blueprint, request, jsonify
from whatsapp_servicio import WhatsAppServicio
import asyncio  # <-- SOLUCIÓN: Importa asyncio

api = Blueprint('api', __name__)
ws_service = WhatsAppServicio()

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    data = request.get_json()
    telefono = data.get('telefono')
    mensaje = data.get('mensaje')

    if not telefono or not mensaje:
        return jsonify({"status": "error", "mensaje": "Faltan datos"}), 400

    try:
        # Ejecuta el envío de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(ws_service.enviar_mensaje(telefono, mensaje))
        loop.close()
        if resultado:
            return jsonify({"status": "ok", "mensaje": "Mensaje enviado"})
        else:
            return jsonify({"status": "error", "mensaje": "No se pudo enviar el mensaje. Verifica sesión activa y perfil."}), 500
    except Exception as e:
        print(f"❌ Error en endpoint whatsapp_enviar: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500