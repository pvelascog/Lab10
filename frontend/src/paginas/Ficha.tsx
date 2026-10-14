import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import { useMarcoVigente, useUsuarios } from "../api/consultas";
import {
  CAMPOS_FICHA,
  type CalculosFinancieros,
  type Criterio,
  type IniciativaDetalle,
} from "../api/tipos";
import { EstadoBadge } from "../componentes/EstadoBadge";
import { SelectorEvaluadores, type Asignaciones } from "../componentes/SelectorEvaluadores";
import { useSesion } from "../estado/sesion";
import { truncar } from "../utilidades/formato";
import { gestiona, puedeEditarFicha } from "../utilidades/permisos";

type Textos = Record<
  "problema" | "solucion_objetivo" | "segmento" | "propuesta_valor" | "datos_disponibles",
  string
>;
type Montos = Record<"inversion_estimada" | "ingresos_esperados" | "flujo_mensual_neto", string>;

const TEXTOS: { campo: keyof Textos; ayuda: string }[] = [
  { campo: "problema", ayuda: "Dolor real del cliente: qué ocurre, a quién y con qué impacto." },
  {
    campo: "solucion_objetivo",
    ayuda: "Qué se propone construir y qué objetivo medible persigue.",
  },
  { campo: "segmento", ayuda: "Tipo de cliente, tamaño, industria o región." },
  { campo: "propuesta_valor", ayuda: "Por qué es mejor que las alternativas actuales." },
  { campo: "datos_disponibles", ayuda: "Evidencia disponible: encuestas, ventas, entrevistas…" },
];

function aTexto(n: number | null): string {
  return n === null ? "" : String(n);
}

function aNumero(s: string): number | null {
  return s.trim() === "" ? null : Number(s);
}

function agruparAsignaciones(i: IniciativaDetalle): Asignaciones {
  const grupos: Asignaciones = {};
  for (const a of i.asignaciones) (grupos[a.dimension] ??= []).push(a.usuario.id);
  return grupos;
}

