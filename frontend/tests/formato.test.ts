import { formatearPorcentaje, truncar } from "../src/utilidades/formato";

test("trunca sin redondear para no cruzar umbrales", () => {
  expect(truncar(3.999)).toBe("3.99");
  expect(truncar(4.1667)).toBe("4.16");
  expect(truncar(2)).toBe("2.00");
  expect(truncar(0.29 * 100)).toBe("29.00");
});

test("formatea pesos como porcentaje", () => {
  expect(formatearPorcentaje(1 / 6)).toBe("16.66 %");
  expect(formatearPorcentaje(0.25)).toBe("25.00 %");
});
