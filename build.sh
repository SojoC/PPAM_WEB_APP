#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala las librerías desde el archivo en la raíz actual (que es 'src')
pip install -r requirements.txt

# Aplica las actualizaciones a la base de datos (crea las tablas)
flask db upgrade

# Ejecuta nuestro script para poblar la base de datos con los contactos
python migracion.py