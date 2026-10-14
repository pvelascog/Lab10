"""Crea el primer administrador del marco.

Uso:
    python -m app.semillas.admin --nombre "Ana Pérez" --correo ana@empresa.com [--roles PM,COMITE]

La contraseña se toma de la variable ADMIN_CONTRASENA o se pide por consola.
"""

import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import fabrica_sesiones
from app.modelos.usuarios import CodigoRol, Usuario
from app.semillas.marco_v3 import sembrar_datos_base
from app.servicios.usuarios import crear_usuario, normalizar_correo

LONGITUD_MINIMA = 10


async def crear_administrador(
    sesion: AsyncSession,
    *,
    nombre: str,
    correo: str,
    contrasena: str,
    roles_extra: list[CodigoRol] | None = None,
) -> Usuario | None:
    """Crea el usuario con rol ADMIN_MARCO. Devuelve None si el correo ya existe."""
    await sembrar_datos_base(sesion)
    if await sesion.scalar(select(Usuario.id).where(Usuario.correo == normalizar_correo(correo))):
        return None
    roles = [CodigoRol.ADMIN_MARCO, *(r for r in roles_extra or [] if r != CodigoRol.ADMIN_MARCO)]
    return await crear_usuario(
        sesion, nombre=nombre, correo=correo, contrasena=contrasena, roles=roles
    )


def _leer_contrasena() -> str:
    if contrasena := os.environ.get("ADMIN_CONTRASENA"):
        return contrasena
    contrasena = getpass.getpass("Contraseña: ")
    if contrasena != getpass.getpass("Repita la contraseña: "):
        sys.exit("Las contraseñas no coinciden.")
    return contrasena


async def principal() -> None:
    parser = argparse.ArgumentParser(description="Crea el primer administrador del marco.")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--correo", required=True)
    parser.add_argument(
        "--roles", default="", help="Roles adicionales separados por comas, p. ej. PM,COMITE"
    )
    argumentos = parser.parse_args()
    try:
        extra = [CodigoRol(r.strip()) for r in argumentos.roles.split(",") if r.strip()]
    except ValueError:
        sys.exit(f"Roles válidos: {', '.join(r.value for r in CodigoRol)}")

    contrasena = _leer_contrasena()
    if len(contrasena) < LONGITUD_MINIMA:
        sys.exit(f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.")

    async with fabrica_sesiones()() as sesion:
        usuario = await crear_administrador(
            sesion,
            nombre=argumentos.nombre,
            correo=argumentos.correo,
            contrasena=contrasena,
            roles_extra=extra,
        )
        await sesion.commit()
    if usuario is None:
        sys.exit(f"Ya existe un usuario con el correo {argumentos.correo}.")
    print(f"Administrador creado: {usuario.correo} ({', '.join(usuario.codigos_roles)})")


if __name__ == "__main__":
    asyncio.run(principal())
