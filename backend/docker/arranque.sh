#!/bin/sh
# Arranque del servicio api: aplica migraciones, carga los datos base y levanta el servidor.
set -e
alembic upgrade head
python -m app.semillas.base
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
