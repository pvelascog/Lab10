# Especificación de Funcionalidad: Validador de Viabilidad de Productos

**Rama**: `001-validador-viabilidad`
**Creada**: 2026-10-14
**Actualizada**: 2026-10-14 – alineada con el *Marco de Viabilidad NEPXA v3.0* (ver [`marco-nepxa.md`](marco-nepxa.md))
**Estado**: Borrador
**Entrada**: "Una máquina que recibe ideas de productos y, basada en unos criterios, califica las iniciativas para
determinar si son viables. Debe incluir elementos de IA que hagan un benchmark de soluciones cuando se inscriban
y recomendaciones para que la idea se pueda convertir en un producto."

> Esta especificación describe **qué** debe hacer el sistema y **por qué**. No define tecnologías ni arquitectura;
> eso corresponde al `plan.md`. Las rúbricas completas de los 28 criterios están en [`marco-nepxa.md`](marco-nepxa.md).

---

## Resumen del modelo

- **6 dimensiones**: Mercado, Comercial, Financiera y de Inversión, Técnica, Competencia y Ecosistema.
- **28 criterios**, cada uno calificado de **1 a 5** con justificación y fuente.
- **Resultado** a partir del promedio ponderado **y** del balance entre dimensiones:
  **GO / Lanzar**, **ITERAR / Desarrollar**, **VALIDAR / Prototipar**, **NO-GO / Descartar**.
- **Decisión final** a cargo del **Comité de Producto**; el sistema entrega un **resultado recomendado**.
- **IA** como apoyo: benchmark de competidores, sugerencia de calificaciones y recomendaciones.

### Ciclo de vida de una iniciativa

```
Identificada ──► Estructurada ──► En evaluación ──► Consolidada ──► En comité ──► Decidida
     ▲                                  ▲                                          │
     │                                  └──────── Revaluación (ITERAR/VALIDAR) ◄────┤
     │                                                                             ├─► En seguimiento (GO)
     └──────────────── Reactivación (cambio de condiciones) ◄── Archivada (NO-GO) ◄─┘
```

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 – Registrar una iniciativa en el backlog (Prioridad: P1)
*Etapa 1 del flujo: Identificación.*

Como **cualquier miembro de la organización**, quiero registrar una idea de producto de forma preliminar
para que entre al backlog de evaluación.

**Prueba independiente**: registrar una idea con datos mínimos y verla en el backlog con estado "Identificada".

**Escenarios de aceptación**:
1. **Dado** un usuario, **cuando** registra nombre, descripción breve y origen de la idea (clientes, equipo interno,
   mercado, socios, tendencias, evolución del portafolio, innovación interna), **entonces** la iniciativa queda en el
   backlog con identificador único y estado "Identificada".
2. **Dado** un registro sin nombre o sin descripción, **cuando** se envía, **entonces** el sistema indica el campo faltante.
3. **Dado** una idea similar a otra ya registrada, **cuando** se registra, **entonces** el sistema advierte la posible duplicidad.

---

### Historia de usuario 2 – Estructurar la ficha de la iniciativa (Prioridad: P1)
*Etapa 2: Estructuración.*

Como **Product Manager**, quiero completar la ficha de la iniciativa para que esté lista para ser evaluada.

**Prueba independiente**: completar la ficha de una iniciativa y verificar que pasa a "Estructurada".

**Escenarios de aceptación**:
1. **Dado** una iniciativa "Identificada", **cuando** el PM completa problema, solución propuesta y objetivo, segmento
   de cliente, propuesta de valor diferencial, supuestos clave y datos disponibles, **entonces** pasa a "Estructurada".
2. **Dado** una ficha incompleta, **cuando** el PM intenta enviarla a evaluación, **entonces** el sistema lista los campos faltantes.
3. **Dado** una ficha, **cuando** el PM registra datos financieros (inversión estimada, ingresos esperados, flujo mensual),
   **entonces** el sistema calcula el ROI y el tiempo de recuperación para apoyar los criterios FIN-02 y FIN-03.

---

### Historia de usuario 3 – Evaluación multidimensional (Prioridad: P1)
*Etapa 3: Evaluación multidimensional.*

Como **miembro del equipo evaluador**, quiero calificar cada criterio de 1 a 5 con justificación y fuente para que la
evaluación se base en evidencia y no en percepciones.

**Prueba independiente**: calificar los 28 criterios de una iniciativa y verificar que la matriz queda completa.

