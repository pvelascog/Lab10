"""T039 – Cálculos financieros de FIN-02 y FIN-03 (FR-009, marco-nepxa.md I-07)."""

from decimal import Decimal as D  # noqa: N817  # abreviatura legible en tablas de casos

import pytest

from app.dominio.calculos_financieros import (
    meses_recuperacion,
    nivel_recuperacion,
    nivel_roi,
    proponer,
    roi_porcentaje,
)

# --- ROI (FIN-03) -----------------------------------------------------------------------------


def test_roi_segun_la_formula_del_marco() -> None:
    # ROI (%) = (Ingresos esperados − Inversión) / Inversión × 100
    assert roi_porcentaje(D("100000"), D("180000")) == D("80")
    assert roi_porcentaje(D("100000"), D("50000")) == D("-50")


@pytest.mark.parametrize("inversion", [D("0"), D("-1")])
def test_roi_rechaza_inversion_no_positiva(inversion: D) -> None:
    with pytest.raises(ValueError, match="inversión"):
        roi_porcentaje(inversion, D("1000"))


@pytest.mark.parametrize(
    ("roi", "nivel"),
    [
        (D("-50"), 1),
        (D("24.99"), 1),
        (D("25"), 2),  # el límite pertenece al nivel mejor
        (D("49.99"), 2),
        (D("50"), 3),
        (D("75"), 4),
        (D("99.99"), 4),
        (D("100"), 5),
        (D("350"), 5),
    ],
)
def test_nivel_roi(roi: D, nivel: int) -> None:
    assert nivel_roi(roi) == nivel


# --- Tiempo de recuperación (FIN-02) ----------------------------------------------------------


def test_meses_de_recuperacion() -> None:
    assert meses_recuperacion(D("120000"), D("10000")) == D("12")
    assert meses_recuperacion(D("100000"), D("30000")) == D("100000") / D("30000")


@pytest.mark.parametrize("flujo", [D("0"), D("-500")])
def test_sin_flujo_positivo_no_se_recupera(flujo: D) -> None:
    assert meses_recuperacion(D("100000"), flujo) is None


@pytest.mark.parametrize(
    ("meses", "nivel"),
    [
        (None, 1),  # nunca se recupera
        (D("48"), 1),
        (D("36.01"), 1),
        (D("36"), 2),  # el límite pertenece al nivel mejor
        (D("24"), 3),
        (D("12.5"), 3),
        (D("12"), 4),
        (D("6"), 4),  # "< 6 meses" es estricto
        (D("5.99"), 5),
        (D("1"), 5),
    ],
)
def test_nivel_recuperacion(meses: D | None, nivel: int) -> None:
    assert nivel_recuperacion(meses) == nivel


# --- Propuesta combinada ----------------------------------------------------------------------


def test_propuesta_completa() -> None:
    p = proponer(inversion=D("120000"), ingresos=D("300000"), flujo_mensual=D("10000"))

    assert p.roi == D("150")
    assert p.nivel_roi == 5
    assert p.meses_recuperacion == D("12")
    assert p.nivel_recuperacion == 4
    assert p.faltantes == []


def test_propuesta_sin_datos_indica_lo_que_falta() -> None:
    p = proponer(inversion=None, ingresos=D("1000"), flujo_mensual=None)

    assert p.roi is None and p.nivel_roi is None
    assert p.meses_recuperacion is None and p.nivel_recuperacion is None
    assert p.faltantes == ["inversion_estimada", "flujo_mensual_neto"]


def test_propuesta_parcial() -> None:
    p = proponer(inversion=D("50000"), ingresos=None, flujo_mensual=D("-100"))

    assert p.nivel_roi is None
    assert p.faltantes == ["ingresos_esperados"]
    # Con flujo negativo la inversión no se recupera: nivel 1.
    assert p.meses_recuperacion is None
    assert p.nivel_recuperacion == 1


@pytest.mark.parametrize(
    ("campo", "valores"),
    [
        ("inversion", {"inversion": D("0"), "ingresos": D("1"), "flujo_mensual": D("1")}),
        ("ingresos", {"inversion": D("10"), "ingresos": D("-1"), "flujo_mensual": D("1")}),
    ],
)
def test_propuesta_rechaza_valores_incoherentes(campo: str, valores: dict[str, D]) -> None:
    with pytest.raises(ValueError, match=campo[:7]):
        proponer(**valores)
