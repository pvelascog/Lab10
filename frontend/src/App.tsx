import { Route, Routes } from "react-router-dom";

import { Diseno } from "./componentes/Diseno";
import { RutaProtegida } from "./estado/sesion";
import { Backlog } from "./paginas/Backlog";
import { DetalleIniciativa } from "./paginas/DetalleIniciativa";
import { Evaluacion } from "./paginas/Evaluacion";
import { Ficha } from "./paginas/Ficha";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { Marco } from "./paginas/Marco";
import { NuevaIniciativa } from "./paginas/NuevaIniciativa";

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
        <Route path="iniciativas" element={<Backlog />} />
        <Route path="iniciativas/nueva" element={<NuevaIniciativa />} />
        <Route path="iniciativas/:id" element={<DetalleIniciativa />} />
        <Route path="iniciativas/:id/ficha" element={<Ficha />} />
        <Route path="evaluaciones/:id" element={<Evaluacion />} />
        <Route path="marco" element={<Marco />} />
        <Route path="*" element={<p className="tarjeta">Página no encontrada.</p>} />
      </Route>
    </Routes>
  );
}
