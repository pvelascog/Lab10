import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominio.motor_decision import Resultado, puntaje_criterio
from app.esquemas.iniciativas import UsuarioBreve
from app.esquemas.marco import NivelSalida
from app.modelos.evaluaciones import (
    Calificacion,
    ComentarioDivergencia,
    EstadoEvaluacion,
    ResultadoConsolidado,
)
from app.modelos.evaluaciones import OrigenCalificacion as Origen
from app.modelos.iniciativas import EstadoIniciativa
from app.modelos.marco import TipoCalculo
from app.servicios.evaluaciones import Contexto


def _no_vacio(valor: str) -> str:
    if not valor.strip():
        raise ValueError("No puede estar vacío")
    return valor


class CalificacionEntrada(BaseModel):
    nivel: Annotated[int, Field(ge=1, le=5)]
    justificacion: Annotated[str, Field(min_length=1, max_length=5000)]
    fuente: Annotated[str, Field(max_length=2000)] | None = None
    # Confirma el nivel calculado desde la ficha (FIN-02 / FIN-03).
    usa_calculo: bool = False

    _justificacion = field_validator("justificacion")(_no_vacio)


class ComentarioEntrada(BaseModel):
    texto: Annotated[str, Field(min_length=1, max_length=5000)]

    _texto = field_validator("texto")(_no_vacio)


class MiCalificacion(BaseModel):
    nivel: int
    justificacion: str
    fuente: str | None
    origen: Origen


class CalificacionPublicada(MiCalificacion):
    evaluador: UsuarioBreve


class ComentarioSalida(BaseModel):
    autor: UsuarioBreve
    texto: str
    creado_en: datetime

    @classmethod
    def desde(cls, c: ComentarioDivergencia) -> "ComentarioSalida":
        return cls(
            autor=UsuarioBreve(id=c.autor.id, nombre=c.autor.nombre),
            texto=c.texto,
            creado_en=c.creado_en,
        )


class CriterioEvaluacion(BaseModel):
    codigo: str
    nombre: str
    definicion: str
    escala_original: int
    calculable: TipoCalculo
    niveles: list[NivelSalida]
    propuesta_calculada: int | None
    mi_calificacion: MiCalificacion | None
    # null mientras el usuario no pueda verlas (calificación a ciegas).
    calificaciones: list[CalificacionPublicada] | None
    promedio: float | None
    divergencia: bool | None
    comentarios: list[ComentarioSalida] | None


class EvaluadorAvance(BaseModel):
    usuario: UsuarioBreve
    calificados: int
    enviado: bool


class DimensionEvaluacion(BaseModel):
    codigo: str
    nombre: str
    peso: float
    soy_evaluador: bool
    enviada_por_mi: bool
    ver_calificaciones: bool
    evaluadores: list[EvaluadorAvance]
    criterios: list[CriterioEvaluacion]


