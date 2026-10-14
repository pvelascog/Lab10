"""Consulta del marco de evaluación (contracts/api.md – Marco)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.errores import NoEncontrado
from app.esquemas.marco import VersionMarcoSalida
from app.modelos.marco import EstadoVersion, VersionMarco
from app.seguridad import UsuarioActual

router = APIRouter(prefix="/marco", tags=["marco"])


@router.get("/vigente")
async def vigente(
    _: UsuarioActual, sesion: Annotated[AsyncSession, Depends(obtener_sesion)]
) -> VersionMarcoSalida:
    version = await sesion.scalar(
        select(VersionMarco).where(VersionMarco.estado == EstadoVersion.VIGENTE)
    )
    if version is None:
        raise NoEncontrado("No hay una versión vigente del marco")
    return VersionMarcoSalida.desde(version)
