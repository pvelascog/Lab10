"""Rutas de evaluación (contracts/api.md – Evaluación)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.esquemas.evaluaciones import (
    CalificacionEntrada,
    ComentarioEntrada,
    ComentarioSalida,
    DivergenciaSalida,
    EvaluacionSalida,
)
from app.seguridad import UsuarioActual
from app.servicios import evaluaciones as servicio
from app.servicios.evaluaciones import Contexto
from app.servicios.visibilidad import gestiona

router = APIRouter(prefix="/evaluaciones", tags=["evaluación"])
Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


def _salida(ctx: Contexto) -> EvaluacionSalida:
    return EvaluacionSalida.construir(ctx, gestiona=gestiona(ctx.usuario, ctx.iniciativa))


async def _confirmar(sesion: AsyncSession, ctx: Contexto) -> EvaluacionSalida:
    await sesion.commit()
    await sesion.refresh(ctx.evaluacion)
    return _salida(ctx)


@router.get("/{evaluacion_id}")
async def detalle(
    evaluacion_id: uuid.UUID, usuario: UsuarioActual, sesion: Sesion
) -> EvaluacionSalida:
    return _salida(await servicio.contexto(sesion, usuario, evaluacion_id))


@router.put("/{evaluacion_id}/calificaciones/{criterio}")
async def calificar(
    evaluacion_id: uuid.UUID,
    criterio: str,
    datos: CalificacionEntrada,
    usuario: UsuarioActual,
    sesion: Sesion,
) -> EvaluacionSalida:
    ctx = await servicio.contexto(sesion, usuario, evaluacion_id)
    await servicio.calificar(
        sesion,
        ctx,
        criterio,
        nivel=datos.nivel,
        justificacion=datos.justificacion,
        fuente=datos.fuente,
        usa_calculo=datos.usa_calculo,
    )
    return await _confirmar(sesion, ctx)


@router.post("/{evaluacion_id}/dimensiones/{dimension}/enviar")
async def enviar_dimension(
    evaluacion_id: uuid.UUID, dimension: str, usuario: UsuarioActual, sesion: Sesion
) -> EvaluacionSalida:
    ctx = await servicio.contexto(sesion, usuario, evaluacion_id)
    await servicio.enviar_dimension(sesion, ctx, dimension)
    return await _confirmar(sesion, ctx)


@router.get("/{evaluacion_id}/divergencias")
async def divergencias(
    evaluacion_id: uuid.UUID, usuario: UsuarioActual, sesion: Sesion
) -> list[DivergenciaSalida]:
    ctx = await servicio.contexto(sesion, usuario, evaluacion_id)
    return [
        DivergenciaSalida(
            criterio=c.codigo,
            dimension=d.codigo,
            niveles=[p.nivel for p in ctx.publicadas(c)],
            comentada=bool(ctx.comentarios(c)),
        )
        for d in ctx.dimensiones
        if ctx.ve_calificaciones(d.codigo)
        for c in d.criterios
        if ctx.diverge(c)
    ]


@router.post(
    "/{evaluacion_id}/divergencias/{criterio}/comentarios", status_code=status.HTTP_201_CREATED
)
async def comentar(
    evaluacion_id: uuid.UUID,
    criterio: str,
    datos: ComentarioEntrada,
    usuario: UsuarioActual,
    sesion: Sesion,
) -> ComentarioSalida:
    ctx = await servicio.contexto(sesion, usuario, evaluacion_id)
    comentario = await servicio.comentar_divergencia(sesion, ctx, criterio, datos.texto)
    await sesion.commit()
    return ComentarioSalida.desde(comentario)