**Escenarios de aceptación**:
1. **Dado** una iniciativa "Estructurada", **cuando** se inicia la evaluación, **entonces** el sistema presenta los criterios
   de las 6 dimensiones con su definición y la descripción de cada nivel (1 a 5).
2. **Dado** un criterio, **cuando** el evaluador lo califica sin justificación, **entonces** el sistema no acepta la calificación.
3. **Dado** un criterio, **cuando** se califica, **entonces** se registra quién calificó, cuándo, la justificación y la fuente.
4. **Dado** varios evaluadores, **cuando** cada uno califica las dimensiones que le corresponden según su rol, **entonces**
   el sistema muestra el avance de la evaluación por dimensión.
5. **Dado** datos financieros en la ficha, **cuando** se evalúan FIN-02 y FIN-03, **entonces** el sistema propone el nivel
   calculado, que el evaluador confirma o ajusta con justificación.

---

### Historia de usuario 4 – Consolidación y resultado recomendado (Prioridad: P1)
*Etapa 4: Consolidación de resultados.*

Como **Product Manager**, quiero que el sistema calcule los puntajes, analice el balance y proponga un resultado para
presentar un resumen ejecutivo al comité.

**Prueba independiente**: con calificaciones y pesos conocidos, el puntaje y el resultado coinciden con los esperados.

**Escenarios de aceptación**:
1. **Dado** una evaluación completa, **cuando** se consolida, **entonces** el sistema calcula el puntaje de cada dimensión,
   el promedio ponderado global y el resultado recomendado según FR-016.
2. **Dado** dimensiones con puntajes 4.2, 4.0, 3.8, 4.5, 4.1 y 4.4 (pesos iguales), **entonces** el promedio es 4.17
   y el resultado es **GO**.
3. **Dado** un promedio de 4.3 con una dimensión en 2.8, **entonces** el resultado es **ITERAR** (dimensión < 3).
4. **Dado** un promedio de 3.4 con dos dimensiones en 2.3 y 2.4, **entonces** el resultado es **VALIDAR** (dos dimensiones < 2.5).
5. **Dado** cualquier promedio con una dimensión en 1.8, **entonces** el resultado es **NO-GO** (regla R1).
6. **Dado** el resultado, **entonces** el resumen ejecutivo incluye: puntajes por dimensión, score total, resultado
   recomendado, regla que lo determinó, fortalezas, debilidades, riesgos y supuestos críticos.
7. **Dado** el resumen, **entonces** se muestra un gráfico radar de las 6 dimensiones.

---

### Historia de usuario 5 – Benchmark de soluciones con IA (Prioridad: P2)

Como **Product Manager**, quiero que al estructurar la iniciativa el sistema identifique soluciones similares o
competidoras para sustentar la dimensión de Competencia.

**Prueba independiente**: con una iniciativa de un mercado conocido, el sistema lista competidores con fuente y comparación.

**Escenarios de aceptación**:
1. **Dado** una iniciativa "Estructurada", **cuando** se ejecuta el benchmark, **entonces** se presentan soluciones similares
   con nombre, descripción, fuente verificable y nivel de similitud.
2. **Dado** el benchmark, **entonces** se compara la iniciativa con cada solución en propuesta de valor, segmento, modelo de
   ingresos y diferenciadores.
3. **Dado** el benchmark, **entonces** el sistema **sugiere** calificaciones para CMP-01 a CMP-04 con su justificación;
   el evaluador las acepta o modifica.
4. **Dado** que no se encuentran soluciones similares, **entonces** el sistema lo informa y no inventa competidores.
5. **Dado** cualquier contenido del benchmark, **entonces** se marca como "generado por IA".

---

### Historia de usuario 6 – Recomendaciones con IA para convertir la idea en producto (Prioridad: P2)

Como **Product Manager**, quiero recibir recomendaciones concretas según las debilidades detectadas para mejorar la
iniciativa o definir los siguientes pasos.

**Escenarios de aceptación**:
1. **Dado** una evaluación consolidada, **cuando** se generan recomendaciones, **entonces** cada una indica la dimensión y
   el criterio que mejora, la acción sugerida, la prioridad (alta, media, baja) y el supuesto que valida.
2. **Dado** un resultado ITERAR o VALIDAR, **entonces** las recomendaciones priorizan las dimensiones < 3 y
   proponen experimentos de validación de supuestos.
3. **Dado** un resultado GO, **entonces** las recomendaciones proponen elementos de roadmap y alcance de MVP o piloto.
4. **Dado** la evaluación, **entonces** la IA propone un borrador de fortalezas, riesgos y supuestos críticos para el resumen ejecutivo.
5. **Dado** cualquier recomendación, **entonces** se marca como "generada por IA".

