# LiteraLevel — Audit Status

Última actualización: 16 sep 2026

## Leyenda

- ⬜ PENDING
- 🟡 RUNNING
- 🟠 FIX REQUIRED
- 🔵 VERIFY
- ✅ PASSED
- ⏸ DEFERRED
- ❌ FAILED

---

## Estado general

**Fase:** PRE-FREEZE

**HEAD de referencia:** `004eb28`

**Front vigente:** `ec68419` / `8a992af`

**Motor vigente:** `72f3cdc` / `61e3bba`

**Código nuevo antes de entrega:** congelado salvo SERIO confirmado.

---

# A0 — Reconciliación del estado real

**Status:** ✅ PASSED

## Criterio de salida

- HEAD contrastado contra HANDOFF.
- Front vigente identificado y desplegado.
- Motor vigente identificado y desplegado.
- No existen arreglos desconocidos pendientes de repo/despliegue.

## Evidencia

- HEAD `004eb28`.
- Front `ec68419` / `8a992af`.
- Motor `72f3cdc` / `61e3bba`.
- `auditoria/ensayo_demo_final_2026-09-16.md`.

---

# A1 — Inventario de afirmaciones verificables

**Status:** ✅ PASSED

## Criterio de salida

- Entregables relevantes inspeccionados de forma dirigida.
- Afirmaciones verificables inventariadas.
- Riesgo asignado antes de ejecutar comprobaciones costosas.

## Resultado

- Un caso de alto riesgo detectado en `guion_video.md`.
- Grupos de riesgo medio identificados.
- Bajo riesgo diferido.

---

# A2 — Auditoría dirigida Ronda 1

**Status:** ✅ PASSED

## Alcance

- referencia del front en `guion_video.md`;
- cifras publicadas de suites;
- hashes presentados como estado actual.

## Resultado

- A1 del guion corregido hacia front vigente.
- 66/66 API confirmado.
- 48/48 corpus confirmado.
- 10/10 voz concurrente confirmado.
- pruebas extremas actuales: 354.
- lectura natural actual: 38/38.
- Las cifras históricas 351 y 34/34 se conservaron porque están explícitamente
  fechadas y ligadas a commits anteriores.
- 0 fallos de aplicación encontrados.

## Criterio de salida

✅ Cumplido.

---

# A3 — Catálogo

**Status:** ✅ PASSED

## Verificar

- 53.179 libros/IDs Gutenberg;
- 585.111 capítulos;
- 15.367 textos libres;
- 68.546 vectores/estado;
- reparto por nivel citado en entregables.

## Fuente de verdad

- CSV actuales;
- API/estado si corresponde;
- scripts de recuento reproducibles.

## Resultado

- `catalogo_medido.csv`: 53.179 filas, 53.179 IDs únicos — exacto.
- `capitulos_medidos.parquet`: 585.111 filas, 53.179 libros únicos — exacto.
- `catalogo_externo.csv`: 15.367 filas — exacto; desglose por fuente exacto
  (storyweaver 14.506, letsread 328, african_storybook 280, voa 253);
  reparto por nivel exacto (766 A1, 5.696 A2, 5.491 B1, 2.524 B2, 777 C1,
  113 C2).
- `ui.catalogo().df` cargado localmente: 68.546 filas — exacto, y es el
  mismo campo (`len(cat.df)`) que expone `/api/estado` en `app/api.py:760`.
- `corpus_abierto.parquet` sigue con la diferencia binaria ya anotada
  (mismas 15.367 filas, bytes distintos, sin commitear) — no afecta ninguna
  cifra de esta auditoría.
- 0 discrepancias. Las cuatro cifras centrales son VIGENTES Y CORRECTAS,
  no solo históricas.

## Criterio de salida

✅ Cumplido: cifras centrales contrastadas, cero cifra central no
sustentada, sin discrepancias que clasificar.

---

# A4 — Accionables A1–A10

**Status:** ✅ PASSED

## Verificar

Estado declarado de los accionables del documento/estrategia.

Especial atención:
- elementos marcados HECHO;
- HECHO a medias;
- parcial;
- pendiente;
- A8 y sus correcciones.

## Resultado

Inventario A1-A10 verificado. 8 correctos, 2 discrepancias, ambas corregidas:
- A6: "163 textos libres" → "3524357 (163 entonces, 203 hoy)" en
  `documento.tex:1171` y `estrategia.md:669`. `db366b8`/600 y el resto de la
  fila quedaron intactos.
