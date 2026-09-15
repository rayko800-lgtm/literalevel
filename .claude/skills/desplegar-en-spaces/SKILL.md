---
name: desplegar-en-spaces
description: Publicar un modelo y una aplicación de Gradio en Hugging Face desde esta máquina — qué cuesta dinero y qué no, cómo se sube sin perder la clave de OpenAI, y las trampas que ya nos costaron tiempo. Úsala al desplegar LiteraLevel o cualquier app de Gradio, al publicar pesos de un modelo, o al tocar secretos y variables de un Space.
---

# Desplegar en Hugging Face

Todo lo de aquí está **hecho y verificado** el 8 de septiembre de 2026 con la
cuenta `MikeMaki1763`.

---

## 1. El token

Va en `C:\Users\laura\.hf_token`, **fuera del repositorio**. Tiene que ser de
tipo **Write**: uno de lectura no sube nada y hay que rehacerlo.

Para pedírselo a Miguel: créale el archivo con la herramienta de escritura y
ábreselo con `code C:\Users\laura\.hf_token`. Pega y guarda, sin pasar por el
chat — un token con permiso de escritura no debe quedar escrito en el
historial de la conversación.

**Si está por AnyDesk desde el móvil no puede pulsar Ctrl+S.** Actívale el
guardado automático de VS Code (`files.autoSave: afterDelay`) o dile que use
Archivo → Guardar con el ratón.

Comprobar sin imprimirlo nunca:

```python
urllib.request.Request("https://huggingface.co/api/whoami-v2",
                       headers={"Authorization": "Bearer " + tok})
# devuelve name, y auth.accessToken.role -> tiene que decir "write"
```

---

## 2. Qué cuesta dinero

- **Repositorios de modelos: gratis.** Publicar los pesos no cuesta nada.
- **Spaces de Gradio sobre CPU: requieren PRO**, 9 USD/mes en cuentas
  personales. Hay una excepción —hasta 2 Spaces de Gradio sobre ZeroGPU en
  cuentas gratuitas— pero exige **cuenta con más de 30 días**, así que no sirve
  para una cuenta recién creada.
- CPU Basic da **2 vCPU y 16 GB**, de sobra para una app que mide 1,05 GB.

### `cpu-basic` NO significa gratis

Es la confusión que costó publicar una cifra falsa en un entregable. La API
devuelve el hardware, no la factura:

```
runtime.hardware.current = "cpu-basic"     # no cobra por hardware
```

y de ahí es tentador concluir «el despliegue es gratuito». **Falso**: el Space
de Gradio existe porque la cuenta es Pro, y la cuenta Pro se paga. `cpu-basic`
solo quiere decir que ese hardware no añade coste **sobre** la suscripción.

Para saber si una cuenta paga, pregúntaselo al Hub:

```python
p = urllib.request.Request('https://huggingface.co/api/whoami-v2',
                           headers={'Authorization': 'Bearer ' + tk})
d = json.load(urllib.request.urlopen(p))
d['isPro']       # True
d['periodEnd']   # epoch de la renovación
```

**En este proyecto:** `MikeMaki1763` es Pro, renueva el 01/10/2026, y Miguel
paga **7 USD/mes** — la tarifa es 9 y le aplicaron descuento. Cuando cites el
coste en un documento, es 7, no 9 y no cero.

---

## 3. Publicar un modelo

```python
api.create_repo(REPO, repo_type="model", private=False, exist_ok=True)
api.upload_folder(folder_path="modelo_v4", repo_id=REPO, repo_type="model")
```

**Verifica siempre la descarga anónima después**, que es lo que hará quien lo
use:

```python
AutoModelForSequenceClassification.from_pretrained(REPO, cache_dir=tmp, token=False)
```

Escribe una ficha de modelo de verdad: las escalas, el troceado, las métricas
con su *n* y **los límites sin adornos**. Va con el nombre del autor.

---

## 4. Publicar la app

