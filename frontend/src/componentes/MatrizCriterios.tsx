import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, ErrorApi } from "../api/cliente";
import type { CriterioEvaluacion, DimensionEvaluacion, Evaluacion } from "../api/tipos";
import { formatearFecha } from "../utilidades/fechas";
import { truncar } from "../utilidades/formato";

interface Props {
  evaluacionId: string;
  dimension: DimensionEvaluacion;
  puedeGestionar: boolean;
  abierta: boolean;
  onActualizada: (evaluacion: Evaluacion) => void;
}

/** Califica los criterios de una dimensión y muestra las calificaciones publicadas (HU3). */
export function MatrizCriterios({
  evaluacionId,
  dimension,
  puedeGestionar,
  abierta,
  onActualizada,
}: Props) {
  const editable = abierta && dimension.soy_evaluador && !dimension.enviada_por_mi;
  const puedeComentar = abierta && (dimension.soy_evaluador || puedeGestionar);
  const calificados = dimension.criterios.filter((c) => c.mi_calificacion).length;

  return (
    <div className="matriz">
      {dimension.soy_evaluador && !dimension.ver_calificaciones && (
        <p className="aviso">
          Calificación a ciegas: verá las calificaciones de los demás evaluadores cuando envíe esta
          dimensión.
        </p>
      )}
      {dimension.criterios.map((c) => (
        <TarjetaCriterio
          key={c.codigo}
          evaluacionId={evaluacionId}
          criterio={c}
          editable={editable}
          puedeComentar={puedeComentar}
          onActualizada={onActualizada}
        />
      ))}
      {editable && (
        <EnviarDimension
          evaluacionId={evaluacionId}
          dimension={dimension}
          completa={calificados === dimension.criterios.length}
          onActualizada={onActualizada}
        />
      )}
    </div>
  );
}

