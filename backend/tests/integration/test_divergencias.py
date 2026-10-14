"""T048 – HU3: divergencias entre evaluadores (FR-010a) y pendientes para consolidar."""

from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import (
    CRITERIOS,
    CrearUsuario,
    calificar,
    calificar_dimension,
    preparar_evaluacion,
)


async def test_divergencias_y_pendientes(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=4)
    for criterio, nivel in zip(CRITERIOS["MER"], [2, 3, 4, 5, 2], strict=True):
        await calificar(b, e, criterio, nivel)  # MER-01 y MER-05 difieren en 2
    await pm.post(f"/api/v1/evaluaciones/{e}/dimensiones/MER/enviar")  # no asignado: no cuenta
    await b.post(f"/api/v1/evaluaciones/{e}/dimensiones/MER/enviar")

    r = await pm.get(f"/api/v1/evaluaciones/{e}/divergencias")

    assert r.status_code == 200
    assert [(d["criterio"], sorted(d["niveles"])) for d in r.json()] == [
        ("MER-01", [2, 4]),
        ("MER-05", [2, 4]),
    ]
    pendientes = (await pm.get(f"/api/v1/evaluaciones/{e}")).json()["pendientes"]
    assert pendientes["MER-01"] == "Divergencia sin comentar"
    # Las demás dimensiones (del PM) siguen sin calificaciones enviadas.
    assert pendientes["FIN-01"] == "Sin calificaciones enviadas"
    assert "MER-02" not in pendientes


async def test_comentar_resuelve_el_pendiente(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=5)
    await calificar_dimension(b, e, "MER", nivel=3)
    for d in ("COM", "FIN", "TEC", "CMP", "ECO"):
        await calificar_dimension(pm, e, d)

    antes = (await pm.get(f"/api/v1/evaluaciones/{e}")).json()["pendientes"]
    assert set(antes) == set(CRITERIOS["MER"])  # las 5 divergen (5 vs 3)

    for criterio in CRITERIOS["MER"]:
        autor = a if criterio != "MER-05" else pm  # evaluador asignado o PM
        r = await autor.post(
            f"/api/v1/evaluaciones/{e}/divergencias/{criterio}/comentarios",
            json={"texto": "A consideró ventas en curso; B, solo conversaciones."},
        )
        assert r.status_code == 201, r.text

    evaluacion = (await pm.get(f"/api/v1/evaluaciones/{e}")).json()
    assert evaluacion["pendientes"] == {}
    mer01 = evaluacion["dimensiones"][0]["criterios"][0]
    assert mer01["comentarios"][0]["texto"].startswith("A consideró")
    assert mer01["comentarios"][0]["autor"]["nombre"] == "a"


async def test_no_se_comenta_un_criterio_sin_divergencia(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    _, e = await preparar_evaluacion(pm)
    await calificar_dimension(pm, e, "MER")

    r = await pm.post(
        f"/api/v1/evaluaciones/{e}/divergencias/MER-01/comentarios", json={"texto": "x"}
    )

    assert r.status_code == 422


async def test_solo_evaluadores_de_la_dimension_o_pm_comentan(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b], "TEC": [tec]})
    await calificar_dimension(a, e, "MER", nivel=5)
    await calificar_dimension(b, e, "MER", nivel=1)

    r = await tec.post(
        f"/api/v1/evaluaciones/{e}/divergencias/MER-01/comentarios", json={"texto": "Opino"}
    )

    assert r.status_code == 403


async def test_comentario_vacio_se_rechaza(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, pm]})
    await calificar_dimension(a, e, "MER", nivel=5)
    await calificar_dimension(pm, e, "MER", nivel=1)

    r = await pm.post(
        f"/api/v1/evaluaciones/{e}/divergencias/MER-01/comentarios", json={"texto": "  "}
    )

    assert r.status_code == 400
