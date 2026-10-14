/**
 * Trunca (no redondea) a la cantidad de decimales indicada, para que un valor nunca
 * aparente cruzar un umbral de decisión: 3.999 se muestra 3.99 (research.md D9).
 */
export function truncar(valor: number, decimales = 2): string {
  const factor = 10 ** decimales;
  // El pequeño margen corrige errores de coma flotante (p. ej. 0.29 * 100 = 28.999…).
  return (Math.trunc(valor * factor + 1e-9) / factor).toFixed(decimales);
}

export function formatearPorcentaje(fraccion: number, decimales = 2): string {
  return `${truncar(fraccion * 100, decimales)} %`;
}