- A8: "Existe una lista priorizada de hallazgos y las tres primeras
  correcciones están hechas" → "Estará hecho cuando exista una lista
  priorizada de hallazgos y las tres primeras correcciones estén hechas"
  en `documento.tex:1175` y `estrategia.md:671`. Consistente con la fila
  "Producto" que ya marcaba A8 como "pendiente" sobre Angular.

`documento.tex` recompilado con tectonic; texto verificado en el PDF
(`163 entonces`, `203 hoy`, `Estará hecho cuando...estén hechas` presentes;
"Existe una lista priorizada" ausente). Overfull \hbox preexistentes en
otras líneas (1281, 1968, 2011, 2778, 2892, 2976, 3020), no relacionados con
esta edición.

## Criterio de salida

✅ Cumplido: cada estado importante corresponde al repo/despliegue/evidencia
real; ninguna acción pendiente se presenta como terminada.

---

# A5 — Corpus externo

**Status:** ✅ PASSED

## Verificar

- StoryWeaver;
- Let's Read;
- African Storybook;
- VOA;
- textos medidos en bloque;
- cifras derivadas del cierre de corpus.

## Resultado

Todas las cifras del checklist son exactas y reproducibles directamente
desde `catalogo_externo.csv` y `git show`, sin depender de auditorías
anteriores como única evidencia:
- fuente: 14.506/328/280/253 (total 15.367) — exacto.
- nivel: 766/5.696/5.491/2.524/777/113 — exacto.
- `raro_en_bloque`: 92 — exacto.
- medida texto/bloque: 11.039/4.328 hoy — consistente con el log histórico
  citado (11.039/4.318 en `377a650`, +10 desde entonces).
- "225 cambian de letra frente al reinicio 19 (42 suben, 183 bajan)":
  reproducido diferenciando `catalogo_externo.csv` en `a557288` (el commit
  justo antes de `740eb84`, que introdujo el cambio) contra el HEAD actual:
  **225 exacto, 42 suben (16 A2→B2, 16 B1→B2, 8 B1→C1, 2 A2→B1) y 183 bajan
  exacto**, coincide dígito a dígito con el documento y con el desglose de
  `auditoria/ronda3_2026-09-15_reinicio21.md`.
- El párrafo de "894 fuera... la salida de cerrar_corpus.py dice..." está
  correctamente anclado a `377a650` ("cuando eran 15.357"): HISTÓRICO
  CORRECTO. Nota de contexto: un recuento posterior (`auditoria/ronda2_2026-09-15_catalogo.md`,
  sobre `6945046`) ya había señalado 884 como cifra corregida en ese punto
  intermedio; es consistente con que el "fuera" bajara 10 al crecer
  "bloque" de 4.318 a 4.328. No requiere cambio porque el documento nunca
  afirma 894 como vigente, solo como lo que decía el log en esa fecha.

0 desactualizadas, 0 sobreafirmadas, 0 no reproducibles, 0 fallos de
aplicación.

## Criterio de salida

✅ Cumplido: totales reproducibles directamente (no solo por artefacto),
documentación consistente e internamente coherente.

---

# A6 — Bajo riesgo documental

**Status:** ⏸ DEFERRED — hasta después de las auditorías funcionales (A7) y
externas (A8-A10), por decisión de Miguel (16 sep).

## Alcance

Solo si A3-A5 están limpias y queda tiempo:

- accesibilidad/contrastes;
- tamaños de datos;
- costes;
- timings históricos;
- descarga Gutenberg;
- portadas;
- citas externas.

## Regla

No gastar recursos aquí mientras exista una auditoría de riesgo medio/alto pendiente.

---

# A7 — Auditoría funcional de demo

**Status:** 🔵 VERIFY — primer ensayo hecho, hace falta un segundo ensayo
cronometrado antes de PASSED o FIX REQUIRED.

## Ya existe

Ensayo final sobre versiones congeladas + primer ensayo funcional de Miguel
(16 sep).

## Resultado del primer ensayo (16 sep)

- Fricción de navegación real durante el recorrido (ver
  `docs/ai/PRODUCT_ROADMAP.md` #1 para la mejora post-entrega; para la
  demo, el guion vigente ya dice cómo saltar/recorrer las bienvenidas).
- Pausa perceptible durante operaciones largas (no cuantificada aún con
  precisión; pendiente de que el segundo ensayo la cronometre).
- **Para la demo final: NO ejecutar "Medir el libro entero" en directo.**
  Usar el resultado ya precalculado o "Vistazo rápido" — es lo que ya
  recomienda el guion para la curva de *Crime and Punishment* (queda
  guardada y sale al momento), pero el ensayo confirma que hay que evitar
  también cualquier medición en vivo de un libro completo en otros pasos.
