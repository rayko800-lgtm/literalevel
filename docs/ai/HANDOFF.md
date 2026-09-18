# LiteraLevel — AI Handoff

Keep this document short and current.

It is operational state, not a historical diary.

## Current objective

Llegar a la demo en vivo y al vídeo del fin de semana del 19-20 sep con la
app, el motor y los guiones cerrados. Nada de código nuevo salvo un SERIO.

## Completed

- Front en la revisión **ec68419** (commit `8a992af`): bienvenida guiada de
  pasos (pregunta si ya hay cuenta), giro de la cara 3D limitado
  (azimut −34°/+20°, polar 75°–96°, medido), frase de Pronunciar visible
  entera al grabar, «Corrígeme» funcional sin sesión, plurales corregidos.
- Motor en la revisión **72f3cdc** (commit `61e3bba`): el aviso de límite
  horario nombra el cubo agotado; el aviso de acento dice explícitamente
  que no se compara la sílaba tónica.
- Guiones cerrados en **c1fcfd4** (sobre commits previos ad51d05, 1415160):
  incluyen las dos medidas del 16 sep con su origen, «Ensáyalo con cuenta»
  y ningún total inventado.
- Ensayo final hecho sobre esas tres versiones exactas (commit 004eb28).
- Texto «assessors»/«accessors» retirado a petición de Miguel (ya no lo
  recuerda como queja) — cerrado como deducible del código, no reabrir.

## Files changed

Nada tocado en esta sesión (Central no edita código). Los commits de arriba
son de otras sesiones (b0/4e, a3/e6); ver `AGENTS.md` para el reparto actual
de archivos y quién audita `reader.py`/`lexicon.py`/`voz.py` (Codex).

## Verification performed

- Rotación 3D medida con límites reales (no de código leído, de la app).
- Prueba del lienzo 3D (borde) confirmada: llegó a 815 al forzar — **no** era
  ciega, se corrigió el conteo de pruebas ciegas de 5 a 4.
- Límite horario comprobado con cronómetro real (11:32 → 49 min, 11:51 → 30
  min), no de memoria.
- Mensaje de acento y de límite verificados en pantalla, no solo en código.

## Important decisions

- El límite horario **no se toca**: es por IP, no por cuenta; no existe
  «eximir por cuenta». Antes de una demo, comprobarlo con esa misma
  conexión y no gastar correcciones en la hora previa.
- `app/catalogo.py` y `app/cuentas.py` siguen **congelados** hasta después
  del 20 sep, salvo SERIO de demo o de usuarios ([[congelacion-hasta-la-entrega]]).
- Blender (labios, corte de apertura) queda pospuesto: lo pidió Miguel
  expresamente para después de la entrega.
- La doble bienvenida en la demo se mantiene tal cual; el guion avisa de
  ella en vez de suprimirla.

## Desarrollo v2 (rama `dev/onboarding-v2`, 17 sep)

**D1 → ✅ COMPLETE.** El tutorial guiado (D1.1-D1.5 + D1.V) queda cerrado
como experiencia, verificado por prueba humana real de Miguel, sin tocar
`master` (sigue en `004eb28`). HEAD de cierre: `8f2e51e`. El onboarding
recorre entrada/intención → búsqueda/libro → lector/léxico/Pronunciar →
cierre, y solo D1.5 puede marcarlo `completado`. Sigue detrás de un flag de
desarrollo (`localStorage['literalevel.tutorial-dev']` o `?tutorialv2=on`);
nada de esto es visible para un usuario normal todavía — el corte a
producción queda pendiente de que Miguel lo pida.

**D1.V** pasó por tres intentos: 1) inválido, solo se probó Bienvenida v1
(activación corregida en `dd9c902`); 2) prueba humana real que encontró tres
problemas de UX en Pronunciar, corregidos en `8f2e51e` (ya no manda a pulsar
«Corrígeme» cuando la app sabe que está bloqueado, guía hacia «Continuar
leyendo» tras un error, copy recortado); 3) repetición aprobada por Miguel —
recorrido anónimo, Pronunciar adaptativo, sin usuario atrapado, «Continuar
leyendo» con regreso correcto al libro y posición. **D1.V → ✅ PASSED.**
Feedback de 2D/3D del vídeo queda registrado para D4, sin implementar.
Detalle: `docs/ai/DEVELOPMENT_STATUS.md` (sección D1.V).

