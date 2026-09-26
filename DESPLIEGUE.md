# Desplegar LiteraLevel: Angular y backend

**Corte operativo del 14 de septiembre de 2026.** Son dos despliegues:

- Angular: `MikeMaki1763/literalevel-front`, sitio estático en
  <https://mikemaki1763-literalevel-front.static.hf.space/>.
- FastAPI y motor/respaldo Gradio: `MikeMaki1763/literalevel`, hardware
  `cpu-basic` existente. El despliegue selectivo `e56cf08` fue cotejado por
  hash el 13 de septiembre; véase el informe enlazado abajo.
- Persistencia: **resuelta el 10 de septiembre**, bucket privado montado en
  `/data`. No reinstalar esa parte siguiendo un diagnóstico anterior.

Los costes y tiempos de arranque del histórico son registros fechados, no
tarifas ni garantías actuales. Este procedimiento no requiere comprar planes,
cambiar hardware ni reescribir secretos. No hacerlo sin autorización expresa.

## Procedimiento vigente: backend selectivo

Un solo desplegador, rutas acordadas, revisión del diff y pruebas antes de subir.
No usar `upload_folder` sobre el repo ni incluir archivos ajenos sin revisar.

```powershell
python -X utf8 tools/desplegar_app.py --seco --solo app/api.py app/voz.py
```

`--seco` compara sin publicar y permite inspeccionar el trabajo sin commit.
Para publicar, **solo después de confirmar las rutas propias y recibir permiso**:

```powershell
python -X utf8 tools/desplegar_app.py --solo app/api.py app/voz.py
python -X utf8 tools/desplegar_app.py --estado
python -X utf8 tools/desplegar_app.py --seco --solo app/api.py app/voz.py
```

Las rutas son un ejemplo del cierre nocturno, no una lista obligatoria para
todo cambio. `--solo` admite rutas exactas de la lista blanca; publicar rechaza
cambios sin commit en esa selección. El script conserva los bytes revisados,
los escanea y usa `parent_commit` para no pisar una revisión remota nueva.

**Desde el 14 sep 2026 compara y sube el commit, no el disco.** Los bytes salen
de `git show <commit>:ruta` (`--commit REF`, por defecto `HEAD`, resuelto una
sola vez al empezar) y el texto va siempre en **LF**; los binarios (`.mp3`,
`.parquet`…) tal cual. Motivo: con `core.autocrlf=true` el disco tiene CRLF, y el
Space había quedado mezclado —lo subido con `git show` en LF, lo subido desde el
disco en CRLF y dos archivos con ambos—, así que `--seco` pedía subir archivos
idénticos en contenido. Ahora cada archivo sale como igual, nuevo, distinto o
«solo fin de línea: pasa a LF» (si hace falta, descarga el texto del Space para
distinguirlo). Pruebas: `python -B -X utf8 -m unittest pruebas_despliegue`.

**El reinicio 7 dejará el Space entero en LF.** Además de sus cambios, subirá
en LF `app/config.py`, `app/cuaderno.py`, `app/paletas.py` y `app/perfil.py`
(en CRLF) y `app/api.py` y `app/voz.py` (finales mezclados). Mismo contenido,
comprobado línea a línea contra `e56cf08`; no cambia el comportamiento.
No ejecutarlo sin opciones para una simple consulta: **el modo por defecto publica**.
Pruebas de esas guardas: `python -X utf8 pruebas_despliegue.py`, sin subir nada.

No sustituir el `app.py` ni el README del Space por `main.py`/README locales.
El montaje Gradio publicado utiliza `demo.launch(ssr_mode=False,
app_kwargs=api.para_gradio())`. `con_gradio` con uvicorn es la alternativa
local, no el arranque del Space.

Después de `RUNNING`, comprobar **JSON de `/api/salud`**, no solo HTTP 200:
el antiguo proxy SSR devolvía HTML con 200 para rutas API. Verificar lectura
Angular, CORS, un recurso estático y el rechazo de operaciones sin acceso,
sin llamar al proveedor de pago durante la comprobación básica. La segunda
comparación debe informar iguales los archivos seleccionados. El reporte
[del cierre selectivo](auditoria/despliegue_codex_2026-09-13_noche.md) conserva
hashes, pruebas, límites y reversión de solo esos archivos.

## Procedimiento vigente: front estático y assets

El front se compila desde `front/` con `npm.cmd run build`. Publicar solo el
resultado de `front/dist/front/browser/`, con los assets del mismo build;
no `node_modules`, fuentes, cachés ni el repositorio completo. `index.html`
debe conservar la meta `literalevel-api` con el origen público correcto del
backend. Los recursos `boca3d/cara.glb` y `boca3d/lengua.glb`, si forman parte
de la versión aprobada, deben viajar con los chunks que los cargan y su
procedencia documentada: un build HTML correcto sin GLB
no completa el recurso 3D.

La publicación debe revisar los bytes y el diff remoto, proteger la revisión
padre y conservar la configuración del Space estático. El coordinador prepara
un script de despliegue dedicado; **hasta verificarlo, no se prescribe aquí una
CLI inexistente**. Tampoco se afirma que el 3D esté publicado porque esté en local.
Después de subir, recargar una pestaña nueva: una pestaña antigua puede pedir
chunks eliminados y dar 404. Comprobar rutas Angular, solicitudes de assets,
conexión API y pantallas móvil/escritorio, incluido el respaldo si falta el GLB.

## La boca 3D didáctica en Pronunciar (24 sep 2026)

- **Publicado:** revisión del Space `5f542ee` del front, generada desde el
  commit `86063b0` (rama `publicar/boca3d-didactica`, avanzada después en
  master en local). Revisión anterior: `ec68419` (commit `8a992af`).
- **Qué entra:** solo `front/src/app/compartido/boca3d/`, los GLB y
  créditos de `front/public/boca3d/didactica/` y `[didactica]="true"` en
  los dos visores de `pronunciar.html`. El backend no cambia.
- **Qué NO entra:** D1-D3 (tutorial v2, Mi espacio, Repasar, Mi progreso)
  de las ramas `dev/*`: su front llama a rutas nuevas de `app/api.py` y
  `app/cuaderno.py`, que exigen desplegar antes la API, en un despliegue
  aparte.
- **`tools/desplegar_front.py`:** admite `boca3d/didactica/cara.glb` y
  `lengua.glb` como binarios, y `.txt` (los créditos CC BY del modelo) como
  texto revisado.
- **Comprobado en la app publicada** a 390 px, táctil: la meta apunta a
  `https://mikemaki1763-literalevel.hf.space`, `/f/` y `/θ/` de frente y de
  lado, sin desbordamiento ni errores de consola. Los GLB se sirven con una
  redirección al CDN: su `X-Linked-ETag` es el sha256 del archivo local (un
  `curl` sin `-L` baja la página de la redirección, no el GLB).
- **Peso:** `didactica/cara.glb` pesa 6,5 MB y `lengua.glb` 0,44 MB; se bajan
  solo al abrir «Boca en 3D».
- **Segunda publicación (24 sep, 17:27 CDMX):** revisión del Space
  `0d4a3b2`, commit `4c9d7d7`. La boca articula la palabra de ejemplo del final
  de cada audio (`palabras_audio.json`), se sincroniza por tramos, la lengua ya
  no forma «dos picos» en /θ ð/ y la cabeza lleva pelo corto, ojos abiertos,
  una sonrisa leve en reposo y la tez más clara. Comprobado en la app pública a
  390 px (/ʒ/ de frente, alejada con «Explorar» y de lado); `X-Linked-ETag`
  del GLB = sha256 local.
- **Tercera publicación (24-25 sep, noche CDMX), front y API:**
  - API: revisión del Space `a88531b` desde `cca283a` (aire 2D en /f/,
    `/api/progreso`, `POST /api/repaso`, textos de θ/ð y `GET /api/lectura/ipa`)
    y después `c49604e` desde `acbee33` (`ficha.py`: una obra de teatro sin
    capítulos ya no se toma por portadilla; PG844 se mide). Pruebas en árbol
    limpio: API 67/67, extremas 355/355, ficha, progreso 22/22, repaso 15/15,
    animación. Comprobado: salud, Gradio, SVG de /f/ con aire, progreso,
    lectura/ipa y el vistazo rápido de PG844 (1,36, B2).
  - Front: revisión `a9ae51f` desde `acbee33`: D1-D3 (Mi espacio, Repasar, Mi
    progreso), lectura de frases en 3D al compás del audio («Verla leída en
    3D»), cara nueva (mentón firme, mejillas que acompañan, /f v/ con cuerpo,
    pelo castaño rizado, tez clara), reposo sin vibración. Front 446/446 y build.
    Probado a 390 px en la app publicada (lectura 3D con `/api/voz` simulado y
    micrófono falso, sin coste) y en local (Mi espacio). `X-Linked-ETag` del
    GLB = sha256 local.
- **Cuarta publicación (25 sep, madrugada CDMX), API y front del commit
  `82cb26a`:** API `79bdcfe` (`POST /api/lectura/vivo`: clave efímera de OpenAI
  para la lectura en voz alta en vivo, un uso por sesión; sin cuenta, 403 sin
  cobrar) y front `4f94c4e` (botón «Leer en voz alta (en vivo)» en el lector,
  ojos abiertos en la malla). Pruebas: API 68/68, extremas 355/355, front
  454/454. Comprobado en producción: salud, Gradio, clave efímera real con la
  cuenta profesor (60 → 59), y la lectura en vivo en la app publicada con una
  lectura sintética (69 palabras a 122 por minuto; «universally», omitida
  adrede, sale como saltada). `X-Linked-ETag` del GLB = sha256 local.
- **Quinta publicación (25 sep, mañana CDMX), API y front del commit
  `7fe5563`:** API `1630528` (`GET /api/lectura/ipa?audio=`: `inicio` y `fin`
  por palabra desde el `.tiempos.json` que la corrección ya guarda junto al mp3;
  sin llamadas nuevas a OpenAI) y front `c3b51ae` (la boca 3D lee la frase del
  TTS palabra a palabra en su sitio, `lineaFraseAlineada`; /ɛ/ y /eɪ/ con la
  mandíbula medida en caras reales, 0,67 y 0,70). Pruebas: API 69/69 en árbol
  limpio (extremas no: solo cambió un endpoint aditivo de `api.py`), front
  456/456, boca 3D 149 + 2 nuevas, `medir_didactica --exigir` y grosor labial.
  Comprobado en producción: revisión en marcha `1630528`, salud (buscador
  listo), Gradio 200, `lectura/ipa` con `audio` inexistente sin marcas, front
  a 390 px sin errores de consola con la meta de la API correcta, y el chunk
  servido lleva `ɛ:{mandibula:.67}`. El caso con marcas reales necesita una
  corrección de pago: queda para la próxima prueba de Miguel.

