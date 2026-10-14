import "@testing-library/jest-dom/vitest";

// jsdom no implementa ResizeObserver, que usa el contenedor adaptable de Recharts.
class ResizeObserverPrueba {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverPrueba as unknown as typeof ResizeObserver;
