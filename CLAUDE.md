# LiteraLevel

## Antes de trabajar

Para una tarea de código:

1. Lee `docs/ai/HANDOFF.md` para conocer el estado operativo actual.
2. Lee `AGENTS.md` antes de tocar código.
3. Consulta únicamente la skill o memoria específica que necesite la tarea.
4. No cargues automáticamente el historial legado.

Para cualquier entregable del Módulo 5, la skill global
`modulo-5-literalevel` contiene la rúbrica y el contexto académico
autoritativo.

Si dos fuentes antiguas contradicen el código o el HANDOFF actual, no adivines:
identifica la discrepancia y determina primero cuál es el estado vigente.

## Política de recursos

La política normal es **secuencial**.

- Un workstream activo por defecto.
- No crear subagentes automáticamente.
- No abrir sesiones adicionales solo porque una tarea pueda paralelizarse.
- Dos workstreams solo cuando sean realmente independientes y el ahorro de
  tiempo justifique el consumo adicional.
- Tres o más requieren permiso explícito de Miguel.
- No mantener sesiones terminadas vivas "por si acaso".

## Modelos

Usa el modelo menos costoso capaz de resolver correctamente la tarea.

- Haiku: trabajo mecánico y repetitivo.
- Sonnet: implementación normal, pruebas y debugging localizado.
- Fable 5.1: arquitectura difícil, root-cause ambiguo, razonamiento complejo
  o escalación cuando Sonnet no sea suficiente.

No usar Fable High como configuración rutinaria.

Después de resolver una dificultad con Fable, devolver el trabajo ordinario
a Sonnet cuando sea práctico.

## Contexto

- Lee únicamente archivos relevantes para la tarea.
- Empieza con búsquedas y rutas específicas.
- No escanees el repositorio completo sin una razón concreta.
- No vuelvas a leer archivos sin cambios innecesariamente.
- Filtra y resume logs grandes localmente.
- No copies informes completos a la conversación si basta con su ruta, hash,
  conclusión y siguiente paso.
- Usa `/compact` durante una tarea larga cuando el contexto crezca.
- Tras terminar una tarea, actualiza `docs/ai/HANDOFF.md`.
- Usa `/clear` antes de empezar una tarea no relacionada.
- Usa `/btw` para preguntas laterales.

## Central

Cuando este chat sea `[Central]`, usa la skill `sesion-central`.

La Central:
- coordina;
- resume;
- prioriza;
- pide decisiones a Miguel;
- mantiene el HANDOFF.

La Central no debe:
- programar rutinariamente;
- multiplicar sesiones;
- interrogar todos los agentes al arrancar;
- conservar en la conversación todo el historial del proyecto.

## Trabajo multiagente

La skill `trabajar-en-equipo` se usa únicamente cuando existe concurrencia real.

No la cargues por defecto.

Las reglas de seguridad del working tree de `AGENTS.md` se mantienen siempre.

## Ejecución

- Prefiere el cambio correcto más pequeño.
- No refactorices código no relacionado.
- Para cambios pequeños, trabaja directamente.
- Para cambios ambiguos o transversales, identifica primero:
  - archivos mínimos;
  - criterio de éxito;
  - restricciones;
  - verificación necesaria.

## Verificación

- Ejecuta primero la prueba más específica relevante.
- Amplía pruebas solo cuando el cambio cruce componentes, haya fallos o exista
  riesgo real de regresión.
- No repitas pruebas que ya pasaron sin un cambio nuevo o motivo concreto.
- Cuando la petición esté resuelta y la verificación relevante pase, detente.

## Browser / MCP

- Browser/devtools solo cuando la tarea necesita navegador o frontend vivo.
- No usarlo por defecto para Python, ML, backend, documentación o análisis
  estático.
- Después de una sesión pesada de navegador, limpiar contexto antes de cambiar
  a trabajo no relacionado.

## Estado y memoria

Conocimiento estable:
- skill `modulo-5-literalevel`;
- memoria del proyecto;
- `AGENTS.md`.

Estado operativo actual:
- `docs/ai/HANDOFF.md`.

Historia antigua:
- `docs/ai/legacy/_architecture/`.

No cargues la historia completa salvo que necesites investigar una decisión
antigua concreta.

## Principio

Optimizar recursos eliminando contexto redundante, duplicación, agentes
innecesarios, herramientas irrelevantes y verificaciones repetidas.

Nunca ahorrar recursos sacrificando conocimiento importante, corrección o
verificación necesaria.
