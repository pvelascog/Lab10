from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_salud_responde_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as cliente:
        respuesta = await cliente.get("/api/v1/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
