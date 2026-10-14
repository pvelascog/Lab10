import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { ErrorApi } from "../api/cliente";
import { useSesion } from "../estado/sesion";

export function Login() {
  const { usuario, iniciarSesion } = useSesion();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? "/";

  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (usuario) return <Navigate to={destino} replace />;

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await iniciarSesion(correo, contrasena);
      navegar(destino, { replace: true });
    } catch (e) {
      setError(e instanceof ErrorApi ? e.detalle : "No fue posible conectar con el servidor");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="pagina-login">
      <form className="tarjeta formulario-login" onSubmit={enviar} noValidate>
        <div>
          <h1>Validador de Viabilidad</h1>
          <p className="texto-secundario sin-margen">Marco de Viabilidad NEPXA v3.0</p>
        </div>

        <label>
          Correo
          <input
            type="email"
            autoComplete="username"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            autoComplete="current-password"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            required
          />
        </label>

        {error && (
          <p role="alert" className="mensaje-error">
            {error}
          </p>
        )}

        <button type="submit" disabled={enviando || !correo || !contrasena}>
          {enviando ? "Ingresando…" : "Iniciar sesión"}
        </button>
      </form>
    </main>
  );
}
