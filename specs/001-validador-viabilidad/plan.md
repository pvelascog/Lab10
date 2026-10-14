# Plan de Implementación: Validador de Viabilidad de Productos

**Rama**: `001-validador-viabilidad` | **Fecha**: 2026-10-14 | **Especificación**: [`spec.md`](spec.md)
**Entrada**: especificación clarificada (sesión 2026-10-14) y [`marco-nepxa.md`](marco-nepxa.md)

Documentos de este plan:
- [`research.md`](research.md) – decisiones técnicas y alternativas evaluadas.
- [`data-model.md`](data-model.md) – entidades, relaciones, estados y reglas de validación.
- [`contracts/api.md`](contracts/api.md) – contratos de la API REST.

---

## Resumen

Aplicación web con un backend **Python + FastAPI**, base de datos **PostgreSQL** y una interfaz **React**.
El núcleo es un **motor de decisión determinista** (funciones puras, sin IA) que calcula puntajes por dimensión,
el score ponderado y el resultado GO / ITERAR / VALIDAR / NO-GO con la regla más restrictiva.
Sobre ese núcleo, un **módulo de IA** con la API de Claude realiza el benchmark mediante búsqueda web y genera
recomendaciones y borradores de fortalezas, riesgos y supuestos. Las tareas de IA corren en un **proceso trabajador**
separado para que la evaluación nunca dependa de la disponibilidad de la IA.

---

## Contexto técnico

| Aspecto | Decisión |
|---------|----------|
| **Lenguaje / versión** | Python 3.12 (backend), TypeScript 5 (frontend) |
| **Backend** | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic para migraciones |
| **Base de datos** | PostgreSQL 16 con la extensión `pg_trgm` (detección de duplicados). `pgvector` reservado para el RAG futuro |
| **Frontend** | React 18 + Vite, React Router, TanStack Query, Recharts (gráfico radar) |
| **IA** | SDK oficial `anthropic` para Python; modelo `claude-opus-5-5`; herramienta de servidor `web_search_20260209`; salidas estructuradas con `client.messages.parse` y modelos Pydantic |
| **Tareas en segundo plano** | Tabla `trabajo_ia` en PostgreSQL + proceso trabajador (`python -m app.trabajador`) con `SELECT … FOR UPDATE SKIP LOCKED` |
| **Autenticación** | Cuentas propias; contraseñas con Argon2; sesión con JWT en cookie `HttpOnly` + `SameSite=Lax`; protección CSRF con cabecera de doble envío |
| **Reporte PDF** | Plantilla HTML (Jinja2) renderizada a PDF en el servidor con WeasyPrint; la misma plantilla alimenta la vista web imprimible |
| **Pruebas** | pytest, pytest-asyncio, Hypothesis (propiedades del motor de decisión), httpx `AsyncClient`; Vitest + Testing Library en el frontend; Playwright para el flujo de punta a punta |
| **Calidad** | Ruff (lint y formato), mypy en modo estricto para `app/dominio`; ESLint + Prettier en el frontend |
| **Entorno** | Docker Compose: `db`, `api`, `trabajador`, `web` |
| **Plataforma objetivo** | Navegadores de escritorio modernos; servidor Linux |
| **Escala** | Laboratorio: decenas de iniciativas, < 50 usuarios concurrentes |
| **Metas de rendimiento** | Consolidación < 5 s (SC-004); benchmark y recomendaciones < 2 min |
| **Restricciones** | Interfaz en español; los datos personales de los autores no se envían a la IA (Principio VI) |

---

## Verificación de la constitución

