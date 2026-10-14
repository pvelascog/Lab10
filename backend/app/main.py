"""Aplicación FastAPI del Validador de Viabilidad de Productos."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, evaluaciones, iniciativas, marco, usuarios
from app.errores import ErrorAplicacion

PREFIJO = "/api/v1"

app = FastAPI(
    title="Validador de Viabilidad de Productos",
    version="0.1.0",
    openapi_url=f"{PREFIJO}/openapi.json",
    docs_url=f"{PREFIJO}/docs",
)


# Formato de errores de contracts/api.md: {"detalle": "...", "campos": {...}}
@app.exception_handler(ErrorAplicacion)
async def _error_aplicacion(_: Request, error: ErrorAplicacion) -> JSONResponse:
    cuerpo: dict[str, object] = {"detalle": error.detalle}
    if error.campos:
        cuerpo["campos"] = error.campos
    return JSONResponse(cuerpo, status_code=error.estado)


@app.exception_handler(RequestValidationError)
async def _error_validacion(_: Request, error: RequestValidationError) -> JSONResponse:
    campos: dict[str, str] = {}
    for e in error.errors():
        ubicacion = [str(p) for p in e["loc"] if p not in ("body", "query", "path")]
        campos.setdefault(ubicacion[0] if ubicacion else "solicitud", e["msg"])
    return JSONResponse({"detalle": "Datos inválidos", "campos": campos}, status_code=400)


@app.exception_handler(StarletteHTTPException)
async def _error_http(_: Request, error: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        {"detalle": error.detail},
        status_code=error.status_code,
        headers=getattr(error, "headers", None),
    )


@app.get(f"{PREFIJO}/salud", tags=["sistema"])
async def salud() -> dict[str, str]:
    """Verificación de disponibilidad usada por Docker Compose y la integración continua."""
    return {"estado": "ok"}


for modulo in (auth, usuarios, marco, iniciativas, evaluaciones):
    app.include_router(modulo.router, prefix=PREFIJO)
