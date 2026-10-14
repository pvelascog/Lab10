import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Evaluacion, Usuario } from "../src/api/tipos";
import { App } from "../src/App";
import { INICIATIVA, MARCO, PM, TECNICO, criterioEval, dimensionEval, evaluacion } from "./datos";
import { renderizar, simularFetch, type Simulador } from "./utilidades";

afterEach(() => vi.unstubAllGlobals());

function servidor(usuario: Usuario, inicial: Evaluacion, extra?: Simulador): Simulador {
  return (metodo, ruta, cuerpo) => {
    if (ruta === "/auth/yo") return [200, usuario];
    if (ruta === "/marco/vigente") return [200, MARCO];
    const r = extra?.(metodo, ruta, cuerpo);
    if (r) return r;
    if (ruta === "/evaluaciones/e1") return [200, inicial];
    return [404, {}];
  };
}

test("el evaluador califica a ciegas con nivel y justificación", async () => {
  let cuerpoEnviado: unknown;
  const inicial = evaluacion([dimensionEval()]);
  const calificada = evaluacion([
    dimensionEval({
      criterios: [
        criterioEval("MER-01", {
          mi_calificacion: {
            nivel: 4,
            justificacion: "Afecta a 3 áreas",
            fuente: null,
            origen: "HUMANA",
          },
        }),
        criterioEval("MER-02"),
      ],
    }),
  ]);
  simularFetch(
    servidor(TECNICO, inicial, (metodo, ruta, cuerpo) => {
      if (metodo === "PUT" && ruta === "/evaluaciones/e1/calificaciones/MER-01") {
        cuerpoEnviado = cuerpo;
        return [200, calificada];
      }
      return undefined as never;
    }),
  );
  renderizar(<App />, "/evaluaciones/e1");

  expect(await screen.findByText(/Calificación a ciegas/)).toBeInTheDocument();
  const tarjeta = screen.getByRole("heading", { name: /MER-01/ }).closest("article")!;
  const guardar = within(tarjeta).getByRole("button", { name: "Guardar calificación" });
  expect(guardar).toBeDisabled();
  await userEvent.click(within(tarjeta).getByLabelText(/Nivel 4 de MER-01/));
  await userEvent.type(
    within(tarjeta).getByLabelText("Justificación de MER-01"),
    "Afecta a 3 áreas",
  );
  await userEvent.click(guardar);

  expect(await within(tarjeta).findByText("Calificado: 4")).toBeInTheDocument();
  expect(cuerpoEnviado).toEqual({
    nivel: 4,
    justificacion: "Afecta a 3 áreas",
    fuente: null,
    usa_calculo: false,
  });
  expect(screen.getByRole("button", { name: "Enviar Mercado" })).toBeDisabled();
});

test("enviar la dimensión pide confirmación", async () => {
  const mia = { nivel: 3, justificacion: "x", fuente: null, origen: "HUMANA" as const };
  const pendiente = dimensionEval({ codigo: "COM", nombre: "Comercial" });
  const completa = dimensionEval({
    criterios: [
      criterioEval("MER-01", { mi_calificacion: mia }),
      criterioEval("MER-02", { mi_calificacion: mia }),
    ],
  });
  const llamadas = simularFetch(
    servidor(TECNICO, evaluacion([completa, pendiente]), (metodo, ruta) =>
      metodo === "POST" && ruta.endsWith("/enviar")
        ? [
            200,
            evaluacion([
              { ...completa, enviada_por_mi: true, ver_calificaciones: true },
              pendiente,
            ]),
          ]
        : (undefined as never),
    ),
  );
  renderizar(<App />, "/evaluaciones/e1");

  await userEvent.click(await screen.findByRole("button", { name: "Enviar Mercado" }));
  expect(llamadas.some((l) => l.ruta.endsWith("/enviar"))).toBe(false);
  await userEvent.click(screen.getByRole("button", { name: "Confirmar envío" }));

  expect(
    llamadas.some(
      (l) => l.metodo === "POST" && l.ruta === "/evaluaciones/e1/dimensiones/MER/enviar",
    ),
  ).toBe(true);
  expect(await screen.findAllByText("Su calificación:", { exact: false })).toHaveLength(2);
});

