"""Modelos SQLAlchemy. Importarlos aquí registra todas las tablas en Base.metadata."""

from app.modelos.auditoria import Auditoria
from app.modelos.marco import Criterio, Dimension, NivelCriterio, VersionMarco
from app.modelos.usuarios import Rol, Usuario

__all__ = ["Auditoria", "Criterio", "Dimension", "NivelCriterio", "Rol", "Usuario", "VersionMarco"]
