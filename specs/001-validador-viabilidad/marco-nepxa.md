# Requisitos extraídos: Marco de Viabilidad NEPXA v3.0

**Fuente**: documento *NEPXA – Marco Viabilidad v3.0* (texto, tablas de criterios y los diagramas
"Flujo operativo del proceso de evaluación de productos" y "Modelo NEPXA de evaluación de viabilidad de productos").
**Extraído**: 2026-10-14
**Uso**: insumo normativo para `spec.md`. Cuando este documento y la especificación difieran, prevalece la
especificación (que registra las decisiones de clarificación). Las inconsistencias detectadas en la fuente
se listan en la sección 6.

---

## 1. Escala de evaluación

| Puntaje | Significado |
|---------|-------------|
| 5 | Excelente |
| 4 | Bueno |
| 3 | Aceptable |
| 2 | Débil |
| 1 | Muy débil |

- Cada **criterio** se califica de **1 a 5** según la evidencia disponible.
- Cada calificación debe tener **justificación** y **fuente** de la evidencia.
- Cada **dimensión** queda calificada de 1 a 5.

---

## 2. Dimensiones y criterios (6 dimensiones, 28 criterios)

### 2.1 Dimensión de Mercado
**Propósito**: evaluar si existe un problema real, relevante y lo bastante grande para justificar una solución
(dolor real del cliente, no interno; magnitud; frecuencia; urgencia).

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| MER-01 | Tamaño del problema | Magnitud del impacto que el problema genera en las organizaciones (costo, riesgo, tiempo o complejidad) | Impacto marginal, afecta procesos secundarios | Impacto limitado en áreas específicas | Impacto relevante en una función clave | Impacto significativo en varias áreas | Impacto crítico en la operación o ingresos |
| MER-02 | Frecuencia | Qué tan seguido ocurre el problema en la operación de los clientes (ej.: reclamos diarios) | Esporádica | Ocasional | Regular | Frecuente | Constante (core del negocio) |
| MER-03 | Urgencia | Prioridad del problema para el cliente en continuidad operativa, cumplimiento o impacto económico | Nice to have | Baja prioridad | Prioridad media | Alta prioridad | Crítico (bloquea operación / genera pérdidas) |
| MER-04 | Disposición a pagar | Grado en que los clientes están dispuestos a invertir para resolver el problema | No hay presupuesto | Interés bajo / exploratorio | Interés real pero no priorizado | Presupuesto identificado | Ya pagan por resolverlo |
| MER-05 | Evidencia de la demanda | Evidencia objetiva de una necesidad real y actual, más allá de opiniones o hipótesis | Suposición interna | Opiniones sin validar | Conversaciones con clientes | Oportunidades comerciales reales | Demanda activa / ventas en curso |

### 2.2 Dimensión Comercial
**Propósito**: evaluar si el producto se puede vender, monetizar y escalar de forma sostenible
(¿pagarían los prospectos?, ¿precio y margen atractivos para NEPXA?, ¿con qué modelo?, ¿repetible o proyecto único?).

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| COM-01 | Modelo de ingresos | Nivel de definición y viabilidad del esquema de ingresos (SaaS, licencias, servicios) | No definido | Hipótesis débil | Parcial (servicios principalmente) | Mixto (servicios + SaaS) | Claro y escalable (SaaS dominante) |
| COM-02 | Ticket potencial | Valor económico promedio que se puede generar por cliente | Bajo | Bajo–medio | Medio | Alto | Muy alto (estratégico) |
| COM-03 | Escalabilidad | Capacidad de crecer en ingresos sin aumentar proporcionalmente los costos operativos | 100 % servicios | Alta dependencia de servicios | Mixto | Escalable con soporte limitado | Altamente escalable (SaaS puro) |
| COM-04 | Recurrencia ⚠️ | Probabilidad de generar una relación comercial de mediano o largo plazo mediante renovaciones | Baja | Media | Alta | — | — |
| COM-05 | Facilidad de venta | Complejidad para explicar, posicionar y cerrar la venta | Difícil de explicar | Complejo / requiere evangelización | Venta consultiva estándar | Problema claro y entendible | Dolor evidente / compra natural |
| COM-06 | Venta integrada | Capacidad de formar parte de soluciones más amplias del portafolio NEPXA (se vende solo o en conjunto; potencia otras soluciones) | Totalmente aislado | Integración débil | Integrable | Parte de soluciones | Núcleo de ofertas integradas |

