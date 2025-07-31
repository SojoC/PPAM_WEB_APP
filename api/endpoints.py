from flask import Blueprint, request, jsonify
from core.motor_busqueda import MotorBusquedaModerno

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