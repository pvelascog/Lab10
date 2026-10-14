# Tareas: Validador de Viabilidad de Productos

**Entrada**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`data-model.md`](data-model.md), [`contracts/api.md`](contracts/api.md),
[`research.md`](research.md), [`marco-nepxa.md`](marco-nepxa.md)
**Fecha**: 2026-10-14

## Formato

`- [ ] T### [P] [HU#] Descripción con ruta del archivo`

- **[P]**: se puede hacer en paralelo con otras tareas [P] de la misma fase (archivos distintos, sin dependencias pendientes).
- **[HU#]**: historia de usuario de `spec.md` a la que pertenece la tarea.
- **Pruebas primero** (Principio V): en cada historia, las pruebas se escriben antes que el código y deben **fallar**
  antes de implementar.
- Rutas relativas a la raíz del repositorio: `backend/` y `frontend/`.

---

## Fase 1: Preparación del proyecto

**Objetivo**: estructura del monorepo, herramientas y entorno local.

- [x] T001 Crear la estructura de carpetas de `backend/` y `frontend/` según `plan.md` (sección Estructura del proyecto)
- [x] T002 Inicializar `backend/pyproject.toml` (Python 3.12) con FastAPI, Pydantic v2, SQLAlchemy 2 async, asyncpg, Alembic, argon2-cffi, PyJWT, anthropic, Jinja2, WeasyPrint; dependencias de desarrollo: pytest, pytest-asyncio, Hypothesis, httpx, Ruff, mypy
- [x] T003 [P] Inicializar `frontend/` con Vite + React 18 + TypeScript, React Router, TanStack Query, Recharts; Vitest + Testing Library; ESLint + Prettier
- [x] T004 [P] Configurar Ruff y mypy (modo estricto en `app/dominio`) en `backend/pyproject.toml`
- [x] T005 [P] Crear `docker-compose.yml` con servicios `db` (PostgreSQL 16 con `pg_trgm`), `api`, `trabajador` y `web`
- [x] T006 [P] Crear `backend/Dockerfile` con las librerías de sistema de WeasyPrint (Pango, HarfBuzz) y `frontend/Dockerfile`
- [x] T007 [P] Crear `.env.example` (DATABASE_URL, JWT_SECRETO, ANTHROPIC_API_KEY, URL_FRONTEND) y `.gitignore`
- [x] T008 [P] Crear el flujo de integración continua `.github/workflows/ci.yml`: Ruff, mypy, pytest (con servicio PostgreSQL), Vitest y ESLint

---

## Fase 2: Base común (bloquea todas las historias)

**Objetivo**: configuración, base de datos, marco NEPXA cargado, inicio de sesión y auditoría.
⚠️ Ninguna historia de usuario puede empezar antes de terminar esta fase.

### Pruebas de la base

- [x] T009 [P] Prueba de integración del inicio de sesión (credenciales válidas, inválidas, bloqueo tras 5 intentos, cierre de sesión, CSRF) en `backend/tests/integration/test_auth.py`
- [x] T010 [P] Prueba de integración de permisos por rol (401 sin sesión, 403 sin rol) en `backend/tests/integration/test_permisos.py`
- [x] T011 [P] Prueba de la semilla del marco: 6 dimensiones, 28 criterios, pesos que suman 1, Recurrencia con niveles {1, 3, 5} en `backend/tests/integration/test_semilla_marco.py`

### Implementación de la base

- [x] T012 Configuración por variables de entorno en `backend/app/config.py`
- [x] T013 Sesión de base de datos async y clase base de modelos (UUID, `creado_en`, `actualizado_en`) en `backend/app/db.py`
- [x] T014 Configurar Alembic en `backend/alembic/` (con la extensión `pg_trgm`)
- [x] T015 [P] Modelos `usuario`, `rol`, `usuario_rol` en `backend/app/modelos/usuarios.py`
- [x] T016 [P] Modelos `version_marco`, `dimension`, `criterio`, `nivel_criterio` en `backend/app/modelos/marco.py`
- [x] T017 [P] Modelo `auditoria` (solo inserción) en `backend/app/modelos/auditoria.py`
- [x] T018 Migración inicial de las tablas de T015–T017 en `backend/alembic/versions/`
- [x] T019 Semilla del Marco NEPXA v3.0 (28 criterios con rúbricas de `marco-nepxa.md`, pesos 1/6, umbrales por defecto, roles sugeridos) en `backend/app/semillas/marco_v3.py`
- [x] T020 Seguridad: hash Argon2, emisión y validación de JWT en cookie, token CSRF, dependencias `usuario_actual` y `requiere_rol(...)` en `backend/app/seguridad.py`
- [x] T021 Servicio de auditoría `registrar(usuario, accion, entidad, antes, despues)` en `backend/app/servicios/auditoria.py`
- [x] T022 Rutas `/auth/login`, `/auth/logout`, `/auth/yo` en `backend/app/api/auth.py`
- [x] T023 Rutas `/usuarios` (listar, crear, cambiar roles, desactivar) en `backend/app/api/usuarios.py`
- [x] T024 Ruta `GET /marco/vigente` en `backend/app/api/marco.py`
- [x] T025 Manejador de errores con el formato de `contracts/api.md` y aplicación FastAPI en `backend/app/main.py`
- [x] T026 Comando para crear el primer administrador en `backend/app/semillas/admin.py`
- [x] T027 [P] Cliente HTTP tipado con cookie y cabecera CSRF en `frontend/src/api/cliente.ts`
- [x] T028 [P] Estado de sesión y rutas protegidas por rol en `frontend/src/estado/sesion.tsx`
- [x] T029 Página de inicio de sesión y diseño general (menú según rol) en `frontend/src/paginas/Login.tsx` y `frontend/src/componentes/Diseno.tsx`

**Punto de control**: se puede iniciar sesión y consultar el marco vigente.

---

## Fase 3: HU1 – Registrar una iniciativa en el backlog (P1) 🎯 MVP

**Objetivo**: cualquier usuario registra una idea con evaluadores por dimensión.
**Prueba independiente**: registrar una idea y verla en el backlog como "Identificada".

### Pruebas HU1

- [x] T030 [P] [HU1] Prueba de contrato de `POST /iniciativas` y `GET /iniciativas` en `backend/tests/contract/test_iniciativas.py`
- [x] T031 [P] [HU1] Prueba de integración: registro válido, campos faltantes (400 con campo), aviso de duplicado, visibilidad (FR-027a) en `backend/tests/integration/test_registro_iniciativa.py`

### Implementación HU1

- [x] T032 [P] [HU1] Modelos `iniciativa` y `asignacion_evaluador` en `backend/app/modelos/iniciativas.py` y migración
- [x] T033 [HU1] Esquemas Pydantic de iniciativa en `backend/app/esquemas/iniciativas.py`
- [x] T034 [HU1] Servicio de registro: código `INI-AAAA-NNNN`, detección de duplicados con similitud trigram ≥ 0.6, asignaciones iniciales en `backend/app/servicios/iniciativas.py`
- [x] T035 [HU1] Filtro de visibilidad (autor, evaluador asignado o rol de portafolio) en `backend/app/servicios/visibilidad.py`
- [x] T036 [HU1] Rutas `POST /iniciativas`, `GET /iniciativas`, `GET /iniciativas/{id}` en `backend/app/api/iniciativas.py`
- [x] T037 [P] [HU1] Página Backlog con filtros por estado, origen, resultado y fecha en `frontend/src/paginas/Backlog.tsx`
- [x] T038 [P] [HU1] Formulario de nueva iniciativa con selección de evaluadores por dimensión en `frontend/src/paginas/NuevaIniciativa.tsx`

**Punto de control**: HU1 funciona por sí sola.

---

## Fase 4: HU2 – Estructurar la ficha (P1) 🎯 MVP

**Objetivo**: el PM completa la ficha y el sistema calcula ROI y tiempo de recuperación.
**Prueba independiente**: completar la ficha y pasar a "Estructurada".

### Pruebas HU2

- [x] T039 [P] [HU2] Pruebas unitarias de cálculos financieros: ROI, tiempo de recuperación, conversión a nivel 1–5 con límites al nivel mejor (12 meses → 4; 50 % → 3), inversión ≤ 0 rechazada en `backend/tests/unit/test_calculos_financieros.py`
- [x] T040 [P] [HU2] Prueba de integración: transición a `ESTRUCTURADA` con ficha incompleta (lista de faltantes), completa, y edición solo en estados permitidos en `backend/tests/integration/test_ficha.py`

### Implementación HU2

- [x] T041 [P] [HU2] Funciones puras de cálculos financieros en `backend/app/dominio/calculos_financieros.py`
- [x] T042 [HU2] Servicio de ciclo de vida con la tabla de transiciones de `data-model.md` (409 si no está permitida) en `backend/app/servicios/ciclo_vida.py`
- [x] T043 [HU2] Rutas `PATCH /iniciativas/{id}`, `PUT /iniciativas/{id}/asignaciones`, `POST /iniciativas/{id}/transiciones`, `GET /iniciativas/{id}/calculos-financieros` en `backend/app/api/iniciativas.py`
- [x] T044 [P] [HU2] Página Ficha con supuestos clave, datos financieros y vista previa de ROI en `frontend/src/paginas/Ficha.tsx`

**Punto de control**: HU1 y HU2 funcionan juntas.

---

## Fase 5: HU3 – Evaluación multidimensional (P1) 🎯 MVP

**Objetivo**: varios evaluadores califican a ciegas, con justificación y detección de divergencias.
**Prueba independiente**: dos evaluadores califican los 28 criterios y la matriz queda completa.

### Pruebas HU3

- [x] T045 [P] [HU3] Pruebas unitarias: promedio por criterio, divergencia con umbral 2, normalización de Recurrencia en `backend/tests/unit/test_calificaciones.py`
- [x] T046 [P] [HU3] Prueba de integración: calificación sin justificación rechazada, evaluador no asignado (403), Recurrencia fuera de {1, 3, 5} (400) en `backend/tests/integration/test_calificar.py`
- [x] T047 [P] [HU3] Prueba de integración de **calificación a ciegas**: no ve calificaciones ajenas antes de enviar la dimensión; sí las ve después; no puede editar tras enviar en `backend/tests/integration/test_calificacion_ciegas.py`
- [x] T048 [P] [HU3] Prueba de integración de divergencias: se detectan y bloquean la consolidación hasta comentarlas en `backend/tests/integration/test_divergencias.py`

### Implementación HU3

- [x] T049 [P] [HU3] Modelos `evaluacion`, `calificacion`, `envio_dimension`, `comentario_divergencia` en `backend/app/modelos/evaluaciones.py` y migración
- [x] T050 [P] [HU3] Funciones puras `puntaje_criterio`, `divergencias`, `normalizar_recurrencia` en `backend/app/dominio/motor_decision.py`
- [x] T051 [HU3] Servicio de evaluación: creación al pasar a `EN_EVALUACION` (versión vigente del marco), borradores, envío por dimensión, avance por dimensión y evaluador en `backend/app/servicios/evaluaciones.py`
- [x] T052 [HU3] Reglas de visibilidad de calificaciones (FR-010b) en `backend/app/servicios/visibilidad.py`
- [x] T053 [HU3] Rutas de calificaciones, envío de dimensión y divergencias de `contracts/api.md` en `backend/app/api/evaluaciones.py`
- [x] T054 [P] [HU3] Componente MatrizCriterios: rúbrica por nivel, justificación obligatoria, borrador y envío por dimensión en `frontend/src/componentes/MatrizCriterios.tsx`
- [x] T055 [P] [HU3] Página Evaluación con avance y divergencias en `frontend/src/paginas/Evaluacion.tsx`

**Punto de control**: HU1–HU3 funcionan juntas.

---

## Fase 6: HU4 – Consolidación y resultado recomendado (P1) 🎯 MVP

**Objetivo**: puntajes, score ponderado, resultado con la regla más restrictiva, resumen y radar.
**Prueba independiente**: con puntajes conocidos, el resultado coincide con la tabla de FR-016.

### Pruebas HU4

- [ ] T056 [P] [HU4] Pruebas de tabla del motor con los ejemplos de HU4 (GO 4.17; ITERAR 4.3 con 2.8; VALIDAR 3.4 con 2.3 y 2.4; NO-GO con 1.8) y valores límite exactos 2.0, 2.5, 3.0 y 4.0 en `backend/tests/unit/test_motor_decision.py`
- [ ] T057 [P] [HU4] Pruebas de propiedades con Hypothesis: nunca GO con una dimensión < 3; siempre NO-GO con una dimensión < 2; bajar un puntaje nunca mejora el resultado; pesos iguales equivalen al promedio simple en `backend/tests/unit/test_motor_propiedades.py`
- [ ] T058 [P] [HU4] Prueba de integración: consolidar con criterios faltantes (422), consolidación correcta, fotografía inmutable del resultado, regla aplicada informada en `backend/tests/integration/test_consolidacion.py`

### Implementación HU4

- [ ] T059 [HU4] Funciones puras `puntaje_dimension`, `score_total` y `resultado` (devuelve regla aplicada y dimensiones implicadas; umbrales desde la versión del marco) en `backend/app/dominio/motor_decision.py`
- [ ] T060 [P] [HU4] Modelo `resultado_consolidado` en `backend/app/modelos/evaluaciones.py` y migración
- [ ] T061 [HU4] Servicio de consolidación (solo calificaciones válidas según origen) en `backend/app/servicios/consolidacion.py`
- [ ] T062 [HU4] Rutas `GET` y `PATCH /evaluaciones/{id}/resultado` en `backend/app/api/evaluaciones.py`
- [ ] T063 [P] [HU4] Componente RadarDimensiones (6 ejes, escala 1–5) en `frontend/src/componentes/RadarDimensiones.tsx`
- [x] T064 [P] [HU4] Utilidad de formato que **trunca** a 2 decimales y su prueba en `frontend/src/utilidades/formato.ts` y `frontend/tests/formato.test.ts` *(adelantada en la Fase 2 para mostrar los pesos del marco)*
- [ ] T065 [HU4] Página Resumen ejecutivo con resultado, regla aplicada, puntajes, pesos, fortalezas, debilidades, riesgos y supuestos en `frontend/src/paginas/Resumen.tsx`

**Punto de control 🎯 MVP**: registrar → estructurar → evaluar con varios evaluadores → resultado con radar. Demostrable.

---

## Fase 7: HU5 – Benchmark con IA (P2)

**Objetivo**: búsqueda web de soluciones similares con fuentes verificadas y calificaciones sugeridas de Competencia.
**Prueba independiente**: con una respuesta de IA simulada, se guardan solo las soluciones con URL real.

### Pruebas HU5

- [ ] T066 [P] [HU5] Prueba de la cola de trabajos: toma con `SKIP LOCKED`, reintentos (máx. 3), estado fallido y reintento manual en `backend/tests/integration/test_trabajos_ia.py`
- [ ] T067 [P] [HU5] Pruebas del benchmark con cliente simulado: respuesta normal; URL inventada descartada; sin resultados → `SIN_RESULTADOS`; `stop_reason` `refusal` y `max_tokens`; error de la herramienta de búsqueda; error 429 en `backend/tests/unit/test_benchmark.py`
- [ ] T068 [P] [HU5] Prueba de que la ficha enviada a la IA no contiene nombres ni correos (Principio VI) en `backend/tests/unit/test_anonimizacion.py`

### Implementación HU5

- [ ] T069 [P] [HU5] Modelos `trabajo_ia`, `benchmark`, `solucion_benchmark` en `backend/app/modelos/ia.py` y migración
- [ ] T070 [HU5] Proceso trabajador (bucle, `SKIP LOCKED`, reintentos con espera) en `backend/app/trabajador.py`
- [ ] T071 [HU5] Cliente de Claude: `claude-opus-5-5`, pensamiento adaptativo, `effort` por tarea, `fallbacks: "default"`, revisión de `stop_reason`, cadena de errores específica, caché de las instrucciones estables en `backend/app/ia/cliente.py`
- [ ] T072 [P] [HU5] Instrucciones del sistema (benchmark y recomendaciones) en `backend/app/ia/prompts.py`
- [ ] T073 [HU5] Interfaz `FuenteBenchmark` y búsqueda web con `web_search_20260209` (recolección de URLs de `web_search_result`) en `backend/app/ia/fuentes/base.py` y `backend/app/ia/fuentes/web.py`
- [ ] T074 [HU5] Benchmark en dos pasos: investigar → estructurar con `messages.parse` (modelo Pydantic `BenchmarkIA`) → descartar URLs no recolectadas → guardar sugerencias CMP-01 a CMP-04 como `IA_SUGERIDA` en `backend/app/ia/benchmark.py`
- [ ] T075 [HU5] Encolar el benchmark al pasar a `ESTRUCTURADA` en `backend/app/servicios/ciclo_vida.py`
- [ ] T076 [HU5] Rutas `GET`/`POST /iniciativas/{id}/benchmark`, `GET /trabajos/{id}` y confirmación de sugerencias en `backend/app/api/ia.py` y `backend/app/api/evaluaciones.py`
- [ ] T077 [P] [HU5] Componente InsigniaIA ("generado por IA") en `frontend/src/componentes/InsigniaIA.tsx`
- [ ] T078 [P] [HU5] Panel Benchmark (lista con enlaces, similitud, comparación, estado y reintento) en `frontend/src/componentes/PanelBenchmark.tsx`
- [ ] T079 [HU5] Mostrar las sugerencias de IA en la matriz con acción "confirmar con justificación" en `frontend/src/componentes/MatrizCriterios.tsx`

**Punto de control**: el benchmark funciona y la evaluación sigue funcionando sin IA.

---

## Fase 8: HU6 – Recomendaciones con IA (P2)

**Objetivo**: recomendaciones priorizadas según el resultado y borrador del resumen ejecutivo.
**Prueba independiente**: con una dimensión < 3, hay al menos una recomendación para ella.

### Pruebas HU6

- [ ] T080 [P] [HU6] Pruebas con cliente simulado: estructura de cada recomendación; prioridad a dimensiones < 3 en ITERAR/VALIDAR; roadmap/MVP en GO; borrador de fortalezas, riesgos y supuestos marcado como IA en `backend/tests/unit/test_recomendaciones.py`

### Implementación HU6

- [ ] T081 [P] [HU6] Modelo `recomendacion` en `backend/app/modelos/ia.py` y migración
- [ ] T082 [HU6] Generación de recomendaciones con `messages.parse` (modelo Pydantic `RecomendacionesIA`) en `backend/app/ia/recomendaciones.py`
- [ ] T083 [HU6] Encolar recomendaciones al consolidar en `backend/app/servicios/consolidacion.py`
- [ ] T084 [HU6] Rutas de recomendaciones de `contracts/api.md` en `backend/app/api/ia.py`
- [ ] T085 [P] [HU6] Panel Recomendaciones con aceptar o descartar en `frontend/src/componentes/PanelRecomendaciones.tsx`

---

## Fase 9: HU7 – Comité de producto, decisión y reporte (P2)

**Objetivo**: el comité registra la decisión y los siguientes pasos; el resumen se exporta a PDF.
**Prueba independiente**: decidir una iniciativa y descargar su PDF.

### Pruebas HU7

- [ ] T086 [P] [HU7] Prueba de integración: decisión sin justificación (422); distinta al resultado sin motivo (422); siguientes pasos y estado según la decisión (GO → seguimiento, NO-GO → archivada, ITERAR/VALIDAR → nueva evaluación) en `backend/tests/integration/test_comite.py`
- [ ] T087 [P] [HU7] Prueba del reporte: el HTML y el PDF contienen puntajes, radar, justificaciones, benchmark, recomendaciones y decisión; respuesta `application/pdf` en `backend/tests/integration/test_reporte.py`

### Implementación HU7

- [ ] T088 [P] [HU7] Modelos `decision_comite` y `siguiente_paso` en `backend/app/modelos/comite.py` y migración
- [ ] T089 [HU7] Servicio de decisión y transición correspondiente en `backend/app/servicios/comite.py`
- [ ] T090 [HU7] Rutas `/comite/agenda`, `/evaluaciones/{id}/decision`, `/portafolio`, `/decisiones/{id}` en `backend/app/api/comite.py`
- [ ] T091 [P] [HU7] Radar en SVG del lado del servidor en `backend/app/reportes/radar_svg.py`
- [ ] T092 [HU7] Plantilla Jinja2 del resumen ejecutivo y conversión a PDF con WeasyPrint en `backend/app/reportes/resumen.html` y `backend/app/reportes/pdf.py`
- [ ] T093 [HU7] Rutas `/evaluaciones/{id}/reporte` y `/evaluaciones/{id}/reporte.pdf` en `backend/app/api/reportes.py`
- [ ] T094 [P] [HU7] Página Comité (agenda, decisión, siguientes pasos, priorización) en `frontend/src/paginas/Comite.tsx`
- [ ] T095 [P] [HU7] Botón "Exportar a PDF" en `frontend/src/paginas/Resumen.tsx`

**Punto de control**: incremento 2 completo (HU1–HU7).

---

## Fase 10: HU8 – Seguimiento y revaluación (P3)

- [ ] T096 [P] [HU8] Prueba de integración: hitos, revaluación con nueva evaluación que conserva el historial, evolución de puntajes en `backend/tests/integration/test_seguimiento.py`
- [ ] T097 [P] [HU8] Modelo `hito_seguimiento` en `backend/app/modelos/seguimiento.py` y migración
- [ ] T098 [HU8] Servicio y rutas de hitos, revaluación y `/iniciativas/{id}/evolucion` en `backend/app/servicios/seguimiento.py` y `backend/app/api/seguimiento.py`
- [ ] T099 [P] [HU8] Página Seguimiento con gráfico de evolución en `frontend/src/paginas/Seguimiento.tsx`

---

## Fase 11: HU9 – Mejora continua del marco (P3)

- [ ] T100 [P] [HU9] Prueba de integración: borrador copiado de la vigente; pesos que no suman 1 (422); publicar retira la anterior; versión usada inmutable (409); evaluaciones antiguas conservan su versión en `backend/tests/integration/test_versiones_marco.py`
- [ ] T101 [HU9] Servicio de versiones del marco en `backend/app/servicios/marco.py`
- [ ] T102 [HU9] Rutas `/marco/versiones` (crear, editar, publicar, historial) en `backend/app/api/marco.py`
- [ ] T103 [P] [HU9] Página Administración del marco (pesos con suma en vivo, umbrales, criterios) en `frontend/src/paginas/AdminMarco.tsx`

---

## Fase 12: HU10 – Recomendación de evaluadores (P3, deseable)

- [ ] T104 [P] [HU10] Pruebas unitarias de la heurística (historial, similitud, carga; sin historial → solo función; razón incluida) en `backend/tests/unit/test_sugerencia_evaluadores.py`
- [ ] T105 [HU10] Heurística de sugerencia en `backend/app/servicios/sugerencia_evaluadores.py`
- [ ] T106 [HU10] Ruta `GET /iniciativas/{id}/sugerencias-evaluadores` en `backend/app/api/iniciativas.py`
- [ ] T107 [P] [HU10] Mostrar sugerencias con su razón en `frontend/src/paginas/NuevaIniciativa.tsx` y `frontend/src/paginas/Ficha.tsx`

---

## Fase 13: Cierre y calidad transversal

- [ ] T108 [P] Prueba de punta a punta con Playwright: registrar → estructurar → dos evaluadores → divergencia → consolidar → comité → PDF en `frontend/tests/e2e/flujo_completo.spec.ts`
- [ ] T109 [P] Prueba de rendimiento: consolidación < 5 s con 10 evaluadores (SC-004) en `backend/tests/integration/test_rendimiento.py`
- [ ] T110 [P] Pruebas de contrato contra el OpenAPI generado para todos los recursos de `contracts/api.md` en `backend/tests/contract/`
- [ ] T111 Revisión de seguridad: permisos de cada ruta, CSRF, cabeceras, ausencia de datos personales en llamadas a la IA
- [ ] T112 [P] Guía de inicio rápido (Docker Compose, crear administrador, datos de ejemplo) en `specs/001-validador-viabilidad/quickstart.md` y `README.md`
- [ ] T113 [P] Datos de demostración (3 iniciativas con resultados GO, ITERAR y NO-GO) en `backend/app/semillas/demo.py`
- [ ] T114 Verificar cada criterio de aceptación de `spec.md` y marcar la lista de verificación

---

## Dependencias y orden de ejecución

### Entre fases

```
Fase 1 ─► Fase 2 ─► HU1 ─► HU2 ─► HU3 ─► HU4 ══ MVP
                              │             ├─► HU6 ─┐
                              └─► HU5 ──────┘        ├─► HU7 ─► HU8
                                                     │
                     Fase 2 ─► HU9 (independiente) ──┘
                     HU1 ─► HU10 (independiente)
                                        Todas ─► Fase 13
```

- **Fase 2** bloquea todo.
- **HU1 → HU2 → HU3 → HU4** son secuenciales: cada una usa el estado que deja la anterior.
- **HU5** necesita HU2 (se dispara al estructurar) y su panel se integra en la matriz de HU3.
- **HU6** necesita HU4 (consolidación) y usa el benchmark de HU5 si existe.
- **HU7** necesita HU4; el reporte incluye HU5 y HU6 si existen.
- **HU8** necesita HU7 (decisiones). **HU9** solo necesita la Fase 2. **HU10** solo necesita HU1.

### Dentro de cada historia

1. Pruebas (deben fallar) → 2. Modelos → 3. Lógica de dominio y servicios → 4. Rutas → 5. Interfaz.

### Ejemplo de trabajo en paralelo (HU3)

```
En paralelo: T045, T046, T047, T048   (pruebas)
En paralelo: T049, T050               (modelos y funciones puras)
Luego:       T051 → T052 → T053       (servicios y rutas)
En paralelo: T054, T055               (interfaz)
```

---

## Estrategia de implementación

1. **MVP primero** (Fases 1–6, T001–T065): entregable demostrable del núcleo del Marco NEPXA sin IA.
   Validar con los ejemplos de HU4 antes de seguir.
2. **Incremento 2** (Fases 7–9, T066–T095): IA y comité. Se puede presentar el flujo completo del Marco NEPXA.
3. **Incremento 3** (Fases 10–12, T096–T107): seguimiento, administración del marco y sugerencia de evaluadores.
4. **Cierre** (Fase 13, T108–T114).

Se hace un commit por tarea o grupo lógico de tareas, y se verifica cada punto de control antes de pasar a la fase siguiente.

**Total**: 114 tareas – Preparación 8 · Base 21 · HU1 9 · HU2 6 · HU3 11 · HU4 10 · HU5 14 · HU6 6 · HU7 10 · HU8 4 · HU9 4 · HU10 4 · Cierre 7.
