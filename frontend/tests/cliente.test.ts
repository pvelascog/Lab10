import { api, ErrorApi } from "../src/api/cliente";
import { simularFetch } from "./utilidades";

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

test("envía la cabecera CSRF solo en métodos que modifican datos", async () => {
  document.cookie = "csrf=token-123";
  const llamadas = simularFetch(() => [200, {}]);

  await api("/usuarios");
  await api("/usuarios", { metodo: "POST", cuerpo: { nombre: "Eva" } });

  expect(llamadas[0]?.cabeceras["X-CSRF-Token"]).toBeUndefined();
  expect(llamadas[1]?.cabeceras["X-CSRF-Token"]).toBe("token-123");
});

test("convierte los errores al formato de la API", async () => {
  simularFetch(() => [400, { detalle: "Datos inválidos", campos: { correo: "inválido" } }]);

  const error = await api("/usuarios", { metodo: "POST", cuerpo: {} }).catch((e: unknown) => e);

  expect(error).toBeInstanceOf(ErrorApi);
  expect(error).toMatchObject({ estado: 400, campos: { correo: "inválido" } });
});

test("omite parámetros vacíos de la consulta", async () => {
  const llamadas = simularFetch(() => [200, []]);

  await api("/usuarios", { parametros: { rol: "PM", otro: undefined } });

  expect(llamadas[0]?.ruta).toBe("/usuarios?rol=PM");
});
