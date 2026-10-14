"""T040 – HU2: estructurar la ficha y pasar a ESTRUCTURADA (FR-002, FR-003, FR-009, FR-010)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modelos.auditoria import Auditoria
from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import IDEA, CrearUsuario, id_de

FICHA = {
    "problema": "Los clientes no saben en qué estado está su reclamo y llaman al call center.",
    "solucion_objetivo": "Portal web de autogestión; objetivo: reducir 40 % las llamadas.",
    "segmento": "Empresas de servicios con más de 10.000 clientes.",
    "propuesta_valor": "Seguimiento en tiempo real integrado con Nexopus.",
    "supuestos_clave": [
        "Los clientes prefieren la autogestión",
        "El call center cuesta 3 USD por llamada",
    ],
    "datos_disponibles": "Encuesta a 120 clientes.",
    "inversion_estimada": 120000,
    "ingresos_esperados": 300000,
    "flujo_mensual_neto": 10000,
}


async def _iniciativa(c: AsyncClient, **datos: object) -> dict:
    r = await c.post("/api/v1/iniciativas", json={**IDEA, **datos})
    assert r.status_code == 201, r.text
    return r.json()


async def _transicion(c: AsyncClient, iniciativa_id: str, hacia: str):
    return await c.post(f"/api/v1/iniciativas/{iniciativa_id}/transiciones", json={"hacia": hacia})


# --- Edición de la ficha ----------------------------------------------------------------------


async def test_pm_completa_la_ficha(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    r = await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={**FICHA, "pm_id": await id_de(pm)})

    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["problema"] == FICHA["problema"]
    assert cuerpo["supuestos_clave"] == FICHA["supuestos_clave"]
    assert cuerpo["inversion_estimada"] == 120000
    assert cuerpo["pm"]["id"] == await id_de(pm)


async def test_el_autor_edita_su_ficha_pero_no_asigna_pm(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO)
    i = await _iniciativa(autor)

    assert (await autor.patch(f"/api/v1/iniciativas/{i['id']}", json=FICHA)).status_code == 200
    r = await autor.patch(f"/api/v1/iniciativas/{i['id']}", json={"pm_id": await id_de(autor)})
    assert r.status_code == 403


async def test_un_evaluador_no_puede_editar_la_ficha(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    i = await _iniciativa(pm, asignaciones=[{"dimension": "TEC", "usuario_id": await id_de(tec)}])

    assert (await tec.patch(f"/api/v1/iniciativas/{i['id']}", json=FICHA)).status_code == 403


async def test_el_pm_asignado_debe_tener_rol_pm(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    i = await _iniciativa(pm)

    r = await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={"pm_id": await id_de(tec)})

    assert r.status_code == 400
    assert "pm_id" in r.json()["campos"]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("inversion_estimada", 0), ("inversion_estimada", -10), ("ingresos_esperados", -1)],
)
async def test_valores_financieros_incoherentes_se_rechazan(
    usuario_con_sesion: CrearUsuario, campo: str, valor: int
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    r = await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={campo: valor})

    assert r.status_code == 400
    assert campo in r.json()["campos"]


async def test_supuestos_vacios_se_descartan(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    r = await pm.patch(
        f"/api/v1/iniciativas/{i['id']}", json={"supuestos_clave": ["  Uno  ", "", "   "]}
    )

    assert r.json()["supuestos_clave"] == ["Uno"]


async def test_la_edicion_queda_en_auditoria(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={"segmento": "Pymes"})

    registro = (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "EDITAR_INICIATIVA"))
    ).scalar_one()
    assert registro.antes == {"segmento": None}
    assert registro.despues == {"segmento": "Pymes"}


# --- Transición a ESTRUCTURADA ----------------------------------------------------------------


async def test_ficha_incompleta_lista_los_faltantes(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)
    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={"problema": "Algo"})

    r = await _transicion(pm, i["id"], "ESTRUCTURADA")

    assert r.status_code == 422
    assert set(r.json()["campos"]) == {
        "pm_id",
        "solucion_objetivo",
        "segmento",
        "propuesta_valor",
        "supuestos_clave",
    }


async def test_ficha_completa_pasa_a_estructurada(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)
    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={**FICHA, "pm_id": await id_de(pm)})

    r = await _transicion(pm, i["id"], "ESTRUCTURADA")

    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "ESTRUCTURADA"
    registro = (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "CAMBIAR_ESTADO"))
    ).scalar_one()
    assert registro.antes == {"estado": "IDENTIFICADA"}
    assert registro.despues == {"estado": "ESTRUCTURADA"}


async def test_los_datos_financieros_son_opcionales_para_estructurar(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)
    sin_finanzas = {
        k: v
        for k, v in FICHA.items()
        if "estimada" not in k and "esperados" not in k and "flujo" not in k
    }
    await pm.patch(
        f"/api/v1/iniciativas/{i['id']}", json={**sin_finanzas, "pm_id": await id_de(pm)}
    )

    assert (await _transicion(pm, i["id"], "ESTRUCTURADA")).status_code == 200


async def test_solo_el_pm_estructura(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="autor@nepxa.test")
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(autor)
    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={**FICHA, "pm_id": await id_de(pm)})

    assert (await _transicion(autor, i["id"], "ESTRUCTURADA")).status_code == 403
    assert (await _transicion(pm, i["id"], "ESTRUCTURADA")).status_code == 200


@pytest.mark.parametrize("hacia", ["CONSOLIDADA", "DECIDIDA", "IDENTIFICADA", "ARCHIVADA"])
async def test_transicion_no_permitida_devuelve_409(
    usuario_con_sesion: CrearUsuario, hacia: str
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    r = await _transicion(pm, i["id"], hacia)

    assert r.status_code == 409


async def test_estado_desconocido_devuelve_400(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    assert (await _transicion(pm, i["id"], "VOLANDO")).status_code == 400


async def test_edicion_solo_en_estados_permitidos(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)
    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={**FICHA, "pm_id": await id_de(pm)})
    await _transicion(pm, i["id"], "ESTRUCTURADA")

    # En ESTRUCTURADA todavía se puede editar.
    assert (
        await pm.patch(f"/api/v1/iniciativas/{i['id']}", json={"segmento": "X"})
    ).status_code == 200


# --- Asignaciones -----------------------------------------------------------------------------


async def test_pm_reemplaza_las_asignaciones(usuario_con_sesion: CrearUsuario, sesion) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tec = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    com = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com@nepxa.test")
    i = await _iniciativa(pm, asignaciones=[{"dimension": "TEC", "usuario_id": await id_de(tec)}])

    r = await pm.put(
        f"/api/v1/iniciativas/{i['id']}/asignaciones",
        json={
            "asignaciones": [
                {"dimension": "MER", "usuario_id": await id_de(com)},
                {"dimension": "TEC", "usuario_id": await id_de(tec)},
            ]
        },
    )

    assert r.status_code == 200, r.text
    assert sorted(a["dimension"] for a in r.json()["asignaciones"]) == ["MER", "TEC"]
    assert (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "EDITAR_ASIGNACIONES"))
    ).scalar_one()


async def test_solo_pm_cambia_asignaciones(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO)
    i = await _iniciativa(autor)

    r = await autor.put(f"/api/v1/iniciativas/{i['id']}/asignaciones", json={"asignaciones": []})

    assert r.status_code == 403


# --- Cálculos financieros ---------------------------------------------------------------------


async def test_calculos_financieros_de_la_ficha(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)
    await pm.patch(f"/api/v1/iniciativas/{i['id']}", json=FICHA)

    r = await pm.get(f"/api/v1/iniciativas/{i['id']}/calculos-financieros")

    assert r.status_code == 200
    assert r.json() == {
        "roi": 150.0,
        "nivel_roi": 5,
        "meses_recuperacion": 12.0,
        "nivel_recuperacion": 4,
        "faltantes": [],
    }


async def test_calculos_sin_datos(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    i = await _iniciativa(pm)

    r = await pm.get(f"/api/v1/iniciativas/{i['id']}/calculos-financieros")

    assert r.json()["faltantes"] == [
        "inversion_estimada",
        "ingresos_esperados",
        "flujo_mensual_neto",
    ]
    assert r.json()["nivel_roi"] is None


async def test_calculos_respetan_la_visibilidad(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="autor@nepxa.test")
    ajeno = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="ajeno@nepxa.test")
    i = await _iniciativa(autor)

    assert (
        await ajeno.get(f"/api/v1/iniciativas/{i['id']}/calculos-financieros")
    ).status_code == 404
