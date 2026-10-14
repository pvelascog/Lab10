"""Conexión a PostgreSQL y clases base de los modelos."""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

from app.config import obtener_configuracion

# Nombres de restricciones estables para que las migraciones sean reproducibles.
CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


class ConId:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class ConFechas:
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


@lru_cache
def fabrica_sesiones() -> async_sessionmaker[AsyncSession]:
    configuracion = obtener_configuracion()
    # En pruebas cada caso usa su propio bucle de eventos: sin pool para no compartir conexiones.
    opciones = {"poolclass": NullPool} if configuracion.entorno == "pruebas" else {}
    motor = create_async_engine(configuracion.database_url, **opciones)
    return async_sessionmaker(motor, expire_on_commit=False)


async def obtener_sesion() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por petición."""
    async with fabrica_sesiones()() as sesion:
        yield sesion
