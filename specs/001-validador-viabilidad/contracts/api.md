# Contratos de la API REST

**Base**: `/api/v1` | **Formato**: JSON (UTF-8) | **Autenticación**: cookie de sesión `HttpOnly` + cabecera `X-CSRF-Token`
en métodos que modifican datos.

El esquema OpenAPI completo lo genera FastAPI en `/api/v1/openapi.json`; este documento fija los recursos, permisos y
respuestas que las pruebas de contrato verifican.

## Errores comunes

| Código | Uso |
|--------|-----|
| 400 | Datos inválidos (cuerpo `{"detalle": "...", "campos": {"campo": "mensaje"}}`) |
| 401 | Sin sesión |
| 403 | Rol o asignación insuficiente |
| 404 | Recurso inexistente **o no visible** para el usuario (no se revela su existencia) |
| 409 | Transición de estado no permitida o versión del marco inmutable |
| 422 | Regla de negocio incumplida (p. ej. pesos que no suman 100 %, divergencias sin comentar) |
| 429 | Cuenta bloqueada temporalmente tras 5 intentos fallidos de inicio de sesión (15 minutos) |

---

## Autenticación y usuarios

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `POST /auth/login` | `{correo, contrasena}` → fija las cookies `sesion` (HttpOnly) y `csrf`; devuelve `{usuario, csrf}`. 401 con mensaje genérico si las credenciales no son válidas; 429 si la cuenta está bloqueada | público |
| `POST /auth/logout` | Borra las cookies de sesión → 204 | público |
| `GET /auth/yo` | Usuario actual y roles | autenticado |
| `GET /usuarios?rol=` | Lista de usuarios (para asignar evaluadores) | PM, ADMIN_MARCO |
| `POST /usuarios` · `PATCH /usuarios/{id}` | Crear usuario, cambiar roles o desactivar | ADMIN_MARCO |

## Marco

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /marco/vigente` | Versión vigente con dimensiones, pesos, criterios y rúbricas | autenticado |
| `GET /marco/versiones` · `GET /marco/versiones/{id}` | Historial de versiones | autenticado |
| `POST /marco/versiones` | Crea un borrador copiando la vigente | ADMIN_MARCO |
| `PATCH /marco/versiones/{id}` | Edita pesos, umbrales o criterios de un borrador (422 si los pesos no suman 1) | ADMIN_MARCO |
| `POST /marco/versiones/{id}/publicar` | Borrador → vigente; la anterior pasa a retirada | ADMIN_MARCO |

## Iniciativas

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /iniciativas?estado=&origen=&resultado=&desde=&hasta=&orden=` | Backlog visible para el usuario (FR-004, FR-027a). `orden` ∈ `-creado_en` (por defecto), `creado_en`, `nombre`, `-nombre`. El filtro `resultado` se habilita con la consolidación (HU4) | autenticado |
| `POST /iniciativas` | `{nombre, descripcion, origen, asignaciones?: [{dimension, usuario_id}]}` → 201 con el detalle. `posible_duplicado_de = {id, codigo, nombre, similitud}` si la similitud trigram con otra iniciativa es ≥ 0.6; `id` y `nombre` son `null` cuando el usuario no puede ver esa iniciativa | autenticado |
| `GET /iniciativas/{id}` | Ficha, estado, asignaciones y `evaluacion_actual_id` | visible |
| `PATCH /iniciativas/{id}` | Edita la ficha; solo aplica los campos enviados (`null` borra). Solo en `IDENTIFICADA` o `ESTRUCTURADA` (409 en otro estado). `pm_id` solo lo asigna un PM y debe ser un usuario con rol PM. Inversión > 0 e ingresos ≥ 0 (400) | autor, PM de la iniciativa o rol PM |
| `PUT /iniciativas/{id}/asignaciones` | `{asignaciones: [{dimension, usuario_id}]}` reemplaza los evaluadores por dimensión (en `IDENTIFICADA`, `ESTRUCTURADA` o `EN_EVALUACION`). Durante la evaluación se descartan los borradores de quien se retira; 409 si se retira a quien ya envió | PM de la iniciativa o rol PM |
| `GET /iniciativas/{id}/sugerencias-evaluadores` | Sugerencias por dimensión con su razón (HU10) | PM |
| `POST /iniciativas/{id}/transiciones` | `{hacia: "ESTRUCTURADA" \| "EN_EVALUACION" \| …}` → 200 con el detalle; 409 si la transición no existe desde el estado actual; 422 con `campos` = lo que falta | según la tabla de estados |
| `GET /iniciativas/{id}/calculos-financieros` | `{roi, nivel_roi, meses_recuperacion, nivel_recuperacion, faltantes}` calculados con los datos guardados de la ficha; `meses_recuperacion = null` con nivel 1 si el flujo mensual no es positivo | visible |

