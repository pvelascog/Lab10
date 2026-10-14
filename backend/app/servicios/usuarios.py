"""Gestión de usuarios y autenticación."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import obtener_configuracion
from app.errores import DatosInvalidos, NoEncontrado
from app.modelos.usuarios import CodigoRol, Rol, Usuario
from app.seguridad import HASH_FICTICIO, hash_contrasena, verificar_contrasena
from app.servicios import auditoria

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos"


def normalizar_correo(correo: str) -> str:
    return correo.strip().lower()


def resumen(usuario: Usuario) -> dict[str, object]:
    """Fotografía de un usuario para la auditoría (sin datos sensibles)."""
    return {
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "activo": usuario.activo,
        "roles": [r.value for r in usuario.codigos_roles],
    }


async def _roles(sesion: AsyncSession, codigos: list[CodigoRol]) -> list[Rol]:
    if not codigos:
        return []
    return list((await sesion.execute(select(Rol).where(Rol.codigo.in_(codigos)))).scalars())


async def crear_usuario(
    sesion: AsyncSession,
    *,
    nombre: str,
    correo: str,
    contrasena: str,
    roles: list[CodigoRol],
    creado_por: uuid.UUID | None = None,
) -> Usuario:
    correo = normalizar_correo(correo)
    if await sesion.scalar(select(Usuario.id).where(Usuario.correo == correo)):
        raise DatosInvalidos({"correo": "Ya existe un usuario con este correo"})
    usuario = Usuario(
        nombre=nombre.strip(),
        correo=correo,
        hash_contrasena=hash_contrasena(contrasena),
        roles=await _roles(sesion, roles),
    )
    sesion.add(usuario)
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=creado_por,
        accion="CREAR_USUARIO",
        entidad="usuario",
        entidad_id=usuario.id,
        despues=resumen(usuario),
    )
    return usuario


async def actualizar_usuario(
    sesion: AsyncSession,
    usuario_id: uuid.UUID,
    *,
    actualizado_por: uuid.UUID,
    nombre: str | None = None,
    roles: list[CodigoRol] | None = None,
    activo: bool | None = None,
) -> Usuario:
    usuario = await sesion.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado")
    antes = resumen(usuario)
    if nombre is not None:
        usuario.nombre = nombre.strip()
    if roles is not None:
        usuario.roles = await _roles(sesion, roles)
    if activo is not None:
        usuario.activo = activo
    await sesion.flush()
    await auditoria.registrar(
        sesion,
        usuario_id=actualizado_por,
        accion="EDITAR_USUARIO",
        entidad="usuario",
        entidad_id=usuario.id,
        antes=antes,
        despues=resumen(usuario),
    )
    return usuario


async def autenticar(sesion: AsyncSession, correo: str, contrasena: str) -> Usuario:
    """Valida credenciales aplicando el bloqueo por intentos fallidos. Confirma la transacción."""
    configuracion = obtener_configuracion()
    ahora = datetime.now(UTC)
    usuario = await sesion.scalar(
        select(Usuario).where(Usuario.correo == normalizar_correo(correo))
    )

    if usuario is not None and usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Cuenta bloqueada temporalmente por intentos fallidos. Intente más tarde.",
        )

    valida = verificar_contrasena(usuario.hash_contrasena if usuario else HASH_FICTICIO, contrasena)
    if usuario is None or not valida or not usuario.activo:
        if usuario is not None and not valida:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= configuracion.intentos_maximos_login:
                usuario.bloqueado_hasta = ahora + timedelta(
                    minutes=configuracion.minutos_bloqueo_login
                )
                usuario.intentos_fallidos = 0
            await sesion.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MENSAJE_CREDENCIALES)

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    await auditoria.registrar(
        sesion,
        usuario_id=usuario.id,
        accion="INICIAR_SESION",
        entidad="usuario",
        entidad_id=usuario.id,
    )
    await sesion.commit()
    return usuario
