import { useQuery } from "@tanstack/react-query";

import { api } from "./cliente";
import type { Usuario, VersionMarco } from "./tipos";

export function useMarcoVigente() {
  return useQuery({
    queryKey: ["marco", "vigente"],
    queryFn: () => api<VersionMarco>("/marco/vigente"),
    staleTime: Infinity,
  });
}

/** Lista de usuarios para asignar evaluadores (solo PM y administrador). */
export function useUsuarios(habilitado: boolean) {
  return useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api<Usuario[]>("/usuarios"),
    enabled: habilitado,
  });
}
