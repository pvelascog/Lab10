"""Quién puede ver qué iniciativa (FR-027a).

Ven el portafolio completo los roles PM, Comité y Administrador del marco. El resto ve solo las
iniciativas que registró, de las que es PM o en las que está asignado como evaluador.
"""

from sqlalchemy import ColumnElement, or_, true

from app.modelos.iniciativas import AsignacionEvaluador, Iniciativa
from app.modelos.usuarios import CodigoRol, Usuario

ROLES_PORTAFOLIO = (CodigoRol.PM, CodigoRol.COMITE, CodigoRol.ADMIN_MARCO)


def ve_portafolio(usuario: Usuario) -> bool:
    return usuario.tiene_rol(*ROLES_PORTAFOLIO)


def condicion_visible(usuario: Usuario) -> ColumnElement[bool]:
    """Filtro SQL equivalente a `es_visible`."""
    if ve_portafolio(usuario):
        return true()
    return or_(
        Iniciativa.autor_id == usuario.id,
        Iniciativa.pm_id == usuario.id,
        Iniciativa.asignaciones.any(AsignacionEvaluador.usuario_id == usuario.id),
    )


def es_visible(usuario: Usuario, iniciativa: Iniciativa) -> bool:
    return (
        ve_portafolio(usuario)
        or usuario.id in (iniciativa.autor_id, iniciativa.pm_id)
        or any(a.usuario_id == usuario.id for a in iniciativa.asignaciones)
    )
