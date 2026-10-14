import { NOMBRES_RESULTADOS, type Resultado } from "../api/tipos";

/** El resultado siempre lleva su texto: el color nunca es la única señal. */
export function ResultadoBadge({
  resultado,
  grande = false,
}: {
  resultado: Resultado;
  grande?: boolean;
}) {
  return (
    <span
      className={`resultado ${resultado === "NO_GO" ? "nogo" : resultado.toLowerCase()} ${grande ? "grande" : ""}`}
    >
      {grande ? NOMBRES_RESULTADOS[resultado] : NOMBRES_RESULTADOS[resultado].split(" · ")[0]}
    </span>
  );
}