---

### Historia de usuario 7 – Comité de producto y decisión (Prioridad: P2)
*Etapas 5, 6 y 7: Presentación, Toma de decisión y Siguientes pasos.*

Como **Comité de Producto**, quiero revisar la evaluación y registrar la decisión con su justificación y siguientes pasos.

**Escenarios de aceptación**:
1. **Dado** una iniciativa "Consolidada", **cuando** se agenda en comité, **entonces** pasa a "En comité" y el comité
   ve el resumen ejecutivo, la matriz con justificaciones, el benchmark y las recomendaciones.
2. **Dado** la sesión de comité, **cuando** se registra la decisión (GO, ITERAR, VALIDAR o NO-GO), **entonces** se exige
   una justificación y queda registrado quién decidió y cuándo.
3. **Dado** una decisión distinta al resultado recomendado, **entonces** el sistema exige explicar el motivo.
4. **Dado** la decisión, **entonces** el sistema solicita los siguientes pasos correspondientes:
   - **GO**: roadmap, MVP o piloto, recursos, responsables, plazos e hitos → "En seguimiento".
   - **ITERAR / VALIDAR**: supuestos a validar, ajustes de la propuesta y fecha de nueva evaluación.
   - **NO-GO**: aprendizajes documentados → "Archivada".
5. **Dado** varias iniciativas decididas, **entonces** el comité puede priorizarlas en el portafolio.

---

### Historia de usuario 8 – Seguimiento y revaluación (Prioridad: P3)
*Etapa 8.*

Como **Product Manager**, quiero monitorear las iniciativas aprobadas y revaluar las que cambian de condiciones.

**Escenarios de aceptación**:
1. **Dado** una iniciativa "En seguimiento", **cuando** se alcanza un hito, **entonces** se registra el cumplimiento de
   objetivos, la validación de supuestos y los resultados.
2. **Dado** una iniciativa ITERAR, VALIDAR o archivada, **cuando** se solicita revaluarla, **entonces** se crea una nueva
   evaluación que conserva el historial de evaluaciones anteriores.
3. **Dado** dos evaluaciones de la misma iniciativa, **entonces** el sistema muestra la evolución de los puntajes.

---

### Historia de usuario 9 – Mejora continua del marco (Prioridad: P3)
*Etapa 9: Retroalimentación y mejora continua.*

Como **administrador del marco** (en nombre del Comité de Producto), quiero ajustar criterios, pesos y umbrales para
mejorar la metodología.

**Escenarios de aceptación**:
1. **Dado** un cambio en criterios, pesos o umbrales, **cuando** se guarda, **entonces** se crea una nueva versión del marco.
2. **Dado** pesos de dimensión que no suman 100 %, **entonces** el sistema no permite guardar.
3. **Dado** evaluaciones anteriores, **entonces** conservan la versión del marco con la que fueron calificadas.

---

### Casos límite

- **IA no disponible**: la evaluación y la consolidación (HU3 y HU4) funcionan igual; el benchmark y las recomendaciones
  quedan "pendientes" y se pueden reintentar.
- **Evaluación incompleta**: no se puede consolidar mientras falte algún criterio; el sistema muestra cuáles faltan.
- **Valores en el límite** (promedio exactamente 4.0, dimensión exactamente 3.0, 2.5 o 2.0): se aplican intervalos
  semiabiertos de FR-016 (4.0 → nivel GO; 3.0 no es "< 3").
- **Valores financieros incoherentes** (inversión ≤ 0, ingresos negativos): se rechazan con un mensaje claro.
- **Evaluadores en desacuerdo**: [NECESITA ACLARACIÓN: ¿cada criterio lo califica un solo responsable, o se promedian
  varias calificaciones del mismo criterio?].

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Identificación y estructuración**
- **FR-001**: El sistema DEBE permitir a cualquier usuario registrar una iniciativa con nombre, descripción y origen.
- **FR-002**: El sistema DEBE permitir al PM completar la ficha: problema, solución propuesta y objetivo, segmento de
  cliente, propuesta de valor diferencial, supuestos clave y datos disponibles (incluidos datos financieros opcionales).
- **FR-003**: El sistema DEBE gestionar el ciclo de vida: Identificada → Estructurada → En evaluación → Consolidada →
  En comité → Decidida → En seguimiento / Archivada, con revaluación.
