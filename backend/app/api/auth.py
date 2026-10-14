"""Rutas de autenticación (contracts/api.md – Autenticación y usuarios)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.esquemas.usuarios import CredencialesEntrada, SesionSalida, UsuarioSalida
from app.seguridad import UsuarioActual, borrar_cookies_sesion, crear_token, fijar_cookies_sesion
from app.servicios.usuarios import autenticar

router = APIRouter(prefix="/auth", tags=["autenticación"])
Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.post("/login")
async def iniciar_sesion(
    credenciales: CredencialesEntrada, respuesta: Response, sesion: Sesion
) -> SesionSalida:
    usuario = await autenticar(sesion, credenciales.correo, credenciales.contrasena)
    token, csrf = crear_token(usuario.id)
    fijar_cookies_sesion(respuesta, token, csrf)
    return SesionSalida(usuario=UsuarioSalida.desde(usuario), csrf=csrf)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def cerrar_sesion(respuesta: Response) -> None:
    borrar_cookies_sesion(respuesta)


@router.get("/yo")
async def yo(usuario: UsuarioActual) -> UsuarioSalida:
    return UsuarioSalida.desde(usuario)
