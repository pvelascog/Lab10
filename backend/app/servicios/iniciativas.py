"""Registro y consulta de iniciativas (HU1)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy import exists, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.dominio.motor_decision import Resultado
from app.errores import DatosInvalidos, NoEncontrado
from app.modelos.evaluaciones import Evaluacion, ResultadoConsolidado
from app.modelos.iniciativas import (
    AsignacionEvaluador,
    EstadoIniciativa,
    Iniciativa,
    OrigenIniciativa,
)
from app.modelos.marco import Dimension, EstadoVersion, VersionMarco
from app.modelos.usuarios import Usuario
from app.servicios import auditoria
from app.servicios.visibilidad import condicion_visible, es_visible

# Similitud trigram a partir de la cual se advierte un posible duplicado (data-model.md).
UMBRAL_DUPLICADO = 0.6

Orden = Literal["-creado_en", "creado_en", "nombre", "-nombre"]


@dataclass(frozen=True)
class AsignacionPedida:
    dimension: str
    usuario_id: uuid.UUID


async def validar_asignaciones(
    sesion: AsyncSession, pedidas: list[AsignacionPedida]
) -> list[AsignacionPedida]:
    """Verifica dimensiones del marco vigente y usuarios activos; elimina repetidas."""
    unicas = list(dict.fromkeys(pedidas))
    if not unicas:
        return []
    dimensiones = set(
        (
            await sesion.execute(
                select(Dimension.codigo)
                .join(VersionMarco)
                .where(VersionMarco.estado == EstadoVersion.VIGENTE)
            )
        ).scalars()
    )
    invalidas = sorted({a.dimension for a in unicas} - dimensiones)
    if invalidas:
        raise DatosInvalidos(
            {"asignaciones": f"Dimensión inexistente en el marco vigente: {', '.join(invalidas)}"}
        )
    ids = {a.usuario_id for a in unicas}
    activos = set(
        (
            await sesion.execute(select(Usuario.id).where(Usuario.id.in_(ids), Usuario.activo))
        ).scalars()
    )
    if ids - activos:
        raise DatosInvalidos({"asignaciones": "Algún usuario asignado no existe o está inactivo"})
    return unicas


async def _buscar_duplicado(
    sesion: AsyncSession, nombre: str, descripcion: str
) -> tuple[uuid.UUID, Decimal] | None:
    similitud = func.greatest(
        func.similarity(Iniciativa.nombre, nombre),
        func.similarity(Iniciativa.descripcion, descripcion),
    ).label("similitud")
    fila = (
        await sesion.execute(
            select(Iniciativa.id, similitud)
            .where(similitud >= UMBRAL_DUPLICADO)
            .order_by(similitud.desc())
            .limit(1)
        )
    ).first()
    if fila is None:
        return None
    return fila.id, Decimal(str(round(float(fila.similitud), 3)))


async def registrar(
    sesion: AsyncSession,
    autor: Usuario,
    *,
    nombre: str,
    descripcion: str,
    origen: OrigenIniciativa,
    asignaciones: list[AsignacionPedida],
) -> Iniciativa:
    nombre, descripcion = nombre.strip(), descripcion.strip()
    validas = await validar_asignaciones(sesion, asignaciones)
    duplicado = await _buscar_duplicado(sesion, nombre, descripcion)

    numero = int(
        await sesion.scalar(text("SELECT nextval(pg_get_serial_sequence('iniciativa', 'numero'))"))
    )
    iniciativa = Iniciativa(
        numero=numero,
        codigo=f"INI-{datetime.now(UTC).year}-{numero:04d}",
        nombre=nombre,
        descripcion=descripcion,
        origen=origen,
        estado=EstadoIniciativa.IDENTIFICADA,
        autor_id=autor.id,
        supuestos_clave=[],
        posible_duplicado_de_id=duplicado[0] if duplicado else None,
        similitud_duplicado=duplicado[1] if duplicado else None,
        asignaciones=[
            AsignacionEvaluador(dimension_codigo=a.dimension, usuario_id=a.usuario_id)
            for a in validas
        ],
    )
    sesion.add(iniciativa)
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=autor.id,
        accion="CREAR_INICIATIVA",
        entidad="iniciativa",
        entidad_id=iniciativa.id,
        despues={
            "codigo": iniciativa.codigo,
            "nombre": iniciativa.nombre,
            "origen": iniciativa.origen.value,
            "asignaciones": [[a.dimension, str(a.usuario_id)] for a in validas],
        },
    )
    return iniciativa


async def obtener_visible(
    sesion: AsyncSession, usuario: Usuario, iniciativa_id: uuid.UUID
) -> Iniciativa:
    """La iniciativa si el usuario puede verla; si no, 404 sin revelar su existencia."""
    iniciativa = await sesion.get(Iniciativa, iniciativa_id)
    if iniciativa is None or not es_visible(usuario, iniciativa):
        raise NoEncontrado("Iniciativa no encontrada")
    return iniciativa


async def listar(
    sesion: AsyncSession,
    usuario: Usuario,
    *,
    estado: EstadoIniciativa | None = None,
    origen: OrigenIniciativa | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    resultado: Resultado | None = None,
    orden: Orden = "-creado_en",
) -> list[Iniciativa]:
    consulta = select(Iniciativa).where(condicion_visible(usuario))
    if resultado is not None:
        # Resultado de la evaluación más reciente de cada iniciativa.
        otra = aliased(Evaluacion)
        ultima = (
            select(func.max(otra.numero)).where(otra.iniciativa_id == Iniciativa.id)
        ).scalar_subquery()
        consulta = consulta.where(
            exists().where(
                Evaluacion.iniciativa_id == Iniciativa.id,
                Evaluacion.numero == ultima,
                ResultadoConsolidado.evaluacion_id == Evaluacion.id,
                ResultadoConsolidado.resultado == resultado,
            )
        )
    if estado is not None:
        consulta = consulta.where(Iniciativa.estado == estado)
    if origen is not None:
        consulta = consulta.where(Iniciativa.origen == origen)
    if desde is not None:
        consulta = consulta.where(Iniciativa.creado_en >= datetime.combine(desde, time(), UTC))
    if hasta is not None:
        fin = datetime.combine(hasta + timedelta(days=1), time(), UTC)
        consulta = consulta.where(Iniciativa.creado_en < fin)

    columna = Iniciativa.nombre if orden.lstrip("-") == "nombre" else Iniciativa.numero
    consulta = consulta.order_by(columna.desc() if orden.startswith("-") else columna.asc())
    return list((await sesion.execute(consulta)).scalars())


async def recargar(sesion: AsyncSession, iniciativa: Iniciativa) -> Iniciativa:
    """Vuelve a leer la iniciativa con todas sus relaciones tras confirmar cambios.

    `refresh` no recarga las relaciones anidadas de objetos ya presentes en la sesión (p. ej. el
    resultado de una evaluación), y en modo asíncrono no se permiten cargas perezosas.
    """
    recargada = await sesion.scalar(
        select(Iniciativa)
        .where(Iniciativa.id == iniciativa.id)
        .options(
            selectinload(Iniciativa.evaluaciones).selectinload(Evaluacion.resultado),
            selectinload(Iniciativa.asignaciones).selectinload(AsignacionEvaluador.usuario),
        )
        .execution_options(populate_existing=True)
    )
    if recargada is None:
        raise NoEncontrado("Iniciativa no encontrada")
    return recargada
