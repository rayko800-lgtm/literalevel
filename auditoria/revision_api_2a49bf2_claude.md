# Revisión de `app/api.py` en 2a49bf2 (Claude, entrega-4e)

Revisión a ciegas y en solo lectura, pedida por la central (13 sep 2026, 19:10)
mientras Codex no está. No se ha tocado `api.py`.

Leído entero `app/api.py` de 2a49bf2 (1.690 líneas), sacado con
`git show 2a49bf2:app/api.py` para no revisar el árbol de trabajo, que sigue
cambiando. Cada hallazgo se ha contrastado con el código del mismo commit:

- `ui.py`: `_ip`, los cubos por hora, `_entrar`, `_dir_lector`, `_cap`,
  `_clave_libro`, `RUTA_ANALISIS`, `_analisis_guardado` y `_sinopsis_guardada`;
- `cuentas.py`, entero;
- `reader.py`, `biblioteca.py`, `cuaderno.py`, `ficha.sinopsis` y
  `voz.registrar_fallos`.

También se contrastó con Starlette 1.6.0 y python-multipart 0.0.32, las
versiones instaladas en esta máquina.

Los números de línea son de 2a49bf2. Quién es dueño de cada arreglo va al final
de cada hallazgo: `api.py` es de e6, `ui.py` es de Claude Code, y `reader.py`
lo audita Codex.

**No reproducido** quiere decir razonado desde el código y sin ejecutar el
ataque. Se dice en cada caso.

---

## Hallazgos

### 1. ALTO. Los topes por hora y el freno de contraseñas dependen de una cabecera que escribe el cliente

- **Dónde:** `app/ui.py:436-448` (2a49bf2). Lo usan `api.py:243` (descargas),
  `1038` (sinopsis), `1204` (léxico), `1487` (voz) y `589` (`/api/entrar` →
  `ui._entrar`, que lo usa en `ui.py:560` y `577`).
- **Cita:**
  ```python
  reenviada = cabeceras.get("x-forwarded-for")
  ...
  if reenviada:
      return str(reenviada).split(",")[0].strip()[:64]
  ```
- **Por qué:**
  - El *primer* valor de `X-Forwarded-For` es el que manda el cliente cuando
    el proxy añade la IP real al final en vez de sustituir la cabecera.
  - Cambiando esa cabecera en cada petición, cada intento cuenta como una IP
    nueva, y eso anula dos frenos:
    - **Contraseñas.** Los 15 intentos fallidos por hora de `/api/entrar`
      desaparecen. Las contraseñas son de dos palabras y tres cifras
      (`tools/rotar_cuentas.py`), así que sin freno un diccionario es viable.
      El freno no tiene contador por cuenta, solo por IP.
    - **Cubos por hora.** Tampoco frenan los de léxico, voz, sinopsis y
      descargas. El dinero lo sigue limitando el tope de cada cuenta, pero una
      cuenta sin tope (`tope 0`) solo tiene este freno.
- **No verificado:** si el proxy de Hugging Face sobrescribe o encadena
  `X-Forwarded-For`. No se ha probado contra el Space.
- **Arreglo:**
  - Tomar la IP del último salto de confianza, no la del primero: el elemento
    `-N` de la lista, con `N` saltos de proxy configurable, o
    `request.client.host` si no hay proxy.
  - Añadir un freno de intentos fallidos **por usuario**, independiente de la
    IP.
- **Dueño:** Claude Code (`ui.py`). Afecta igual a Gradio.

### 2. ALTO. El tope de 20 MB no evita una bomba de descompresión en un EPUB

- **Dónde:** `app/api.py:784-816` (`POST /api/libros`) y `app/reader.py:134-178`.
- **Cita** (`api.py:798-800`):
  ```python
  # Un epub es un zip: sin tope cabe una bomba de descompresion.
  if total > _TOPE_SUBIDA:
      raise _no(413, "El archivo pasa de 20 MB.")
  ```
  Y en `reader.py:178`: `bruto = z.read(n).decode("utf-8", "replace")`. No se
  mira `ZipInfo.file_size` en ningún sitio.
- **Por qué:**
  - El tope mide el archivo **comprimido**. Un zip de 20 MB con datos
    repetidos se descomprime a varios GB, y `z.read(n)` lo carga entero en
    memoria.
  - Basta con tener `X-Lector`, sin cuenta y sin pagar, para que el proceso del
    Space se quede sin memoria y se caiga para todos.
  - El comentario de `api.py` afirma una protección que no existe.
