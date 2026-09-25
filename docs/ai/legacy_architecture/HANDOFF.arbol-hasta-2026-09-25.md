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

## Boca 3D realista (rama `dev/articulacion-v2`, 24 sep)

Codex se quedó sin cupo y Claude tomó el relevo. `8cb4e7c`: lengua
suavizada. `cc18efe`: /u/ más redonda (morfo `fruncir` parametrizado
con `FRUNCE_*`), labios con zonas secas y húmedas, lengua con mucosa
(saburra, surco, papilas). Medidor de 2.227 estados sin cambios;
135/135, tsc y build en verde. Respaldo en la release privada
`boca3d-noche-2026-09-23/labios-lengua-cc18efe.zip`. El estado detallado
está en `Documents/Codex/2026-09-23/hola-mi-amigo-mira-tengo-otro/ESTADO_BLENDER_NICO.md`.
Después, `f88a8cc`: el perfil del corte es tejido blando continuo de la
nariz al submentón. `b34f871`: poros en la piel perioral. Respaldo en
`perfil-piel-b34f871.zip`. `efb92ea`: el corte lateral ya usa el contorno
de la cara de frente (nariz, cráneo, nuca y cuello propios; se ocultan
las piezas del escaneo); respaldo `cabeza-efb92ea.zip`. `ed3814b`: cerebro, columna cervical y
/f v/ sin cuña (respaldo `anatomia-ed3814b.zip`). `1d1581e`: /f v/ y /θ ð/
según las fotos de Miguel (mandíbula f-v 0,08; lengua interdental aplanada,
θ-ð vuelven a 0,36); respaldo `fv-theta-1d1581e.zip`. `86977b4`: retoque final de /f v/
(material). `4d41512`: **D4** — la boca didáctica ya está en Pronunciar
(entrada `didactica` de Boca3d, GLB en `front/public/boca3d/didactica/`,
Frente/Lado, créditos CC BY). Front 432/432 y build en verde; probada en la
app a 390 px. `b98874c`: lengua sin «dos
picos» en /θ ð/ (alisado de normales) y boca al compás del audio (tramos
que suenan en cada grabación de Miguel, `alCompasDeTramos`).
**PUBLICADO (24 sep, 16:36 CDMX):** front Space `5f542ee` desde `86063b0`
(rama `publicar/boca3d-didactica` = master + solo el 3D; master local
avanzado a `86063b0` + `bdeca0e`, sin subir a GitHub porque origin/master
va muy por detrás con trabajo ajeno). D1-D3 NO publicados (necesitan
desplegar la API). Cuentas comprobadas en la app publicada: profesor 60,
invitado1-7 20, invitado8 17 (contraseñas en `literalevel_codigos.txt`,
nunca en la salida). Detalle en `DESPLIEGUE.md`.
**Segunda publicación (24 sep, 17:27 CDMX):** Space `0d4a3b2` desde
`4c9d7d7` (dev: `894064c` palabra de ejemplo, `c179fdf` cabeza amable). Master
local en `26d80e1`. Pendiente de auditoría del vídeo de Miguel: dientes como
bloques separados, costura vertical en la barbilla vista de tres cuartos,
torso desnudo al alejar (sin ropa). Ni master ni
producción cambiaron.
**Tercera publicación (24-25 sep, noche):** rama `publicar/v2` (worktree
`publicar-3d`) = master + dev. API Space `a88531b` (`cca283a`) y `c49604e`
(`acbee33`, arreglo de PG844 en `ficha.py`); front `a9ae51f` (`acbee33`): D1-D3
(Mi espacio, Repasar, Mi progreso), aire 2D de /f/, lectura 3D de frases
(`GET /api/lectura/ipa` + `lineaFrase`), mentón y mandíbula
(`tools/boca3d_blender/rostro_didactico.py`), mejillas, /f v/ con cuerpo, pelo
rizado castaño y tez clara. Registro en `DESPLIEGUE.md` (commit `6b7c95c`).
**Master local NO avanzado:** el fast-forward choca con `docs/ai/*` sin
seguimiento en el árbol principal (HANDOFF, AUDIT_STATUS…) que la rama sí
versiona; no se sobrescribieron. Pendiente decidir cómo unirlos.
Siguiente: encargo de investigación del modelo articulatorio en
`docs/ai/investigacion_modelo_articulatorio.md` (otra sesión); pendientes
visuales: ojos, dientes como bloques, costura del mentón, torso.

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

---

## Audio D4 · estado al 21 sep 2026 (14:50)

Sustituye a la sección «Audio D4 · 20 sep 21:10». Todo pid, conteo y hash se
comprobó el 21 a las ~14:50, salvo lo marcado [SIN MEDIR]. Reconfirmado a las
14:56: los tres procesos de §2 vivos y `estado.json` igual (11 · 1 · 73).

### 1. Git

