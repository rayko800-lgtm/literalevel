# Encargo: poner al día todos los entregables del Módulo 5 (26 sep 2026)

Pedido por Miguel el 26 sep 2026. Para una sesión nueva de Claude Code.

## Antes de empezar

1. Lee `CLAUDE.md`, `AGENTS.md` y `docs/ai/HANDOFF.md`, que es el estado vigente.
2. Carga la skill `modulo-5-literalevel` (rúbrica y contexto académico; manda sobre todo lo demás).
   Carga `corregir-sin-inventar` antes de tocar cifras y `latex-en-esta-maquina` antes de tocar
   cualquier `.tex` o `.bib`.
3. Trabaja en un **worktree propio** (rama `dev/entregables`), no en el árbol principal. Hay otra
   sesión (`literalevel-c2`) entrenando el modelo de la cara (Eos) y usando Unreal: no toques
   `tools/cara_parlante/`, `D:/literalevel_cara/` ni la pantalla (nada de clics ni teclado; si
   hace falta un navegador, usa uno sin ventana).
4. Nunca uses `git stash`, un `checkout` global ni `add -A`. Haz commit solo de tus rutas.

## Qué hay que hacer

Poner al día **todos los entregables** con el estado real del 26 sep. Están en `entrega/`:
`documento.md` y `documento.tex` (y su PDF), `presentacion.tex` (PDF), `guion_video.md` y
`guion_video.tex` (PDF), `guion_demo_en_vivo.md`, `mensaje_profesor.md`, `estrategia.md`,
`notebook_proyecto.py` y `notebook_proyecto.ipynb`, `_portada.py` y `referencias.bib`. Además,
`README.md` y `PENDIENTES.md` de la raíz.

Primero haz un **inventario**: por cada archivo, las frases, cifras, enlaces y capturas que ya no son
ciertas. Enséñaselo a Miguel antes de cambiar nada grande. Piloto antes que lote: corrige un archivo
entero, que Miguel lo vea, y luego sigue con el resto.

## Lo que cambió (compruébalo en el código y en `docs/ai/HANDOFF.md`; no lo copies a ciegas)

- **Nombre:** la aplicación se llama **Pléyade** (antes LiteraLevel), con logo e icono nuevos
  (pegaso sobre un libro con alas; están en `front/public/marca/` y en `D:/literalevel_cara/marca/`).
  Los repositorios, los Spaces de Hugging Face, el paquete y el modelo v4 **siguen** llamándose
  `literalevel`: no los renombres. Antes de decidir cómo se nombra el proyecto en el documento
  académico, pregúntale a Miguel: por ejemplo, «Pléyade (proyecto LiteraLevel)», o si el modelo
  sigue siendo «modelo LiteraLevel v4».
- **El significado del nombre:** el texto aprobado por Miguel está en
  `front/src/app/compartido/sobre-pleyade.ts` (se abre al pulsar el logo).