- **No reproducido:** no se ha construido la bomba.
- **Arreglo:**
  - En `reader._cargar_epub`, antes de leer: sumar `file_size` de las entradas
    y rechazar si pasa de un tope (por ejemplo 200 MB) o si la razón con
    `compress_size` es desmedida.
  - Leer con `z.open(n).read(tope + 1)`.
  - Revisar lo mismo en PDF (pypdf).
  - Corregir el comentario de `api.py`.
- **Dueño:** Codex (`reader.py`) y e6 (el comentario).

### 3. SERIO. Las subidas no tienen tope de tamaño antes de llegar a disco ni tope por lector

- **Dónde:**
  - `app/api.py:785-810` (`/api/libros`) y `1471-1486` (`/api/voz`);
  - Starlette 1.6.0, `MultiPartParser`, línea 38 del método.
- **Cita** (Starlette):
  ```python
  if self._current_part.file is None:
      if len(self._current_part.data) + len(message_bytes) > self.max_part_size:
  ```
  `max_part_size` solo se aplica a los campos que **no** son archivos. Los
  archivos van a un `SpooledTemporaryFile` (1 MB en memoria y el resto a disco)
  sin límite.
- **Por qué:**
  - Cuando `subir_libro` lee los primeros trozos y responde 413, el cuerpo
    entero ya está escrito en el temporal. Una petición de varios GB llena el
    disco del contenedor antes de que nadie la rechace. Con `/api/voz` pasa lo
    mismo: el `audio.read(_TOPE_AUDIO + 1)` llega tarde.
  - No hay tope de número de libros por lector ni cubo por hora. Cada archivo
    distinto de hasta 20 MB se guarda en `lectores/<id>/subidos`, y el
    `X-Lector` se puede cambiar libremente.
- **No verificado:** si el proxy de Hugging Face corta cuerpos grandes.
- **Arreglo:**
  - Un middleware que rechace por `Content-Length` (y cuente bytes si falta)
    antes del parser en `/api/libros` y `/api/voz`.
  - Un tope de libros y de MB por lector.
  - Un cubo por hora para subir.
- **Dueño:** e6 (`api.py`).

### 4. SERIO. Un libro subido puede escribir la curva y la sinopsis que ven todos los lectores de un libro del catálogo

- **Dónde:**
  - `app/ui.py:2083-2093` (`_clave_libro`) y `ui.py:2080` (`RUTA_ANALISIS`);
  - `app/api.py:989-1011` (curva) y `1030-1069` (sinopsis), que aceptan ids
    `u…` de libros subidos;
  - `app/reader.py:144-146` y `233` (de dónde sale el título).
- **Cita** (`ui.py:2089-2092`):
  ```python
  h = hashlib.sha256(
      f"v3-sin-portadilla\x1f{libro.titulo}\x1f{libro.palabras}".encode("utf-8"))
  for c in libro.capitulos[:40]:
      h.update(f"{c.titulo}\x1f{c.palabras}".encode("utf-8"))
  ```
- **Por qué:**
  - La clave no incluye el texto, solo el título, las palabras y los títulos y
    recuentos de capítulo.
  - Todo eso lo controla quien sube el archivo: el título sale del
    `dc:title` del EPUB o de la cabecera del `.txt`.
  - `RUTA_ANALISIS` es **común** a todos los lectores.
  - Un archivo con el mismo título y los mismos recuentos por capítulo que un
    libro del catálogo, pero con otro texto, guarda:
    - su curva (`POST …/curva`, gratis);
    - su sinopsis (`POST …/sinopsis`, un uso).

    Las dos quedan bajo la clave del libro auténtico. `ya_medido`
    (`api.py:994-996`) impide volver a medirlo, y la sinopsis guardada se sirve
    a todos (`api.py:1035-1037`).
- **No reproducido.** Necesita conocer los recuentos del libro, que son
  públicos.
- **Arreglo:**
  - Meter un hash del texto de los capítulos en `_clave_libro`. Invalida los
    análisis guardados: hay que subir la versión de la clave.
  - O no escribir análisis ni sinopsis compartidos para libros `u…`, sino
    guardarlos en la carpeta del lector.
- **Dueño:** Claude Code (`ui._clave_libro`) o e6 (que `api.py` no comparta
  los de `u…`).

### 5. MEDIO. `/api/palabra` devuelve un uso que no se cobró

- **Dónde:** `app/api.py:1207-1217`.
- **Cita:**
  ```python
  with _CANDADO_LEXICO:
      try:
          if config.falta():
              puede, motivo = False, ""
          else:
              puede, motivo = ui._puede_pagar(pet)
          r = ui.consultor().consultar(...)
      except Exception as e:
          cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
          raise _no(503, ...) from e
  ```
