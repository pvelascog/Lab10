from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, fabrica_sesiones
from app.main import app
from app.modelos.usuarios import CodigoRol
from app.semillas.marco_v3 import sembrar_datos_base
from app.servicios.usuarios import crear_usuario

RAIZ_BACKEND = Path(__file__).resolve().parents[2]
CONTRASENA = "Contrasena-segura-123"


@pytest.fixture(scope="session", autouse=True)
def esquema() -> None:
    configuracion = Config(str(RAIZ_BACKEND / "alembic.ini"))
    configuracion.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    command.downgrade(configuracion, "base")
    command.upgrade(configuracion, "head")


@pytest.fixture(autouse=True)
async def datos_limpios() -> None:
    tablas = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with fabrica_sesiones()() as sesion:
        await sesion.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
        await sembrar_datos_base(sesion)
        await sesion.commit()


@pytest.fixture
async def sesion() -> AsyncIterator[AsyncSession]:
    async with fabrica_sesiones()() as s:
        yield s


@pytest.fixture
async def cliente() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as c:
        yield c


CrearUsuario = Callable[..., Awaitable[AsyncClient]]


@pytest.fixture
async def usuario_con_sesion() -> AsyncIterator[CrearUsuario]:
    """Crea un usuario con los roles indicados y devuelve un cliente con su sesión iniciada."""

    clientes: list[AsyncClient] = []

    async def _crear(*roles: CodigoRol, correo: str | None = None) -> AsyncClient:
        correo = correo or f"{'-'.join(r.value.lower() for r in roles) or 'sin-rol'}@nepxa.test"
        async with fabrica_sesiones()() as s:
            await crear_usuario(
                s,
                nombre=correo.split("@")[0],
                correo=correo,
                contrasena=CONTRASENA,
                roles=list(roles),
            )
            await s.commit()
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba")
        clientes.append(c)
        respuesta = await c.post(
            "/api/v1/auth/login", json={"correo": correo, "contrasena": CONTRASENA}
        )
        assert respuesta.status_code == 200, respuesta.text
        c.headers["X-CSRF-Token"] = respuesta.json()["csrf"]
        return c

    yield _crear
    for c in clientes:
        await c.aclose()


async def id_de(c: AsyncClient) -> str:
    """Identificador del usuario con sesión en el cliente."""
    return str((await c.get("/api/v1/auth/yo")).json()["id"])


IDEA = {
    "nombre": "Portal de autogestión de reclamos",
    "descripcion": "Plataforma para que los clientes registren y sigan sus reclamos en línea.",
    "origen": "CLIENTES",
}