- **Dónde está la app:** el front principal está en Vercel,
  <https://pleyade-app.vercel.app> (plan gratis Hobby; se publica solo con cada push a `master` en
  GitHub, repo privado `rayko800-lgtm/literalevel`). El front de Hugging Face
  (<https://mikemaki1763-literalevel-front.static.hf.space/>) queda como respaldo. La API y el
  modelo siguen en el Space `MikeMaki1763/literalevel`. El modelo v4 está en
  `MikeMaki1763/literalevel-v4`.
- **Cuentas:** desde el 26 sep, al entrar con usuario y contraseña los datos (libros, palabras,
  nivel) son de la **cuenta** y se ven igual en cualquier aparato. Sin cuenta, se guardan por
  navegador. Se guardan en el bucket privado `MikeMaki1763/literalevel-datos`. Las contraseñas se
  rotaron y las cuentas empezaron en cero el 26 sep.
- **Diseño:** tema de la marca (azul del icono, oro rosa y azul noche) con fondo de galaxia en todas
  las pantallas, sobre una lámina translúcida del tema. Siguen los temas claro, noche y papel.
  «Sobre Pléyade» al pulsar el logo.
- **Boca 3D (modelo de Blender, en Pronunciar):** más ligera (texturas WebP: 3,5 → 1,7 MB por la
  red), con botones de zoom + y −, cámara lenta («Despacio») y giro («Explorar»). La cara parlante
  **Eos** (MetaHuman de Epic) sigue en desarrollo en otra sesión: no la presentes como terminada.
- **Fecha de entrega:** archivos en Classroom el 4 oct 2026 a las 11:59 p.m. («Trabajo Final»,
  editada el 26 sep); demo en vivo de Miguel el 10 oct, turno 5 (el otro día es el 8 oct). Antes
  se decía «3 oct»: lo corrigió f3 al leer Classroom el 26 sep.

## Reglas que no se rompen

- **Las contraseñas nunca van en un entregable** (ya pasó una vez en `mensaje_profesor.md` y quedó
  en el historial de git). `literalevel_codigos.txt` no se imprime ni se copia, ni siquiera
  enmascarado. En el mensaje al profesor basta con decir que su usuario y contraseña se los manda
  Miguel aparte.
- **Ninguna cifra sin fuente.** Cada número (métricas del modelo, tamaños del catálogo, tiempos)
  debe salir del código, de `investigacion/` o de `DESPLIEGUE.md`. Si no encuentras la fuente,
  márcalo como hueco y pregúntale a Miguel; no lo rellenes.
- **Las capturas** que muestren LiteraLevel o el diseño viejo se rehacen desde la app publicada, con
  un navegador sin ventana, a 390 px y en escritorio. Guárdalas en `entrega/capturas/` y anota de
  dónde salió cada una.
- **Los PDF** se recompilan (tectonic, según la skill `latex-en-esta-maquina`) y se revisan página
  por página antes de darlos por buenos.
- No cambies código de la app ni publiques nada: esta tarea es solo de documentos.

## Al terminar

- Una tabla por archivo con lo que cambió, lo que quedó pendiente y por qué.
- Actualiza `docs/ai/HANDOFF.md` con el estado y el siguiente paso.
- Avísale a Miguel. Si la Central o la sesión `literalevel-f3` necesitan saberlo, mándales un
  mensaje en español.

---

## Registro vivo (lo lleva la sesión de los entregables)

Rama `dev/entregables`, worktree `.claude/worktrees/entregables`. **Sin fusionar en master.**

### Decisiones de Miguel (26 sep)

- Nombre en los documentos: **«Pléyade (proyecto LiteraLevel)»**. El modelo sigue siendo
  `literalevel-v4` y la compañía ficticia sigue siendo **Peldaño**.
- El modelo articulatorio entra en los entregables: un subapartado (documento §7.8) y una
  diapositiva.
- Para las capturas con cuenta se usa la cuenta `miguel`, cuya contraseña se lee dentro del
  guion y nunca se imprime. El nivel real de Miguel es C2: el cuestionario en la app da
  **1,88**, lo más cercano a 1,85 que permite (la otra opción es 1,81). La cuenta queda con
  ese perfil.
- La cuenta Pro de Hugging Face sigue activa (7 USD al mes).
- El borrador de `mensaje_profesor.md` del 16 de septiembre ya se envió. Ahora el archivo es
  el mensaje de la entrega final.
- Classroom: queda fuera. Habría que entrar desde el navegador de Miguel, y el encargo
  prohíbe tocar la pantalla.

### Hecho (commits en `dev/entregables`)

| Commit | Qué |
|---|---|
| `1352740` | Inventario (`docs/ai/inventario_entregables_2026-09-26.md`); documento tex, pdf y md; 8 referencias nuevas con DOI comprobados |
| `942b6ed` | 22 capturas desde Vercel (móvil a 390 px y escritorio), con `entrega/capturas/registro.txt`; guion `tools/capturas_2026_09_26.mjs` |
| `2426f70` | Mensaje de entrega final al profesor; guion de la demo; guion del vídeo (md, tex y pdf), con 514 palabras habladas |
| `b4bdc8e` | Estrategia; presentación (16 diapositivas, con la del modelo articulatorio); cuaderno, solo el texto markdown, con las salidas intactas; README y PENDIENTES |

Los PDF se recompilaron con tectonic y se revisaron página por página: ninguna referencia rota,
y los desbordes que quedan son de menos de 3 pt o no se ven.

### Pendiente

- Miguel: revisar y fusionar `dev/entregables` en master.
- Miguel: poner a cero `uso_openai.json`, probar la lectura en vivo con su voz, grabar el
  vídeo y ensayar la demo (poner el perfil 1,20 en la cuenta y volver a medirse después).
- Declarado como hueco en los documentos: el contraste del tema de la marca sobre la galaxia
  y la prueba con lectores del front nuevo (A8). El tiempo de carga de la boca 3D en Vercel lo
  midió f3 el 26 sep (3,0–3,1 s sin caché del navegador; 8,9 s con la CDN fría; 1,7 MB por la
  red, no 1,4: corregido en los siete archivos que lo decían).
- ~~La bienvenida enseñaba una «L»~~: la cambió literalevel-f3 por el icono de Pléyade
  (`2b37573`, publicado). Ninguna de las 22 capturas muestra esa tarjeta, así que no hay
  que rehacer ninguna.

### 27 sep: vídeo narrado por Eos (pedido por Miguel)

- Miguel quiere que el vídeo lo narre **Eos**, en formato de anuncio al estilo Duolingo, y le
  preguntó al profesor si el formato vale. Mientras no conteste, la versión que cumple la rúbrica
  es `guion_video.md` (Miguel a cámara).
- Reparto: esta sesión lleva el guion (`entrega/guion_video_eos.md`) y la voz; literalevel-d6
  lleva la animación y el montaje; f3 (literalevel-86) lleva la lista de planos. El audio elegido
  se deja en `D:/literalevel_respaldos/eos_voz/`.
- Voz, primera tanda: gpt-4o-mini-tts-2025-12-15 (coral, marin, sage, shimmer, nova). **Miguel
  la descartó**: no suena natural.
- Voz, segunda tanda: Ava Multilingual (la misma voz de la Eos inglesa, en-US-AvaNeural, hablando
  en español; gratis con edge-tts), Emma Multilingual y gpt-audio-1.5 (marin y coral).
  `gpt-6-astra` no genera audio (400). Pendiente de que Miguel elija.
- Gasto de OpenAI: aprobado expresamente por Miguel el 27 sep («Tenemos la API. Utiliza el modelo
  más reciente»).
- Pendiente de Miguel: la duración (un anuncio corto de 60 a 90 s o el vídeo completo de unos
  3 a 4 min).
- **Traspaso (27 sep):** desde ahora el guion y la voz del anuncio los lleva **literalevel-0e**,
  que recibió de Miguel la instrucción más reciente; literalevel-d0 los deja. Las muestras de voz
  y los scripts del casting están en `D:/literalevel_respaldos/eos_voz/casting/` (tanda 1:
  `eos_*.mp3`; tanda 2: `tanda2/`). Los dueños de lo demás: el rig de Eos (lengua, dientes,
  mirada, cejas) es de literalevel-c2; la animación y el montaje, de literalevel-d6.
