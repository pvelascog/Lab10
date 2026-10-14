"""T057 – Propiedades del motor de decisión con Hypothesis (FR-016)."""

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.dominio.motor_decision import ORDEN, Resultado, Umbrales, decidir, score_total

DIMS = ("MER", "COM", "FIN", "TEC", "CMP", "ECO")
IGUALES = {d: Decimal(1) / 6 for d in DIMS}
puntaje = st.floats(min_value=1.0, max_value=5.0, allow_nan=False)
puntajes = st.lists(puntaje, min_size=6, max_size=6).map(lambda v: dict(zip(DIMS, v, strict=True)))
pesos = st.lists(st.integers(min_value=1, max_value=100), min_size=6, max_size=6).map(
    lambda v: {d: Decimal(p) / sum(v) for d, p in zip(DIMS, v, strict=True)}
)


def resultado(d: dict[str, float], w: dict[str, Decimal] = IGUALES) -> Resultado:
    return decidir(score_total(d, w), d, Umbrales()).resultado


@given(puntajes)
def test_nunca_go_con_una_dimension_debil(d: dict[str, float]) -> None:
    if min(d.values()) < 3.0:
        assert resultado(d) is not Resultado.GO


@given(puntajes)
def test_siempre_no_go_con_una_dimension_critica(d: dict[str, float]) -> None:
    if min(d.values()) < 2.0:
        assert resultado(d) is Resultado.NO_GO


@given(puntajes)
def test_go_solo_si_score_alto_y_todas_aceptables(d: dict[str, float]) -> None:
    if resultado(d) is Resultado.GO:
        assert score_total(d, IGUALES) >= 4.0
        assert min(d.values()) >= 3.0


@settings(max_examples=300)
@given(puntajes, st.sampled_from(DIMS), st.floats(min_value=0.0, max_value=4.0))
def test_bajar_un_puntaje_nunca_mejora_el_resultado(
    d: dict[str, float], dimension: str, baja: float
) -> None:
    peor = {**d, dimension: max(1.0, d[dimension] - baja)}
    assert ORDEN[resultado(peor)] <= ORDEN[resultado(d)]


@given(puntajes)
def test_pesos_iguales_equivalen_al_promedio_simple(d: dict[str, float]) -> None:
    assert abs(score_total(d, IGUALES) - sum(d.values()) / 6) < 1e-9


@given(puntajes, pesos)
def test_el_score_queda_entre_el_minimo_y_el_maximo(
    d: dict[str, float], w: dict[str, Decimal]
) -> None:
    s = score_total(d, w)
    assert min(d.values()) - 1e-9 <= s <= max(d.values()) + 1e-9


@given(puntajes, pesos)
def test_la_decision_es_determinista(d: dict[str, float], w: dict[str, Decimal]) -> None:
    s = score_total(d, w)
    assert decidir(s, d, Umbrales()) == decidir(s, d, Umbrales())