- **Sexta publicación (25 sep, mañana CDMX), solo front:** revisión `0f41932`
  desde `de1498e`. La boca 3D mueve palabras y frases con el modelo
  articulatorio aprendido (dominancia de GRID, `boca3d/modelo.ts`; interruptor
  `MODELO_ARTICULATORIO_ACTIVO`). Sin cambios en la API. Front 460/460; en la
  app publicada, «Verla leída en 3D» sin errores a 390 px; tira de fotogramas
  modelo contra reglas revisada.

- **Séptima publicación (25 sep, mañana CDMX), solo front:** revisión `eef0543`
  desde el merge de `dev/articulacion-v2` (pestaña «Mi espacio» en la barra de
  navegación). Front 460/460; comprobado en la app publicada a 390 px.

- **Octava publicación (26 sep, CDMX), solo front:** revisión `7820589`
  desde `37f5845` (master y `publicar/v2` avanzados en rápido). La app pasa a
  llamarse **Pléyade** en la interfaz (API, Spaces y paquetes siguen igual),
  iconos y manifest nuevos, «Sobre Pléyade» al pulsar el logo, y la portada
  sobre un fondo astral propio (`tools/marca/galaxia.py`).
  `desplegar_front.py` admite los binarios de `marca/` y los iconos. Front
  460/460, `pruebas_despliegue_front.py` 16/16; en la app publicada a 390 px y
  1366 px, sin respuestas 4xx/5xx, sin desplazamiento lateral y con el panel
  abriéndose desde el logo.

- **Novena publicación (26 sep, CDMX), solo front:** revisión `72b3dd7`
  desde `df7b6ad`. El fondo astral pasa a todas las pantallas (body); cada
  pantalla se lee sobre una lámina translúcida de su tema (93 % en claro y
  papel, 74 % en noche), sin desenfoque. Front 460/460; capturas de
  Encontrar, libro, lector, Pronunciar, Mis palabras y Mi espacio a 390 px y
  1366 px en claro, noche y papel; en la app publicada, galaxia y lámina
  presentes y sin respuestas de error.

## Historial de infraestructura y opciones evaluadas

Lo siguiente conserva decisiones y observaciones de los días 10 al 13 de
septiembre. Los precios, cuotas y alternativas no se han reconsultado para
recomendar una contratación. El arranque medido entonces fue 31 s hasta
`RUNNING` y 32 s hasta responder (`medir_arranque.py`).

## Lo que hay que colocar
> **Lo que hay desplegado NO es lo que decía este documento**, y se comprobó
> listando el Space el 10 de septiembre de 2026:
>
> - El punto de entrada es **`app.py`** en la raíz del Space, no `main.py`.
>   Hugging Face busca `app.py` por convención y ahí se declara
>   `app_file: app.py`. `main.py` existe en el repositorio local y **no está
>   subido**: son dos puntos de entrada equivalentes, y el que corre es el del
>   Space.
> - El **diccionario de 243 MB está dentro del Space**, junto con
>   `catalogo_recomendaciones.csv` y los embeddings del catálogo. No se montan
>   como repositorio de datos aparte: eso era el plan y no es lo que se hizo.
>   Lo que sí vive fuera es el **modelo**, en `MikeMaki1763/literalevel-v4`, y
>   `app.py` apunta ahí con `LITERALEVEL_MODELO`.
>
> Se deja escrito porque el plan y la realidad divergieron, y quien lea solo el
> plan desplegará mal.


| Qué | Tamaño | Dónde va |
|---|---|---|
| Código (`app/`, el punto de entrada, pruebas) | ~120 KB | el repositorio del despliegue |
| `catalogo_recomendaciones.csv` | 1 MB | el repositorio del despliegue |
| `modelo_v4/` | **332 MB** (los pesos solos, 328) | fuera: repo de modelo, montado de solo lectura |
| `kaikki_diccionario.db` | **243 MB** | **en el propio Space**, no en un repo aparte (ver el aviso de abajo) |

Los 575 MB de datos **no van en el repositorio** y están en `.gitignore`. La app
los localiza por variable de entorno, y eso ya está probado moviéndolos fuera:

```
LITERALEVEL_MODELO       -> carpeta del modelo v4 O el identificador de un
                            repositorio del Hub (por defecto ./modelo_v4;
                            en el Space, MikeMaki1763/literalevel-v4)
LITERALEVEL_CUENTAS      -> perfiles con acceso a lo de pago, en formato
                            usuario:contrasena:tope separados por comas.
                            Tope 0 = sin limite. Vacia = puerta abierta.
LITERALEVEL_DICCIONARIO  -> SQLite de Kaikki        (por defecto ./kaikki_diccionario.db)
OPENAI_API_KEY           -> secreto; sin ella la app degrada, no falla
```

## Consumo medido, no estimado

**~1,05 GB de RSS** con el modelo y los embeddings del catálogo cargados; con
spaCy y el diccionario encima, pico realista de **1,2–1,5 GB**. Esto **descarta**
Render free, Koyeb free y cualquier plan de 512 MB. No lo intentes.

## Opción A — Hugging Face PRO, 9 $ un mes

La más corta: Gradio nativo, cero reescritura, 16 GB de RAM.

**Ojo, esto cambió a mediados de 2026** y casi toda la documentación de terceros
sigue desactualizada. La doc oficial del Hub dice literalmente:

> *"Static Spaces are free for everyone. Gradio and Docker Spaces run on compute
> and require a paid plan to create: PRO for personal accounts."*

Pasos:

1. Suscribirse a PRO y crear un Space **Gradio**, hardware CPU Basic
   (2 vCPU / 16 GB / 50 GB efímeros, sin coste por hora).
2. Subir el **modelo** como repo aparte: `python desplegar_datos.py`. (El
   diccionario acabó dentro del Space; ver el aviso de arriba.)
3. En el README del Space, el front matter declara el punto de entrada:

   ```yaml
   ---
   title: LiteraLevel
   emoji: 🧊
   colorFrom: blue
   colorTo: indigo
   sdk: gradio
   sdk_version: 6.26.0
   app_file: app.py
   pinned: false
   ---
   ```
4. `OPENAI_API_KEY` y `LITERALEVEL_CUENTAS` como **Secrets** del Space —las dos
   llevan credenciales: la clave de pago y las contraseñas de los perfiles. Sin
   `LITERALEVEL_CUENTAS` no hay puerta y lo que cuesta dinero queda abierto a
   cualquier visitante. `app/config.py` ya lee `os.environ` antes que el
   archivo, así que no hay que tocar código.
5. Ajustar `LITERALEVEL_MODELO` y `LITERALEVEL_DICCIONARIO` a donde queden
   montados los datos. `LITERALEVEL_MODELO` acepta una carpeta local o el
   identificador de un repositorio del Hub; en el Space es
   `MikeMaki1763/literalevel-v4`. `LITERALEVEL_DICCIONARIO` es siempre la ruta
   de un archivo `.db`: ahí un identificador del Hub no vale.
6. Comprobar en la pestaña **Estado** de la app que dice «Perfiles: N válidos
   de N declarados». Si descarta alguno, ahí sale el motivo: el secreto se
   edita a ciegas y una contraseña con `:` dentro rompe su entrada.

Contra: en `cpu-basic` el Space **se duerme por inactividad** y el primer
visitante paga un arranque frío de decenas de segundos (torch + 328 MB). Para
una evaluación es asumible; si molesta, un mes de CPU Upgrade.

## Opción B — ZeroGPU, gratis

La doc del Hub deja una excepción: una cuenta personal gratuita en buen estado
puede alojar **hasta 2 Spaces Gradio sobre ZeroGPU**.

Pero léelo antes de ilusionarte: ZeroGPU está pensado para cargas **de GPU**, y
un distilroberta sobre 8 bloques de 250 palabras no necesita GPU. La cuota es de
**5 minutos de GPU al día**, y su documentación **desaconseja la carga perezosa**
— que es justo la regla de este proyecto para que la app abra en el acto. Si
obedeces a ZeroGPU rompes eso.

Viable si los 9 $ son un problema real. No es el camino limpio.

## Opción C — Modal, gratis de verdad

**30 $/mes de créditos renovables, sin tarjeta.** Escala a cero, factura por
segundo, URL estable con `modal deploy`. Con un profesor evaluando no se gastan
ni de lejos. Gradio se monta como app ASGI y los 575 MB van en un Volume.

Coste: una tarde de ingeniería y aprender su modelo mental. Es el camino más
largo de los tres, y el único sin factura.

## Lo que ya no hace falta resolver

- El punto de entrada mete `app/` en `sys.path` y expone `demo`. **Y sí puede
  llamarse `app.py` conviviendo con la carpeta `app/`**, que es lo que hay
  desplegado: aquí se decía que chocarían, y no chocan, porque el archivo
  nunca hace `import app` —mete `app/` en la ruta e importa `ui` directamente—.
  Comprobado en el Space, que lleva los dos y arranca.
- Las rutas del modelo y del diccionario son configurables, y está comprobado
  con los datos fuera del repositorio.
- `requirements.txt` instala `en_core_web_sm` por URL directa, porque en un
  despliegue no hay quien ejecute `python -m spacy download`.

## Los audios de los fonemas (12 sep 2026)

La corrección de voz enseña el fonema que falla con un mp3 pregrabado. Son 41
archivos en `app/audio_fonemas/`, versionados, y **no se generan en el Space**:
se generaron una vez en local con `tools/generar_fonemas.py` y suben como
cualquier otro archivo de la lista blanca de `tools/desplegar_app.py`, que los
enumera desde `app/fonemas.py` y se niega a desplegar si falta uno.

- **Son binarios, y Hugging Face rechaza binarios fuera de LFS/Xet.** El
  `.gitattributes` del Space se miró el 12 de septiembre y **no tenía regla
  para `*.mp3`** (sí para `*.parquet` y `*.npy`). `desplegar_app.py` la añade él
  solo, en un commit aparte y ANTES de subir los audios, porque el Hub decide si
  un archivo va por LFS con el `.gitattributes` que ya está en el repositorio, no
  con el que viaja en el mismo commit. `--seco` avisa de que falta sin tocar nada.
- **Tienen que poder servirse.** `ui.RUTAS_PERMITIDAS` incluye
  `app/audio_fonemas/`, y el `app.py` del Space ya pasa `ui.RUTAS_PERMITIDAS`
  a `launch()`. Sin eso, el `<audio>` daría 403.
- **No usan la clave.** Se oyen sin `OPENAI_API_KEY` y sin gastar crédito.

## Los corpus libres en el catálogo (12 sep 2026)

StoryWeaver, African Storybook, VOA Learning English y Let's Read entran al
catálogo **solo con licencia libre** (pipeline en `PIPELINE_CORPUS.md`). Los
genera `tools/catalogar_corpus.py` y viajan en tres archivos:

