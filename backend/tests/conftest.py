"""Configuración común de pruebas.

Las pruebas de integración usan una base PostgreSQL real (DATABASE_URL_PRUEBAS).
El esquema se crea una vez por sesión con las migraciones de Alembic y los datos
se vacían y se vuelven a sembrar antes de cada prueba.
"""

import os

os.environ.setdefault(
    "DATABASE_URL_PRUEBAS",
    "postgresql+asyncpg://validador:validador@localhost:5432/validador_pruebas",
)
os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_PRUEBAS"]
os.environ["ENTORNO"] = "pruebas"
os.environ.setdefault("JWT_SECRETO", "secreto-de-pruebas-con-longitud-suficiente-0123456789")
