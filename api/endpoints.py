from flask import Blueprint, request, jsonify, send_file
from core.motor_busqueda import MotorBusquedaModerno
from whatsapp_servicio import WhatsAppServicio
import asyncio
import threading
import time
import os
import zipfile
from werkzeug.utils import secure_filename
import shutil
import stat

# Se crea el "plano" (blueprint) para todas las rutas de la API
api = Blueprint('api', __name__)

# Se crean las instancias del motor de búsqueda y del servicio de WhatsApp
# Estas son las versiones que usará toda la aplicación.
motor = MotorBusquedaModerno()
ws_service = WhatsAppServicio()

PERFIL_DIR = os.path.abspath("playwright_whatsapp_profile")
PERFIL_ZIP = os.path.abspath("playwright_whatsapp_profile.zip")

@api.route('/api/buscar', methods=['POST'])
def buscar():
    """
    Esta es la ruta que el frontend llama para buscar contactos.
    Cuando el término de búsqueda está vacío, carga toda la tabla.
    """
    try:
        termino = request.get_json().get('termino', '')
        resultados = motor.buscar_contactos(termino)
        return jsonify({"usuarios": resultados})
    except Exception as e:
        print(f"❌ ERROR en /api/buscar: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# --- RUTAS PARA WHATSAPP (CORREGIDAS PARA PLAYWRIGHT/ASYNCIO) ---

@api.route('/api/whatsapp/conectar', methods=['POST'])
def whatsapp_conectar():
    """Maneja la conexión inicial con WhatsApp Web."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(ws_service.conectar_whatsapp())
        loop.close()
        return jsonify(resultado)
    except Exception as e:
        print(f"❌ Error en /api/whatsapp/conectar: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/estado', methods=['GET'])
def whatsapp_estado():
    """Verifica si la sesión de WhatsApp está activa."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logueado = loop.run_until_complete(ws_service.esta_logueado())
        loop.close()
        return jsonify({"status": "logueado" if logueado else "desconectado"})
    except Exception as e:
        print(f"❌ Error en /api/whatsapp/estado: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@api.route('/api/whatsapp/enviar', methods=['POST'])
def whatsapp_enviar():
    """
    Recibe la lista de usuarios y el mensaje, y los envía en segundo plano
    para no bloquear la aplicación.
    """
    data = request.get_json()
    usuarios = data.get('usuarios', [])
    mensaje = data.get('mensaje', '')


    import datetime
    def tarea_de_envio_en_hilo():
        from whatsapp_servicio import WhatsAppServicio
        ws_service_local = WhatsAppServicio()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for usuario in usuarios:
            inicio = datetime.datetime.now()
            print(f"[METRICA] Intentando enviar a {usuario['telefono']} a las {inicio}")
            try:
                resultado = loop.run_until_complete(ws_service_local.enviar_mensaje(usuario['telefono'], mensaje))
                fin = datetime.datetime.now()
                print(f"[METRICA] Resultado: {resultado} para {usuario['telefono']} en {fin-inicio}")
            except Exception as e:
                print(f"[METRICA] ERROR enviando a {usuario['telefono']}: {e}")
        loop.close()

    # Inicia el hilo que hará el trabajo pesado.
    thread = threading.Thread(target=tarea_de_envio_en_hilo)
    thread.start()

    # Devuelve una respuesta inmediata al usuario.
    return jsonify({"status": "iniciado", "mensaje": f"Proceso de envío iniciado para {len(usuarios)} usuarios."})

@api.route('/api/whatsapp/cerrar', methods=['POST'])
def whatsapp_cerrar():
    """Cierra la sesión de Playwright."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ws_service.cerrar())
        loop.close()
        return jsonify({"status": "cerrado", "mensaje": "Sesión de WhatsApp cerrada."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

def on_rm_error(func, path, exc_info):
    # Cambia permisos y reintenta borrar
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

@api.route('/api/whatsapp/subir_perfil', methods=['POST'])
def subir_perfil():
    if 'perfil' not in request.files:
        return jsonify({"status": "error", "mensaje": "No se envió ningún archivo."}), 400
    archivo = request.files['perfil']
    filename = secure_filename(archivo.filename)
    ruta_zip = os.path.join(os.path.dirname(PERFIL_DIR), filename)
    archivo.save(ruta_zip)
    try:
        # Cierra Playwright antes de manipular el perfil
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_service.cerrar())
            loop.close()
        except Exception as e:
            print(f"Advertencia: No se pudo cerrar Playwright antes de reemplazar el perfil: {e}")
        # Elimina el perfil anterior de forma robusta
        if os.path.exists(PERFIL_DIR):
            shutil.rmtree(PERFIL_DIR, onerror=on_rm_error)
        # Extrae el nuevo perfil
        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            zip_ref.extractall(PERFIL_DIR)
        os.remove(ruta_zip)
        return jsonify({"status": "ok", "mensaje": "Perfil subido y extraído correctamente. Por favor, vuelve a conectar WhatsApp Web."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error al extraer el perfil: {e}"}), 500

@api.route('/api/whatsapp/descargar_perfil', methods=['GET'])
def descargar_perfil():
    if not os.path.exists(PERFIL_DIR):
        return jsonify({"status": "error", "mensaje": "No existe perfil para descargar."}), 404
    try:
        with zipfile.ZipFile(PERFIL_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(PERFIL_DIR):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, PERFIL_DIR)
                    zipf.write(abs_path, rel_path)
        response = send_file(PERFIL_ZIP, as_attachment=True, download_name="playwright_whatsapp_profile.zip")
        # Limpia el ZIP temporal después de enviar
        @response.call_on_close
        def cleanup():
            if os.path.exists(PERFIL_ZIP):
                os.remove(PERFIL_ZIP)
        return response
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error al comprimir el perfil: {e}"}), 500

import os

@api.route('/api/whatsapp/verificar_perfil', methods=['GET'])
def verificar_perfil():
    perfil_dir = os.path.abspath("playwright_whatsapp_profile")
    if not os.path.exists(perfil_dir):
        return jsonify({"status": "error", "mensaje": "No existe la carpeta de perfil."}), 404
    archivos = []
    for root, dirs, files in os.walk(perfil_dir):
        for file in files:
            archivos.append(os.path.relpath(os.path.join(root, file), perfil_dir))
    return jsonify({
        "status": "ok",
        "mensaje": f"Perfil encontrado con {len(archivos)} archivos.",
        "archivos": archivos[:20]  # Muestra solo los primeros 20 para no saturar la respuesta
    })