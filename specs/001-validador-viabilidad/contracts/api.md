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

---

## Autenticación y usuarios

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `POST /auth/login` | `{correo, contrasena}` → fija cookie; devuelve usuario y roles | público |
| `POST /auth/logout` | Cierra la sesión | autenticado |
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
| `GET /iniciativas?estado=&origen=&resultado=&desde=&hasta=&orden=` | Backlog visible para el usuario (FR-004, FR-027a) | autenticado |
| `POST /iniciativas` | `{nombre, descripcion, origen, asignaciones?: [{dimension, usuario_id}]}` → 201 con `posible_duplicado_de` | autenticado |
| `GET /iniciativas/{id}` | Ficha, estado, asignaciones, evaluaciones | visible |
| `PATCH /iniciativas/{id}` | Edita la ficha (solo en `IDENTIFICADA` o `ESTRUCTURADA`) | autor o PM |
| `PUT /iniciativas/{id}/asignaciones` | Reemplaza evaluadores por dimensión | PM |
| `GET /iniciativas/{id}/sugerencias-evaluadores` | Sugerencias por dimensión con su razón (HU10) | PM |
| `POST /iniciativas/{id}/transiciones` | `{hacia: "ESTRUCTURADA" \| "EN_EVALUACION" \| …}` → 200 o 409/422 con lo que falta | según la tabla de estados |
| `GET /iniciativas/{id}/calculos-financieros` | ROI, tiempo de recuperación y niveles propuestos | visible |

## Evaluación

| Método y ruta | Descripción | Permiso |
|---------------|-------------|---------|
| `GET /evaluaciones/{id}` | Matriz con avance por dimensión y evaluador; las calificaciones ajenas solo si ya se envió la dimensión (FR-010b) | visible |
| `PUT /evaluaciones/{id}/calificaciones/{criterio}` | `{nivel, justificacion, fuente?}` → guarda borrador propio | evaluador asignado a la dimensión |
| `POST /evaluaciones/{id}/calificaciones/{criterio}/confirmar-sugerencia` | Convierte una sugerencia de IA o un cálculo en calificación propia, con justificación | evaluador asignado |
| `POST /evaluaciones/{id}/dimensiones/{dimension}/enviar` | Envía la dimensión (422 si falta algún criterio) | evaluador asignado |
| `GET /evaluaciones/{id}/divergencias` | Criterios con diferencia ≥ umbral | visible |
| `POST /evaluaciones/{id}/divergencias/{criterio}/comentarios` | `{texto}` | evaluador asignado o PM |
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
