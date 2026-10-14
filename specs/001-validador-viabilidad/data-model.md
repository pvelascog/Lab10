# Modelo de datos

**Funcionalidad**: `001-validador-viabilidad` | **Fecha**: 2026-10-14

Convenciones: claves primarias `id` (UUID); todas las tablas tienen `creado_en` y `actualizado_en` (UTC).
Los nombres siguen el dominio en español.

---

## Diagrama de relaciones

```
usuario ─┬─< usuario_rol >── rol
         │
         ├─< iniciativa (autor_id, pm_id)
         │      ├─< asignacion_evaluador >── dimension
         │      ├─< evaluacion >── version_marco
         │      │      ├─< envio_dimension
         │      │      ├─< calificacion >── criterio
         │      │      ├─< comentario_divergencia
         │      │      ├── resultado_consolidado (1:1)
         │      │      ├─< recomendacion
         │      │      └─< decision_comite ─< siguiente_paso
         │      ├─< benchmark ─< solucion_benchmark
         │      └─< hito_seguimiento
         │
version_marco ─< dimension ─< criterio ─< nivel_criterio
trabajo_ia (iniciativa_id, evaluacion_id)
auditoria (entidad, entidad_id, usuario_id)
```

---

## Entidades

### Usuarios y acceso

**usuario**
| Campo | Tipo | Reglas |
|-------|------|--------|
| nombre | texto | obligatorio |
| correo | texto | obligatorio, único, minúsculas |
| hash_contrasena | texto | Argon2 |
| activo | booleano | por defecto `true` |
| intentos_fallidos / bloqueado_hasta | entero / fecha-hora | bloqueo tras 5 intentos |

**rol**: `codigo` ∈ {`MIEMBRO`, `PM`, `LIDER_COMERCIAL`, `LIDER_TECNICO`, `LIDER_ESTRATEGIA`, `COMITE`, `ADMIN_MARCO`}.
**usuario_rol**: (`usuario_id`, `rol_id`) único. Un usuario puede tener varios roles.

### Marco de evaluación (versionado)

**version_marco**
| Campo | Tipo | Reglas |
|-------|------|--------|
| numero | texto | p. ej. `3.0`, `3.1`; único |
| estado | enum | `BORRADOR` → `VIGENTE` → `RETIRADA`; solo una `VIGENTE` |
| umbral_critico | decimal | por defecto 2.0 |
| umbral_validar | decimal | por defecto 2.5 (dos o más dimensiones por debajo) |
| umbral_debil | decimal | por defecto 3.0 |
| umbral_score_go / iterar / validar | decimal | por defecto 4.0 / 3.0 / 2.0 |
| umbral_divergencia | entero | por defecto 2 |
| creada_por, notas_cambio | ref usuario, texto | trazabilidad (HU9) |

Una versión `VIGENTE` o `RETIRADA` es **inmutable**; para cambiarla se crea otra versión.

**dimension**
| Campo | Tipo | Reglas |
|-------|------|--------|
| version_marco_id | ref | |
| codigo | texto | `MER`, `COM`, `FIN`, `TEC`, `CMP`, `ECO` |
| nombre, proposito | texto | |
| peso | decimal(9,8) | la suma por versión debe ser exactamente 1 (FR-012, HU9); con pesos iguales la última dimensión absorbe el residuo de redondeo |
| rol_sugerido | código de rol | asignación por defecto de evaluadores (FR-010) |
| orden | entero | |

**criterio**
| Campo | Tipo | Reglas |
|-------|------|--------|
| dimension_id | ref | |
| codigo | texto | `MER-01` … `ECO-04`; único por versión |
| nombre, definicion | texto | |
| escala_original | entero | 5 (o 3 para Recurrencia) |
| calculable | enum | `NO`, `ROI`, `RECUPERACION` (FR-009) |

**nivel_criterio**: (`criterio_id`, `nivel` 1–5) con `descripcion` de la rúbrica. Para Recurrencia se guardan los
niveles 1, 3 y 5 (normalización FR-008), y la interfaz solo ofrece esos tres.