La infraestructura temporal de la prueba remota (túnel Cloudflare, `ng
serve`, meta de API y `allowedHosts` en el worktree) quedó cerrada y
revertida tras la aprobación; el worktree está limpio.

**H1 (higiene de tests, commit `2cd01a8`):** el ruido preexistente
`el.scrollTo is not a function` en la suite era una fuga real de
temporizador en `lector.ts` (un `setTimeout` de `recolocar()` sin limpiar
en `ngOnDestroy`, a diferencia de los otros tres del componente), no una
limitación de jsdom. Corregido con el mismo patrón que los demás. Suite
completa: 35/35, 274/274, **0 errores** (antes 6). Detalle:
`docs/ai/DEVELOPMENT_STATUS.md` (sección H1).

**D2 → ✅ PASSED (rama `dev/navigation-v2`, creada desde el checkpoint
`2cd01a8` de `dev/onboarding-v2`, no desde `master`).** Diseño aprobado con
correcciones: D2 fue hardening, no reconstrucción — "Continuar leyendo" ya
existía en Inicio, `LeerEntrada` y Pronunciar (D1.4), todos reutilizando
`sesion.inicio()?.seguir` (cache del front, no canónica), alimentado
exclusivamente por `PUT /api/libros/:id/progreso` (`biblioteca.json` por
`X-Lector`, la fuente canónica — **sin relación con la cuenta/login**: la
estantería no sincroniza entre dispositivos aunque haya cuenta). Sin
estado "Terminado" (registrado para D3: requiere evento explícito, no
inferible de `avance`). 23 tests nuevos/extendidos cierran el hueco de
cobertura; un test con temporizadores reales reprodujo un bug real
distinto al de H1 (rAF de `restaurarPosicion()` sin invalidar en
`ngOnDestroy`), corregido con el mismo mecanismo de `token` que ya usaba
`cargar()`. Suite completa: 38/38, **290/290**, 0 errores. Commits:
`f26c548` (preservación de `docs/ai/` operativo, sin trackear hasta ahora)
y `7ee50f9` (D2). Detalle: `docs/ai/DEVELOPMENT_STATUS.md` (sección D2).

**D3 → ✅ COMPLETE** (rama `dev/mi-espacio-v2`, creada desde el checkpoint
`5ab6555` de `dev/navigation-v2`, no desde `master`). UX0 → ✅ PASSED
("Continuar leyendo" fijo en la barra de acciones de Pronunciar, móvil).
D3.1 → ✅ PASSED (Inicio evoluciona a "Mi espacio" para el lector
recurrente — sin `/espacio` nueva, sin quinta pestaña; criterio: libros,
consultas o un nivel ya medido). **D3.2 → ✅ PASSED**: Repaso pasa de
"voltear tarjetas" a recuerdo activo con persistencia real — evaluación
identificada por `consulta_id` (la consulta exacta, no solo el lema),
tabla nueva `repasos` (append-only, migración automática vía el mismo
`_ESQUEMA` que ya crea `consultas`, sin tocar ninguna fila existente),
ruta propia `/repasar`. Sin repetición espaciada todavía (`para_repasar()`
intacto). Verificado con las cuatro suites en verde, incluida
`pruebas_extremas.py` completa (354/354). **D3.3 → ✅ PASSED**: `GET
/api/progreso` agrega palabras consultadas por día (14 días, **día LOCAL
real del navegador** vía `zoneinfo`, nunca UTC del servidor) y resultados
de los últimos 20 repasos — nunca anotaciones completas. Sección "Mi
progreso" en Mi espacio (barras CSS, sin librería), y en la ficha de un
libro de un solo capítulo, comparación real nivel-vs-dificultad en vez de
una curva falsa de un punto. Nada de "palabras aprendidas"/"retención"/
"dominio" en ningún copy. **D3.V → ✅ PASSED**: Miguel completó el
recorrido conjunto (Inicio→Mi espacio→Continuar leyendo→Mis palabras→
Repasar→resumen→Mi progreso) más los spot checks; funcionalidad principal
correcta, dos fricciones de UX en móvil resueltas aparte (ver más abajo).
Detalle: `docs/ai/DEVELOPMENT_STATUS.md` (sección D3).

