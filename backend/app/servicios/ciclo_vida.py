"""Ciclo de vida de la iniciativa (data-model.md – Máquina de estados).

Cada transición permitida declara sus condiciones y, si corresponde, su efecto. Las transiciones de
etapas posteriores se agregan a la tabla a medida que se implementan sus historias (tasks.md).
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import Conflicto, ReglaIncumplida, SinPermiso
from app.modelos.iniciativas import EstadoIniciativa as E
from app.modelos.iniciativas import Iniciativa
from app.modelos.usuarios import Usuario
from app.servicios import auditoria, consolidacion, evaluaciones
from app.servicios.visibilidad import gestiona

__all__ = ["cambiar_estado", "exigir_editable", "faltantes_ficha", "gestiona"]

OBLIGATORIO = "Obligatorio para estructurar la iniciativa"
ESTADOS_EDITABLES = (E.IDENTIFICADA, E.ESTRUCTURADA)
NOMBRES = {
    E.IDENTIFICADA: "Identificada",
    E.ESTRUCTURADA: "Estructurada",
    E.EN_EVALUACION: "En evaluación",
    E.CONSOLIDADA: "Consolidada",
    E.EN_COMITE: "En comité",
    E.DECIDIDA: "Decidida",
    E.EN_SEGUIMIENTO: "En seguimiento",
    E.ARCHIVADA: "Archivada",
}


def faltantes_ficha(i: Iniciativa) -> dict[str, str]:
    """Campos de la ficha que faltan para pasar a ESTRUCTURADA (HU2, escenario 2)."""
    faltan: dict[str, str] = {}
    if i.pm_id is None:
        faltan["pm_id"] = "Asigne un Product Manager"
    for campo in ("problema", "solucion_objetivo", "segmento", "propuesta_valor"):
        if not (getattr(i, campo) or "").strip():
            faltan[campo] = OBLIGATORIO
    if not i.supuestos_clave:
        faltan["supuestos_clave"] = "Registre al menos un supuesto clave"
    return faltan


async def _ficha_completa(_: AsyncSession, i: Iniciativa) -> dict[str, str]:
    return faltantes_ficha(i)


async def _lista_para_evaluar(sesion: AsyncSession, i: Iniciativa) -> dict[str, str]:
    """Ficha completa y al menos un evaluador por dimensión del marco vigente (FR-010)."""
    faltan = faltantes_ficha(i)
    marco = await evaluaciones.marco_vigente(sesion)
    con_evaluador = {a.dimension_codigo for a in i.asignaciones}
    for d in marco.dimensiones:
        if d.codigo not in con_evaluador:
            faltan[d.codigo] = f"Asigne al menos un evaluador para {d.nombre}"
    return faltan


async def _iniciar_evaluacion(sesion: AsyncSession, _: Usuario, i: Iniciativa) -> None:
    await evaluaciones.crear(sesion, i)


async def _sin_pendientes(_: AsyncSession, i: Iniciativa) -> dict[str, str]:
    return consolidacion.pendientes(i)


async def _consolidar(sesion: AsyncSession, usuario: Usuario, i: Iniciativa) -> None:
    await consolidacion.consolidar(sesion, usuario, i)


@dataclass(frozen=True)
class Transicion:
    condiciones: Callable[[AsyncSession, Iniciativa], Awaitable[dict[str, str]]]
    efecto: Callable[[AsyncSession, Usuario, Iniciativa], Awaitable[None]] | None = None


TRANSICIONES: dict[tuple[E, E], Transicion] = {
    (E.IDENTIFICADA, E.ESTRUCTURADA): Transicion(_ficha_completa),
    (E.ESTRUCTURADA, E.EN_EVALUACION): Transicion(_lista_para_evaluar, _iniciar_evaluacion),
    (E.EN_EVALUACION, E.CONSOLIDADA): Transicion(_sin_pendientes, _consolidar),
}


async def cambiar_estado(
    sesion: AsyncSession, usuario: Usuario, iniciativa: Iniciativa, hacia: E
) -> Iniciativa:
    if not gestiona(usuario, iniciativa):
        raise SinPermiso("Solo el Product Manager puede cambiar el estado de la iniciativa")
    desde = iniciativa.estado
    transicion = TRANSICIONES.get((desde, hacia))
    if transicion is None:
        raise Conflicto(f"No se puede pasar de «{NOMBRES[desde]}» a «{NOMBRES[hacia]}»")
    faltan = await transicion.condiciones(sesion, iniciativa)
    if faltan:
        raise ReglaIncumplida(
            f"La iniciativa no cumple las condiciones para pasar a «{NOMBRES[hacia]}»", faltan
        )
    if transicion.efecto is not None:
        await transicion.efecto(sesion, usuario, iniciativa)
    iniciativa.estado = hacia
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=usuario.id,
        accion="CAMBIAR_ESTADO",
        entidad="iniciativa",
        entidad_id=iniciativa.id,
        antes={"estado": desde.value},
        despues={"estado": hacia.value},
    )
    return iniciativa


def exigir_editable(iniciativa: Iniciativa) -> None:
    if iniciativa.estado not in ESTADOS_EDITABLES:
        raise Conflicto(f"La ficha no se puede modificar en estado «{NOMBRES[iniciativa.estado]}»")
