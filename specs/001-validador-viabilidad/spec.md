# Especificación de Funcionalidad: Validador de Viabilidad de Productos

**Rama**: `001-validador-viabilidad`
**Creada**: 2026-10-14
**Estado**: Borrador
**Entrada**: "Una máquina que recibe ideas de productos y, basada en unos criterios, califica las iniciativas para
determinar si son viables desde el punto de vista financiero, técnico, de mercado y comercial. Debe incluir
elementos de IA que hagan un benchmark de soluciones cuando se inscriban y recomendaciones para que la idea
se pueda convertir en un producto."

> Esta especificación describe **qué** debe hacer el sistema y **por qué**. No define tecnologías ni arquitectura;
> eso corresponde al `plan.md`.

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 – Inscribir una idea de producto (Prioridad: P1)

Como **emprendedor/proponente**, quiero inscribir mi idea de producto con la información clave
para que pueda ser evaluada.

**Por qué esta prioridad**: sin ideas inscritas no hay nada que evaluar; es la puerta de entrada del sistema.

**Prueba independiente**: se puede verificar inscribiendo una idea completa y comprobando que queda
registrada con estado "Inscrita".

**Escenarios de aceptación**:
1. **Dado** un proponente, **cuando** completa todos los campos obligatorios y envía la idea,
   **entonces** el sistema la registra con un identificador único y estado "Inscrita".
2. **Dado** un proponente, **cuando** omite un campo obligatorio, **entonces** el sistema indica qué campo
   falta y no registra la idea.
3. **Dado** una idea en estado "Inscrita", **cuando** el proponente la edita antes de ser evaluada,
   **entonces** se guardan los cambios.

---

### Historia de usuario 2 – Calificar la viabilidad en cuatro dimensiones (Prioridad: P1)

Como **proponente o evaluador**, quiero que la idea se califique en las dimensiones **financiera, técnica,
de mercado y comercial** para saber si es viable y por qué.

**Por qué esta prioridad**: es el propósito central del validador.

**Prueba independiente**: con una idea de datos conocidos y una configuración de criterios conocida,
el puntaje y el veredicto obtenidos coinciden con los valores esperados.

**Escenarios de aceptación**:
1. **Dado** una idea inscrita, **cuando** se solicita la evaluación, **entonces** el sistema entrega un puntaje
   por cada dimensión, un puntaje global ponderado y un veredicto.
2. **Dado** un resultado de evaluación, **cuando** el usuario lo consulta, **entonces** ve el puntaje, el peso
   y la justificación de cada criterio.
3. **Dado** una dimensión con puntaje por debajo de su umbral mínimo, **cuando** se calcula el veredicto,
   **entonces** la idea no puede ser "Viable" aunque el puntaje global sea alto.
4. **Dado** la misma idea y la misma versión de criterios, **cuando** se evalúa dos veces, **entonces**
   los puntajes de los criterios cuantitativos son idénticos.

---

### Historia de usuario 3 – Benchmark de soluciones existentes con IA (Prioridad: P2)

Como **proponente**, quiero que al inscribir mi idea el sistema identifique soluciones similares o
competidoras y las compare con mi propuesta, para conocer mi diferenciación.

**Por qué esta prioridad**: aporta contexto de mercado clave, pero el validador ya entrega valor sin él.

**Prueba independiente**: inscribiendo una idea de un mercado conocido, el sistema lista soluciones similares
con fuente y una comparación por atributos.

**Escenarios de aceptación**:
1. **Dado** una idea inscrita, **cuando** se ejecuta el benchmark, **entonces** el sistema presenta una lista de
   soluciones similares con nombre, descripción breve, fuente y nivel de similitud.
2. **Dado** el benchmark, **cuando** el usuario lo consulta, **entonces** ve una comparación de la idea frente a
   cada solución (propuesta de valor, precio, segmento, diferenciadores).
3. **Dado** que no se encuentran soluciones similares, **cuando** termina el benchmark, **entonces** el sistema
   lo informa explícitamente y no inventa competidores.
4. **Dado** cualquier resultado del benchmark, **entonces** se marca como "generado por IA".

---

### Historia de usuario 4 – Recomendaciones para convertir la idea en producto (Prioridad: P2)

Como **proponente**, quiero recibir recomendaciones concretas que me ayuden a convertir la idea en un
producto viable, priorizadas según las debilidades detectadas.

**Por qué esta prioridad**: transforma la evaluación en acciones; depende de la evaluación (HU2).

**Prueba independiente**: con una idea evaluada que tiene una dimensión débil, las recomendaciones incluyen
al menos una acción dirigida a esa dimensión.

