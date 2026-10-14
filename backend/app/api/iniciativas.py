"""Rutas de iniciativas (contracts/api.md – Iniciativas)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.dominio.calculos_financieros import proponer
from app.dominio.motor_decision import Resultado
from app.esquemas.iniciativas import (
    AsignacionesEntrada,
    CalculosFinancierosSalida,
    IniciativaCrear,
    IniciativaDetalle,
    IniciativaEditar,
    IniciativaResumen,
    TransicionEntrada,
)
from app.modelos.iniciativas import EstadoIniciativa, Iniciativa, OrigenIniciativa
from app.modelos.usuarios import Usuario
from app.seguridad import UsuarioActual
from app.servicios import ciclo_vida, ficha
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
    resultado: Resultado | None = None,
    orden: servicio.Orden = "-creado_en",
) -> list[IniciativaResumen]:
    iniciativas = await servicio.listar(
        sesion,
        usuario,
        estado=estado,
        origen=origen,
        desde=desde,
        hasta=hasta,
        resultado=resultado,
        orden=orden,
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
    return _detalle(usuario, await servicio.recargar(sesion, iniciativa))


@router.get("/{iniciativa_id}")
async def detalle(
    iniciativa_id: uuid.UUID, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    return _detalle(usuario, await servicio.obtener_visible(sesion, usuario, iniciativa_id))


async def _guardar(sesion: AsyncSession, usuario: Usuario, i: Iniciativa) -> IniciativaDetalle:
    await sesion.commit()
    return _detalle(usuario, await servicio.recargar(sesion, i))


@router.patch("/{iniciativa_id}")
async def editar(
    iniciativa_id: uuid.UUID, datos: IniciativaEditar, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    iniciativa = await servicio.obtener_visible(sesion, usuario, iniciativa_id)
    await ficha.editar_ficha(sesion, usuario, iniciativa, datos.cambios())
    return await _guardar(sesion, usuario, iniciativa)


@router.put("/{iniciativa_id}/asignaciones")
async def reemplazar_asignaciones(
    iniciativa_id: uuid.UUID, datos: AsignacionesEntrada, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    iniciativa = await servicio.obtener_visible(sesion, usuario, iniciativa_id)
    pedidas = [
        servicio.AsignacionPedida(a.dimension.upper(), a.usuario_id) for a in datos.asignaciones
    ]
    await ficha.reemplazar_asignaciones(sesion, usuario, iniciativa, pedidas)
    return await _guardar(sesion, usuario, iniciativa)


@router.post("/{iniciativa_id}/transiciones")
async def transicion(
    iniciativa_id: uuid.UUID, datos: TransicionEntrada, usuario: UsuarioActual, sesion: Sesion
) -> IniciativaDetalle:
    iniciativa = await servicio.obtener_visible(sesion, usuario, iniciativa_id)
    await ciclo_vida.cambiar_estado(sesion, usuario, iniciativa, datos.hacia)
    return await _guardar(sesion, usuario, iniciativa)


@router.get("/{iniciativa_id}/calculos-financieros")
async def calculos_financieros(
    iniciativa_id: uuid.UUID, usuario: UsuarioActual, sesion: Sesion
) -> CalculosFinancierosSalida:
    i = await servicio.obtener_visible(sesion, usuario, iniciativa_id)
    p = proponer(
        inversion=i.inversion_estimada,
        ingresos=i.ingresos_esperados,
        flujo_mensual=i.flujo_mensual_neto,
    )
    return CalculosFinancierosSalida(
        roi=None if p.roi is None else round(float(p.roi), 2),
        nivel_roi=p.nivel_roi,
        meses_recuperacion=None
        if p.meses_recuperacion is None
        else round(float(p.meses_recuperacion), 2),
        nivel_recuperacion=p.nivel_recuperacion,
        faltantes=p.faltantes,
    )
