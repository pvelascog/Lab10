"""T031 – HU1: registrar una iniciativa en el backlog (FR-001, FR-003, FR-004, FR-010, FR-027a)."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modelos.auditoria import Auditoria
from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import IDEA, CrearUsuario, id_de


async def _registrar(c: AsyncClient, **cambios: object) -> dict:
    respuesta = await c.post("/api/v1/iniciativas", json={**IDEA, **cambios})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


# --- Escenario 1: registro válido -------------------------------------------------------------


async def test_cualquier_usuario_registra_una_iniciativa(usuario_con_sesion: CrearUsuario) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)

    iniciativa = await _registrar(miembro)

    assert iniciativa["estado"] == "IDENTIFICADA"
    assert iniciativa["pm"] is None
    backlog = (await miembro.get("/api/v1/iniciativas")).json()
    assert [i["codigo"] for i in backlog] == [iniciativa["codigo"]]


async def test_los_codigos_son_unicos_y_correlativos(usuario_con_sesion: CrearUsuario) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)

    a = await _registrar(miembro, nombre="Idea A", descripcion="Primera idea sin relación.")
    b = await _registrar(miembro, nombre="Idea B", descripcion="Otra cosa completamente distinta.")

    anio = date.today().year
    assert a["codigo"] == f"INI-{anio}-0001"
    assert b["codigo"] == f"INI-{anio}-0002"


async def test_el_registro_queda_en_auditoria(usuario_con_sesion: CrearUsuario, sesion) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)

    iniciativa = await _registrar(miembro)

    registro = (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "CREAR_INICIATIVA"))
    ).scalar_one()
    assert registro.entidad_id == iniciativa["id"]
    assert registro.despues["codigo"] == iniciativa["codigo"]


# --- Escenario 2: campos faltantes ------------------------------------------------------------


@pytest.mark.parametrize("campo", ["nombre", "descripcion", "origen"])
async def test_campo_obligatorio_faltante_devuelve_400_con_el_campo(
    usuario_con_sesion: CrearUsuario, campo: str
) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)
    datos = {k: v for k, v in IDEA.items() if k != campo}

    respuesta = await miembro.post("/api/v1/iniciativas", json=datos)

    assert respuesta.status_code == 400
    assert campo in respuesta.json()["campos"]


async def test_nombre_en_blanco_y_origen_invalido_se_rechazan(
    usuario_con_sesion: CrearUsuario,
) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)

    respuesta = await miembro.post(
        "/api/v1/iniciativas", json={**IDEA, "nombre": "   ", "origen": "OTRO"}
    )

    assert respuesta.status_code == 400
    assert {"nombre", "origen"} <= set(respuesta.json()["campos"])


# --- Escenario 3: posible duplicado -----------------------------------------------------------


async def test_advierte_posible_duplicado(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    original = await _registrar(pm)

    similar = await _registrar(pm, nombre="Portal de autogestión para reclamos")

    assert similar["posible_duplicado_de"]["codigo"] == original["codigo"]
    assert similar["posible_duplicado_de"]["nombre"] == original["nombre"]
    assert similar["posible_duplicado_de"]["similitud"] >= 0.6


async def test_ideas_distintas_no_se_marcan_como_duplicadas(
    usuario_con_sesion: CrearUsuario,
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    await _registrar(pm)

    otra = await _registrar(
        pm,
        nombre="Motor de recomendaciones de precios",
        descripcion="Modelo que sugiere precios dinámicos a partir de la demanda histórica.",
    )

    assert otra["posible_duplicado_de"] is None


async def test_duplicado_no_visible_solo_revela_el_codigo(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="autor@nepxa.test")
    otro = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="otro@nepxa.test")
    original = await _registrar(autor)

    similar = await _registrar(otro, nombre="Portal de autogestión para reclamos")

    assert similar["posible_duplicado_de"]["codigo"] == original["codigo"]
    assert similar["posible_duplicado_de"]["nombre"] is None  # Principio VI: confidencialidad


# --- Escenario 4: evaluadores por dimensión ---------------------------------------------------


async def test_registra_varios_evaluadores_por_dimension(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    com1 = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com1@nepxa.test")
    com2 = await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com2@nepxa.test")

    iniciativa = await _registrar(
        pm,
        asignaciones=[
            {"dimension": "MER", "usuario_id": await id_de(com1)},
            {"dimension": "MER", "usuario_id": await id_de(com2)},
            {"dimension": "COM", "usuario_id": await id_de(com1)},
        ],
    )

    pares = sorted((a["dimension"], a["usuario"]["nombre"]) for a in iniciativa["asignaciones"])
    assert pares == [("COM", "com1"), ("MER", "com1"), ("MER", "com2")]


@pytest.mark.parametrize(
    ("asignacion", "mensaje"),
    [
        ({"dimension": "XYZ", "usuario_id": None}, "dimensión"),
        ({"dimension": "MER", "usuario_id": "00000000-0000-0000-0000-000000000000"}, "usuario"),
    ],
)
async def test_asignacion_invalida_devuelve_400(
    usuario_con_sesion: CrearUsuario, asignacion: dict, mensaje: str
) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    if asignacion["usuario_id"] is None:
        asignacion = {**asignacion, "usuario_id": await id_de(pm)}

    respuesta = await pm.post("/api/v1/iniciativas", json={**IDEA, "asignaciones": [asignacion]})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["campos"]["asignaciones"].lower()


async def test_asignacion_repetida_se_guarda_una_vez(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    uid = await id_de(pm)

    iniciativa = await _registrar(pm, asignaciones=[{"dimension": "FIN", "usuario_id": uid}] * 2)

    assert len(iniciativa["asignaciones"]) == 1


# --- Visibilidad (FR-027a) --------------------------------------------------------------------


async def test_visibilidad_del_backlog(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="autor@nepxa.test")
    ajeno = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="ajeno@nepxa.test")
    evaluador = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="eval@nepxa.test")
    tecnico_no_asignado = await usuario_con_sesion(
        CodigoRol.LIDER_TECNICO, correo="tec2@nepxa.test"
    )
    pm = await usuario_con_sesion(CodigoRol.PM)
    comite = await usuario_con_sesion(CodigoRol.COMITE)
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)

    # El autor (miembro) no puede listar usuarios, así que la asignación la hace un PM al registrar.
    iniciativa = await _registrar(
        pm, asignaciones=[{"dimension": "TEC", "usuario_id": await id_de(evaluador)}]
    )
    propia = await _registrar(autor, nombre="Idea propia", descripcion="Algo sin relación alguna.")

    async def codigos(c: AsyncClient) -> set[str]:
        return {i["codigo"] for i in (await c.get("/api/v1/iniciativas")).json()}

    assert await codigos(autor) == {propia["codigo"]}
    assert await codigos(ajeno) == set()
    assert await codigos(evaluador) == {iniciativa["codigo"]}
    assert await codigos(tecnico_no_asignado) == set()
    for portafolio in (pm, comite, admin):
        assert await codigos(portafolio) == {iniciativa["codigo"], propia["codigo"]}


async def test_detalle_no_visible_devuelve_404(usuario_con_sesion: CrearUsuario) -> None:
    autor = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="autor@nepxa.test")
    ajeno = await usuario_con_sesion(CodigoRol.MIEMBRO, correo="ajeno@nepxa.test")
    iniciativa = await _registrar(autor)

    assert (await autor.get(f"/api/v1/iniciativas/{iniciativa['id']}")).status_code == 200
    assert (await ajeno.get(f"/api/v1/iniciativas/{iniciativa['id']}")).status_code == 404
    inexistente = "/api/v1/iniciativas/00000000-0000-0000-0000-000000000000"
    assert (await autor.get(inexistente)).status_code == 404


async def test_backlog_requiere_sesion(cliente: AsyncClient) -> None:
    assert (await cliente.get("/api/v1/iniciativas")).status_code == 401
    assert (await cliente.post("/api/v1/iniciativas", json=IDEA)).status_code == 401


# --- Filtros y orden (FR-004) -----------------------------------------------------------------


async def test_filtra_por_origen_y_fecha(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    a = await _registrar(pm, origen="CLIENTES")
    b = await _registrar(
        pm, nombre="Idea de socios", descripcion="Alianza con un socio.", origen="SOCIOS"
    )
    hoy = date.today().isoformat()

    async def codigos(**parametros: str) -> list[str]:
        respuesta = await pm.get("/api/v1/iniciativas", params=parametros)
        assert respuesta.status_code == 200, respuesta.text
        return [i["codigo"] for i in respuesta.json()]

    assert await codigos(origen="SOCIOS") == [b["codigo"]]
    assert await codigos(estado="IDENTIFICADA", orden="creado_en") == [a["codigo"], b["codigo"]]
    assert await codigos(estado="ESTRUCTURADA") == []
    assert await codigos(desde=hoy, hasta=hoy, orden="-creado_en") == [b["codigo"], a["codigo"]]
    assert await codigos(desde="2000-01-01", hasta="2000-12-31") == []
    assert await codigos(orden="nombre") == [b["codigo"], a["codigo"]]


async def test_filtro_invalido_devuelve_400(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)

    respuesta = await pm.get("/api/v1/iniciativas", params={"estado": "NO_EXISTE"})

    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()["campos"]
