import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import { useMarcoVigente } from "../api/consultas";
import { NOMBRES_ORIGENES, type IniciativaDetalle } from "../api/tipos";
import { EstadoBadge } from "../componentes/EstadoBadge";
import { formatearFecha } from "../utilidades/fechas";

export function DetalleIniciativa() {
  const { id = "" } = useParams();
  const recienCreada = (useLocation().state as { recienCreada?: boolean } | null)?.recienCreada;
  const marco = useMarcoVigente();
  const {
    data: i,
    error,
    isPending,
  } = useQuery({
    queryKey: ["iniciativas", id],
    queryFn: () => api<IniciativaDetalle>(`/iniciativas/${id}`),
  });

  if (isPending) return <p className="cargando">Cargando…</p>;
  if (error || !i) {
    const noExiste = error instanceof ErrorApi && error.estado === 404;
    return (
      <p className="tarjeta mensaje-error">
        {noExiste ? "La iniciativa no existe o no tiene acceso a ella." : "Error al cargar."}
      </p>
    );
  }

  const dimensiones = marco.data?.dimensiones ?? [];
  const duplicado = i.posible_duplicado_de;

  return (
    <>
      {recienCreada && (
        <p className="aviso exito">Iniciativa {i.codigo} registrada en el backlog.</p>
      )}
      {duplicado && (
        <p className="aviso advertencia" role="status">
          Posible duplicado de{" "}
          {duplicado.id ? (
            <Link to={`/iniciativas/${duplicado.id}`}>
              {duplicado.codigo} · {duplicado.nombre}
            </Link>
          ) : (
            <strong>{duplicado.codigo}</strong>
          )}{" "}
          (similitud {Math.trunc(duplicado.similitud * 100)} %).
          {!duplicado.id && " Consulte con el Product Manager antes de continuar."}
        </p>
      )}

      <section className="tarjeta">
        <header className="encabezado-pagina">
          <div>
            <p className="codigo">{i.codigo}</p>
            <h1>{i.nombre}</h1>
          </div>
          <EstadoBadge estado={i.estado} />
        </header>
        <p>{i.descripcion}</p>
        <dl className="datos">
          <dt>Origen</dt>
          <dd>{NOMBRES_ORIGENES[i.origen]}</dd>
          <dt>Registrada por</dt>
          <dd>
            {i.autor.nombre} · {formatearFecha(i.creado_en)}
          </dd>
          <dt>Product Manager</dt>
          <dd>{i.pm?.nombre ?? "Sin asignar"}</dd>
        </dl>
      </section>

      <section className="tarjeta">
        <h2>Evaluadores por dimensión</h2>
        <table className="tabla">
          <tbody>
            {dimensiones.map((d) => {
              const nombres = i.asignaciones
                .filter((a) => a.dimension === d.codigo)
                .map((a) => a.usuario.nombre);
              return (
                <tr key={d.codigo}>
                  <th scope="row">
                    {d.codigo} · {d.nombre}
                  </th>
                  <td className={nombres.length ? "" : "texto-secundario"}>
                    {nombres.join(", ") || "Sin evaluador"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </>
  );
}