⚠️ COM-04 usa una escala de 1 a 3 en la fuente (ver inconsistencia I-04).

### 2.3 Dimensión Financiera y de Inversión
**Propósito**: evaluar la viabilidad económica (inversión requerida, tiempo de recuperación, rentabilidad esperada, riesgo financiero).

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| FIN-01 | Inversión MVP | Esfuerzo económico para construir una versión funcional (personas, licencias, infraestructura) | Muy alta | Alta | Media | Baja | Muy baja |
| FIN-02 | Tiempo de recuperación | Tiempo estimado para recuperar la inversión inicial | > 36 meses | 24–36 meses | 12–24 meses | 6–12 meses | < 6 meses |
| FIN-03 | Potencial de ROI | Relación entre utilidad esperada e inversión. **ROI (%) = (Ingresos esperados − Inversión) / Inversión × 100** | < 25 % | 25–50 % | 50–75 % | 75–100 % | > 100 % |
| FIN-04 | Riesgo financiero | Incertidumbre sobre ingresos, adopción y costos | Muy alto | Alto | Medio | Bajo | Muy bajo |

> FIN-02 y FIN-03 son **calculables** a partir de datos numéricos (inversión, ingresos esperados, flujo mensual);
> el resto de criterios son de juicio experto basado en evidencia.

### 2.4 Dimensión Técnica
**Propósito**: determinar si NEPXA puede construir, integrar y operar el producto de forma eficiente y escalable
(complejidad real, encaje con la arquitectura, dependencias externas, capacidad del equipo).

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| TEC-01 | Complejidad técnica | Dificultad para diseñar, desarrollar e implementar (algoritmos, integraciones, arquitectura, incertidumbre técnica) | Muy alta / incierta | Alta | Media | Baja | Muy baja / trivial |
| TEC-02 | Alineación con arquitectura | Compatibilidad con la arquitectura actual de NEPXA | No encaja | Requiere cambios grandes | Ajustes moderados | Encaja bien | Encaje natural |
| TEC-03 | Capacidad del equipo | Preparación del equipo interno para desarrollar y mantener (necesidad de contratación o capacitación) | No disponible | Muy limitada | Parcial | Suficiente | Totalmente cubierta |
| TEC-04 | Dependencias | Dependencia de terceros (proveedores, APIs, infraestructura externa); control sobre la solución | Críticas y externas | Altas | Moderadas | Bajas | Mínimas / control total |
| TEC-05 | Tiempo de desarrollo | Tiempo estimado para construir el MVP (time to market) | > 12 meses | 9–12 meses | 4–9 meses | 2–4 meses | < 2 meses |

### 2.5 Dimensión Competencia
**Propósito**: identificar y calificar la ventaja real que tiene o tendrá NEPXA para competir en el mercado.

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| CMP-01 | Diferenciación | Nivel en que la solución ofrece algo único frente a alternativas existentes | Commodity | Baja | Moderada | Clara | Única / fuerte |
| CMP-02 | Competencia | Cantidad y fuerza de competidores con soluciones similares | Muy alta | Alta | Media | Baja | Muy baja |
| CMP-03 | Barreras de entrada | Dificultad para que otros desarrollen o copien una solución similar | Nulas | Bajas | Moderadas | Altas | Muy altas |
| CMP-04 | Posicionamiento | Claridad y fuerza con la que la solución se entiende y diferencia (facilidad del mensaje comercial) | Confuso | Difícil de explicar | Entendible | Claro | Muy claro y diferenciador |

> Esta dimensión es la que más se apoya en el **benchmark con IA** (competidores actuales y potenciales).

### 2.6 Dimensión Ecosistema
**Propósito**: identificar si el producto fortalece o debilita el ecosistema integrado de NEPXA
(integración con **Nexopus**, sinergia con otras soluciones, reutilización de capacidades, potencial de cross-selling).

| ID | Criterio | Definición | 1 | 2 | 3 | 4 | 5 |
|----|----------|------------|---|---|---|---|---|
| ECO-01 | Integración | Conexión funcional y técnica con la plataforma central (Nexopus) | Independiente | Baja | Integrable | Integrado | Nativo |
| ECO-02 | Sinergia | Capacidad de complementar y potenciar otros productos del portafolio | Aislado | Baja | Media | Alta | Muy alta |
| ECO-03 | Reutilización | Aprovechamiento de componentes, desarrollos o funcionalidades existentes | Todo nuevo | Baja | Media | Alta | Muy alta |
| ECO-04 | Cross-selling | Capacidad de generar ventas adicionales en el mismo cliente | No genera | Bajo | Medio | Alto | Muy alto |