- Ningún fallo bloqueante reportado en el primer ensayo, pero no se
  completó un cronometraje formal — de ahí que quede en VERIFY y no en
  PASSED.

## Pendiente

Segundo ensayo cronometrado con la hoja de tiempos completa, evitando
"Medir el libro entero" en vivo, para decidir entre ✅ PASSED y 🟠 FIX
REQUIRED.

## Criterio de salida

- recorrido completo sin bloqueo;
- tiempo adecuado;
- bienvenidas controladas;
- pronunciación disponible;
- ningún paso contradice el guion.

---

# A8 — Auditoría visual / móvil

**Status:** ⬜ PENDING

## Herramienta autorizada

Browser/devtools únicamente para esta auditoría.

## Verificar

- viewport móvil;
- scroll;
- texto cortado;
- overlays;
- botones;
- contraste;
- Pronunciar;
- comportamiento durante pantalla compartida.

## Criterio de salida

- flujo visible usable en viewport objetivo;
- cero problema SERIO visual conocido.

---

# A9 — Auditoría independiente Codex/Astra

**Status:** ⬜ PENDING

**Fecha prevista:** 19 sep 2026

## Entrada

- commit congelado;
- alcance acotado;
- preguntas cerradas;
- sin informes anteriores;
- solo lectura.

## Regla

Codex NO corrige código.

## Salida esperada

`auditoria/auditoria_final_codex_2026-09-19.md`

---

# A10 — Verificación de hallazgos externos

**Status:** ⬜ PENDING

## Flujo

Codex/Fable
→ hallazgo
→ Sonnet reproduce

No reproducible
→ cerrar.

Reproducible MENOR
→ post-entrega.

Reproducible SERIO
→ corregir.

---

# A11 — Re-test de correcciones

**Status:** ⬜ PENDING

Solo se ejecuta si A10 genera correcciones.

## Criterio

- test dirigido verde;
- fronteras afectadas verificadas;
- paso de demo afectado repetido.

---

# A12 — Freeze final

**Status:** ⬜ PENDING

## Criterio de salida

- código congelado;
- documentos sincronizados;
- auditorías prioritarias cerradas;
- hallazgos externos resueltos;
- pruebas relevantes verdes;
- HEAD final registrado;
- front final registrado;
- motor final registrado.

## Salida

Crear/actualizar un registro final de freeze.

---

# A13 — Vídeo y demo

**Status:** ⬜ PENDING

## Criterio

- vídeo grabado;
- demo cronometrada;
- guiones definitivos;
- versión mostrada coincide con versión auditada.

---

# Próxima auditoría

**A6 — Bajo riesgo documental** (solo si no hay auditoría de riesgo
medio/alto pendiente; revisar A7-A13 antes de decidir)

No iniciar automáticamente.
Esperar instrucción de Miguel.

---

# E1 — Auditoría de la entrega del Módulo 5 (29 sep 2026, 18:30)

**Status:** 🔵 VERIFY (A1, A2, A6 corregidas y medidas a las 19:15; falta la ejecución en Colab real, el ensayo de la demo y las decisiones de Miguel A3/A4/A7)

## Criterio de salida

- Nota simulada ≥ 80 con notebook ejecutado en limpio, demo ensayada y copia del vídeo decidida.

## Evidencia

- `auditoria/preentrega_2026-09-29.md` (nota 86/110; A1 SERIO: copia local del notebook sin salidas por regeneración en sitio; A2–A5 menores).
- `auditoria/mecanica_2026-09-29.json` (37 OK · 5 avisos · 1 fallo).
- Recorrido real a 390 px en `pleyade-app.vercel.app`: 0 errores de consola, Eos y boca 3D funcionando.

## Siguiente

- Bajar de Colab la copia ejecutada del notebook; ensayo de la demo; adjuntar el 720p H.264.

---

# E2 — Segunda auditoría de la entrega (30 sep 2026, 01:40)

**Status:** 🔵 VERIFY (89/110; 0 serios; falta Colab real, ensayo de la demo y las decisiones de Miguel sobre el vídeo y Classroom)

## Evidencia

- `auditoria/preentrega_2026-09-30.md`; `auditoria/mecanica_2026-09-30.json` (38 OK · 4 avisos · 0 fallos).
- Notebook ejecutado en carpeta limpia fuera del repo: 57 celdas, 1–57, 0 errores, 0 stderr (segunda vez).
- Recorrido real a 390 px en producción sin errores; vídeo 720p con SHA256 igual al registrado.

## Siguiente

- Colab real con Miguel delante; volver a adjuntar en Classroom; ensayo de la demo.
