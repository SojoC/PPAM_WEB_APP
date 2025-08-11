#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- PASO 1: Instalando dependencias de Python ---"
pip install -r requirements.txt

echo "--- PASO 2: Definiendo la aplicación para los comandos de Flask ---"
export FLASK_APP=app:create_app

echo "--- PASO 3: Creando/Actualizando las tablas de la base de datos ---"
flask db upgrade

# Puebla la base de datos con nuestro nuevo comando
flask seed

echo "--- PASO 4: Poblando la base de datos con los 502 contactos ---"
python migracion.py

echo "--- MISIÓN CUMPLIDA: El build se ha completado exitosamente ---"







