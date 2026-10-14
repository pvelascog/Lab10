"""T009 – Inicio de sesión, bloqueo, cierre de sesión y CSRF (FR-027, research.md D6)."""

from httpx import AsyncClient

from app.modelos.usuarios import CodigoRol
from tests.integration.conftest import CONTRASENA, CrearUsuario


async def test_login_valido_fija_cookie_y_devuelve_usuario(
    cliente: AsyncClient, usuario_con_sesion: CrearUsuario
) -> None:
    await usuario_con_sesion(CodigoRol.PM, correo="ana@nepxa.test")
    await cliente.post("/api/v1/auth/logout")  # cliente nuevo, sin sesión

    respuesta = await cliente.post(
        "/api/v1/auth/login", json={"correo": "ANA@nepxa.test", "contrasena": CONTRASENA}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["usuario"]["correo"] == "ana@nepxa.test"
    assert cuerpo["usuario"]["roles"] == ["PM"]
    assert cuerpo["csrf"]
    cookie = respuesta.headers["set-cookie"]
    assert "sesion=" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()


async def test_yo_devuelve_el_usuario_de_la_sesion(usuario_con_sesion: CrearUsuario) -> None:
    c = await usuario_con_sesion(CodigoRol.LIDER_TECNICO, CodigoRol.COMITE)

    respuesta = await c.get("/api/v1/auth/yo")

    assert respuesta.status_code == 200
    assert sorted(respuesta.json()["roles"]) == ["COMITE", "LIDER_TECNICO"]
    assert "hash_contrasena" not in respuesta.json()


async def test_credenciales_invalidas_devuelven_401_generico(
    cliente: AsyncClient, usuario_con_sesion: CrearUsuario
) -> None:
    await usuario_con_sesion(CodigoRol.MIEMBRO, correo="beto@nepxa.test")

    mala_clave = await cliente.post(
        "/api/v1/auth/login", json={"correo": "beto@nepxa.test", "contrasena": "incorrecta"}
    )
    inexistente = await cliente.post(
        "/api/v1/auth/login", json={"correo": "nadie@nepxa.test", "contrasena": "incorrecta"}
    )

    assert mala_clave.status_code == inexistente.status_code == 401
    assert mala_clave.json()["detalle"] == inexistente.json()["detalle"]


async def test_bloqueo_tras_cinco_intentos_fallidos(
    cliente: AsyncClient, usuario_con_sesion: CrearUsuario
) -> None:
    await usuario_con_sesion(CodigoRol.MIEMBRO, correo="carla@nepxa.test")
    for _ in range(5):
        await cliente.post(
            "/api/v1/auth/login", json={"correo": "carla@nepxa.test", "contrasena": "mala"}
        )

    # Bloqueada aunque ahora use la contraseña correcta.
    respuesta = await cliente.post(
        "/api/v1/auth/login", json={"correo": "carla@nepxa.test", "contrasena": CONTRASENA}
    )

    assert respuesta.status_code == 429
    assert "bloqueada" in respuesta.json()["detalle"].lower()


async def test_usuario_inactivo_no_puede_iniciar_sesion(
    cliente: AsyncClient, usuario_con_sesion: CrearUsuario
) -> None:
    admin = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)
    creado = await admin.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Dani",
            "correo": "dani@nepxa.test",
            "contrasena": CONTRASENA,
            "roles": ["MIEMBRO"],
        },
    )
    await admin.patch(f"/api/v1/usuarios/{creado.json()['id']}", json={"activo": False})

    respuesta = await cliente.post(
        "/api/v1/auth/login", json={"correo": "dani@nepxa.test", "contrasena": CONTRASENA}
    )

    assert respuesta.status_code == 401


async def test_logout_cierra_la_sesion(usuario_con_sesion: CrearUsuario) -> None:
    c = await usuario_con_sesion(CodigoRol.MIEMBRO)

    assert (await c.post("/api/v1/auth/logout")).status_code == 204
    assert (await c.get("/api/v1/auth/yo")).status_code == 401


async def test_metodo_que_modifica_sin_csrf_es_rechazado(usuario_con_sesion: CrearUsuario) -> None:
    c = await usuario_con_sesion(CodigoRol.ADMIN_MARCO)
    del c.headers["X-CSRF-Token"]

    respuesta = await c.post(
        "/api/v1/usuarios",
        json={"nombre": "X", "correo": "x@nepxa.test", "contrasena": CONTRASENA, "roles": []},
    )

    assert respuesta.status_code == 403
    assert "csrf" in respuesta.json()["detalle"].lower()


async def test_csrf_de_otra_sesion_es_rechazado(usuario_con_sesion: CrearUsuario) -> None:
    a = await usuario_con_sesion(CodigoRol.ADMIN_MARCO, correo="a@nepxa.test")
    b = await usuario_con_sesion(CodigoRol.ADMIN_MARCO, correo="b@nepxa.test")
    a.headers["X-CSRF-Token"] = b.headers["X-CSRF-Token"]

    respuesta = await a.post(
        "/api/v1/usuarios",
        json={"nombre": "X", "correo": "x@nepxa.test", "contrasena": CONTRASENA, "roles": []},
    )

    assert respuesta.status_code == 403


async def test_token_manipulado_es_rechazado(usuario_con_sesion: CrearUsuario) -> None:
    c = await usuario_con_sesion(CodigoRol.MIEMBRO)
    token = c.cookies["sesion"]
    c.cookies.set("sesion", token[:-2] + ("AA" if not token.endswith("AA") else "BB"))

    assert (await c.get("/api/v1/auth/yo")).status_code == 401


async def test_inicio_de_sesion_queda_en_auditoria(
    usuario_con_sesion: CrearUsuario, sesion
) -> None:
    from sqlalchemy import select

    from app.modelos.auditoria import Auditoria

    await usuario_con_sesion(CodigoRol.MIEMBRO)

    acciones = (await sesion.execute(select(Auditoria.accion))).scalars().all()
    assert "INICIAR_SESION" in acciones
