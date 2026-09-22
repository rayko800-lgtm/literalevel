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

**D4 2D articulatorio → ✅ COMPLETE / FROZEN.** Miguel aprobó la
geometría en el checkpoint `f8db895`: quedan congeladas la lengua, las
rutas de aire, contactos, constricciones, timings internos, el ciclo base
de 2.0 s y la lógica fonética, salvo que una auditoría futura demuestre un
error real. El selector discreto de velocidad (`44d25f9`) ofrece 0.25×,
0.50×, 1.00× y 1.25× y gobierna audio, SVG 2D y reproducción sincronizada
3D sin cambiar anatomía ni tono. Verificación: 44/44 archivos y 388/388
pruebas del front, más comprobación móvil real a 390 px. **D4 global no
está COMPLETE:** continúa con la auditoría enfocada D4.4 del 3D actual.

Próximo: D4.4, decidir por familia qué puede resolverse en runtime
(visibilidad, cámara/target y material) y qué requiere Blender
(geometría/shape keys), sin remodelar todavía.

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

### Audio D4 · publicado · 21 sep 2026, ~22:40

**Estado: los 85 fonemas del AFI suenan con la voz de Miguel en producción.**

- Grabación terminada: 61 fichas con 5/5 piezas + 24 consonantes cubiertas por su pareja GA/RP (`build/grabador/compartidos.json`). 0 fichas sin cubrir. Las 305 piezas en verde, sin hashes repetidos entre tomas.
- Montaje: `build/grabador/montar2.py` → `candidate/{ga,rp}/<hex>.mp3` + `manifiesto2.json`. Formato A de Miguel sin cambios (sostenido · 0,7 s · corto 0,45 s · 0,7 s · palabra; mono 24 kHz; pico −1,0 ±0,3 dBFS medido sobre el mp3).
  - Reglas fijas, no juicios: oclusivas/africadas = las tres tomas en orden como tres golpes (hueco 0,5 s); sostenidos = la toma en verde con mejor SNR; palabra = la de mejor SNR de las dos. Qué toma se usó en cada asset: `manifiesto2.json`, campos `fonema_piezas` y `palabra_pieza`.
  - Recorte de silencios nuevo (grupo de sonido más energético ±60 ms): el de `montar.py` dejaba hasta 2 s delante en /t/ y /k/ y vaciaba el «corto». Piloto de 4 antes del lote.
  - Encoder forzado a mono (el de `montar.py` sacaba estéreo).
- Verificación (`verificar2.py` → `verificacion2.json`): **85/85** pasan pico, clipping, 24 kHz mono, estructura de eventos y silencio inicial < 0,5 s (tope del visor 3D). 24 hashes repetidos = exactamente los 24 pares compartidos.
- Sincronía con la boca, medida a 390 px:
  - dev (`dev/articulacion-v2`, front 4200 + API local): el corte 2D dura lo que el mp3 dividido por la velocidad a 0,25/0,5/1/1,25×; el audio suena a esa velocidad con `preservesPitch`; el 3D decodifica el mp3 nuevo entero (5,19 s en /p/). Los 85 servidos = candidatos por sha256.
  - producción: /s/ 5,01 s → corte 5,00 s; /p/ 5,19 → 5,20; /æ/ 4,51 → 4,50; con «Despacio» /s/ → 10,00 s y audio a 0,5× con tono conservado.
- Commits: `ed2cce6` en `dev/articulacion-v2` y `cbd12f4` en `master` (solo los 85 mp3, `git diff --cached` sin nada más). Sin push.
- Space `MikeMaki1763/literalevel`: revisión antes `72f3cdce0225a8ddd24d2ee68bfcf7332e23e75f` → después `8c8f7f17e17a140a791002d44d918f64e17adbab` (subido con `desplegar_app.py --solo` y las 85 rutas). RUNNING; `/api/salud` `{"estado":"ok"}`; `/api/fonemas?acento=ga|rp` 200; **85/85 mp3 servidos = locales por sha256**; Gradio `/` 200; front 302 → index.html.
- **Vuelta atrás**: `python tools/desplegar_app.py --commit 004eb28 --solo <las 85 rutas>` (bytes del commit anterior), o las copias de `build/grabador/produccion_anterior/{ga,rp}` (sha256 del conjunto `a7eae0af…1bb4`).
- Respaldo: `C:\Users\laura\Downloads\literalevel_grabador_2026-09-21_final.zip` (20 778 393 B, md5 `95132e8c2a1d23c0c7324357eb5b3ecc`, 523 archivos, 329 en `crudo/`).
- **Para Miguel por la mañana**: página de escucha `https://fraser-newest-assessing-glance.trycloudflare.com/escucha.html`, con nuevo y anterior, las 5 tomas (las usadas en azul), Bien/Mal y nota, y «Copiar resultado».
- A oír con atención: /dʒ/ (GA y RP comparten), cuyas tres tomas duran ~1,4 s cada una frente a 0,1–0,4 s de /tʃ/, y el asset sale de 8,4 s.
- Sigue abierto: el ciclo único del 2D/3D se estira sobre todo el mp3 (sostenido + corto + palabra), igual que con los audios anteriores. Es consecuencia del formato A y no se ha tocado.
- Procesos del grabador vivos (29844 servidor, 34412 vigilante, 37196 túnel): no cerrar hasta que Miguel termine la escucha.

