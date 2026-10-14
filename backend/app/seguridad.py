"""Contraseñas, tokens de sesión, CSRF y dependencias de acceso por rol (research.md D6).

- La sesión es un JWT firmado en una cookie HttpOnly + SameSite=Lax.
- Protección CSRF de doble envío ligada al token: el JWT lleva un valor `csrf` que el cliente
  debe repetir en la cabecera X-CSRF-Token en todo método que modifique datos.
"""

import hmac
import secrets
import uuid
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import obtener_configuracion
from app.db import obtener_sesion
from app.modelos.usuarios import CodigoRol, Usuario

COOKIE_SESION = "sesion"
COOKIE_CSRF = "csrf"
CABECERA_CSRF = "X-CSRF-Token"
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}
ALGORITMO = "HS256"

_hasher = PasswordHasher()
# Hash de referencia para igualar el tiempo de respuesta cuando el correo no existe.
HASH_FICTICIO = _hasher.hash(secrets.token_urlsafe(16))


def hash_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar_contrasena(hash_guardado: str, contrasena: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerificationError, InvalidHashError):
        return False


def crear_token(usuario_id: uuid.UUID) -> tuple[str, str]:
    """Devuelve (jwt, csrf)."""
    configuracion = obtener_configuracion()
    ahora = datetime.now(UTC)
    csrf = secrets.token_urlsafe(32)
    carga = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=configuracion.jwt_minutos),
        "csrf": csrf,
    }
    return jwt.encode(carga, configuracion.jwt_secreto, algorithm=ALGORITMO), csrf


def fijar_cookies_sesion(respuesta: Response, token: str, csrf: str) -> None:
    configuracion = obtener_configuracion()
    duracion = configuracion.jwt_minutos * 60
    respuesta.set_cookie(
        COOKIE_SESION,
        token,
        max_age=duracion,
        httponly=True,
        samesite="lax",
        secure=configuracion.cookie_segura,
        path="/",
    )
    # Legible por el frontend para reenviarla en la cabecera tras recargar la página.
    respuesta.set_cookie(
        COOKIE_CSRF,
        csrf,
        max_age=duracion,
        httponly=False,
        samesite="lax",
        secure=configuracion.cookie_segura,
        path="/",
    )


def borrar_cookies_sesion(respuesta: Response) -> None:
    respuesta.delete_cookie(COOKIE_SESION, path="/")
    respuesta.delete_cookie(COOKIE_CSRF, path="/")


def _no_autenticado(detalle: str = "Se requiere iniciar sesión") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detalle)


async def usuario_actual(
    request: Request, sesion: Annotated[AsyncSession, Depends(obtener_sesion)]
) -> Usuario:
    token = request.cookies.get(COOKIE_SESION)
    if not token:
        raise _no_autenticado()
    try:
        carga = jwt.decode(
            token,
            obtener_configuracion().jwt_secreto,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "exp", "csrf"]},
        )
        usuario_id = uuid.UUID(carga["sub"])
    except (jwt.PyJWTError, ValueError) as error:
        raise _no_autenticado("Sesión inválida o expirada") from error

    usuario = await sesion.scalar(select(Usuario).where(Usuario.id == usuario_id))
    if usuario is None or not usuario.activo:
        raise _no_autenticado("Sesión inválida o expirada")

    if request.method not in METODOS_SEGUROS:
        enviado = request.headers.get(CABECERA_CSRF, "")
        if not hmac.compare_digest(enviado.encode(), str(carga["csrf"]).encode()):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Token CSRF inválido o ausente")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


def requiere_rol(*roles: CodigoRol) -> Callable[..., Coroutine[Any, Any, Usuario]]:
    """Dependencia que exige al menos uno de los roles indicados."""

    async def _verificar(usuario: UsuarioActual) -> Usuario:
        if not usuario.tiene_rol(*roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permisos para esta acción")
        return usuario

    return _verificar