| Principio | Cómo lo cumple el plan | Estado |
|-----------|------------------------|--------|
| I. Especificación primero | El plan deriva de `spec.md` clarificada; cada tarea de `tasks.md` referenciará su HU y FR | ✅ |
| II. Calificaciones explicables | `calificacion.justificacion` es `NOT NULL`; el motor devuelve la regla aplicada (`regla_aplicada`) junto al resultado | ✅ |
| III. La IA asiste, la persona decide | Las sugerencias de IA se guardan con `origen = 'ia_sugerida'` y no cuentan hasta que una persona las confirma; la decisión la registra el comité | ✅ |
| III. Fuentes del benchmark | Cada solución debe citar una URL devuelta por la búsqueda web; las que no la tienen se descartan en el servidor | ✅ |
| IV. Criterios trazables | `version_marco` inmutable una vez usada; cada evaluación guarda `version_marco_id` | ✅ |
| V. Pruebas como evidencia | Motor de decisión en funciones puras con pruebas de tabla y de propiedades; IA probada con respuestas simuladas | ✅ |
| VI. Confidencialidad | Control de acceso por rol y por asignación (FR-027a); a la IA solo se envía el contenido de la ficha, nunca nombres ni correos | ✅ |
| VII. Simplicidad | Sin colas externas (Redis/Celery): la cola es una tabla; sin microservicios; monorepo con dos aplicaciones | ✅ |

No hay desviaciones que justificar.

---

## Arquitectura

```
┌──────────────────────┐     HTTPS/JSON      ┌───────────────────────────────────────────┐
│  web (React + Vite)  │ ──────────────────► │  api (FastAPI)                            │
│  - Backlog           │ ◄────────────────── │  ├─ api/        rutas y dependencias      │
│  - Ficha             │                     │  ├─ servicios/  casos de uso              │
│  - Matriz evaluación │                     │  ├─ dominio/    motor de decisión (puro)  │
│  - Resumen + radar   │                     │  ├─ reportes/   HTML → PDF (WeasyPrint)   │
│  - Comité            │                     │  └─ modelos/    SQLAlchemy                │
│  - Admin del marco   │                     └───────────────┬───────────────────────────┘
└──────────────────────┘                                     │ encola trabajo_ia
                                                             ▼
                              ┌──────────────────┐   ┌─────────────────────────────────┐
                              │  PostgreSQL 16   │◄──│  trabajador (proceso Python)    │
                              │  pg_trgm         │   │  ├─ ia/benchmark.py             │
                              └──────────────────┘   │  ├─ ia/recomendaciones.py       │
                                                     │  └─ ia/fuentes/ (web, interna*) │
                                                     └───────────────┬─────────────────┘
                                                                     │ SDK anthropic
                                                                     ▼
                                                           API de Claude + web_search
                                                     (* fuente interna RAG: versión futura)
```

### Flujo del benchmark (HU5, FR-018, FR-019)

1. Al pasar la iniciativa a "Estructurada", la API encola un `trabajo_ia` de tipo `benchmark`.
2. **Investigación**: el trabajador llama a Claude con la herramienta `web_search_20260209` y la ficha anonimizada.
   Se recolectan las URLs de los bloques `web_search_result`.
3. **Estructuración**: una segunda llamada con `client.messages.parse(output_format=BenchmarkIA)` convierte la
   investigación en una lista de soluciones (nombre, descripción, URL, similitud 0–1, comparación por atributos)
   y en calificaciones sugeridas para CMP-01 a CMP-04 con su justificación.
4. **Validación anti-invención**: el servidor descarta toda solución cuya URL no esté entre las URLs recolectadas
   en el paso 2. Si no queda ninguna, el benchmark se guarda como "sin soluciones similares" (HU5, escenario 4).
5. Se guarda con `generado_por_ia = true`; las calificaciones sugeridas quedan como `ia_sugerida`.

La interfaz `FuenteBenchmark` (`buscar(ficha) -> list[Evidencia]`) aísla la búsqueda web; la fuente interna con RAG
(pgvector sobre iniciativas y productos NEPXA) será otra implementación de la misma interfaz.

### Flujo de recomendaciones (HU6, FR-020)

Al consolidar, se encola un trabajo `recomendaciones`. El trabajador envía la matriz (puntajes, justificaciones),
el resultado recomendado y el benchmark, y obtiene con `messages.parse` una lista de recomendaciones
(dimensión, criterio, acción, prioridad, supuesto a validar) y un borrador de fortalezas, riesgos y supuestos críticos.

### Uso de la API de Claude

- Modelo `claude-opus-5-5` con `thinking: {type: "adaptive"}` y `output_config.effort` explícito
  (`high` para el benchmark, `medium` para recomendaciones).
