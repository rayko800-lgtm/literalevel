---
name: auditoria-literalevel
description: Método de auditoría de LiteraLevel. Úsala cuando Miguel pida auditar, verificar entregables, revisar la demo, comprobar cifras, revisar hallazgos de Codex/Fable o continuar las auditorías. Lee primero docs/ai/AUDIT_STATUS.md y ejecuta únicamente la auditoría indicada.
---

# Auditoría de LiteraLevel

## Principio

Nunca empezar con "revisa todo".

Toda auditoría sigue:

MAPEAR
→ PRIORIZAR
→ VERIFICAR
→ REPRODUCIR
→ CLASIFICAR
→ CORREGIR SOLO LO CONFIRMADO
→ RE-VERIFICAR
→ CERRAR

Auditar no significa cambiar.

Primero demuestra.
Después clasifica.
Solo después decide si hace falta modificar algo.

## Antes de empezar

1. Lee `docs/ai/AUDIT_STATUS.md`.
2. Lee `docs/ai/HANDOFF.md`.
3. Consulta solo las partes relevantes de `AGENTS.md`.
4. Identifica una única auditoría.
5. Márcala `🟡 RUNNING`.

No cargues el historial legado salvo que una decisión histórica concreta lo requiera.

## Política de recursos

- Una auditoría a la vez.
- No abrir subagentes por defecto.
- No abrir sesiones adicionales por defecto.
- No usar Fable/Codex si Git, Python o una suite dirigida pueden resolverlo.
- No usar navegador salvo que la pregunta sea visual o funcional.
- No ejecutar toda la batería de tests si una suite específica demuestra la afirmación.

## Jerarquía de evidencia

Prefiere:

1. código/archivo actual;
2. resultado reproducible;
3. test dirigido;
4. hash/git/artefacto;
5. despliegue servido;
6. HANDOFF;
7. memoria/skill;
8. historia antigua.

Una afirmación de otra sesión no demuestra que algo ocurrió.

## Afirmaciones documentales

Extrae primero solo hechos verificables:

- cifras;
- hashes;
- versiones;
- resultados;
- métricas;
- arquitectura;
- despliegue;
- pruebas;
- reproducibilidad.

Clasifica:

### ALTO
Puede afectar demo, vídeo, privacidad, reproducibilidad o una afirmación central.

### MEDIO
Puede producir una discrepancia visible o documental relevante.

### BAJO
Dato histórico, secundario o claramente fechado.

Verifica ALTO antes que MEDIO.
No gastes recursos en BAJO mientras haya ALTO/MEDIO pendientes.

## Histórico vs vigente

Antes de actualizar una cifra pregunta:

¿describe el estado actual o una medición histórica?

Si es histórica y está correctamente fechada/ligada a un commit:
`HISTÓRICO CORRECTO`.

Si pretende ser actual y ya cambió:
`DOCUMENTACIÓN`.

Nunca combines una cifra medida hoy con un commit donde nunca fue medida.

## Tests

1. Identifica la afirmación.
2. Identifica la suite mínima.
3. Ejecuta únicamente esa suite.
4. Usa modo sin claves/sin gasto cuando exista.

Más pruebas verdes que antes no significa regresión.

Ejemplo:

351 históricas sobre commit X → conservar si está fechado.

354 actuales sobre HEAD → usar solo si el texto pretende describir HEAD.

## Auditoría funcional

Cuando toque demo, prueba el recorrido completo:

inicio
→ bienvenida
→ cuenta
→ perfil
→ búsqueda
→ libro
→ léxico
→ pronunciación
→ resultado

Los tests aislados no sustituyen el recorrido real.

## Browser / MCP

Permitido solamente si se requiere comprobar:

- responsive;
- scroll;
- overlays;
- elementos cortados;
- interacción;
- flujo real;
- estado visual servido.

No usar para algo que Git/Python/tests ya contestan.

## Auditor externo

Codex/Astra o Fable sirven para independencia, no como coeditores.

Una auditoría externa recibe:

- commit congelado;
- alcance acotado;
- preguntas concretas;
- solo lectura;
- sin auditorías anteriores cuando se quiera una revisión ciega.

Cada hallazgo debe incluir:

- ubicación;
- evidencia reproducible;
- severidad;
- impacto;
- prueba mínima.

## Hallazgos externos

Nunca corregir automáticamente.

HALLAZGO
→ Sonnet reproduce

No reproducible:
→ cerrar.

Reproducible MENOR:
→ post-entrega.

Reproducible SERIO:
→ corregir
→ test dirigido
→ repetir frontera/flujo afectado.

## Severidades

- `SERIO`: amenaza demo, privacidad, reproducibilidad o función central.
- `MENOR`: problema real sin impacto inmediato importante.
- `DOCUMENTACIÓN`: producto correcto; texto desactualizado.
- `HISTÓRICO CORRECTO`: dato antiguo correctamente contextualizado.
- `POST-ENTREGA`: mejora válida que no justifica romper el freeze.

## Estados

Usa únicamente:

- ⬜ PENDING
- 🟡 RUNNING
- 🟠 FIX REQUIRED
- 🔵 VERIFY
- ✅ PASSED
- ⏸ DEFERRED
- ❌ FAILED

`✅ PASSED` significa que el criterio de salida está demostrado,
no simplemente que Claude terminó de trabajar.

## Cierre

Al finalizar:

1. actualiza `docs/ai/AUDIT_STATUS.md`;
2. registra evidencia mínima;
3. actualiza HANDOFF si cambió el estado operativo;
4. indica la siguiente auditoría;
5. detente.

No inicies automáticamente la siguiente.

## Formato para Miguel

Entrega el reporte principal dentro de un único bloque `markdown`.

Usa:

# Auditoría — nombre

## Resumen
- Estado:
- Commit:
- Alcance:
- Hallazgos serios:
- Hallazgos menores:

## Hallazgos

### A1 — título
- **Severidad:**
- **Afirmación:**
- **Fuente:**
- **Evidencia:**
- **Resultado:**
- **Acción:**

## Verificaciones pendientes
- ...

## Siguiente paso
1. ...

Evita tablas excesivamente anchas.
Para detalles complejos usa subsecciones.
