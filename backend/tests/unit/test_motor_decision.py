"""T056 – Motor de decisión: ejemplos de HU4 y valores límite (FR-011 a FR-016)."""

from decimal import Decimal

import pytest

from app.dominio.motor_decision import (
    Resultado,
    Umbrales,
    decidir,
    puntaje_dimension,
    score_total,
)

DIMS = ("MER", "COM", "FIN", "TEC", "CMP", "ECO")
IGUALES = {d: Decimal(1) / 6 for d in DIMS}


def dims(*valores: float) -> dict[str, float]:
    return dict(zip(DIMS, valores, strict=True))


def evaluar(*valores: float) -> tuple[float, Resultado, str, list[str]]:
    d = dims(*valores)
    score = score_total(d, IGUALES)
    decision = decidir(score, d, Umbrales())
    return score, decision.resultado, decision.regla, decision.dimensiones_implicadas


# --- Puntajes ---------------------------------------------------------------------------------


def test_puntaje_de_dimension_es_el_promedio_simple_de_sus_criterios() -> None:
    assert puntaje_dimension([4.0, 3.5, 5.0, 3.5]) == 4.0


def test_puntaje_de_dimension_sin_criterios_es_error() -> None:
    with pytest.raises(ValueError):
        puntaje_dimension([])


def test_score_ponderado() -> None:
    d = {"A": 4.0, "B": 2.0}
    assert score_total(d, {"A": Decimal("0.75"), "B": Decimal("0.25")}) == pytest.approx(3.5)


def test_score_con_pesos_iguales_es_el_promedio() -> None:
    assert score_total(dims(4.2, 4.0, 3.8, 4.5, 4.1, 4.4), IGUALES) == pytest.approx(25 / 6)


def test_score_exige_peso_para_cada_dimension() -> None:
    with pytest.raises(ValueError, match="peso"):
        score_total({"A": 4.0, "B": 3.0}, {"A": Decimal(1)})


# --- Ejemplos de la especificación (HU4, escenarios 2 a 5) ------------------------------------


def test_ejemplo_go() -> None:
    score, resultado, regla, implicadas = evaluar(4.2, 4.0, 3.8, 4.5, 4.1, 4.4)

    assert score == pytest.approx(4.1667, abs=1e-4)
    assert resultado is Resultado.GO
    assert regla == "R4"
    assert implicadas == []


def test_ejemplo_iterar_por_dimension_debil() -> None:
    score, resultado, regla, implicadas = evaluar(2.8, 4.6, 4.6, 4.6, 4.6, 4.6)

    assert score == pytest.approx(4.3)
    assert resultado is Resultado.ITERAR
    assert regla == "R3"
    assert implicadas == ["MER"]


def test_ejemplo_validar_por_dos_dimensiones_bajo_2_5() -> None:
    score, resultado, regla, implicadas = evaluar(2.3, 2.4, 4.0, 4.0, 4.0, 3.7)

    assert score == pytest.approx(3.4)
    assert resultado is Resultado.VALIDAR
    assert regla == "R2"
    assert implicadas == ["MER", "COM"]


def test_ejemplo_no_go_por_dimension_critica() -> None:
    _, resultado, regla, implicadas = evaluar(5, 5, 1.8, 5, 5, 5)

    assert resultado is Resultado.NO_GO
    assert regla == "R1"
    assert implicadas == ["FIN"]


# --- Reglas por score -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("valores", "esperado"),
    [
        ((1.9,) * 6, Resultado.NO_GO),  # score < 2.0
        ((2.9,) * 6, Resultado.VALIDAR),  # score < 3.0 (todas ≥ 2.5)
        ((3.9,) * 6, Resultado.ITERAR),  # score < 4.0 (todas ≥ 3.0)
        ((4.0,) * 6, Resultado.GO),
    ],
)
def test_reglas_por_score(valores: tuple[float, ...], esperado: Resultado) -> None:
    assert evaluar(*valores)[1] is esperado


# --- Valores límite exactos (intervalos semiabiertos, research.md D9) -------------------------


def test_dimension_en_2_0_no_es_critica() -> None:
    # 2.0 no es < 2.0; pero dos dimensiones < 2.5 → VALIDAR.
    assert evaluar(2.0, 2.0, 5, 5, 5, 5)[1] is Resultado.VALIDAR
    assert evaluar(2.0, 5, 5, 5, 5, 5)[1] is Resultado.ITERAR


def test_dimension_en_2_5_no_cuenta_para_validar() -> None:
    assert evaluar(2.5, 2.5, 5, 5, 5, 5)[1] is Resultado.ITERAR
    assert evaluar(2.49, 2.5, 5, 5, 5, 5)[1] is Resultado.ITERAR  # solo una < 2.5
    assert evaluar(2.49, 2.49, 5, 5, 5, 5)[1] is Resultado.VALIDAR


def test_dimension_en_3_0_no_es_debil() -> None:
    assert evaluar(3.0, 5, 5, 5, 5, 5)[1] is Resultado.GO
    assert evaluar(2.99, 5, 5, 5, 5, 5)[1] is Resultado.ITERAR


def test_score_en_los_limites() -> None:
    assert evaluar(4.0, 4.0, 4.0, 4.0, 4.0, 4.0)[1] is Resultado.GO
    assert evaluar(3.0, 3.0, 3.0, 3.0, 3.0, 3.0)[1] is Resultado.ITERAR
    assert evaluar(2.0, 2.0, 2.0, 2.0, 2.0, 2.0)[1] is Resultado.VALIDAR


def test_un_score_apenas_bajo_4_es_iterar_aunque_se_muestre_4_00() -> None:
    assert evaluar(3.999, 3.999, 3.999, 3.999, 3.999, 3.999)[1] is Resultado.ITERAR


# --- Regla más restrictiva (C1) ---------------------------------------------------------------


def test_prevalece_la_regla_mas_restrictiva() -> None:
    # Score alto (4.47) pero una dimensión crítica: NO-GO, no GO.
    score, resultado, _, _ = evaluar(1.8, 5, 5, 5, 5, 5)
    assert score > 4
    assert resultado is Resultado.NO_GO


def test_la_descripcion_explica_la_regla() -> None:
    d = dims(5, 5, 1.75, 5, 5, 5)
    decision = decidir(score_total(d, IGUALES), d, Umbrales())

    assert decision.descripcion == "R1: dimensión FIN = 1.75 < 2.0"


def test_descripciones_de_las_demas_reglas() -> None:
    casos = {
        (2.3, 2.4, 4, 4, 4, 3.7): "R2: dos o más dimensiones < 2.5 (MER = 2.30, COM = 2.40)",
        (2.8, 4.6, 4.6, 4.6, 4.6, 4.6): "R3: dimensión MER = 2.80 < 3.0",
        (3.9,) * 6: "R3: score 3.90 < 4.0",
        (4.0,) * 6: "R4: score ≥ 4.0 y todas las dimensiones ≥ 3.0",
        (1.9,) * 6: "R1: score 1.90 < 2.0",
    }
    for valores, esperada in casos.items():
        d = dims(*valores)
        assert decidir(score_total(d, IGUALES), d, Umbrales()).descripcion == esperada


def test_umbrales_configurables() -> None:
    estrictos = Umbrales(score_go=4.5)
    d = dims(4.2, 4.0, 3.8, 4.5, 4.1, 4.4)

    assert decidir(score_total(d, IGUALES), d, estrictos).resultado is Resultado.ITERAR
