import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import { useMarcoVigente } from "../api/consultas";
import { CAMPOS_FICHA, NOMBRES_ORIGENES, type IniciativaDetalle } from "../api/tipos";
import { EstadoBadge } from "../componentes/EstadoBadge";
import { useSesion } from "../estado/sesion";
import { formatearFecha } from "../utilidades/fechas";
import { gestiona, puedeEditarFicha } from "../utilidades/permisos";

export function DetalleIniciativa() {
  const { id = "" } = useParams();
  const recienCreada = (useLocation().state as { recienCreada?: boolean } | null)?.recienCreada;
  const marco = useMarcoVigente();
  const { usuario } = useSesion();
  const {
    data: i,
    error,
    isPending,
  } = useQuery({
    queryKey: ["iniciativas", id],
    queryFn: () => api<IniciativaDetalle>(`/iniciativas/${id}`),
  });
  const navegar = useNavigate();
  const clienteConsultas = useQueryClient();
  const iniciar = useMutation({
    mutationFn: () =>
      api<IniciativaDetalle>(`/iniciativas/${id}/transiciones`, {
        metodo: "POST",
        cuerpo: { hacia: "EN_EVALUACION" },
      }),
    onSuccess: async (nueva) => {
      clienteConsultas.setQueryData(["iniciativas", id], nueva);
      await clienteConsultas.invalidateQueries({ queryKey: ["iniciativas"] });
      if (nueva.evaluacion_actual_id) navegar(`/evaluaciones/${nueva.evaluacion_actual_id}`);
    },
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

      {(i.evaluacion_actual_id || (i.estado === "ESTRUCTURADA" && gestiona(usuario, i))) && (
        <section className="tarjeta" aria-labelledby="titulo-evaluacion">
          <header className="encabezado-pagina">
            <h2 id="titulo-evaluacion">Evaluación multidimensional</h2>
            {i.evaluacion_actual_id ? (
              <Link className="boton" to={`/evaluaciones/${i.evaluacion_actual_id}`}>
                Ir a la evaluación
              </Link>
            ) : (
              <button type="button" disabled={iniciar.isPending} onClick={() => iniciar.mutate()}>
                Iniciar evaluación
              </button>
            )}
          </header>
          {!i.evaluacion_actual_id && (
            <p className="texto-secundario sin-margen">
              Cada dimensión necesita al menos un evaluador. Al iniciar, los evaluadores asignados
              podrán calificar los criterios.
            </p>
          )}
          {iniciar.error instanceof ErrorApi && (
            <div className="aviso advertencia" role="alert">
              <p className="sin-margen">{iniciar.error.detalle}</p>
              <ul>
                {Object.entries(iniciar.error.campos).map(([campo, motivo]) => (
                  <li key={campo}>{motivo}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="tarjeta">
        <header className="encabezado-pagina">
          <h2>Ficha de la iniciativa</h2>
          <Link
            className={puedeEditarFicha(usuario, i) ? "boton" : "boton secundario"}
            to={`/iniciativas/${i.id}/ficha`}
          >
            {!puedeEditarFicha(usuario, i)
              ? "Ver ficha"
              : i.problema
                ? "Editar ficha"
                : "Completar ficha"}
          </Link>
        </header>
        {i.problema ? (
          <dl className="datos">
            {(["problema", "solucion_objetivo", "segmento", "propuesta_valor"] as const).map(
              (c) => (
                <div key={c} className="contents">
                  <dt>{CAMPOS_FICHA[c]}</dt>
                  <dd>{i[c] ?? <span className="texto-secundario">Pendiente</span>}</dd>
                </div>
              ),
            )}
            <dt>{CAMPOS_FICHA.supuestos_clave}</dt>
            <dd>
              {i.supuestos_clave.length ? (
                <ul className="sin-margen">
                  {i.supuestos_clave.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : (
                <span className="texto-secundario">Pendiente</span>
              )}
            </dd>
          </dl>
        ) : (
          <p className="texto-secundario">
            La ficha aún no se completa. El Product Manager la estructura antes de la evaluación.
          </p>
        )}
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
