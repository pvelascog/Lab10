import type { IniciativaDetalle, Usuario, VersionMarco } from "../src/api/tipos";

export const PM: Usuario = {
  id: "u-pm",
  nombre: "Paula PM",
  correo: "pm@nepxa.test",
  activo: true,
  roles: ["PM"],
};

export const MIEMBRO: Usuario = { ...PM, id: "u-m", nombre: "Mario", roles: ["MIEMBRO"] };

export const TECNICO: Usuario = {
  ...PM,
  id: "u-tec",
  nombre: "Tomás Técnico",
  roles: ["LIDER_TECNICO"],
};

const dimension = (
  codigo: string,
  nombre: string,
  rol: Usuario["roles"][number],
  criterios: VersionMarco["dimensiones"][number]["criterios"] = [],
) => ({ codigo, nombre, proposito: "", peso: 1 / 6, rol_sugerido: rol, criterios });

const criterio = (codigo: string, nombre: string, niveles: string[]) => ({
  codigo,
  nombre,
  definicion: "",
  escala_original: 5,
  calculable: "NO" as const,
  niveles: niveles.map((descripcion, n) => ({ nivel: n + 1, descripcion })),
});

export const MARCO: VersionMarco = {
  id: "m1",
  numero: "3.0",
  estado: "VIGENTE",
  umbrales: {
    critico: 2,
    validar: 2.5,
    debil: 3,
    score_go: 4,
    score_iterar: 3,
    score_validar: 2,
    divergencia: 2,
  },
  dimensiones: [
    dimension("MER", "Mercado", "LIDER_COMERCIAL"),
    dimension("FIN", "Financiera", "PM", [
      criterio("FIN-02", "Tiempo de recuperación", ["> 36", "24–36", "12–24", "6–12", "< 6"]),
      criterio("FIN-03", "Potencial de ROI", ["< 25", "25–50", "50–75", "75–100", "> 100 %"]),
    ]),
    dimension("TEC", "Técnica", "LIDER_TECNICO"),
  ],
};

export const INICIATIVA: IniciativaDetalle = {
  id: "i1",
  codigo: "INI-2026-0001",
  nombre: "Portal de reclamos",
  descripcion: "Autogestión de reclamos",
  origen: "CLIENTES",
  estado: "IDENTIFICADA",
  autor: { id: PM.id, nombre: PM.nombre },
  pm: null,
  creado_en: "2026-10-14T12:00:00Z",
  resultado: null,
  problema: null,
  solucion_objetivo: null,
  segmento: null,
  propuesta_valor: null,
  supuestos_clave: [],
  datos_disponibles: null,
  inversion_estimada: null,
  ingresos_esperados: null,
  flujo_mensual_neto: null,
  asignaciones: [],
  posible_duplicado_de: null,
  evaluacion_actual_id: null,
};

import type { CriterioEvaluacion, DimensionEvaluacion, Evaluacion } from "../src/api/tipos";

const criterioEval = (
  codigo: string,
  extra: Partial<CriterioEvaluacion> = {},
): CriterioEvaluacion => ({
  codigo,
  nombre: `Criterio ${codigo}`,
  definicion: "Definición",
  escala_original: 5,
  calculable: "NO",
  niveles: [1, 2, 3, 4, 5].map((nivel) => ({ nivel, descripcion: `Nivel ${nivel} de ${codigo}` })),
  propuesta_calculada: null,
  mi_calificacion: null,
  calificaciones: null,
  promedio: null,
  divergencia: null,
  comentarios: null,
  ...extra,
});

export function dimensionEval(extra: Partial<DimensionEvaluacion> = {}): DimensionEvaluacion {
  return {
    codigo: "MER",
    nombre: "Mercado",
    peso: 1 / 6,
    soy_evaluador: true,
    enviada_por_mi: false,
    ver_calificaciones: false,
    evaluadores: [{ usuario: { id: PM.id, nombre: PM.nombre }, calificados: 0, enviado: false }],
    criterios: [criterioEval("MER-01"), criterioEval("MER-02")],
    ...extra,
  };
}

export { criterioEval };

export function evaluacion(
  dimensiones: DimensionEvaluacion[],
  extra: Partial<Evaluacion> = {},
): Evaluacion {
  return {
    id: "e1",
    numero: 1,
    estado: "ABIERTA",
    version_marco: "3.0",
    umbral_divergencia: 2,
    iniciativa: {
      id: "i1",
      codigo: "INI-2026-0001",
      nombre: "Portal de reclamos",
      estado: "EN_EVALUACION",
    },
    puede_gestionar: false,
    dimensiones,
    pendientes: {},
    ...extra,
  };
}
