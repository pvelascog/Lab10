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


FICHA = {
    "problema": "Los clientes no saben en qué estado está su reclamo y llaman al call center.",
    "solucion_objetivo": "Portal web de autogestión; objetivo: reducir 40 % las llamadas.",
    "segmento": "Empresas de servicios con más de 10.000 clientes.",
    "propuesta_valor": "Seguimiento en tiempo real integrado con Nexopus.",
    "supuestos_clave": ["Los clientes prefieren la autogestión"],
    "inversion_estimada": 120000,
    "ingresos_esperados": 300000,
    "flujo_mensual_neto": 10000,
}

CRITERIOS = {
    "MER": ["MER-01", "MER-02", "MER-03", "MER-04", "MER-05"],
    "COM": ["COM-01", "COM-02", "COM-03", "COM-04", "COM-05", "COM-06"],
    "FIN": ["FIN-01", "FIN-02", "FIN-03", "FIN-04"],
    "TEC": ["TEC-01", "TEC-02", "TEC-03", "TEC-04", "TEC-05"],
    "CMP": ["CMP-01", "CMP-02", "CMP-03", "CMP-04"],
    "ECO": ["ECO-01", "ECO-02", "ECO-03", "ECO-04"],
}


async def preparar_evaluacion(
    pm: AsyncClient, evaluadores: dict[str, list[AsyncClient]] | None = None
) -> tuple[str, str]:
    """Iniciativa estructurada y en evaluación. Las dimensiones sin evaluador indicado se asignan
    al PM. Devuelve (iniciativa_id, evaluacion_id)."""
    evaluadores = evaluadores or {}
    asignaciones = [
        {"dimension": d, "usuario_id": await id_de(c)}
        for d in CRITERIOS
        for c in evaluadores.get(d, [pm])
    ]
    r = await pm.post("/api/v1/iniciativas", json={**IDEA, "asignaciones": asignaciones})
    assert r.status_code == 201, r.text
    iniciativa_id = r.json()["id"]
    r = await pm.patch(
        f"/api/v1/iniciativas/{iniciativa_id}", json={**FICHA, "pm_id": await id_de(pm)}
    )
    assert r.status_code == 200, r.text
    for hacia in ("ESTRUCTURADA", "EN_EVALUACION"):
        r = await pm.post(
            f"/api/v1/iniciativas/{iniciativa_id}/transiciones", json={"hacia": hacia}
        )
        assert r.status_code == 200, r.text
    return iniciativa_id, r.json()["evaluacion_actual_id"]


async def calificar(
    c: AsyncClient, evaluacion_id: str, criterio: str, nivel: int, justificacion: str = "Evidencia"
):
    return await c.put(
        f"/api/v1/evaluaciones/{evaluacion_id}/calificaciones/{criterio}",
        json={"nivel": nivel, "justificacion": justificacion},
    )


async def calificar_dimension(
    c: AsyncClient, evaluacion_id: str, dimension: str, nivel: int = 4, enviar: bool = True
) -> None:
    for criterio in CRITERIOS[dimension]:
        n = {1: 1, 2: 3, 3: 3, 4: 5, 5: 5}[nivel] if criterio == "COM-04" else nivel
        r = await calificar(c, evaluacion_id, criterio, n)
        assert r.status_code == 200, r.text
    if enviar:
        r = await c.post(f"/api/v1/evaluaciones/{evaluacion_id}/dimensiones/{dimension}/enviar")
        assert r.status_code == 200, r.text
