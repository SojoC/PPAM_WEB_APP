#!/usr/bin/env bash
# exit on error
set -o errexit

# Le decimos a pip dónde está el archivo de requerimientos
pip install -r src/requirements.txt

# Entramos a la carpeta src para que los comandos de flask funcionen
cd src

# Aplicamos las migraciones a la base de datos
flask db upgrade

# Poblamos la base de datos
python migracion.py