### Audio D4 · CERRADO · 22 sep 2026

- **Validado de oído por Miguel: 85/85 OK** (41 GA + 44 RP) en `escucha.html`. Pegó el resultado de «Copiar resultado» en la sesión [ejecutora]. Registro: `build/grabador/validacion_miguel_2026-09-22.json`. No se cambia ninguna toma.
- En producción: commit `cbd12f4` (master, solo los 85 mp3) y Space `MikeMaki1763/literalevel` en la revisión `8c8f7f17e17a140a791002d44d918f64e17adbab`. En dev: `ed2cce6`.
- Vuelta atrás: `python tools/desplegar_app.py --commit 004eb28 --solo <las 85 rutas>` o `build/grabador/produccion_anterior/{ga,rp}`.
- Infraestructura del grabador **cerrada** el 22 sep: cloudflared 37196, servidor 29844 y vigilante 34412 parados y comprobados. El puerto 8989 ya no escucha y la URL trycloudflare responde 530. `crudo/`, masters y respaldos intactos (zip en `Downloads\literalevel_grabador_2026-09-21_final.zip`).
- Siguiente fase: **D4.4b (Blender), sin empezar.**

### D4.4b · piloto v4 (22 sep 2026, [ejecutora], Fable 5.1)

- Implementado sobre v3 (`9544250`) según `auditoria/d4_4b_v4/especificacion_d44b_v4.md` (y las dos investigaciones, copiadas ahí), con el ajuste de Dirección: nada de piel de MakeHuman (se sustituye en v5). Informe: `auditoria/d4_4b_piloto4_2026-09-22.md`; evidencia en `build/d4_4b_piloto4/`.
- `/θ ð/`: punta roma (superelipse N=3,2) y clave interdental por cizalla y avance, sin recorte por vértice: volumen +2 % (v3 +15 %), punta 0,74 / lámina 0,92, toca el borde de los incisivos. `/k ŋ/`: cúpula ancha, volumen +9,6 % (v3 +79 %). Reposo con los labios casi juntos (`cierreLabial`), sección de los labios en el corte (`corte_labio_*` con las shape keys de la piel), soplo de aspiración en `/p t k/` (`Linea.aspiracion`), recuadro por textura (0,7×, MSAA, uno de cada dos cuadros en movimiento).
- Comprobaciones nuevas: hidrostato en `lengua.py` y en `tools/boca3d_demo/medir_lengua.mjs` (lo llama `comprobar_modelos.mjs`); `v4.spec.ts`. Pruebas: boca3d 120/120, front 416/416, tsc OK, build OK, Blender 53/53.
- FPS bilabial frente a `8bd4a66`: ver la tabla del informe. Lo que queda por debajo es enseñar el interior en `/p b m/`, no el recuadro.
- **Siguiente**: Miguel mira la vista previa; si aprueba, lote (primero `cuerpo_alto`/`raiz_atras`/`punta_arriba` con el hidrostato: `/l w j i u ɪ ʊ ɝ/` siguen fuera de ±10 %). v5: cabeza escaneada (sección «Preparación v5» del informe).

### D4.4b · piloto v5 (22 sep 2026, [ejecutora], Fable 5.1)

