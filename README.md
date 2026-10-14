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
| 6. Implementación | Código y pruebas | 🚧 Fases 1–3 de 13 completadas |

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

## Cómo ejecutar

Requisitos: Docker con Docker Compose. Para desarrollo sin Docker: Python 3.12+ con [uv](https://docs.astral.sh/uv/) y Node.js 22.

```bash
cp .env.example .env          # completar JWT_SECRETO (y ANTHROPIC_API_KEY desde la Fase 7)
docker compose up --build     # db (5432), api (8000) y web (5173)
```

Al arrancar, la API aplica las migraciones y carga los roles y el Marco NEPXA v3.0. Luego cree el primer
administrador (puede sumarle otros roles para probar):

```bash
docker compose exec api python -m app.semillas.admin --nombre "Administrador" --correo admin@empresa.com --roles PM,COMITE
```

- Interfaz: http://localhost:5173
- API: http://localhost:8000/api/v1/salud · documentación en http://localhost:8000/api/v1/docs

### Desarrollo y pruebas

```bash
# Backend
cd backend
uv sync
uv run pytest                 # pruebas
uv run ruff check . && uv run ruff format --check . && uv run mypy app
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm test && npm run lint && npm run typecheck
npm run dev
```

La integración continua (`.github/workflows/ci.yml`) ejecuta estas mismas verificaciones y compila las imágenes de Docker.
