import { NOMBRES_ESTADOS, type EstadoIniciativa } from "../api/tipos";

export function EstadoBadge({ estado }: { estado: EstadoIniciativa }) {
  return <span className={`estado estado-${estado.toLowerCase()}`}>{NOMBRES_ESTADOS[estado]}</span>;
}
