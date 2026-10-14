"""Usuarios y roles (data-model.md – Usuarios y acceso)."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, ConFechas, ConId


class CodigoRol(StrEnum):
    MIEMBRO = "MIEMBRO"
    PM = "PM"
    LIDER_COMERCIAL = "LIDER_COMERCIAL"
    LIDER_TECNICO = "LIDER_TECNICO"
    LIDER_ESTRATEGIA = "LIDER_ESTRATEGIA"
    COMITE = "COMITE"
    ADMIN_MARCO = "ADMIN_MARCO"


usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
)


class Rol(ConId, Base):
    __tablename__ = "rol"

    codigo: Mapped[CodigoRol] = mapped_column(
        Enum(CodigoRol, name="codigo_rol", native_enum=False, length=30), unique=True
    )
    nombre: Mapped[str] = mapped_column(String(100))


class Usuario(ConId, ConFechas, Base):
    __tablename__ = "usuario"

    nombre: Mapped[str] = mapped_column(String(200))
    correo: Mapped[str] = mapped_column(String(320), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(default=True)
    intentos_fallidos: Mapped[int] = mapped_column(default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list[Rol]] = relationship(secondary=usuario_rol, lazy="selectin")

    @property
    def codigos_roles(self) -> list[CodigoRol]:
        orden = list(CodigoRol)
        return sorted((r.codigo for r in self.roles), key=orden.index)

    def tiene_rol(self, *roles: CodigoRol) -> bool:
        return any(r.codigo in roles for r in self.roles)
