"""Registro de auditoría (FR-026). Solo inserta; nunca modifica ni borra."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.auditoria import Auditoria


async def registrar(
    sesion: AsyncSession,
    *,
    usuario_id: uuid.UUID | None,
    accion: str,
    entidad: str,
    entidad_id: uuid.UUID | str | None = None,
    antes: dict[str, Any] | None = None,
    despues: dict[str, Any] | None = None,
) -> None:
    sesion.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
            antes=antes,
            despues=despues,
        )
    )
    await sesion.flush()
