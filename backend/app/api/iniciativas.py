"""Rutas de iniciativas (contracts/api.md – Iniciativas)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.esquemas.iniciativas import IniciativaCrear, IniciativaDetalle, IniciativaResumen
from app.modelos.iniciativas import EstadoIniciativa, Iniciativa, OrigenIniciativa
from app.modelos.usuarios import Usuario
from app.seguridad import UsuarioActual
from app.servicios import iniciativas as servicio
from app.servicios.visibilidad import es_visible

router = APIRouter(prefix="/iniciativas", tags=["iniciativas"])
Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


def _detalle(usuario: Usuario, iniciativa: Iniciativa) -> IniciativaDetalle:
    duplicado = iniciativa.posible_duplicado_de
    return IniciativaDetalle.construir(
        iniciativa, duplicado_visible=duplicado is not None and es_visible(usuario, duplicado)
    )


@router.get("")
async def listar(
    usuario: UsuarioActual,
    sesion: Sesion,
    estado: EstadoIniciativa | None = None,
    origen: OrigenIniciativa | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    orden: servicio.Orden = "-creado_en",
) -> list[IniciativaResumen]:
    iniciativas = await servicio.listar(
        sesion, usuario, estado=estado, origen=origen, desde=desde, hasta=hasta, orden=orden
    )
    return [IniciativaResumen.desde(i) for i in iniciativas]


@router.post("", status_code=status.HTTP_201_CREATED)
async def registrar(
    datos: IniciativaCrear, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    iniciativa = await servicio.registrar(
        sesion,
        usuario,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        origen=datos.origen,
        asignaciones=[
            servicio.AsignacionPedida(a.dimension.upper(), a.usuario_id) for a in datos.asignaciones
        ],
    )
    await sesion.commit()
    await sesion.refresh(iniciativa)
    return _detalle(usuario, iniciativa)


@router.get("/{iniciativa_id}")
async def detalle(
    iniciativa_id: uuid.UUID, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    return _detalle(usuario, await servicio.obtener_visible(sesion, usuario, iniciativa_id))
