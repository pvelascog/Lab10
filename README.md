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
| 2. Especificación | [`specs/001-validador-viabilidad/spec.md`](specs/001-validador-viabilidad/spec.md) | ✅ Completa |
| 3. Clarificación | Sección "Clarificaciones" de la especificación | ✅ Sesión 2026-10-14 |
| 4. Plan técnico | [`plan.md`](specs/001-validador-viabilidad/plan.md), [`research.md`](specs/001-validador-viabilidad/research.md), [`data-model.md`](specs/001-validador-viabilidad/data-model.md), [`contracts/api.md`](specs/001-validador-viabilidad/contracts/api.md) | ✅ Completo |
| 5. Tareas | [`tasks.md`](specs/001-validador-viabilidad/tasks.md) – 114 tareas en 13 fases | ✅ Completo |
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
│       ├── spec.md              # Qué y por qué (sin tecnología)
│       ├── plan.md              # Cómo: arquitectura, stack, pruebas, incrementos
│       ├── research.md          # Decisiones técnicas y alternativas
│       ├── data-model.md        # Entidades, reglas y máquina de estados
│       ├── contracts/api.md     # Contratos de la API REST
│       └── tasks.md             # Tareas de implementación por historia
└── README.md
```

## Stack técnico

Python 3.12 · FastAPI · PostgreSQL 16 · React 18 + Vite · API de Claude (benchmark con búsqueda web y recomendaciones) ·
WeasyPrint (PDF) · Docker Compose.