- Árbol: `C:\Users\laura\literalevel\.claude\worktrees\articulacion-v2`, rama `dev/articulacion-v2`.
- HEAD `21611337b5d82ff88de28fa27296a525e24e926f` (19 sep 17:36, «D4.4a 3D: limpiar dentadura, vibración y lengua»).
- `git status --porcelain`: solo ` M front/angular.json`. Staging vacío.
- **`front/angular.json` está modificado**, no fuera: +4 líneas en `serve.options` (`allowedHosts: ["strings-living-revealed-wagon.trycloudflare.com"]`, `proxyConfig: "proxy.conf.json"`). mtime 19 sep 13:09, anterior al audio; viene de una sesión del front de D4.4a. No hacer commit. Decide Miguel si se revierte.
- `build/` está en `.gitignore:38`. Nada del audio está versionado (ver §5).

### 2. Procesos vivos — NO cerrar

| pid | proceso | puerto | qué hace | desde |
|---|---|---|---|---|
| 41232 | `python.exe servidor.py 8989` (cp312, §6) | 127.0.0.1:8989 | Sirve `build/grabador/`, recibe `POST /grabar`, guarda en `crudo/` | 20 sep 20:25 |
| 37196 | `cloudflared.exe tunnel --url http://127.0.0.1:8989 --no-autoupdate` | 127.0.0.1:20241 (métricas) | Túnel público | 20 sep 20:25 |
| 7424 | `python.exe -X utf8 vigilante.py` | — | Reescribe `estado.json` cada 2 s | 20 sep 20:41 |

Los `colab-mcp.exe` (3080, 7044, 25764, 23064, 30148, 12052, 8212, 13528, 33232, 40880) son de otras sesiones de Claude/Codex: no tocarlos.

- URL pública: `https://fraser-newest-assessing-glance.trycloudflare.com/` (200 en `/`, `/app.js` 13311 B, `/estado.json`, `/fichas.json`).
- **Por qué no se cierran:** la cola de IndexedDB del móvil de Miguel está atada a ese origen. Un quick tunnel nuevo tiene otra URL y la cola queda inalcanzable. Se cierran solo cuando Miguel confirme que su cola está vacía.
- Con corriente el PC no se suspende (`STANDBYIDLE=0`, `HIBERNATEIDLE=0`); con batería, a los 600 s.

### 3. El grabador (`build/grabador/`)

| archivo | B | mtime | función |
|---|---|---|---|
| `index.html` | 3429 | 21 09:03 | Ficha con dos piezas (fonema/palabra); panel de exportar fuera de `#ficha`, visible sin permiso de micrófono |
| `app.js` | 13311 | 21 09:00 | Grabación, subida, cola, exportar, sondeo del estado |
| `styles.css` | 10546 | 21 09:00 | |
| `servidor.py` | 10198 | 20 20:23 | `ThreadingHTTPServer`, `do_POST /grabar`. **Guarda antes de evaluar**; devuelve `{ok, verde, avisos, datos}` |
| `vigilante.py` | 2497 | 20 20:41 | Escribe `estado.json` con reemplazo atómico (existe para no reiniciar el servidor) |
| `estado.json` | ~9.7 K | vivo | `completos`, `a_medias`, `faltan` |
| `fichas.json` | 39267 | 20 20:20 | 85 fichas: GA golpes 8 + sostenido 33, RP golpes 8 + sostenido 36 |
| `montar.py` | 7037 | 20 20:27 | De `crudo/` a `candidate/{ga,rp}/<hex>.mp3` |
| `manifiesto.json` | 4316 | 20 20:27 | Ensayo en seco: `montados=0`, `faltan=85` |
| `importar.py` | 7550 | 21 11:05 | Importador del plan B |
| `crudo/{ga,rp}/<hex>_{fonema,palabra}.webm` | | | Tomas brutas |
| `crudo_rotos/0064_fonema.webm` | 40000 | | Apartado (trampa 1) |
| `entrada/tomas_01.json` | 480107 | | Primer lote exportado por Miguel, ya importado |

**Semáforo (`servidor.py:evalua`):** `PICO_SATURA=0.99`, `PICO_MINIMO=0.06`. Marcos de 0.020 s, umbral `max(p20·3, p95·0.08, 1e-5)`, huecos ≤0.20 s fusionados, eventos <0.10 s descartados. `SNR_MIN_DB=25.0` (mediana activos vs quietos). Suelo elevado: tramos de quietos (k=max(20, n/4)), salta si `max − mediana ≥ 5.0 dB` **y** `snr_local < 34`. Fonema `golpes` ≥3 eventos; `sostenido` ≥1.5 s útil. Sonoridad con YIN (`ruido_fondo.track`), marcos `s>0.55` y F0 100–220 Hz: sordo `<0.35`, sonoro `>0.15`. Palabra: vocal si `voz ≥ 0.05` o `lo(<1 kHz) ≥ 0.40` (salvo `poca_voz_esperada`); `COLA_MIN_S=0.12`.

