"""Cálculos financieros que alimentan FIN-02 y FIN-03 (FR-009, marco-nepxa.md).

Funciones puras, sin dependencias de base de datos. Cuando un valor cae justo en el límite entre
dos rangos de la rúbrica, se asigna el nivel mejor (marco-nepxa.md, inconsistencia I-07).
"""

from dataclasses import dataclass, field
from decimal import Decimal

CERO = Decimal(0)

# (umbral mínimo de ROI en %, nivel) de mejor a peor. Rúbrica FIN-03.
_RANGOS_ROI: tuple[tuple[Decimal, int], ...] = (
    (Decimal(100), 5),
    (Decimal(75), 4),
    (Decimal(50), 3),
    (Decimal(25), 2),
)


def roi_porcentaje(inversion: Decimal, ingresos: Decimal) -> Decimal:
    """ROI (%) = (Ingresos esperados − Inversión) / Inversión × 100."""
    if inversion <= CERO:
        raise ValueError("La inversión debe ser mayor que cero")
    return (ingresos - inversion) / inversion * 100


def nivel_roi(roi: Decimal) -> int:
    """< 25 % → 1 · 25–50 % → 2 · 50–75 % → 3 · 75–100 % → 4 · ≥ 100 % → 5."""
    for minimo, nivel in _RANGOS_ROI:
        if roi >= minimo:
            return nivel
    return 1


def meses_recuperacion(inversion: Decimal, flujo_mensual_neto: Decimal) -> Decimal | None:
    """Meses para recuperar la inversión. None si el flujo no es positivo (no se recupera)."""
    if inversion <= CERO:
        raise ValueError("La inversión debe ser mayor que cero")
    if flujo_mensual_neto <= CERO:
        return None
    return inversion / flujo_mensual_neto


def nivel_recuperacion(meses: Decimal | None) -> int:
    """< 6 → 5 · 6–12 → 4 · 12–24 → 3 · 24–36 → 2 · > 36 o nunca → 1."""
    if meses is None:
        return 1
    if meses < 6:
        return 5
    if meses <= 12:
        return 4
    if meses <= 24:
        return 3
    if meses <= 36:
        return 2
    return 1


@dataclass(frozen=True)
class PropuestaFinanciera:
    """Niveles propuestos para FIN-03 (ROI) y FIN-02 (recuperación) y los datos que faltan."""

    roi: Decimal | None = None
    nivel_roi: int | None = None
    meses_recuperacion: Decimal | None = None
    nivel_recuperacion: int | None = None
    faltantes: list[str] = field(default_factory=list)


def proponer(
    *,
    inversion: Decimal | None,
    ingresos: Decimal | None,
    flujo_mensual: Decimal | None,
) -> PropuestaFinanciera:
    if inversion is not None and inversion <= CERO:
        raise ValueError("La inversión debe ser mayor que cero")
    if ingresos is not None and ingresos < CERO:
        raise ValueError("Los ingresos esperados no pueden ser negativos")

    faltantes = [
        nombre
        for nombre, valor in (
            ("inversion_estimada", inversion),
            ("ingresos_esperados", ingresos),
            ("flujo_mensual_neto", flujo_mensual),
        )
        if valor is None
    ]
    roi = nivel_r = meses = nivel_m = None
    if inversion is not None and ingresos is not None:
        roi = roi_porcentaje(inversion, ingresos)
        nivel_r = nivel_roi(roi)
    if inversion is not None and flujo_mensual is not None:
        meses = meses_recuperacion(inversion, flujo_mensual)
        nivel_m = nivel_recuperacion(meses)
    return PropuestaFinanciera(roi, nivel_r, meses, nivel_m, faltantes)
