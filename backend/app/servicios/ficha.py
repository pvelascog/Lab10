"""Edición de la ficha y de los evaluadores de una iniciativa (HU2)."""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import DatosInvalidos, SinPermiso
from app.modelos.iniciativas import AsignacionEvaluador, Iniciativa
from app.modelos.usuarios import CodigoRol, Rol, Usuario
from app.servicios import auditoria
from app.servicios.ciclo_vida import exigir_editable, gestiona
from app.servicios.iniciativas import AsignacionPedida, validar_asignaciones

CAMPOS_TEXTO = (
    "nombre",
    "descripcion",
    "problema",
    "solucion_objetivo",
    "segmento",
    "propuesta_valor",
    "datos_disponibles",
)


def _serializable(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, uuid.UUID):
        return str(valor)
    if hasattr(valor, "value"):  # enumeraciones
        return valor.value
    return valor


async def editar_ficha(
    sesion: AsyncSession, usuario: Usuario, iniciativa: Iniciativa, cambios: dict[str, Any]
) -> Iniciativa:
    """Aplica solo los campos enviados. El autor edita la ficha; el PM además asigna el PM."""
    es_pm = gestiona(usuario, iniciativa)
    if not es_pm and usuario.id != iniciativa.autor_id:
        raise SinPermiso("Solo el autor o el Product Manager pueden editar la ficha")
    if "pm_id" in cambios and not es_pm:
        raise SinPermiso("Solo un Product Manager puede asignar el PM de la iniciativa")
    exigir_editable(iniciativa)

    if cambios.get("pm_id") is not None:
        pm = await sesion.scalar(
            select(Usuario).where(
                Usuario.id == cambios["pm_id"],
                Usuario.activo,
                Usuario.roles.any(Rol.codigo == CodigoRol.PM),
            )
        )
        if pm is None:
            raise DatosInvalidos({"pm_id": "Debe ser un usuario activo con rol Product Manager"})

    for campo in CAMPOS_TEXTO:
        if isinstance(cambios.get(campo), str):
            cambios[campo] = cambios[campo].strip() or None
    if "supuestos_clave" in cambios:
        cambios["supuestos_clave"] = [
            s.strip() for s in cambios["supuestos_clave"] or [] if s.strip()
        ]

    antes: dict[str, Any] = {}
    despues: dict[str, Any] = {}
    for campo, valor in cambios.items():
        anterior = getattr(iniciativa, campo)
        if anterior != valor:
            antes[campo], despues[campo] = _serializable(anterior), _serializable(valor)
            setattr(iniciativa, campo, valor)
    if despues:
        await sesion.flush()
        await auditoria.registrar(
            sesion,
            usuario_id=usuario.id,
            accion="EDITAR_INICIATIVA",
            entidad="iniciativa",
            entidad_id=iniciativa.id,
            antes=antes,
            despues=despues,
        )
    return iniciativa


async def reemplazar_asignaciones(
    sesion: AsyncSession,
    usuario: Usuario,
    iniciativa: Iniciativa,
    pedidas: list[AsignacionPedida],
) -> Iniciativa:
    if not gestiona(usuario, iniciativa):
        raise SinPermiso("Solo el Product Manager puede asignar evaluadores")
    exigir_editable(iniciativa)
    nuevas = await validar_asignaciones(sesion, pedidas)

    actuales = {(a.dimension_codigo, a.usuario_id): a for a in iniciativa.asignaciones}
    deseadas = {(a.dimension, a.usuario_id) for a in nuevas}
    # Se conservan las que no cambian para no violar la restricción única al reinsertarlas.
    iniciativa.asignaciones = [a for clave, a in actuales.items() if clave in deseadas] + [
        AsignacionEvaluador(dimension_codigo=d, usuario_id=u)
        for d, u in sorted(deseadas - actuales.keys(), key=str)
    ]
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=usuario.id,
        accion="EDITAR_ASIGNACIONES",
        entidad="iniciativa",
        entidad_id=iniciativa.id,
        antes={"asignaciones": sorted([d, str(u)] for d, u in actuales)},
        despues={"asignaciones": sorted([d, str(u)] for d, u in deseadas)},
    )
    return iniciativa
