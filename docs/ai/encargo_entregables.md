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
- **Boca 3D (modelo de Blender, en Pronunciar):** más ligera (texturas WebP: 3,5 → 1,4 MB por la
  red), con botones de zoom + y −, cámara lenta («Despacio») y giro («Explorar»). La cara parlante
  **Eos** (MetaHuman de Epic) sigue en desarrollo en otra sesión: no la presentes como terminada.
- **Fecha de entrega:** 3 oct 2026.

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
