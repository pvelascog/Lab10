"""Gestión de usuarios: listado para asignar evaluadores y administración (ADMIN_MARCO)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import obtener_sesion
from app.esquemas.usuarios import UsuarioActualizar, UsuarioCrear, UsuarioSalida
from app.modelos.usuarios import CodigoRol, Rol, Usuario
from app.seguridad import requiere_rol
from app.servicios.usuarios import actualizar_usuario, crear_usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]
PmOAdmin = Annotated[Usuario, Depends(requiere_rol(CodigoRol.PM, CodigoRol.ADMIN_MARCO))]
Admin = Annotated[Usuario, Depends(requiere_rol(CodigoRol.ADMIN_MARCO))]


@router.get("")
async def listar(sesion: Sesion, _: PmOAdmin, rol: CodigoRol | None = None) -> list[UsuarioSalida]:
    consulta = select(Usuario).order_by(Usuario.nombre)
    if rol is not None:
        consulta = consulta.where(Usuario.roles.any(Rol.codigo == rol))
    usuarios = (await sesion.execute(consulta)).scalars()
    return [UsuarioSalida.desde(u) for u in usuarios]


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(datos: UsuarioCrear, sesion: Sesion, admin: Admin) -> UsuarioSalida:
    usuario = await crear_usuario(
        sesion,
        nombre=datos.nombre,
        correo=datos.correo,
        contrasena=datos.contrasena,
        roles=datos.roles,
        creado_por=admin.id,
    )
    await sesion.commit()
    return UsuarioSalida.desde(usuario)


@router.patch("/{usuario_id}")
async def actualizar(
    usuario_id: uuid.UUID, datos: UsuarioActualizar, sesion: Sesion, admin: Admin
) -> UsuarioSalida:
    usuario = await actualizar_usuario(
        sesion,
        usuario_id,
        actualizado_por=admin.id,
        nombre=datos.nombre,
        roles=datos.roles,
        activo=datos.activo,
    )
    await sesion.commit()
    return UsuarioSalida.desde(usuario)