**UX post-D3 (microfixes, commit `1fba1c9`) → ✅ PASSED:** dos fricciones
de D3.V resueltas antes de D4 — UX-F1 (toast inmediato, no modal, al
pedir explicación contextual sin perfil/cuenta, mismo criterio que ya usa
Pronunciar) y UX-F2 (`capturar()` limpia la selección nativa de Android/
Chrome con `removeAllRanges()` solo tras aceptar la palabra, nunca
antes). Suite del front: 41/41, **329/329**, 0 errores. Detalle:
`docs/ai/DEVELOPMENT_STATUS.md` (sección "UX post-D3").

Próximo: D4 (visualización articulatoria), pendiente de que Miguel lo
pida — no se empieza automáticamente.

**Nota:** los ensayos completos de D1.4 (grabar + Corrígeme de verdad)
consumen cupo real de Corrígeme; evitar repeticiones innecesarias al
probar.

## A7 — Primer ensayo funcional (16 sep, tarde) 🔵 VERIFY

Fricción de navegación real y una pausa perceptible en operaciones largas
salieron en el primer ensayo. Para la demo final: **no ejecutar "Medir el
libro entero" en directo**, usar el resultado precalculado o "Vistazo
rápido". A7 sigue en VERIFY hasta un segundo ensayo cronometrado (hoja de
tiempos completa). Seis ideas de producto derivadas del ensayo quedaron en
`docs/ai/PRODUCT_ROADMAP.md`, todas POST-ENTREGA, sin código tocado.

## A5 — Corpus externo (16 sep, tarde) ✅ PASSED

Todas las cifras verificadas exactas y reproducibles directamente (no solo
por auditoría previa): fuente 14.506/328/280/253, nivel 766/5.696/5.491/
2.524/777/113, `raro_en_bloque` 92, y "225 cambian de letra: 42 suben, 183
bajan" reproducido diferenciando `catalogo_externo.csv` en `a557288` contra
HEAD. Sin ediciones: nada estaba desactualizado. Detalle en
`docs/ai/AUDIT_STATUS.md` (A5).

## A4 — Cierre (16 sep, tarde) ✅ PASSED

Dos correcciones documentales mínimas aplicadas y verificadas en el PDF
compilado:
- `entrega/documento.tex:1171` y `entrega/estrategia.md:669` (A6): la cifra
  vigente de textos libres excluidos por no ser lectura en inglés pasó de
  "163" a "3524357 (163 entonces, 203 hoy)" — 600 (Gutenberg, `db366b8`) no
  se tocó.
- `entrega/documento.tex:1175` y `entrega/estrategia.md:671` (A8): el
  criterio de éxito pasó de presente ("Existe...están hechas") a condicional
  ("Estará hecho cuando exista...estén hechas"), consistente con la fila
  que ya marcaba A8 como pendiente sobre Angular.

Ningún otro accionable ni código de aplicación se tocó. Tablero
(`docs/ai/AUDIT_STATUS.md`) al día; próxima auditoría marcada: A5 — Corpus
externo, sin empezar hasta que Miguel lo pida.

## A3 — Catálogo (16 sep, tarde) ✅ PASSED

Las cuatro cifras centrales del catálogo se reprodujeron localmente y son
exactas: 53.179 IDs Gutenberg (`catalogo_medido.csv`), 585.111 capítulos
(`capitulos_medidos.parquet`), 15.367 textos libres con su desglose por
fuente y nivel (`catalogo_externo.csv`), y 68.546 total (`ui.catalogo().df`,
el mismo campo que sirve `/api/estado`). Cero discrepancias. Detalle en
`docs/ai/AUDIT_STATUS.md` (A3). Próxima auditoría del tablero: A4 —
Accionables A1-A10, sin empezar hasta que Miguel lo pida.

