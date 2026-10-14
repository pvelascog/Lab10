import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import { useMarcoVigente, useUsuarios } from "../api/consultas";
import {
  NOMBRES_ORIGENES,
  ORIGENES,
  type IniciativaDetalle,
  type OrigenIniciativa,
} from "../api/tipos";
import { SelectorEvaluadores, type Asignaciones } from "../componentes/SelectorEvaluadores";
import { useSesion } from "../estado/sesion";

export function NuevaIniciativa() {
  const navegar = useNavigate();
  const clienteConsultas = useQueryClient();
  const { tieneRol } = useSesion();
  const puedeAsignar = tieneRol("PM", "ADMIN_MARCO");
  const marco = useMarcoVigente();
  const usuarios = useUsuarios(puedeAsignar);

  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [origen, setOrigen] = useState<OrigenIniciativa | "">("");
  const [asignaciones, setAsignaciones] = useState<Asignaciones>({});
  const [errores, setErrores] = useState<Record<string, string>>({});

  const registrar = useMutation({
    mutationFn: () =>
      api<IniciativaDetalle>("/iniciativas", {
        metodo: "POST",
        cuerpo: {
          nombre,
          descripcion,
          origen,
          asignaciones: Object.entries(asignaciones).flatMap(([dimension, ids]) =>
            ids.map((usuario_id) => ({ dimension, usuario_id })),
          ),
        },
      }),
    onSuccess: async (iniciativa) => {
      await clienteConsultas.invalidateQueries({ queryKey: ["iniciativas"] });
      navegar(`/iniciativas/${iniciativa.id}`, { state: { recienCreada: true } });
    },
    onError: (e) =>
      setErrores(
        e instanceof ErrorApi
          ? { ...e.campos, general: e.detalle }
          : { general: "No fue posible registrar" },
      ),
  });

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    const faltantes: Record<string, string> = {};
    if (!nombre.trim()) faltantes.nombre = "El nombre es obligatorio";
    if (!descripcion.trim()) faltantes.descripcion = "La descripción es obligatoria";
    if (!origen) faltantes.origen = "Seleccione el origen de la idea";
    setErrores(faltantes);
    if (Object.keys(faltantes).length === 0) registrar.mutate();
  }

  return (
    <form className="tarjeta formulario" onSubmit={enviar} noValidate>
      <h1>Nueva iniciativa</h1>
      <p className="texto-secundario">
        Registro preliminar en el backlog. La ficha completa se llena en la etapa de estructuración.
      </p>

      <label>
        Nombre
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          maxLength={200}
          aria-invalid={!!errores.nombre}
        />
        {errores.nombre && <span className="mensaje-error">{errores.nombre}</span>}
      </label>
      <label>
        Descripción breve
        <textarea
          rows={4}
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          aria-invalid={!!errores.descripcion}
        />
        {errores.descripcion && <span className="mensaje-error">{errores.descripcion}</span>}
      </label>
      <label>
        Origen de la idea
        <select
          value={origen}
          onChange={(e) => setOrigen(e.target.value as OrigenIniciativa)}
          aria-invalid={!!errores.origen}
        >
          <option value="">Seleccione…</option>
          {ORIGENES.map((o) => (
            <option key={o} value={o}>
              {NOMBRES_ORIGENES[o]}
            </option>
          ))}
        </select>
        {errores.origen && <span className="mensaje-error">{errores.origen}</span>}
      </label>

      <h2>Evaluadores por dimensión</h2>
      {puedeAsignar && marco.data && usuarios.data ? (
        <>
          <p className="texto-secundario">
            Opcional al registrar. Antes de iniciar la evaluación, cada dimensión necesita al menos
            un evaluador. ★ = rol sugerido.
          </p>
          <SelectorEvaluadores
            dimensiones={marco.data.dimensiones}
            usuarios={usuarios.data}
            valor={asignaciones}
            onChange={setAsignaciones}
          />
          {errores.asignaciones && <p className="mensaje-error">{errores.asignaciones}</p>}
        </>
      ) : (
        <p className="texto-secundario">
          {puedeAsignar ? "Cargando…" : "El Product Manager asignará los evaluadores."}
        </p>
      )}

      {errores.general && !Object.keys(errores).some((k) => k !== "general") && (
        <p role="alert" className="mensaje-error">
          {errores.general}
        </p>
      )}
      <div className="acciones">
        <button type="button" className="secundario" onClick={() => navegar("/iniciativas")}>
          Cancelar
        </button>
        <button type="submit" disabled={registrar.isPending}>
          {registrar.isPending ? "Registrando…" : "Registrar iniciativa"}
        </button>
      </div>
    </form>
  );
}
