"""T030 – Contrato de POST /iniciativas y GET /iniciativas (contracts/api.md – Iniciativas)."""

import re

from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import IDEA, CrearUsuario, id_de

CAMPOS_RESUMEN = {
    "id",
    "codigo",
    "nombre",
    "descripcion",
    "origen",
    "estado",
    "autor",
    "pm",
    "creado_en",
}
CAMPOS_DETALLE = CAMPOS_RESUMEN | {
    "problema",
    "solucion_objetivo",
    "segmento",
    "propuesta_valor",
    "supuestos_clave",
    "datos_disponibles",
    "inversion_estimada",
    "ingresos_esperados",
    "flujo_mensual_neto",
    "asignaciones",
    "posible_duplicado_de",
    "evaluacion_actual_id",
}


async def test_post_iniciativas_devuelve_201_con_el_detalle(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    tecnico = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")

    respuesta = await pm.post(
        "/api/v1/iniciativas",
        json={**IDEA, "asignaciones": [{"dimension": "TEC", "usuario_id": await id_de(tecnico)}]},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_DETALLE
    assert re.fullmatch(r"INI-\d{4}-\d{4}", cuerpo["codigo"])
    assert cuerpo["estado"] == "IDENTIFICADA"
    assert cuerpo["autor"] == {"id": await id_de(pm), "nombre": "pm"}
    assert cuerpo["supuestos_clave"] == []
    assert cuerpo["posible_duplicado_de"] is None
    assert cuerpo["asignaciones"] == [
        {
            "dimension": "TEC",
            "usuario": {"id": await id_de(tecnico), "nombre": "tec"},
            "origen": "MANUAL",
        }
    ]


async def test_get_iniciativas_devuelve_lista_de_resumenes(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    await pm.post("/api/v1/iniciativas", json=IDEA)

    respuesta = await pm.get("/api/v1/iniciativas")

    assert respuesta.status_code == 200
    lista = respuesta.json()
    assert isinstance(lista, list) and len(lista) == 1
    assert set(lista[0]) == CAMPOS_RESUMEN
