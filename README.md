# Lab10 – Validador de Viabilidad de Productos

Sistema que recibe ideas de productos y las califica según el **Marco de Viabilidad NEPXA v3.0**: 6 dimensiones
(**Mercado, Comercial, Financiera y de Inversión, Técnica, Competencia y Ecosistema**), 28 criterios en escala 1–5
y un resultado **GO / ITERAR / VALIDAR / NO-GO** que considera el promedio y el balance entre dimensiones. Incorpora componentes de **IA** que realizan un **benchmark** de soluciones similares al
inscribir una idea y generan **recomendaciones** para convertirla en un producto.

## Metodología: Desarrollo Guiado por Especificaciones (Spec-Driven Development)

El proyecto avanza por fases; cada una produce un documento versionado en este repositorio:

| Fase | Documento | Estado |
|------|-----------|--------|
| 1. Constitución | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | ✅ v1.1.0 |
| 2a. Marco de referencia | [`specs/001-validador-viabilidad/marco-nepxa.md`](specs/001-validador-viabilidad/marco-nepxa.md) | ✅ Extraído |
| 2. Especificación | [`specs/001-validador-viabilidad/spec.md`](specs/001-validador-viabilidad/spec.md) | 📝 Borrador |
| 3. Clarificación | Resolver `[NECESITA ACLARACIÓN]` en la especificación | ⏳ Pendiente |
| 4. Plan técnico | `specs/001-validador-viabilidad/plan.md` | ⏳ Pendiente |
| 5. Tareas | `specs/001-validador-viabilidad/tasks.md` | ⏳ Pendiente |
| 6. Implementación | Código y pruebas | ⏳ Pendiente |

## Estructura

```
.
├── .specify/
│   └── memory/
│       └── constitution.md      # Principios del proyecto
├── specs/
│   └── 001-validador-viabilidad/
│       ├── marco-nepxa.md       # Dimensiones, rúbricas, modelo de decisión y flujo (fuente)
│       └── spec.md              # Qué y por qué (sin tecnología)
└── README.md
```
