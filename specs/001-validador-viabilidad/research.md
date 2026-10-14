# Investigación y decisiones técnicas

**Funcionalidad**: `001-validador-viabilidad` | **Fecha**: 2026-10-14

Cada decisión indica qué se eligió, por qué y qué alternativas se descartaron.

---

## D1. Backend: Python 3.12 + FastAPI
- **Decisión**: FastAPI con Pydantic v2 y SQLAlchemy 2.0.
- **Por qué**: el SDK oficial de Claude para Python está maduro; Pydantic sirve a la vez para validar la API y para
  definir las salidas estructuradas de la IA (`messages.parse`); FastAPI genera OpenAPI automáticamente, útil para
  las pruebas de contrato.
- **Alternativas**: Django (más pesado, ORM menos cómodo con async); Node/Next.js (separaría el lenguaje del SDK
  de las pruebas de propiedades con Hypothesis).

## D2. Base de datos: PostgreSQL 16
- **Decisión**: PostgreSQL con `pg_trgm`; `pgvector` disponible para el RAG futuro.
- **Por qué**: transacciones para el ciclo de vida, `SKIP LOCKED` para la cola de trabajos, similitud de texto para
  duplicados y, a futuro, vectores en el mismo motor.
- **Alternativas**: SQLite (sin `SKIP LOCKED` ni extensiones); MongoDB (el dominio es relacional).

## D3. Frontend: React 18 + Vite + TypeScript
- **Decisión**: SPA con React Router, TanStack Query y Recharts.
- **Por qué**: Recharts trae gráfico radar; TanStack Query simplifica el estado de los trabajos de IA (sondeo hasta "completado").
- **Alternativas**: plantillas del servidor (HTMX) – más simple, pero la matriz de 28 criterios con borradores y
  envío por dimensión es más cómoda en una SPA.

## D4. IA: API de Claude
- **Decisión**: SDK `anthropic`, modelo `claude-opus-5-5`, pensamiento adaptativo, `effort` explícito por tarea.
- **Búsqueda web**: herramienta de servidor `web_search_20260209` (filtrado dinámico incluido; no se declara
  `code_execution` aparte). Los errores de la herramienta llegan como bloque de resultado con `error_code`, no como
  excepción, y se tratan explícitamente.
- **Salidas estructuradas**: `client.messages.parse(..., output_format=ModeloPydantic)`.
- **Dos pasos en el benchmark** (investigar → estructurar): permite validar que cada URL de la salida estructurada
  provenga de un resultado real de la búsqueda, cumpliendo el Principio III (sin competidores sin fuente).
- **Rechazos**: `stop_reason == "refusal"` se maneja siempre; se habilita `fallbacks: "default"`
  (beta `server-side-fallback-2026-07-01`) para reintentar en el servidor con otro modelo.
- **Uso forzado de herramientas**: este modelo no admite `tool_choice` `any`/`tool`; se usa `auto` con instrucciones
  explícitas y, para obtener JSON, salidas estructuradas.
- **Alternativas**: un solo paso con búsqueda y salida estructurada a la vez (no permite verificar las fuentes antes
  de guardar); otros proveedores (fuera del alcance acordado).

## D5. Tareas en segundo plano: tabla en PostgreSQL
- **Decisión**: tabla `trabajo_ia` + proceso trabajador con `SELECT … FOR UPDATE SKIP LOCKED`.
- **Por qué**: Principio VII (simplicidad); sin infraestructura extra; los trabajos sobreviven a reinicios.
- **Alternativas**: Celery/ARQ + Redis (otro servicio que operar); `BackgroundTasks` de FastAPI (se pierden al reiniciar).

## D6. Autenticación
- **Decisión**: cuentas propias, Argon2 para contraseñas, JWT de corta duración en cookie `HttpOnly`, `Secure`,
  `SameSite=Lax`, más token CSRF de doble envío; bloqueo temporal tras 5 intentos fallidos.
- **Por qué**: cumple FR-027 sin depender de un proveedor externo; la cookie evita exponer el token a JavaScript.
- **Alternativas**: SSO corporativo (fuera de alcance, versión futura); token en `localStorage` (expuesto a XSS).

## D7. Reporte PDF: WeasyPrint
- **Decisión**: una plantilla Jinja2 genera el HTML del resumen ejecutivo; WeasyPrint lo convierte a PDF.
  El gráfico radar se genera como SVG en el servidor para que salga igual en la web y en el PDF.
- **Alternativas**: imprimir desde el navegador (resultado variable); Playwright para PDF (más pesado en el servidor).

## D8. Recomendación de evaluadores
- **Decisión**: heurística explicable basada en historial (ver `plan.md`).
- **Por qué**: con decenas de iniciativas no hay datos para entrenar un modelo; la heurística mejora sola a medida
  que crece el historial y cada sugerencia muestra su razón.
- **Alternativas**: modelo de ML (sin datos suficientes); que la IA generativa sugiera personas (enviaría datos
  personales a un servicio externo, contra el Principio VI).

## D9. Redondeo y límites
- **Decisión**: cálculos sin redondear; comparación estricta `<` contra los umbrales; presentación **truncada**
  (no redondeada) a 2 decimales. Así, un score de 3.999 (ITERAR) se muestra 3.99 y nunca aparenta cruzar el umbral de GO.
- **Por qué**: FR-013 y el caso límite de valores en el borde.
