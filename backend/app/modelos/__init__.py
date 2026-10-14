"""Modelos SQLAlchemy. Importarlos aquí registra todas las tablas en Base.metadata."""

from app.modelos.auditoria import Auditoria
from app.modelos.evaluaciones import (
    Calificacion,
    ComentarioDivergencia,
    EnvioDimension,
    Evaluacion,
)
from app.modelos.iniciativas import AsignacionEvaluador, Iniciativa
from app.modelos.marco import Criterio, Dimension, NivelCriterio, VersionMarco
from app.modelos.usuarios import Rol, Usuario

__all__ = [
    "AsignacionEvaluador",
    "Auditoria",
    "Calificacion",
    "ComentarioDivergencia",
    "EnvioDimension",
    "Evaluacion",
    "Iniciativa",
    "Criterio",
    "Dimension",
    "NivelCriterio",
    "Rol",
    "Usuario",
    "VersionMarco",
]
