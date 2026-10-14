"""T026 – Creación del primer administrador."""

from app.modelos.usuarios import CodigoRol
from app.semillas.admin import crear_administrador


async def test_crea_administrador_con_roles_extra(sesion, cliente) -> None:
    usuario = await crear_administrador(
        sesion,
        nombre="Ana",
        correo="Ana@NEPXA.test",
        contrasena="Contrasena-segura-123",
        roles_extra=[CodigoRol.PM, CodigoRol.ADMIN_MARCO],
    )
    await sesion.commit()

    assert usuario is not None
    assert usuario.codigos_roles == [CodigoRol.PM, CodigoRol.ADMIN_MARCO]
    respuesta = await cliente.post(
        "/api/v1/auth/login",
        json={"correo": "ana@nepxa.test", "contrasena": "Contrasena-segura-123"},
    )
    assert respuesta.status_code == 200


async def test_no_duplica_si_el_correo_existe(sesion) -> None:
    datos = {"nombre": "Ana", "correo": "ana@nepxa.test", "contrasena": "Contrasena-segura-123"}
    assert await crear_administrador(sesion, **datos) is not None
    assert await crear_administrador(sesion, **datos) is None
