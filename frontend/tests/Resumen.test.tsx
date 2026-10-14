import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { ResultadoEvaluacion, Usuario } from "../src/api/tipos";
import { App } from "../src/App";
import { INICIATIVA, MARCO, PM, TECNICO, dimensionEval, evaluacion } from "./datos";
import { renderizar, simularFetch, type Simulador } from "./utilidades";

afterEach(() => vi.unstubAllGlobals());

const RESULTADO: ResultadoEvaluacion = {
  evaluacion_id: "e1",
  iniciativa: {
    id: "i1",
    codigo: "INI-2026-0001",
    nombre: "Portal de reclamos",
    estado: "CONSOLIDADA",
  },
  version_marco: "3.0",
  score_total: 3.999,
  puntajes_dimension: { MER: 4.5, COM: 4.2, FIN: 2.8, TEC: 4.4, CMP: 4.1, ECO: 4.0 },
  puntajes_criterio: { "MER-01": 4.5 },
  pesos: { MER: 1 / 6, COM: 1 / 6, FIN: 1 / 6, TEC: 1 / 6, CMP: 1 / 6, ECO: 1 / 6 },
  umbrales: { critico: 2, validar: 2.5, debil: 3, score_go: 4, score_iterar: 3, score_validar: 2 },
  nombres_dimension: {
    MER: "Mercado",
    COM: "Comercial",
    FIN: "Financiera",
    TEC: "Técnica",
    CMP: "Competencia",
    ECO: "Ecosistema",
  },
  resultado: "ITERAR",
  regla: "R3",
  regla_aplicada: "R3: dimensión FIN = 2.80 < 3.0",
  dimensiones_implicadas: ["FIN"],
  fortalezas: ["Mercado (4.50)"],
  debilidades: ["Financiera (2.80)"],
  riesgos: [],
  supuestos_criticos: ["Los clientes prefieren la autogestión"],
  borrador_ia: false,
  consolidado_en: "2026-10-14T15:00:00Z",
  consolidado_por: { id: PM.id, nombre: PM.nombre },
  puede_editar: true,
};

function servidor(usuario: Usuario, extra?: Simulador): Simulador {
  return (metodo, ruta, cuerpo) => {
    if (ruta === "/auth/yo") return [200, usuario];
    if (ruta === "/marco/vigente") return [200, MARCO];
    const r = extra?.(metodo, ruta, cuerpo);
    if (r) return r;
    if (ruta === "/evaluaciones/e1/resultado") return [200, RESULTADO];
    return [404, {}];
  };
}

test("muestra el resultado, la regla y el score truncado", async () => {
  simularFetch(servidor(PM));
  renderizar(<App />, "/evaluaciones/e1/resumen");

  expect(await screen.findByText("ITERAR · Desarrollar")).toBeInTheDocument();
  // 3.999 se muestra 3.99: nunca aparenta alcanzar el umbral de GO (4.00).
  expect(screen.getByText("3.99")).toBeInTheDocument();
  expect(screen.getByText("R3: dimensión FIN = 2.80 < 3.0")).toBeInTheDocument();
  expect(screen.getByText(/La decisión final corresponde al Comité/)).toBeInTheDocument();
});

test("la tabla de dimensiones marca el balance con texto, no solo color", async () => {
  simularFetch(servidor(PM));
  renderizar(<App />, "/evaluaciones/e1/resumen");

  const fila = (await screen.findByRole("rowheader", { name: "FIN · Financiera" })).closest("tr")!;
  expect(within(fila).getByText("2.80")).toBeInTheDocument();
  expect(within(fila).getByText("Débil")).toBeInTheDocument();
  expect(within(fila).getByText("16.66 %")).toBeInTheDocument();
  const eco = screen.getByRole("rowheader", { name: "ECO · Ecosistema" }).closest("tr")!;
  expect(within(eco).getByText("Aceptable")).toBeInTheDocument();
});

test("el PM edita una lista del resumen", async () => {
  let cuerpo: unknown;
  simularFetch(
    servidor(PM, (metodo, ruta, c) => {
      if (metodo === "PATCH" && ruta === "/evaluaciones/e1/resultado") {
        cuerpo = c;
        return [200, { ...RESULTADO, riesgos: ["Dependencia de Nexopus"] }];
      }
      return undefined as never;
    }),
  );
  renderizar(<App />, "/evaluaciones/e1/resumen");

  const riesgos = await screen.findByRole("article", { name: "Riesgos" });
  expect(within(riesgos).getByText("Sin elementos.")).toBeInTheDocument();
  await userEvent.click(within(riesgos).getByRole("button", { name: "Editar" }));
  await userEvent.type(within(riesgos).getByLabelText("Editar riesgos"), "Dependencia de Nexopus");
  await userEvent.click(within(riesgos).getByRole("button", { name: "Guardar" }));

  expect(await within(riesgos).findByText("Dependencia de Nexopus")).toBeInTheDocument();
  expect(cuerpo).toEqual({ riesgos: ["Dependencia de Nexopus"] });
});

test("quien no gestiona ve el resumen sin editar", async () => {
  simularFetch(
    servidor(TECNICO, (_, ruta) =>
      ruta === "/evaluaciones/e1/resultado"
        ? [200, { ...RESULTADO, puede_editar: false }]
        : (undefined as never),
    ),
  );
  renderizar(<App />, "/evaluaciones/e1/resumen");

  expect(await screen.findByText("ITERAR · Desarrollar")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
});

test("consolidar se habilita sin pendientes y lleva al resumen", async () => {
  const sinPendientes = evaluacion([dimensionEval({ soy_evaluador: false })], {
    puede_gestionar: true,
  });
  const llamadas = simularFetch(
    servidor(PM, (metodo, ruta) => {
      if (metodo === "POST" && ruta === "/iniciativas/i1/transiciones") return [200, INICIATIVA];
      if (ruta === "/evaluaciones/e1") return [200, sinPendientes];
      return undefined as never;
    }),
  );
  renderizar(<App />, "/evaluaciones/e1");

  await userEvent.click(await screen.findByRole("button", { name: "Consolidar evaluación" }));

  expect(await screen.findByText("ITERAR · Desarrollar")).toBeInTheDocument();
  expect(
    llamadas.some((l) => l.metodo === "POST" && l.ruta === "/iniciativas/i1/transiciones"),
  ).toBe(true);
});

test("con pendientes no se puede consolidar", async () => {
  const conPendientes = evaluacion([dimensionEval({ soy_evaluador: false })], {
    puede_gestionar: true,
    pendientes: { "MER-01": "Sin calificaciones enviadas" },
  });
  simularFetch(
    servidor(PM, (_, ruta) =>
      ruta === "/evaluaciones/e1" ? [200, conPendientes] : (undefined as never),
    ),
  );
  renderizar(<App />, "/evaluaciones/e1");

  expect(await screen.findByRole("button", { name: "Consolidar evaluación" })).toBeDisabled();
});

test("el backlog muestra el resultado y lo filtra", async () => {
  const llamadas = simularFetch(
    servidor(PM, (_, ruta) =>
      ruta.startsWith("/iniciativas")
        ? [200, [{ ...INICIATIVA, resultado: "GO" }]]
        : (undefined as never),
    ),
  );
  renderizar(<App />, "/iniciativas");

  const fila = (await screen.findByText("INI-2026-0001")).closest("tr")!;
  expect(within(fila).getByText("GO")).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText("Resultado"), "NO_GO");

  expect(llamadas.some((l) => l.ruta === "/iniciativas?resultado=NO_GO")).toBe(true);
});