- **Por qué:**
  - `devolver` se llama con cualquier excepción, también cuando no se cobró
    nada:
    - sin clave de OpenAI;
    - o con el cupo ya agotado, porque `consumir` ya deshizo su incremento
      (`cuentas.py:326-333`).
  - `devolver` (`cuentas.py:274-293`) resta un uso a cualquier cuenta válida
    con tope.
  - Una cuenta agotada recupera un uso cada vez que `consultar` lanza.
- **Qué hace falta para aprovecharlo:** que `consultar` falle, por ejemplo con
  el diccionario no disponible. Explotarlo es difícil, pero la contabilidad
  queda mal.
- **Arreglo:** `puede = False` antes del `try`, y en el `except` devolver solo
  `if puede`.
- **Dueño:** e6.

### 6. MEDIO. El trabajo con el modelo no tiene tope por lector y un solo cliente lo bloquea para todos

- **Dónde:**
  - `app/api.py:685-704` (`/api/perfil/muestra`, hasta 25.000 caracteres);
  - `847-859` (`…/medir`, un capítulo entero);
  - `989-1011` (`POST …/curva`);
  - `675` (`_CANDADO_MODELO`) y `896` (`_UNA_CURVA_A_LA_VEZ`).
- **Cita:**
  ```python
  threading.Thread(target=_medir_libro, args=(trabajo, lib, datos.modo),
                   daemon=True).start()
  ```
- **Por qué:**
  - Ninguna de estas rutas consume un cubo por hora, y todas se serializan en
    `_CANDADO_MODELO`. Un cliente que encadena peticiones de muestra o de
    capítulo deja el modelo ocupado para los demás lectores.
  - Cada `POST …/curva` de un par (libro, modo) nuevo arranca un hilo que
    espera al semáforo, sin tope de cola. Cada hilo retiene el `Libro` en
    memoria.
  - Con el hallazgo 3 (subidas sin tope), cada archivo subido abre un hilo más.
  - Además `_TRABAJOS` (`1007-1008`) desaloja el más antiguo aunque siga
    `en_curso`. Entonces `curva` ya no lo encuentra y un segundo POST lanza la
    misma medición otra vez.
- **Arreglo:**
  - Un cubo por hora (por IP corregida y por `X-Lector`) en muestra, medir y
    curva.
  - Un 429 cuando haya más de N trabajos esperando.
  - No desalojar trabajos `en_cola` o `en_curso`.
- **Dueño:** e6.

### 7. BAJO. Tres rutas acaban en un 500 genérico donde las demás dan un mensaje

- **Dónde y cita:**
  - `app/api.py:757`: `cat = ui.catalogo()` sin `try`. `/api/buscar`
    (`742-745`) sí lo envuelve y da 503.
  - `app/api.py:722`: `p.guardar(ui._archivo_lector("perfil.json", pet))` sin
    `try`. `/api/perfil/muestra` (`700-703`) sí da «No he podido guardar tu
    nivel».
  - `app/api.py:806-810`: `carpeta.mkdir(...)` y `destino.write_bytes(...)`
    sin `try`. Un disco lleno (hallazgo 3) sale como «Algo ha fallado».
- **Por qué:** no filtran nada, porque el manejador global (`100-107`) no
  enseña la traza. Pero el lector recibe un mensaje peor que en las rutas
  hermanas.
- **Arreglo:** los mismos `try` con 503 o 500 y mensaje, como en las rutas de
  al lado.
- **Dueño:** e6.

### 8. BAJO. Detalles menores

- **`/api/audio/{nombre}`** (`api.py:1279-1285`) acepta `.wav` y `.ogg` pero
  responde siempre `audio/mpeg`, sin `X-Content-Type-Options: nosniff`. Hoy
  solo se generan mp3, así que no tiene efecto.
- **`ui._RONDA_FRASE`** (`api.py:886-888`) crece con cada (título, capítulo)
  pedido y no se poda nunca. Es memoria menor.
- **Arreglo:** el tipo según la extensión, `nosniff`, y podar el diccionario
  como hace `_gasto`.
- **Dueño:** e6 (la primera) y Claude Code (la segunda).

---

## Comprobado y correcto

**Identidad y datos de otros lectores**
- `X-Lector` es obligatorio (400) en todas las rutas que leen o escriben datos
  del lector. `LectorOpcional` solo aparece en `/api/buscar`, que lee el perfil
  si hay id, y en `/api/perfil/cuestionario`, que exige id para guardar
  (`666-667`).
- El id se sanea con el mismo `ui._SESION_SEGURA` que usa `_dir_lector`, con un
  mínimo de 16 caracteres (`153-159`, `ui.py:377`).
