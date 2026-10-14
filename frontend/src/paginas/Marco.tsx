import { useMarcoVigente } from "../api/consultas";
import { NOMBRES_ROLES } from "../api/tipos";
import { formatearPorcentaje } from "../utilidades/formato";

export function Marco() {
  const { data: marco, isPending, error } = useMarcoVigente();

  if (isPending) return <p className="cargando">Cargando marco…</p>;
  if (error || !marco) return <p className="mensaje-error">No fue posible cargar el marco.</p>;

  const u = marco.umbrales;
  return (
    <>
      <section className="tarjeta">
        <h1>Marco de Viabilidad NEPXA v{marco.numero}</h1>
        <p className="texto-secundario">
          {marco.dimensiones.length} dimensiones ·{" "}
          {marco.dimensiones.reduce((n, d) => n + d.criterios.length, 0)} criterios · escala 1–5
        </p>
        <h2>Reglas de decisión (la más restrictiva prevalece)</h2>
        <ol className="reglas">
          <li>
            <span className="resultado nogo">NO-GO</span> score &lt; {u.score_validar} o alguna
            dimensión &lt; {u.critico}
          </li>
          <li>
            <span className="resultado validar">VALIDAR</span> score &lt; {u.score_iterar} o dos o
            más dimensiones &lt; {u.validar}
          </li>
          <li>
            <span className="resultado iterar">ITERAR</span> score &lt; {u.score_go} o alguna
            dimensión &lt; {u.debil}
          </li>
          <li>
            <span className="resultado go">GO</span> en otro caso
          </li>
        </ol>
      </section>

      {marco.dimensiones.map((d) => (
        <section key={d.codigo} className="tarjeta">
          <header className="encabezado-dimension">
            <h2>
              {d.codigo} · {d.nombre}
            </h2>
            <span className="etiqueta">Peso {formatearPorcentaje(d.peso)}</span>
            {d.rol_sugerido && (
              <span className="etiqueta">Evaluador sugerido: {NOMBRES_ROLES[d.rol_sugerido]}</span>
            )}
          </header>
          <p>{d.proposito}</p>
          {d.criterios.map((c) => (
            <details key={c.codigo} className="criterio">
              <summary>
                <strong>{c.codigo}</strong> {c.nombre}
                {c.calculable !== "NO" && <span className="etiqueta">Calculable</span>}
              </summary>
              <p>{c.definicion}</p>
              <ol className="niveles">
                {c.niveles.map((n) => (
                  <li key={n.nivel}>
                    <span className="nivel">{n.nivel}</span> {n.descripcion}
                  </li>
                ))}
              </ol>
            </details>
          ))}
        </section>
      ))}
    </>
  );
}
