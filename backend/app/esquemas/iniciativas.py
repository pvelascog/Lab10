import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.modelos.iniciativas import (
    EstadoIniciativa,
    Iniciativa,
    OrigenAsignacion,
    OrigenIniciativa,
)
from app.modelos.usuarios import Usuario


def _no_vacio(valor: str) -> str:
    if not valor.strip():
        raise ValueError("No puede estar vacío")
    return valor


class AsignacionEntrada(BaseModel):
    dimension: Annotated[str, Field(min_length=3, max_length=3)]
    usuario_id: uuid.UUID


class IniciativaCrear(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=200)]
    descripcion: Annotated[str, Field(min_length=1, max_length=5000)]
    origen: OrigenIniciativa
    asignaciones: list[AsignacionEntrada] = []

    _validar_textos = field_validator("nombre", "descripcion")(_no_vacio)


class UsuarioBreve(BaseModel):
    id: uuid.UUID
    nombre: str

    @classmethod
    def desde(cls, u: Usuario | None) -> "UsuarioBreve | None":
        return cls(id=u.id, nombre=u.nombre) if u else None


class AsignacionSalida(BaseModel):
    dimension: str
    usuario: UsuarioBreve
    origen: OrigenAsignacion


class DuplicadoSalida(BaseModel):
    """Posible duplicado. El nombre y el id solo se muestran si el usuario puede verla."""

    id: uuid.UUID | None
    codigo: str
    nombre: str | None
    similitud: float


class IniciativaResumen(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str
    origen: OrigenIniciativa
    estado: EstadoIniciativa
    autor: UsuarioBreve
    pm: UsuarioBreve | None
    creado_en: datetime

    @classmethod
    def desde(cls, i: Iniciativa) -> "IniciativaResumen":
        return cls(
            id=i.id,
            codigo=i.codigo,
            nombre=i.nombre,
            descripcion=i.descripcion,
            origen=i.origen,
            estado=i.estado,
            autor=UsuarioBreve(id=i.autor.id, nombre=i.autor.nombre),
            pm=UsuarioBreve.desde(i.pm),
            creado_en=i.creado_en,
        )


class IniciativaDetalle(IniciativaResumen):
    problema: str | None
    solucion_objetivo: str | None
    segmento: str | None
    propuesta_valor: str | None
    supuestos_clave: list[str]
    datos_disponibles: str | None
    inversion_estimada: float | None
    ingresos_esperados: float | None
    flujo_mensual_neto: float | None
    asignaciones: list[AsignacionSalida]
    posible_duplicado_de: DuplicadoSalida | None

    @classmethod
    def construir(cls, i: Iniciativa, *, duplicado_visible: bool) -> "IniciativaDetalle":
        def num(valor: Decimal | None) -> float | None:
            return None if valor is None else float(valor)

        duplicado = None
        if i.posible_duplicado_de is not None:
            d = i.posible_duplicado_de
            duplicado = DuplicadoSalida(
                id=d.id if duplicado_visible else None,
                codigo=d.codigo,
                nombre=d.nombre if duplicado_visible else None,
                similitud=float(i.similitud_duplicado or 0),
            )
        return cls(
            **IniciativaResumen.desde(i).model_dump(),
            problema=i.problema,
            solucion_objetivo=i.solucion_objetivo,
            segmento=i.segmento,
            propuesta_valor=i.propuesta_valor,
            supuestos_clave=list(i.supuestos_clave or []),
            datos_disponibles=i.datos_disponibles,
            inversion_estimada=num(i.inversion_estimada),
            ingresos_esperados=num(i.ingresos_esperados),
            flujo_mensual_neto=num(i.flujo_mensual_neto),
            asignaciones=[
                AsignacionSalida(
                    dimension=a.dimension_codigo,
                    usuario=UsuarioBreve(id=a.usuario.id, nombre=a.usuario.nombre),
                    origen=a.origen,
                )
                for a in i.asignaciones
            ],
            posible_duplicado_de=duplicado,
        )
