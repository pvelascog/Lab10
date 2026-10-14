"""Registro de auditoría de solo inserción (FR-026)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, ConId


class Auditoria(ConId, Base):
    __tablename__ = "auditoria"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), index=True
    )
    accion: Mapped[str] = mapped_column(String(50), index=True)
    entidad: Mapped[str] = mapped_column(String(50))
    entidad_id: Mapped[str | None] = mapped_column(String(64))
    antes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    despues: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
