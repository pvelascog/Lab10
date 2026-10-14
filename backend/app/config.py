"""Configuración de la aplicación a partir de variables de entorno (archivo .env opcional)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    entorno: Literal["desarrollo", "pruebas", "produccion"] = "desarrollo"
    database_url: str = "postgresql+asyncpg://validador:validador@localhost:5432/validador"

    jwt_secreto: str = Field(min_length=32)
    jwt_minutos: int = 8 * 60
    # Activar en producción (HTTPS). En desarrollo local se trabaja sobre http://localhost.
    cookie_segura: bool = False

    url_frontend: str = "http://localhost:5173"
    anthropic_api_key: str | None = None

    intentos_maximos_login: int = 5
    minutos_bloqueo_login: int = 15


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