- Respaldo ante rechazos: parámetro `fallbacks: "default"` con la beta `server-side-fallback-2026-07-01`;
  siempre se revisa `stop_reason` antes de leer el contenido (`refusal`, `max_tokens`, `pause_turn`).
- Caché de prompts: las instrucciones del sistema y la descripción del Marco NEPXA son estables y van primero,
  con `cache_control`; los datos de la iniciativa van al final.
- Errores: cadena específica (`RateLimitError` → reintento con espera; `APIStatusError` 4xx → fallo definitivo;
  `APIConnectionError` → reintento). Máximo 3 intentos por trabajo; después queda "fallido" y se puede reintentar
  desde la interfaz (caso límite "IA no disponible").
- La clave `ANTHROPIC_API_KEY` se lee del entorno; nunca se guarda en el repositorio.

### Motor de decisión (HU4, FR-011 a FR-016)

Módulo puro `app/dominio/motor_decision.py`, sin dependencias de base de datos:

```python
def puntaje_criterio(calificaciones: list[int]) -> float          # promedio (FR-010a)
def puntaje_dimension(criterios: list[float]) -> float            # promedio simple (FR-011)
def score_total(dimensiones: dict[str, float], pesos: dict[str, Decimal]) -> float   # FR-012
def resultado(score: float, dimensiones: dict[str, float], umbrales: Umbrales) -> Resultado
    # Regla más restrictiva, en orden (FR-016):
    # 1. score < 2.0 o alguna dimensión < 2.0           → NO_GO
    # 2. score < 3.0 o ≥ 2 dimensiones < 2.5            → VALIDAR
    # 3. score < 4.0 o alguna dimensión < 3.0           → ITERAR
    # 4. en otro caso                                   → GO
    # Devuelve también la regla que se cumplió y las dimensiones implicadas.
def divergencias(calificaciones: list[int], umbral: int = 2) -> bool   # FR-010a
def normalizar_recurrencia(nivel: int) -> int                     # 1→1, 2→3, 3→5 (FR-008)
```

Los umbrales (2.0, 2.5, 3.0, 4.0 y el umbral de divergencia) se leen de la versión del marco, no están fijos en el código.
`app/dominio/calculos_financieros.py` calcula ROI y tiempo de recuperación y los convierte a nivel 1–5 (FR-009).

### Reglas de visibilidad (FR-010b, FR-027a)

- Un evaluador guarda calificaciones en borrador y **envía** cada dimensión asignada.
- La API devuelve las calificaciones de otros evaluadores de una dimensión solo si quien consulta ya envió la suya
  para esa dimensión, o si tiene rol PM, Comité o Administrador y la evaluación ya fue consolidada.
- Cada consulta de iniciativa filtra por: autor, evaluador asignado, o rol con visión de portafolio.

### Recomendación de evaluadores (HU10, FR-010c)

Primera versión heurística y explicable (sin modelo entrenado): para cada dimensión se ordenan los usuarios con la
función correspondiente por `0.5·(evaluaciones previas en la dimensión) + 0.3·(similitud trigram con iniciativas que
evaluó) − 0.2·(evaluaciones abiertas)`, y se muestra el porqué. El sistema "aprende" porque el historial crece;
más adelante se puede reemplazar por similitud de embeddings con pgvector.

---

## Estructura del proyecto

### Documentación (esta funcionalidad)

```
specs/001-validador-viabilidad/
├── marco-nepxa.md      # Requisitos extraídos del Marco NEPXA v3.0
├── spec.md             # Especificación (qué y por qué)
├── plan.md             # Este archivo
├── research.md         # Decisiones técnicas
├── data-model.md       # Modelo de datos
├── contracts/
│   └── api.md          # Contratos de la API
└── tasks.md            # Siguiente fase
```

### Código fuente