- **Los libros subidos solo se resuelven dentro de `lectores/<id>/subidos` del
  propio lector:** `_ruta_libro` en `229-235`, e `_id_de_ruta` en `268-270`,
  que comprueba que la carpeta padre es la suya. La caché `_LIBROS` va por ruta
  completa, que es propia de cada lector.
- CORS sin credenciales, con la identidad en una cabecera y no en una cookie:
  otro origen `*.hf.space` no puede leer el `X-Lector` de nadie.
- La sesión de pago va por `X-Lector` (`ui._sesion_de`). Está documentado que
  no es autenticación: quien copie el id de otro hereda su sesión. No es un
  hallazgo nuevo.

**Puerta de pago**
- Las tres rutas que llaman a OpenAI cobran con `ui._puede_pagar`, que es
  `cuentas.consumir`, atómico, antes de la llamada:
  - `/api/palabra` en la etapa completa (`1203-1223`);
  - `/api/libros/{id}/sinopsis` (`1044-1046`);
  - `/api/voz` (`1492-1494`).
- La etapa `diccionario` llama con `usar_openai=False` (`1194-1195`).
- Ninguna otra ruta llega a OpenAI. Perfil, medir y curva usan el modelo
  local.
- Se devuelve el uso cuando no hubo llamada de pago:
  - en `/api/palabra`, con `llamadas_de_pago == 0` (`1220-1221`);
  - en la sinopsis, con `sin_red` o `sin_pasajes` (`1057-1058`).
- El cubo por hora solo se gasta si la petición va a costar (`_va_a_costar`,
  `1025-1027`).
- Las comprobaciones de tamaño de `/api/voz` van **antes** de cobrar
  (`1482-1486`).

**Validación**
- `_normalizar_id` es una lista blanca por expresión regular, que nunca
  admite una ruta (`206-216`).
- Un capítulo negativo o fuera de rango da 404: `ui._cap` comprueba
  `0 <= i < len` (`ui.py:1966`).
- Las rutas de audio, fonemas y cortes validan por expresión regular o por
  inventario, sin salir de su carpeta (`1277-1285`, `1331-1339`, `1412-1423`).
- `palabra.svg` tiene un tope de 60 caracteres, solo admite caracteres IPA
  (`_es_ipa`) y responde con CSP `default-src 'none'` y `nosniff`. La caché
  `lru_cache` tiene 512 entradas.
- Los cuerpos llevan topes de Pydantic: palabra 200, oración 2000, muestra
  25.000, consulta 300, `n ≤ 30`, respuestas del cuestionario en 0..2 y claves
  conocidas.

**Errores**
- El manejador global da un 500 con una frase y sin traza (`100-107`), y
  también se registra en `para_gradio` (`1671`).
- No lanzan hacia la API:
  - `cuaderno.registrar` (captura `sqlite3.Error` y `OSError`);
  - `voz.registrar_fallos` (`except Exception`);
  - `ficha.sinopsis` (devuelve una causa).

  Una corrección o una consulta ya pagadas no se convierten en 500 por el
  historial.
- `/api/inicio`: `biblioteca` guarda `capitulo` como `int` (`biblioteca.py:94`)
  y la `HTTPException` de `_abrir` se captura. La portada no cae por un libro
  que ya no está.
- `/api/estado` es pública y no expone usuarios: `cuentas.problemas()` usa
  `con_nombre=False`, y `declaradas()` es un recuento.
- Contraseñas:
  - el freno va antes de `verificar` (`ui.py:560`);
  - `compare_digest` compara en bytes;
  - el mensaje es el mismo si falla el usuario o la contraseña.

**Contrato con las privadas de `ui.py`**
- Los 49 nombres privados `ui._…` que importa `api.py` existen como funciones
  o variables del módulo `ui.py` en 2a49bf2. Comprobado con `ast`: el único
  «no definido» era el texto «ui.py» de un docstring.
- Firmas y valores por defecto cuadran con las llamadas:
  - `_analisis_guardado(libro, modo="completo")`;
  - `_muestra_de_libro(libro, palabras=2400)`;
  - `_guardar_sesion(ruta_libro, titulo, capitulo, peticion)`;
  - `_dentro_del_limite(peticion, cubo, tope)`;
  - `_mensaje_limite(idioma, minutos)`.
- `ui._ip` lee `headers.get(...)`, que funciona igual con los `Headers` de
  Starlette que con los de Gradio.

## Sin verificar

- Si Hugging Face sobrescribe `X-Forwarded-For` (hallazgo 1) y si limita el
  tamaño del cuerpo (hallazgo 3). Hay que comprobarlo contra el Space.
- Las bombas de descompresión en EPUB y PDF (hallazgo 2) no se han construido.
- El envenenamiento de la clave de análisis (hallazgo 4) no se ha reproducido.
