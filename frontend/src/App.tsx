import { Route, Routes } from "react-router-dom";

import { Diseno } from "./componentes/Diseno";
import { RutaProtegida } from "./estado/sesion";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { Marco } from "./paginas/Marco";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RutaProtegida>
            <Diseno />
          </RutaProtegida>
        }
      >
        <Route index element={<Inicio />} />
        <Route path="marco" element={<Marco />} />
        <Route path="*" element={<p className="tarjeta">Página no encontrada.</p>} />
      </Route>
    </Routes>
  );
}
