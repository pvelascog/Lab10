"""T010 – Permisos por rol: 401 sin sesión, 403 sin rol (FR-027, contracts/api.md)."""

import pytest
from httpx import AsyncClient

from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import CONTRASENA, CrearUsuario


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [("get", "/api/v1/auth/yo"), ("get", "/api/v1/usuarios"), ("get", "/api/v1/marco/vigente")],
)
async def test_sin_sesion_devuelve_401(cliente: AsyncClient, metodo: str, ruta: str) -> None:
    respuesta = await getattr(cliente, metodo)(ruta)

    assert respuesta.status_code == 401
    assert "detalle" in respuesta.json()


async def test_listar_usuarios_requiere_pm_o_admin(usuario_con_sesion: CrearUsuario) -> None:
    miembro = await usuario_con_sesion(CodigoRol.MIEMBRO)
    pm = await usuario_con_sesion(CodigoRol.PM)
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)

    assert (await miembro.get("/api/v1/usuarios")).status_code == 403
    assert (await pm.get("/api/v1/usuarios")).status_code == 200
    assert (await admin.get("/api/v1/usuarios")).status_code == 200


async def test_listar_usuarios_filtra_por_rol(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    await usuario_con_sesion(CodigoRol.LIDER_TECNICO, correo="tec@nepxa.test")
    await usuario_con_sesion(CodigoRol.LIDER_COMERCIAL, correo="com@nepxa.test")

    respuesta = await pm.get("/api/v1/usuarios", params={"rol": "LIDER_TECNICO"})

    assert [u["correo"] for u in respuesta.json()] == ["tec@nepxa.test"]


async def test_solo_admin_crea_y_modifica_usuarios(usuario_con_sesion: CrearUsuario) -> None:
    pm = await usuario_con_sesion(CodigoRol.PM)
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)
    nuevo = {
        "nombre": "Eva",
        "correo": "eva@nepxa.test",
        "contrasena": CONTRASENA,
        "roles": ["MIEMBRO"],
    }

    assert (await pm.post("/api/v1/usuarios", json=nuevo)).status_code == 403
    creado = await admin.post("/api/v1/usuarios", json=nuevo)
    assert creado.status_code == 201
    assert creado.json()["roles"] == ["MIEMBRO"]

    id_eva = creado.json()["id"]
    assert (await pm.patch(f"/api/v1/usuarios/{id_eva}", json={"activo": False})).status_code == 403
    cambiado = await admin.patch(f"/api/v1/usuarios/{id_eva}", json={"roles": ["PM", "COMITE"]})
    assert cambiado.status_code == 200
    assert sorted(cambiado.json()["roles"]) == ["COMITE", "PM"]


async def test_correo_duplicado_devuelve_400(usuario_con_sesion: CrearUsuario) -> None:
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO, correo="admin@nepxa.test")

    respuesta = await admin.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Otro",
            "correo": "Admin@nepxa.test",
            "contrasena": CONTRASENA,
            "roles": [],
        },
    )

    assert respuesta.status_code == 400
    assert "correo" in respuesta.json()["campos"]


async def test_datos_invalidos_devuelven_400_con_campos(usuario_con_sesion: CrearUsuario) -> None:
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)

    respuesta = await admin.post(
        "/api/v1/usuarios",
        json={
            "nombre": "",
            "correo": "no-es-correo",
            "contrasena": "corta",
            "roles": ["NO_EXISTE"],
        },
    )

    assert respuesta.status_code == 400
    assert {"nombre", "correo", "contrasena", "roles"} <= set(respuesta.json()["campos"])


async def test_cambio_de_roles_queda_en_auditoria(usuario_con_sesion: CrearUsuario, sesion) -> None:
    from sqlalchemy import select

    from app.modelos.auditoria import Auditoria

    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)
    creado = await admin.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Fer",
            "correo": "fer@nepxa.test",
            "contrasena": CONTRASENA,
            "roles": ["MIEMBRO"],
        },
    )
    await admin.patch(f"/api/v1/usuarios/{creado.json()['id']}", json={"roles": ["PM"]})

    registro = (
        await sesion.execute(select(Auditoria).where(Auditoria.accion == "EDITAR_USUARIO"))
    ).scalar_one()
    assert registro.antes["roles"] == ["MIEMBRO"]
    assert registro.despues["roles"] == ["PM"]
