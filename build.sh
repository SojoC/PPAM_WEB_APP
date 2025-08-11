#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala las librerías (el archivo está en la raíz)
pip install -r requirements.txt

# Aplica las actualizaciones a la base de datos
flask db upgrade

# Ejecuta el script para poblar la base de datos
python migracion.py