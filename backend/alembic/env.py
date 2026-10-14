"""Entorno de Alembic: usa DATABASE_URL de la configuración de la aplicación."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

import app.modelos  # noqa: F401  # registra todas las tablas
from app.config import obtener_configuracion
from app.db import Base

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)

metadatos = Base.metadata


def _ejecutar(conexion: Connection) -> None:
    context.configure(connection=conexion, target_metadata=metadatos, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _ejecutar_en_linea() -> None:
    motor = create_async_engine(obtener_configuracion().database_url, poolclass=NullPool)
    async with motor.connect() as conexion:
        await conexion.run_sync(_ejecutar)
    await motor.dispose()


if context.is_offline_mode():
    context.configure(
        url=obtener_configuracion().database_url, target_metadata=metadatos, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_ejecutar_en_linea())
