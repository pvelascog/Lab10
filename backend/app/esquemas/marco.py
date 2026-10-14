import uuid

from pydantic import BaseModel

from app.modelos.marco import EstadoVersion, TipoCalculo, VersionMarco
from app.modelos.usuarios import CodigoRol


class NivelSalida(BaseModel):
    nivel: int
    descripcion: str


class CriterioSalida(BaseModel):
    codigo: str
    nombre: str
    definicion: str
    escala_original: int
    calculable: TipoCalculo
    niveles: list[NivelSalida]


class DimensionSalida(BaseModel):
    codigo: str
    nombre: str
    proposito: str
    peso: float
    rol_sugerido: CodigoRol | None
    criterios: list[CriterioSalida]


class UmbralesSalida(BaseModel):
    critico: float
    validar: float
    debil: float
    score_go: float
    score_iterar: float
    score_validar: float
    divergencia: int


class VersionMarcoSalida(BaseModel):
    id: uuid.UUID
    numero: str
    estado: EstadoVersion
    umbrales: UmbralesSalida
    dimensiones: list[DimensionSalida]

    @classmethod
    def desde(cls, v: VersionMarco) -> "VersionMarcoSalida":
        return cls(
            id=v.id,
            numero=v.numero,
            estado=v.estado,
            umbrales=UmbralesSalida(
                critico=float(v.umbral_critico),
                validar=float(v.umbral_validar),
                debil=float(v.umbral_debil),
                score_go=float(v.umbral_score_go),
                score_iterar=float(v.umbral_score_iterar),
                score_validar=float(v.umbral_score_validar),
                divergencia=v.umbral_divergencia,
            ),
            dimensiones=[
                DimensionSalida(
                    codigo=d.codigo,
                    nombre=d.nombre,
                    proposito=d.proposito,
                    peso=float(d.peso),
                    rol_sugerido=d.rol_sugerido,
                    criterios=[
                        CriterioSalida(
                            codigo=c.codigo,
                            nombre=c.nombre,
                            definicion=c.definicion,
                            escala_original=c.escala_original,
                            calculable=c.calculable,
                            niveles=[
                                NivelSalida(nivel=n.nivel, descripcion=n.descripcion)
                                for n in c.niveles
                            ],
                        )
                        for c in d.criterios
                    ],
                )
                for d in v.dimensiones
            ],
        )