| Archivo | Qué es | Cómo sube |
|---|---|---|
| `catalogo_externo.csv` | filas del catálogo, con licencia y atribución | lista blanca |
| `corpus_abierto.parquet` | el texto que la app sirve al abrir el libro, con la atribución al final | lista blanca (LFS: el Space tiene `*.parquet`) |
| `catalogo_emb_ext_<huella>.npy` | embeddings del buscador para esas filas | **a mano**, con `upload_file`: su nombre cambia con cada versión del externo |

- Sin el `.npy` en el Space, la primera búsqueda recalcula esas filas en 2 vCPU.
  Los de Gutenberg (`catalogo_emb_<huella>.npy`, 82 MB) no se tocan.
- El CSV se escribe con **LF**: con CRLF su huella, y con ella el nombre del `.npy`,
  cambiaba según la máquina que lo generara.
- **Falso positivo de credenciales**, ya resuelto: la URL de VOA de *The Cask of
  Amontillado* contiene «ca**sk-of-amontillado**…» y casaba con el patrón de las
  claves de OpenAI, así que el guion se negaba a desplegar. Los patrones exigen
  ahora que `sk-` y `hf_` empiecen su propio token.

## Montar la API de Angular en el Space: el primer intento falló (13 sep 2026)

Se intentó servir `app/api.py` (FastAPI) en `/api` y Gradio en `/` desde el mismo
proceso, cambiando en el `app.py` del Space `demo.launch(...)` por
`uvicorn.run(api.con_gradio(demo), host="0.0.0.0", port=7860)`.

- **En local funcionaba entero** (`PORT=7901 python app.py`): `/api/salud`, `/api/perfil`
  con y sin `X-Lector`, Gradio en `/` y el audio de los fonemas.
- **En el Space no.** Llegó a RUNNING, pero `/api/salud` devolvía la página de carga de
  Hugging Face y después todo dio 502/503. El guion de despliegue lo deshizo solo,
  restaurando el `app.py` anterior (commit del Space `bf9f0be`), y Gradio volvió a 200 en
  menos de un minuto.
- **La causa probable** está en el arranque bueno: `Running on local URL:
  http://0.0.0.0:7860, with SSR ⚡ (Node proxy -> Python :7861)`. Un Space `sdk: gradio`
  corre Gradio con renderizado en servidor: `launch()` pone un proxy Node en el 7860 y
  Python en el 7861. Un uvicorn propio en el 7860 no levanta ese proxy. La imagen además
  usa **Python 3.13**, no el 3.11 local.
- **Los registros del intento fallido no se conservan**: `/logs/run` y `/logs/build`
  solo devuelven el último arranque. Si falla, hay que leerlos *antes* de deshacer.

Tres reglas para el siguiente intento:

1. Que siga arrancando `demo.launch()` y las rutas de `/api` se registren sobre la app
   de Gradio; probarlo en local con `GRADIO_SSR_MODE=true` y Python 3.13.
2. **Comprobar el JSON, no el código HTTP**: con Gradio montado, cualquier ruta
   desconocida (`/api/salud` incluida) responde 200 con su HTML.
3. Desplegar solo `app.py` y `app/api.py`, en un commit propio, con la vuelta atrás
   automática preparada y el `app.py` actual guardado antes.

**El segundo intento funcionó** (commit del Space `c80356f`). La causa exacta estaba en
el código de Gradio 6.26 (`templates/node/build/proxy_routes.js`): con SSR, el proxy de
Node solo pasa a Python `/gradio_api`, `/config`, `/login`, `/logout`, `/theme.css`,
`/robots.txt`, `/pwa_icon`, `/manifest.json` y `/monitoring`; cualquier `/api/*` va a la
página de Gradio. El `app.py` del Space sigue llamando a `demo.launch(...)` y añade:

- `ssr_mode=False`: Python atiende el 7860 directamente, como en local;
- `app_kwargs=api.para_gradio()`: las rutas entran en la app FastAPI que crea Gradio.

Comprobado contra el Space: `/api/salud` con su JSON, `/api/perfil` 400/200, preflight
CORS desde `https://mikemaki1763-literalevel-front.static.hf.space` con `x-lector`,
Gradio en `/` y `/config`, y el audio de un fonema. En el log de arranque aparece
`Exception ignored in: BaseEventLoop.__del__ … Invalid file descriptor: -1` (Python
3.13, dos segundos después de arrancar): Python lo ignora y no rompe nada.

## La tabla del IPA y los arreglos del front, en despliegues pequeños (13 sep 2026)

Despliegues seguidos, cada uno con sus comprobaciones y su vuelta atrás preparada:

| Commit del Space | Qué subió | De quién (commit del repo) | Comprobado |
|---|---|---|---|
| `405694e` | `app/api.py` | e6, `e39d9f0` | la sinopsis sin perfil da 403 sin «arriba del todo» |
| `23e434a` | `app/ui.py`, `app/articulacion.py`, 41 + 44 mp3 | 4e, `7e097e0` + `b19b707` | pestaña en `/config`, mp3 americano y británico como `audio/mpeg` |
| `6b71a6d` | `app/api.py` | e6, `dc0efa9` | `/api/fonemas` 41 y 44 con `?v=`; PG8171 abre en la obra, sin licencia; frases limpias |
| `b8a3b01` | `app/lexicon.py`, `app/ui.py`, `app/articulacion.py` | 4e, `5033e69` | pestaña «Sonidos IPA»; `/api/palabra` con los campos nuevos |
| `5765c0d` | `app/api.py` | e6, `3c09934` | frases sin los `_` de cursiva de Gutenberg |
| `ec68aa2` | `app/api.py` + `app/ui.py`, `app/voz.py`, `app/lexicon.py` | e6 `295f3a0` + 4e `3a3d546`, un solo reinicio | 20 frases de PG56711 sin índices; prueba de pago con invitado8 (entrar, medir en frío 5,3 s, palabra por IA 11 s, sinopsis 8,8 s, voz 3,6 s) |
| `dbd997e` | `app/api.py` | e6, `536ee10` | `/api/voz/falladas` guarda la palabra con su frase; audio de la palabra fallada 200 |
| `f5bdd46` | `app/ui.py`, `app/lexicon.py`, `app/voz.py`, `app/fonemas.py`, `app/pronunciacion_cmu.tsv` y su licencia | 4e, `519b802` (hallazgos de Codex) + `5029a40` (fonema determinista) | dos voces con el mismo audio dan el mismo fonema /t/ con IPA /ˈtɹædʒɪk/ y consejo de `articulacion.FICHAS` |
| `e793383` | `app/api.py`, `app/ui.py`, `app/lexicon.py`, `app/voz.py`, `app/fonemas.py` | 4e `5fa2cea` (compuestos) + e6 `66a0427` | «house» con `dudoso` coherente con y sin sesión; `/api/voz` con acento FR da 422; «war-chant» con `parte_del_diccionario` «war» e IPA por IA; voz con «war dance» trae audio de cada pieza |

| `5de9ab4` | `app/ui.py`, `app/voz.py`, `app/articulacion.py` y el módulo nuevo `app/animacion_articulatoria.py` | 4e, `05783c0` (animaciones 2D) | 85 SVG de la tabla en `/config`, servidos desde `/data/articulacion_svg/` como `image/svg+xml`; la voz de un compuesto ya solo detalla la pieza que falla |

