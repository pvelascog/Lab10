import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Usuario } from "../src/api/tipos";
import { App } from "../src/App";
import { renderizar, simularFetch } from "./utilidades";

const ANA: Usuario = {
  id: "1",
  nombre: "Ana",
  correo: "ana@nepxa.test",
  activo: true,
  roles: ["PM", "COMITE"],
};

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

test("sin sesión redirige al inicio de sesión", async () => {
  simularFetch(() => [401, { detalle: "Se requiere iniciar sesión" }]);

  renderizar(<App />, "/marco");

  expect(await screen.findByRole("button", { name: "Iniciar sesión" })).toBeInTheDocument();
});

test("iniciar sesión muestra el diseño con el nombre y los roles", async () => {
  let conSesion = false;
  simularFetch((metodo, ruta) => {
    if (ruta === "/auth/yo") return conSesion ? [200, ANA] : [401, { detalle: "x" }];
    if (metodo === "POST" && ruta === "/auth/login") {
      conSesion = true;
      return [200, { usuario: ANA, csrf: "abc" }];
    }
    return [404, {}];
  });
  renderizar(<App />);

  await userEvent.type(await screen.findByLabelText("Correo"), "ana@nepxa.test");
  await userEvent.type(screen.getByLabelText("Contraseña"), "Contrasena-segura-123");
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  expect(await screen.findByRole("heading", { name: "Hola, Ana" })).toBeInTheDocument();
  expect(screen.getByText("Product Manager · Comité de Producto")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Marco NEPXA" })).toBeInTheDocument();
});

test("credenciales inválidas muestran el mensaje del servidor", async () => {
  simularFetch((_, ruta) =>
    ruta === "/auth/login"
      ? [401, { detalle: "Correo o contraseña incorrectos" }]
      : [401, { detalle: "x" }],
  );
  renderizar(<App />, "/login");

  await userEvent.type(await screen.findByLabelText("Correo"), "ana@nepxa.test");
  await userEvent.type(screen.getByLabelText("Contraseña"), "mala");
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Correo o contraseña incorrectos");
});

test("cerrar sesión vuelve al formulario de ingreso", async () => {
  let conSesion = true;
  simularFetch((metodo, ruta) => {
    if (metodo === "POST" && ruta === "/auth/logout") {
      conSesion = false;
      return [204, null];
    }
    if (ruta === "/auth/yo") return conSesion ? [200, ANA] : [401, { detalle: "x" }];
    return [404, {}];
  });
  renderizar(<App />);

  await userEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

  expect(await screen.findByRole("button", { name: "Iniciar sesión" })).toBeInTheDocument();
});
