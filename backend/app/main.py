"""Aplicación FastAPI del Validador de Viabilidad de Productos."""

from fastapi import FastAPI

app = FastAPI(
    title="Validador de Viabilidad de Productos",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
)


@app.get("/api/v1/salud", tags=["sistema"])
async def salud() -> dict[str, str]:
    """Verificación de disponibilidad usada por Docker Compose y la integración continua."""
    return {"estado": "ok"}
