import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Usuario } from "../src/api/tipos";
import { App } from "../src/App";
import { INICIATIVA, MARCO, MIEMBRO, PM, TECNICO } from "./datos";
import { renderizar, simularFetch, type Simulador } from "./utilidades";

afterEach(() => vi.unstubAllGlobals());

function servidor(usuario: Usuario, extra: Simulador = () => [404, {}]): Simulador {
  return (metodo, ruta, cuerpo) => {
    if (ruta === "/auth/yo") return [200, usuario];
    if (ruta === "/marco/vigente") return [200, MARCO];
    if (ruta === "/usuarios") return [200, [PM, TECNICO]];
    return extra(metodo, ruta, cuerpo);
  };
}

test("el backlog lista las iniciativas y envía los filtros", async () => {
  const llamadas = simularFetch(
    servidor(PM, (_, ruta) => (ruta.startsWith("/iniciativas") ? [200, [INICIATIVA]] : [404, {}])),
  );
  renderizar(<App />, "/iniciativas");

  const fila = (await screen.findByText("INI-2026-0001")).closest("tr")!;
  expect(within(fila).getByRole("link", { name: "Portal de reclamos" })).toBeInTheDocument();
  expect(within(fila).getByText("Identificada")).toBeInTheDocument();

  await userEvent.selectOptions(screen.getByLabelText("Origen"), "SOCIOS");

  expect(llamadas.some((l) => l.ruta === "/iniciativas?origen=SOCIOS")).toBe(true);
});

test("validación local de campos obligatorios", async () => {
  const llamadas = simularFetch(servidor(PM));
  renderizar(<App />, "/iniciativas/nueva");

  await userEvent.click(await screen.findByRole("button", { name: "Registrar iniciativa" }));

  expect(screen.getByText("El nombre es obligatorio")).toBeInTheDocument();
  expect(screen.getByText("Seleccione el origen de la idea")).toBeInTheDocument();
  expect(llamadas.some((l) => l.metodo === "POST")).toBe(false);
});

test("el PM registra con evaluadores y ve el aviso de duplicado", async () => {
  let enviado: unknown;
  simularFetch(
    servidor(PM, (metodo, ruta, cuerpo) => {
      if (metodo === "POST" && ruta === "/iniciativas") {
        enviado = cuerpo;
        return [201, INICIATIVA];
      }
      if (ruta === "/iniciativas/i1") {
        const asignaciones = [
          {
            dimension: "TEC",
            usuario: { id: TECNICO.id, nombre: TECNICO.nombre },
            origen: "MANUAL",
          },
        ];
        const posible_duplicado_de = {
          id: null,
          codigo: "INI-2026-0000",
          nombre: null,
          similitud: 0.82,
        };
        return [200, { ...INICIATIVA, asignaciones, posible_duplicado_de }];
      }
      return [404, {}];
    }),
  );
  renderizar(<App />, "/iniciativas/nueva");

  await userEvent.type(await screen.findByLabelText("Nombre"), "Portal de reclamos");
  await userEvent.type(screen.getByLabelText("Descripción breve"), "Autogestión de reclamos");
  await userEvent.selectOptions(screen.getByLabelText("Origen de la idea"), "CLIENTES");
  const agregarTecnico = await screen.findByLabelText("Agregar evaluador de Técnica");
  // El usuario con el rol sugerido aparece primero y marcado con ★.
  expect(within(agregarTecnico).getAllByRole("option")[1]).toHaveTextContent("Tomás Técnico ★");
  await userEvent.selectOptions(agregarTecnico, TECNICO.id);
  await userEvent.click(screen.getByRole("button", { name: "Registrar iniciativa" }));

  expect(
    await screen.findByText("Iniciativa INI-2026-0001 registrada en el backlog."),
  ).toBeVisible();
  expect(enviado).toEqual({
    nombre: "Portal de reclamos",
    descripcion: "Autogestión de reclamos",
    origen: "CLIENTES",
    asignaciones: [{ dimension: "TEC", usuario_id: TECNICO.id }],
  });
  expect(screen.getByRole("status")).toHaveTextContent("Posible duplicado de INI-2026-0000");
  expect(screen.getByRole("status")).toHaveTextContent("Consulte con el Product Manager");
  const filaTecnica = screen.getByRole("rowheader", { name: "TEC · Técnica" }).closest("tr")!;
  expect(within(filaTecnica).getByText("Tomás Técnico")).toBeInTheDocument();
});

test("un miembro registra sin asignar evaluadores", async () => {
  simularFetch(servidor(MIEMBRO));
  renderizar(<App />, "/iniciativas/nueva");

  expect(await screen.findByText("El Product Manager asignará los evaluadores.")).toBeVisible();
  expect(screen.queryByLabelText("Agregar evaluador de Técnica")).not.toBeInTheDocument();
});

test("detalle inexistente o sin acceso muestra un mensaje", async () => {
  simularFetch(servidor(MIEMBRO, () => [404, { detalle: "Iniciativa no encontrada" }]));
  renderizar(<App />, "/iniciativas/otra");

  expect(
    await screen.findByText("La iniciativa no existe o no tiene acceso a ella."),
  ).toBeInTheDocument();
});
