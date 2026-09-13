# Auditoría 18 — commit `1445a3c`: fonemas del AFI con audio en la corrección de voz

Auditor externo (Fable), a ciegas: no se ha leído ningún informe anterior. Solo lectura;
ninguna llamada a OpenAI. Comprobaciones con `git show`, `grep`, `inspect` y
`python -X utf8 -c` sobre el árbol actual (gradio 6.26.0, openai 3.8.0, pydantic 2.13.5).

**Recuento:** 0 críticos, 1 serio, 5 menores, 7 notas.

---

## Serio

### S1. El siguiente despliegue tira el Space entero: `app/fonemas.py` no está en la lista blanca y `ui.py` lo importa en la cabecera

- **Archivo:línea:** `tools/desplegar_app.py:47-73` (`LISTA_BLANCA`), `app/ui.py:52` (`import fonemas`), `app/voz.py:25` (`import fonemas`).
- **Cita literal:**
  ```
  LISTA_BLANCA = [
      "app/biblioteca.py",
      ...
      "app/ui.py",
      "app/voz.py",
      "requirements.txt",
  ```
  `grep -n fonemas tools/desplegar_app.py` no devuelve nada.
- **Escenario:** alguien corre `python tools/desplegar_app.py`. `--seco` dice que `ui.py` y `voz.py` «cambian» y los sube; `fonemas.py` no figura en la lista, así que ni se sube ni se echa en falta (`faltan` solo mira los que están en la lista). El Space arranca, `ui.py` hace `import fonemas` en la línea 52 → `ModuleNotFoundError` → **ninguna** pestaña funciona, no solo la de voz. El contrato («sin clave sigue funcionando todo lo que no usa red») se rompe en producción por un módulo que no usa red.
- **Por qué no lo bajo a nota aunque el commit diga «Sin desplegar»:** el mensaje del commit y la fila nueva de `AGENTS.md` hablan de «los mp3 en la lista blanca y una regla `*.mp3` de LFS», pero no de `fonemas.py`. Quien lea esa nota y decida «despliego sin audio, ya vendrán los mp3» tumba la app. Los mp3 que falten degradan bien (`audio_de` devuelve `None`); el `.py` que falte, no.
- **Arreglo:** añadir `"app/fonemas.py"` a `LISTA_BLANCA` en el mismo commit que toque `desplegar_app.py`, y de paso los 41 `app/audio_fonemas/*.mp3` (1,04 MB, cabe sin LFS: la propia lista ya sube un CSV de 22 MB por LFS, y aquí el umbral no se alcanza). Corregir la fila de `AGENTS.md` para que diga que **el módulo** también falta en la lista. Barato y útil: una prueba en `pruebas_extremas.py` que compruebe que todo `import x` de módulos propios en `ui.py` está en `LISTA_BLANCA` (habría cazado esto).

---

## Menores

### M1. `ə˞` (schwa con gancho rótico) se normaliza a `ə`, y dos entradas de `_ALIAS` son código muerto

- **Archivo:línea:** `app/fonemas.py:138` (`_DIACRITICOS`), `:128-129` (`_ALIAS`).
- **Cita literal:**
  ```
  "ɜː": "ɝ", "ɜːr": "ɝ", "ɜr": "ɝ", "ɝː": "ɝ", "ɜ˞": "ɝ", "ɜ": "ɝ",
  "ər": "ɚ", "ə˞": "ɚ", "ɚː": "ɚ",
  ...
  _DIACRITICOS = {"͡", "͜", "̯", "̩", "ʰ", "̚",
                  "̠", "̟", "̥", "̪", "̃", "˞"}
  ```
- **Escenario:** `normalizar("ə˞")` → se quita `˞` antes de mirar `_ALIAS` → queda `ə`, que está en el inventario → devuelve **`ə`** (comprobado). El gancho rótico no es un diacrítico que «no cambia el fonema»: es exactamente la diferencia entre `ə` («sofa») y `ɚ` («butter»). Con `ɜ˞` sale bien por casualidad (`ɜ` tiene alias a `ɝ`). Las claves `"ɜ˞"` y `"ə˞"` de `_ALIAS` son inalcanzables. Hoy no llega por la API (el `enum` estricto lo impide) pero `normalizar` se documenta como apta para «lo que devuelve un modelo o un diccionario», y la prueba `_normalizacion_de_simbolos` no lo cubre.
- **Arreglo:** sacar `˞` de `_DIACRITICOS` (así las dos claves de `_ALIAS` empiezan a funcionar), y añadir `"ə˞": "ɚ"` a los casos de la prueba. Lo mismo vale para `"̃"` (tilde nasal): `normalizar("ñ")` devuelve `n`; inofensivo, pero no es la intención.

