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

export const ESTADOS = [
  "IDENTIFICADA",
  "ESTRUCTURADA",
  "EN_EVALUACION",
  "CONSOLIDADA",
  "EN_COMITE",
  "DECIDIDA",
  "EN_SEGUIMIENTO",
  "ARCHIVADA",
] as const;
export type EstadoIniciativa = (typeof ESTADOS)[number];

export const NOMBRES_ESTADOS: Record<EstadoIniciativa, string> = {
  IDENTIFICADA: "Identificada",
  ESTRUCTURADA: "Estructurada",
  EN_EVALUACION: "En evaluación",
  CONSOLIDADA: "Consolidada",
  EN_COMITE: "En comité",
  DECIDIDA: "Decidida",
  EN_SEGUIMIENTO: "En seguimiento",
  ARCHIVADA: "Archivada",
};

export const ORIGENES = [
  "CLIENTES",
  "EQUIPO_INTERNO",
  "MERCADO",
  "SOCIOS",
  "TENDENCIAS",
  "PORTAFOLIO",
  "INNOVACION_INTERNA",
] as const;
export type OrigenIniciativa = (typeof ORIGENES)[number];

export const NOMBRES_ORIGENES: Record<OrigenIniciativa, string> = {
  CLIENTES: "Clientes",
  EQUIPO_INTERNO: "Equipo interno",
  MERCADO: "Mercado",
  SOCIOS: "Socios",
  TENDENCIAS: "Tendencias",
  PORTAFOLIO: "Evolución del portafolio",
  INNOVACION_INTERNA: "Innovación interna",
};

export interface UsuarioBreve {
  id: string;
  nombre: string;
}

export interface IniciativaResumen {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  origen: OrigenIniciativa;
  estado: EstadoIniciativa;
  autor: UsuarioBreve;
  pm: UsuarioBreve | null;
  creado_en: string;
  resultado: Resultado | null;
}

export interface Asignacion {
  dimension: string;
  usuario: UsuarioBreve;
  origen: "MANUAL" | "SUGERIDA";
}

export interface IniciativaDetalle extends IniciativaResumen {
  problema: string | null;
  solucion_objetivo: string | null;
  segmento: string | null;
  propuesta_valor: string | null;
  supuestos_clave: string[];
  datos_disponibles: string | null;
  inversion_estimada: number | null;
  ingresos_esperados: number | null;
  flujo_mensual_neto: number | null;
  asignaciones: Asignacion[];
  posible_duplicado_de: {
    id: string | null;
    codigo: string;
    nombre: string | null;
    similitud: number;
  } | null;
  evaluacion_actual_id: string | null;
}

export interface CalculosFinancieros {
  roi: number | null;
  nivel_roi: number | null;
  meses_recuperacion: number | null;
  nivel_recuperacion: number | null;
  faltantes: string[];
}

/** Etiquetas de los campos de la ficha (también para los mensajes de faltantes). */
export const CAMPOS_FICHA: Record<string, string> = {
  pm_id: "Product Manager",
  problema: "Problema",
  solucion_objetivo: "Solución propuesta y objetivo",
  segmento: "Segmento de cliente",
  propuesta_valor: "Propuesta de valor diferencial",
  supuestos_clave: "Supuestos clave",
  datos_disponibles: "Datos disponibles",
  inversion_estimada: "Inversión estimada",
  ingresos_esperados: "Ingresos esperados",
  flujo_mensual_neto: "Flujo mensual neto",
};

// --- Evaluación (HU3) ------------------------------------------------------------------------

export type OrigenCalificacion =
  "HUMANA" | "IA_SUGERIDA" | "IA_CONFIRMADA" | "CALCULADA_CONFIRMADA";

export interface MiCalificacion {
  nivel: number;
  justificacion: string;
  fuente: string | null;
  origen: OrigenCalificacion;
}

export interface CalificacionPublicada extends MiCalificacion {
  evaluador: UsuarioBreve;
}

export interface Comentario {
  autor: UsuarioBreve;
  texto: string;
  creado_en: string;
}

export interface CriterioEvaluacion extends Criterio {
  propuesta_calculada: number | null;
  mi_calificacion: MiCalificacion | null;
  calificaciones: CalificacionPublicada[] | null;
  promedio: number | null;
  divergencia: boolean | null;
  comentarios: Comentario[] | null;
}

export interface DimensionEvaluacion {
  codigo: string;
  nombre: string;
  peso: number;
  soy_evaluador: boolean;
  enviada_por_mi: boolean;
  ver_calificaciones: boolean;
  evaluadores: { usuario: UsuarioBreve; calificados: number; enviado: boolean }[];
  criterios: CriterioEvaluacion[];
}

export interface Evaluacion {
  id: string;
  numero: number;
  estado: "ABIERTA" | "CONSOLIDADA" | "DECIDIDA";
  version_marco: string;
  umbral_divergencia: number;
  iniciativa: { id: string; codigo: string; nombre: string; estado: EstadoIniciativa };
  puede_gestionar: boolean;
  dimensiones: DimensionEvaluacion[];
  pendientes: Record<string, string>;
}

// --- Resultado (HU4) -------------------------------------------------------------------------

export const RESULTADOS = ["GO", "ITERAR", "VALIDAR", "NO_GO"] as const;
export type Resultado = (typeof RESULTADOS)[number];

export const NOMBRES_RESULTADOS: Record<Resultado, string> = {
  GO: "GO · Lanzar",
  ITERAR: "ITERAR · Desarrollar",
  VALIDAR: "VALIDAR · Prototipar",
  NO_GO: "NO-GO · Descartar",
};

export interface ResultadoEvaluacion {
  evaluacion_id: string;
  iniciativa: { id: string; codigo: string; nombre: string; estado: EstadoIniciativa };
  version_marco: string;
  score_total: number;
  puntajes_dimension: Record<string, number>;
  puntajes_criterio: Record<string, number>;
  pesos: Record<string, number>;
  umbrales: Record<
    "critico" | "validar" | "debil" | "score_go" | "score_iterar" | "score_validar",
    number
  >;
  nombres_dimension: Record<string, string>;
  resultado: Resultado;
  regla: string;
  regla_aplicada: string;
  dimensiones_implicadas: string[];
  fortalezas: string[];
  debilidades: string[];
  riesgos: string[];
  supuestos_criticos: string[];
  borrador_ia: boolean;
  consolidado_en: string;
  consolidado_por: UsuarioBreve | null;
  puede_editar: boolean;
}
