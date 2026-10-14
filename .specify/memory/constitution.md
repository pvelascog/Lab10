# Constitución del Proyecto: Validador de Viabilidad de Productos

> Principios no negociables que guían todas las fases (especificación, plan, tareas e implementación).
> Cualquier decisión de diseño que contradiga un principio debe justificarse explícitamente en el `plan.md`.

## Principios

### I. Especificación primero
Ninguna funcionalidad se implementa sin una especificación (`spec.md`) revisada y sin un plan (`plan.md`) aprobado.
La especificación describe el **qué** y el **por qué**; el plan describe el **cómo**. El código se valida contra
los criterios de aceptación de la especificación.

### II. Calificaciones explicables
Toda calificación en las seis dimensiones del Marco NEPXA (Mercado, Comercial, Financiera y de Inversión,
Técnica, Competencia y Ecosistema) debe mostrar:
- el puntaje obtenido por cada criterio (1 a 5),
- el peso aplicado,
- la justificación y la fuente de la evidencia.

El resultado recomendado debe indicar la regla de decisión que lo determinó: el balance entre dimensiones
es tan importante como el promedio. Una calificación o un resultado sin justificación se considera un defecto.

### III. La IA asiste, la persona decide
Los componentes de IA (benchmark, calificaciones sugeridas y recomendaciones) son **apoyo** a la decisión.
La decisión final (GO, ITERAR, VALIDAR o NO-GO) corresponde al **Comité de Producto**.
- Los resultados de IA se identifican claramente como generados por IA.
- El benchmark debe indicar la fuente de cada solución comparada; no se presentan competidores sin fuente.
- Toda calificación sugerida por IA debe ser confirmada por una persona antes de contar en el puntaje.
- Si el comité decide distinto al resultado recomendado, debe quedar registrado el motivo.

### IV. Criterios configurables y trazables
Los criterios, pesos y umbrales de viabilidad son configurables y versionados. Cada evaluación registra
la versión de criterios con la que fue calificada, de modo que el resultado sea reproducible.

### V. Pruebas como evidencia
Cada historia de usuario tiene pruebas que verifican sus criterios de aceptación. La lógica de puntaje
se prueba de forma determinista (sin depender de la IA). Los componentes de IA se prueban con respuestas simuladas.

### VI. Confidencialidad de las ideas
Las ideas registradas son información sensible: solo las ven su autor y los roles autorizados.
No se envían datos personales del autor a servicios externos de IA.

### VII. Simplicidad
Se construye primero el flujo mínimo de valor (registrar → calificar → ver resultado) y se agregan
capacidades de IA de forma incremental. Se evita la complejidad que no esté justificada por la especificación.

## Flujo de trabajo (Spec-Driven Development)

1. **Constitución** – este documento.
2. **Especificación** – `specs/NNN-nombre/spec.md`.
3. **Clarificación** – resolver los marcadores `[NECESITA ACLARACIÓN]` de la especificación.
4. **Plan** – `specs/NNN-nombre/plan.md` (arquitectura, tecnología, modelo de datos).
5. **Tareas** – `specs/NNN-nombre/tasks.md`.
6. **Implementación** – código y pruebas, verificados contra la especificación.

## Gobernanza

- Esta constitución prevalece sobre cualquier otra práctica del proyecto.
- Las enmiendas se documentan con fecha, motivo y versión.

### Historial de enmiendas
- **1.1.0 (2026-10-14)**: alineación con el Marco de Viabilidad NEPXA v3.0 (seis dimensiones, escala 1–5,
  regla de balance, decisión del Comité de Producto).

**Versión**: 1.1.0 | **Ratificada**: 2026-10-14 | **Última enmienda**: 2026-10-14
