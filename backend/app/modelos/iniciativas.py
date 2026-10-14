"""Iniciativas y asignación de evaluadores (data-model.md – Iniciativas)."""

import uuid
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Identity, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, ConFechas, ConId
from app.modelos.usuarios import Usuario

if TYPE_CHECKING:
    from app.modelos.evaluaciones import Evaluacion


class EstadoIniciativa(StrEnum):
    IDENTIFICADA = "IDENTIFICADA"
    ESTRUCTURADA = "ESTRUCTURADA"
    EN_EVALUACION = "EN_EVALUACION"
    CONSOLIDADA = "CONSOLIDADA"
    EN_COMITE = "EN_COMITE"
    DECIDIDA = "DECIDIDA"
    EN_SEGUIMIENTO = "EN_SEGUIMIENTO"
    ARCHIVADA = "ARCHIVADA"


class OrigenIniciativa(StrEnum):
    CLIENTES = "CLIENTES"
    EQUIPO_INTERNO = "EQUIPO_INTERNO"
    MERCADO = "MERCADO"
    SOCIOS = "SOCIOS"
    TENDENCIAS = "TENDENCIAS"
    PORTAFOLIO = "PORTAFOLIO"
    INNOVACION_INTERNA = "INNOVACION_INTERNA"


class OrigenAsignacion(StrEnum):
    MANUAL = "MANUAL"
    SUGERIDA = "SUGERIDA"


class Iniciativa(ConId, ConFechas, Base):
    __tablename__ = "iniciativa"

    # Número correlativo para el código legible INI-AAAA-NNNN.
    numero: Mapped[int] = mapped_column(Identity(), unique=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    origen: Mapped[OrigenIniciativa] = mapped_column(
        Enum(OrigenIniciativa, name="origen_iniciativa", native_enum=False, length=30)
    )
    estado: Mapped[EstadoIniciativa] = mapped_column(
        Enum(EstadoIniciativa, name="estado_iniciativa", native_enum=False, length=30),
        default=EstadoIniciativa.IDENTIFICADA,
        index=True,
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
    pm_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), index=True)

    # Ficha (HU2). Obligatoria para pasar a ESTRUCTURADA.
    problema: Mapped[str | None] = mapped_column(Text)
    solucion_objetivo: Mapped[str | None] = mapped_column(Text)
    segmento: Mapped[str | None] = mapped_column(Text)
    propuesta_valor: Mapped[str | None] = mapped_column(Text)
    supuestos_clave: Mapped[list[str]] = mapped_column(JSONB, default=list)
    datos_disponibles: Mapped[str | None] = mapped_column(Text)
    inversion_estimada: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    ingresos_esperados: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    flujo_mensual_neto: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))

    posible_duplicado_de_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("iniciativa.id", ondelete="SET NULL")
    )
    similitud_duplicado: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    autor: Mapped[Usuario] = relationship(foreign_keys=[autor_id], lazy="selectin")
    pm: Mapped[Usuario | None] = relationship(foreign_keys=[pm_id], lazy="selectin")
    posible_duplicado_de: Mapped["Iniciativa | None"] = relationship(
        remote_side="Iniciativa.id", lazy="selectin", join_depth=1
    )
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="Evaluacion.numero"
    )
    asignaciones: Mapped[list["AsignacionEvaluador"]] = relationship(
        back_populates="iniciativa",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="(AsignacionEvaluador.dimension_codigo, AsignacionEvaluador.creado_en)",
    )

    @property
    def evaluacion_actual(self) -> "Evaluacion | None":
        return self.evaluaciones[-1] if self.evaluaciones else None


class AsignacionEvaluador(ConId, ConFechas, Base):
    __tablename__ = "asignacion_evaluador"
    __table_args__ = (UniqueConstraint("iniciativa_id", "dimension_codigo", "usuario_id"),)

    iniciativa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("iniciativa.id", ondelete="CASCADE")
    )
    dimension_codigo: Mapped[str] = mapped_column(String(3))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
    origen: Mapped[OrigenAsignacion] = mapped_column(
        Enum(OrigenAsignacion, name="origen_asignacion", native_enum=False, length=20),
        default=OrigenAsignacion.MANUAL,
    )
    razon_sugerencia: Mapped[str | None] = mapped_column(Text)

    iniciativa: Mapped[Iniciativa] = relationship(back_populates="asignaciones")
    usuario: Mapped[Usuario] = relationship(lazy="selectin")
