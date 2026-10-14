import { NavLink, Outlet } from "react-router-dom";

import { NOMBRES_ROLES, type CodigoRol } from "../api/tipos";
import { useSesion } from "../estado/sesion";

interface EntradaMenu {
  ruta: string;
  texto: string;
  roles?: CodigoRol[]; // sin roles: visible para todo usuario con sesión
}

// Las entradas se agregan a medida que se implementan las historias de usuario (tasks.md).
const MENU: EntradaMenu[] = [
  { ruta: "/", texto: "Inicio" },
  { ruta: "/marco", texto: "Marco NEPXA" },
];

export function Diseno() {
  const { usuario, tieneRol, cerrarSesion } = useSesion();
  const visibles = MENU.filter((e) => !e.roles || tieneRol(...e.roles));

  return (
    <div className="diseno">
      <header className="encabezado">
        <span className="marca">Validador de Viabilidad</span>
        <nav aria-label="Principal">
          {visibles.map((e) => (
            <NavLink key={e.ruta} to={e.ruta} end={e.ruta === "/"}>
              {e.texto}
            </NavLink>
          ))}
        </nav>
        {usuario && (
          <div className="usuario">
            <span>
              <strong>{usuario.nombre}</strong>
              <small>{usuario.roles.map((r) => NOMBRES_ROLES[r]).join(" · ") || "Sin rol"}</small>
            </span>
            <button type="button" className="secundario" onClick={() => void cerrarSesion()}>
              Cerrar sesión
            </button>
          </div>
        )}
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  );
}