- **FR-004**: El sistema DEBE mantener un backlog de iniciativas filtrable por estado, origen, resultado y fecha.

**Evaluación**
- **FR-005**: El sistema DEBE evaluar las **6 dimensiones** y **28 criterios** definidos en `marco-nepxa.md`, con la
  definición y la rúbrica de cada nivel visibles al calificar.
- **FR-006**: Cada criterio DEBE calificarse con un entero de **1 a 5**.
- **FR-007**: Cada calificación DEBE incluir justificación (obligatoria) y fuente de la evidencia.
- **FR-008**: El criterio **Recurrencia** (escala original 1–3) DEBE normalizarse a 1–5: Baja = 1, Media = 3, Alta = 5.
- **FR-009**: El sistema DEBE calcular ROI (%) = (Ingresos esperados − Inversión) / Inversión × 100 y el tiempo de
  recuperación, y proponer el nivel de FIN-02 y FIN-03 según sus rangos; el límite de un rango pertenece al nivel mejor.
- **FR-010**: El sistema DEBE asignar responsables por dimensión según el rol (configurable). Asignación por defecto:
  Mercado y Comercial → Líder Comercial; Técnica → Líder Técnico; Ecosistema → Líder de Estrategia;
  Financiera y Competencia → Product Manager.

**Consolidación y resultado**
- **FR-011**: El puntaje de una dimensión DEBE ser el promedio simple de sus criterios.
- **FR-012**: El score total DEBE ser el promedio ponderado de las dimensiones; por defecto todas pesan igual (1/6).
- **FR-013**: Los cálculos DEBEN usar los valores sin redondear; la presentación se muestra con 2 decimales.
- **FR-014**: Una dimensión es **crítica** si su puntaje es < 2.0 y **débil** si es < 3.0.
- **FR-015**: El sistema DEBE informar qué regla determinó el resultado recomendado.
- **FR-016**: El resultado recomendado DEBE calcularse aplicando las reglas en este orden (la primera que se cumple prevalece):

  | Orden | Condición | Resultado |
  |-------|-----------|-----------|
  | 1 | Score total < 2.0 **o** alguna dimensión < 2.0 | **NO-GO / Descartar** |
  | 2 | Score total < 3.0 **o** dos o más dimensiones < 2.5 | **VALIDAR / Prototipar** |
  | 3 | Score total < 4.0 **o** alguna dimensión < 3.0 | **ITERAR / Desarrollar** |
  | 4 | En otro caso (score ≥ 4.0 y todas las dimensiones ≥ 3.0) | **GO / Lanzar** |

  [NECESITA ACLARACIÓN: confirmar esta regla de precedencia; la fuente tiene condiciones que se solapan (I-06).]
- **FR-017**: El sistema DEBE generar un resumen ejecutivo con puntajes por dimensión, score total, resultado recomendado,
  fortalezas, debilidades, riesgos, supuestos críticos y un gráfico radar.

**IA**
- **FR-018**: El sistema DEBE generar un benchmark de soluciones similares con fuente verificable y nivel de similitud
  [NECESITA ACLARACIÓN: origen — ¿búsqueda web, base interna de iniciativas/productos NEPXA, o ambas?].
- **FR-019**: El sistema DEBE sugerir calificaciones con justificación para los criterios de Competencia a partir del
  benchmark; la calificación final la confirma una persona.
- **FR-020**: El sistema DEBE generar recomendaciones accionables (dimensión, criterio, acción, prioridad, supuesto a validar)
  según el resultado.
- **FR-021**: El sistema DEBE marcar todo contenido generado por IA y distinguir las calificaciones sugeridas de las confirmadas.

**Comité, seguimiento y gobierno**
- **FR-022**: El Comité de Producto DEBE registrar la decisión (GO, ITERAR, VALIDAR, NO-GO) con justificación obligatoria;
  si difiere del resultado recomendado, DEBE explicar el motivo.
- **FR-023**: El sistema DEBE registrar los siguientes pasos según la decisión (roadmap, MVP o piloto, recursos,
  responsables, plazos e hitos; supuestos a validar; aprendizajes).
- **FR-024**: El sistema DEBE permitir revaluar iniciativas conservando el historial de evaluaciones.
- **FR-025**: El sistema DEBE versionar el marco (criterios, pesos, umbrales) y registrar en cada evaluación la versión usada.
- **FR-026**: El sistema DEBE registrar en auditoría calificaciones, cambios de estado y decisiones (quién, cuándo, qué).
- **FR-027**: El sistema DEBE controlar el acceso por rol: Miembro, Product Manager, Líder Comercial, Líder Técnico,
  Líder de Estrategia, Comité de Producto y Administrador del marco
  [NECESITA ACLARACIÓN: ¿autenticación real o selección simple de rol para el alcance del laboratorio?].
