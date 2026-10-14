import type { EstadoIniciativa, IniciativaDetalle, Usuario } from "../api/tipos";

// Reflejo en la interfaz de las reglas del backend (servicios/ciclo_vida.py y ficha.py).
export const ESTADOS_EDITABLES: EstadoIniciativa[] = ["IDENTIFICADA", "ESTRUCTURADA"];

/** PM de la iniciativa o cualquier usuario con rol PM. */
export function gestiona(usuario: Usuario | null, i: IniciativaDetalle): boolean {
  return !!usuario && (usuario.roles.includes("PM") || i.pm?.id === usuario.id);
}

export function puedeEditarFicha(usuario: Usuario | null, i: IniciativaDetalle): boolean {
  return (
    !!usuario &&
    ESTADOS_EDITABLES.includes(i.estado) &&
    (gestiona(usuario, i) || i.autor.id === usuario.id)
  );
}
