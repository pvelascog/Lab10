import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.usuarios import CodigoRol, Usuario

PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Correo = Annotated[str, Field(pattern=PATRON_CORREO, max_length=320)]
Nombre = Annotated[str, Field(min_length=1, max_length=200)]


class CredencialesEntrada(BaseModel):
    correo: Correo
    contrasena: str = Field(min_length=1, max_length=200)


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    correo: str
    activo: bool
    roles: list[CodigoRol]

    @classmethod
    def desde(cls, usuario: Usuario) -> "UsuarioSalida":
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            activo=usuario.activo,
            roles=usuario.codigos_roles,
        )


class SesionSalida(BaseModel):
    usuario: UsuarioSalida
    csrf: str


class UsuarioCrear(BaseModel):
    nombre: Nombre
    correo: Correo
    contrasena: str = Field(min_length=10, max_length=200)
    roles: list[CodigoRol] = []

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre es obligatorio")
        return valor


class UsuarioActualizar(BaseModel):
    nombre: Nombre | None = None
    roles: list[CodigoRol] | None = None
    activo: bool | None = None