**Escenarios de aceptación**:
1. **Dado** una idea evaluada, **cuando** se generan recomendaciones, **entonces** cada recomendación indica la
   dimensión que mejora, la acción sugerida y su prioridad (alta, media, baja).
2. **Dado** una idea con veredicto "No viable", **cuando** se generan recomendaciones, **entonces** se priorizan
   las dimensiones que bloquean la viabilidad.
3. **Dado** cualquier recomendación, **entonces** se marca como "generada por IA".

---

### Historia de usuario 5 – Configurar criterios, pesos y umbrales (Prioridad: P3)

Como **administrador**, quiero definir los criterios de cada dimensión, sus pesos y los umbrales de viabilidad,
para adaptar el validador a la política de la organización.

**Por qué esta prioridad**: el sistema puede operar con una configuración por defecto.

**Escenarios de aceptación**:
1. **Dado** un administrador, **cuando** modifica pesos o umbrales, **entonces** se crea una nueva versión de criterios.
2. **Dado** pesos de una dimensión que no suman 100 %, **cuando** se intenta guardar, **entonces** el sistema lo impide.
3. **Dado** evaluaciones previas, **cuando** cambian los criterios, **entonces** las evaluaciones previas conservan
   la versión con la que fueron calificadas.

---

### Historia de usuario 6 – Revisión humana y reporte (Prioridad: P3)

Como **evaluador**, quiero revisar el resultado, ajustar el veredicto con una justificación y exportar un reporte
de viabilidad, para tomar y comunicar la decisión final.

**Escenarios de aceptación**:
1. **Dado** una evaluación, **cuando** el evaluador cambia el veredicto, **entonces** debe ingresar una justificación
   y el sistema registra quién, cuándo y qué cambió.
2. **Dado** una evaluación, **cuando** se solicita el reporte, **entonces** se genera un documento con puntajes,
   justificaciones, benchmark y recomendaciones.
3. **Dado** varias ideas evaluadas, **cuando** el evaluador consulta el listado, **entonces** puede ordenarlas
   y filtrarlas por puntaje global, veredicto y fecha.

---

### Casos límite

- ¿Qué pasa si el servicio de IA no responde? → La calificación (HU2) debe completarse igual; el benchmark y las
  recomendaciones quedan como "pendientes" y pueden reintentarse.
- ¿Qué pasa si la idea tiene información muy escasa o ambigua? → El sistema advierte qué datos faltan y qué
  criterios se calificaron con baja confianza.
- ¿Qué pasa si se inscribe una idea duplicada? → El sistema advierte la posible duplicidad.
- ¿Qué pasa con valores financieros incoherentes (p. ej. costos negativos)? → Se rechazan con un mensaje claro.

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Inscripción**
- **FR-001**: El sistema DEBE permitir inscribir una idea con: nombre, descripción, problema que resuelve,
  cliente objetivo, propuesta de valor, modelo de ingresos, estimación de costos, inversión requerida,
  recursos/tecnología requeridos y competidores conocidos (opcional).
- **FR-002**: El sistema DEBE validar los campos obligatorios y los formatos numéricos antes de registrar.
- **FR-003**: El sistema DEBE asignar un identificador único y un estado a cada idea
  (Inscrita → En evaluación → Evaluada → Revisada).

**Calificación**
- **FR-004**: El sistema DEBE calificar cada idea en cuatro dimensiones: financiera, técnica, de mercado y comercial.
- **FR-005**: Cada dimensión DEBE componerse de criterios con puntaje en una escala común
  [NECESITA ACLARACIÓN: escala de puntaje — ¿0–100, 1–5?].
- **FR-006**: El sistema DEBE calcular un puntaje por dimensión y un puntaje global ponderado.
- **FR-007**: El sistema DEBE emitir un veredicto: **Viable**, **Viable con condiciones** o **No viable**,
  según umbrales globales y umbrales mínimos por dimensión.
- **FR-008**: Cada puntaje DEBE acompañarse de una justificación legible.
- **FR-009**: El sistema DEBE registrar la versión de criterios usada en cada evaluación.

**Benchmark con IA**
- **FR-010**: El sistema DEBE generar, al inscribir una idea, un benchmark de soluciones similares o competidoras.
- **FR-011**: Cada solución del benchmark DEBE incluir fuente y nivel de similitud
  [NECESITA ACLARACIÓN: origen de las soluciones — ¿búsqueda web, base de datos interna de ideas/productos, o ambas?].
