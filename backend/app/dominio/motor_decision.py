"""Motor de decisión del Marco NEPXA (plan.md – Motor de decisión).

Funciones puras y deterministas, sin base de datos ni IA (Principio V). En la Fase 5 (HU3) se
implementan las reglas por criterio; la consolidación por dimensión y el resultado se agregan
en la Fase 6 (HU4).
"""

from collections.abc import Sequence

UMBRAL_DIVERGENCIA = 2

# Recurrencia (COM-04) usa una escala 1–3 en el marco; se normaliza a 1, 3 y 5 (FR-008).
_RECURRENCIA = {1: 1, 2: 3, 3: 5}


def puntaje_criterio(calificaciones: Sequence[int]) -> float:
    """Puntaje de un criterio: promedio de las calificaciones de sus evaluadores (FR-010a)."""
    if not calificaciones:
        raise ValueError("Se necesita al menos una calificación")
    return sum(calificaciones) / len(calificaciones)


def divergencia(calificaciones: Sequence[int], umbral: int = UMBRAL_DIVERGENCIA) -> bool:
    """Hay divergencia si dos calificaciones del mismo criterio difieren en `umbral` o más."""
    return len(calificaciones) >= 2 and max(calificaciones) - min(calificaciones) >= umbral


def normalizar_recurrencia(nivel_original: int) -> int:
    """Convierte la escala 1–3 de Recurrencia a la escala común 1–5."""
    if nivel_original not in _RECURRENCIA:
        raise ValueError("Recurrencia se califica de 1 a 3 en su escala original")
    return _RECURRENCIA[nivel_original]
