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

const dimension = (codigo: string, nombre: string, rol: Usuario["roles"][number]) => ({
  codigo,
  nombre,
  proposito: "",
  peso: 1 / 6,
  rol_sugerido: rol,
  criterios: [],
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
};