- **FR-012**: El benchmark DEBE alimentar la calificación de la dimensión de mercado (competencia y diferenciación).

**Recomendaciones con IA**
- **FR-013**: El sistema DEBE generar recomendaciones accionables a partir de la evaluación y el benchmark.
- **FR-014**: Cada recomendación DEBE indicar dimensión, acción y prioridad.

**Configuración, revisión y reportes**
- **FR-015**: Un administrador DEBE poder configurar criterios, pesos y umbrales, generando versiones.
- **FR-016**: Un evaluador DEBE poder ajustar el veredicto con justificación obligatoria y registro de auditoría.
- **FR-017**: El sistema DEBE generar un reporte de viabilidad exportable
  [NECESITA ACLARACIÓN: formato del reporte — ¿PDF, web, ambos?].
- **FR-018**: El sistema DEBE marcar todo contenido generado por IA como tal.
- **FR-019**: El sistema DEBE restringir el acceso a cada idea a su autor y a los roles autorizados.
- **FR-020**: Los usuarios DEBEN autenticarse [NECESITA ACLARACIÓN: ¿cuentas propias del sistema, o no se requiere
  autenticación para el alcance del laboratorio?].

### Criterios de evaluación propuestos (configuración por defecto)

| Dimensión   | Peso global | Criterios sugeridos                                                                 |
|-------------|-------------|--------------------------------------------------------------------------------------|
| Financiera  | 30 %        | Margen bruto estimado, punto de equilibrio, retorno de inversión, inversión requerida |
| Técnica     | 20 %        | Madurez de la tecnología, complejidad, disponibilidad de capacidades, riesgos técnicos |
| Mercado     | 25 %        | Tamaño del mercado, crecimiento, intensidad competitiva, diferenciación (benchmark)   |
| Comercial   | 25 %        | Claridad de la propuesta de valor, canales de venta, modelo de ingresos, barreras de entrada |

Umbrales por defecto: **Viable** ≥ 70 y ninguna dimensión < 50; **Viable con condiciones** entre 50 y 69,
o global ≥ 70 con alguna dimensión < 50; **No viable** < 50.
[NECESITA ACLARACIÓN: confirmar pesos y umbrales con el curso/organización.]

### Entidades clave

- **Idea de producto**: propuesta inscrita por un proponente; contiene la información de FR-001 y su estado.
- **Usuario / Rol**: Proponente, Evaluador, Administrador.
- **Versión de criterios**: conjunto de dimensiones, criterios, pesos y umbrales vigente en un momento.
- **Evaluación**: resultado de calificar una idea con una versión de criterios; contiene puntajes,
  justificaciones y veredicto.
- **Benchmark**: lista de soluciones comparables con fuente, similitud y comparación por atributos.
- **Recomendación**: acción sugerida vinculada a una dimensión, con prioridad.
- **Registro de auditoría**: cambios de veredicto realizados por evaluadores.

---

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Un proponente puede inscribir una idea completa en menos de 10 minutos.
- **SC-002**: El 100 % de las evaluaciones muestran puntaje, peso y justificación por criterio.
- **SC-003**: La calificación determinista (sin IA) se entrega en menos de 5 segundos.
- **SC-004**: El benchmark y las recomendaciones se entregan en menos de 2 minutos tras la inscripción.
- **SC-005**: El 100 % de las soluciones del benchmark tienen una fuente identificable.
- **SC-006**: En una muestra de ideas revisadas por evaluadores, al menos el 80 % de los veredictos automáticos
  coinciden con el criterio del evaluador.
- **SC-007**: Al menos el 80 % de los proponentes consideran útiles las recomendaciones (encuesta).

---

## Supuestos

- El proyecto es un laboratorio académico; el volumen de usuarios es bajo (decenas de ideas).
- La interfaz y los contenidos estarán en español.
- Se dispone de acceso a un modelo de IA generativa para benchmark y recomendaciones.
- Algunos criterios (p. ej. tamaño de mercado) dependen de datos aportados por el proponente o estimados por IA,
  por lo que se reporta su nivel de confianza.

## Fuera de alcance (por ahora)

- Integración con sistemas financieros o CRM externos.
- Seguimiento del desarrollo del producto después de la evaluación.
- Aplicación móvil nativa.

---

## Lista de verificación de la especificación

- [x] Se describe el qué y el por qué, sin detalles de implementación
- [x] Las historias de usuario son independientes y priorizadas
- [x] Los requisitos son verificables
- [x] Los criterios de éxito son medibles
- [ ] Todos los marcadores `[NECESITA ACLARACIÓN]` están resueltos
