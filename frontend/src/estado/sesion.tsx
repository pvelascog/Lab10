import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { api, ErrorApi } from "../api/cliente";
import type { CodigoRol, SesionIniciada, Usuario } from "../api/tipos";

interface ContextoSesion {
  usuario: Usuario | null;
  cargando: boolean;
  iniciarSesion: (correo: string, contrasena: string) => Promise<Usuario>;
  cerrarSesion: () => Promise<void>;
  tieneRol: (...roles: CodigoRol[]) => boolean;
}

const Contexto = createContext<ContextoSesion | null>(null);
const CLAVE_YO = ["sesion", "yo"];

async function consultarYo(): Promise<Usuario | null> {
  try {
    return await api<Usuario>("/auth/yo");
  } catch (error) {
    if (error instanceof ErrorApi && error.estado === 401) return null;
    throw error;
  }
}

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const clienteConsultas = useQueryClient();
  const yo = useQuery({ queryKey: CLAVE_YO, queryFn: consultarYo, retry: false });

  const login = useMutation({
    mutationFn: (datos: { correo: string; contrasena: string }) =>
      api<SesionIniciada>("/auth/login", { metodo: "POST", cuerpo: datos }),
    onSuccess: (sesion) => clienteConsultas.setQueryData(CLAVE_YO, sesion.usuario),
  });

  const logout = useMutation({
    mutationFn: () => api<void>("/auth/logout", { metodo: "POST" }),
    onSettled: () => {
      // Descarta los datos del usuario anterior sin volver a consultar la sesión.
      clienteConsultas.removeQueries({ predicate: (q) => q.queryKey[0] !== CLAVE_YO[0] });
      clienteConsultas.setQueryData(CLAVE_YO, null);
    },
  });

  const usuario = yo.data ?? null;
  const valor: ContextoSesion = {
    usuario,
    cargando: yo.isPending,
    iniciarSesion: async (correo, contrasena) =>
      (await login.mutateAsync({ correo, contrasena })).usuario,
    cerrarSesion: async () => {
      await logout.mutateAsync();
    },
    tieneRol: (...roles) => !!usuario && usuario.roles.some((r) => roles.includes(r)),
  };

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion(): ContextoSesion {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useSesion debe usarse dentro de ProveedorSesion");
  return contexto;
}

/** Exige sesión iniciada y, si se indican, al menos uno de los roles. */
export function RutaProtegida({ roles, children }: { roles?: CodigoRol[]; children: ReactNode }) {
  const { usuario, cargando, tieneRol } = useSesion();
  const ubicacion = useLocation();

  if (cargando) return <p className="cargando">Cargando…</p>;
  if (!usuario) return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  if (roles && !tieneRol(...roles)) {
    return (
      <section className="tarjeta">
        <h2>Sin permisos</h2>
        <p>Su rol no permite acceder a esta sección.</p>
      </section>
    );
  }
  return <>{children}</>;
}
