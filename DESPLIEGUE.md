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