---

## 3. Modelo de decisión

### 3.1 Cómo se obtiene el resultado (según la fuente)
1. **Calificar** cada dimensión de 1 a 5 según los criterios definidos.
2. **Calcular el promedio ponderado**, aplicando el peso definido para cada dimensión.
3. **Analizar el balance**: verificar el equilibrio e identificar dimensiones críticas.
4. **Determinar el resultado recomendado**: asignar la categoría y definir próximos pasos.
5. **Definir los siguientes pasos**: validar, iterar, desarrollar o lanzar.

> "El resultado no depende solo del promedio, sino del equilibrio entre las 6 dimensiones."
> "El balance entre dimensiones es tan importante como el promedio."

### 3.2 Resultados posibles

| Resultado | Promedio | Condición de balance | Interpretación |
|-----------|----------|----------------------|----------------|
| **GO / Lanzar** | 4.0 – 5.0 | Sin dimensiones críticas (< 3) | Alta viabilidad; fortalezas en las 6 dimensiones y buen balance |
| **ITERAR / Desarrollar** | 3.0 – 3.9 | Una o más dimensiones entre 2 y 3 | Viabilidad media-alta; existen debilidades por mejorar |
| **VALIDAR / Prototipar** | 2.0 – 2.9 | Dos o más dimensiones < 2.5 | Viabilidad baja; alta incertidumbre en varias dimensiones |
| **NO-GO / Descartar** | 1.0 – 1.9 | Una o más dimensiones críticas (< 2) | Muy baja viabilidad; riesgos críticos en la mayoría de dimensiones |

### 3.3 Reglas clave
- **R1**: Ninguna dimensión crítica puede estar por debajo de 2.
- **R2**: El balance entre dimensiones es tan importante como el promedio.
- **R3**: Se debe reevaluar si cambian supuestos clave del entorno.

---

## 4. Flujo operativo de evaluación (9 etapas)

| # | Etapa | Actividades | Responsable | Salida |
|---|-------|-------------|-------------|--------|
| 1 | Identificación de la iniciativa | Detectar necesidades, oportunidades o ideas. Fuentes: clientes, equipo interno, mercado, socios, tendencias, evolución del portafolio, innovación interna. Captura preliminar. | Cualquier miembro de NEPXA | Registro inicial en el **backlog de evaluación** |
| 2 | Estructuración de la iniciativa | Completar la ficha: problema, solución propuesta y objetivo, segmento de cliente, propuesta/valor diferencial, supuestos clave y primeros datos disponibles. | Product Manager | Ficha lista para evaluar |
| 3 | Evaluación multidimensional | Aplicar la matriz en las 6 dimensiones; calificar cada criterio de 1 a 5 según evidencia; documentar justificación y fuentes. Evaluación colaborativa. | Equipo evaluador multidisciplinario (producto, negocio, tecnología) | Matriz calificada |
| 4 | Consolidación de resultados | Calcular promedio ponderado por dimensión; determinar resultado general y nivel de viabilidad; identificar fortalezas, debilidades, riesgos y supuestos críticos. | Product Manager | **Resumen ejecutivo**: puntajes por dimensión, score total, fortalezas, riesgos, supuestos críticos |
| 5 | Presentación en comité de producto | Presentar iniciativa, evaluación, supuestos y resultados; discutir hallazgos, riesgos y oportunidades; validar justificaciones; resolver dudas. | Product Manager | Evaluación discutida |
| 6 | Toma de decisión | El comité decide según el resultado y el contexto estratégico (GO, ITERAR, VALIDAR, NO-GO). La decisión se documenta con su justificación. | Comité de Producto | Decisión documentada |
| 7 | Definición de siguientes pasos | GO: roadmap, inicio de MVP o piloto, asignación de recursos. ITERAR: validar supuestos, ajustar propuesta, nueva evaluación. NO-GO: archivar iniciativa, documentar aprendizajes. Asignar responsables, recursos, plazos e hitos. | Product Manager | Plan de acción |
| 8 | Seguimiento y revaluación | Monitorear avances, indicadores y aprendizajes (cumplimiento de objetivos, validación de supuestos, resultados). Revaluar en hitos o ante cambios relevantes; las descartadas o iteradas pueden revaluarse. | Equipo + PM | Evaluación actualizada |
| 9 | Retroalimentación y mejora continua | Capturar aprendizajes del proceso; mejorar criterios, pesos y metodología. | Comité de Producto | Nueva versión del marco |