| `bdc0b8d` | `app/api.py` | e6, `edbcd01` | `/api/articulacion/{ga,rp}/{símbolo}.svg` y `palabra.svg` dan 200 `image/svg+xml` con caché de 30 días y `nosniff`; fuera de inventario 404; IPA inválida 422 |
| `dfc755c` | `app/api.py` | e6, `2a49bf2` | con acento UK el sonido que falla y su audio son británicos (`/api/fonemas/rp/…`); la IPA de la palabra sigue US si no hay transcripción británica (decisión de la central) |
| `e0e5f81` | `app/api.py`, `app/ui.py`, `app/reader.py` | 4e `514786b` + `9eb3c91` + `17b8ac3`, e6 `d7098e9` | subida de 21 MB da 413 a los 0,7 s (curl; urllib ve `SSLEOFError` porque sigue enviando); registro: «_ip: x-forwarded-for con 1 valores (publica); se usa el 1», así que no hace falta `LITERALEVEL_SALTOS_PROXY` |
| `e3a79cb` | `app/api.py`, `app/catalogo.py`, `app/ficha.py`, `app/lexicon.py`, `app/ui.py`, `app/animacion_articulatoria.py`, `avisos_contenido.csv`, `correcciones_catalogo.csv` | f4 `de8a4a8`, 4e (5 commits), e6 `e5ae1ad` | aviso de contenido en ficha y tarjetas; PG17824 6.º por nivel; PG2242 a 1,713; «bank» sin sesión con 4 acepciones principales; frases de Alice sin comillas sueltas; `alice.txt` conserva su nombre; sinopsis de Alice regenerada sin el final (se borró `analisis/47f56b5ec94e389e56c5-sinopsis.json` del bucket) |
| `c9ee482` | `app/catalogo.py`, `app/ui.py`; `app/voz.py`, `app/config.py`, `app/cuaderno.py`, `app/paletas.py`, `app/perfil.py` solo a LF | f4 `061df6b` (busqueda por titulo) + 4e `1a4b998` (cita por clausula), subido con `desplegar_app.py --solo` desde `c675b93` | «Little Black Sambo» en `/api/buscar` da PG1330 y PG17824 primeros; aviso de PG17824 intacto; segunda pasada de `--seco`: solo `app/api.py` por fin de linea (sucio en el disco, va al reinicio 8) |
| `8107f18` | `app/api.py`, `app/ui.py`, `app/voz.py`, `avisos_contenido.csv` | e6 `32534bc` + `73d956e`, 4e `d765ee0`, f4 `dcb8c83`, con `desplegar_app.py --solo` desde `db366b8` | aviso en PG17824 y PG1330; «cita» de 31 palabras frente a la oración de 106; DELETE de un libro del catálogo 400; `/api/voz/falladas` sin base con `aviso` null; dos sinopsis simultáneas de PG2542 con el mismo texto y un solo `*-sinopsis.json` en el bucket; segunda pasada de `--seco`: **nada que subir, Space entero en LF** |
| `de36496` | `app/api.py`, `app/animacion_articulatoria.py`, `app/voz.py`, `app/lexicon.py` | e6 `ee80fd9` + `dc340a4` (dur/una, PG1661, `/api/voz/ritmo`), 4e `9f5f909`, `55d546c`, `b41ff5e` (lectura natural), `0973777`, `9f29f05`, `da5c96d` (tope de dur a 30 s), `cdc7b6b` (IPA por forma), con `desplegar_app.py --solo` desde `a0e7284` | `θ.svg?dur=2.5&una=1` distinto del ciclo; «eclipses» con `/ɪkˈlɪpsɪz/`; PG1661 empieza en «To Sherlock Holmes»; `POST /api/voz` (cuenta miguel, audio SAPI de «Don't you want to come with us?») con `ritmo.medido` true y reducciones doncha/wanna marcadas IA; `GET /api/voz/ritmo` con 1 intento; segunda pasada de `--seco` desde `af7f6a9`: nada que subir |
| `26b303c` | `catalogo_externo.csv`, `corpus_abierto.parquet`; antes, `catalogo_emb_ext_c0de66f8d3dfff21.npy` a mano con `upload_file` (`69ed77e`) | f4 `377a650`: StoryWeaver medido con el v4 en CPU local (`tools/medir_corpus.py`, 12.800 unidades) y `tools/cerrar_corpus.py`; externo 3.919 -> 15.357 filas. **La misma obra entra una vez, con StoryWeaver delante de Let's Read** (letsread 424 -> 326, african_storybook 281 -> 278) | `/api/estado` 68.536 libros; `/api/recomendar` con perfil A2: 9 cuentos nuevos de StoryWeaver entre 30 (las 12 primeras siguen siendo Gutenberg, que se ordena por descargas); `/api/buscar` con resultados SWV y ASB, 21 s la primera consulta por la carga del modelo, sin recalcular el `.npy`; SWV100019 se abre; segunda pasada de `--seco` desde `3a532b5`: nada que subir |
| `2bb1276` | `app/api.py` | e6 `0ba8219` (cherry-pick de `35d105c`: topes por IP y hora de medidas 40 y curvas 6, cola de 4 curvas vivas, nosniff en `/api/audio`, `dur` hasta 30 s), con `desplegar_app.py --solo` desde `e7a2f1c` | `θ.svg?dur=17.2&una=1` y `dur=20` distintos de `dur=10`; nosniff en el mp3; muestra 200; 7 curvas seguidas de cuentos SWV de 182 palabras: 6 con 200 y la 7.ª con 429, y un libro ya medido sigue dando `ya_medido` tras el tope; `/api/estado` 68.536; `/api/recomendar?n=30`: A1 con 30 de 30 textos libres, A2 con 11 (posiciones 20 a 30), B1 con 0; segunda pasada de `--seco` desde `11c9d47`: nada que subir |
| `71f6a1d` | `app/catalogo.py`, `app/api.py` | f4 `d5ed4b5` (textos libres intercalados en `por_nivel`: puestos 2, 5, 8…) + e6 `281c89e` (aviso propio del 429 de medidas y curvas), con `desplegar_app.py --solo` desde `32557f4` | `/api/recomendar?n=30`: A1 con 30 de 30 libres; A2 con 11 (2, 5, 8 … 29, 30); B1 con 10 (2, 5, 8 … 29); 3 en las 9 primeras en A2 y B1; PG17824, con aviso, 9.º en B1; la 7.ª curva seguida da 429 «Has llegado al límite de curvas de libros de esta hora… Leer y buscar siguen funcionando.»; segunda pasada de `--seco` desde `32557f4`: nada que subir |
| `ce104d0` | `app/api.py`, `app/voz.py` | e6 `b9d30ca` («temas» y «portada_ia» en tarjeta y ficha, `GET /api/portadas/{ID.ext}` con nosniff) + 4e `2974d49` (IPA de enlaces del diccionario, énfasis fuera de palabras funcionales), con `desplegar_app.py --solo` desde `515a449` | PG1661 con «Detective and mystery stories, English» y `portada_ia` null; `/api/portadas/PG1661.webp`, minúsculas, `.svg` y `..%2F` dan 404 (con `%00` da 400 antes de la ruta); 30 tarjetas con temas; `recomendar` n=30 en 0,33-0,37 s (antes 0,33-0,41: los `stat()` de la portada no se notan con la carpeta vacía); ficha de PG1661 en 2,2-3,3 s, igual que antes; segunda pasada de `--seco` desde `515a449`: nada que subir |
| `371db00` | `app/api.py`, `app/ui.py`, `app/ficha.py`, `app/catalogo.py` | f4 `8ee42f0`: `ficha.para_medir` (la atribución de un texto libre no se puntúa), libres por cercanía al nivel y `medido_en_bloque` en tarjeta y ficha. Completa el `0e270f9` de e6, que se había llevado las llamadas a `para_medir` sin la función. e6 `0e270f9` + `95a3839`: plurales y nota de nivel. Subido con `desplegar_app.py --solo` desde `9be2c42` | «¿Cómo de difícil es?» de SWV229485 da 0,007 A1 (antes 0,35) y su curva rápida recalculada, 0,007. `medido_en_bloque` sale true en SWV100019 y false en SWV229485 y PG1661. A2 abre con SWV161290/198230/282453 (0,40) y B1 con SWV142665/411122/480165 (0,80), sin cuentos en común. **Borradas del bucket las 12 curvas guardadas de textos libres** (`analisis/*-rapido.json` de swv…txt, medidas con la atribución dentro; se recalculan gratis al pedirlas); las sinopsis, intactas. Segunda pasada de `--seco` desde `b81af8d`: nada que subir |
| `7c09d90` | `corpus_abierto.parquet` | f4 `04fced0`: texto servido sin U+FEFF, sin párrafos repetidos seguidos y sin páginas dobles; la medida no cambia. Subido con `desplegar_app.py --solo` desde `ab4e36f` | Estado igual antes y después (68.536). SWV138722 y SWV229485 conservan letra, dificultad y `medido_en_bloque`. SWV138722 pasa de 669 a 628 palabras («Laptop was opened» ×1) y SWV229485 de 201 a 199 (sin U+FEFF). Segunda pasada de `--seco`: nada que subir |
| `484b83b` | `app/catalogo.py`, `no_lectura_externo.csv` (nuevo en la lista blanca) | f4 `3524357`: con el ajuste de nivel, el nivel ordena solo dentro de lo relevante (a 0,05 del mejor parecido) y un título acertado va delante; 163 textos libres que no son lectura en inglés (`tools/marcar_no_lectura.py`: 115 con menos de 10 palabras distintas en alfabeto latino, 48 con menos del 60 % en el diccionario inglés) fuera de buscar y recomendar, sin tocar el CSV externo ni su `.npy`. Diagnóstico de e6. Subido con `desplegar_app.py --solo` desde `3524357` | Con perfil 0,95, «A Midsummer Night's Dream» saca primero sus tres ediciones (PG1514, PG2242, PG1113). «amor» ya no empieza por edws, Love story (en coreano) ni bumbumyj,jc. «love» con ajuste pone primero los relevantes de B1. Ningún id marcado en seis búsquedas ni en `recomendar` A2 y B1 (30 tarjetas; 11 y 10 libres). Primera búsqueda en frío en 19,7 s. Segunda pasada de `--seco`: nada que subir |
| `f237e61` | `app/api.py`, `app/ui.py` | f4 `31325a4`: S1 y S2 de la auditoría cruzada de 4e. `/api/voz` y la subida leen el formulario en async y lo demás va a `run_in_threadpool` (whisper, gpt y tts-1, o escribir y abrir el libro, bloqueaban el proceso entero). La etapa completa de `/api/palabra` ya no retiene el candado léxico durante OpenAI. Con e6 `cb799bc`: «1 minuto», y un solo tiempo si los dos ritmos coinciden. Tuvo que ir en el mismo reinicio: `api.py` ya llamaba a `ui._reloj_llano`. Subido con `desplegar_app.py --solo` desde `72c9ee6` | Salud 200 y estado 68.536. `/api/voz` sin sesión de pago da 403 con su motivo en 0,3 s, y un audio corto 422. Un `.txt` se sube, se abre, se borra (200) y el segundo borrado da 404. `/api/palabra` en la etapa diccionario, 200. `/api/salud` en 0,33-0,38 s mientras se sube un `.txt` de 6 MB. Un `.txt` de 168 palabras dice «entre 1 minuto y 2 minutos». Segunda pasada de `--seco`: iguales 2, nada que subir |
| `6e0b972` | `app/catalogo.py`, `app/ficha.py`, `catalogo_externo.csv`, `corpus_abierto.parquet`, `no_lectura_externo.csv`; antes, `catalogo_emb_ext_5e8a5dab191c1917.npy` a mano con `upload_file` (`4964f2d`) | f4 `6945046`: auditoría cruzada de e6 sobre catálogo y despliegue. **S1:** los 15.367 textos libres se indexan por su texto y sus temas, no solo por título y autor: `hook` es el arranque del texto (12-30 palabras) y `huella_texto` son los temas sin «reading level N» más las 40 palabras siguientes; el `.npy` externo se calculó por partes en CPU. **S2:** la cola de cada grupo se mide (externo 15.357 -> 15.367; 882 fuera por el filtro de prosa y 2 por grupo corto, contados aparte). M1 `buscar` recorre el orden entero; M2 huella del modelo en la clave de medida; M3 StoryWeaver sin licencia no entra; `para_medir` quita la atribución de un texto sin cuerpo (SWV137935, `no_lectura` 163 -> 164). Subido con `desplegar_app.py --solo` desde `6945046` | Estado 68.546. «a girl who makes an umbrella» saca SWV211552 (Chunchun) primero, con y sin ajuste. «love» con B1: 11 de 12 sobre amor, todos libres y con gancho. «A Midsummer Night's Dream» con perfil 0,95: PG1514, PG2242, PG1113. Ningún id de `no_lectura` en seis búsquedas ni en `recomendar` A2 y B1 (30 tarjetas; 11 y 10 libres); ninguna tarjeta libre sin gancho. **«amor» sigue mal** («Design and tradition» por el autor «Fenn, Amor»): es del rescate por nombre y va al reinicio 19. Primera búsqueda en frío en 20,9 s. Segunda pasada de `--seco`: iguales 5 y el `.npy` ya en el Space, nada que subir |
| `053a486` | `app/api.py`, `app/catalogo.py`, `app/lexicon.py`, `app/voz.py`, `catalogo_externo.csv`, `no_lectura_externo.csv`; antes, `catalogo_emb_ext_de142b47fda8c8bf.npy` a mano con `upload_file` (`45bf9a1`) | Subido con `desplegar_app.py --solo ... --commit bffc69d`: los seis tal cual los probó el árbol limpio, porque 4e hizo commit de sus restos de voz (`2c0e681`, para el reinicio 20) en vez de apartarlos. f4 `c63ce44`: el 422 ya no devuelve la entrada (en `/api/entrar`, la contraseña), también en `para_gradio`; candado por lector y `nombres.json` atómico en las subidas; candado en `CacheLexico`. f4 `7d94bd9`: el nombre solo rescata con el título entero o el apellido y si se parece a lo pedido (`MARGEN_SEMANTICO_NOMBRE` 0,20), una palabra suelta también se busca en «historias de» y «libros sobre» (76 -> 88 de 96), 89 filas sin título fuera, URL fuera de ganchos y huellas. f4 `a557288`: anuncios solo en StoryWeaver y con enlace comercial; `no_lectura` 164 -> 185. Con 4e `d58b0be` (voz y léxico) | «amor» con perfil B1: 12 de 12 sobre amor, con y sin ajuste, sin «Design and tradition». «Jane Austen» sin Jane G. Austin; «cuentos de miedo» sin los himnarios de Brownlie; «cuentos/historias sobre la lluvia y los agricultores» con Rain y The Water Seed; «viaje al espacio y la luna» con Journey To The Moon; dostoyevski, chejov y Midsummer (0,95) igual; paraguas y «love» (B1) bien. Ningún id de `no_lectura` ni gancho con enlace en 14 búsquedas ni en `recomendar` A2 y B1. 422 de `/api/entrar` y del cuestionario sin la entrada. Dos subidas a la vez del mismo lector conservan su nombre. Segunda pasada de `--seco --commit bffc69d`: iguales 6, nada que subir |
| `af72fb0` | `app/voz.py`, `app/lexicon.py` | 4e `2c0e681`, restos de voz de la ronda 2 de e6: sin ninguna palabra oída no se guardan fallos (whisper devuelve "" en silencio), la IPA toda ASCII solo vale si no es la palabra escrita, y «Mr.», «Mrs.», «Dr.», «St.» no cortan la frase para el enlace. El candado de `CacheLexico` (f4 `c63ce44`) sigue. Subido con `desplegar_app.py --solo ... --commit fdbc54e` tras árbol limpio de 12 suites en D: (api 55/55, extremas 349, integración 27, corpus 39, voz, voz_ritmo, voz_concurrencia, lexicon, despliegue, ficha, smoke, voz_temporal) | RUNNING en 46 s. Salud 200 y estado 68.546. `/api/voz/ritmo` con «Mr. Adams wants to come with us.» y con «Don't you want to come with us?»: 200, sin intentos y sin aviso. `/api/voz` sin sesión: 403 con su motivo en 0,3 s (la corrección de verdad pide contraseña; la cubren las pruebas locales y los 7 mutantes de 4e). Vista previa del diccionario 200 (IPA US /ˈhɑɹbɚ/). «amor» con B1 12 de 12 y dostoyevski 4 de 5, como tras el 19. Segunda pasada de `--seco --commit fdbc54e`: iguales 2, nada que subir |
| `384a206` | `app/catalogo.py`, `catalogo_externo.csv`, `no_lectura_externo.csv` | Subido con `--commit ef1138c` tras árbol limpio de 10 suites en D:. f4 `7c9c289`: bloques con un texto raro (`MARGEN_RARO` 0,5: el raro conserva la medida del bloque entero y se marca en `raro_en_bloque`) y el nombre entero del autor delante de los libros sobre él, sin coincidencias parciales. f4 `740eb84`: externo regenerado, 92 bloques con raro, 225 textos cambian de letra (A1 749 -> 766, A2 5.589 -> 5.696, B1 5.543 -> 5.491, B2 2.583 -> 2.524, C1 790 -> 777), los 92 raros revisados a mano (7 a `no_lectura`: APOCALYPTO, cuatro en francés, uno en italiano y uno con copyright en el texto) y 8 anuncios largos de 4e; `no_lectura` 185 -> 200. f4 `ef1138c`: el nombre entero solo con dos palabras o más (con una sola, el apellido de un colaborador, «rosa», pasaba delante de los títulos); lo cazó la batería de `buscador-encontrar` antes de subir | Salud y estado 68.546. «Jane Austen» sin perfil: primero una obra suya y ni Sidney Austen ni Calamity Jane. «rosa» sin perfil: «Roses: a Monograph of the Genus Rosa», «Rosa», «Rosa Mundi». «amor» con B1: 12 de 12, sin «Design and tradition». dostoyevski, chejov y Midsummer (0,95) igual. SWV991 («Why, Oh Why!») pasa de B2 a A2 (0,273). APOCALYPTO ya no sale. **Queda para el 22:** con perfil B1, «Jane Austen» abre con la adaptación teatral de MacKaye (C1, con Austen acreditada como coautora), porque dentro de la ventana de nombre ordena el nivel; y la batería en el Space sigue fallando en cervantes, dante, moliere, agatha christie, «tolstoy» sin perfil y «luna»/«rosa» con B1, igual que antes del 21. Las del API con «y otros» en el autor salen como fallos falsos en la batería (hay que comparar por id). Ningún anuncio de la batería sale ya. Segunda pasada de `--seco --commit ef1138c`: iguales 3, nada que subir |
| `62a5373` | `app/catalogo.py`, `app/api.py`, `no_lectura_externo.csv` | Subido con `--commit 8b259c5` (datos `9dcd867`) tras árbol limpio en D: (api 58/58, corpus 41/41, extremas 349), con el «ok» de 4e (`f79b562`) a catalogo.py y datos y el de e6 a api.py. f4 `8b259c5`: serio de 4e sobre el 21 (54d6591), un apellido suelto solo se apaga si la consulta trae el nombre de pila de OTRO autor con ese apellido, y un seudónimo solo cuenta con dos palabras o más y entero; subidas de la ronda 3 de e6 (borrado entero bajo el candado, abrir fuera del candado, `_escribir_nombres` avisa). Mutantes C8, C9 y C10: 12 de 12 por su prueba. f4 `9dcd867`: no_lectura 200 -> 203 (SWV644124 GHB, SWV644179 metanfetamina de la misma cuenta, SWV119683 SEO; 29 cuentas y 36 textos revisados) | RUNNING `62a5373` en 45 s, salud ok, 68.546 libros. Autor en los 10 primeros sin perfil (Space 21 -> 22): treasure island stevenson 2 -> 8, love poems by browning 0 -> 9, the secret garden frances hodgson burnett 0 -> 8, white fang jack london 0 -> 2, the call of the wild by jack london 4 -> 10; «browning» y «robert browning» abren con Browning con y sin B1; «amor» B1 12 de 12 sin Fenn; «rosa» con Rosa primero; «Buying GHB Online» sin los anuncios. Batería de buscador-encontrar en el Space igual que en local: 11 fallos, los mismos que antes (cervantes, dante, moliere, christie, tolstoy; luna y rosa con B1), al 24. «Jane Austen» con B1 abre con la adaptación de MacKaye (coautora Austen), también al 24. Segunda pasada de `--seco`: nada que subir |
| `d854649` | `app/voz.py`, `app/lexicon.py` | Reinicio 23, solo voz, subido con `--commit 86e6e1d` (4e, restos de voz de la ronda 3 de e6, b152637; ok de e6) tras árbol limpio en D: (voz, api_voz_temporal, voz_ritmo, voz_concurrencia, lexicon y api 58/58, sin claves). La búsqueda por franja pasa al 24 y lo que era 24 al 25 | RUNNING `d854649` en 15 s, salud ok, 68.546 libros, `/api/voz/ritmo` 200 con historial vacío; segunda pasada de `--seco` sin nada que subir. Prueba de pago autorizada con invitado8, **2 usos (20 -> 18, sin reponer)**: «Baker St. It was late.» (voz local de Windows) transcrita exacta y sin enlace st‿it, bien; **2,5 s de silencio FALLA**: whisper devuelve «you», `transcripcion_ok` true, se genera la corrección de pago (6 detalles y audio) y se guardan 6 palabras falladas en el lector de prueba. 86e6e1d solo cubre transcripción vacía o «...»; la alucinación de whisper queda para 0a759a5 de 4e (muletillas con casi silencio) |
| `0c09197` | `app/voz.py` | Reinicio 24, solo el silencio de whisper, subido con `--commit 0a759a5` (4e, muletillas de whisper con casi silencio; ok de e6, 10 de 11 mutantes: la prueba de dos segmentos para `all`->`any` la añade 4e aparte) tras árbol limpio en D: (api_voz_temporal, voz, voz_concurrencia, voz_ritmo, lexicon y api 58/58, sin claves). La búsqueda por franja pasa al 25 y lo demás al 26 | RUNNING `0c09197` en 46 s, salud ok, 68.546 libros, `/api/voz/ritmo` 200; segunda pasada de `--seco` sin nada que subir. La misma prueba de pago del 23 con invitado8, **1 uso (18 -> 17, sin reponer)**: 2,5 s de silencio con «The cat sat on the mat.» dan `transcripcion_ok` false, transcripción vacía, sin resumen ni detalles, ritmo sin medir y nada guardado (falladas y ritmo vacíos). Sigue llegando `audio_correcto` (el mp3 de la frase modelo, mismo hash que en el 23, de caché); sin probar si una frase nueva en silencio pide tts-1 |
| `4ba66f9` | antes `catalogo_tit_ext_936bb14e0e7fda90.npy` (`f50cc1b`, a mano con `subir_npy_externo.py --titulos`); `app/catalogo.py`, `app/api.py` | Reinicio 25, búsqueda por franja, subido con `--commit 9132a59` (f4 `cb39b91` + `9132a59`) tras árbol limpio en D: (api 59/59, ficha, perfil; corpus 42/42 y extremas 349 repetidas solas, la primera pasada se quedó sin RAM con el banco en paralelo), ok de e6 a api.py y de 4e a catalogo.py, banco C11 y C6 17 de 17. Con nivel, `/api/buscar` añade detrás de los n hasta 12 textos de la franja (nivel - 0,45, nivel + 0,45] marcados `por_franja` (suelo 0,60, a 0,15 del mejor de la franja y 0,25 del techo; parecido por tema, título solo de los externos y, con una palabra, contra sus frases: variante E) y devuelve `franja` [lo, hi]. El .npy se comprueba al cargar (forma y 8 títulos). Las palabras enteras en el rescate por título se quitaron por el serio de 4e (erratas) y van al 26 | RUNNING `4ba66f9` en 46 s, salud ok, 68.546 libros; `franja` y `por_franja` en todas las respuestas; «Fantasmas» A2 13 marcados (primera búsqueda 18,6 s: modelo y comprobación del .npy), Robots A2 9 y B1 7, «Terror gótico» B1 sin ACTION PART-1, «familia» C1 4 sin «Familiar», «rosa» B1 sin los dos casos de e6, «ghost stories» sin perfil igual y 0 marcados, «amor» B1 sin Fenn, anuncios de GHB y metanfetamina fuera. Batería (sin perfil, A2 y B1) con los mismos 16 fallos que el Space de antes. Límites declarados: «Monstruos» 1/12, «Historias de amor» con «My story», «Terror gótico» B1 con «The Enemy»; MENOR de 4e: MARGEN_TECHO corta 2 de 1197 con C1. Segunda pasada de `--seco` sin nada que subir |
| `5c6f8d9` | `app/ui.py`, `app/voz.py`, `app/cuentas.py`, `app/api.py` (`app/catalogo.py` igual) | Reinicio 26, subido con `--commit 49a8e4d` tras árbol limpio en D: por tandas (voz, voz_ritmo y voz_concurrencia; api 62/62; extremas 350; corpus 42/42). f4 `41e7e6d`: precarga del buscador en un hilo de fondo desde `para_gradio` (SPACE_ID, o `LITERALEVEL_PRECARGA=1`; `=0` la apaga en pruebas) y `cuentas.devolver_por_silencio` (10 al día por cuenta, bajo el candado del cobro) cableada en `/api/voz` con `uso_devuelto` y `origen="api"`; `/api/estado` con la memoria del proceso. 4e 681544f, 50a6304 y 06a7aac (voz sin voz: sin audio modelo ni análisis, `sin_voz`, registro de no_speech_prob); e6 aab69be, d1a756a, 274db93 y 49a8e4d (Gradio: «No te oí», `origen="gradio"` y la devolución). ok de 4e a cuentas.py y a ui.py, de e6 a api.py. Mutantes C12 5/5 y C13 5/5; C14 3 de 3 con la prueba de extremas de e6 `24279b2` (el primer banco dejó vivo C14-gradio-codigo-despues-de-cobrar por un hueco de la prueba; ui.py no cambia) | RUNNING `5c6f8d9` en 85 s. Precarga en el registro: catálogo 4,6 s, modelo, títulos y primera búsqueda 24,8 s; una búsqueda con nivel lanzada a los 5 s de RUNNING esperó 22,1 s y respondió 200 con 13 marcados; después Robots 0,75 s, familia 0,71 s y amor 0,93 s. `/api/salud` dice catálogo cargado a los 6 s, antes de que acabe el modelo. Memoria del proceso 2.562 MB (no hay medida del Space de antes para compararla; en local la precarga suma lo mismo que la primera búsqueda, +1,2 GB). Pruebas de pago con invitado8 autorizadas por la Central, **usos 17 -> 17**: `/api/voz` con 2,5 s de silencio da `transcripcion_ok` false, sin corrección, `uso_devuelto` true y restantes 17; Gradio con el mismo silencio dice «No te oí» y los usos siguen en 17. Registro: `voz sin_voz: no_speech_prob=[0.943] hora=… origen=api` y `origen=gradio`, sin texto. Segunda pasada de `--seco` sin nada que subir |
| `1708cb1` | `app/catalogo.py`, `app/api.py`, `app/cuentas.py`, `app/ui.py`, `app/ficha.py` | Reinicio 27, subido con `--commit 9e51c18` tras árbol limpio en D: por tandas (api 66/66, corpus 46/46, extremas 351, ficha). f4 `9e51c18`: clásicos por apellido (la compuerta de tema no apaga el apellido exacto del primer autor con al menos 5 obras; riesgo medido con 100 palabras de tema en `auditoria/palabras_de_tema_2026-09-15.txt`, 0 cambian), a igual rescate el autor gana al título (solo el primer autor), «Jane Austen» con nivel ordena primero al primer autor con el nombre entero, `buscador_listo` en /api/salud, `_resumen_curva` sin forma ni extremos con una fila, /api/voz lee el código una vez y los dos menores de `devolver_por_silencio`. e6 `ae4c8d8`, `3151f51` (ficha de un capítulo y regla de MAYÚSCULAS), `4a265f6` (`_puede_pagar(peticion, codigo)`), `5985e8e` y `dd0248e`. ok de 4e a catalogo.py y cuentas.py, de e6 a api.py; 4e a ui.py/ficha.py de e6. Mutantes C15-api, C16 (3), C17, C18 (2), C19 (2), C20 y C13 (2): 12 de 12 | RUNNING `1708cb1` en 26 s; `buscador_listo` false y luego true a los 29,2 s (`catalogo` a los 0,6 s). SWV4008 (Kian): un capítulo, `distintivas` vacía, curva de una fila con `forma`, `facil` y `dificil` a None. Abren con obra suya, sin perfil y con B1: cervantes, dante, moliere, agatha christie y tolstoy (sus obras antes que los libros sobre él); «Jane Austen» con B1 abre con The Watsons, Emma y Love and Freindship. Batería en el Space (sin perfil, A2 y B1): de 16 fallos a 3, los que quedan son «rosa» A2 y B1 («The Water Supply of the El Paso») y «luna» B1 («Luna, The Rajapalayam Puppy»), al 28. Segunda pasada de `--seco` sin nada que subir |
| `74f1484` | `app/catalogo.py` | Reinicio 28, subido con `--commit b896b1f` tras árbol limpio en D: con cada suite sola (corpus 46/46, api 66/66, extremas 351). f4 `b896b1f`: arreglo de la regresión del 27 (SERIO de 4e): palabras corrientes que son apellido o nombre de entidad («london», «hope», «king», «school», «brown», «castle», «snow», «love», «forest»…) traían al autor en vez del tema. Sale entera la regla (b) «a igual rescate el autor gana al título», y la clave del primer autor antes que el nivel solo actúa con dos palabras o más; la exención (a) con N = 5 se queda. Medido contra la línea base del 26 (`catalogo.py` de 49a8e4d, top 10 de las 100 palabras sin perfil y con B1, en `auditoria/top10_palabras_de_tema_26.json`, con «rose» añadida en `5a2fc04`): 0 de 198 listas distintas. ok de 4e. Mutantes C19 (2), C20 y C22-primero-con-una-palabra: 4 de 4 | RUNNING `74f1484` en 46 s; `buscador_listo` a los 20 s. Las 198 listas por /api/buscar iguales al 26 (en el 27 vivo, el mismo guion daba 54 distintas en 28 palabras). cervantes, dante, moliere y agatha christie abren con obra suya sin perfil y con B1; «Jane Austen» con B1, con The Watsons, Emma y Love and Freindship; «tolstoy» sin perfil vuelve a «My Visit to Tolstoy», como en el 26 (aceptado por la Central), y con B1 sus obras van primero. 4e lo repite a ciegas en el Space (anexos `762d987` y `68b7cf3`, «rose» incluida): igual al 26. Batería en el Space: 4 fallos, «tolstoy» sin perfil (aceptado) y los tres que ya iban al 29 («rosa» A2 y B1, «luna» B1). Segunda pasada de `--seco` sin nada que subir |
| `74f1484` (límite) | nada | Límite declarado de la búsqueda por franja, decidido por la Central tras el 28: el título en consultas largas («Historias de amor» marca «My stories»; «Terror gótico») se queda sin cambio de código, porque ninguna variante (G, J, K) gana a lo desplegado en 14 consultas de calibración escritas antes de medir (base 85,4 %, G 84,4 %, J 80,7 %, K 81,2 %). Tablas de calibración y batería en `auditoria/limite_titulo_consultas_largas_2026-09-15.md` | El chip «Historias de amor» del front se queda: cumple el criterio del tema (5 y 7 contados a mano) |
| `74f1484` (límite) | nada | Límite declarado (Central): «rosa» con A2 y B1 («The Water Supply of the El Paso») y «luna» con B1 («Luna, The Rajapalayam Puppy») se quedan sin cambio de código. La causa, medida: con una sola palabra, `_titulo_completo` da lex 1 a todo título que la contenga (134 con «rosa», 25 con «luna»), la compuerta de tema se decide con la mejor fila con nombre («Roses: … Genus Rosa», índice 0,704 frente a un techo de 0,735) y queda abierta para todas, y con nivel la ventana de nombres la ordena el nivel. El arreglo medido, decidir el rescate por palabra del título fila a fila con una palabra (índice de la fila a menos de 0,20 del techo), quitaba El Paso y el perro, pero cambiaba 70 de las 200 listas de las 100 palabras de tema (en 27 el primero) y con «dracul» sin perfil perdía «Dracula» (PG345, PG45839) de los puestos 2 y 3 | Fallos que ya están en el Space, anotados sin tocar: «emma» con B1, «hamlet» sin perfil (abre con «Shakspere and Montaigne») y «ulysses» sin perfil no abren con el libro; «frankenstien» (errata) no abre con Frankenstein, ni sin perfil ni con B1 |
| `5ab6832` | `app/catalogo.py` | Reinicio 29, subido con `--commit 7e2b861` tras árbol limpio en D: con cada suite sola (corpus 47/47, api 66/66, extremas 351). f4 `7e2b861`: paso 3 de la demo (e6, «dostoyevski» con perfil 1,20 marcaba «Books», «Story Chikkappa» o «Tanaji Malusare», que casan por título con «libros sobre dostoyevski»): si el primer resultado es un libro propio (índice por debajo de `_n_propio`) rescatado por su autor, la franja marca los que ya están pero no añade. Medido contra el 28 con n=24: 100 palabras sin perfil y B1, 0 de 198; 20 de control, solo «institute» B1 (aceptado); temas A2/B1 iguales; autores con 1,20 sin cuentos colados. ok de 4e. Mutantes C23 (2): 2 de 2. **Hueco de medida: ninguna consulta de tema con perfil 1,20** | RUNNING `5ab6832` en 56 s; contra el volcado del Space 28 (257 listas, n=24): 0 de 247 distintas donde no se esperaba cambio y 0 de 10 donde sí; «Crimen y castigo de Dostoyevski» 0 marcas con 1,20 y con B1. Batería: los 4 fallos del 28. **Regresión encontrada por e6 con 1,20** y medida después (29 contra 28, n=24): «león» 12 → 0, «brown» 12 → 0, «hope» 9 → 4 y «animales de la granja» 15 → 3 (también A2 16 → 4 y B1 13 → 1): el primer resultado es un libro propio con un autor que casa con la consulta (Cieza de León, Brown, Laura Lee Hope, «United States. Bureau of Animal Industry» con «animales» ≈ «animal» 0,793). Los otros 26 chips y reservas, iguales en A2, B1 y 1,20. Más de 3 temas perdidos: vuelta atrás |
| `62e5a06` | `app/catalogo.py` (el de `b896b1f`) | Vuelta atrás al reinicio 28, regla acordada con la Central (más de 3 temas con marcas perdidas con 1,20). El primer intento lo denegó el clasificador de permisos de la sesión («Production Deploy»); subido después con la autorización de Miguel en el chat de f4. i4 (`7e2b861`) queda en el historial y no en el Space; el siguiente intento (i7, contra el vector del título que casa solo con el marco «historias de»/«libros sobre») se mide en local con A2, B1 y 1,20 | RUNNING `62e5a06` en 72 s; `buscador_listo` a los 55 s (log: «api precarga: catalogo 11.9 s; modelo, titulos (si) y primera busqueda 44.4 s», con MiniLM bajado del Hub en ese arranque). Las 257 listas del volcado del Space 28 (n=24): 257 iguales en ids y marcas. Paso 3: «Crimen y castigo de Dostoyevski» con 1,20, 0 marcas y Crime and Punishment primero. 4e lo repite a ciegas (anexo `b7cd8d7`): 33 listas iguales al 28; «león» 12, «brown» 12, «hope» 9, «animales de la granja» 15/16/13. Segunda pasada de `--seco` sin nada que subir. Queda: «dostoyevski» a secas vuelve a marcar cuentos colados (15 con 1,20) |
| `62e5a06` (límite) | nada | Límite declarado (Central): con perfil, buscar un autor por una sola palabra («dostoyevski», «tolstoy», «cervantes», «oscar wilde») marca en la franja cuentos sin relación (con 1,20 y n=24: 15, 12, 12 y 12). Con una palabra, la franja compara el título de los libres con «historias de X» y «libros sobre X», y MiniLM acerca a esas frases títulos de misterio, bestias o fantasía aunque no tengan que ver con el autor. La búsqueda del guion, «Crimen y castigo de Dostoyevski», da 0 marcas. Probado y descartado, contra el 28 con A2, B1 y 1,20 y n=24: **i4** (decidir «autor» por el primer resultado; subido como 29 y vuelto atrás: «león», «brown», «hope» y «animales de la granja» perdían marcas con 1,20); **i7** (el título solo cuenta si casa mejor con la frase que con el marco sin X; márgenes 0,00/0,05/0,10: calibración de 18 consultas escrita antes de medir, colados 221 → 184/150/119 con los buenos en 161, pero tolstoy, cervantes y wilde siguen en 12 y con 0,05 pierden marcas 14/12/11 palabras y 12/12/6 de control); **i7b** (4e: título solo con índice bajo el suelo, marcar sin añadir: colados 221 → 21 pero buenos 161 → 109, y pierden marcas 82/79/83 de 99 palabras y 23/22/25 de 27 chips, «amor» 12 → 0) | Después de la entrega, sin medir: decidir «autor» por la consulta y no por el primer resultado (apellido de un autor con 5 obras o más). Ojo (Central): «tolstoy» también aparece en títulos («My Visit to Tolstoy»), así que la condición no puede ser «no aparece en títulos» |
| `282c46f` | `README.md` del Space (solo la cabecera) | Reinicio 30a (Central): `preload_from_hub` de `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` con 10 archivos (modules.json, config_sentence_transformers.json, README.md, sentence_bert_config.json, config.json, model.safetensors, tokenizer_config.json, tokenizer.json, special_tokens_map.json, 1_Pooling/config.json), sin commit fijo para que exista refs/main. Motivo: sin almacenamiento persistente (ya no existe en Spaces), cada arranque bajaba MiniLM del Hub sin token (log de 62e5a06). Los 10 son los que el Space bajaba en tiempo de ejecución y bastan sin red: comprobado en local con una caché nueva (HF_HOME en D:, HF_HUB_OFFLINE=1), `_ruta_local` resuelve el snapshot e8f8c21 y encode da (2, 384). El repo entero son 4,6 GB (onnx, openvino, tf, pytorch_model.bin). Variables del Space: solo LITERALEVEL_DATOS y LITERALEVEL_MODELO; en app/ no hay HF_HOME ni TRANSFORMERS_CACHE. Subido con `scratchpad/preload_readme_r30a.py`, que aborta si el cambio toca algo fuera de la cabecera (diff: +2 líneas). ok de 4e. Antes, `3345ba9` revierte i4 (`7e2b861`) en app/catalogo.py, pruebas_corpus.py y tools/banco_mutantes.py, que quedan iguales a `b896b1f`, lo que corre en el Space | **Primera medida:** RUNNING a los 61 s de lanzar la medida; `buscador_listo` a los 20 s de RUNNING (55 s en 62e5a06); log «api precarga: catalogo 5.9 s; modelo, titulos (si) y primera busqueda 17.2 s» (11.9 s y 44.4 s en 62e5a06); 0 descargas de MiniLM y sin el aviso de peticiones sin token en el tramo leído. **Cautela:** el log se leyó por SSE durante 20 s y se cortó por tiempo; llegó a la línea de precarga, pero no garantiza haber leído el arranque entero. **Segunda medida** (arranque del 30b, Space `0319290`, sin reiniciar solo para medir, como pidió la Central): RUNNING a los 51 s de lanzar la medida; `buscador_listo` a los 12 s de RUNNING; log leído entero desde el arranque del contenedor (44 líneas, 15:56:45 → 15:57:45): «api precarga: catalogo 3.8 s; modelo, titulos (si) y primera busqueda 13.7 s» y 0 descargas de MiniLM (ni model.safetensors, ni modules.json, ni tokenizer.json, ni el aviso de peticiones sin token). Con las dos medidas, el modelo sale de la imagen: `buscador_listo` 55 s → 20 s → 12 s |
| `0319290` | `app/catalogo.py` | Reinicio 30b (Central): orden determinista ante parecidos iguales. Subido con `--commit 1643c4b` tras árbol limpio en D: con cada suite sola (corpus 48/48, api 66/66, extremas 351); mutantes C24 (3): 3 de 3; ok de 4e. En los tres ordenamientos, parecido redondeado a 6 decimales y orden estable por fila; en la franja, a igual parecido redondeado, primero la copia más cercana al nivel del lector y después la fila. Medido en local contra el 28 (545 listas, n=24, sin perfil, A2, B1 y 1,20): ningún top 10 cambia de conjunto (único cruce, «mystery» sin perfil 7↔8 a 0,857000); 88 cambios solo en la cola y 18 antes, todos empates a 6 decimales; marcas y longitudes iguales; ids marcados distintos solo en una lista cerrada de 10 («familia» A2, «escuela» B1, «family» A2 y B1, «friendship» 1,20, «Familia» A2 y B1, «Amigos inseparables» A2 y B1, «Brujas y magia» A2), siempre con una copia de mismo título igual de cerca del nivel o más; ruido entre procesos descartado (dos corridas del 28, 218/218). Criterio corregido dos veces antes de ver el resultado: el top 10 se juzga por conjunto (dentro, solo cruces de empatados a 6 decimales), y la referencia de la marcha atrás es el volcado del Space 28, no la medida local | RUNNING `0319290` en 46 s; `buscador_listo` a los 14 s. **Primer código 2 (error de referencia, no se volvió atrás, decisión de la Central):** la regla comparaba con la medida local del 28, que ya difería del Space en 13 listas y justo en «magic» B1 (el Space marca SWV537780, «The Magical World» 0,39, igual que el Space 28; el local SWV522867, 0,73); además, el «257/257» dado como prueba de local = Space era Space 28 contra Space 28, y se informó mal. **Contra el volcado del Space 28 (257 listas, mismo entorno):** 198 iguales; 58 solo orden (53 en la cola con parecidos idénticos; «Crimen y castigo de Dostoyevski» B1 con PG2554 primero y 4 marcas como en el 28; conjunto del top 10 igual en las 59 listas distintas); 0 para volver; 1 código 3 aceptado por la Central como excepción revisada: «pintura» B1 deja SWV494921 («The Magic Paintbrush» 0,99, a 0,19 del nivel) por SWV661856 (misma obra, 0,775, a 0,025), longitud 36 y marcas 17 iguales. Contra la medida local del candidato (545): 541 idénticas, 3 solo orden en la cola, 1 con otra copia («magic» B1). e6 en el front 72e9525 a 390 px con 1,20: paso 3 con aviso y Crime and Punishment primero en «De otros niveles» a 679 px; «animales de la granja» 9 libres; «cuentos de dragones» 19 de 20; «mystery» sin perfil, mismo top 10 con 7↔8. Segunda pasada de `--seco` sin nada que subir. **Límite declarado:** el redondeo a 6 decimales no iguala el Space y el local en todas las parejas; la clave de nivel solo actúa donde hay empate de verdad en cada entorno. Ejemplos: «magic» B1 empata en local y no en el Space, y «mystery» sin perfil cruza también 11↔12 en el Space y no en local. No ordena igual en cualquier máquina |
| `72f3cdc` | `app/api.py`, `app/ui.py`, `app/voz.py` | Dos textos, sin lógica nueva (Central, 16 sep). Subido con `--commit 61e3bba` (encima de `4e95a1f`); comprobado antes con `--seco --commit b7242f4` que el Space tenía esos tres archivos iguales al padre, así que solo subieron los dos commits de f4. **(1)** El aviso del tope por hora dice qué se acabó: `ui._mensaje_limite` recibe el cubo y los 7 puntos de llamada lo pasan; antes los cinco caminos decían «límite de consultas» y a Miguel le saltó en *Pronunciar* el cubo `voz` (10/h) con el nombre del de `lexico` (30/h). Ya no promete que medir un capítulo «no cuesta nada». Genéricos en español e inglés sin cubo; en inglés no se reparte por cubo (a la cola). **(2)** El «igual» de `voz._SIN_COMPARACION` deja de culpar a la transcripción: `fonemas.segmentar` quita la marca de acento, así que un fallo de sílaba tónica cae ahí por definición. Texto: «Lo que no comparamos es en qué sílaba cae el acento». Caso «assessors» cerrado como deducido del código. Pruebas: `pruebas_extremas.py` 519-521 no podía fallar (devolvía una tupla) y ahora asevera; 560 y 2243 pasan su cubo; nuevas del cubo, de «no es gratis» y del «igual». Mutantes T1-tope-sin-cubo y T2-igual-culpa-a-whisper: 2 de 2 por su prueba. Árbol limpio en D: de `61e3bba`, suites de una en una: smoke, api 66/66, extremas 354, integración 27, corpus 48, voz, voz_ritmo, voz_concurrencia, lexicon, despliegue, ficha. Ok de 4e a los dos commits | RUNNING `72f3cdc` en ~40 s; `buscador_listo` a los ~10 s; `/api/estado` 68.546. Los tres archivos de la revisión, descargados del Space, llevan los textos nuevos. Segunda pasada de `--seco --commit 61e3bba`: iguales 3, nada que subir. **No comprobado en vivo:** los dos avisos solo salen con un cubo agotado de una cuenta o con una corrección de pago. **Prueba rota de antes y ajena a este cambio: `pruebas_api_voz_temporal.py`** falla igual en `b7242f4` (`AttributeError`: su `ui` falso no tiene `_codigo_de`, que `_corregir_voz` llama desde el reinicio 27; la línea del 429 tocada aquí ni se evalúa porque `_va_a_costar` es False). **Lleva rota desde el 27 y desapareció de las filas del 28 al 30b sin que nadie lo dijera:** una red que no medía nada, esta vez por ausencia. Se arregla en commit aparte |

### Estado al cierre del 14 de septiembre de 2026

- **Motor (Gradio + API):** `MikeMaki1763/literalevel` en `7c09d90`, RUNNING
  (reinicio 15). Los reinicios 9 a 15 de hoy están en la tabla, de `de36496` a
  `7c09d90`, y cada uno se cerró con una segunda pasada de `--seco` sin nada que
  subir.
- **Front estático:** `MikeMaki1763/literalevel-front` en `45d9999`, RUNNING. Lo
  publica e6. f4 lo probó como persona tras el reinicio 12, pero no después de
  los cambios de e6 de la tarde (plurales, `medido_en_bloque`, portadas).
- **Cupos recargados (14 sep, con permiso explícito de Miguel):**
  `uso_openai.json` del bucket pasó de `{invitado7: 3, invitado8: 20,
  invitado1: 14, invitado3: 3}` a `{}`. Contraseñas y secreto, intactos.
  Comprobado entrando en el Space con cada cuenta: invitado1 a invitado8 con 20
  restantes y profesor con 60; miguel no tiene tope.
- **Borrado en el bucket:** las 12 curvas `analisis/*-rapido.json` de textos
  libres, medidas con la atribución dentro (reinicio 14). Las sinopsis no.

### El catálogo externo con StoryWeaver (14 sep 2026, reinicios 10 y 12)

- **Medición.** `tools/medir_corpus.py` en CPU local, gratis, reanudable en shards de 250 (`corpus_graduado/medidas/`): 12.800 unidades; se cerró con `tools/cerrar_corpus.py`. De 16.251 textos libres (364 obras repetidas entre fuentes, fuera) quedan 15.357 medidos: 11.039 solos y 4.318 en bloques de al menos 250 palabras de su fuente y nivel.
- **Una obra, una fila.** Si la misma obra está en dos bibliotecas, entra una sola vez y StoryWeaver va delante de Let's Read: por eso Let's Read baja de 424 a 326 y African Storybook de 281 a 278.
- **894 fuera, sin medida.** 776 tienen menos de 150 palabras. 878 cayeron en uno de los 260 bloques que el filtro de prosa del v4 rechazó (215 «lista, menú o tabla», 32 por frases, 13 con menos de 4 frases). De los 16 restantes, 15 no llegaron a formar bloque y 1 se midió solo, lo rechazó el filtro y no llegó a bloque. Por fuente: StoryWeaver 828, Let's Read 40, African Storybook 23, VOA 3.
- **Embeddings.** `catalogo_emb_ext_<huella>.npy` cambia de nombre con cada versión del externo y se sube a mano, antes del `--solo` de los CSV. La primera búsqueda tras arrancar tarda unos 21 s mientras carga el modelo.
- **Texto servido limpio, medida intacta (14 sep, para el reinicio 15).** `tools/catalogar_corpus.py` limpia solo el texto que va a `corpus_abierto.parquet`. Quita los U+FEFF, un párrafo idéntico al anterior y un párrafo que es la misma página dos veces (cada mitad con al menos 12 palabras y dos frases). Los estribillos y la repetición no consecutiva se quedan. El texto que se mide no cambia: la clave de `medir_corpus` es su contenido, y `catalogo_externo.csv` sale **idéntico byte a byte**, así que la dificultad, las letras y el `.npy` no cambian. Cambian 1.442 de 15.357 textos servidos: 1.257 solo por U+FEFF o espacios y 185 por párrafos o páginas dobles (SWV138722 pasa de 669 a 628 palabras). La columna `palabras` del CSV sigue contando el texto medido. Las curvas guardadas de esos textos no hacen falta borrarlas: su clave cambia con el texto.
- **Intercalado.** En la recomendación por nivel, si hay textos libres en la franja del lector, ocupan los puestos 2, 5, 8… (un tercio de las tarjetas); el resto sigue por descargas. Sin libres, nada cambia, y un título con aviso de contenido sigue fuera de los 5 primeros. Decisión de Miguel del 14 sep: ordenados por descargas, los cuentos libres salían del puesto 20 en adelante en A2 y ninguno en B1.

**El bucket se lista con retraso.** Lo que la app escribe en `/data` (el montaje del
Storage Bucket) tarda unos segundos en aparecer en `list_bucket_tree`: en el reinicio 8,
listar justo después de las dos sinopsis daba 0 archivos nuevos y, poco después, el
único esperado. Una comprobación que cuente archivos del bucket tiene que esperar o
reintentar antes de dar un fallo.

**La prueba final como persona** (13 sep 2026, front publicado a 390 px táctil) se hizo con un micrófono
falso: `getUserMedia` sustituido por un script inyectado que reproduce un WAV de TTS. Servir el WAV
desde `127.0.0.1` se queda colgado (Chrome pide permiso de «acceso a red local» a una web pública):
hay que meterlo en la página como `data:` URL, subiéndolo a un `<input type=file>` creado para eso.
Y una pestaña abierta durante una publicación del front deja de navegar sin avisar, porque los chunks
del build anterior dan 404 (lo arregló e6 recargando una vez).

`app/animacion_articulatoria.py` llegó en `87f1435`, antes de la base desplegada, y
**nunca se había subido**: un despliegue que solo compara commits no lo habría visto. Se
fuerza con `SUBIR_TAMBIEN`. Las animaciones solo existen en `ui.py`: mientras
`app/api.py` no exponga la URL de cada SVG, el front de Angular no las tiene.

En aquel procedimiento, desde `e793383`, el guion subía **todo lo que difería en `app/` entre el
commit desplegado y el nuevo** (`git diff --name-only`), no solo lo que tocan los commits
que se nombraban. El procedimiento selectivo actual de la cabecera sustituye esa
instrucción: no autoriza incluir automáticamente trabajo de otras sesiones.

Tras `dbd997e` el consejo de fonema salía del texto libre del modelo y cambiaba entre
llamadas con el mismo audio (/dʒ/ y luego /tʃ/ para un error /tr/→/m/). `5029a40` lo
saca de comparar la IPA esperada con la entendida, con CMUdict donde Kaikki no trae IPA.

Archivos de datos nuevos que viajan con el código: `app/pronunciacion_cmu.tsv` (2,9 MB,
texto, sin LFS) está en la lista blanca desde `4a833f7`. **Un guion de despliegue que
compila lo que sube no puede compilar un `.tsv`**, y la vuelta atrás de un archivo nuevo
no es «la versión anterior»: se queda, porque la versión anterior del código no lo lee.

Lo que conviene repetir:

- **Subir lo que hay en el commit, no lo que hay en el disco.** Aquí trabajan varias
  sesiones sobre el mismo árbol, y siempre hay archivos a medias de alguien. Los guiones
  leen cada archivo con `git show <commit>:<ruta>`, y la vuelta atrás usa el commit que
  estaba en el Space.
- **Una subida de audio que da 403 bajo `/gradio_api/file=`** no significa que el archivo
  falte: su carpeta no está en `allowed_paths`. Por eso `ui.RUTAS_PERMITIDAS` incluye
  `articulacion.DIR_AUDIO_RP`.
- **La lista blanca de los mp3 sale de los inventarios** (`fonemas.INVENTARIO` y
  `articulacion.INVENTARIO_RP`), no de un glob: si falta un audio, el despliegue se para.
- **Cada reinicio se avisa antes a las otras sesiones**, y nada se sube mientras Miguel
  está probando: un reinicio de un minuto le cierra lo que tenga abierto.
- La prueba «sin `OPENAI_API_KEY`» no se puede hacer en el Space, que tiene la clave; la
  cubren las pruebas locales (`pruebas_lexicon.py`, `pruebas_extremas.py`).

## Persistencia: ahora importa más que antes

`~/.literalevel/` es disco **efímero** en un Space y se borra en cada reinicio.
Cuando ahí solo había cachés (léxico, audio) daba igual: se rehacen solas y lo
único que se pierde es velocidad. Ya no da igual. Ahí viven también:

| Archivo | Qué se pierde si desaparece |
|---|---|
| `biblioteca.json` | **Mis libros**: los libros empezados y por dónde iba cada uno |
| `cuaderno.db` | **Mis palabras**: todo el vocabulario consultado |
| `analisis/` | las curvas de dificultad ya calculadas (86 s por libro largo) |
| `perfil.json` | el nivel del lector, y habría que rehacer el cuestionario |

Un Space que se duerme y despierta con la estantería vacía deja en ridículo la
pestaña *Mis libros*.

> **HECHO el 10 de septiembre de 2026 por la noche (accionable A4 cerrado).**
> Hay un **Storage Bucket privado**, `MikeMaki1763/literalevel-datos`, montado
> en `/data` del Space, y la variable `LITERALEVEL_DATOS=/data` apuntando la app
> ahí. Verificado de punta a punta: se fijó un perfil, se **reinició el Space** y
> el `perfil.json` seguía en el bucket.
>
> Lo que hubo que arreglar en el código: este documento prometía que «no hace
> falta tocar código, solo la ruta base», y era verdad **a medias**. Los cuatro
> archivos que importan ya colgaban de `LITERALEVEL_DATOS`, pero la carpeta de
> audio que Gradio sirve, los libros descargados, `voz.db` y las **dos cachés
> que evitan volver a pagar a OpenAI** —`lexicon.db` y el audio de tts-1—
> estaban clavadas a `~/.literalevel`. Ahora las nueve rutas de escritura salen
> de `config.dir_datos()`, y una prueba lo exige.
>
> **Y SQLite sobre el montaje funciona**, que era el riesgo de verdad: un bucket
> se monta por NFS/FUSE y SQLite en modo WAL no vale ahí. Este proyecto no usa
> WAL —no toca ningún `PRAGMA`, así que va en `journal_mode=DELETE`, que sí
> funciona—. Comprobado en el Space: una consulta léxica escribió `cuaderno.db`
> (16 KB) y `lexicon.db` (20 KB) en el bucket sin un solo error. Si alguna vez
> saliera un «database is locked» con varios visitantes a la vez, `_consultar`
> lo atrapa y devuelve el uso del cupo: degrada, no revienta.
>
> **Coste:** 18 USD/TB al mes en repositorio privado (12 si fuera público), y
> hay franja gratuita. Con 20 KB dentro, no suma nada a la factura; privado y no
> público porque ahí viven el cuaderno de vocabulario, el perfil y la estantería
> de cada lector.

La buena noticia es el precio: los Storage Buckets del Hub cuestan **12 $/TB al
mes** en repositorio público y 18 $/TB en privado. Esto ocupa unos cientos de
megas —en local, `~/.literalevel/` entero son **10,9 MB** medidos el 10 de
septiembre de 2026—, así que la
factura de almacenamiento es despreciable. Se monta el bucket y se apunta la
app ahí; no hace falta tocar código, solo la ruta base.