function TarjetaCriterio({
  evaluacionId,
  criterio: c,
  editable,
  puedeComentar,
  onActualizada,
}: {
  evaluacionId: string;
  criterio: CriterioEvaluacion;
  editable: boolean;
  puedeComentar: boolean;
  onActualizada: (e: Evaluacion) => void;
}) {
  const mia = c.mi_calificacion;
  const [nivel, setNivel] = useState<number | null>(mia?.nivel ?? null);
  const [justificacion, setJustificacion] = useState(mia?.justificacion ?? "");
  const [fuente, setFuente] = useState(mia?.fuente ?? "");
  const [usaCalculo, setUsaCalculo] = useState(mia?.origen === "CALCULADA_CONFIRMADA");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setNivel(mia?.nivel ?? null);
    setJustificacion(mia?.justificacion ?? "");
    setFuente(mia?.fuente ?? "");
    setUsaCalculo(mia?.origen === "CALCULADA_CONFIRMADA");
  }, [mia]);

  const guardar = useMutation({
    mutationFn: () =>
      api<Evaluacion>(`/evaluaciones/${evaluacionId}/calificaciones/${c.codigo}`, {
        metodo: "PUT",
        cuerpo: {
          nivel,
          justificacion,
          fuente: fuente.trim() || null,
          usa_calculo: usaCalculo && nivel === c.propuesta_calculada,
        },
      }),
    onSuccess: (e) => {
      setError(null);
      onActualizada(e);
    },
    onError: (e) =>
      setError(
        e instanceof ErrorApi
          ? (Object.values(e.campos)[0] ?? e.detalle)
          : "No fue posible guardar",
      ),
  });

  const cambios =
    nivel !== (mia?.nivel ?? null) ||
    justificacion !== (mia?.justificacion ?? "") ||
    fuente !== (mia?.fuente ?? "");
  const idGrupo = `nivel-${c.codigo}`;

  return (
    <article className={`criterio-evaluacion ${c.divergencia ? "con-divergencia" : ""}`}>
      <header>
        <h3>
          <span className="codigo">{c.codigo}</span> {c.nombre}
        </h3>
        {mia && !cambios && <span className="etiqueta">Calificado: {mia.nivel}</span>}
        {c.divergencia && <span className="etiqueta alerta">Divergencia</span>}
      </header>
      <p className="texto-secundario sin-margen">{c.definicion}</p>

      {editable ? (
        <>
          <fieldset className="niveles-opciones" aria-labelledby={idGrupo}>
            <legend id={idGrupo} className="solo-lectores">
              Nivel de {c.codigo}
            </legend>
            {c.niveles.map((n) => (
              <label key={n.nivel} className={nivel === n.nivel ? "elegido" : ""}>
                <input
                  type="radio"
                  name={idGrupo}
                  value={n.nivel}
                  checked={nivel === n.nivel}
                  onChange={() => {
                    setNivel(n.nivel);
                    setUsaCalculo(false);
                  }}
                />
                <span className="nivel">{n.nivel}</span>
                <span>{n.descripcion}</span>
              </label>
            ))}
          </fieldset>
          {c.propuesta_calculada !== null && (
            <p className="sin-margen">
              Nivel calculado desde la ficha: <strong>{c.propuesta_calculada}</strong>{" "}
              <button
                type="button"
                className="secundario"
                onClick={() => {
                  setNivel(c.propuesta_calculada);
                  setUsaCalculo(true);
                  if (!justificacion) setJustificacion("Según los datos financieros de la ficha.");
                }}
              >
                Usar nivel calculado
              </button>
            </p>
          )}
          <label>
            Justificación (obligatoria)
            <textarea
              rows={2}
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              aria-label={`Justificación de ${c.codigo}`}
            />
          </label>
          <label>
            Fuente de la evidencia
            <input
              value={fuente}
              onChange={(e) => setFuente(e.target.value)}
              aria-label={`Fuente de ${c.codigo}`}
              placeholder="Entrevista, informe, CRM…"
            />
          </label>
          {error && (
            <p className="mensaje-error" role="alert">
              {error}
            </p>
          )}
          <div className="acciones">
            <button
              type="button"
              disabled={!nivel || !justificacion.trim() || !cambios || guardar.isPending}
              onClick={() => guardar.mutate()}
            >
              {guardar.isPending ? "Guardando…" : mia ? "Actualizar" : "Guardar calificación"}
            </button>
          </div>
        </>
      ) : (
        mia && (
          <p className="sin-margen">
            Su calificación: <strong>{mia.nivel}</strong> — {mia.justificacion}
          </p>
        )
      )}

      {c.calificaciones && c.calificaciones.length > 0 && (
        <div className="publicadas">
          <p className="sin-margen">
            <strong>Calificaciones enviadas</strong>
            {c.promedio !== null && <> · promedio {truncar(c.promedio)}</>}
          </p>
          <ul>
            {c.calificaciones.map((p) => (
              <li key={p.evaluador.id}>
                <span className="nivel">{p.nivel}</span>
                <strong>{p.evaluador.nombre}:</strong> {p.justificacion}
                {p.fuente && <span className="texto-secundario"> · Fuente: {p.fuente}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {c.divergencia && (
        <Divergencia
          evaluacionId={evaluacionId}
          criterio={c}
          puedeComentar={puedeComentar}
          onComentado={async () =>
            onActualizada(await api<Evaluacion>(`/evaluaciones/${evaluacionId}`))
          }
        />
      )}
    </article>
  );
}

function Divergencia({
  evaluacionId,
  criterio,
  puedeComentar,
  onComentado,
}: {
  evaluacionId: string;
  criterio: CriterioEvaluacion;
  puedeComentar: boolean;
  onComentado: () => Promise<void>;
}) {
  const [texto, setTexto] = useState("");
  const comentar = useMutation({
    mutationFn: () =>
      api(`/evaluaciones/${evaluacionId}/divergencias/${criterio.codigo}/comentarios`, {
        metodo: "POST",
        cuerpo: { texto },
      }),
    onSuccess: async () => {
      setTexto("");
      await onComentado();
    },
  });

  return (
    <div className="divergencia">
      <p className="sin-margen">
        Las calificaciones difieren en 2 puntos o más. Comente el motivo antes de consolidar.
      </p>
      {criterio.comentarios?.map((m) => (
        <blockquote key={m.creado_en}>
          {m.texto}
          <footer className="texto-secundario">
            {m.autor.nombre} · {formatearFecha(m.creado_en)}
          </footer>
        </blockquote>
      ))}
      {puedeComentar && (
        <div className="fila-supuesto">
          <input
            aria-label={`Comentario sobre la divergencia de ${criterio.codigo}`}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Explique a qué se debe la diferencia"
          />
          <button
            type="button"
            className="secundario"
            disabled={!texto.trim() || comentar.isPending}
            onClick={() => comentar.mutate()}
          >
            Comentar
          </button>
        </div>
      )}
    </div>
  );
}

function EnviarDimension({
  evaluacionId,
  dimension,
  completa,
  onActualizada,
}: {
  evaluacionId: string;
  dimension: DimensionEvaluacion;
  completa: boolean;
  onActualizada: (e: Evaluacion) => void;
}) {
  const [confirmando, setConfirmando] = useState(false);
  const enviar = useMutation({
    mutationFn: () =>
      api<Evaluacion>(`/evaluaciones/${evaluacionId}/dimensiones/${dimension.codigo}/enviar`, {
        metodo: "POST",
      }),
    onSuccess: onActualizada,
  });

  return (
    <div className="tarjeta enviar-dimension">
      {!completa && (
        <p className="texto-secundario sin-margen">
          Califique todos los criterios de {dimension.nombre} para poder enviarla.
        </p>
      )}
      {enviar.error instanceof ErrorApi && (
        <p className="mensaje-error" role="alert">
          {enviar.error.detalle}
        </p>
      )}
      {confirmando ? (
        <div className="acciones">
          <span>¿Enviar {dimension.nombre}? Después no podrá modificar sus calificaciones.</span>
          <button type="button" className="secundario" onClick={() => setConfirmando(false)}>
            Cancelar
          </button>
          <button type="button" disabled={enviar.isPending} onClick={() => enviar.mutate()}>
            Confirmar envío
          </button>
        </div>
      ) : (
        <div className="acciones">
          <button type="button" disabled={!completa} onClick={() => setConfirmando(true)}>
            Enviar {dimension.nombre}
          </button>
        </div>
      )}
    </div>
  );
}