Estructura del Space: `app.py` en la raíz (es lo que busca Hugging Face), el
paquete `app/` al lado, y los datos que la app espera en la raíz del
repositorio, porque `RAIZ = Path(__file__).parent.parent` resuelve ahí.

El `app.py` solo debe **arrancar** lo que ya existe. Nada de una versión «de la
nube» que se desincronice de la de casa.

**Trampas que ya nos mordieron:**

- `short_description` del README **no puede pasar de 60 caracteres**, o
  `upload_folder` falla con un 400 de `validate-yaml` que no dice dónde.
- **El modelo de spaCy no se instala solo.** Hay que ponerlo en
  `requirements.txt` por URL:
  `en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`
- Los pesos no se suben al Space: se ponen como **variable**
  (`add_space_variable`) apuntando al repositorio del modelo, y se bajan al
  arrancar.
- Los archivos grandes (un `.db` de 233 MB) sí van en el Space; `upload_folder`
  los pasa por LFS solo.

---

## 4 bis. Subir cambios a un Space que ya existe

`python tools/desplegar_app.py` (`--seco` para ver qué haría, `--estado` para
mirar cómo va). Lo que hace, y por qué cada pieza:

**Lista blanca explícita, nunca `upload_folder` sobre la raíz.**
`huggingface_hub.upload_folder` **no lee `.gitignore`**. Apuntado a este
repositorio subiría `CLAVES.txt` y `.env` —con la clave de OpenAI dentro— a un
Space **público**. El guion enumera los archivos uno a uno y además revisa cada
uno buscando algo con forma de credencial antes de subirlo.

**Comparar por hash y subir solo lo distinto, en un commit.** El sha1 de blob de
git se calcula en local (`sha1("blob <n>\0" + contenido)`) y se compara con el
`blob_id` que devuelve `list_repo_tree(..., expand=True)`. Así el commit dice de
verdad qué cambió, y se ve de un vistazo si el Space está al día.

### Cómo se despliega desde el 13 sep 2026 (reinicios 6 a 15)

- **Se sube el contenido del COMMIT, no el del disco**, con el texto en LF
  (`--commit REF`, por defecto HEAD). Con `core.autocrlf=true` el disco tiene
  CRLF y el repo LF; comparando el disco, `--seco` daba archivos «distintos» que
  no lo eran. Si el remoto tiene fin de línea mezclado, se descarga y se compara
  normalizado; la etiqueta dice «solo fin de línea: pasa a LF».
- **`--solo a b c`** siempre. Guardas que no se saltan: cada archivo elegido
  tiene que estar versionado y **sin cambios en el disco** (si otra sesión dejó
  `api.py` sucio, no sube: pídele que lo limpie o que haga commit);
  `parent_commit` con la revisión remota leída, para que dos subidas no se pisen;
  y escaneo de credenciales sobre los bytes que se envían.
- **Pruebas en árbol limpio** antes de subir: `git archive <commit> app tools
  pruebas_*.py ...`, enlaces duros a los datos grandes y `LITERALEVEL_MODELO`
  apuntando a `modelo_v4`. Y comprobar que `app/` en HEAD es igual al commit
  probado: otras sesiones hacen commits entre medias.
- **El protocolo de cada reinicio:** aviso a Central antes, con el hash del
  Space y lo que sube; `--solo`; un guion `comprobar_reinicioN.py` que espera
  `RUNNING` en una revisión **distinta** de la anterior, comprueba `/api/salud`
  y Gradio y luego lo concreto del cambio; segunda pasada de `--seco` («nada que
  subir»); fila en `DESPLIEGUE.md` y hash a Central. Cuando el cambio es de
  datos, guarda **antes** de subir la foto de lo que no debe cambiar (letra,
  dificultad, estado) y compárala después.
- **Una comprobación que falla puede ser del guion.** En el 12 y en el 13 las
  dos «fallas» fueron expectativas mías: una frase citada de memoria y un 404
  que el servidor da como 400 con `%00`. Míralo antes de tocar código.