### M2. `sonido_que_falla`, `como_colocar_la_boca` y `resumen` van al Markdown sin escapar; la prueba que dice cubrirlo es tautológica

- **Archivo:línea:** `app/ui.py:3126-3128` (`_detalle_de_voz`), `app/ui.py:3210` (`resumen`), `pruebas_extremas.py` (`_fonema_desconocido_no_revienta`).
- **Cita literal:**
  ```
  sonido = str(getattr(d, "sonido_que_falla", "") or "").strip().rstrip(".")
  boca = str(getattr(d, "como_colocar_la_boca", "") or "").strip()
  explicacion = " ".join(t for t in (f"{sonido}." if sonido else "", boca) if t)
  ```
  y en la prueba: `for raro in ("zzz", "ninguno", "", "ɒ", "<script>", None): ... assert "<script" not in html`.
- **Escenario:** ejecutado: `DetallePalabra(palabra="warn", fonema="w", sonido_que_falla='<img src=x onerror=alert(1)>', como_colocar_la_boca='<script>alert(2)</script>')` → `_detalle_de_voz` devuelve el `<img onerror>` y el `<script>` **literales** dentro del veredicto. En la interfaz normal no explota porque `gr.Markdown` tiene `sanitize_html=True` y DOMPurify lo limpia en el navegador (comprobado en el bundle: `audio`/`controls` permitidos, `script`/`on*` no). Pero la misma cadena sale cruda por `/gradio_api/call/...` a cualquier cliente de la API, y `palabra` sí se escapa dos líneas más arriba: la protección es inconsistente. La prueba con `"<script>"` en **`fonema`** pasa siempre, porque un fonema que no está en el inventario nunca se imprime (`buscar` da `None` y el texto no aparece): no asevera nada sobre escapado. Este punto es preexistente (antes del commit `d.sonido_que_falla` también iba crudo); lo que añade el commit es la prueba que da una confianza que no da.
- **Arreglo:** `_html.escape(..., quote=False)` en `sonido`, `boca` y `resumen`, igual que en `palabra`; y en la prueba meter el `<script>` en `sonido_que_falla` y aseverar que sale como `&lt;script`.

### M3. El fallo al abrir Kaikki se recuerda para siempre en el proceso

- **Archivo:línea:** `app/fonemas.py:203-224` (`_abrir_diccionario`).
- **Cita literal:** `except Exception: _diccionario_fallo = True` y, al entrar, `if _diccionario is not None or _diccionario_fallo: return _diccionario`.
- **Escenario:** en un Space, `kaikki_diccionario.db` «se monta como volumen de solo lectura» (`lexicon.py:66`). Si la primera práctica de voz ocurre antes de que el volumen esté (o durante un `FileNotFoundError` transitorio, un `OperationalError: database is locked` de sqlite), **todas** las prácticas hasta el siguiente reinicio dicen «sin transcripción fonética en el diccionario» aunque el diccionario ya esté ahí, y no hay traza de por qué. La consulta léxica (`ConsultorLexico`) sí lo abriría bien porque no comparte esta bandera.
- **Arreglo:** recordar la marca de tiempo del fallo y reintentar pasado un minuto, o, más simple, no recordar `OperationalError` (solo `FileNotFoundError`). Y registrar el motivo con `logging` una vez.

### M4. La IPA que se pinta y el fonema del audio pueden usar dos convenciones en la misma línea

- **Archivo:línea:** `app/fonemas.py:232-247` (`ipa_de_palabra` devuelve la UK si no hay US), `app/ui.py:3110-3113`.
- **Cita literal:** `if us: return us, "US"` / `if _uk: return _uk, "UK"`.
- **Escenario:** `thought` → Kaikki solo trae `/θɔːt/` (UK); el modelo elige `ɔ`. El alumno ve `- **thought** /θɔːt/ (UK)` y, debajo, `Sonido /ɔ/, como en law, caught` con audio de General American. El docstring del módulo justifica todo el inventario con «enseñar /r/ en el fonema junto a /woɹn/ en la palabra sería enseñar dos símbolos para el mismo sonido en la misma línea», y eso es exactamente lo que pasa con `ɔː`/`ɔ`, `ɜː`/`ɝ`, `əʊ`/`oʊ`, `ɒ`/`ɑ` cada vez que hay que caer a UK. Medido en el volcado: 40.286 entradas con `ipa_uk` frente a 40.143 con `ipa_us`; el solapamiento no es total, así que el caso ocurre.
- **Arreglo:** cuando la variante es UK, añadir una coletilla corta («transcripción británica; el sonido de abajo es el americano»), o pasar la IPA UK por una versión de `normalizar` símbolo a símbolo (el módulo ya sabe hacer `ɔː→ɔ`, `ɜː→ɝ`, `əʊ→oʊ`). Como mínimo, no prometer en el docstring una consistencia que la ruta UK rompe.