**Cola (`app.js`):** IndexedDB `literalevel-grabador` v1, store `pendientes`, `clave = "<ACENTO>-<hex>_<pieza>"`, `put` reemplaza. `localStorage['literalevel.grabador-v1']` guarda veredictos y última ficha. `sube()`: 3 intentos (1/3/7 s); tras un fallo total `sinRed=true` → 1 intento, vuelve a `false` al primer éxito. `vaciaCola()` cada 12 s y en `online`, `break` al primer fallo. `refrescaEstado()` cada 5 s. La cola sobrevive a una recarga (medido: 10 → 10).

**Plan B (la red del trabajo bloquea POST y deja descargar), usado en real:** un botón de exportar por lote de 10 fichas (`POR_LOTE=10`) → `tomas_NN.json` con las tomas en base64. **No desencola**: la toma sale de la cola solo cuando el servidor confirma. `importar.py [archivos|carpeta]` (por defecto `entrada/`) valida contra `fichas.json`, base64 estricto, `bytes`, ≥1000 B y que PyAV decodifique; **no pisa lo existente**; pasa el semáforo a cada toma. Probado con lote bueno, reimportación y lote truncado.

### 4. Material grabado

`crudo/ga/` 23 `.webm`, `crudo/rp/` 0. `estado.json`: **11 completos · 1 a medias · 73 faltan**. **Usables de verdad: 9/85** (`estado.json` cuenta 11 porque solo mira si el archivo existe; trampa 4).

| n | id | fonema | sitio | SNR fon./pal. (dB) | semáforo |
|---|---|---|---|---|---|
| 1 | GA-0070 | /p/ pen | casa | 32.9 / 44.6 | ✓✓ |
| 2 | GA-0062 | /b/ bad | casa | 49.3 / 39.6 | ✓✓ |
| 3 | GA-0074 | /t/ tea | casa | 40.7 / 46.3 | ✓✓ |
| 4 | GA-0064 | /d/ did | casa | — / 48.7 | a medias: falta el fonema (trampa 1) |
| 5 | GA-006b | /k/ cat | casa | 50.2 / 43.1 | ✓✓ |
| 6 | GA-0261 | /ɡ/ get | trabajo | 19.8 / 20.7 | ✕✕ SNR |
| 7 | GA-0066 | /f/ fall | casa | 50.4 / 46.7 | ✓✓ |
| 8 | GA-0076 | /v/ van | casa | 52.4 / 50.0 | ✓✓ |
| 9 | GA-03b8 | /θ/ thin | trabajo | 16.4 / 18.8 | ✕✕ SNR |
| 10 | GA-00f0 | /ð/ this | casa | 46.9 / 46.0 | ✓✓ |
| 11 | GA-0073 | /s/ see | casa | 51.0 / 48.2 | ✓✓ |
| 12 | GA-007a | /z/ zoo | casa | 45.8 / 46.8 | ✓✓ |

Casa: 33–52 dB, 19/19 verdes. Trabajo: 16–21 dB, 0/4; ruido estacionario (no saltó el detector de suelo elevado).

**Faltan GA (29):** `0283 0292 0068 0074_0283 0064_0292 006d 006e 014b 006c 0279 0077 006a 0069 026a 025b 00e6 0251 0254 028a 0075 028c 0259 025d 025a 0065_026a 0061_026a 0254_026a 006f_028a 0061_028a`

**Faltan RP (44):** `0070 0062 0074 0064 006b 0261 0066 0076 03b8 00f0 0073 007a 0283 0292 0068 0074_0283 0064_0292 006d 006e 014b 006c 0072 0077 006a 0069_02d0 026a 0065 00e6 028c 0251_02d0 0254_02d0 0252 028a 0075_02d0 025c_02d0 0259 0065_026a 0061_026a 0254_026a 0259_028a 0061_028a 026a_0259 0065_0259 028a_0259`

**A regrabar además:** GA-0064 fonema, GA-0261 ×2 y GA-03b8 ×2, en un sitio con SNR ≥ 28.

### 5. Respaldos

| ruta | contenido |
|---|---|
| `build/audio_candidates_85/` | Los 85 cortados de masters (método abandonado): 41 GA + 44 RP; 279 mp3 en total, 9.3 MB |
| `build/audio_candidates_human/` | Codex: /z n ŋ/ humanos, 12 mp3 + `.deps` 68 MB (PyAV) |
| `build/audio_candidates_openai/` | Codex: TTS, 37 mp3, 25 MB |
| `build/audio_candidates/` | Codex: piloto GA, 9 mp3 + `.deps` 95 MB (numpy, soundfile, openai, pydantic) |
| `build/audio_audit_human/` | Arnés de auditoría de 85 de Codex |
| `C:\Users\laura\Downloads\literalevel_audio_build_2026-09-20.zip` | 76305138 B, md5 `58d2094d8e5e375c3a480be76363605c`, 6597 entradas, más nueva 20 sep 14:31:40 |

**El zip es anterior a esta fase**: no contiene `audio_candidates_85/`, `grabador/`, `crudo/` ni el catálogo. **Ese trabajo no está versionado.** Respaldo del 21 sep en §9. Lo más valioso: `crudo/` y `grabador/`.

