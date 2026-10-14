import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/cliente";
import {
  ESTADOS,
  NOMBRES_ESTADOS,
  NOMBRES_ORIGENES,
  ORIGENES,
  type IniciativaResumen,
} from "../api/tipos";
import { EstadoBadge } from "../componentes/EstadoBadge";
import { formatearFecha } from "../utilidades/fechas";

const FILTROS = ["estado", "origen", "desde", "hasta", "orden"] as const;

export function Backlog() {
  // Los filtros viven en la URL para poder compartir o recargar la vista.
  const [parametros, setParametros] = useSearchParams();
  const filtros = Object.fromEntries(
    FILTROS.map((f) => [f, parametros.get(f) ?? undefined]),
  ) as Record<(typeof FILTROS)[number], string | undefined>;

  const { data, isPending, error } = useQuery({
    queryKey: ["iniciativas", filtros],
    queryFn: () => api<IniciativaResumen[]>("/iniciativas", { parametros: filtros }),
  });

  function cambiar(nombre: (typeof FILTROS)[number], valor: string) {
    const nuevos = new URLSearchParams(parametros);
    if (valor) nuevos.set(nombre, valor);
    else nuevos.delete(nombre);
    setParametros(nuevos, { replace: true });
  }

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Backlog de iniciativas</h1>
        <Link className="boton" to="/iniciativas/nueva">
          Nueva iniciativa
        </Link>
      </header>

      <section className="tarjeta filtros" aria-label="Filtros">
        <label>
          Estado
          <select value={filtros.estado ?? ""} onChange={(e) => cambiar("estado", e.target.value)}>
            <option value="">Todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {NOMBRES_ESTADOS[e]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Origen
          <select value={filtros.origen ?? ""} onChange={(e) => cambiar("origen", e.target.value)}>
            <option value="">Todos</option>
            {ORIGENES.map((o) => (
              <option key={o} value={o}>
                {NOMBRES_ORIGENES[o]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Desde
          <input
            type="date"
            value={filtros.desde ?? ""}
            onChange={(e) => cambiar("desde", e.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={filtros.hasta ?? ""}
            onChange={(e) => cambiar("hasta", e.target.value)}
          />
        </label>
        <label>
          Orden
          <select value={filtros.orden ?? ""} onChange={(e) => cambiar("orden", e.target.value)}>
            <option value="">Más recientes</option>
            <option value="creado_en">Más antiguas</option>
            <option value="nombre">Nombre (A–Z)</option>
            <option value="-nombre">Nombre (Z–A)</option>
          </select>
        </label>
      </section>

      {isPending && <p className="cargando">Cargando iniciativas…</p>}
      {error && <p className="mensaje-error">No fue posible cargar el backlog.</p>}
      {data && data.length === 0 && (
        <p className="tarjeta texto-secundario">No hay iniciativas con estos filtros.</p>
      )}
      {data && data.length > 0 && (
        <div className="tarjeta tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th>Código</th>
                <th>Iniciativa</th>
                <th>Origen</th>
                <th>Estado</th>
                <th>Registrada por</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {data.map((i) => (
                <tr key={i.id}>
                  <td className="codigo">{i.codigo}</td>
                  <td>
                    <Link to={`/iniciativas/${i.id}`}>{i.nombre}</Link>
                  </td>
                  <td>{NOMBRES_ORIGENES[i.origen]}</td>
                  <td>
                    <EstadoBadge estado={i.estado} />
                  </td>
                  <td>{i.autor.nombre}</td>
                  <td>{formatearFecha(i.creado_en)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