- Implementado sobre v4 (`2d61d23`) por encargo de e6 aprobado por Miguel: la cabeza de MakeHuman se sustituye por el escaneo de Lee Perry-Smith (three.js, **CC BY 3.0 Unported**; licencia verificada y copiada con el GLB y dos texturas en `tools/boca3d_blender/lps/`; atribución en el README de `boca3d` y en `cara.py`; la app no tiene pantalla de créditos). Informe: `auditoria/d4_4b_piloto5_2026-09-22.md`; evidencia en `build/d4_4b_piloto5/`. Sin deploy, push ni merge.
- `cara.py`: `cabeza_escaneada` (importa el GLB, quita 372 caras interiores de la boca, abre la ranura de los labios en y = 0,15 con `split_edges` ±0,012, decima nuca y cuello; `labios_en_piel = 2`, `nariz_salida`), `perfil_lps`, secciones de labio con bermellón y mucosa curva, `techo_nasal` y `suelo_boca` ajustados al escaneo (`hundir_bajo_la_piel` por rayos). `cara.glb` 1 942 444 B (límite 2 188 394). `SIN_LPS=1` vuelve a MakeHuman.
- `lengua.py`: ALTO 0,39 y PUNTA_N 2,9; 53/53, exceso 0, hidrostato 13/13 (`/θ/` +2,8 %, `/k ŋ/` +7,4 %).
- `escena.ts`: texturas del GLB (`texturasDe`), corte seco de la mandíbula en la ranura, `REFERENCIA_CIERRE` (cierre calculado a mandíbula 0,2 y escalado por `mandibula/0,2`: los labios se tocan en reposo), `geometriaAireNasal(salida)`, y dos optimizaciones medidas: `menosPixelesEnMovimiento` (pixel ratio 1,25 mientras hay línea o transición) y `usarMaterialesBaratos` (Standard donde no hay clearcoat/sheen). `?opt=0` en la demo las apaga.
- FPS (SwiftShader, medianas de 3 rondas alternas, CPU ×4/×1): bilabial base 12,7/13,5 → v5 16,2/17,1; confirmación con el GLB final 15,2/16,1 contra 13,2/13,6 (+15 %/+18 %; v4 era −18 %/−28 %). Vista por defecto 7,9/8,6 → 12,6/14,4.
- Pruebas: boca3d focalizadas 119/119 (8 archivos), front 416/416 (46), tsc OK, build OK, `comprobar_modelos` OK, banda labios-dientes 20/20, guard de borde 534 [SIN MEDIR: sin tocar borde ni CSS].
- Sin resolver: ojos cerrados del escaneo; cara inferior más corta que el interior (el suelo de la boca queda como lámina y el hueso pasa a ≤ 0,1 de la piel por los lados del mentón, sin asomar en las vistas medidas); la decimación alcanza la cara (1 159 vértices); las secciones del labio asoman de ¾ a partir de ~−50° (fuera del giro del alumno, tope −34°); fps en teléfono sin medir.
- **Siguiente**: Miguel mira la evidencia; si aprueba v5, el lote de fonemas se hace sobre esta base.

### D4.4b · piloto v6 (22 sep 2026, [ejecutora], Fable 5.1) — labios de verdad sobre la cabeza escaneada

- Encargo de e6 con el vídeo de Miguel como referencia (`…/d64c111b…/scratchpad/labios/`, no se copia al repo). **Rama del plan: v6** (las tres condiciones del límite cumplidas: recuadro con reposo/cierre/liberación distintos, sin franja ni herida, corte con los labios). Informe: `auditoria/d4_4b_piloto6_2026-09-22.md`; evidencia en `build/d4_4b_piloto6/`. Sin deploy, push ni merge.
- Diagnóstico de la «herida» de v5: la ranura ya estaba en la línea de contacto real (sonda de textura: bermellón z 0,00..−0,23, contacto −0,10); lo que la rasgaba era el giro de reposo de la mandíbula (1 cm en los labios) con el cierre devolviendo solo el borde. v6: el labio de abajo se retrasa respecto al hueso (20 % en reposo, 60 % en vocales; `peso_labio_inferior_lps` = `deformarPiel` con `retraso`), sello suave, compresión que recoge el bermellón, tiras de mucosa tras la ranura, fruncir/estirar con las cifras de Miguel, secciones del corte abombadas, cara sin decimar (2 505 / 2 204 vértices). `cara.glb` 2 134 088 B (límite 2 188 394).
- Liberación brusca en `mezclarPose` (escena.ts): al salir de una oclusión bilabial, mandíbula/cierre/compresión van por delante (`1 − (1 − f)^5`); hacia una pose sellada (el ciclo de /p b m/ acaba en reposo) hay un rebote en el primer 45 % del tramo (cierre 0, mandíbula +0,32·MAND_MAX, compresión −0,6): los timings no cambian. Medido: /p/ → /æ/ 12,9 mm a 77 ms; /p/ → reposo 11,4 mm a 155 ms y sellado de nuevo desde 417 ms.
- Cifras frente a Miguel (IO = 2,71 u): reposo 0,4 mm; /p/ 0,3 mm; /u/ −31,5 % de anchura, 5,8 mm de orificio, 10 mm de avance; /i/ +28,5 % (objetivo +33) y 4,8 mm; /æ/ 25,5 mm (máximo de Miguel ≈24).
- **Reloj de las tiras**: cada captura del lienzo tarda ~1 s en SwiftShader; las tiras «cada 0,28 s» de v4/v5 cubrían ~10 s. Ahora `tira_exacta.mjs` sustituye `performance.now` en la página y captura en tiempos exactos del ciclo.
- Pruebas: boca3d 119/119, front 416/416, tsc OK, build OK, banda labios-dientes 20/20, `comprobar_modelos` OK, guard 534 [SIN MEDIR]. FPS (v5 → v6, medianas de 3 rondas, ×4/×1): bilabial 16,9/15,9 → 15,7/15,6; defecto 12,5/13,4 → 12,2/12,6 (−2..−7 %; sigue +24 %/+16 % sobre 8bd4a66).
- Sin resolver: ojos cerrados (los párpados del escaneo no son un hueco; globos probados y quitados), boquete bajo la nariz, por la boca abierta se ve la cara beige del corte, tiras facetadas, estirado +28,5 %.
- **Siguiente**: Miguel juzga la evidencia; si aprueba, el lote de fonemas sobre v6.
