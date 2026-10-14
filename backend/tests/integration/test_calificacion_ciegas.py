"""T047 – HU3: calificación a ciegas (FR-010b)."""

from httpx import AsyncClient

from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import (
    CrearUsuario,
    calificar,
    calificar_dimension,
    preparar_evaluacion,
)


async def _mer(c: AsyncClient, e: str) -> dict:
    r = await c.get(f"/api/v1/evaluaciones/{e}")
    assert r.status_code == 200, r.text
    return next(d for d in r.json()["dimensiones"] if d["codigo"] == "MER")


async def test_no_ve_calificaciones_ajenas_antes_de_enviar(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=2)  # A envía
    await calificar(b, e, "MER-01", 5)  # B tiene un borrador

    mer_b = await _mer(b, e)

    assert mer_b["ver_calificaciones"] is False
    for criterio in mer_b["criterios"]:
        assert criterio["calificaciones"] is None
        assert criterio["promedio"] is None
        assert criterio["divergencia"] is None
    assert mer_b["criterios"][0]["mi_calificacion"]["nivel"] == 5


async def test_despues_de_enviar_ve_las_calificaciones_enviadas(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=2)
    await calificar_dimension(b, e, "MER", nivel=4)

    mer_a = await _mer(a, e)

    assert mer_a["ver_calificaciones"] is True
    mer01 = mer_a["criterios"][0]
    assert sorted(c["nivel"] for c in mer01["calificaciones"]) == [2, 4]
    assert mer01["promedio"] == 3.0
    assert mer01["divergencia"] is True


async def test_los_borradores_ajenos_nunca_se_muestran(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="b@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a, b]})
    await calificar_dimension(a, e, "MER", nivel=2)
    await calificar(b, e, "MER-01", 5)  # borrador de B

    mer_a = await _mer(a, e)

    assert [c["nivel"] for c in mer_a["criterios"][0]["calificaciones"]] == [2]


async def test_pm_ve_las_enviadas_salvo_en_su_propia_dimension_pendiente(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a]})  # el PM evalúa el resto
    await calificar_dimension(a, e, "MER", nivel=3)

    dimensiones = {
        d["codigo"]: d for d in (await pm.get(f"/api/v1/evaluaciones/{e}")).json()["dimensiones"]
    }

    assert dimensiones["MER"]["ver_calificaciones"] is True  # no la evalúa: supervisa
    assert dimensiones["FIN"]["ver_calificaciones"] is False  # la evalúa y no la envió


async def test_un_miembro_autor_no_ve_calificaciones_durante_la_evaluacion(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="a@nepxa.test")
    _, e = await preparar_evaluacion(pm, {"MER": [a]})
    await calificar_dimension(a, e, "MER")
    lider_tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="t@nepxa.test")

    # No asignado y sin rol de portafolio: ni siquiera ve la evaluación.
    assert (await lider_tec.get(f"/api/v1/evaluaciones/{e}")).status_code == 404
