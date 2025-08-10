#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r src/requirements.txt

# Entramos a la carpeta src para que los comandos de flask funcionen
cd src
flask db upgrade