import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import { useMarcoVigente } from "../api/consultas";
import type { ResultadoEvaluacion } from "../api/tipos";
import { RadarDimensiones } from "../componentes/RadarDimensiones";
import { ResultadoBadge } from "../componentes/ResultadoBadge";
import { formatearFecha } from "../utilidades/fechas";
import { formatearPorcentaje, truncar } from "../utilidades/formato";

type Lista = "fortalezas" | "debilidades" | "riesgos" | "supuestos_criticos";
const LISTAS: { campo: Lista; titulo: string }[] = [
  { campo: "fortalezas", titulo: "Fortalezas" },
  { campo: "debilidades", titulo: "Debilidades" },
  { campo: "riesgos", titulo: "Riesgos" },
  { campo: "supuestos_criticos", titulo: "Supuestos críticos" },
];

function estadoDimension(r: ResultadoEvaluacion, puntaje: number): string | null {
  if (puntaje < r.umbrales.critico) return "Crítica";
  if (puntaje < r.umbrales.debil) return "Débil";
  return null;
}

export function Resumen() {
  const { id = "" } = useParams();
  const clienteConsultas = useQueryClient();
  const marco = useMarcoVigente();
  const {
    data: r,
    error,
    isPending,
  } = useQuery({
    queryKey: ["evaluaciones", id, "resultado"],
    queryFn: () => api<ResultadoEvaluacion>(`/evaluaciones/${id}/resultado`),
  });
  const [editando, setEditando] = useState<Lista | null>(null);
  const [texto, setTexto] = useState("");

  const guardar = useMutation({
    mutationFn: (campo: Lista) =>
      api<ResultadoEvaluacion>(`/evaluaciones/${id}/resultado`, {
        metodo: "PATCH",
        cuerpo: { [campo]: texto.split("\n") },
      }),
    onSuccess: (nuevo) => {
      clienteConsultas.setQueryData(["evaluaciones", id, "resultado"], nuevo);
      setEditando(null);
    },
  });

  if (isPending) return <p className="cargando">Cargando resumen…</p>;
  if (error || !r) {
    const pendiente = error instanceof ErrorApi && error.estado === 404;
    return (
      <p className="tarjeta mensaje-error">
        {pendiente ? "La evaluación aún no está consolidada." : "No fue posible cargar el resumen."}
      </p>
    );
  }

  const nombresCriterio = Object.fromEntries(
    (marco.data?.dimensiones ?? []).flatMap((d) => d.criterios).map((c) => [c.codigo, c.nombre]),
  );

  return (
    <>
      <header className="encabezado-pagina">
        <div>
          <p className="codigo">
            <Link to={`/iniciativas/${r.iniciativa.id}`}>{r.iniciativa.codigo}</Link> · Marco v
            {r.version_marco} · consolidada el {formatearFecha(r.consolidado_en)}
            {r.consolidado_por && ` por ${r.consolidado_por.nombre}`}
          </p>
          <h1>Resumen ejecutivo · {r.iniciativa.nombre}</h1>
        </div>
      </header>

      <section className="tarjeta resultado-principal" aria-labelledby="titulo-resultado">
        <h2 id="titulo-resultado" className="solo-lectores">
          Resultado recomendado
        </h2>
        <ResultadoBadge resultado={r.resultado} grande />
        <div>
          <p className="score">
            Score total <strong>{truncar(r.score_total)}</strong>
            <span className="texto-secundario"> / 5</span>
          </p>
          <p className="sin-margen">
            Regla aplicada: <strong>{r.regla_aplicada}</strong>
          </p>
          <p className="texto-secundario sin-margen">
            Resultado recomendado por el modelo. La decisión final corresponde al Comité de
            Producto.
          </p>
        </div>
      </section>

      <section className="tarjeta rejilla-resumen" aria-labelledby="titulo-dimensiones">
        <RadarDimensiones
          puntajes={r.puntajes_dimension}
          nombres={r.nombres_dimension}
          referencias={[
            { valor: r.umbrales.debil, etiqueta: "débil" },
            { valor: r.umbrales.score_go, etiqueta: "GO" },
          ]}
        />
        <div>
          <h2 id="titulo-dimensiones">Puntajes por dimensión</h2>
          <table className="tabla">
            <thead>
              <tr>
                <th>Dimensión</th>
                <th>Puntaje</th>
                <th>Peso</th>
                <th>Balance</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(r.puntajes_dimension).map(([codigo, puntaje]) => {
                const estado = estadoDimension(r, puntaje);
                return (
                  <tr
                    key={codigo}
                    className={r.dimensiones_implicadas.includes(codigo) ? "implicada" : ""}
                  >
                    <th scope="row">
                      {codigo} · {r.nombres_dimension[codigo]}
                    </th>
                    <td className="numero">{truncar(puntaje)}</td>
                    <td className="numero">{formatearPorcentaje(r.pesos[codigo] ?? 0)}</td>
                    <td>
                      {estado ? (
                        <span className={`etiqueta ${estado === "Crítica" ? "critica" : "alerta"}`}>
                          {estado}
                        </span>
                      ) : (
                        <span className="texto-secundario">Aceptable</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rejilla-listas">
        {LISTAS.map(({ campo, titulo }) => (
          <article key={campo} className="tarjeta" aria-labelledby={`titulo-${campo}`}>
            <header className="encabezado-pagina">
              <h2 id={`titulo-${campo}`}>{titulo}</h2>
              {r.puede_editar && editando !== campo && (
                <button
                  type="button"
                  className="secundario"
                  onClick={() => {
                    setTexto(r[campo].join("\n"));
                    setEditando(campo);
                  }}
                >
                  Editar
                </button>
              )}
            </header>
            {editando === campo ? (
              <div className="formulario">
                <label>
                  Un elemento por línea
                  <textarea
                    rows={5}
                    value={texto}
                    onChange={(e) => setTexto(e.target.value)}
                    aria-label={`Editar ${titulo.toLowerCase()}`}
                  />
                </label>
                <div className="acciones">
                  <button type="button" className="secundario" onClick={() => setEditando(null)}>
                    Cancelar
                  </button>
                  <button
                    type="button"
                    disabled={guardar.isPending}
                    onClick={() => guardar.mutate(campo)}
                  >
                    Guardar
                  </button>
                </div>
              </div>
            ) : r[campo].length ? (
              <ul className="sin-margen">
                {r[campo].map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            ) : (
              <p className="texto-secundario sin-margen">Sin elementos.</p>
            )}
          </article>
        ))}
      </section>

      <details className="tarjeta">
        <summary>
          <strong>Puntaje de cada criterio</strong>
        </summary>
        <table className="tabla">
          <tbody>
            {Object.entries(r.puntajes_criterio).map(([codigo, puntaje]) => (
              <tr key={codigo}>
                <th scope="row">
                  {codigo} {nombresCriterio[codigo] ?? ""}
                </th>
                <td>{truncar(puntaje)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p>
          <Link to={`/evaluaciones/${r.evaluacion_id}`}>Ver calificaciones y justificaciones</Link>
        </p>
      </details>
    </>
  );
}
