# Auditoría cruzada a ciegas: voz, léxico, fonemas y animación

- **Auditor:** e6 (Claude Code). **Área:** `app/voz.py`, `app/lexicon.py`,
  `app/fonemas.py`, `app/animacion_articulatoria.py` y sus pruebas (de 4e).
- **HEAD al empezar:** `4d4bb1b2b8a300ecf49e9e18fc4c9e855bf4c62d`.
- **Método:** lectura completa de `voz.py` y `fonemas.py`; de `lexicon.py`, las
  partes de fonética, IA, caché y degradación (líneas 400–460, 600–700,
  905–1236); de `animacion_articulatoria.py`, duración y una pasada (480–520,
  806–850, 936–1085). Verificaciones ejecutadas, marcadas **[V]**; solo leídas,
  **[L]**.

> **Aviso sobre la verificación.** Corrí `pruebas_voz.py` y `pruebas_lexicon.py`
> creyendo que iban sin clave (`OPENAI_API_KEY=` vacía), pero `config.cargar()`
> la rellena desde `CLAVES.txt` cuando la variable está vacía: esas dos pruebas
> y un guion mío hicieron **llamadas reales** a OpenAI (whisper, tts-1,
> gpt-4o-mini y gpt-5). Es gasto autorizado (Miguel añadió créditos para pruebas
> el 14 sep), pero conviene saberlo: para ensayar de verdad sin clave hay que
> usar `LITERALEVEL_SIN_CLAVES=1`. Lo que cuento como «sin clave» abajo está
> verificado con `_cliente` sustituido por `None`, no con esas corridas.

Resultados de las pruebas: `pruebas_voz.py` TODO OK · `pruebas_voz_ritmo.py` OK ·
`pruebas_voz_concurrencia.py` OK · `pruebas_animacion.py` todo ok ·
`pruebas_lexicon.py` **1 fallo** (ver DUDA 1).

---

## SERIO

### S1. El validador de la lectura natural deja pasar reducciones falsas: «going to» + nombre → «gonna» **[V]**

- **Dónde:** `app/voz.py:1026-1030`
- **Qué dice:**
  `conocidas = REDUCCIONES_CONOCIDAS.get(tuple(palabras[desde:hasta + 1]), set())`
  … `if forma.lower() in conocidas and not solapa:`
- **Por qué:** solo mira que las palabras reducidas sean las de la lista, no lo
  que va detrás. «gonna» solo vale para *going to* + verbo (futuro), y «gotta»
  para *got to* de obligación. Ejecutado con `_validar_natural` y lo que podría
  proponer el modelo:
  - «I am going to school.» → acepta `gonna`, versión natural **«I am gonna school.»**
  - «We got to the station late.» → acepta `gotta`, versión natural **«We gotta the station late.»**
  Y esa versión natural es la que se manda al TTS («Escúchalo natural»): el
  lector oiría una frase agramatical presentada como la natural.
- **Arreglo:** para `going to`, `got to`, `have to`, `has to`, `want to` y
  `ought to`, exigir que la palabra siguiente no sea determinante, pronombre
  objeto ni nombre (o que sea un verbo en la forma base según spaCy), o sacarlas
  de la lista automática y aceptarlas solo con verbo detrás.

### S2. La corrección confunde dos veces la misma palabra dicha de dos maneras **[V]**

- **Dónde:** `app/voz.py:403-404` y `411-412`
- **Qué dice:**
  `oidas = ({_clave_palabra(o): (d or "") for o, d in entendidas if o} …)` y
  `simbolo, motivo = _comparar(clave, oidas[clave])`