```
backend/
├── pyproject.toml
├── alembic/                    # Migraciones
├── app/
│   ├── main.py                 # Aplicación FastAPI
│   ├── config.py               # Configuración por variables de entorno
│   ├── db.py                   # Sesión SQLAlchemy
│   ├── seguridad.py            # Hash de contraseñas, JWT, CSRF, dependencias de rol
│   ├── api/                    # Rutas: auth, usuarios, iniciativas, evaluaciones, comite, marco, reportes, ia
│   ├── esquemas/               # Modelos Pydantic de entrada/salida
│   ├── modelos/                # Modelos SQLAlchemy
│   ├── servicios/              # Casos de uso (ciclo de vida, consolidación, asignación, auditoría)
│   ├── dominio/                # Lógica pura: motor_decision.py, calculos_financieros.py
│   ├── ia/
│   │   ├── cliente.py          # Cliente anthropic, reintentos, manejo de stop_reason
│   │   ├── prompts.py          # Instrucciones del sistema (estables, cacheables)
│   │   ├── benchmark.py
│   │   ├── recomendaciones.py
│   │   └── fuentes/            # FuenteBenchmark: web.py (ahora), interna.py (futuro)
│   ├── reportes/               # Plantillas Jinja2 y generación de PDF
│   ├── semillas/               # Marco NEPXA v3.0 como versión inicial (28 criterios, pesos 1/6)
│   └── trabajador.py           # Bucle del proceso trabajador
└── tests/
    ├── unit/                   # Motor de decisión, cálculos financieros, validaciones
    ├── integration/            # API + PostgreSQL (ciclo de vida, visibilidad, permisos)
    └── contract/               # Respuestas de la API frente a contracts/api.md

frontend/
├── package.json
├── src/
│   ├── api/                    # Cliente HTTP tipado
│   ├── paginas/                # Login, Backlog, Ficha, Evaluación, Resumen, Comité, Seguimiento, AdminMarco
│   ├── componentes/            # MatrizCriterios, RadarDimensiones, InsigniaIA, ResultadoBadge, …
│   └── estado/                 # Sesión y rol activo
└── tests/

docker-compose.yml
```

**Decisión de estructura**: aplicación web con backend y frontend separados en un monorepo.

---

## Estrategia de pruebas

| Nivel | Qué cubre | Herramientas |
|-------|-----------|--------------|
| Unitarias | Motor de decisión: tabla con los ejemplos de HU4 y los valores límite (2.0, 2.5, 3.0, 4.0); propiedades: el resultado nunca es GO si alguna dimensión < 3, nunca mejor que NO-GO si alguna < 2, y bajar un puntaje nunca mejora el resultado (monotonía). Cálculos financieros y normalización de Recurrencia | pytest, Hypothesis |
| Integración | Ciclo de vida completo; calificación a ciegas; divergencias; permisos por rol; versionado del marco; auditoría | pytest + PostgreSQL de pruebas |
| IA | Benchmark y recomendaciones con un cliente simulado: respuesta normal, URL inventada (debe descartarse), sin resultados, `refusal`, `max_tokens`, error 429 | pytest con respuestas grabadas |
| Contrato | Forma de las respuestas según `contracts/api.md` | pytest + esquema OpenAPI generado |
| Frontend | Componentes de matriz, radar e insignia "generado por IA" | Vitest + Testing Library |
| Punta a punta | Registrar → estructurar → evaluar (2 evaluadores) → consolidar → decidir → exportar PDF | Playwright |

Las pruebas no llaman a la API real de Claude; una prueba manual opcional (`pytest -m ia_real`) la usa si hay clave.

---

## Fases de entrega

| Incremento | Historias | Resultado demostrable |
|------------|-----------|-----------------------|
| **MVP** | HU1, HU2, HU3, HU4 + inicio de sesión | Registrar, estructurar, evaluar con varios evaluadores y obtener el resultado recomendado con radar |
| **Incremento 2** | HU5, HU6, HU7 + exportación PDF | Benchmark web, recomendaciones IA, decisión del comité y reporte |
| **Incremento 3** | HU8, HU9, HU10 | Seguimiento, revaluación, administración del marco y sugerencia de evaluadores |

## Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| La IA cita fuentes inexistentes | Validación de URLs contra los resultados reales de la búsqueda (paso 4 del benchmark) |
| Costo o latencia de la IA | Tareas en segundo plano, caché de prompts, `max_uses` en la búsqueda web, effort ajustado por tarea |
| Ambigüedad de reglas del marco | Umbrales parametrizados en la versión del marco; pruebas de tabla con los ejemplos acordados |
| WeasyPrint requiere librerías del sistema | Incluidas en la imagen Docker de la API |
