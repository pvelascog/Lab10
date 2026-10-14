"""Consolidación de la evaluación y resumen ejecutivo (HU4, FR-011 a FR-017)."""

from math import floor
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.motor_decision import Umbrales, decidir, puntaje_dimension, score_total
from app.errores import Conflicto, NoEncontrado, SinPermiso
from app.modelos.evaluaciones import EstadoEvaluacion, Evaluacion, ResultadoConsolidado
from app.modelos.iniciativas import Iniciativa
from app.modelos.marco import VersionMarco
from app.modelos.usuarios import Usuario
from app.servicios import auditoria
from app.servicios.evaluaciones import Contexto
from app.servicios.visibilidad import gestiona

# Un criterio con puntaje menor o igual a este se propone como riesgo en el borrador.
UMBRAL_RIESGO = 2.0


def umbrales(version: VersionMarco) -> Umbrales:
    return Umbrales(
        critico=float(version.umbral_critico),
        validar=float(version.umbral_validar),
        debil=float(version.umbral_debil),
        score_go=float(version.umbral_score_go),
        score_iterar=float(version.umbral_score_iterar),
        score_validar=float(version.umbral_score_validar),
    )


def _t(valor: float) -> str:
    return f"{floor(valor * 100 + 1e-9) / 100:.2f}"


def evaluacion_abierta(iniciativa: Iniciativa) -> Evaluacion:
    e = iniciativa.evaluacion_actual
    if e is None or e.estado != EstadoEvaluacion.ABIERTA:
        raise Conflicto("La iniciativa no tiene una evaluación abierta")
    return e


def pendientes(iniciativa: Iniciativa) -> dict[str, str]:
    """Lo que impide consolidar, calculado con la vista completa (sin reglas de visibilidad)."""
    return Contexto(evaluacion_abierta(iniciativa), iniciativa, None).pendientes()


async def consolidar(sesion: AsyncSession, usuario: Usuario, iniciativa: Iniciativa) -> None:
    evaluacion = evaluacion_abierta(iniciativa)
    ctx = Contexto(evaluacion, iniciativa, None)
    version = evaluacion.version_marco
    u = umbrales(version)

    por_criterio = ctx.puntajes_criterio()
    por_dimension = {
        d.codigo: puntaje_dimension([por_criterio[c.codigo] for c in d.criterios])
        for d in version.dimensiones
    }
    score = score_total(por_dimension, {d.codigo: d.peso for d in version.dimensiones})
    decision = decidir(score, por_dimension, u)

    # Borrador del resumen ejecutivo; el PM lo ajusta (y en la Fase 8 se suma el de IA).
    nombres = {d.codigo: d.nombre for d in version.dimensiones}
    ordenadas = sorted(por_dimension.items(), key=lambda x: -x[1])
    evaluacion.resultado = ResultadoConsolidado(
        score_total=score,
        puntajes_dimension=por_dimension,
        puntajes_criterio=por_criterio,
        resultado=decision.resultado,
        regla=decision.regla,
        regla_aplicada=decision.descripcion,
        dimensiones_implicadas=decision.dimensiones_implicadas,
        fortalezas=[f"{nombres[c]} ({_t(p)})" for c, p in ordenadas if p >= u.score_go],
        debilidades=[f"{nombres[c]} ({_t(p)})" for c, p in reversed(ordenadas) if p < u.debil],
        riesgos=[
            f"{c.codigo} {c.nombre}: {_t(por_criterio[c.codigo])}"
            for d in version.dimensiones
            for c in d.criterios
            if por_criterio[c.codigo] <= UMBRAL_RIESGO
        ],
        supuestos_criticos=list(iniciativa.supuestos_clave or []),
        borrador_ia=False,
        consolidado_por_id=usuario.id,
    )
    evaluacion.estado = EstadoEvaluacion.CONSOLIDADA
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=usuario.id,
        accion="CONSOLIDAR",
        entidad="evaluacion",
        entidad_id=evaluacion.id,
        despues={
            "score_total": score,
            "resultado": decision.resultado.value,
            "regla": decision.descripcion,
        },
    )


LISTAS_EDITABLES = ("fortalezas", "debilidades", "riesgos", "supuestos_criticos")


async def editar_resumen(
    sesion: AsyncSession,
    usuario: Usuario,
    evaluacion: Evaluacion,
    iniciativa: Iniciativa,
    cambios: dict[str, Any],
) -> ResultadoConsolidado:
    if not gestiona(usuario, iniciativa):
        raise SinPermiso("Solo el Product Manager edita el resumen ejecutivo")
    resultado = evaluacion.resultado
    if resultado is None:
        raise NoEncontrado("La evaluación aún no está consolidada")
    if evaluacion.estado != EstadoEvaluacion.CONSOLIDADA:
        raise Conflicto("El resumen ya no se puede modificar")
    antes: dict[str, Any] = {}
    despues: dict[str, Any] = {}
    for campo in LISTAS_EDITABLES:
        if campo in cambios:
            nueva = [x.strip() for x in cambios[campo] or [] if x.strip()]
            antes[campo], despues[campo] = getattr(resultado, campo), nueva
            setattr(resultado, campo, nueva)
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=usuario.id,
        accion="EDITAR_RESUMEN",
        entidad="evaluacion",
        entidad_id=evaluacion.id,
        antes=antes,
        despues=despues,
    )
    return resultado
