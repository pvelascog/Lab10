"""T046 – HU3: inicio de la evaluación y calificación de criterios (FR-005 a FR-010, FR-025)."""

import pytest
from sqlalchemy import select

from app.modelos.auditoria import Auditoria
from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import (
    CRITERIOS,
    FICHA,
    IDEA,
    CrearUsuario,
    calificar,
    calificar_dimension,
    id_de,
    preparar_evaluacion,
)

# --- Paso a EN_EVALUACION ---------------------------------------------------------------------


async def test_iniciar_evaluacion_exige_un_evaluador_por_dimension(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    uid = await id_de(pm)
    r = await pm.post(
        "/api/v1/iniciativas",
        json={
            **IDEA,
            "asignaciones": [
                {"dimension": "MER", "usuario_id": uid},
                {"dimension": "TEC", "usuario_id": uid},
            ],
        },
    )
    i = r.json()["id"]
    await pm.patch(f"/api/v1/iniciativas/{i}", json={**FICHA, "pm_id": uid})
    await pm.post(f"/api/v1/iniciativas/{i}/transiciones", json={"hacia": "ESTRUCTURADA"})

    r = await pm.post(f"/api/v1/iniciativas/{i}/transiciones", json={"hacia": "EN_EVALUACION"})

    assert r.status_code == 422
    assert set(r.json()["campos"]) == {"COM", "FIN", "CMP", "ECO"}


async def test_iniciar_evaluacion_crea_la_evaluacion_con_la_version_vigente(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)

    iniciativa_id, evaluacion_id = await preparar_evaluacion(pm)

    detalle = (await pm.get(f"/api/v1/iniciativas/{iniciativa_id}")).json()
    assert detalle["estado"] == "EN_EVALUACION"
    assert detalle["evaluacion_actual_id"] == evaluacion_id
    e = (await pm.get(f"/api/v1/evaluaciones/{evaluacion_id}")).json()
    assert e["numero"] == 1
    assert e["estado"] == "ABIERTA"
    assert e["version_marco"] == "3.0"
    assert [d["codigo"] for d in e["dimensiones"]] == list(CRITERIOS)
    assert sum(len(d["criterios"]) for d in e["dimensiones"]) == 28


async def test_la_ficha_no_se_edita_durante_la_evaluacion(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    iniciativa_id, _ = await preparar_evaluacion(pm)

    r = await pm.patch(f"/api/v1/iniciativas/{iniciativa_id}", json={"segmento": "Otro"})

    assert r.status_code == 409


# --- Calificar --------------------------------------------------------------------------------


async def test_evaluador_asignado_califica_un_criterio(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    r = await calificar(pm, e, "MER-01", 4, "Afecta a 3 áreas")

    assert r.status_code == 200, r.text
    criterio = next(
        c for d in r.json()["dimensiones"] for c in d["criterios"] if c["codigo"] == "MER-01"
    )
    assert criterio["mi_calificacion"] == {
        "nivel": 4,
        "justificacion": "Afecta a 3 áreas",
        "fuente": None,
        "origen": "HUMANA",
    }


async def test_volver_a_calificar_reemplaza_el_borrador(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    await calificar(pm, e, "MER-01", 2)
    r = await calificar(pm, e, "MER-01", 5, "Corregido")

    criterio = next(
        c for d in r.json()["dimensiones"] for c in d["criterios"] if c["codigo"] == "MER-01"
    )
    assert criterio["mi_calificacion"]["nivel"] == 5


@pytest.mark.parametrize("justificacion", ["", "   "])
async def test_calificacion_sin_justificacion_se_rechaza(
    usuario_con_sesion: CrearUsuario, justificacion: str
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    r = await calificar(pm, e, "MER-01", 3, justificacion)

    assert r.status_code == 400
    assert "justificacion" in r.json()["campos"]


@pytest.mark.parametrize("nivel", [0, 6])
async def test_nivel_fuera_de_rango_se_rechaza(
    usuario_con_sesion: CrearUsuario, nivel: int
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    assert (await calificar(pm, e, "MER-01", nivel)).status_code == 400


@pytest.mark.parametrize(("nivel", "estado"), [(1, 200), (2, 400), (3, 200), (4, 400), (5, 200)])
async def test_recurrencia_solo_admite_1_3_y_5(
    usuario_con_sesion: CrearUsuario, nivel: int, estado: int
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    r = await calificar(pm, e, "COM-04", nivel)

    assert r.status_code == estado
    if estado == 400:
        assert "nivel" in r.json()["campos"]


async def test_evaluador_no_asignado_a_la_dimension_recibe_403(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"TEC": [tec]})

    assert (await calificar(tec, e, "TEC-01", 3)).status_code == 200
    assert (await calificar(tec, e, "MER-01", 3)).status_code == 403
    # El PM no está asignado a Técnica: tampoco puede calificarla.
    assert (await calificar(pm, e, "TEC-01", 3)).status_code == 403


async def test_criterio_inexistente_devuelve_404(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    assert (await calificar(pm, e, "XYZ-99", 3)).status_code == 404


async def test_evaluacion_no_visible_devuelve_404(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    ajeno = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="ajeno@nepxa.test")
    _, e = await preparar_evaluacion(pm)

    assert (await ajeno.get(f"/api/v1/evaluaciones/{e}")).status_code == 404
    assert (await calificar(ajeno, e, "MER-01", 3)).status_code == 404


async def test_la_calificacion_queda_en_auditoria(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)

    await calificar(pm, e, "MER-02", 5, "Reclamos diarios")

    registro = (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "CALIFICAR"))
    ).scalar_one()
    assert registro.despues == {
        "criterio": "MER-02",
        "nivel": 5,
        "justificacion": "Reclamos diarios",
        "origen": "HUMANA",
    }


# --- Propuesta calculada de FIN-02 / FIN-03 ---------------------------------------------------


async def test_confirmar_el_nivel_calculado(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)  # ficha: ROI 150 % → 5; recuperación 12 meses → 4

    ok = await pm.put(
        f"/api/v1/evaluaciones/{e}/calificaciones/FIN-03",
        json={"nivel": 5, "justificacion": "Según el cálculo de la ficha", "usa_calculo": True},
    )
    distinto = await pm.put(
        f"/api/v1/evaluaciones/{e}/calificaciones/FIN-02",
        json={"nivel": 2, "justificacion": "No coincide", "usa_calculo": True},
    )
    no_calculable = await pm.put(
        f"/api/v1/evaluaciones/{e}/calificaciones/FIN-01",
        json={"nivel": 3, "justificacion": "x", "usa_calculo": True},
    )

    assert ok.status_code == 200
    fin03 = next(
        c for d in ok.json()["dimensiones"] for c in d["criterios"] if c["codigo"] == "FIN-03"
    )
    assert fin03["mi_calificacion"]["origen"] == "CALCULADA_CONFIRMADA"
    assert fin03["propuesta_calculada"] == 5
    assert distinto.status_code == 400
    assert no_calculable.status_code == 400


# --- Envío por dimensión y avance -------------------------------------------------------------


async def test_enviar_dimension_incompleta_lista_los_criterios_faltantes(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)
    await calificar(pm, e, "FIN-01", 3)

    r = await pm.post(f"/api/v1/evaluaciones/{e}/dimensiones/FIN/enviar")

    assert r.status_code == 422
    assert set(r.json()["campos"]) == {"FIN-02", "FIN-03", "FIN-04"}


async def test_avance_por_dimension_y_evaluador(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    com1 = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com1@nepxa.test")
    com2 = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com2@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [com1, com2]})

    await calificar_dimension(com1, e, "MER")
    await calificar(com2, e, "MER-01", 4)

    mer = (await pm.get(f"/api/v1/evaluaciones/{e}")).json()["dimensiones"][0]
    avance = {
        ev["usuario"]["nombre"]: (ev["calificados"], ev["enviado"]) for ev in mer["evaluadores"]
    }
    assert avance == {"com1": (5, True), "com2": (1, False)}
    assert (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "ENVIAR_DIMENSION"))
    ).scalar_one()


async def test_no_se_edita_ni_reenvia_una_dimension_enviada(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)
    await calificar_dimension(pm, e, "ECO")

    assert (await calificar(pm, e, "ECO-01", 1)).status_code == 409
    assert (await pm.post(f"/api/v1/evaluaciones/{e}/dimensiones/ECO/enviar")).status_code == 409


# --- Reasignación durante la evaluación (caso límite) -----------------------------------------


async def test_pm_reasigna_a_un_evaluador_que_no_califico(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec1 = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec1@nepxa.test")
    tec2 = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec2@nepxa.test")
    iniciativa_id, e = await preparar_evaluacion(pm, {"TEC": [tec1]})
    await calificar(tec1, e, "TEC-01", 2)  # borrador sin enviar

    asignaciones = [
        {"dimension": d, "usuario_id": await id_de(pm)} for d in CRITERIOS if d != "TEC"
    ]
    r = await pm.put(
        f"/api/v1/iniciativas/{iniciativa_id}/asignaciones",
        json={
            "asignaciones": [*asignaciones, {"dimension": "TEC", "usuario_id": await id_de(tec2)}]
        },
    )

    assert r.status_code == 200, r.text
    assert (await calificar(tec1, e, "TEC-02", 2)).status_code in (403, 404)
    assert (await calificar(tec2, e, "TEC-01", 3)).status_code == 200


async def test_no_se_quita_a_quien_ya_envio(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    iniciativa_id, e = await preparar_evaluacion(pm, {"TEC": [tec]})
    await calificar_dimension(tec, e, "TEC")

    asignaciones = [{"dimension": d, "usuario_id": await id_de(pm)} for d in CRITERIOS]
    r = await pm.put(
        f"/api/v1/iniciativas/{iniciativa_id}/asignaciones", json={"asignaciones": asignaciones}
    )

    assert r.status_code == 409
