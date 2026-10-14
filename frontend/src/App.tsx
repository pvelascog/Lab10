import { Route, Routes } from "react-router-dom";

function Inicio() {
  return (
    <main>
      <h1>Validador de Viabilidad de Productos</h1>
      <p>Marco de Viabilidad NEPXA v3.0</p>
    </main>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="*" element={<Inicio />} />
    </Routes>
  );
}
