"""Marco de evaluación versionado (data-model.md – Marco de evaluación)."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, ConFechas, ConId
from app.modelos.usuarios import CodigoRol


class EstadoVersion(StrEnum):
    BORRADOR = "BORRADOR"
    VIGENTE = "VIGENTE"
    RETIRADA = "RETIRADA"


class TipoCalculo(StrEnum):
    NO = "NO"
    ROI = "ROI"
    RECUPERACION = "RECUPERACION"


class VersionMarco(ConId, ConFechas, Base):
    __tablename__ = "version_marco"
    __table_args__ = (
        # Solo puede haber una versión vigente.
        Index(
            "uq_version_marco_vigente",
            "estado",
            unique=True,
            postgresql_where="estado = 'VIGENTE'",
        ),
    )

    numero: Mapped[str] = mapped_column(String(20), unique=True)
    estado: Mapped[EstadoVersion] = mapped_column(
        Enum(EstadoVersion, name="estado_version", native_enum=False, length=20)
    )
    umbral_critico: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("2.0"))
    umbral_validar: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("2.5"))
    umbral_debil: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("3.0"))
    umbral_score_go: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("4.0"))
    umbral_score_iterar: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("3.0"))
    umbral_score_validar: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("2.0"))
    umbral_divergencia: Mapped[int] = mapped_column(default=2)
    creada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )
    notas_cambio: Mapped[str | None] = mapped_column(Text)

    dimensiones: Mapped[list["Dimension"]] = relationship(
        back_populates="version_marco",
        order_by="Dimension.orden",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Dimension(ConId, Base):
    __tablename__ = "dimension"
    __table_args__ = (UniqueConstraint("version_marco_id", "codigo"),)

    version_marco_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("version_marco.id", ondelete="CASCADE")
    )
    codigo: Mapped[str] = mapped_column(String(3))
    nombre: Mapped[str] = mapped_column(String(100))
    proposito: Mapped[str] = mapped_column(Text)
    # Fracción del score total; la suma por versión es exactamente 1 (FR-012).
    peso: Mapped[Decimal] = mapped_column(Numeric(9, 8))
    rol_sugerido: Mapped[CodigoRol | None] = mapped_column(
        Enum(CodigoRol, name="codigo_rol", native_enum=False, length=30)
    )
    orden: Mapped[int]

    version_marco: Mapped[VersionMarco] = relationship(back_populates="dimensiones")
    criterios: Mapped[list["Criterio"]] = relationship(
        back_populates="dimension",
        order_by="Criterio.orden",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Criterio(ConId, Base):
    __tablename__ = "criterio"
    __table_args__ = (UniqueConstraint("dimension_id", "codigo"),)

    dimension_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dimension.id", ondelete="CASCADE"))
    codigo: Mapped[str] = mapped_column(String(10))
    nombre: Mapped[str] = mapped_column(String(100))
    definicion: Mapped[str] = mapped_column(Text)
    escala_original: Mapped[int] = mapped_column(default=5)
    calculable: Mapped[TipoCalculo] = mapped_column(
        Enum(TipoCalculo, name="tipo_calculo", native_enum=False, length=20),
        default=TipoCalculo.NO,
    )
    orden: Mapped[int]

    dimension: Mapped[Dimension] = relationship(back_populates="criterios")
    niveles: Mapped[list["NivelCriterio"]] = relationship(
        back_populates="criterio",
        order_by="NivelCriterio.nivel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NivelCriterio(ConId, Base):
    __tablename__ = "nivel_criterio"
    __table_args__ = (
        UniqueConstraint("criterio_id", "nivel"),
        CheckConstraint("nivel BETWEEN 1 AND 5", name="nivel_rango"),
    )

    criterio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("criterio.id", ondelete="CASCADE"))
    nivel: Mapped[int]
    descripcion: Mapped[str] = mapped_column(Text)

    criterio: Mapped[Criterio] = relationship(back_populates="niveles")