### M5. `_normalizar` acepta mayúsculas solo para las letras que tienen alias

- **Archivo:línea:** `app/fonemas.py:167` (`return _ALIAS.get(texto) or _ALIAS.get(texto.lower())`).
- **Escenario:** `normalizar("R")` → `ɹ`, `normalizar("G")` → `ɡ`, pero `normalizar("W")` → `None`, `normalizar("S")` → `None`, porque la comprobación contra `_POR_SIMBOLO` va antes y no baja a minúsculas. Poca importancia práctica (el `enum` estricto lo impide desde la API), pero es la clase de inconsistencia que una prueba futura de «acepta lo que escribe un profesor» encontrará.
- **Arreglo:** bajar a minúsculas una vez, antes de las dos búsquedas, solo si `texto` es ASCII (los símbolos AFI no tienen mayúscula y `lower()` no los toca, así que basta con `texto = texto.lower() if texto.isascii() else texto`).

---

## Notas

### N1. Cobertura real de la IPA en Kaikki: un tercio de las palabras más comunes no la tiene

`SELECT` sobre `entradas`: 1.487.639 filas, 40.143 con `ipa_us`, 40.286 con `ipa_uk`. De 102 palabras corrientes probadas, 64 tienen IPA; **`the`, `I`, `ship`, `be`, `in`, `that`, `is`... no**. La línea «(sin transcripción fonética en el diccionario)» va a ser lo normal, no la excepción, en frases de nivel 0. El commit lo reconoce en el docstring («el hueco es frecuente») y la interfaz lo dice; queda apuntado para que nadie lo tome por un fallo del código. Si algún día se quiere cerrar el hueco, la fuente es otro volcado de Kaikki con los campos `sounds`, no el modelo.

### N2. La URL del `<audio>` expone la ruta absoluta del sistema de archivos

`_reproductor_fonema` produce `src="gradio_api/file=C:/Users/laura/literalevel/app/audio_fonemas/0077.mp3"` (en el Space, `/home/user/app/...`). Es lo que Gradio hace con todo archivo servido, así que no añade riesgo nuevo, pero un nombre de usuario en el HTML de un Space público es información gratis. Si se quiere evitar, `gr.set_static_paths([fonemas.DIR_AUDIO])` sirve los mp3 sin pasar por `allowed_paths` y con la misma URL.

### N3. `explicar_correccion(idioma=...)` ya no tiene sentido con el prompt nuevo

`_PROMPT_SISTEMA` fija «inglés americano (General American)» y el `enum` es el inventario inglés; el parámetro `idioma` sigue interpolándose en el mensaje de usuario. Con `idioma="francés"` el modelo recibe una contradicción. Es vestigial: o se quita el parámetro, o se documenta que solo vale `"ingles"`.

### N4. La prueba «la práctica pinta ipa y audio» no asevera que se pinte ninguna IPA

`_la_practica_pinta_ipa_y_audio` comprueba dos `<audio>`, los símbolos `/w/` y `/ʃ/`, el texto del detalle sin fonema y el conteo de líneas de lista; ninguna aserción mira la transcripción de la palabra. Pasa igual con `kaikki_diccionario.db` presente o ausente. No es tautológica (rompe si `_detalle_de_voz` deja de llamarse), pero el nombre promete más de lo que mide. Si se quiere que mida la IPA, doblar `fonemas._diccionario` como hace `_ipa_ausente_no_se_inventa` y aseverar `"/woɹn/ (US)"`.

### N5. El generador escribe los temporales dentro de la carpeta servida

`tools/generar_fonemas.py:178`: `tempfile.mkstemp(dir=str(destino.parent), prefix=f".{destino.stem}.", suffix=".tmp")`. Mientras dura la escritura (y si el proceso muere con un `kill -9`, para siempre) hay un `.0077.xxxx.tmp` en `app/audio_fonemas/`, que está en `allowed_paths`. Solo se sirve a quien adivine el nombre aleatorio, y como `application/octet-stream`; el `finally` lo borra en el caso normal. Vale con un `tempfile.gettempdir()` y `shutil.move`, o con aceptarlo y dejar esta nota.

