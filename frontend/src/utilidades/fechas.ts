const FORMATO = new Intl.DateTimeFormat("es", { dateStyle: "medium" });

export function formatearFecha(iso: string): string {
  return FORMATO.format(new Date(iso));
}
