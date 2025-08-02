from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno
from core.models import db

api = Blueprint('api', __name__)
motor = MotorBusquedaModerno()

@api.route('/api/buscar', methods=['POST'])
def buscar():
    try:
        data = request.get_json()
        termino = data.get('termino', '')
        
        resultados = motor.buscar_contactos(termino)
        
        return jsonify({
            "usuarios": resultados,
            "total": len(resultados)
        })

    except Exception as e:
        print(f"❌ ERROR en el endpoint /api/buscar: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor."}), 500
    
    # En src/api/endpoints.py

from core.models import User # Asegúrate de importar User

@api.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint simple para verificar el estado y la cantidad de datos.
    """
    try:
        total_usuarios = db.session.query(User).count()
        return jsonify({
            "status": "ok",
            "total_usuarios_en_db": total_usuarios
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500