**Principios del flujo**: estandarización, trazabilidad, colaboración, enfoque en valor, iteración continua,
objetividad, transparencia, enfoque estratégico, adaptabilidad y creación de valor.

---

## 5. Roles y responsabilidades

| Rol | Responsabilidades en el proceso |
|-----|--------------------------------|
| **Product Manager** | Formular la propuesta de valor; documentar problema y segmento; consolidar la información; presentar en comité; incorporar ajustes; liderar la evolución si se aprueba. |
| **Líder Comercial / Negocio** | Validar el problema en clientes reales; evaluar disposición a pagar y potencial de ingresos; identificar oportunidades de venta y posicionamiento; aportar evidencia de demanda. |
| **Líder Técnico / Arquitectura** | Evaluar complejidad; validar encaje con la arquitectura; identificar dependencias y riesgos; estimar tiempos de desarrollo. |
| **Líder de Estrategia / Dirección** | Validar coherencia con la estrategia; evaluar impacto en el portafolio; analizar contribución al ecosistema; tomar decisiones finales en el comité. |
| **Comité de Producto** | Revisar evaluaciones y justificaciones; identificar riesgos y supuestos críticos; definir la decisión; priorizar iniciativas del portafolio. Integrado por producto, negocio, tecnología y dirección. |

**Principios de gobierno**: basado en evidencia, multidisciplinario, transparente, iterativo y alineado a la estrategia.

---

## 6. Inconsistencias y vacíos detectados en la fuente

| ID | Hallazgo | Propuesta para la especificación |
|----|----------|----------------------------------|
| I-01 | El texto ("Evaluación multidimensional", "Gobierno de producto") lista **5 dimensiones** y omite la Financiera; las tablas de criterios y el modelo de decisión usan **6**. El flujo dice "5 (o 6)". | Usar **6 dimensiones**. |
| I-02 | El texto define **3 decisiones** (GO, ITERAR, NO-GO); el modelo de decisión y el flujo definen **4** (incluye VALIDAR / Prototipar). | Usar **4 resultados**. |
| I-03 | Se menciona "el peso definido para cada dimensión", pero **no se definen pesos**. | Pesos iguales (1/6) por defecto y configurables. |
| I-04 | **Recurrencia** (COM-04) tiene escala 1–3; el resto, 1–5. | Normalizar a 1–5: Baja = 1, Media = 3, Alta = 5. |
| I-05 | No se indica cómo se obtiene el puntaje de una dimensión a partir de sus criterios. | Promedio simple de sus criterios. |
| I-06 | Las condiciones de resultado se **solapan** (p. ej. promedio 4.2 con una dimensión en 1.8 cumple GO por promedio y NO-GO por balance) y los rangos dejan huecos (3.9–4.0). | Aplicar la **regla más restrictiva** con intervalos semiabiertos (ver `spec.md`, FR-016). |
| I-07 | Los rangos numéricos de FIN-02, FIN-03 y TEC-05 comparten límites (p. ej. 12 meses aparece en "6–12" y "12–24"). | El límite pertenece al nivel **mejor**: 12 meses → 4; 50 % → 3. |
| I-08 | FIN-01 (Inversión MVP) y COM-02 (Ticket potencial) no tienen montos de referencia. | Montos configurables por la organización; mientras tanto, juicio del evaluador con justificación. |
| I-09 | Los textos del diagrama de dimensiones no siempre coinciden con los criterios de las tablas (p. ej. Mercado menciona "crecimiento, segmentación"; Financiera, "apalancamiento comercial"). | Las **tablas de criterios** son la referencia. |
| I-10 | El texto del flujo tiene 8 etapas; el diagrama tiene 9 (agrega "Retroalimentación y mejora continua"). | Usar **9 etapas**. |
| I-11 | No se define qué rol califica cada dimensión. | Asignación sugerida (configurable): Mercado y Comercial → Líder Comercial; Técnica → Líder Técnico; Ecosistema → Líder de Estrategia; Financiera y Competencia → PM con Líder Comercial. |