### N6. `_ENVOLTURA` quita el punto y la comilla simple de en medio, no solo de los bordes

`"".join(c for c in texto if ... c not in _ENVOLTURA)` elimina `.`, `'`, espacio y comillas en cualquier posición. `normalizar("t ʃ")` → `tʃ` (bien por casualidad), `normalizar("s.t")` → `st` → `None`. No produce un fonema equivocado en ningún caso que haya encontrado; queda como aviso de que «envoltura» no describe lo que hace.

### N7. Los 41 audios, según el propio registro, tienen 15 «dudosos» y 3 «no verificables» y nadie los ha oído

Contado en `tools/fonemas_generados.json`: `verificado` 23, `dudoso` 15, `no verificable` 3 — coincide con el mensaje del commit, que es honesto al respecto. No es un defecto de código; es lo primero que hay que hacer antes de enseñárselo a un alumno de 15 años: que alguien con oído los escuche (`θ`, `ð`, `æ`, `ʌ`, `ɚ` son los que el reconocedor confunde por diseño).

---

## Comprobado y está bien

**Seguridad al servir archivos**
- `RUTAS_PERMITIDAS = [dir_datos()/audio, fonemas.DIR_AUDIO]` llega a `launch(allowed_paths=...)` (`ui.py:4065`). `DIR_AUDIO` es `app/audio_fonemas/` exactamente, sin subir al padre; listado: 41 archivos, todos `.mp3`, nada más.
- No hay ruta controlada por el usuario ni por el modelo: `_detalle_de_voz` → `fonemas.buscar(d.fonema)` → solo devuelve un `Fonema` del inventario cerrado → `audio_de(fonema.simbolo)` → `fonema.ruta = DIR_AUDIO / <hex>.mp3`. Un `fonema` con `../`, barras o `<script>` da `None` y no pinta nada.
- Gradio 6.26: `file_fetch` (`route_utils.py`) resuelve con `abspath().resolve()` y exige `relative_to(allowed_path)`; rechaza directorios, URLs y lo que no existe con 403. Ruta absoluta de Windows con `C:` funciona (es lo que Gradio usa para sus propios archivos). `mimetypes` da `audio/mpeg` → `inline`.
- `_reproductor_fonema` escapa `src`, `aria-label` y `title` con `_html.escape(quote=True)`; `palabra` e `ipa` con `quote=False`. El `<audio controls preload src style aria-label title>` sobrevive a DOMPurify (etiquetas y atributos comprobados en el bundle de `templates/frontend/assets`; `FORBID_TAGS` solo lleva `style`).
- `allowed_paths` no se valida en `launch`: un Space sin la carpeta de mp3 no revienta al arrancar; `audio_de` devuelve `None` y no se pinta el reproductor.

**Structured Outputs**
- `chat.completions.parse` en openai 3.8 pasa por `type_to_response_format_param` → `to_strict_json_schema(Correccion)` con `strict: True` (leído con `inspect`). El esquema resultante para `fonema` es `{"type": "string", "enum": [42 valores]}`, con `fonema` en `required` y `additionalProperties: false`; el `json_schema_extra` de pydantic 2.13 se fusiona sin problema. 42 valores están muy por debajo de los límites de OpenAI para `enum`.
- Con `strict: True` el servidor garantiza que el valor pertenece al `enum`: barras, variantes RP, cadena vacía o texto libre **no pueden llegar** por la API. Si llegan de otro sitio (caché futura, cambio de modelo), `fonema: str` en pydantic no lanza, `normalizar` da `None` y la interfaz pinta el texto sin reproductor. `"ninguno"` → `len > 4` → `None`. Comprobado en ejecución.
- `resp.choices[0].message.parsed` con `refusal` da `None` y `explicar_correccion` devuelve `None`; `_practicar` lo trata como «sin corrección». Preexistente y coherente.

**Degradación elegante**
- Sin clave: `_practicar` devuelve el aviso antes de tocar `voz.practicar`; `audio_de("/w/")` devuelve la ruta con `OPENAI_API_KEY` borrada del entorno (ejecutado). `fonemas.py` no importa el SDK de OpenAI.
- Sin diccionario: `lexicon.Diccionario.__init__` lanza `FileNotFoundError` si la ruta no existe → capturado → `(None, None)` → «(sin transcripción fonética en el diccionario)». Nada llega a la interfaz como excepción (ver M3 para el «para siempre»).
- Palabra ausente o sin IPA: `(None, None)`; la fila con `ipa_uk`/`ipa_us` vacíos se trata como ausente. No se inventa ninguna transcripción: la única fuente es `lexicon._mejor_fonetica` sobre filas de Kaikki. `Diccionario.buscar` baja a minúsculas, así que «Warn» funciona; «warn,» no, pero `normalizar_palabras` (`voz.py:68`) ya quita la puntuación antes de que las palabras lleguen al modelo.
- mp3 ausente: `audio_de` mira `is_file()` y `st_size > 0` dentro de `try/except OSError` → `None` → sin reproductor, sin excepción.
- `_detalle_de_voz` lee con `getattr` y tolera `SimpleNamespace()` vacío (ejecutado).

