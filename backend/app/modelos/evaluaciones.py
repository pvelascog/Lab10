"""Evaluaciones, calificaciones, envíos por dimensión y comentarios (data-model.md – Evaluación)."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, ConFechas, ConId
from app.modelos.marco import Criterio, VersionMarco
from app.modelos.usuarios import Usuario


class EstadoEvaluacion(StrEnum):
    ABIERTA = "ABIERTA"
    CONSOLIDADA = "CONSOLIDADA"
    DECIDIDA = "DECIDIDA"


class OrigenCalificacion(StrEnum):
    HUMANA = "HUMANA"
    IA_SUGERIDA = "IA_SUGERIDA"
    IA_CONFIRMADA = "IA_CONFIRMADA"
    CALCULADA_CONFIRMADA = "CALCULADA_CONFIRMADA"


# Solo estas cuentan para el puntaje (Principio III: la IA sugiere, la persona confirma).
ORIGENES_VALIDOS = (
    OrigenCalificacion.HUMANA,
    OrigenCalificacion.IA_CONFIRMADA,
    OrigenCalificacion.CALCULADA_CONFIRMADA,
)


class Evaluacion(ConId, ConFechas, Base):
    __tablename__ = "evaluacion"
    __table_args__ = (UniqueConstraint("iniciativa_id", "numero"),)

    iniciativa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("iniciativa.id", ondelete="CASCADE"), index=True
    )
    # Versión del marco vigente al crearla; no cambia (Principio IV).
    version_marco_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("version_marco.id"))
    numero: Mapped[int]
    estado: Mapped[EstadoEvaluacion] = mapped_column(
        Enum(EstadoEvaluacion, name="estado_evaluacion", native_enum=False, length=20),
        default=EstadoEvaluacion.ABIERTA,
    )

    version_marco: Mapped[VersionMarco] = relationship(lazy="selectin")
    calificaciones: Mapped[list["Calificacion"]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan", lazy="selectin"
    )
    envios: Mapped[list["EnvioDimension"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    comentarios: Mapped[list["ComentarioDivergencia"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ComentarioDivergencia.creado_en",
    )


class Calificacion(ConId, ConFechas, Base):
    __tablename__ = "calificacion"
    __table_args__ = (
        UniqueConstraint("evaluacion_id", "criterio_id", "evaluador_id"),
        CheckConstraint("nivel BETWEEN 1 AND 5", name="nivel_rango"),
        CheckConstraint("length(trim(justificacion)) > 0", name="justificacion_obligatoria"),
    )

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="CASCADE"), index=True
    )
    criterio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("criterio.id"))
    # Nulo solo en las sugerencias de IA (data-model.md).
    evaluador_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
    nivel: Mapped[int]
    justificacion: Mapped[str] = mapped_column(Text)
    fuente: Mapped[str | None] = mapped_column(Text)
    origen: Mapped[OrigenCalificacion] = mapped_column(
        Enum(OrigenCalificacion, name="origen_calificacion", native_enum=False, length=30),
        default=OrigenCalificacion.HUMANA,
    )

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="calificaciones")
    criterio: Mapped[Criterio] = relationship(lazy="selectin")
    evaluador: Mapped[Usuario | None] = relationship(lazy="selectin")


class EnvioDimension(ConId, Base):
    __tablename__ = "envio_dimension"
    __table_args__ = (UniqueConstraint("evaluacion_id", "dimension_codigo", "evaluador_id"),)

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="CASCADE")
    )
    dimension_codigo: Mapped[str] = mapped_column(String(3))
    evaluador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
    enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComentarioDivergencia(ConId, ConFechas, Base):
    __tablename__ = "comentario_divergencia"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="CASCADE")
    )
    criterio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("criterio.id"))
    autor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
    texto: Mapped[str] = mapped_column(Text)

    autor: Mapped[Usuario] = relationship(lazy="selectin")