## Evaluación

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /evaluaciones/{id}` | Matriz por dimensión: mi calificación, avance por evaluador (`calificados`, `enviado`) y, si `ver_calificaciones`, las calificaciones **enviadas** de todos con promedio, divergencia y comentarios (FR-010b). `pendientes` (solo para quien gestiona) = criterios sin calificaciones enviadas o con divergencia sin comentar | visible |
| `PUT /evaluaciones/{id}/calificaciones/{criterio}` | `{nivel, justificacion, fuente?, usa_calculo?}` → guarda o reemplaza el borrador propio. 400 si el nivel no existe en la rúbrica (Recurrencia: 1, 3, 5) o si `usa_calculo` no coincide con el nivel calculado de FIN-02/FIN-03; 409 si la dimensión ya fue enviada | evaluador asignado a la dimensión |
| `POST /evaluaciones/{id}/calificaciones/{criterio}/confirmar-sugerencia` | Convierte una sugerencia de IA en calificación propia, con justificación (HU5). Los niveles calculados se confirman con `usa_calculo` en el `PUT` | evaluador asignado |
| `POST /evaluaciones/{id}/dimensiones/{dimension}/enviar` | Envía la dimensión y publica sus calificaciones (422 con los criterios sin calificar; 409 si ya se envió) | evaluador asignado |
| `GET /evaluaciones/{id}/divergencias` | `[{criterio, dimension, niveles, comentada}]` de las dimensiones que el usuario puede ver | visible |
| `POST /evaluaciones/{id}/divergencias/{criterio}/comentarios` | `{texto}` → 201. 422 si el criterio no tiene una divergencia visible | evaluador de la dimensión o PM |
| `GET /evaluaciones/{id}/resultado` | Resultado consolidado (404 antes de consolidar) | visible |
| `PATCH /evaluaciones/{id}/resultado` | Edita fortalezas, debilidades, riesgos y supuestos | PM |

**Respuesta de `GET /evaluaciones/{id}/resultado`**
```json
{
  "score_total": 4.1667,
  "puntajes_dimension": {"MER": 4.2, "COM": 4.0, "FIN": 3.8, "TEC": 4.5, "CMP": 4.1, "ECO": 4.4},
  "pesos": {"MER": 0.1667, "COM": 0.1667, "FIN": 0.1667, "TEC": 0.1667, "CMP": 0.1667, "ECO": 0.1667},
  "resultado": "GO",
  "regla_aplicada": "R4: score ≥ 4.0 y todas las dimensiones ≥ 3.0",
  "dimensiones_implicadas": [],
  "version_marco": "3.0",
  "fortalezas": ["…"], "debilidades": ["…"], "riesgos": ["…"], "supuestos_criticos": ["…"],
  "borrador_ia": true
}
```

## IA

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /iniciativas/{id}/benchmark` | Último benchmark: estado, soluciones con `url_fuente`, `generado_por_ia: true` | visible |
| `POST /iniciativas/{id}/benchmark` | Reintenta o vuelve a ejecutar → 202 con `trabajo_id` | PM |
| `GET /evaluaciones/{id}/recomendaciones` | Recomendaciones con dimensión, criterio, acción, prioridad, supuesto | visible |
| `POST /evaluaciones/{id}/recomendaciones` | Regenera → 202 | PM |
| `PATCH /recomendaciones/{id}` | `{aceptada: true \| false}` | PM |
| `GET /trabajos/{id}` | Estado del trabajo (`EN_COLA`, `EN_CURSO`, `COMPLETADO`, `FALLIDO`) | visible |

## Comité y seguimiento

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /comite/agenda` | Iniciativas `EN_COMITE` | COMITE |
| `POST /evaluaciones/{id}/decision` | `{decision, justificacion, motivo_diferencia?, participantes, siguientes_pasos: [...]}` → 422 si falta el motivo cuando difiere del recomendado | COMITE |
| `GET /portafolio?orden=prioridad` · `PATCH /decisiones/{id}` | Priorización del portafolio | COMITE |
| `GET/POST /iniciativas/{id}/hitos` · `PATCH /hitos/{id}` | Seguimiento (HU8) | PM |
| `GET /iniciativas/{id}/evolucion` | Puntajes de todas las evaluaciones de la iniciativa | visible |

## Reportes

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /evaluaciones/{id}/reporte` | HTML del resumen ejecutivo (vista imprimible) | visible |
| `GET /evaluaciones/{id}/reporte.pdf` | Mismo contenido en PDF (`application/pdf`) | visible |
