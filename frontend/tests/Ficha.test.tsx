import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { IniciativaDetalle, Usuario } from "../src/api/tipos";
import { App } from "../src/App";
import { INICIATIVA, MIEMBRO, MARCO, PM, TECNICO } from "./datos";
import { renderizar, simularFetch, type Simulador } from "./utilidades";

afterEach(() => vi.unstubAllGlobals());

const CALCULOS = {
  roi: 150,
  nivel_roi: 5,
  meses_recuperacion: 12,
  nivel_recuperacion: 4,
  faltantes: [],
};

function servidor(usuario: Usuario, iniciativa: IniciativaDetalle, extra?: Simulador): Simulador {
  return (metodo, ruta, cuerpo) => {
    if (ruta === "/auth/yo") return [200, usuario];
    if (ruta === "/marco/vigente") return [200, MARCO];
    if (ruta === "/usuarios") return [200, [PM, TECNICO]];
    if (ruta === "/iniciativas/i1/calculos-financieros") return [200, CALCULOS];
    const respuesta = extra?.(metodo, ruta, cuerpo);
    if (respuesta) return respuesta;
    if (ruta === "/iniciativas/i1") return [200, iniciativa];
    return [404, {}];
  };
}

test("muestra la propuesta de niveles financieros con la rúbrica", async () => {
  simularFetch(servidor(PM, INICIATIVA));
  renderizar(<App />, "/iniciativas/i1/ficha");

  const calculos = await screen.findByRole("region", {
    name: "Propuesta para los criterios financieros",
  });
  expect(await within(calculos).findByText(/ROI 150.00 %/)).toBeInTheDocument();
  expect(within(calculos).getByText("(> 100 %)")).toBeInTheDocument();
  expect(within(calculos).getByText(/12.0 meses/)).toBeInTheDocument();
  expect(within(calculos).getByText("(6–12)")).toBeInTheDocument();
});

test("al estructurar con la ficha incompleta lista los faltantes", async () => {
  const llamadas = simularFetch(
    servidor(PM, INICIATIVA, (metodo, ruta) => {
      if (metodo === "PATCH") return [200, INICIATIVA];
      if (metodo === "POST" && ruta.endsWith("/transiciones"))
        return [
          422,
          {
            detalle: "La iniciativa no cumple las condiciones para pasar a «Estructurada»",
            campos: { pm_id: "Asigne un Product Manager", segmento: "Obligatorio" },
          },
        ];
      return undefined as never;
    }),
  );
  renderizar(<App />, "/iniciativas/i1/ficha");

  await userEvent.type(await screen.findByLabelText(/^Problema/), "Llamadas al call center");
  await userEvent.type(screen.getByLabelText("Supuesto 1"), "Prefieren autogestión");
  await userEvent.click(screen.getByRole("button", { name: "Guardar y marcar como estructurada" }));

  const alerta = await screen.findByRole("alert");
  expect(alerta).toHaveTextContent("no cumple las condiciones");
  expect(within(alerta).getByText("Product Manager")).toBeInTheDocument();
  expect(within(alerta).getByText("Segmento de cliente")).toBeInTheDocument();
  const patch = llamadas.find((l) => l.metodo === "PATCH");
  expect(patch?.ruta).toBe("/iniciativas/i1");
});

test("estructurar con éxito informa y cambia el estado", async () => {
  let actual: IniciativaDetalle = INICIATIVA;
  simularFetch(
    servidor(PM, INICIATIVA, (metodo, ruta) => {
      if (metodo === "PATCH") return [200, actual];
      if (metodo === "POST" && ruta.endsWith("/transiciones")) {
        actual = { ...INICIATIVA, estado: "ESTRUCTURADA" };
        return [200, actual];
      }
      if (ruta === "/iniciativas/i1") return [200, actual];
      return undefined as never;
    }),
  );
  renderizar(<App />, "/iniciativas/i1/ficha");

  await userEvent.click(
    await screen.findByRole("button", { name: "Guardar y marcar como estructurada" }),
  );

  expect(await screen.findByRole("status")).toHaveTextContent("quedó estructurada");
  expect(screen.getByText("Estructurada")).toBeInTheDocument();
});

test("un evaluador ve la ficha en solo lectura", async () => {
  simularFetch(servidor(TECNICO, INICIATIVA));
  renderizar(<App />, "/iniciativas/i1/ficha");

  expect(await screen.findByText(/Solo lectura/)).toBeInTheDocument();
  expect(screen.getByLabelText(/^Problema/)).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Guardar ficha" })).not.toBeInTheDocument();
});

test("el autor edita la ficha pero no elige PM ni estructura", async () => {
  const propia = { ...INICIATIVA, autor: { id: MIEMBRO.id, nombre: MIEMBRO.nombre } };
  simularFetch(servidor(MIEMBRO, propia));
  renderizar(<App />, "/iniciativas/i1/ficha");

  expect(await screen.findByRole("button", { name: "Guardar ficha" })).toBeEnabled();
  expect(screen.queryByLabelText("Product Manager")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Guardar y marcar como estructurada" }),
  ).not.toBeInTheDocument();
});
