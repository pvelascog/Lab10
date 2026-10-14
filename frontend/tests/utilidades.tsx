import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import { ProveedorSesion } from "../src/estado/sesion";

/** Respuesta simulada de fetch según el método y la ruta. */
export type Simulador = (metodo: string, ruta: string, cuerpo?: unknown) => [number, unknown];

export function simularFetch(simulador: Simulador) {
  const llamadas: { metodo: string; ruta: string; cabeceras: Record<string, string> }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      const metodo = init.method ?? "GET";
      const ruta = url.replace("/api/v1", "");
      llamadas.push({ metodo, ruta, cabeceras: (init.headers ?? {}) as Record<string, string> });
      const [estado, datos] = simulador(
        metodo,
        ruta,
        init.body ? JSON.parse(String(init.body)) : undefined,
      );
      return new Response(estado === 204 ? null : JSON.stringify(datos), { status: estado });
    }),
  );
  return llamadas;
}

export function renderizar(elemento: ReactElement, ruta = "/") {
  const clienteConsultas = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={clienteConsultas}>
      <MemoryRouter initialEntries={[ruta]}>
        <ProveedorSesion>{elemento}</ProveedorSesion>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
