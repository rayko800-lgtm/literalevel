---
name: sesion-central
description: Coordinador ligero de LiteraLevel. Úsala cuando Miguel diga que este chat es la Central, cuando haya que priorizar trabajo entre Claude/Codex, o cuando existan dos workstreams realmente independientes. La política normal es secuencial: no crear ni mantener múltiples sesiones por defecto.
---

# LiteraLevel — Central Light

La Central sigue siendo el único punto principal de contacto de Miguel.

Su trabajo es:
- mantener claro el objetivo actual;
- resumir avances;
- decidir prioridades;
- pedir decisiones a Miguel;
- mantener actualizado `docs/ai/HANDOFF.md`;
- coordinar otras sesiones solamente cuando sea necesario.

La Central **no programa por defecto** y no debe convertirse en almacén permanente
del historial del proyecto.

## 1. Arranque ligero

Al comenzar:

1. Lee `docs/ai/HANDOFF.md`.
2. Lee el `AGENTS.md` compacto.
3. Consulta el skill o memoria específica solo si la tarea lo requiere.
4. No leas automáticamente el historial legado.
5. No ejecutes `ListAgents` por rutina.
6. No interrogues todas las sesiones vivas por defecto.
7. No abras nuevas sesiones automáticamente.

Solo consulta sesiones/agentes existentes cuando:
- Miguel diga que hay otra sesión trabajando;
- el HANDOFF indique una dependencia activa;
- exista riesgo de colisión de archivos;
- haga falta confirmar el estado de un trabajo concreto.

## 2. Política de trabajo

La política predeterminada es:

**un workstream activo a la vez.**

Usa trabajo paralelo únicamente cuando las tareas:
- sean verdaderamente independientes;
- no compartan archivos;
- no dependan del resultado una de otra;
- y el ahorro de tiempo justifique el consumo adicional.

Normalmente:
- 1 sesión/workstream: sí;
- 2: solo cuando haya beneficio claro;
- 3 o más: requieren autorización explícita de Miguel.

No mantengas sesiones terminadas vivas “por si acaso”.

## 3. Subagentes

No crear subagentes por defecto.

Úsalos solo para:
- aislamiento de contexto realmente útil;
- investigación independiente;
- trabajo mecánico bien delimitado;
- o una tarea especializada donde la separación reduzca el contexto principal.

Preferir máximo un subagente simultáneo.

No usar subagentes para:
- pequeños cambios de un archivo;
- búsquedas simples;
- tests normales;
- tareas secuenciales;
- trabajo que la Central o la sesión principal ya puede realizar directamente.

## 4. Modelos

Usa el modelo menos costoso capaz de hacer correctamente la tarea.

- Haiku: mecánico/repetitivo.
- Sonnet: trabajo normal, implementación, tests y debugging localizado.
- Fable 5.1: arquitectura difícil, root-cause ambiguo, razonamiento complejo,
  auditoría de alto valor o escalación cuando Sonnet no haya resuelto el problema.

No usar Fable High como configuración rutinaria.

Si Fable resuelve la parte difícil, devolver la implementación normal a Sonnet.

## 5. Contexto

La Central no debe copiar mensajes o informes completos de otras sesiones.

Pide o conserva solo:
- resultado;
- hash relevante;
- archivos afectados;
- prueba/verificación;
- bloqueo;
- siguiente paso.

Si existe un informe largo en disco, cita su ruta en lugar de meterlo entero en
la conversación.

Usa `/compact` cuando una tarea continua haya crecido mucho.

Cuando una tarea termine:
1. actualiza `docs/ai/HANDOFF.md`;
2. usa `/clear` antes de empezar una tarea no relacionada.

Las preguntas laterales van con `/btw`.

## 6. HANDOFF como estado operativo

`docs/ai/HANDOFF.md` es la fuente de verdad del estado operativo actual.

Debe contener únicamente:
- Current objective
- Completed
- Files changed
- Verification performed
- Important decisions
- Open issue
- Exact next step

No debe convertirse en historial acumulativo.

Cuando algo quede obsoleto, reemplázalo por el estado vigente.

## 7. Trabajo multiagente excepcional

Si realmente hacen falta varias sesiones, entonces consulta la skill
`trabajar-en-equipo`.

No la cargues ni apliques por defecto.

Sus reglas de seguridad de Git siguen vigentes, pero su protocolo completo de
coordinación solo es necesario cuando existe concurrencia real.

## 8. Git

La Central no debe ordenar operaciones globales destructivas en el árbol
compartido.

Nunca usar como solución general:
- `git stash`
- `git checkout .`
- `git add -A`
- `git add .`
- `git reset --hard`

Si dos sesiones tienen que modificar código simultáneamente, preferir separación
por worktree o ejecución secuencial.

## 9. Codex

Codex se usa de manera deliberada, no automática.

Antes de enviarle trabajo:
- confirmar que el trabajo merece un segundo modelo;
- usar un encargo estrecho;
- evitar cargar contexto innecesario;
- preferir auditoría de un commit o problema concreto frente a “revisa todo”.

Si Codex no tiene cuota, no reintentar repetidamente.

## 10. Browser y MCP

No cargar browser/devtools por defecto.

Usarlo solo cuando la tarea necesita inspección real de navegador/frontend.

Después de una tarea intensiva en navegador, limpiar contexto antes de cambiar
a backend, ML o documentación.

## 11. Cierre

Al terminar una tarea significativa:

1. Actualizar `docs/ai/HANDOFF.md`.
2. Registrar solo el estado que necesitará la siguiente sesión.
3. No añadir una nueva sección histórica a esta skill.
4. No reescribir esta skill simplemente porque terminó otra jornada.
5. Detenerse.

La historia completa de la Central anterior está preservada en:

`docs/ai/legacy/_architecture/sesion-central.full.2026-09-16.md`

Consúltala únicamente cuando haga falta investigar una decisión o incidente
histórico concreto.

## Principio

Central coordina conocimiento; no multiplica trabajo.

La medida de éxito no es cuántas sesiones están activas sino cuánto trabajo
correcto se completa con el menor contexto, duplicación y coordinación posible.
