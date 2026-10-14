import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { truncar } from "../utilidades/formato";

interface Props {
  puntajes: Record<string, number>;
  nombres: Record<string, string>;
  /** Anillos de referencia, p. ej. umbral débil (3) y de GO (4). */
  referencias: { valor: number; etiqueta: string }[];
}

// Colores desde los tokens del tema (claro/oscuro); los atributos SVG no admiten var().
function token(nombre: string, respaldo: string): string {
  if (typeof window === "undefined") return respaldo;
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim() || respaldo;
}

/** Radar de las 6 dimensiones en escala 1–5 (HU4, escenario 7). Una sola serie: sin leyenda. */
export function RadarDimensiones({ puntajes, nombres, referencias }: Props) {
  const primario = token("--primario", "#1f4f8f");
  const secundario = token("--texto-secundario", "#5b6573");
  const borde = token("--borde", "#dde1e7");
  const datos = Object.entries(puntajes).map(([codigo, puntaje]) => ({
    codigo,
    nombre: nombres[codigo] ?? codigo,
    puntaje,
    ...Object.fromEntries(referencias.map((r) => [`ref${r.valor}`, r.valor])),
  }));

  return (
    <figure className="radar" aria-label="Gráfico radar de los puntajes por dimensión">
      <ResponsiveContainer width="100%" height={360}>
        <RadarChart data={datos} outerRadius="80%">
          <PolarGrid stroke={borde} />
          <PolarAngleAxis dataKey="codigo" tick={{ fill: secundario, fontSize: 13 }} />
          <PolarRadiusAxis
            domain={[0, 5]}
            tickCount={6}
            // Entre los dos primeros ejes, para no tapar sus etiquetas.
            angle={60}
            tickFormatter={(v: number) => (v === 0 ? "" : String(v))}
            tick={{ fill: secundario, fontSize: 11 }}
            axisLine={false}
          />
          {referencias.map((r) => (
            <Radar
              key={r.valor}
              dataKey={`ref${r.valor}`}
              stroke={secundario}
              strokeDasharray="4 4"
              strokeWidth={1}
              fill="none"
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />
          ))}
          <Radar
            dataKey="puntaje"
            stroke={primario}
            strokeWidth={2}
            fill={primario}
            fillOpacity={0.15}
            dot={{ r: 4, fill: primario, strokeWidth: 0 }}
            activeDot={{ r: 6 }}
            isAnimationActive={false}
          />
          <Tooltip
            content={({ active, payload }) => {
              const punto = payload?.find((p) => p.dataKey === "puntaje");
              if (!active || !punto) return null;
              const fila = punto.payload as (typeof datos)[number];
              return (
                <div className="tooltip-grafico">
                  <strong>
                    {fila.codigo} · {fila.nombre}
                  </strong>
                  <span>Puntaje {truncar(fila.puntaje)}</span>
                </div>
              );
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
      <figcaption className="texto-secundario">
        Líneas punteadas: {referencias.map((r) => `${r.valor} (${r.etiqueta})`).join(" y ")}.
      </figcaption>
    </figure>
  );
}