- **El `.npy` de embeddings del externo** cambia de nombre con cada versión: se
  sube a mano con `upload_file` **antes** del `--solo` de los CSV. Su nombre
  sale de la huella de las filas; el de Gutenberg no se toca.
- **Un commit ajeno puede llevarse líneas tuyas sin commit.** El `0e270f9` de e6
  subió `api.py` y `ui.py` enteros con cinco llamadas mías a `ficha.para_medir`,
  y la función seguía sin commit: `HEAD` rompía al medir. Nada se desplegó.
  Con varias sesiones en el mismo árbol, haz commit pronto de lo que otros
  archivos ya llaman, y antes de desplegar mira `git log` de cada archivo.

### El bucket de datos (`MikeMaki1763/literalevel-datos`, montado en `/data`)

- **El listado llega con unos segundos de retraso** tras escribir: una
  comprobación que cuenta archivos justo después da de menos. Espera unos 8 s y
  vuelve a listar antes de concluir nada.
- `HfApi.list_bucket_tree`, `download_bucket_files` y
  `batch_bucket_files(add=…, delete=…)`. Antes de borrar, descarga y mira el
  contenido; los nombres de `analisis/` son huellas y no dicen de qué libro son.
- **Cupos de las cuentas:** el tope va en el secreto `LITERALEVEL_CUENTAS`
  (`usuario:contrasena:tope`), pero **lo gastado vive en `uso_openai.json`**
  del bucket (`{"invitado8": 20, ...}`). Recargar un cupo es dejar esos
  contadores a cero, **sin tocar contraseñas ni secreto**
  (`tools/rotar_cuentas.py` es para rotar contraseñas, no para esto). Relee el
  archivo justo antes de escribir, vuelve a leerlo después y entra en el Space
  con cada cuenta: `/api/entrar` devuelve `restantes`. Las contraseñas se leen
  del archivo local y no se imprimen. No hace falta reiniciar: la app lee el
  archivo en cada consulta.
- **Escribir en el bucket necesita permiso explícito de Miguel en la sesión.**
  El clasificador de modo automático lo deniega como «recurso compartido». No se
  rodea ni se le pide a otra sesión: se para, se explica y se espera el «te
  autorizo».
- Los topes por IP y hora (40 medidas, 6 curvas, 4 curvas vivas) son de la
  instancia: una comprobación que pide 7 curvas agota las de esa hora para tu IP.

**Lo que NO se toca, y hay que saberlo antes de estropearlo:**

- **`README.md`**: el del Space no es el del repositorio. Lleva el front matter
  con `sdk_version` y `app_file`. Sobrescribirlo rompe el arranque.
- **`app.py`**: es el punto de entrada del Space y no existe en local (aquí es
  `main.py`).
- **`kaikki_diccionario.db`, `catalogo_emb_*.npy`, `.gitattributes`**: 243 MB de
  datos y la configuración de LFS, ya colocados.

**Que el Space esté al día no es opcional.** Aquí estuvo cinco módulos por
detrás del árbol local durante dos días, con la cola de Gradio atendiendo a
**una** persona a la vez y sin plazos en las llamadas a OpenAI. Todo eso estaba
arreglado en casa. Cuando termines una ronda de correcciones, la ronda no está
terminada hasta que está subida.

### Comprueba lo que el `requirements.txt` no declara

Se encontró subiendo: `catalogo.py` y `lexicon.py` llaman a
`huggingface_hub.snapshot_download`, y `huggingface_hub` **no estaba en
`requirements.txt`**. Funcionaba de rebote, porque `transformers` lo arrastra.
Un día que `transformers` deje de depender de él, «clona y ejecuta» se rompe.

```bash
grep -rhn "^import \|^from \|    import " app/ | sort -u    # y compara
```

Y pon **techo de versión mayor** a todo. En este proyecto `transformers` pasó de
4 a 5 y `gradio` de 5 a 6 mientras se escribía, y las dos veces cambió la API.
`gradio` va fijado exacto: es la única versión con la que se probó, y el
`sdk_version` del README del Space tiene que decir la misma.