test("tras enviar ve las calificaciones, la divergencia y puede comentarla", async () => {
  const publicadas = [
    {
      nivel: 2,
      justificacion: "Solo opiniones",
      fuente: null,
      origen: "HUMANA" as const,
      evaluador: { id: "a", nombre: "Ana" },
    },
    {
      nivel: 4,
      justificacion: "Ventas en curso",
      fuente: "CRM",
      origen: "HUMANA" as const,
      evaluador: { id: "b", nombre: "Beto" },
    },
  ];
  const dim = dimensionEval({
    enviada_por_mi: true,
    ver_calificaciones: true,
    criterios: [
      criterioEval("MER-01", {
        mi_calificacion: {
          nivel: 2,
          justificacion: "Solo opiniones",
          fuente: null,
          origen: "HUMANA",
        },
        calificaciones: publicadas,
        promedio: 3,
        divergencia: true,
        comentarios: [],
      }),
    ],
  });
  let comentario: unknown;
  simularFetch(
    servidor(TECNICO, evaluacion([dim]), (metodo, ruta, cuerpo) => {
      if (metodo === "POST" && ruta.endsWith("/comentarios")) {
        comentario = cuerpo;
        return [201, {}];
      }
      return undefined as never;
    }),
  );
  renderizar(<App />, "/evaluaciones/e1");

  const tarjeta = (await screen.findByRole("heading", { name: /MER-01/ })).closest("article")!;
  expect(within(tarjeta).getByText("Divergencia")).toBeInTheDocument();
  expect(within(tarjeta).getByText(/promedio 3.00/)).toBeInTheDocument();
  expect(within(tarjeta).getByText("Beto:")).toBeInTheDocument();
  expect(within(tarjeta).getByText(/Fuente: CRM/)).toBeInTheDocument();
  await userEvent.type(
    within(tarjeta).getByLabelText("Comentario sobre la divergencia de MER-01"),
    "Ana no consideró el CRM",
  );
  await userEvent.click(within(tarjeta).getByRole("button", { name: "Comentar" }));

  await vi.waitFor(() => expect(comentario).toEqual({ texto: "Ana no consideró el CRM" }));
});

test("el PM ve el avance por evaluador y los pendientes", async () => {
  const supervisada = dimensionEval({
    soy_evaluador: false,
    ver_calificaciones: true,
    evaluadores: [
      { usuario: { id: "a", nombre: "Ana" }, calificados: 2, enviado: true },
      { usuario: { id: "b", nombre: "Beto" }, calificados: 1, enviado: false },
    ],
  });
  simularFetch(
    servidor(
      PM,
      evaluacion([supervisada], {
        puede_gestionar: true,
        pendientes: {
          "MER-01": "Divergencia sin comentar",
          "MER-02": "Sin calificaciones enviadas",
        },
      }),
    ),
  );
  renderizar(<App />, "/evaluaciones/e1");

  const avance = await screen.findByRole("region", { name: "Avance de la evaluación" });
  expect(within(avance).getByText("Ana: enviada")).toBeInTheDocument();
  expect(within(avance).getByText("Beto: 1/2")).toBeInTheDocument();
  expect(within(avance).getByText("2 criterios pendientes para consolidar.")).toBeInTheDocument();
  expect(within(avance).getByText("MER-01")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Guardar calificación" })).not.toBeInTheDocument();
});

test("iniciar la evaluación sin evaluadores muestra lo que falta", async () => {
  const estructurada = {
    ...INICIATIVA,
    estado: "ESTRUCTURADA" as const,
    pm: { id: PM.id, nombre: PM.nombre },
  };
  simularFetch((metodo, ruta) => {
    if (ruta === "/auth/yo") return [200, PM];
    if (ruta === "/marco/vigente") return [200, MARCO];
    if (metodo === "POST" && ruta.endsWith("/transiciones"))
      return [
        422,
        {
          detalle: "La iniciativa no cumple las condiciones para pasar a «En evaluación»",
          campos: { TEC: "Asigne al menos un evaluador para Técnica" },
        },
      ];
    if (ruta === "/iniciativas/i1") return [200, estructurada];
    return [404, {}];
  });
  renderizar(<App />, "/iniciativas/i1");

  await userEvent.click(await screen.findByRole("button", { name: "Iniciar evaluación" }));

  const alerta = await screen.findByRole("alert");
  expect(alerta).toHaveTextContent("Asigne al menos un evaluador para Técnica");
});