- **FR-028**: El sistema DEBE exportar el resumen ejecutivo
  [NECESITA ACLARACIÓN: formato — ¿PDF, página web o ambos?].

### Entidades clave

- **Iniciativa**: idea de producto con su ficha, origen, estado y responsable (PM).
- **Usuario / Rol**: Miembro, PM, Líder Comercial, Líder Técnico, Líder de Estrategia, Comité, Administrador del marco.
- **Versión del marco**: dimensiones, criterios con rúbricas, pesos y umbrales vigentes.
- **Evaluación**: calificación de una iniciativa con una versión del marco; puede haber varias por iniciativa (revaluación).
- **Calificación de criterio**: puntaje 1–5, justificación, fuente, autor, fecha y si fue sugerida por IA.
- **Resumen ejecutivo**: puntajes, score total, resultado recomendado, fortalezas, debilidades, riesgos y supuestos críticos.
- **Benchmark**: soluciones comparables con fuente, similitud y comparación.
- **Recomendación**: acción sugerida vinculada a dimensión y criterio, con prioridad.
- **Decisión de comité**: resultado, justificación, fecha, participantes y siguientes pasos.
- **Registro de auditoría**: historial de acciones.

---

## Criterios de éxito *(obligatorio)*

- **SC-001**: Un usuario registra una iniciativa en el backlog en menos de 3 minutos; un PM completa la ficha en menos de 15.
- **SC-002**: El 100 % de las calificaciones tienen justificación; el 100 % de los resultados indican la regla aplicada.
- **SC-003**: Para cualquier combinación de puntajes, el resultado recomendado coincide con la tabla de FR-016
  (verificado con pruebas automatizadas que incluyen los valores límite).
- **SC-004**: La consolidación se entrega en menos de 5 segundos; el benchmark y las recomendaciones, en menos de 2 minutos.
- **SC-005**: El 100 % de las soluciones del benchmark tienen una fuente identificable.
- **SC-006**: Al menos el 80 % de las decisiones del comité coinciden con el resultado recomendado.
- **SC-007**: Al menos el 80 % de los PM consideran útiles las recomendaciones (encuesta).

---

## Supuestos

- El marco de referencia es el *Marco de Viabilidad NEPXA v3.0*; se usan 6 dimensiones y 4 resultados (ver I-01 e I-02).
- Montos de referencia para Inversión MVP y Ticket potencial: no definidos en la fuente; se califican por juicio del evaluador
  con justificación hasta que la organización los configure (I-08).
- Proyecto de laboratorio académico con bajo volumen (decenas de iniciativas). Interfaz y contenido en español.
- Se dispone de un modelo de IA generativa para el benchmark y las recomendaciones.

## Fuera de alcance (por ahora)

- Integración real con Nexopus u otros sistemas NEPXA (el criterio ECO-01 se califica manualmente).
- Gestión del roadmap y ejecución del MVP después de la decisión (solo se registran los siguientes pasos e hitos).
- Agenda y convocatoria de las sesiones de comité.
- Aplicación móvil nativa.

---

## Clarificaciones pendientes

| # | Pregunta | Propuesta por defecto |
|---|----------|----------------------|
| C1 | Regla de precedencia de resultados (FR-016) | La regla más restrictiva prevalece (tabla FR-016) |
| C2 | Pesos por dimensión (FR-012) | Iguales: 1/6 cada una |
| C3 | ¿Un evaluador por criterio o varias calificaciones promediadas? | Un responsable por dimensión |
| C4 | Origen del benchmark (FR-018) | Búsqueda web con fuentes citadas |
| C5 | Autenticación (FR-027) | Selección simple de rol (laboratorio) |
| C6 | Formato del reporte (FR-028) | Página web imprimible a PDF |

## Lista de verificación de la especificación

- [x] Se describe el qué y el por qué, sin detalles de implementación
- [x] Las historias de usuario son independientes y priorizadas
- [x] Los requisitos son verificables
- [x] Los criterios de éxito son medibles
- [x] Dimensiones, criterios, escalas y flujo alineados con el Marco NEPXA v3.0
- [ ] Todos los marcadores `[NECESITA ACLARACIÓN]` están resueltos
