import { NOMBRES_ROLES, type Dimension, type Usuario } from "../api/tipos";

export type Asignaciones = Record<string, string[]>; // código de dimensión → ids de usuario

interface Props {
  dimensiones: Dimension[];
  usuarios: Usuario[];
  valor: Asignaciones;
  onChange: (valor: Asignaciones) => void;
}

/** Uno o varios evaluadores por dimensión; primero se ofrecen los del rol sugerido (FR-010). */
export function SelectorEvaluadores({ dimensiones, usuarios, valor, onChange }: Props) {
  const activos = usuarios.filter((u) => u.activo);
  const nombre = (id: string) => activos.find((u) => u.id === id)?.nombre ?? id;

  return (
    <div className="selector-evaluadores">
      {dimensiones.map((d) => {
        const elegidos = valor[d.codigo] ?? [];
        const disponibles = activos
          .filter((u) => !elegidos.includes(u.id))
          .sort((a, b) => {
            const sugeridoA = d.rol_sugerido && a.roles.includes(d.rol_sugerido) ? 0 : 1;
            const sugeridoB = d.rol_sugerido && b.roles.includes(d.rol_sugerido) ? 0 : 1;
            return sugeridoA - sugeridoB || a.nombre.localeCompare(b.nombre);
          });
        return (
          <fieldset key={d.codigo} className="fila-evaluadores">
            <legend>
              {d.codigo} · {d.nombre}
              {d.rol_sugerido && (
                <small className="texto-secundario">
                  {" "}
                  — sugerido: {NOMBRES_ROLES[d.rol_sugerido]}
                </small>
              )}
            </legend>
            <ul className="chips">
              {elegidos.map((id) => (
                <li key={id} className="chip">
                  {nombre(id)}
                  <button
                    type="button"
                    aria-label={`Quitar a ${nombre(id)} de ${d.nombre}`}
                    onClick={() =>
                      onChange({ ...valor, [d.codigo]: elegidos.filter((x) => x !== id) })
                    }
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
            <select
              aria-label={`Agregar evaluador de ${d.nombre}`}
              value=""
              onChange={(e) =>
                e.target.value && onChange({ ...valor, [d.codigo]: [...elegidos, e.target.value] })
              }
            >
              <option value="">Agregar evaluador…</option>
              {disponibles.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre}
                  {d.rol_sugerido && u.roles.includes(d.rol_sugerido) ? " ★" : ""}
                </option>
              ))}
            </select>
          </fieldset>
        );
      })}
    </div>
  );
}