- **Por qué:** el diccionario se indexa por palabra, así que si la frase repite
  una palabra y se falla de dos formas, la segunda pisa a la primera. Con
  `entendidas = [("cat", "cut"), ("cat", "cap")]` los dos detalles salen con
  **/t/**, cuando por separado «cat→cut» es **/æ/** y «cat→cap» es /t/. El
  consejo de boca del primero es falso. Es justo la clase de error que el
  apartado «fonema determinista» quería eliminar.
- **Arreglo:** emparejar los detalles con `entendidas` por orden (una cola por
  palabra) en vez de por un diccionario.

---

## MENOR

### M1. `practicar` guarda como falladas todas las palabras cuando no hay transcripción **[V]**

- **Dónde:** `app/voz.py:1276-1279`
- **Qué dice:** `evaluacion = evaluar_pronunciacion(frase_objetivo, transcripcion or "")`
  … `if guardar_fallos and evaluacion.palabras_falladas: registrar_fallos(...)`
- **Por qué:** sin clave, sin red o con un audio ilegible, `transcripcion` es
  `None`, todo cuenta como fallado y, con el valor por defecto
  `guardar_fallos=True`, se guardan todas en «Tus palabras difíciles».
  Ejecutado con un audio inexistente: guardaría `['the', 'quick', 'brown',
  'fox', 'jumps']`. Hoy no pasa en producción porque la API
  (`api.py`) y Gradio (`ui.py:3771`) llaman con `guardar_fallos=False` y miran
  `transcripcion_ok`, pero el valor por defecto es la trampa.
- **Arreglo:** `if guardar_fallos and transcripcion is not None and …`.

### M2. Un enlace «consonante + vocal» se acepta a través de un punto **[V]**

- **Dónde:** `app/voz.py:1014-1018` con `normalizar_palabras` (`voz.py:87`)
- **Qué dice:** `and _enlace_real(tipo, palabras[de], palabras[a])`
- **Por qué:** las palabras llegan sin puntuación, así que el validador no ve
  las fronteras de frase. «Stop. Eat it.» acepta el enlace *stop‿eat*
  (`/stɑp‿it/`), que no se da con un punto en medio.
- **Arreglo:** pasar al validador las posiciones seguidas de `.`, `?`, `!`, `;`
  o `:` en la frase original y descartar enlaces que las crucen.

### M3. La IPA del énfasis sale del modelo, sin validar y sin marca de IA **[V]**

- **Dónde:** `app/voz.py:1012` y `1077-1079`
- **Qué dice:** `enfasis.append({"indice": i, "ipa": _ipa_corta(_campo(e, "ipa"))})`
- **Por qué:** `_ipa_corta` acepta cualquier texto de hasta 40 caracteres:
  `"cualquier cosa"` sale como `/cualquier cosa/`. A los enlaces se les rehace la
  IPA con el diccionario (`_ipa_enlace`) y las reducciones llevan
  `generado_por_ia`, pero el énfasis no tiene ni lo uno ni lo otro. El front
  actual no pinta esa IPA, pero la API la devuelve.
- **Arreglo:** sustituirla por `fonemas.ipa_de_palabra` como en los enlaces, o
  marcarla `generado_por_ia`.

### M4. Dos lectores con la misma frase nueva pagan dos veces el análisis natural y la transcripción de referencia **[L]**

- **Dónde:** `app/voz.py:1103-1135` (`analizar_natural`) y `761-783`
  (`_tiempos_de_referencia`)
- **Qué dice:** se mira la caché (`if ruta.is_file()`) y, si falta, se llama a
  OpenAI, sin candado entre medias.
- **Por qué:** el TTS sí tiene candado por clave (`_candado_audio`) y relee
  dentro; estas dos no. Con la misma frase a la vez, cada petición paga su
  gpt-4o-mini y su whisper de la referencia.
- **Arreglo:** el mismo `_candado_audio(str(ruta))` con relectura dentro.

### M5. Si la transcripción con marcas falla, se transcribe otra vez **[L]**

- **Dónde:** `app/voz.py:1272-1275`
- **Qué dice:** `tiempos = transcribir_con_tiempos(ruta_audio)` … `if tiempos is None: transcripcion = transcribir_audio(ruta_audio)`
- **Por qué:** `transcribir_con_tiempos` devuelve `None` por cualquier excepción,
  también por un plazo agotado después de que OpenAI haya procesado (y cobrado)
  el audio. Entonces se sube y se paga otra vez. El comentario dice «sale una
  sola», que es cierto sin clave, pero no con un fallo de red.
- **Arreglo:** reintentar solo si el error es de formato (400) y no de plazo o
  de conexión.

### M6. `_ipa_de_modelo` acepta cualquier texto como IPA **[V]**

- **Dónde:** `app/lexicon.py:624-630`
- **Qué dice:** `return texto if texto.startswith(("/", "[")) else f"/{texto.strip('/')}/"`
- **Por qué:** «no sé, quizá» sale como `/no sé, quizá/` con la marca «IPA por
  IA». La marca avisa, pero lo que se pinta no es una transcripción.
- **Arreglo:** exigir que todos los caracteres sean del alfabeto IPA, acentos y
  signos (como `_es_ipa` de `api.py`) y, si no, dejarla vacía.

---

## DUDA

### D1. `pruebas_lexicon.py` falla en «set off»

- **Dónde:** `pruebas_lexicon.py`, salida: `- 'set off': se esperaba el sentido de hacer explotar`
- **Por qué es duda:** la prueba va contra la base y el modelo reales, y la
  corrida tuvo clave (ver el aviso de arriba). No distingo si es una regresión
  de la desambiguación por embeddings, un cambio de la base o una respuesta
  distinta del modelo, y no la repito para no volver a gastar.
- **Qué haría:** repetirla con `LITERALEVEL_SIN_CLAVES=1`. Si falla igual, es la
  elección de acepción local; si no, depende de OpenAI y la prueba no debería
  exigirla sin clave.

---

## Comprobado y correcto

- **Animación con `dur` y `repetir`** **[V, en el Space]:**
  - `dur=0.3` y `dur=30` se aplican (0,30 s y 30,00 s).
  - `0.2`, `30.04`, `31`, `nan`, `inf` y `-5` se ignoran y vuelve el ciclo de
    2,80 s; `quieto=1` ignora las dos cosas.
  - Con `una=1` las 23 animaciones del ciclo pasan de `infinite` a `1 both`, y
    sin él siguen infinitas. La única que queda `infinite` es el temblor de
    0,09 s de la vibración, que es a propósito y se apaga con la opacidad al
    acabar.
  - `svg_palabra(..., dur=2, repetir=False)` hace lo mismo (24 y 29
    animaciones de una pasada para «wɔɹ» y «ˈdoʊntʃə»).
- **Fonema determinista** **[V]:** `fonema_que_cambia("tragic", "magic")` da `t`
  tres veces seguidas; sale de comparar IPA de diccionario y el consejo de
  `articulacion.FICHAS`, no del modelo (`voz.py:397-444`). Solo falla con
  palabras repetidas (S2).
- **IPA por forma y marca de IA** **[L]:**
  - `_fonetica_de_la_forma` usa las entradas de ESA forma y nunca el audio del
    lema (`lexicon.py:441-456`).
  - La IPA del modelo solo rellena lo que falta y enciende
    `ipa_generada_por_ia`, tanto en el modo IA como en el compuesto o sin IPA
    (`lexicon.py:1159-1167`, `1198-1206`).
  - `fonemas.ipa_de_palabra` nunca pide la transcripción al modelo
    (`fonemas.py:292-336`).
- **Degradación sin clave** **[V con `_cliente` a `None`, y L]:**
  - `transcribir_audio`, `explicar_correccion` y `generar_audio_correcto`
    devuelven `None`, y el audio ya generado se sirve sin clave
    (`voz.py:514-527`).
  - `analizar_natural` sirve lo guardado.
  - `ConsultorLexico.consultar` deja avisos en vez de lanzar (`lexicon.py:1013-1042`).
  - `pruebas_voz_ritmo.py` lo cubre con `_cliente` sustituido.
- **Caché y coste del TTS** **[L]:** la clave va por contenido, voz, modelo y
  versión; la escritura es atómica y hay un candado por clave exacta con
  relectura dentro (`voz.py:457-535`). En léxico, candados por franja con
  relectura y `llamadas_de_pago` contado después de pagar (`lexicon.py:1053-1129`).
- **Concurrencia e historial** **[V, `pruebas_voz_concurrencia.py` OK]:**
  - La migración se serializa solo si falta la tabla o la columna.
  - Si la base existe y no se lee, sale `HistorialIlegible`, no una lista vacía.
  - La tabla del ritmo se crea con `BEGIN IMMEDIATE` (`voz.py:550-582`, `1144-1167`).
- **Validador de la lectura natural, lo que sí filtra** **[L y V]:**
  - Índices fuera de rango.
  - Enlaces que no son `a = de + 1`, o cuyo tipo no casa con los bordes
    sonoros de la IPA de diccionario.
  - Reducciones de palabras que no están en la lista, las que se solapan y la
    «to come → gonna» del primer caso real.
  - La versión natural se reconstruye si no coincide.
  - El énfasis no cae en palabras funcionales al releer la caché.