**Masters (sha256)**, tres copias idénticas (`literalevel\audio_masters\`, `Downloads\`, `build/audio_masters/`):

| archivo | B | sha256 |
|---|---|---|
| Consonantes GA.m4a | 7757986 | `ccca8a2ce8b7d7080165735ae4d8df0863f8c0ceb2220347e63bd1aa6525539a` |
| Consonantes RP.m4a | 5243889 | `1c13eb7a575c2013d140b5d5f8aa1449a02fffe1cd016ca30aeadee08265ed70` |
| Vocales GA.m4a | 4388395 | `c838bba0ea53f6937ed1331dc253d9cd2a6e4d1819bc16ee39ddb722ecdbf388` |
| Vocales RP.m4a | 4613121 | `3f8f5ff860063ebd6ab44996bcdcb361bb6cc474db3c42fb9f7d67d16d0a6e6d` |
| Prueba n, z y eta.m4a (solo Downloads) | 2236897 | `69f599efdaeee6044c1bcf752088396966bebe6dc258eaaac6e67522c4c86a7c` |

**Producción intacta:** `app/audio_fonemas` 41 mp3 y `app/audio_fonemas_rp` 44 mp3, versionados; `git status`/`git diff HEAD` sobre `app/` vacíos.

### 6. Runtime

- Intérprete: `C:\Users\laura\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` (CPython 3.12.14 x64).
- Dependencias no instaladas; cada script las añade a `sys.path`: av 18.1.0 (`build/audio_candidates_human/.deps/av/`), numpy 2.5.3 y soundfile 0.14.0 (`build/audio_candidates/.deps/`), `ruido_fondo` (`build/audio_masters/ruido_fondo.py`, YIN).
- Trampas: el `python` del PATH es WindowsApps 3.11.9 y no carga ruedas cp312; no hay ffmpeg/ffprobe (todo pasa por PyAV); consola cp1252 → usar `-X utf8`.
- Si desaparece `~/.cache/codex-runtimes/`: caen servidor (al reiniciar), vigilante, `importar.py`, `montar.py` y `audio_masters/`. Haría falta cualquier CPython 3.12 x64. [SIN MEDIR con otro 3.12.]
- Si desaparece `build/audio_masters/`, el grabador no arranca (`servidor.py` importa `ruido_fondo`).

### 7. `build/audio_masters/`

**Reutilizable / crítico:** `ruido_fondo.py` (el grabador depende de él); `alineacion_prueba/lib_align.py` (`decode`, `frames_of`, `runs_and_groups`); `suelo_local.py/.json` (detector +5 dB, validado 3/3 con el oído de Miguel; base de la regla del servidor); `segmentacion_rp/valles.py` (validado 4/5); `inspect_masters.py` + `masters_inspection.json`; `audio_candidates_85/formato/nivelar.py` (normaliza sobre el MP3 codificado; `montar.py` copia su lógica).

**Obsoleto** (registro, no se usa): `alineacion_final/`, `alineacion_prueba/export_pass*.py` + `alineacion.json`, `catalogo_85/`, `segmentacion_rp/catalogo.*`, `barrido_ruido{,2,3}.*`, los arneses `transcripcion/`, `transcripcion_vocales/`, `escucha_cierre/`, y los scripts de `audio_candidates_85/`.

### 8. Lo que no está escrito en ningún otro sitio

**Trampas**

1. **Probar el front en `127.0.0.1:8989` escribe en el servidor real.** `vaciaCola()` corre cada 12 s en cualquier pestaña y sube lo que haya en la cola de ese origen. Una prueba con entradas falsas sobrescribió `crudo/ga/0064_fonema.webm` (toma real de Miguel) con un blob sintético de 40000 B; apartado en `crudo_rotos/` y perdido. **Probar el front solo en otro puerto y otra carpeta, o con `vaciaCola` desactivada.** A Miguel se le dijo por error que fue «una subida cortada por el túnel»: hay que corregírselo.
2. **Una cola vieja puede pisar una toma nueva** (`app.js:envia`): tras una subida directa con éxito no se hace `desencola` de esa clave. Si Miguel regraba GA-0261 o GA-03b8 (que tiene en cola), el siguiente `vaciaCola` puede subir la toma vieja encima. Arreglo: `await desencola(\`${f.id}_${pieza}\`)` en la rama de éxito. **Sin aplicar.**
3. **`S.decodifica(bytes, destino)` hace `write_bytes` antes de abrir.** Ya reescribió todo `crudo/` (mtime 21 sep 11:06): **los mtimes de `crudo/` no sirven como prueba forense.** Para leer, `av.open` directo.
4. **En `estado.json`, completo = existen los dos archivos**, no que decodifiquen ni que estén en verde.
5. En Windows `pkill -f` falla sin avisar: buscar por puerto (`Get-NetTCPConnection`) o por `Win32_Process.CommandLine`.
6. Un `\\n` dentro de `'''…'''` de Python generado desde un heredoc de bash acabó como salto real y rompió una f-string. Usar el Write tool.
7. El servidor sirve con `Cache-Control: no-store`: cambios en `app.js`/`index.html`/`styles.css` se ven con recarga, sin reiniciar. Cambiar `servidor.py` obliga a reiniciar y **cambia la URL** (§2).

**Umbrales calibrados sobre material real**

- SNR del inventario sano 27.9–41.6 dB; la GA /p/ mala daba 22; casa 33–52; trabajo 16–21.
- Suelo elevado: +5 dB contra la **mediana** de los tramos (contra el mínimo daba falsos positivos) y `snr_local < 34`.
- Nivel de entrega: −1.0 dBFS ±0.3 medido sobre el MP3 decodificado. La dispersión de −4.90 dBFS tenía 4 causas (normalizar la fuente a 48 k y no el MP3; interpolación lineal que baja transitorios hasta −1.64 dB; LAME baja ~3.9 dB el pico de fricativas; corrección solo a la baja). Resuelto con iteración amortiguada (1.0, luego 0.5).

**Detectores descartados**

- F0 por argmax de autocorrelación (daba 615 Hz en voz masculina) → YIN (115–198 Hz).
- Segmentar por umbral de hueco: ningún umbral da 24/20 en RP.
- Distinguir palabra de toma sostenida: seis métricas, las seis fallaron. **No es resoluble midiendo**; solo la transcripción a ciegas de Miguel.
- Control de orden con ventana fija de 0.9 s → se compara el primer evento contra el resto de su propio sostenido.

**Decisiones de Miguel (no reabrir)**

- Donde detección y transcripción no coincidan, gana la transcripción.
- Formato A, una sola toma: `sostenido · 0.7 s · corto (0.45 s del sostenido) · 0.7 s · palabra`, fades de 5 ms, mp3 mono 24 kHz, nombre en hex como `app/audio_fonemas*`.
- Sin reducción de ruido. Sin gasto.
- Se abandona el corte de masters (51 limpios, 34 con problema, 24 por corte). Se graba directo.

**Método:** skill `.claude/skills/ritmo-de-trabajo/` y memoria `ritmo-piloto-antes-que-lote`.

### 9. A medias

| tema | estado | qué falta |
|---|---|---|
| Grabación | 9 usables · 3 a regrabar · 73 sin grabar | Miguel busca un sitio con SNR ≥28 (1 ficha de prueba, exportar e importar para medir) y sigue desde n=13 |
| `montar.py` | Nunca ejecutado con audio real | Ejecutarlo sobre **una** ficha verde (p. ej. GA-0070), que Miguel la escuche, y solo entonces el resto |
| Trampa 2 | Diagnosticada, sin aplicar | Una línea en `app.js`; se ve con recarga |
| Cola del móvil | [SIN MEDIR] Es de esperar que conserve al menos las 4 tomas de `tomas_01` | Se vacía sola cuando el POST funcione; mantener §2 vivo |
| «3 tomas en cola» del 20 por la noche | [SIN MEDIR] ¿subconjunto de las 4 de `tomas_01`? | Lo dirá el siguiente export |
| Respaldo de esta fase | Hecho 21 sep 15:00: `C:/Users/laura/Downloads/literalevel_grabador_2026-09-21.zip`, 2443232 B, md5 `601597914c6a60f74a7c1c88e54a22b1`, 23 tomas de `crudo/ga` + la rota | Repetirlo tras cada sesión de grabación |
| `front/angular.json` | Modificado desde el 19 sep, ajeno | Decide Miguel |
| Corregir a Miguel lo del 0064 | Pendiente | Decirle que fue una prueba nuestra, no el túnel |
| Blender / D4.4b | Sin tocar | — |

### Actualización 21 sep 21:30 · grabador v2 y fichas compartidas

- Codex cambió el contrato a **5 piezas por ficha** (`fonema_1..3`, `palabra_1..2`) y quitó `X-Ficha`. Procesos actuales: servidor pid 29844, vigilante 34412, túnel 37196 (misma URL).
- Revisión de solo lectura (av.open + `evalua` del servidor, sin escribir en `crudo/`): **38 fichas con 5/5 piezas, las 190 en verde, sin hashes duplicados**. RP-0066 tiene solo `fonema_1`, en rojo (1,3 s de sonido útil).
- Nuevo `build/grabador/compartidos.json`: 24 pares GA/RP de consonantes que usan la misma grabación (incluido GA /ɹ/ = RP /r/ en «red»). Las vocales **no** se comparten; las 9 con el mismo símbolo y la misma palabra están en `vocales_posibles`, a la espera de que decida Miguel.
- `app.js`: la página recorre solo las fichas que faltan (23: GA /f v θ/, que valen para los dos acentos, y 20 vocales RP). La ruta se calcula al cargar; progreso, «te has dejado atrás» y ◀ ▶ Saltar Aceptar van sobre la ruta. Probado en otro origen (127.0.0.1:8990, 390 px), nunca en 8989. Copia previa en el scratchpad de la sesión `[ejecutora]`.
- Pendiente: `montar.py` no conoce ni las 5 piezas ni `compartidos.json`. Las 12 fichas GA v1 quedan cubiertas por su pareja RP (/p b t d k ɡ/) o siguen en la ruta (/f v θ/).

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

### D4.4b · piloto v7 (22 sep 2026, [ejecutora], Fable 5.1) — última vuelta de la cara

- Encargo de e6 (Miguel eligió una vuelta más; después, lote de fonemas con Sonnet). Informe: `auditoria/d4_4b_piloto7_2026-09-22.md`; evidencia en `build/d4_4b_piloto7/`. Sin deploy, push ni merge; `lengua.py`/`lengua.glb` sin tocar.
- Los cinco puntos: (1) dientes al abrir: el labio de abajo sigue al hueso (k = 1 en vocales, 0,2 en reposo), el de arriba sube al abrir (peso −0,22, `deformarPiel` admite negativos); el recuadro (capa 1) ve incisivos y caninos 3–8, lengua y un fondo oscuro de boca, y su pasada enseña esas piezas aunque el perfil dental del corte las esconda; la punta de la lengua tapa los incisivos de abajo en las vocales muy abiertas. (2) Hueco bajo la nariz cerrado con abanico propio y UV oscura (2 tapas). (3) /i/ +32,7 % con los incisivos superiores a la vista. (4) Tiras de mucosa: ranura subdividida ×3, 4 anillos hasta el surco, UV oscura, y rígidas con su borde REAL (grupo `mucosa`; con la curva ajustada la comisura lejana del escaneo, 0,3 más adelante, dejaba /u/ en −25,7 %). (5) Ojos abiertos por ranura + deformación del párpado y globos `ojo_*`; de frente bizcos (huecos asimétricos) pero fuera de los encuadres del alumno; cerrarlos = tres líneas en `cabeza_escaneada`.
- No regresión: sello/compresión igual (0,5/0,3/0,5 mm), liberación brusca (28,7 mm a 94 ms; rebote 20 mm a 74 ms y sellado a 404 ms), /u/ −32,2 %, corte con los dos labios, lengua/θ sin tocar (hidrostato 13/13), fps bilabial 14,5/14,3 frente a base 13,4/14,3 (6 rondas: +8 % a ×4, empate a ×1; v6 15,8/14,9). Coste que hay que saber: con k = 1 la abertura de /æ/ es la de la mandíbula del catálogo (52,7 mm; Miguel ≈ 24): bajar `MAND_MAX` sería la palanca, no tocada.
- Pruebas: boca3d 119/119, front 416/416 (sola; con capturas en paralelo 3 fallos ajenos en `lector.progreso.spec.ts`), tsc OK, build OK, banda labios-dientes 20/20, `comprobar_modelos` OK. `cara.glb` 2 162 772 B (límite 2 188 394). La exportación no es byte-determinista (±2,5 KB, conjuntos bmesh en los rellenos).
- **Siguiente**: cara cerrada; lote de fonemas (otra orden, Sonnet).

### D4.4b · cierre de cara (22 sep 2026, [ejecutora], Fable 5.1) — MAND_MAX y ojos

- Encargo de e6 con los dos ajustes aprobados por Miguel. Informe: `auditoria/d4_4b_cierre_cara_2026-09-22.md`; evidencia en `build/d4_4b_cierre_cara/`. Sin deploy, push ni merge. **La cara queda cerrada; el lote de fonemas va en otra orden y con Sonnet.**
- **MAND_MAX 0,42 → 0,21 rad**, el mismo valor en `escena.ts`, `cara.py` (clave de cierre y banda labios-dientes) y `lengua.py` (comprobación); k = 1 en vocales se conserva; subida de `estirar` 0,50 → 0,40. Aberturas interlabiales (demo, IO 63 mm): reposo 0,5 · /p/ 0,3 · /æ/ 29,8 (v7 52,7) · /ɑ/ 20,8 · /ʌ/ 13,4 · /ɛ/ 8,1 · /ɪ/ 1,4 · /i/ 8,8 (+32,7 % de anchura) · /u/ 4,3 (−32,2 %); liberación 12,5 mm a 73 ms; rebote 9,7 mm a 69 ms y sellado a 378 ms.
- **Ojos cerrados** otra vez (tres llamadas fuera en `cabeza_escaneada`); `cara.glb` 2 130 576 B.
- Lengua con la mandíbula nueva: 53/53, exceso 0, pliegue 0, roce −0,039; hidrostato 13/13. Tres cambios acordados con e6: (1) **/θ ð/ mandíbula 0,36 → 0,6 en `poses.ejemplo.json`** (la punta aprobada, 0,64 de grosor, no cabía en el hueco de 0,54 entre bordes incisales; con 0,6 el hueco es 0,78 y se conserva `INTERDENTAL_ALZA` 1,25); comprobado a 390 px que sigue leyéndose la punta entre los dientes. (2) /tʃ dʒ/ `punta_arriba` con toque 1,0 → 0,85 (tres mapeos: `lengua.py`, `escena.ts`, `medir_lengua.mjs`). (3) Dorso sin toque ×0,9 (/w l ɝ ɚ/): **revisar en el lote**. `v4.spec.ts` actualizado (/θ/ ya no cierra a medias; el caso lo hace /ɜː/).
- fps (3 rondas alternas, ×4/×1): bilabial base 13,6/14,3 · v7 14,3/13,6 · **cierre 14,7/15,2**; defecto 7,9/7,9 · 12,2/13,9 · 12,6/13,7. Pruebas: boca3d 119/119, front 416/416, tsc OK, build OK.
- Anotado: /ɛ/ 8,1 mm en el borde bajo de la banda; /ɪ/ 1,4 mm es la abertura más justa; exportación del GLB no byte-determinista; fps en teléfono y guard 534 sin medir.

### D4.4b · lote fase 1 (22 sep 2026, [ejecutora]) — dentales, /ɹ/ y contraste rótico

- Encargo de e6 (investigación fonética §9, prioridades 1–3). Informe: `auditoria/d4_4b_lote/fase1_2026-09-22.md`; tabla de divergencias 2D/3D: `auditoria/d4_4b_lote/divergencias_2d_3d.md`; evidencia en `build/d4_4b_lote/fase1/`. Sin deploy, push ni merge; `cara.py`, `cara.glb` y `lengua.glb` sin tocar.
- **Regla nueva**: `poses.ejemplo.json` es la exportación intacta del 2D (vuelto a `d09446f`); lo que el 3D cambia vive en `poses.ajustes3d.json` y se mezcla al cargar (`conAjustes3d` en `poses.ts`; misma regla en `lengua.py` y `medir_lengua.mjs`). Toda divergencia va a la tabla. Aviso: el exportador daría `factor_lento` 1,143 frente al 1,6 commiteado (timing congelado): no regenerar sin resolverlo.
- /ɹ ɝ ɚ/ de GA abombadas (punta en reposo, cuerpo alto, dorso, raíz contra la faringe) con campo 3D `rotica` que las manda a la familia `rotico`, cuyo preset se amplía (target [−0,3; 0,4], zoom 1) para que se vea la pared faríngea: la constricción ya existía en v7 pero quedaba fuera de cuadro. RP /r/ nueva (`rp.ɹ`): postalveolar, sin raíz ni joroba. Ningún otro fonema cambia de familia.
- Hallazgo destapado por la comprobación faríngea nueva de `lengua.py` (raíz contra el perfil medido de la pared, dentro de las comprobaciones de siempre): /ɑ ɒ ɔ/ y RP /ɔː/ entraban 0,57/0,62/0,35/0,14 u en la pared (el giro de la mandíbula ya lleva la raíz 0,44 u atrás); ajustadas a raíz 0/0/0,15/0,15 con el cuerpo menos atrás, holgura 0,02–0,08.
- Comprobaciones: lengua.py 54/54 (exceso 0, pliegue 0, roce −0,039, faringe −0,022), banda 20/20, hidrostato 13/13, comprobar_modelos OK; pruebas boca3d 119/119, front 416/416, tsc, build. fps base → fase 1: bilabial 13,8/14,0 → 14,7/15,4; defecto 7,9/9,1 → 12,7/14,0; rótico 6,6/7,6 → 12,0/13,8.
- RP no rótica en coda: viene de las transcripciones (medido en local con `app/fonemas.py`: car /kɑː/, hard /hɑːd/, teacher /ˈtiː.t͡ʃəː/…); aviso: bird sale /ˈbɝd/ también en UK (catálogo).
- **Siguiente**: fases 2 y 3 del lote (otra orden).

### D4.4b · lote fase 2 (23 sep 2026, [ejecutora]) — /f v/, vocales, /l/ e hidrostato

- Encargo de e6 (ahora literalevel-6c), prioridades 4–7 de §9. Informe: `auditoria/d4_4b_lote/fase2_2026-09-23.md`; divergencias: `auditoria/d4_4b_lote/divergencias_2d_3d.md`; evidencia en `build/d4_4b_lote/fase2/`. Sin deploy, push ni merge.
- **Corrección de la fase 1**: su «hidrostato 13/13» solo miraba 13 poses; sobre todas, 17 de 47 estaban fuera de ±10 % (róticas hasta +43 %). Causa: tres claves de `lengua.py` (`cuerpo_alto` engordaba, `punta_arriba` estrechaba el cuerpo para compensarlo, `raiz_atras` alargaba sin adelgazar). Arregladas; `comprobar_modelos` exige ahora el volumen en las 54 poses (0 fuera) y la punta en 47/54 (sin exigir, nombradas: /ɹ w ʊ u ɝ ɚ ʊə/).
- /f v/: `labio_atras` de `cara.py` reescrita (el borde del labio de abajo sube a 2,9 mm del filo incisal; antes 7,4) y recuadro frontal en la familia labiodental; banda labios-dientes 28/28. /ɪ/ mandíbula 0,36 (5,2 mm). /ɹ ɝ/ con menos raíz (0,6 / 0,65), joroba y constricción siguen visibles. /l/ de GA oscura por defecto con chip «clara · inicio de sílaba» en la ficha. Descartados, con cifras: recuadro en /s ʃ tʃ/, forzar el redondeo de /ʃ/, levantar el labio superior en /f v/.
- Pruebas: boca3d 119/119, front 416/416, tsc, build, lengua.py 54/54 (exceso 0), comprobar_modelos OK. fps por encima de la base en bilabial, labiodental y defecto.
- **Siguiente**: fase 3 del lote (otra orden).

### D4.4b · lote fase 3 (22 sep 2026, [ejecutora], Opus 5.5) — /ŋ/, /ɒ ɑ/, aspiración, barrido y cierre

- Encargo de literalevel-6c, prioridades 8–10 de §9 + barrido + cierre. Informe: `auditoria/d4_4b_lote/fase3_2026-09-22.md`; divergencias (con la sección «Cierre del D4.4b: motivo y fuente de cada fila»): `auditoria/d4_4b_lote/divergencias_2d_3d.md`; evidencia en `build/d4_4b_lote/fase3/`. Sin deploy, push ni merge.
- /ŋ/ ya estaba bien (sin suelta ni soplo; sing/singer sin [ɡ]); ahora con prueba. /ɒ/ RP mandíbula 1,0 → 0,8 (abría 24,2 mm, más que /ɑ/ 20,8; ahora 19,9). Soplo de /p t k/ por lugar (VOT 25/35/42 ms → 0,39/0,55/0,66 s), y la vibración de la vocal espera al soplo.
- Pruebas: boca3d 122/122, front 419/419, tsc, build; lengua.py 54/54 (exceso 0), hidrostato 54/54 (punta 47/54), banda labios-dientes 28/28, comprobar_modelos OK; fps como la fase 2.
- Pendiente para decidir antes del 3 oct (§5 del informe): fps en teléfono y guarda 534; soplo tras /s/ y en coda (recomendado arreglar, 3 líneas); posición en la sílaba; RP clásica o SSB. Propuesta de validación humana en §6 (~25 min de Miguel).
- **Siguiente**: decisión de 6c/Miguel sobre §5 y la validación.

### D4.4b · aspiración por contexto y plan SSB (22 sep 2026, [ejecutora], Opus 5.5)

- Encargo de 6c tras aceptar la fase 3. Informe: `auditoria/d4_4b_lote/aspiracion_contexto_2026-09-22.md`; plan: `auditoria/d4_4b_lote/ssb_moderno.md`. Decisión de Miguel: el acento británico será el SSB moderno (Lindsey 2019), con un aviso en la plataforma.
- Soplo de /p t k/ solo si se suelta hacia una vocal o /l ɹ w j/ y no va tras /s/ (`seAspira`). Boca3d 123/123, front 420/420, tsc, build.
- Vista previa: la build se comprobó en local (13/13 fonemas a 390 px). **El túnel no está abierto**: el clasificador de permisos lo bloquea en esta sesión; hace falta el permiso de Miguel.
- Plan SSB: GOOSE como piloto, CURE → /ɔː/, la cadena FOOT/THOUGHT/DRESS, GOAT/FACE; unas 4 h 30. Hay un borrador del aviso esperando la aprobación de Miguel. El catálogo UK trae formas GA (sure /ʃʊɹ/…). No se ha tocado ninguna pose.
- **Siguiente**: decisión de Miguel/6c sobre el túnel, el aviso y el plan SSB.
### D4.4b · v8 cara neutra en el recuadro (23 sep 2026, [ejecutora], Opus 5.5)

- Encargo de literalevel-9b (la Dirección; cambio de rumbo tras ver Miguel el 3D en el móvil). Informe: `auditoria/d4_4b_v8_2026-09-23.md`; evidencia en `build/d4_4b_v8/`.
- En la pasada del recuadro, la piel del escaneo usa una textura lisa derivada de `Map-COL.jpg` (tono uniforme y el contorno del labio de la foto; sin barba, poros ni mapa de normales), con un 30 % de luz propia y una raya por vértice entre los labios. La cámara del recuadro pasa de 32° a 22° y deja fuera la «segunda boca» bajo el mentón. Bastaron las opciones 1 y 2b.
- El corte de perfil no cambia: 0 % de píxeles distintos (0,03 % en /ɹ/). Tampoco cambian la mecánica labial ni los modelos. Pruebas: boca3d 125/125, front 422/422, tsc, build y comprobar_modelos; fps igual que v7.
- **Siguiente**: que Miguel lo juzgue en la vista previa. Queda pendiente la raya de los labios cerrados (suave) y decidir si el perfil lleva también la piel lisa.