### Iniciativas

**iniciativa**
| Campo | Tipo | Reglas |
|-------|------|--------|
| codigo | texto | legible, p. ej. `INI-2026-0007`; único |
| nombre, descripcion | texto | obligatorios (HU1) |
| origen | enum | `CLIENTES`, `EQUIPO_INTERNO`, `MERCADO`, `SOCIOS`, `TENDENCIAS`, `PORTAFOLIO`, `INNOVACION_INTERNA` |
| autor_id, pm_id | ref usuario | `pm_id` obligatorio para pasar a `ESTRUCTURADA` |
| estado | enum | ver máquina de estados |
| problema, solucion_objetivo, segmento, propuesta_valor | texto | obligatorios para `ESTRUCTURADA` (HU2) |
| supuestos_clave | lista de texto | al menos uno para `ESTRUCTURADA` |
| datos_disponibles | texto | opcional |
| inversion_estimada | decimal | opcional; > 0 si se informa |
| ingresos_esperados | decimal | opcional; ≥ 0 |
| flujo_mensual_neto | decimal | opcional; para el tiempo de recuperación |
| posible_duplicado_de | ref iniciativa | sugerido por similitud trigram ≥ 0.6 |

**asignacion_evaluador**: (`iniciativa_id`, `dimension_codigo`, `usuario_id`) único; `origen` ∈ {`MANUAL`, `SUGERIDA`};
`razon_sugerencia` (texto, HU10). Cada dimensión necesita al menos una asignación para pasar a `EN_EVALUACION`.

### Evaluación

**evaluacion**
| Campo | Tipo | Reglas |
|-------|------|--------|
| iniciativa_id | ref | una iniciativa puede tener varias (revaluación, HU8) |
| version_marco_id | ref | la `VIGENTE` al crearla; no cambia (Principio IV) |
| numero | entero | 1, 2, 3… por iniciativa |
| estado | enum | `ABIERTA` → `CONSOLIDADA` → `DECIDIDA` |

**calificacion**
| Campo | Tipo | Reglas |
|-------|------|--------|
| evaluacion_id, criterio_id | ref | |
| evaluador_id | ref usuario | nulo solo si `origen = IA_SUGERIDA`; único (`evaluacion_id`, `criterio_id`, `evaluador_id`) |
| nivel | entero | 1–5; para Recurrencia ∈ {1, 3, 5} |
| justificacion | texto | **obligatoria** (FR-007) |
| fuente | texto | recomendada |
| origen | enum | `HUMANA`, `IA_SUGERIDA`, `IA_CONFIRMADA`, `CALCULADA_CONFIRMADA` |

Solo cuentan para el puntaje las calificaciones `HUMANA`, `IA_CONFIRMADA` y `CALCULADA_CONFIRMADA` (Principio III).
Las de origen `IA_SUGERIDA` no tienen evaluador humano y se muestran como propuesta.

**envio_dimension**: (`evaluacion_id`, `dimension_codigo`, `evaluador_id`, `enviado_en`). Tras el envío, el evaluador
no puede editar esa dimensión y puede ver las calificaciones de los demás (FR-010b).

**comentario_divergencia**: (`evaluacion_id`, `criterio_id`, `autor_id`, `texto`). Requerido para cada criterio con
divergencia antes de consolidar (FR-010a).

**resultado_consolidado** (1:1 con evaluación; se guarda como fotografía al consolidar)
| Campo | Tipo |
|-------|------|
| puntajes_dimension | JSON `{MER: 4.2, …}` |
| score_total | decimal |
| resultado | enum `GO`, `ITERAR`, `VALIDAR`, `NO_GO` |
| regla_aplicada | texto (p. ej. `R1: dimensión FIN = 1.75 < 2.0`) |
| dimensiones_implicadas | lista de códigos |
| fortalezas, debilidades, riesgos, supuestos_criticos | listas de texto (editables; borrador de IA marcado) |

