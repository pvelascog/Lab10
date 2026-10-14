"""T058 – HU4: consolidación, resultado recomendado y resumen ejecutivo (FR-011 a FR-017)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modelos.auditoria import Auditoria
from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import (
    CRITERIOS,
    CrearUsuario,
    calificar,
    calificar_dimension,
    preparar_evaluacion,
)


async def _consolidar(c: AsyncClient, iniciativa_id: str):
    return await c.post(
        f"/api/v1/iniciativas/{iniciativa_id}/transiciones", json={"hacia": "CONSOLIDADA"}
    )


async def _evaluar_todo(pm: AsyncClient, e: str, niveles: dict[str, int] | None = None) -> None:
    for d in CRITERIOS:
        await calificar_dimension(pm, e, d, nivel=(niveles or {}).get(d, 4))


# --- Precondiciones ---------------------------------------------------------------------------


async def test_no_consolida_con_pendientes(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i, e = await preparar_evaluacion(pm)
    await calificar_dimension(pm, e, "MER")

    r = await _consolidar(pm, i)

    assert r.status_code == 422
    assert set(r.json()["campos"]) == {c for d in CRITERIOS if d != "MER" for c in CRITERIOS[d]}
    assert (await pm.get(f"/api/v1/evaluaciones/{e}/resultado")).status_code == 404


async def test_no_consolida_con_divergencias_sin_comentar_aunque_el_pm_no_las_vea(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    # El PM también evalúa Mercado y nunca envía: aun así la divergencia de A y B bloquea.
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"MER": [a, b, pm]})
    await calificar_dimension(a, e, "MER", nivel=5)
    await calificar_dimension(b, e, "MER", nivel=2)
    for d in ("COM", "FIN", "TEC", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)

    r = await _consolidar(pm, i)

    assert r.status_code == 422
    assert set(r.json()["campos"]) == set(CRITERIOS["MER"])


async def test_solo_el_pm_consolida(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"TEC": [tec]})
    await calificar_dimension(tec, e, "TEC")
    for d in ("MER", "COM", "FIN", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)

    assert (await _consolidar(tec, i)).status_code == 403


# --- Consolidación correcta -------------------------------------------------------------------


async def test_consolida_y_calcula_el_resultado(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=4)
    await calificar_dimension(b, e, "MER", nivel=5)  # promedio por criterio 4.5
    for d in ("COM", "FIN", "TEC", "CMP", "ECO"):
        await calificar_dimension(pm, e, d, nivel=4)

    r = await _consolidar(pm, i)

    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "CONSOLIDADA"
    res = (await pm.get(f"/api/v1/evaluaciones/{e}/resultado")).json()
    assert list(res["puntajes_dimension"]) == list(CRITERIOS)  # orden del marco
    assert list(res["puntajes_criterio"])[:2] == ["MER-01", "MER-02"]
    assert res["puntajes_criterio"]["MER-01"] == 4.5
    assert res["puntajes_dimension"]["MER"] == 4.5
    # Comercial: 5 criterios en 4 y Recurrencia (COM-04) en 5 → 25/6.
    assert res["puntajes_dimension"]["COM"] == pytest.approx(25 / 6)
    assert res["puntajes_dimension"]["FIN"] == 4.0
    assert res["score_total"] == pytest.approx((4.5 + 25 / 6 + 4 * 4) / 6)
    assert res["resultado"] == "GO"
    assert res["regla"] == "R4"
    assert res["regla_aplicada"] == "R4: score ≥ 4.0 y todas las dimensiones ≥ 3.0"
    assert res["dimensiones_implicadas"] == []
    assert res["version_marco"] == "3.0"
    assert sum(res["pesos"].values()) == pytest.approx(1)
    assert res["umbrales"]["critico"] == 2.0
    estado = (await pm.get(f"/api/v1/evaluaciones/{e}")).json()["estado"]
    assert estado == "CONSOLIDADA"
    assert (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "CONSOLIDAR"))
    ).scalar_one().despues["resultado"] == "GO"


async def test_no_go_por_dimension_critica(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i, e = await preparar_evaluacion(pm)
    await _evaluar_todo(pm, e, {"FIN": 1})

    await _consolidar(pm, i)
    res = (await pm.get(f"/api/v1/evaluaciones/{e}/resultado")).json()

    assert res["resultado"] == "NO_GO"
    assert res["regla_aplicada"] == "R1: dimensión FIN = 1.00 < 2.0"
    assert res["dimensiones_implicadas"] == ["FIN"]


async def test_solo_cuentan_las_calificaciones_enviadas(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=3)
    await calificar(b, e, "MER-01", 5)  # borrador de B: no cuenta
    for d in ("COM", "FIN", "TEC", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)

    assert (await _consolidar(pm, i)).status_code == 200
    res = (await pm.get(f"/api/v1/evaluaciones/{e}/resultado")).json()
    assert res["puntajes_criterio"]["MER-01"] == 3.0


# --- Después de consolidar --------------------------------------------------------------------


async def test_el_resultado_queda_fijo(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i, e = await preparar_evaluacion(pm)
    await _evaluar_todo(pm, e)
    await _consolidar(pm, i)

    assert (await calificar(pm, e, "MER-01", 1)).status_code == 409
    assert (await _consolidar(pm, i)).status_code == 409


async def test_al_consolidar_todas_las_calificaciones_quedan_visibles(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"TEC": [tec]})
    await calificar_dimension(tec, e, "TEC")
    for d in ("MER", "COM", "FIN", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)
    antes = (await tec.get(f"/api/v1/evaluaciones/{e}")).json()["dimensiones"][0]
    assert antes["ver_calificaciones"] is False  # Mercado no es suya

    await _consolidar(pm, i)

    despues = (await tec.get(f"/api/v1/evaluaciones/{e}")).json()["dimensiones"][0]
    assert despues["ver_calificaciones"] is True
    assert (await tec.get(f"/api/v1/evaluaciones/{e}/resultado")).status_code == 200


async def test_borrador_automatico_del_resumen(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i, e = await preparar_evaluacion(pm)
    await _evaluar_todo(pm, e, {"MER": 5, "TEC": 2, "ECO": 3})

    await _consolidar(pm, i)
    res = (await pm.get(f"/api/v1/evaluaciones/{e}/resultado")).json()

    assert any(f.startswith("Mercado") for f in res["fortalezas"])
    assert any(d.startswith("Técnica") for d in res["debilidades"])
    assert not any(d.startswith("Ecosistema") for d in res["debilidades"])  # 3.0 no es débil
    assert any(r.startswith("TEC-01") for r in res["riesgos"])  # criterios con puntaje ≤ 2
    assert res["supuestos_criticos"] == ["Los clientes prefieren la autogestión"]
    assert res["borrador_ia"] is False


async def test_el_pm_edita_el_resumen(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    i, e = await preparar_evaluacion(pm, {"TEC": [tec]})
    await calificar_dimension(tec, e, "TEC")
    for d in ("MER", "COM", "FIN", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)
    await _consolidar(pm, i)
    cambios = {"fortalezas": ["Demanda validada", "  "], "riesgos": ["Dependencia de Nexopus"]}

    r = await pm.patch(f"/api/v1/evaluaciones/{e}/resultado", json=cambios)

    assert r.status_code == 200, r.text
    assert r.json()["fortalezas"] == ["Demanda validada"]
    assert r.json()["riesgos"] == ["Dependencia de Nexopus"]
    assert r.json()["resultado"] == "GO"  # los puntajes y el resultado no se editan
    no_pm = await tec.patch(f"/api/v1/evaluaciones/{e}/resultado", json=cambios)
    assert no_pm.status_code == 403
    invalido = await pm.patch(f"/api/v1/evaluaciones/{e}/resultado", json={"resultado": "NO_GO"})
    assert invalido.status_code == 400
    assert (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "EDITAR_RESUMEN"))
    ).scalar_one()


# --- Backlog (FR-004) -------------------------------------------------------------------------


async def test_backlog_muestra_y_filtra_por_resultado(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i_go, e_go = await preparar_evaluacion(pm)
    await _evaluar_todo(pm, e_go)
    await _consolidar(pm, i_go)
    i_nogo, e_nogo = await preparar_evaluacion(pm)
    await _evaluar_todo(pm, e_nogo, {"FIN": 1})
    await _consolidar(pm, i_nogo)
    i_abierta, _ = await preparar_evaluacion(pm)

    backlog = {x["id"]: x["resultado"] for x in (await pm.get("/api/v1/iniciativas")).json()}
    solo_go = (await pm.get("/api/v1/iniciativas", params={"resultado": "GO"})).json()

    assert backlog == {i_go: "GO", i_nogo: "NO_GO", i_abierta: None}
    assert [x["id"] for x in solo_go] == [i_go]
