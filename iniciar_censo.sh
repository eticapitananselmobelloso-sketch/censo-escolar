#!/bin/bash
# Activa el entorno y corre el proceso de censo
source venv/bin/activate
python procesar_censo.py
echo "Proceso finalizado. Presiona Enter para salir."
read