### IA

**benchmark**: `iniciativa_id`, `estado` (`PENDIENTE`, `COMPLETADO`, `SIN_RESULTADOS`, `FALLIDO`), `consulta_resumen`,
`modelo`, `generado_por_ia = true`, `generado_en`.

**solucion_benchmark**: `benchmark_id`, `nombre`, `descripcion`, `url_fuente` (**obligatoria** y presente en los
resultados reales de la búsqueda), `similitud` (0–1), `propuesta_valor`, `segmento`, `modelo_ingresos`, `diferenciadores`.

**recomendacion**: `evaluacion_id`, `dimension_codigo`, `criterio_codigo` (opcional), `accion`, `prioridad`
(`ALTA`, `MEDIA`, `BAJA`), `supuesto_a_validar`, `generado_por_ia = true`, `aceptada` (booleano, nulo hasta revisar).

**trabajo_ia**: `tipo` (`BENCHMARK`, `RECOMENDACIONES`), `iniciativa_id`, `evaluacion_id`, `estado`
(`EN_COLA`, `EN_CURSO`, `COMPLETADO`, `FALLIDO`), `intentos` (máx. 3), `ultimo_error`, `tomado_en`.

### Comité y seguimiento

**decision_comite**: `evaluacion_id`, `decision` (`GO`, `ITERAR`, `VALIDAR`, `NO_GO`), `justificacion` (obligatoria),
`motivo_diferencia` (obligatorio si `decision ≠ resultado_consolidado.resultado`), `decidida_por`, `participantes`,
`fecha`, `prioridad_portafolio` (entero, opcional).

**siguiente_paso**: `decision_id`, `tipo` (`ROADMAP`, `MVP_PILOTO`, `RECURSOS`, `VALIDAR_SUPUESTO`, `AJUSTE`,
`APRENDIZAJE`), `descripcion`, `responsable_id`, `fecha_objetivo`.

**hito_seguimiento**: `iniciativa_id`, `descripcion`, `fecha_objetivo`, `cumplido`, `objetivos_resultado`,
`supuestos_validados`, `resultados`.

### Auditoría

**auditoria**: `usuario_id`, `accion` (p. ej. `CALIFICAR`, `ENVIAR_DIMENSION`, `CAMBIAR_ESTADO`, `DECIDIR`,
`EDITAR_MARCO`), `entidad`, `entidad_id`, `antes` (JSON), `despues` (JSON), `fecha`. Solo inserción (FR-026).

---

## Máquina de estados de la iniciativa

| Desde | Hacia | Condición | Quién |
|-------|-------|-----------|-------|
| — | `IDENTIFICADA` | nombre, descripción y origen | cualquier usuario |
| `IDENTIFICADA` | `ESTRUCTURADA` | ficha completa y PM asignado; encola benchmark | PM |
| `ESTRUCTURADA` | `EN_EVALUACION` | al menos un evaluador por dimensión; crea `evaluacion` | PM |
| `EN_EVALUACION` | `CONSOLIDADA` | cada criterio con ≥ 1 calificación válida y divergencias comentadas; ejecuta el motor y encola recomendaciones | PM |
| `CONSOLIDADA` | `EN_COMITE` | — | PM |
| `EN_COMITE` | `DECIDIDA` | decisión registrada | COMITE |
| `DECIDIDA` | `EN_SEGUIMIENTO` | decisión GO y siguientes pasos | PM |
| `DECIDIDA` | `ARCHIVADA` | decisión NO-GO y aprendizajes | PM |
| `DECIDIDA` | `EN_EVALUACION` | decisión ITERAR o VALIDAR; nueva `evaluacion` | PM |
| `EN_SEGUIMIENTO` / `ARCHIVADA` | `EN_EVALUACION` | revaluación por cambio de condiciones; nueva `evaluacion` | PM |

Toda transición queda en `auditoria`. Una transición no permitida responde `409 Conflict`.
