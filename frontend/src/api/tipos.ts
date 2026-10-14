// Tipos de la API (contracts/api.md).

export const ROLES = [
  "MIEMBRO",
  "PM",
  "LIDER_COMERCIAL",
  "LIDER_TECNICO",
  "LIDER_ESTRATEGIA",
  "COMITE",
  "ADMIN_MARCO",
] as const;
export type CodigoRol = (typeof ROLES)[number];

export const NOMBRES_ROLES: Record<CodigoRol, string> = {
  MIEMBRO: "Miembro",
  PM: "Product Manager",
  LIDER_COMERCIAL: "Líder Comercial",
  LIDER_TECNICO: "Líder Técnico",
  LIDER_ESTRATEGIA: "Líder de Estrategia",
  COMITE: "Comité de Producto",
  ADMIN_MARCO: "Administrador del marco",
};

export interface Usuario {
  id: string;
  nombre: string;
  correo: string;
  activo: boolean;
  roles: CodigoRol[];
}

export interface SesionIniciada {
  usuario: Usuario;
  csrf: string;
}

export interface Nivel {
  nivel: number;
  descripcion: string;
}

export interface Criterio {
  codigo: string;
  nombre: string;
  definicion: string;
  escala_original: number;
  calculable: "NO" | "ROI" | "RECUPERACION";
  niveles: Nivel[];
}

export interface Dimension {
  codigo: string;
  nombre: string;
  proposito: string;
  peso: number;
  rol_sugerido: CodigoRol | null;
  criterios: Criterio[];
}

export interface VersionMarco {
  id: string;
  numero: string;
  estado: "BORRADOR" | "VIGENTE" | "RETIRADA";
  umbrales: {
    critico: number;
    validar: number;
    debil: number;
    score_go: number;
    score_iterar: number;
    score_validar: number;
    divergencia: number;
  };
  dimensiones: Dimension[];
}
