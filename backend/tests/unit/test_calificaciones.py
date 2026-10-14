"""T045 – Promedio por criterio, divergencia y normalización de Recurrencia (FR-008, FR-010a)."""

import pytest

from app.dominio.motor_decision import divergencia, normalizar_recurrencia, puntaje_criterio


@pytest.mark.parametrize(
    ("calificaciones", "esperado"),
    [([4], 4.0), ([3, 4], 3.5), ([1, 2, 4], 7 / 3), ([5, 5, 5, 5], 5.0)],
)
def test_puntaje_del_criterio_es_el_promedio(calificaciones: list[int], esperado: float) -> None:
    assert puntaje_criterio(calificaciones) == pytest.approx(esperado)


def test_puntaje_sin_calificaciones_es_error() -> None:
    with pytest.raises(ValueError, match="calificación"):
        puntaje_criterio([])


@pytest.mark.parametrize(
    ("calificaciones", "hay"),
    [
        ([4], False),  # una sola calificación no diverge
        ([3, 4], False),
        ([2, 4], True),  # diferencia de 2 puntos: divergencia
        ([1, 3, 2], True),
        ([5, 5, 4, 4], False),
        ([1, 5], True),
    ],
)
def test_divergencia_con_umbral_de_dos_puntos(calificaciones: list[int], hay: bool) -> None:
    assert divergencia(calificaciones) is hay


def test_umbral_de_divergencia_configurable() -> None:
    assert divergencia([2, 4], umbral=3) is False
    assert divergencia([2, 3], umbral=1) is True


@pytest.mark.parametrize(("original", "normalizado"), [(1, 1), (2, 3), (3, 5)])
def test_normalizacion_de_recurrencia(original: int, normalizado: int) -> None:
    assert normalizar_recurrencia(original) == normalizado


@pytest.mark.parametrize("fuera_de_rango", [0, 4, 5])
def test_recurrencia_fuera_de_su_escala(fuera_de_rango: int) -> None:
    with pytest.raises(ValueError):
        normalizar_recurrencia(fuera_de_rango)
