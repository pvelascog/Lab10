import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/cliente";
import type { Evaluacion as TipoEvaluacion } from "../api/tipos";
import { EstadoBadge } from "../componentes/EstadoBadge";
import { MatrizCriterios } from "../componentes/MatrizCriterios";

export function Evaluacion() {
  const { id = "" } = useParams();
  const clienteConsultas = useQueryClient();
  const { data: e, isPending } = useQuery({
    queryKey: ["evaluaciones", id],
    queryFn: () => api<TipoEvaluacion>(`/evaluaciones/${id}`),
  });
  const [elegida, setElegida] = useState<string | null>(null);

  if (isPending) return <p className="cargando">Cargando evaluación…</p>;
  if (!e)
    return <p className="tarjeta mensaje-error">La evaluación no existe o no tiene acceso.</p>;

  // Por defecto se abre la primera dimensión que el usuario debe calificar.
  const codigo =
    elegida ??
    (e.dimensiones.find((d) => d.soy_evaluador && !d.enviada_por_mi) ?? e.dimensiones[0])!.codigo;
  const dimension = e.dimensiones.find((d) => d.codigo === codigo)!;
  const pendientes = Object.entries(e.pendientes);
  const actualizar = (nueva: TipoEvaluacion) => {
    // Se queda en la dimensión actual: al enviarla se revelan las calificaciones de los demás.
    setElegida(codigo);
    clienteConsultas.setQueryData(["evaluaciones", id], nueva);
  };

  return (
    <>
      <header className="encabezado-pagina">
        <div>
          <p className="codigo">
            <Link to={`/iniciativas/${e.iniciativa.id}`}>{e.iniciativa.codigo}</Link> · Evaluación{" "}
            {e.numero} · Marco v{e.version_marco}
          </p>
          <h1>{e.iniciativa.nombre}</h1>
        </div>
        <EstadoBadge estado={e.iniciativa.estado} />
      </header>

      {e.puede_gestionar && (
        <section className="tarjeta" aria-labelledby="titulo-avance">
          <h2 id="titulo-avance">Avance de la evaluación</h2>
          <table className="tabla">
            <thead>
              <tr>
                <th>Dimensión</th>
                <th>Evaluadores</th>
              </tr>
            </thead>
            <tbody>
              {e.dimensiones.map((d) => (
                <tr key={d.codigo}>
                  <th scope="row">
                    {d.codigo} · {d.nombre}
                  </th>
                  <td>
                    {d.evaluadores.map((ev) => (
                      <span key={ev.usuario.id} className="etiqueta">
                        {ev.usuario.nombre}:{" "}
                        {ev.enviado ? "enviada" : `${ev.calificados}/${d.criterios.length}`}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className={pendientes.length ? "" : "texto-secundario"}>
            {pendientes.length
              ? `${pendientes.length} criterios pendientes para consolidar.`
              : "Sin pendientes: la evaluación se puede consolidar."}
          </p>
          {pendientes.some(([, motivo]) => motivo.startsWith("Divergencia")) && (
            <ul>
              {pendientes
                .filter(([, motivo]) => motivo.startsWith("Divergencia"))
                .map(([criterio, motivo]) => (
                  <li key={criterio}>
                    <strong>{criterio}</strong>: {motivo}
                  </li>
                ))}
            </ul>
          )}
        </section>
      )}

      <nav className="pestanas" aria-label="Dimensiones">
        {e.dimensiones.map((d) => {
          const calificados = d.criterios.filter((c) => c.mi_calificacion).length;
          return (
            <button
              key={d.codigo}
              type="button"
              className={d.codigo === codigo ? "activa" : ""}
              aria-current={d.codigo === codigo ? "page" : undefined}
              onClick={() => setElegida(d.codigo)}
            >
              {d.codigo} · {d.nombre}
              {d.soy_evaluador && (
                <small>
                  {d.enviada_por_mi ? " ✓ enviada" : ` ${calificados}/${d.criterios.length}`}
                </small>
              )}
            </button>
          );
        })}
      </nav>

      <section className="tarjeta" aria-label={`Dimensión ${dimension.nombre}`}>
        {!dimension.soy_evaluador && !dimension.ver_calificaciones && (
          <p className="aviso">
            No evalúa esta dimensión. Las calificaciones se mostrarán al consolidar la evaluación.
          </p>
        )}
        <MatrizCriterios
          evaluacionId={e.id}
          dimension={dimension}
          puedeGestionar={e.puede_gestionar}
          abierta={e.estado === "ABIERTA"}
          onActualizada={actualizar}
        />
      </section>
    </>
  );
}
