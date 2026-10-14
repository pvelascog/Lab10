"""Motor de decisión del Marco NEPXA (plan.md – Motor de decisión).

Funciones puras y deterministas, sin base de datos ni IA (Principio V). Incluye las reglas por
criterio (HU3) y la consolidación por dimensión con el resultado recomendado (HU4).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from math import floor

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


# --- Consolidación y resultado (HU4) ----------------------------------------------------------


class Resultado(StrEnum):
    GO = "GO"
    ITERAR = "ITERAR"
    VALIDAR = "VALIDAR"
    NO_GO = "NO_GO"


# De peor a mejor: sirve para comparar resultados.
ORDEN: dict[Resultado, int] = {
    Resultado.NO_GO: 0,
    Resultado.VALIDAR: 1,
    Resultado.ITERAR: 2,
    Resultado.GO: 3,
}


@dataclass(frozen=True)
class Umbrales:
    """Umbrales del modelo de decisión; se leen de la versión del marco (Principio IV)."""

    critico: float = 2.0  # una dimensión por debajo → NO-GO
    validar: float = 2.5  # dos o más dimensiones por debajo → VALIDAR
    debil: float = 3.0  # una dimensión por debajo → ITERAR
    score_go: float = 4.0
    score_iterar: float = 3.0
    score_validar: float = 2.0


@dataclass(frozen=True)
class Decision:
    resultado: Resultado
    regla: str  # R1..R4
    descripcion: str
    dimensiones_implicadas: list[str] = field(default_factory=list)


def puntaje_dimension(puntajes_criterios: Sequence[float]) -> float:
    """Promedio simple de los criterios de la dimensión (FR-011)."""
    if not puntajes_criterios:
        raise ValueError("La dimensión no tiene criterios calificados")
    return sum(puntajes_criterios) / len(puntajes_criterios)


def score_total(puntajes: Mapping[str, float], pesos: Mapping[str, Decimal]) -> float:
    """Promedio ponderado de las dimensiones (FR-012). Se normaliza por la suma de pesos."""
    faltan = set(puntajes) - set(pesos)
    if faltan:
        raise ValueError(f"Falta el peso de: {', '.join(sorted(faltan))}")
    total_pesos = sum(float(pesos[d]) for d in puntajes)
    if total_pesos <= 0:
        raise ValueError("La suma de los pesos debe ser positiva")
    return sum(float(pesos[d]) * s for d, s in puntajes.items()) / total_pesos


def _t(valor: float) -> str:
    """Trunca a 2 decimales para las explicaciones (nunca aparenta cruzar un umbral)."""
    return f"{floor(valor * 100 + 1e-9) / 100:.2f}"


def _u(umbral: float) -> str:
    return f"{umbral:.1f}"


def _lista(puntajes: Mapping[str, float], codigos: list[str]) -> str:
    return ", ".join(f"{c} = {_t(puntajes[c])}" for c in codigos)


def decidir(score: float, puntajes: Mapping[str, float], u: Umbrales) -> Decision:
    """Resultado recomendado con la regla más restrictiva (FR-016, clarificación C1).

    Se aplican en orden y prevalece la primera que se cumple:
      R1. score < 2.0 o alguna dimensión < 2.0          → NO-GO
      R2. score < 3.0 o dos o más dimensiones < 2.5     → VALIDAR
      R3. score < 4.0 o alguna dimensión < 3.0          → ITERAR
      R4. en otro caso                                  → GO
    Las comparaciones son estrictas y sobre valores sin redondear.
    """
    criticas = [d for d, v in puntajes.items() if v < u.critico]
    if score < u.score_validar or criticas:
        if score < u.score_validar:
            texto = f"R1: score {_t(score)} < {_u(u.score_validar)}"
        elif len(criticas) == 1:
            texto = f"R1: dimensión {_lista(puntajes, criticas)} < {_u(u.critico)}"
        else:
            texto = f"R1: dimensiones {_lista(puntajes, criticas)} < {_u(u.critico)}"
        return Decision(Resultado.NO_GO, "R1", texto, criticas)

    bajas = [d for d, v in puntajes.items() if v < u.validar]
    if score < u.score_iterar or len(bajas) >= 2:
        if score < u.score_iterar:
            texto = f"R2: score {_t(score)} < {_u(u.score_iterar)}"
        else:
            texto = f"R2: dos o más dimensiones < {_u(u.validar)} ({_lista(puntajes, bajas)})"
        return Decision(Resultado.VALIDAR, "R2", texto, bajas if len(bajas) >= 2 else [])

    debiles = [d for d, v in puntajes.items() if v < u.debil]
    if score < u.score_go or debiles:
        if score < u.score_go:
            texto = f"R3: score {_t(score)} < {_u(u.score_go)}"
        elif len(debiles) == 1:
            texto = f"R3: dimensión {_lista(puntajes, debiles)} < {_u(u.debil)}"
        else:
            texto = f"R3: dimensiones {_lista(puntajes, debiles)} < {_u(u.debil)}"
        return Decision(Resultado.ITERAR, "R3", texto, debiles)

    return Decision(
        Resultado.GO,
        "R4",
        f"R4: score ≥ {_u(u.score_go)} y todas las dimensiones ≥ {_u(u.debil)}",
    )
