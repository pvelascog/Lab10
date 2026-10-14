import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { App } from "../src/App";

test("muestra el título de la aplicación", () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  expect(
    screen.getByRole("heading", { name: "Validador de Viabilidad de Productos" }),
  ).toBeInTheDocument();
});
