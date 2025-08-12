#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- PASO 1: Instalando dependencias de Python ---"
pip install -r requirements.txt

echo "--- PASO 2: Instalando navegadores para Playwright ---"
playwright install

echo "--- PASO 3: Definiendo la aplicación para los comandos de Flask ---"
export FLASK_APP=app:create_app

echo "--- PASO 4: Creando/Actualizando las tablas de la base de datos ---"
flask db upgrade

echo "--- PASO 5: Poblando la base de datos con los datos iniciales ---"
python migracion.py

echo "--- ¡Build completado exitosamente! ---"

