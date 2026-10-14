import { NOMBRES_ROLES } from "../api/tipos";
import { useSesion } from "../estado/sesion";

export function Inicio() {
  const { usuario } = useSesion();
  if (!usuario) return null;

  return (
    <section className="tarjeta">
      <h1>Hola, {usuario.nombre}</h1>
      <p>
        Este sistema evalúa iniciativas de producto con el Marco de Viabilidad NEPXA v3.0: seis
        dimensiones, 28 criterios en escala de 1 a 5 y un resultado GO, ITERAR, VALIDAR o NO-GO.
      </p>
      <p className="texto-secundario">
        Sus roles: {usuario.roles.map((r) => NOMBRES_ROLES[r]).join(", ") || "ninguno asignado"}
      </p>
    </section>
  );
}