## A2 — Cierre (16 sep, tarde) ✅ PASSED

Sin ediciones: las cuatro ocurrencias de 351/34 de 34 en `documento.tex`
(líneas 1090-1091, 1202) y `estrategia.md` (líneas 472-473, 693) están
explícitamente fechadas ("del 15 de septiembre", árbol `0319290`/`1643c4b`,
"corte anterior `d58b0be`") y citan su propia evidencia
(`DESPLIEGUE.md`). Ninguna afirma el resultado vigente sin fecha/árbol, así
que no califican para la sincronización autorizada. No se tocó ningún .tex;
no hizo falta recompilar. R2 (`a1c4268`/`9b4a3b5`) se deja igual, como pidió
Miguel.

## Auditoría dirigida — Ronda 1 (16 sep, tarde)

- `entrega/guion_video.md` corregido: la cita de "el front publicado" para
  la boca 3D pasó de `f4920fa`/`a656c2e` (11:19, anterior al giro limitado
  `a70af4e` y a todo el paso 0 de bienvenida) a `ec68419`/`8a992af` (front
  vigente). Único archivo modificado en esta ronda.
- Pruebas ejecutadas hoy, sin claves: API 66/66 (exacto), corpus 48/48
  (exacto), extremas 354/354 (documento cita 351 — desactualizado, no
  fallo), voz_concurrencia 10/10 (exacto), voz_ritmo ("lectura natural")
  38/38 (documento cita 34/34 de `d58b0be` — desactualizado, no fallo).
  Ningún fallo real encontrado.
- Pendiente de decidir con Miguel: si vale la pena actualizar las cifras de
  pruebas en documento.tex/estrategia.md (351→354, 34→38) antes de entregar,
  dado que están congelados salvo SERIO y esto no es SERIO.

## Reconciliation check (16 sep, sesión Central posterior)

- Fase A confirmada de solo lectura: HEAD sigue en 004eb28, coincide con
  front ec68419/8a992af y motor 72f3cdc/61e3bba (blob a blob) — ver
  `auditoria/ensayo_demo_final_2026-09-16.md`. Nada pendiente de repo ni de
  despliegue.
- Fase B (documentos de entrega) con comprobaciones puntuales, no lectura
  completa: hashes citados en `documento.tex` (8ee42f0/7c09d90/ab4e36f) son
  narrativa histórica del cambio a Angular, no estado actual — correctos tal
  cual. Conteo de "40 rutas" en `app/api.py` sigue exacto. Menciones a
  Gradio como interfaz están marcadas como "de entonces", no vigentes. Sin
  hallazgos que requieran editar documento.tex, estrategia.md o
  presentacion.tex. Miguel decidió no hacer lectura completa línea por línea
  (280 KB) a dos días de la demo.
- Nota aparte, no bloqueante: `docs/ai/HANDOFF.md` y `docs/` en general
  siguen sin commitear (untracked); `corpus_abierto.parquet` aparece
  modificado sin relación con esta tarea — revisar en la próxima sesión que
  toque commits.

## Open issue

- Cola completa de trabajo post-entrega en
  `auditoria/cola_tras_la_entrega_2026-09-16.md`: pruebas que no pueden
  fallar, mensajes de servidor poco claros (p. ej. en inglés), el esquema
  de voz.py:171-173 (reservado para la auditoría de Codex del 19 sep), y
  el traslado de la caché de HF a D:.
- Ninguno de los pendientes bloquea la demo ni el vídeo.

## Exact next step

1. Miguel cronometra la demo completa con su cuenta antes del fin de
   semana, sin gastar correcciones en la hora previa a grabar.
2. Lanzar Codex el 19 sep a las 9:00 (comprobar cupo con una llamada de una
   palabra antes) usando el encargo ya redactado.
3. Recorrer o saltar ambas bienvenidas antes de compartir pantalla.
4. Grabar vídeo y demo el 19-20 sep.
5. No iniciar trabajo nuevo de código sin petición explícita de Miguel.
