"""Evaluación multidimensional (HU3): calificación a ciegas, envío por dimensión y divergencias.

Reglas de visibilidad (FR-010b):
- Una calificación se *publica* cuando su evaluador envía la dimensión. Los borradores solo los ve
  su autor.
- Un evaluador asignado a una dimensión ve las calificaciones publicadas de los demás solo después
  de enviar la suya.
- Quien ve el portafolio (PM, Comité, Administrador) y no evalúa esa dimensión ve las publicadas.
- Al consolidar (HU4) todas quedan visibles para quien pueda ver la iniciativa.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.calculos_financieros import proponer
from app.dominio.motor_decision import divergencia, puntaje_criterio
from app.errores import Conflicto, DatosInvalidos, NoEncontrado, ReglaIncumplida, SinPermiso
from app.modelos.evaluaciones import (
    ORIGENES_VALIDOS,
    Calificacion,
    ComentarioDivergencia,
    EnvioDimension,
    EstadoEvaluacion,
    Evaluacion,
    OrigenCalificacion,
)
from app.modelos.iniciativas import Iniciativa
from app.modelos.marco import Criterio, Dimension, EstadoVersion, TipoCalculo, VersionMarco
from app.modelos.usuarios import Usuario
from app.servicios import auditoria
from app.servicios.visibilidad import es_visible, gestiona, ve_portafolio


async def marco_vigente(sesion: AsyncSession) -> VersionMarco:
    version = await sesion.scalar(
        select(VersionMarco).where(VersionMarco.estado == EstadoVersion.VIGENTE)
    )
    if version is None:
        raise Conflicto("No hay una versión vigente del marco")
    return version


async def crear(sesion: AsyncSession, iniciativa: Iniciativa) -> Evaluacion:
    """Nueva evaluación con la versión vigente del marco (también para revaluaciones, HU8)."""
    version = await marco_vigente(sesion)
    evaluacion = Evaluacion(
        version_marco_id=version.id,
        numero=len(iniciativa.evaluaciones) + 1,
        estado=EstadoEvaluacion.ABIERTA,
    )
    iniciativa.evaluaciones.append(evaluacion)
    await sesion.flush()
    await sesion.refresh(evaluacion, ["version_marco"])
    return evaluacion


@dataclass
class Contexto:
    """Una evaluación junto con su iniciativa y el usuario que la consulta."""

    evaluacion: Evaluacion
    iniciativa: Iniciativa
    # None: vista completa del sistema, sin reglas de visibilidad (consolidación).
    usuario: Usuario | None

    @property
    def dimensiones(self) -> list[Dimension]:
        return self.evaluacion.version_marco.dimensiones

    def criterio(self, codigo: str) -> Criterio:
        for d in self.dimensiones:
            for c in d.criterios:
                if c.codigo == codigo.upper():
                    return c
        raise NoEncontrado(f"El criterio {codigo} no existe en esta versión del marco")

    def dimension(self, codigo: str) -> Dimension:
        for d in self.dimensiones:
            if d.codigo == codigo.upper():
                return d
        raise NoEncontrado(f"La dimensión {codigo} no existe en esta versión del marco")

    def dimension_de(self, criterio: Criterio) -> Dimension:
        return next(d for d in self.dimensiones if d.id == criterio.dimension_id)

    def evaluadores(self, dimension: str) -> list[Usuario]:
        return [a.usuario for a in self.iniciativa.asignaciones if a.dimension_codigo == dimension]

    def _uid(self, usuario_id: uuid.UUID | None) -> uuid.UUID | None:
        return usuario_id or (self.usuario.id if self.usuario else None)

    def evalua(self, dimension: str, usuario_id: uuid.UUID | None = None) -> bool:
        uid = self._uid(usuario_id)
        return any(u.id == uid for u in self.evaluadores(dimension))

    def envio(self, dimension: str, usuario_id: uuid.UUID | None = None) -> bool:
        uid = self._uid(usuario_id)
        return any(
            e.dimension_codigo == dimension and e.evaluador_id == uid
            for e in self.evaluacion.envios
        )

    def ve_calificaciones(self, dimension: str) -> bool:
        if self.usuario is None or self.evaluacion.estado != EstadoEvaluacion.ABIERTA:
            return True
        if self.evalua(dimension):
            return self.envio(dimension)
        return ve_portafolio(self.usuario)

    def puntajes_criterio(self) -> dict[str, float]:
        """Promedio de las calificaciones enviadas de cada criterio que tiene alguna."""
        return {
            c.codigo: puntaje_criterio([p.nivel for p in publicadas])
            for d in self.dimensiones
            for c in d.criterios
            if (publicadas := self.publicadas(c))
        }

    def mia(self, criterio: Criterio) -> Calificacion | None:
        if self.usuario is None:
            return None
        return next(
            (
                c
                for c in self.evaluacion.calificaciones
                if c.criterio_id == criterio.id and c.evaluador_id == self.usuario.id
            ),
            None,
        )

    def publicadas(self, criterio: Criterio) -> list[Calificacion]:
        dimension = self.dimension_de(criterio).codigo
        return [
            c
            for c in self.evaluacion.calificaciones
            if c.criterio_id == criterio.id
            and c.origen in ORIGENES_VALIDOS
            and c.evaluador_id is not None
            and self.envio(dimension, c.evaluador_id)
        ]

    def diverge(self, criterio: Criterio) -> bool:
        umbral = self.evaluacion.version_marco.umbral_divergencia
        return divergencia([c.nivel for c in self.publicadas(criterio)], umbral)

    def comentarios(self, criterio: Criterio) -> list[ComentarioDivergencia]:
        return [c for c in self.evaluacion.comentarios if c.criterio_id == criterio.id]

    def propuesta_calculada(self, criterio: Criterio) -> int | None:
        if criterio.calculable == TipoCalculo.NO:
            return None
        i = self.iniciativa
        p = proponer(
            inversion=i.inversion_estimada,
            ingresos=i.ingresos_esperados,
            flujo_mensual=i.flujo_mensual_neto,
        )
        return p.nivel_roi if criterio.calculable == TipoCalculo.ROI else p.nivel_recuperacion

    def pendientes(self) -> dict[str, str]:
        """Lo que impide consolidar (HU4): criterios sin calificaciones enviadas y divergencias
        sin comentar. No revela divergencias de dimensiones que el usuario aún no puede ver."""
        pendientes: dict[str, str] = {}
        for d in self.dimensiones:
            visible = self.ve_calificaciones(d.codigo)
            for c in d.criterios:
                if not self.publicadas(c):
                    pendientes[c.codigo] = "Sin calificaciones enviadas"
                elif visible and self.diverge(c) and not self.comentarios(c):
                    pendientes[c.codigo] = "Divergencia sin comentar"
        return pendientes


async def contexto(sesion: AsyncSession, usuario: Usuario, evaluacion_id: uuid.UUID) -> Contexto:
    evaluacion = await sesion.get(Evaluacion, evaluacion_id)
    iniciativa = (
        await sesion.get(Iniciativa, evaluacion.iniciativa_id) if evaluacion is not None else None
    )
    if evaluacion is None or iniciativa is None or not es_visible(usuario, iniciativa):
        raise NoEncontrado("Evaluación no encontrada")
    return Contexto(evaluacion, iniciativa, usuario)


def _usuario(ctx: Contexto) -> Usuario:
    if ctx.usuario is None:
        raise ValueError("Operación que requiere un usuario")
    return ctx.usuario


def _exigir_abierta(ctx: Contexto) -> None:
    if ctx.evaluacion.estado != EstadoEvaluacion.ABIERTA:
        raise Conflicto("La evaluación ya no admite cambios")


def _exigir_evaluador(ctx: Contexto, dimension: Dimension) -> None:
    if not ctx.evalua(dimension.codigo):
        raise SinPermiso(f"No está asignado como evaluador de la dimensión {dimension.nombre}")
    if ctx.envio(dimension.codigo):
        raise Conflicto(f"Ya envió la dimensión {dimension.nombre}; no se puede modificar")


async def calificar(
    sesion: AsyncSession,
    ctx: Contexto,
    codigo_criterio: str,
    *,
    nivel: int,
    justificacion: str,
    fuente: str | None,
    usa_calculo: bool = False,
) -> Calificacion:
    _exigir_abierta(ctx)
    criterio = ctx.criterio(codigo_criterio)
    _exigir_evaluador(ctx, ctx.dimension_de(criterio))

    permitidos = sorted(n.nivel for n in criterio.niveles)
    if nivel not in permitidos:
        raise DatosInvalidos({"nivel": f"Niveles válidos: {', '.join(map(str, permitidos))}"})
    origen = OrigenCalificacion.HUMANA
    if usa_calculo:
        propuesta = ctx.propuesta_calculada(criterio)
        if propuesta is None or propuesta != nivel:
            raise DatosInvalidos(
                {"nivel": "No coincide con el nivel calculado a partir de la ficha"}
            )
        origen = OrigenCalificacion.CALCULADA_CONFIRMADA

    calificacion = ctx.mia(criterio)
    if calificacion is None:
        calificacion = Calificacion(
            criterio=criterio,
            evaluador_id=_usuario(ctx).id,
            nivel=nivel,
            justificacion=justificacion.strip(),
            fuente=fuente,
            origen=origen,
        )
        ctx.evaluacion.calificaciones.append(calificacion)
    else:
        calificacion.nivel = nivel
        calificacion.justificacion = justificacion.strip()
        calificacion.fuente = fuente
        calificacion.origen = origen
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=_usuario(ctx).id,
        accion="CALIFICAR",
        entidad="evaluacion",
        entidad_id=ctx.evaluacion.id,
        despues={
            "criterio": criterio.codigo,
            "nivel": nivel,
            "justificacion": calificacion.justificacion,
            "origen": origen.value,
        },
    )
    return calificacion


async def enviar_dimension(sesion: AsyncSession, ctx: Contexto, codigo_dimension: str) -> None:
    _exigir_abierta(ctx)
    dimension = ctx.dimension(codigo_dimension)
    _exigir_evaluador(ctx, dimension)
    faltan = {c.codigo: "Sin calificar" for c in dimension.criterios if ctx.mia(c) is None}
    if faltan:
        raise ReglaIncumplida(
            f"Califique todos los criterios de {dimension.nombre} antes de enviarla", faltan
        )
    ctx.evaluacion.envios.append(
        EnvioDimension(dimension_codigo=dimension.codigo, evaluador_id=_usuario(ctx).id)
    )
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=_usuario(ctx).id,
        accion="ENVIAR_DIMENSION",
        entidad="evaluacion",
        entidad_id=ctx.evaluacion.id,
        despues={"dimension": dimension.codigo},
    )


async def comentar_divergencia(
    sesion: AsyncSession, ctx: Contexto, codigo_criterio: str, texto: str
) -> ComentarioDivergencia:
    _exigir_abierta(ctx)
    criterio = ctx.criterio(codigo_criterio)
    dimension = ctx.dimension_de(criterio)
    if not (ctx.evalua(dimension.codigo) or gestiona(_usuario(ctx), ctx.iniciativa)):
        raise SinPermiso("Solo los evaluadores de la dimensión o el PM pueden comentar")
    if not ctx.ve_calificaciones(dimension.codigo) or not ctx.diverge(criterio):
        raise ReglaIncumplida(f"El criterio {criterio.codigo} no presenta una divergencia visible")
    comentario = ComentarioDivergencia(
        criterio_id=criterio.id, autor_id=_usuario(ctx).id, texto=texto.strip()
    )
    ctx.evaluacion.comentarios.append(comentario)
    await sesion.flush()
    await sesion.refresh(comentario, ["autor", "creado_en"])
    await auditoria.registrar(
        sesion,
        usuario_id=_usuario(ctx).id,
        accion="COMENTAR_DIVERGENCIA",
        entidad="evaluacion",
        entidad_id=ctx.evaluacion.id,
        despues={"criterio": criterio.codigo, "texto": comentario.texto},
    )
    return comentario