export function Ficha() {
  const { id = "" } = useParams();
  const clienteConsultas = useQueryClient();
  const { usuario } = useSesion();
  const marco = useMarcoVigente();
  const consulta = useQuery({
    queryKey: ["iniciativas", id],
    queryFn: () => api<IniciativaDetalle>(`/iniciativas/${id}`),
  });
  const calculos = useQuery({
    queryKey: ["iniciativas", id, "calculos"],
    queryFn: () => api<CalculosFinancieros>(`/iniciativas/${id}/calculos-financieros`),
  });
  const i = consulta.data;
  const esPm = !!i && gestiona(usuario, i);
  const usuarios = useUsuarios(esPm);

  const [textos, setTextos] = useState<Textos>({
    problema: "",
    solucion_objetivo: "",
    segmento: "",
    propuesta_valor: "",
    datos_disponibles: "",
  });
  const [montos, setMontos] = useState<Montos>({
    inversion_estimada: "",
    ingresos_esperados: "",
    flujo_mensual_neto: "",
  });
  const [supuestos, setSupuestos] = useState<string[]>([""]);
  const [pmId, setPmId] = useState("");
  const [asignaciones, setAsignaciones] = useState<Asignaciones>({});
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [mensaje, setMensaje] = useState<string | null>(null);
  const avisos = useRef<HTMLDivElement>(null);

  // Lleva la vista a los avisos para que el resultado de guardar o validar no pase inadvertido.
  useEffect(() => {
    if (errores.general || mensaje) avisos.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [errores.general, mensaje]);

  // Carga inicial del formulario desde la iniciativa.
  useEffect(() => {
    if (!i) return;
    setTextos({
      problema: i.problema ?? "",
      solucion_objetivo: i.solucion_objetivo ?? "",
      segmento: i.segmento ?? "",
      propuesta_valor: i.propuesta_valor ?? "",
      datos_disponibles: i.datos_disponibles ?? "",
    });
    setMontos({
      inversion_estimada: aTexto(i.inversion_estimada),
      ingresos_esperados: aTexto(i.ingresos_esperados),
      flujo_mensual_neto: aTexto(i.flujo_mensual_neto),
    });
    setSupuestos(i.supuestos_clave.length ? i.supuestos_clave : [""]);
    setPmId(i.pm?.id ?? "");
    setAsignaciones(agruparAsignaciones(i));
  }, [i]);

  async function refrescar(nueva: IniciativaDetalle) {
    clienteConsultas.setQueryData(["iniciativas", id], nueva);
    await clienteConsultas.invalidateQueries({ queryKey: ["iniciativas"] });
  }

  function mostrarError(e: unknown) {
    setMensaje(null);
    setErrores(
      e instanceof ErrorApi
        ? { ...e.campos, general: e.detalle }
        : { general: "No fue posible guardar" },
    );
  }

  const guardar = useMutation({
    mutationFn: () =>
      api<IniciativaDetalle>(`/iniciativas/${id}`, {
        metodo: "PATCH",
        cuerpo: {
          ...textos,
          supuestos_clave: supuestos,
          inversion_estimada: aNumero(montos.inversion_estimada),
          ingresos_esperados: aNumero(montos.ingresos_esperados),
          flujo_mensual_neto: aNumero(montos.flujo_mensual_neto),
          ...(esPm ? { pm_id: pmId || null } : {}),
        },
      }),
    onSuccess: async (nueva) => {
      await refrescar(nueva);
      setErrores({});
      setMensaje("Ficha guardada.");
    },
    onError: mostrarError,
  });

  const guardarEvaluadores = useMutation({
    mutationFn: () =>
      api<IniciativaDetalle>(`/iniciativas/${id}/asignaciones`, {
        metodo: "PUT",
        cuerpo: {
          asignaciones: Object.entries(asignaciones).flatMap(([dimension, ids]) =>
            ids.map((usuario_id) => ({ dimension, usuario_id })),
          ),
        },
      }),
    onSuccess: async (nueva) => {
      await refrescar(nueva);
      setErrores({});
      setMensaje("Evaluadores guardados.");
    },
    onError: mostrarError,
  });

  const estructurar = useMutation({
    mutationFn: async () => {
      await guardar.mutateAsync();
      return api<IniciativaDetalle>(`/iniciativas/${id}/transiciones`, {
        metodo: "POST",
        cuerpo: { hacia: "ESTRUCTURADA" },
      });
    },
    onSuccess: async (nueva) => {
      await refrescar(nueva);
      setErrores({});
      setMensaje("La iniciativa quedó estructurada y lista para la evaluación.");
    },
    onError: mostrarError,
  });

  if (consulta.isPending) return <p className="cargando">Cargando…</p>;
  if (!i)
    return <p className="tarjeta mensaje-error">La iniciativa no existe o no tiene acceso.</p>;

  const editable = puedeEditarFicha(usuario, i);
  const pms = (usuarios.data ?? []).filter((u) => u.activo && u.roles.includes("PM"));
  const criterios = Object.fromEntries(
    (marco.data?.dimensiones ?? []).flatMap((d) => d.criterios).map((c) => [c.codigo, c]),
  ) as Record<string, Criterio>;
  const faltantes = Object.keys(errores).filter((k) => k in CAMPOS_FICHA);
  const ocupado = guardar.isPending || estructurar.isPending;

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    guardar.mutate();
  }

  return (
    <>
      <header className="encabezado-pagina">
        <div>
          <p className="codigo">
            <Link to={`/iniciativas/${i.id}`}>{i.codigo}</Link>
          </p>
          <h1>Ficha · {i.nombre}</h1>
        </div>
        <EstadoBadge estado={i.estado} />
      </header>

      <div ref={avisos} className="avisos">
        {!editable && (
          <p className="aviso">
            Solo lectura: la ficha la editan el autor y el Product Manager mientras la iniciativa
            está identificada o estructurada.
          </p>
        )}
        {mensaje && (
          <p className="aviso exito" role="status">
            {mensaje}
          </p>
        )}
        {errores.general && (
          <div className="aviso advertencia" role="alert">
            <p className="sin-margen">{errores.general}</p>
            {faltantes.length > 0 && (
              <ul>
                {faltantes.map((f) => (
                  <li key={f}>
                    <strong>{CAMPOS_FICHA[f]}</strong>: {errores[f]}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <form className="tarjeta formulario" onSubmit={enviar} noValidate>
        <fieldset disabled={!editable || ocupado} className="sin-borde formulario">
          <h2>Definición</h2>
          {esPm && (
            <label>
              {CAMPOS_FICHA.pm_id}
              <select
                value={pmId}
                onChange={(e) => setPmId(e.target.value)}
                aria-invalid={!!errores.pm_id}
              >
                <option value="">Sin asignar</option>
                {pms.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
              </select>
            </label>
          )}
          {TEXTOS.map(({ campo, ayuda }) => (
            <label key={campo}>
              {CAMPOS_FICHA[campo]}
              <small className="texto-secundario">{ayuda}</small>
              <textarea
                rows={3}
                value={textos[campo]}
                onChange={(e) => setTextos({ ...textos, [campo]: e.target.value })}
                aria-invalid={!!errores[campo]}
              />
            </label>
          ))}

          <div>
            <h2>{CAMPOS_FICHA.supuestos_clave}</h2>
            <p className="texto-secundario sin-margen">
              Hipótesis que deben cumplirse para que la iniciativa funcione.
            </p>
          </div>
          <ol className="lista-supuestos" aria-invalid={!!errores.supuestos_clave}>
            {supuestos.map((s, n) => (
              <li key={n}>
                <div className="fila-supuesto">
                  <input
                    aria-label={`Supuesto ${n + 1}`}
                    value={s}
                    onChange={(e) =>
                      setSupuestos(supuestos.map((x, k) => (k === n ? e.target.value : x)))
                    }
                  />
                  {supuestos.length > 1 && (
                    <button
                      type="button"
                      className="secundario"
                      aria-label={`Quitar supuesto ${n + 1}`}
                      onClick={() => setSupuestos(supuestos.filter((_, k) => k !== n))}
                    >
                      ×
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ol>
          <div>
            <button
              type="button"
              className="secundario"
              onClick={() => setSupuestos([...supuestos, ""])}
            >
              Agregar supuesto
            </button>
          </div>

          <h2>Datos financieros (opcionales)</h2>
          <div className="filtros">
            {(Object.keys(montos) as (keyof Montos)[]).map((campo) => (
              <label key={campo}>
                {CAMPOS_FICHA[campo]}
                <input
                  type="number"
                  inputMode="decimal"
                  step="0.01"
                  value={montos[campo]}
                  onChange={(e) => setMontos({ ...montos, [campo]: e.target.value })}
                  aria-invalid={!!errores[campo]}
                />
                {errores[campo] && <span className="mensaje-error">{errores[campo]}</span>}
              </label>
            ))}
          </div>
        </fieldset>

        {editable && (
          <div className="acciones">
            <button type="submit" className="secundario" disabled={ocupado}>
              {guardar.isPending ? "Guardando…" : "Guardar ficha"}
            </button>
            {i.estado === "IDENTIFICADA" && esPm && (
              <button type="button" disabled={ocupado} onClick={() => estructurar.mutate()}>
                {estructurar.isPending ? "Validando…" : "Guardar y marcar como estructurada"}
              </button>
            )}
          </div>
        )}
      </form>

      <section className="tarjeta" aria-labelledby="titulo-calculos">
        <h2 id="titulo-calculos">Propuesta para los criterios financieros</h2>
        <p className="texto-secundario">
          Calculada con los datos guardados. El evaluador financiero la confirma o ajusta con
          justificación durante la evaluación.
        </p>
        {calculos.data && (
          <dl className="datos">
            <dt>FIN-03 · Potencial de ROI</dt>
            <dd>
              {calculos.data.roi === null ? (
                "Faltan datos"
              ) : (
                <>
                  ROI {truncar(calculos.data.roi)} % → nivel{" "}
                  <strong>{calculos.data.nivel_roi}</strong>{" "}
                  <span className="texto-secundario">
                    (
                    {
                      criterios["FIN-03"]?.niveles.find((n) => n.nivel === calculos.data.nivel_roi)
                        ?.descripcion
                    }
                    )
                  </span>
                </>
              )}
            </dd>
            <dt>FIN-02 · Tiempo de recuperación</dt>
            <dd>
              {calculos.data.nivel_recuperacion === null ? (
                "Faltan datos"
              ) : (
                <>
                  {calculos.data.meses_recuperacion === null
                    ? "No se recupera (flujo no positivo)"
                    : `${truncar(calculos.data.meses_recuperacion, 1)} meses`}{" "}
                  → nivel <strong>{calculos.data.nivel_recuperacion}</strong>{" "}
                  <span className="texto-secundario">
                    (
                    {
                      criterios["FIN-02"]?.niveles.find(
                        (n) => n.nivel === calculos.data.nivel_recuperacion,
                      )?.descripcion
                    }
                    )
                  </span>
                </>
              )}
            </dd>
          </dl>
        )}
      </section>

      {esPm && marco.data && usuarios.data && (
        <section className="tarjeta formulario">
          <h2>Evaluadores por dimensión</h2>
          <p className="texto-secundario">
            Cada dimensión necesita al menos un evaluador antes de iniciar la evaluación.
          </p>
          <fieldset disabled={!editable || guardarEvaluadores.isPending} className="sin-borde">
            <SelectorEvaluadores
              dimensiones={marco.data.dimensiones}
              usuarios={usuarios.data}
              valor={asignaciones}
              onChange={setAsignaciones}
            />
          </fieldset>
          {editable && (
            <div className="acciones">
              <button
                type="button"
                className="secundario"
                disabled={guardarEvaluadores.isPending}
                onClick={() => guardarEvaluadores.mutate()}
              >
                Guardar evaluadores
              </button>
            </div>
          )}
        </section>
      )}
    </>
  );
}
