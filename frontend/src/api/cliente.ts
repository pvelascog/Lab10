// Cliente HTTP de la API. La sesión viaja en una cookie HttpOnly; en los métodos que
// modifican datos se reenvía el token CSRF (cookie legible "csrf") en la cabecera X-CSRF-Token.

export const BASE_API = "/api/v1";
const METODOS_SEGUROS = new Set(["GET", "HEAD", "OPTIONS"]);

export class ErrorApi extends Error {
  constructor(
    readonly estado: number,
    readonly detalle: string,
    readonly campos: Record<string, string> = {},
  ) {
    super(detalle);
    this.name = "ErrorApi";
  }
}

export function leerCookie(nombre: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((par) => par.startsWith(`${nombre}=`))
    ?.slice(nombre.length + 1);
}

interface Opciones {
  metodo?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  cuerpo?: unknown;
  parametros?: Record<string, string | undefined>;
}

export async function api<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const metodo = opciones.metodo ?? "GET";
  const cabeceras: Record<string, string> = { Accept: "application/json" };
  if (opciones.cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
  if (!METODOS_SEGUROS.has(metodo)) {
    const csrf = leerCookie("csrf");
    if (csrf) cabeceras["X-CSRF-Token"] = csrf;
  }

  const consulta = new URLSearchParams(
    Object.entries(opciones.parametros ?? {}).filter((par): par is [string, string] => !!par[1]),
  ).toString();

  const respuesta = await fetch(`${BASE_API}${ruta}${consulta ? `?${consulta}` : ""}`, {
    method: metodo,
    headers: cabeceras,
    credentials: "same-origin",
    body: opciones.cuerpo === undefined ? undefined : JSON.stringify(opciones.cuerpo),
  });

  if (respuesta.status === 204) return undefined as T;
  const datos: unknown = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const error = datos as { detalle?: string; campos?: Record<string, string> };
    throw new ErrorApi(
      respuesta.status,
      error.detalle ?? "Ocurrió un error inesperado",
      error.campos ?? {},
    );
  }
  return datos as T;
}