class IniciativaBreve(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    estado: EstadoIniciativa


class EvaluacionSalida(BaseModel):
    id: uuid.UUID
    numero: int
    estado: EstadoEvaluacion
    version_marco: str
    umbral_divergencia: int
    iniciativa: IniciativaBreve
    puede_gestionar: bool
    dimensiones: list[DimensionEvaluacion]
    # Solo para quien gestiona la iniciativa: lo que impide consolidar.
    pendientes: dict[str, str]

    @classmethod
    def construir(cls, ctx: Contexto, *, gestiona: bool) -> "EvaluacionSalida":
        e, i = ctx.evaluacion, ctx.iniciativa

        def publicada(c: Calificacion) -> CalificacionPublicada:
            if c.evaluador is None:  # las publicadas siempre tienen evaluador
                raise ValueError("Calificación publicada sin evaluador")
            return CalificacionPublicada(
                nivel=c.nivel,
                justificacion=c.justificacion,
                fuente=c.fuente,
                origen=c.origen,
                evaluador=UsuarioBreve(id=c.evaluador.id, nombre=c.evaluador.nombre),
            )

        dimensiones = []
        for d in ctx.dimensiones:
            ver = ctx.ve_calificaciones(d.codigo)
            criterios = []
            for c in d.criterios:
                mia = ctx.mia(c)
                publicadas = ctx.publicadas(c) if ver else []
                criterios.append(
                    CriterioEvaluacion(
                        codigo=c.codigo,
                        nombre=c.nombre,
                        definicion=c.definicion,
                        escala_original=c.escala_original,
                        calculable=c.calculable,
                        niveles=[
                            NivelSalida(nivel=n.nivel, descripcion=n.descripcion) for n in c.niveles
                        ],
                        propuesta_calculada=ctx.propuesta_calculada(c),
                        mi_calificacion=MiCalificacion(
                            nivel=mia.nivel,
                            justificacion=mia.justificacion,
                            fuente=mia.fuente,
                            origen=mia.origen,
                        )
                        if mia
                        else None,
                        calificaciones=[publicada(p) for p in publicadas] if ver else None,
                        promedio=puntaje_criterio([p.nivel for p in publicadas])
                        if ver and publicadas
                        else None,
                        divergencia=ctx.diverge(c) if ver else None,
                        comentarios=[ComentarioSalida.desde(x) for x in ctx.comentarios(c)]
                        if ver
                        else None,
                    )
                )
            dimensiones.append(
                DimensionEvaluacion(
                    codigo=d.codigo,
                    nombre=d.nombre,
                    peso=float(d.peso),
                    soy_evaluador=ctx.evalua(d.codigo),
                    enviada_por_mi=ctx.envio(d.codigo),
                    ver_calificaciones=ver,
                    evaluadores=[
                        EvaluadorAvance(
                            usuario=UsuarioBreve(id=u.id, nombre=u.nombre),
                            calificados=sum(
                                1
                                for x in e.calificaciones
                                if x.evaluador_id == u.id and x.criterio.dimension_id == d.id
                            ),
                            enviado=ctx.envio(d.codigo, u.id),
                        )
                        for u in ctx.evaluadores(d.codigo)
                    ],
                    criterios=criterios,
                )
            )
        return cls(
            id=e.id,
            numero=e.numero,
            estado=e.estado,
            version_marco=e.version_marco.numero,
            umbral_divergencia=e.version_marco.umbral_divergencia,
            iniciativa=IniciativaBreve(id=i.id, codigo=i.codigo, nombre=i.nombre, estado=i.estado),
            puede_gestionar=gestiona,
            dimensiones=dimensiones,
            pendientes=ctx.pendientes() if gestiona else {},
        )


class DivergenciaSalida(BaseModel):
    criterio: str
    dimension: str
    niveles: list[int]
    comentada: bool


class ResultadoSalida(BaseModel):
    """Resumen ejecutivo de una evaluación consolidada (FR-017)."""

    evaluacion_id: uuid.UUID
    iniciativa: IniciativaBreve
    version_marco: str
    score_total: float
    puntajes_dimension: dict[str, float]
    puntajes_criterio: dict[str, float]
    pesos: dict[str, float]
    umbrales: dict[str, float]
    nombres_dimension: dict[str, str]
    resultado: Resultado
    regla: str
    regla_aplicada: str
    dimensiones_implicadas: list[str]
    fortalezas: list[str]
    debilidades: list[str]
    riesgos: list[str]
    supuestos_criticos: list[str]
    borrador_ia: bool
    consolidado_en: datetime
    consolidado_por: UsuarioBreve | None
    puede_editar: bool

    @classmethod
    def construir(
        cls, ctx: Contexto, r: ResultadoConsolidado, *, puede_editar: bool
    ) -> "ResultadoSalida":
        v, i = ctx.evaluacion.version_marco, ctx.iniciativa
        return cls(
            evaluacion_id=ctx.evaluacion.id,
            iniciativa=IniciativaBreve(id=i.id, codigo=i.codigo, nombre=i.nombre, estado=i.estado),
            version_marco=v.numero,
            score_total=r.score_total,
            # JSONB no conserva el orden de las claves: se devuelven en el orden del marco.
            puntajes_dimension={d.codigo: r.puntajes_dimension[d.codigo] for d in v.dimensiones},
            puntajes_criterio={
                c.codigo: r.puntajes_criterio[c.codigo]
                for d in v.dimensiones
                for c in d.criterios
                if c.codigo in r.puntajes_criterio
            },
            pesos={d.codigo: float(d.peso) for d in v.dimensiones},
            umbrales={
                "critico": float(v.umbral_critico),
                "validar": float(v.umbral_validar),
                "debil": float(v.umbral_debil),
                "score_go": float(v.umbral_score_go),
                "score_iterar": float(v.umbral_score_iterar),
                "score_validar": float(v.umbral_score_validar),
            },
            nombres_dimension={d.codigo: d.nombre for d in v.dimensiones},
            resultado=r.resultado,
            regla=r.regla,
            regla_aplicada=r.regla_aplicada,
            dimensiones_implicadas=r.dimensiones_implicadas,
            fortalezas=r.fortalezas,
            debilidades=r.debilidades,
            riesgos=r.riesgos,
            supuestos_criticos=r.supuestos_criticos,
            borrador_ia=r.borrador_ia,
            consolidado_en=r.creado_en,
            consolidado_por=UsuarioBreve.desde(r.consolidado_por),
            puede_editar=puede_editar,
        )


Item = Annotated[str, Field(max_length=1000)]


class ResumenEditar(BaseModel):
    """Solo las listas del resumen; puntajes y resultado no se editan."""

    model_config = ConfigDict(extra="forbid")

    fortalezas: list[Item] | None = Field(default=None, max_length=30)
    debilidades: list[Item] | None = Field(default=None, max_length=30)
    riesgos: list[Item] | None = Field(default=None, max_length=30)
    supuestos_criticos: list[Item] | None = Field(default=None, max_length=30)
