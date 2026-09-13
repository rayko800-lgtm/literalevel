# Desplegar LiteraLevel (punto 6)

**Ya está desplegado**: `MikeMaki1763/literalevel` en Hugging Face Spaces,
público y en marcha, sobre hardware `cpu-basic` y una cuenta Pro de 7 USD/mes.
Arranque medido tras reiniciar: **31 s** hasta que el runtime dice `RUNNING`
y **32 s** hasta que la página responde (`medir_arranque.py`).

Lo que sigue es el procedimiento con el que se hizo y lo que haría falta para
repetirlo en otra plataforma. Lo que **no** está resuelto es el almacenamiento
persistente: el Space arranca con la estantería vacía tras cada reinicio.

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