---

## 5. Secretos y variables

```python
api.add_space_variable(REPO, "LITERALEVEL_MODELO", "usuario/modelo")   # publico
api.add_space_secret(REPO, "OPENAI_API_KEY", clave)                    # secreto
```

**Antes de poner una clave de pago en un Space público, para y piensa.**
Cualquiera que abra el enlace gasta el saldo del dueño. La solución que
funcionó aquí no fue cerrar la app con `auth=` —eso mata lo que la hace útil de
enseñar— sino **códigos de acceso que se canjean dentro** (`app/cuentas.py`):
la app entera libre, y con llave solo lo que llama a la API.

---

## 6. Comprobar que arrancó

```python
api.get_space_runtime(REPO).stage   # BUILDING -> APP_STARTING -> RUNNING
```

`RUNNING` y un 200 en `https://<usuario>-<space>.hf.space` no bastan: la página
puede servirse y la app estar rota. Ábrela de verdad antes de dar el enlace.

---

## 7. Por qué esto es mejor que el túnel

El enlace de `gradio.live` **muere al reiniciar el proceso**, y cada reinicio da
una dirección nueva — en esta máquina llegaron a acumularse catorce túneles
vivos de intentos sucesivos. La dirección del Space **no cambia nunca**, aunque
se siga desarrollando: cada subida reconstruye en un par de minutos sobre la
misma URL, con historial y vuelta atrás.

## El front estático: la meta de la API y la primera carga (14 sep 2026)

`tools/desplegar_front.py` (lo escribió Codex la noche del 13) publicó una vez
el front **sin la dirección de la API**: el build de Angular minifica la
etiqueta a `<meta name="literalevel-api" content>` y el parser recibía `None`,
así que el front pedía `/api/...` a su propio dominio y todo daba 404. La app
publicada estuvo rota unos minutos. Se arregló en `f6a7942` con una prueba
sobre el HTML minificado. Dos reglas:

- Después de publicar el estático, **abrir la app publicada a 390 px y ver que
  `/api/salud` responde desde el dominio del Space de Gradio**, no el propio.
  Un 200 del `index.html` no dice nada.
- La primera carga puede decir «No consigo hablar con el motor» si el Space de
  Gradio se está despertando: recargar una vez antes de dar el fallo por bueno.


## Un modelo del Hub se baja en cada arranque si no se precarga (15 sep)

El Space de LiteraLevel es `cpu-basic` y **no tiene almacenamiento
persistente** (ya no existe en Spaces). El buscador carga MiniLM
(`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) con
`snapshot_download` y, si no está en la caché local, lo baja del Hub en el
primer uso: 471 MB, sin token. Resultado: el tiempo hasta `buscador_listo` iba
de 20 a 55 s según cómo respondiera el Hub, y un Hub lento justo tras un
reinicio podía dejar el buscador sin cargar.

Arreglo (reinicio 30a, Space 282c46f): `preload_from_hub` en la cabecera YAML
del README **del Space** (no el del repo), solo con los archivos que la app
baja de verdad, no el repositorio entero (4,6 GB con onnx, openvino, tf…):

```yaml
preload_from_hub:
  - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 <archivos separados por comas>
```

- HF lo baja **al construir la imagen** a `~/.cache/huggingface/hub`, la caché
  por defecto: comprueba antes que el Space no tenga `HF_HOME` ni
  `TRANSFORMERS_CACHE` apuntando a otra ruta.
- Sin revisión fija, para que exista `refs/main` y `local_files_only=True` lo
  resuelva.
- Edita solo la cabecera con un guion que aborte si el diff toca algo fuera de
  ella: el README del Space no es el del repositorio y sobrescribirlo rompe el
  arranque.
- Medido: la precarga del arranque bajó de 44,4 s a 17,2 s y `buscador_listo`
  de 55 s a 20 s; el log ya no muestra descargas.
- No reinicies el Space solo para repetir una medida si hay usuarios probando:
  mídelo en el siguiente despliegue, que reinicia igualmente.