**Rendimiento**
- La base se abre una sola vez (`_abrir_diccionario`, doble comprobación con `threading.Lock`), en `mode=ro` y con `check_same_thread=False`; cada `buscar` va bajo `_cerrojo`. `entradas(palabra)` tiene `idx_palabra` y el plan es `SEARCH ... USING INDEX`. Medido: 200 consultas en 45 ms. La primera llamada tarda 1,4 s en un proceso limpio porque importa `lexicon` (numpy); en `ui.py` `lexicon` ya está importado en la cabecera, así que no se paga. No se toca spaCy ni MiniLM: `lexicon` los carga en `ConsultorLexico`, no en `Diccionario`.

**Normalización e inventario**
- 24 consonantes, 12 vocales, 5 diptongos: es el inventario fonémico de General American completo (con `ɝ`/`ɚ` como vocales róticas y `ɔ` mantenido para quien no tenga la fusión cot-caught). `ʍ→w`, `ɫ→l` y las silábicas (`n̩`, `l̩`) se tratan como alófonos, que es lo correcto. `ɒ`, `ɪə`, `eə`, `ʊə`, `ɾ`, `ʔ` → `None`, con la justificación escrita en el docstring.
- Equivalencias `r→ɹ`, `iː→i`, `uː→u`, `ɑː→ɑ`, `ɔː→ɔ`, `e→ɛ`, `ɜː/ɜːr/ɜr→ɝ`, `ər→ɚ`, `əʊ→oʊ`, `ʧ→tʃ`, `ʤ→dʒ`, `t͡ʃ→tʃ`, `g→ɡ`: todas correctas para el uso previsto (Cambridge/Oxford/RP → GA). Acentos `ˈ`/`ˌ` y ligaduras se quitan bien (`ˈɔɪ→ɔɪ`, `oʊ̯→oʊ`, `tʃʰ→tʃ`).
- Kaikki usa `ɹ` en 16.080 `ipa_us` y `r` a secas solo en 422: la afirmación del docstring de que Wiktionary GA escribe `ɹ` se sostiene.
- Nombre del mp3: `"_".join(f"{ord(c):04x}")`. Con el separador `_` y ancho fijo de 4, `tʃ` → `0074_0283` no puede chocar con `t` (`0074`) ni con `ʃ` (`0283`); la prueba `_inventario_completo_y_sin_duplicados` lo asevera sobre los 41 y el listado del disco lo confirma.

**Pruebas nuevas (8)**
- Todas devuelven cadenas (nunca `False` ni listas), así que el envoltorio `prueba` no puede dejarlas pasar en verde por accidente. `_inventario_completo_y_sin_duplicados`, `_cada_fonema_tiene_su_audio` (mira el disco y `RUTAS_PERMITIDAS`), `_normalizacion_de_simbolos` (39 casos con esperado explícito), `_ipa_ausente_no_se_inventa` (dobla el diccionario y restaura en `finally`) y `_esquema_y_prompt_apuntan_al_inventario` (usa el `to_strict_json_schema` real) aseveran lo que dicen. Las dos excepciones parciales están en M2 y N4. `assert "warn" in html and "Redondea" in html or raro is None` tiene la precedencia que pretende.

**Prompt de `explicar_correccion`**
- No pide ni permite definir la palabra, ni su transcripción: solo el fonema (del `enum`), el anclaje a una palabra del español y la instrucción de la boca. La IPA de la palabra viene de Kaikki y solo de ahí. La lista del prompt y el `enum` salen del mismo `fonemas.INVENTARIO`, así que no pueden divergir. No contradice el contrato.

**Contrato entre módulos**
- `voz.py` (de Codex) gana un campo público obligatorio; está avisado en el título del commit y en `AGENTS.md`. `fonemas.py` no importa `voz` ni `ui`; `lexicon` no importa `voz` ni `fonemas`: sin ciclos. La escala 0..2 no se toca.
