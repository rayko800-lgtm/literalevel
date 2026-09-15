# LiteraLevel — reglas para agentes

Aquí trabajan **dos agentes a la vez** sobre el mismo repo: Claude Code y Codex.
El afectado de una colisión es Miguel. Lee esto antes de tocar nada.

## Reparto vigente (6 sep 2026)

| Zona | Dueño | Regla |
|---|---|---|
| `app/ui.py` | **Claude Code** | Codex no la edita. Puede leerla para auditar contratos. |
| `app/cuaderno.py` | **Claude Code** | Historial de palabras consultadas. NO es la cache de `lexicon.py`. |
| `app/reader.py`, `app/lexicon.py`, `app/voz.py` | **Codex** | Está auditándolos. Claude no los edita sin avisar. |
| — | — | **7 sep, 11:00:** Codex agotó su cuota y Miguel pidió a Claude Code que asumiera sus tareas. Los cambios de Claude en esos tres archivos van marcados en el commit. Cuando Codex vuelva, que lea `git log` antes de tocar nada. |
| — | — | **9 sep, 09:25:** Claude Code ha tocado archivos compartidos cerrando dos auditorías. `app/scoring.py` (mensaje de error del modelo y comentario del lote), `app/paletas.py` (ocho colores oscurecidos por contraste), `pruebas_extremas.py` (la prueba de contraste pasa de 4 a 8 parejas por paleta), `validar_local.py` (el regex del nivel, el bloque del baseline y `cuerpo_estricto`), `colab_precalculo.py` y **`app/ficha.py`**: `_es_boilerplate` miraba las primeras 400 palabras SIN quitar la envoltura legal de Gutenberg, y por eso descartaba como licencia cualquier `.txt` sin encabezados de capitulo. Se perdian libros enteros. Todo desde el commit `aed7751`. **Lee `auditoria/cierre_2026-09-09.md` y `git log` antes de tocar nada.** |
| — | — | **9 sep, 21:30 (Claude Code):** cierre de la décima auditoría. Tocados `app/ui.py`, `app/cuentas.py`, `app/paletas.py`, `pruebas_extremas.py`, `DESPLIEGUE.md`, `PENDIENTES.md`, `README.md`, `entrega/{documento.tex,estrategia.md,mensaje_profesor.md}`. **`app/cuentas.py` tiene interfaz pública nueva**: `problemas()` y `declaradas()`, y `_tabla` se apoya en `_analizar`. Lee `auditoria/cierre_2026-09-09_noche.md` antes de tocar nada. **Sin desplegar todavía.** |
| — | — | **9 sep, 23:00 (Claude Code):** cierre de la **undécima** auditoría, la más productiva del proyecto. Tocados otra vez `app/ui.py`, `app/cuentas.py`, `app/paletas.py`, `app/perfil.py` y `pruebas_extremas.py`. **`app/cuentas.py` añade `devolver()`** a su interfaz pública, y **`app/perfil.py` valida ahora que `nivel` sea numérico** en `cargar` (un perfil con `nivel: "abc"` se daba por bueno y reventaba después). Lo importante para quien venga: **el envoltorio `prueba` trata `False` como fallo e itera generadoras**, así que una prueba que devuelva el booleano crudo ya no vale — tiene que aseverar su expectativa. Lee `auditoria/cierre_auditoria_11.md`. **Sin desplegar.** |
| — | — | **10 sep, 01:00 (Claude Code):** cierre de la **duodécima** auditoría (0 críticos, 8 serios). Tocados `app/ui.py` y `pruebas_extremas.py`. **Cambio de comportamiento a tener en cuenta:** el tope por hora del cubo «lexico» ya solo se aplica cuando la consulta VA A COSTAR dinero —hay clave y la sesión puede pagar—, porque una consulta sin perfil es diccionario local y la cabecera del módulo promete que lo gratis no se limita. Y `_analisis_guardado`/`_sinopsis_guardada` validan ahora la FORMA del JSON, no solo que parsee. Lee `auditoria/cierre_auditoria_12.md`. **Sin desplegar, y la tarjeta del modelo en HF tiene un enlace roto que necesita tu token.** |
| — | — | **10 sep, tarde (Claude Code):** cierre de cuatro revisiones en paralelo. **Tocados `app/reader.py` y `app/voz.py`, que son TUYOS**, y `app/scoring.py`, que es compartido. En `reader.py`: el manifiesto del epub se leía con un regex que exigía `id` antes que `href`, y Gutenberg los escribe al revés, así que el `spine` no se resolvía en NINGUNO de los 10 epub cacheados y el índice caía a un orden de texto (1, 10, 11, 12, 2…): *The Final Problem* salía de capítulo 5 de 13. En `scoring.py`: `continuous_prose` rechazaba por DOS VIÑETAS en absoluto, y eso tiraba capítulos de novela enteros —52 de 58 falsos rechazos medidos—; ahora mira la fracción de palabras en líneas de maquetado (`PESO_MAQUETADO`). **Consecuencia en una cifra publicada: los textos que pasan el filtro completo pasan de 31 a 36.** En `voz.py`: el cliente de OpenAI lleva `timeout`. Lee `auditoria/` y `git log`. |
| — | — | **10 sep, 17:00 (Claude Code):** cierre de la **decimotercera** auditoría (0 críticos, 8 serios, 14 menores). **Tocados `app/reader.py` y `app/lexicon.py`, que son TUYOS.** En `reader.py`: los epub viejos de Gutenberg (`pg28xxx`) repiten `<h1>The Project Gutenberg eBook of X</h1>` al principio de cada archivo y se colaba como título del capítulo —la *Alicia* ilustrada salía con 13 capítulos llamados igual y la curva del libro entero se calculaba sobre 1 de 13—; y el `<span class="caption">` de un pie de lámina se colaba delante del título en *Orgullo y prejuicio*. En `lexicon.py`: **`ResultadoLexico` tiene un campo nuevo, `llamadas_de_pago: int`**, porque `desde_cache` solo habla de la explicación y el audio se pide aparte —«Fetters», «FETTERS» y «fetters.» pagaban un tts-1 cada una con el cupo devuelto—; y la clave del audio se normaliza (minúsculas, sin puntuación en los bordes). También `ui.py`, `ficha.py` (con `miles()`, que usa `catalogo` desde ahora), `perfil.py` (con `HOLGURA`, la ÚNICA holgura de recomendación, que `ui` lee de ahí), `catalogo.py`, `pruebas_extremas.py` y `pruebas_lexicon.py`. Lee `auditoria/cierre_auditoria_13.md`. **Desplegado el 10 de septiembre y cotejado por hash.** Para saber si el Space está al día no te fíes de esta tabla: corre `python tools/desplegar_app.py --seco`, que lo compara y lo dice. |
| — | — | **11 sep, tarde (Claude Code):** cierre de la **decimoquinta** auditoría (0 críticos, 7 serios, 6 menores, 2 notas) y de sus **22 mutantes vivos**. **Tocado `app/lexicon.py`, que es TUYO, y con cambio de firma interna:** `_generar_audio_tts` devuelve ahora `(ruta, se_pago)` y `llamadas_de_pago` se cuenta **después** de llamar, no antes — un *timeout* o un 401 no cuestan un céntimo y descontaban un uso del cupo, y el mp3 que ya estaba en disco se cobraba como si se hubiera pedido a tts-1. **`app/cuentas.py`: `_analizar` acepta `con_nombre`** y `problemas()` la llama con `False`, porque la pestaña «Estado» es pública y escribía los nombres de usuario de las entradas rotas del secreto. También `ui.py` (freno de intentos en la puerta, `_estado_de_entrada` en `demo.load`, las dos cajas de la pestaña de voz, la nota del nivel heredado en las dos tablas) y `ficha.py` (`_VACIAS` con contracciones y verbos corrientes, y `_PALABRA_RE` con letras no ASCII: «Svidrigaïlov» se partía en dos). `pruebas_extremas.py` pasa de 276 a **296**. Lee `auditoria/cierre_auditoria_15.md`. **Desplegado el 11 de septiembre y cotejado por hash.** |
| — | — | **12 sep, noche (Claude Code):** fonemas del AFI con audio pregrabado en la corrección de voz, a petición de Miguel y de Laura. **Tocado `app/voz.py`, que es TUYO, y con cambio de forma pública:** `DetallePalabra` tiene un campo nuevo y obligatorio, **`fonema: str`**, restringido en el esquema de Structured Outputs (un `enum`) al inventario de `app/fonemas.py` más `"ninguno"` (`voz.SIN_FONEMA`); en pydantic se deja como `str` a propósito, para que un símbolo raro no tire la corrección entera. El prompt de `explicar_correccion` se reescribió: ancla cada sonido a una palabra del español y prohíbe «más fuerte/más suave» sin decir qué mover. **Módulo nuevo `app/fonemas.py`** (41 fonemas de General American, `normalizar`, `audio_de`, `ipa_de_palabra` sobre Kaikki sin spaCy) con sus mp3 versionados en `app/audio_fonemas/`, generados una vez con `tools/generar_fonemas.py` (registro en `tools/fonemas_generados.json`). En `ui.py`, solo `_practicar`, dos funciones que la ayudan y `RUTAS_PERMITIDAS`. Para el Space hacen falta los mp3 en la lista blanca y una regla `*.mp3` de LFS, que su `.gitattributes` no tiene: eso va en un commit aparte sobre `tools/desplegar_app.py`, pendiente de coordinar con quien lo está cambiando. `pruebas_extremas.py` pasa de 306 a **314**. **Sin desplegar.** |
| — | — | **12 sep, madrugada (Claude Code, sesión entrega-ef):** cierre de la **auditoría 18 de Codex** (`auditoria/informe_codex_18.md`: 2 serios y 2 menores, verificados todos) y de un fallo que destapó la prueba de voz de punta a punta. **Tocado otra vez `app/voz.py`, que es TUYO, con forma pública ampliada y compatible:** `Evaluacion` gana `entendidas: list[tuple[str, str]]`, pares (debía decir, se entendió; `""` si no se oyó) con valor por defecto, y `explicar_correccion(..., entendidas=None)` los mete en el prompt. Sin ellos el modelo adivinaba el sonido: con «fix» por «fox» culpaba a la /f/. En `ui.py`: `JS_AL_TEXTO` ya no desplaza al vencer el plazo, cancela la navegación anterior y cede al gesto del lector; «Otra frase» lleva `cancels=[ev_practicar]`; el relleno de los Markdown excluye los `gr.HTML` (`.html-container`); `_autor_corto` quita solo títulos de `_TITULOS_NOBILIARIOS` y conserva «Jr.», «II» y los paréntesis. **Tres sesiones en la misma carpeta esa noche** (entrega-ef: feedback de Laura y AFI; entrega-17: corpus graduados y **único desplegador**; entrega-e6: migración a Angular en `app/api.py` y `front/`): el protocolo está en `.claude/skills/trabajar-en-equipo/`. `pruebas_extremas.py` pasa a **318**. |
| — | — | **13 sep (Claude Code, sesión entrega-e6):** migración a Angular. **Archivos nuevos y míos: `app/api.py`, `front/`, `pruebas_api.py`**; no se tocó ningún módulo existente. `api.py` (FastAPI, 33 rutas en `/api`) **no reimplementa reglas: importa `ui.py`** y usa sus privadas `_puede_pagar`, `_codigo_de`, `_dentro_del_limite`, `_minutos_para_la_siguiente`, `_entrar`/`_salir`, `_dir_lector`/`_archivo_lector`, `_descargar_gutenberg`, `_esta_cacheado`, `_abrible`, `_analisis_guardado`/`_guardar_analisis`, `_filas_del_catalogo`, `_sinopsis_guardada`, `_oracion_de`, `_frase_del_capitulo`, `_humanizar`, `_autor_corto`, `_cefr` y `_muestra_de_libro`: **si cambias la firma o lo que devuelve alguna, avísalo**, porque la API se rompe en silencio igual que `ui.py`. La identidad del lector viaja en la cabecera `X-Lector` y hace de `session_hash`. `pruebas_api.py`: 22 pruebas, 6 de 6 mutantes cazados. `front/`: Angular 22 sin zone.js, `ng test` 3 de 3. **Space estático público `MikeMaki1763/literalevel-front`** (commit `8519d74`, con permiso de Miguel): solo el build, con la meta `literalevel-api` apuntando al Space de Gradio. **Montaje de la API en el Space de Gradio:** el primer intento (uvicorn propio con `api.con_gradio`, commit del Space `2eff61a`) dio 502/503 y se deshizo. Hugging Face arranca Gradio con SSR y su proxy de Node solo pasa a Python `/gradio_api`, `/config`, `/login` y pocos más; `/api` devolvía la página de Gradio con un 200. **El montaje bueno es `demo.launch(..., ssr_mode=False, app_kwargs=api.para_gradio())`** (commit `783c555`), probado imitando el arranque del Space. `con_gradio` queda solo para local. Tras desplegar, **mira el JSON de `/api/salud`, no el 200**. |
| — | — | **13 sep, tarde (Claude Code, sesión entrega-4e):** **tocado `app/lexicon.py`, que es TUYO, con campos públicos nuevos y compatibles** (al final, con valor por defecto) en `ResultadoLexico`: `traduccion`, `definicion_ia`, `generado_por_ia` y `acepcion_elegida_por_ia`. Tres cambios de comportamiento: (1) `_elegir_sentido` aparta las acepciones con etiquetas `_ETIQUETAS_MARGINALES` (obsolete, archaic, dated, rare…) si hay otra —con «mostly» ganaba una obsoleta—; (2) con elección dudosa, `_pedir_explicacion_openai` recibe `alternativas` y puede devolver `acepcion_usada`, que solo se acepta si coincide con una glosa del diccionario; (3) sin acepción utilizable y con cliente, `_pedir_definicion_ia` define la palabra y el resultado va marcado. La clave de caché de las explicaciones pasa a `contextual-v2` (traen traducción). Además, en `ui.py`: pestaña «Sonidos IPA» (antes «Sonidos AFI»), la ficha con traducción y marca de IA, y un botón de voz del navegador (Web Speech API, gratis) cuando la palabra no tiene audio. |
| — | — | **13 sep, 18:00 (Claude Code, sesión central):** **decisión de Miguel: la entrega es el front Angular** (`front/`, Space estático `literalevel-front`) sobre `app/api.py`; Gradio (`app/ui.py`) queda como motor y respaldo. **Ninguna función está terminada hasta que tiene ruta en `api.py` y pantalla en `front/`**: quien añada algo en `ui.py`, `voz.py` o `lexicon.py` avisa a la sesión de la API del contrato (campos, nombres) en el mismo mensaje del commit. Esa tarde hubo cuatro sesiones coordinadas por una central (protocolo en `.claude/skills/sesion-central/`): entrega-f4 desplegó cinco veces (último reinicio con 05783c0: animaciones 2D del corte de la boca, `app/animacion_articulatoria.py` en la lista blanca), entrega-e6 publicó el front cuatro veces (último bd3b06c), entrega-4e cerró la auditoría de Codex `auditoria/codex_lexicon_5033e69.md` (4 de 4 confirmados) y el fonema determinista con CMUdict. Codex se quedó sin cupo a las 17:10; volvió a las 21:40 **desde la app de Miguel, con permiso directo**, hizo 20 commits en master entre 20:51 y 21:51 (desplegó api.py y voz.py, integró la boca 3D en Pronunciar, reescribió guion y presentación, escribió `auditoria/relevo_codex_2026-09-13_noche.md` para la central) y agotó el cupo semanal hasta el 19 sep. **Madrugada del 14 sep (central):** cada dueño verificó lo de Codex en sus archivos; reinicios 7 y 8 (Space `c9ee482`, `8107f18`: todo el backend en LF e igual a HEAD `db366b8`); `tools/desplegar_app.py` compara y sube `git show <commit>:ruta` normalizado a LF (c675b93); avisos de contenido curados en `avisos_contenido.csv` (2 títulos) y `correcciones_catalogo.csv`; rama `boca3d` fusionada en master (ea7fdf2) pero **el 3D se publica apagado** por decisión de Miguel; guion del vídeo fusionado (db366b8, 496 palabras); documento y estrategia con cifras medidas (7a7613d, 81da225). Protocolo de la central en `.claude/skills/sesion-central/`. |
| — | — | **14 sep, mañana (central):** reinicios 9, 10 y 11 (Space `de36496` → `26b303c` → topes por hora). **Nuevo en el motor:** lectura natural en `app/voz.py` (marcas por palabra de whisper, `medir_ritmo`, análisis con OpenAI validado contra IPA de diccionario, `registrar_ritmo`/`evolucion_ritmo`, tabla `ritmo_intentos`), IPA y audio por forma escrita (Kaikki → CMU → lema si coincide → IA marcada) en `lexicon.py`, animación 2D explícita y al compás del audio (`animacion_articulatoria.py` con `dur`/`repetir`), palabras funcionales fuera de falladas, «sonido fácil» sin fonema. **API:** `/api/voz` devuelve `ritmo`, `GET /api/voz/ritmo`, `?dur=&una=` en los SVG, índice de PG1661, topes por hora en muestra/medir/curva con cola de 4 hilos. **Front:** boca 3D de Blender encendida (`boca3d/`, rig de comisuras, guarda de fps), «Escuchar y ver» pegado a la animación con «Más lento» (1×/0,5×/0,25×), pantalla de lectura natural, una mano en las cuatro pantallas. **Catálogo externo:** 3.919 → 15.357 textos libres medidos con v4 en CPU local (`tools/medir_corpus.py`, `tools/cerrar_corpus.py`; 894 sin medida por el filtro de prosa); `/api/estado` 68.536. **Sin gasto desde hoy:** Colab solo gratis, nada de compras; temporales y banco de mutantes en `D:`. |
| — | — | **14 sep, tarde (central):** reinicios 12 a 15 (Space `7c09d90`). Catálogo: libres intercalados por cercanía al nivel (un tercio de las tarjetas), `medido_en_bloque` en tarjeta y ficha, `ficha.para_medir` quita la atribución de los textos libres antes de puntuar (Doggie 0,35 → 0,007), texto servido limpio de U+FEFF y páginas dobles sin volver a medir. Front: portadas tipográficas por 12 familias de tema y lector teñido con contraste garantizado (ajuste para apagarlo), «Escuchar y ver» pegado a la boca con «Más lento», ruta `/api/portadas` para portadas por IA futuras. 3D: **cabeza de MakeHuman 1.3.0 (CC0, `tools/boca3d_blender/makehuman_cabeza.obj`)** con corte sagital, labios y mejillas por shape keys, arcada anatómica, sombras suaves; publicada en la app. Docs: `entrega/guion_demo_en_vivo.md`, diapositiva «Lo que hace por el lector», cifras del catálogo externo en documento/estrategia/presentación, `auditoria/bateria_lectura_natural_2026-09-14.md`, `auditoria/informe_codex_para_miguel_2026-09-13.md`. Lección: un commit de e6 arrastró líneas de f4 sin commit y HEAD dejó de medir media hora (ver skill sesion-central §7). Créditos de OpenAI repuestos por Miguel a mediodía. |
| — | — | **15 sep (Claude Code, sesión entrega-4e):** **tocados `app/voz.py` y `app/lexicon.py`, que son TUYOS** (`2c0e681`, va al reinicio 20). `SesionVoz.transcripcion_ok` es `False` también cuando whisper no oye ninguna palabra (antes solo con `None`), y entonces no se guardan fallos ni se piden audios por palabra; la API y Gradio, que guardan si `transcripcion_ok`, lo heredan. `lexicon._ipa_de_modelo` rechaza una IPA toda ASCII que sea la palabra escrita, o que llegue sin `palabra`. `voz._fronteras_de_frase` no corta en «Mr.», «Mrs.», «Ms.», «Dr.» ni «St.». Las dudas de «going to work» → gonna y del emparejado por orden en `fijar_fonemas` quedan escritas en el código, sin cambiar. **Módulo nuevo `pruebas_tmp.py` (`42de4cb`):** `carpeta(prefijo)` sustituye a `tempfile.mkdtemp` en las suites; crea bajo `LITERALEVEL_TMP` si está definida, borra al salir (lo que Windows retiene por un SQLite abierto lo borra un proceso aparte) y, al crear, borra las de su prefijo con más de 3 horas. **Quien escriba una suite nueva, que la use:** cada corrida dejaba ~100 MB en %TEMP% y C: llegó a 0 GB. |
| `app/scoring.py`, `app/perfil.py`, `app/catalogo.py`, `app/config.py` | compartido | Quien entre, avisa en el commit. |
| `modelo_v4/`, `kaikki_diccionario.db` | nadie | Datos. No se regeneran ni se versionan. |

**Si vas a cambiar la firma pública de un módulo, dilo en el mensaje de commit
en la primera línea.** `ui.py` depende de todas ellas y se rompe en silencio.

## Lo que no se toca

- **El modelo v4 es final y no se reentrena.** La fase es la interfaz.
- **Oxford Dictionaries está descartado** (sus claves dan HTTP 403). El
  diccionario es Kaikki/Wiktionary en SQLite local, sin límites de API. OpenAI
  aporta la explicación contextual y gramatical y la traducción, y **tiene
  prohibido redefinir una palabra que el diccionario trae**: como mucho, si la
  acepción elegida era dudosa, escoge OTRA acepción del diccionario. **Cambio de
  Miguel del 13 sep 2026:** si el diccionario no trae la palabra —o no trae
  ninguna acepción utilizable—, OpenAI la define, y la interfaz lo marca como
  «generada por IA».
- **`app/perfil.py` no puede llamarse `profile.py`**: taparía el módulo
  `profile` de la stdlib y rompe `import cProfile` dentro de torch.
- `CLAVES.txt` y `.env` llevan claves reales y están en `.gitignore`.

## Contrato entre módulos

Al día el 14 de septiembre de 2026 (HEAD `74ffffc`); cada nombre está comprobado
con `grep` en el código. Escalas: la **pública es 0..2** (la que ve el usuario y
la que consumen `catalogo`, `lexicon`, `perfil` y la API); la interna del modelo
es 0..5. `public_score(y) = clip(y,0,5)*0.4`.

**Motor**

- `scoring.Puntuador(ruta).puntuar(texto) -> Resultado` — lanza `ValueError`
  legible si no es prosa continua.
- `reader.cargar(ruta) -> Libro(titulo, autor, capitulos[])`
- `perfil.desde_cuestionario(dict) / desde_muestra(texto, puntuador) -> Perfil`.
  `perfil.HOLGURA` es la holgura de recomendación, la única.
- `ficha.miles(n) -> str` (separador de miles en español);
  `ficha.para_medir(texto) -> str` (sin licencia de Gutenberg ni atribución de
  un texto libre: solo para puntuar, lo que se enseña la conserva);
  `ficha.capitulos_de_cuerpo(libro) -> [(indice, capitulo)]` (el mismo filtro en
  Colab y en la app); `ficha.sinopsis(libro, cliente) -> (datos, causa)`, que
  nunca recibe el último capítulo.

**Catálogo** (`catalogo.Catalogo`)

- Filas: 53.179 libros de Gutenberg (`catalogo_medido.csv`) y 15.367 textos de
  licencia libre (`catalogo_externo.csv`, commit `a557288`): 68.546, que es lo
  que cuenta `/api/estado`. Cuéntalo con pandas: el campo `hook` lleva saltos de
  línea entrecomillados. El catálogo heredado de 1.197 se retiró el 12 sep.
- `buscar(consulta, nivel_lector=None, n=...) -> (libros, aviso)` — nunca
  devuelve vacío en silencio.
- `por_nivel(nivel_lector, holgura=0.25, n=10) -> list[Libro]` — fuera lo que no
  es lectura, solo obras literarias; los `PRIMEROS_SIN_AVISO` (5) primeros
  puestos sin aviso de contenido; un tercio de los puestos para textos libres,
  por cercanía al nivel (`_intercalar_libres`).
- `Libro`: `dificultad` (v4; `None` si es heredada), `aviso_contenido` (`""` si
  no hay; lista curada `avisos_contenido.csv`), `medida` (`"texto"`, `"bloque"`
  o `""` en Gutenberg) y la propiedad `medido_en_bloque`. `aviso_de(id) -> str |
  None` y `medida_de(id) -> str`. `correcciones_catalogo.csv` se aplica al cargar.

**Léxico** (`lexicon.ConsultorLexico`)

- `consultar(palabra_superficie, oracion, nivel, idioma="es", usar_openai=True)
  -> ResultadoLexico` — nunca lanza por falta de red o clave; lo que falte va en
  `.avisos`. `usar_openai=False` es **la puerta de pago**. `llamadas_de_pago` dice
  cuántas peticiones de pago salieron de verdad (no `desde_cache`).
- `ipa_uk`, `ipa_us`, `audio_uk`, `audio_us` son **de la forma escrita**: entrada
  de Kaikki de esa forma → CMUdict de la forma (americano) → el lema solo si
  coincide → lo que falte, OpenAI, con `ipa_generada_por_ia=True`.
- `traduccion`, `definicion_ia`, `generado_por_ia`, `acepcion_elegida_por_ia`;
  `acepciones_principales` (lista, solo con elección dudosa y sin explicación de
  OpenAI, y con dos o más); `compuesto` y `parte_del_diccionario` para los
  compuestos con guion que el diccionario no trae enteros.

**Voz** (`voz`)

- `practicar(ruta_audio, frase_objetivo, guardar_fallos=True, nivel=None) ->
  SesionVoz(evaluacion, correccion, audio_correcto, transcripcion_ok,
  audios_palabras, ritmo)`. La API y Gradio lo llaman con `guardar_fallos=False`
  y guardan ellos en la base de su lector.
- `medir_ritmo(evaluacion, tiempos_lector, tiempos_referencia, nivel) -> dict`
  con `medido`, `duracion_s`, `palabras`, `pausas`, `tramos` y `natural`;
  `analizar_natural(frase, palabras) -> dict | None` (énfasis, enlaces
  comprobados con IPA de diccionario, reducciones de `REDUCCIONES_CONOCIDAS`,
  versión natural), cacheado por frase.
- `registrar_fallos(palabras, ruta, frase)` no guarda palabras funcionales
  cortas; `registrar_ritmo(ritmo, frase, ruta)` solo guarda intentos medidos.
  Ninguno lanza.
- `palabras_para_practicar(n, ruta)`, `puntos_debiles(n, ruta)` y
  `evolucion_ritmo(frase, n, ruta)`: `[]` sin base; **`HistorialIlegible`**
  (`RuntimeError`) si la base existe y no se lee.

**Corte de la boca** (`animacion_articulatoria`)

- `svg_articulacion(simbolo, acento="ga", dur=None, repetir=True)` y
  `svg_palabra(ipa, acento="ga", dur=None, repetir=True)`: `dur` en segundos de
  0,3 a 30 (fuera, se ignora); `repetir=False` da una pasada y acaba en reposo.
  `svg_articulacion_quieto(simbolo, acento)` sin animación.

**Frontera HTTP** (`app/api.py`)

- La identidad del lector viaja en `X-Lector`. En el Space se monta con
  `demo.launch(ssr_mode=False, app_kwargs=api.para_gradio())`; `con_gradio()`
  es solo para local. La API importa ayudantes privados de `ui.py` (entre ellos
  `_fragmento_para_leer(oracion, palabra, tope=30)`): si cambias su firma, avisa.

Regla común: **degradación elegante**. Sin `OPENAI_API_KEY` la app funciona
(diccionario, IPA, audio de Wiktionary, buscador, puntuación y ficha no usan
red); lo que se apaga es la explicación contextual, las definiciones e IPA por
IA, la voz y el resumen.

## Arranque

```bash
python -X utf8 -m uvicorn app.api:app --host 127.0.0.1 --port 8000   # API para el front
cd front && npm.cmd ci && npm.cmd start       # Angular en :4200, /api por proxy.conf.json
python -X utf8 app/api.py                     # API + Gradio en un proceso (solo local)
python -X utf8 main.py                        # solo Gradio, el respaldo, en :7860
python -X utf8 validar_local.py               # la validación externa para el profesor
```

`ui.py` carga los tres recursos pesados (modelo 328 MB, embeddings del
catálogo, diccionario 243 MB + spaCy + MiniLM) **al primer uso, no al
arrancar**. No lo cambies a carga anticipada: la demo se vuelve inusable.

**Pruebas** (recuento del 14 sep 2026 en HEAD `74ffffc`; las filas con fecha llevan el commit sobre el que se corrieron; corridas con
`LITERALEVEL_SIN_CLAVES=1`, que no lee claves ni gasta):

| Suite | Qué cubre | Hoy |
|---|---|---|
| `tests_smoke.py` | bloques y escala, sin modelo | todo ok (no imprime recuento) |
| `pruebas_extremas.py` | robustez del motor y de Gradio | 349 de 349 (15 sep, `42de4cb`) |
| `pruebas_integracion.py` | recorrido completo encadenado | 27 pasos de 27 (15 sep, `42de4cb`) |
| `pruebas_desambiguacion.py` | acepciones, sin red | 8 de 8 |
| `pruebas_perfil.py` | cuestionario de nivel | todo ok (no imprime recuento) |
| `pruebas_ficha.py` | ficha, pasajes y capítulos de cuerpo | 49 comprobaciones, 0 fallos |
| `pruebas_corpus.py` | textos libres en catálogo y lector | 39 de 39 (15 sep, `40cdcd4`) |
| `pruebas_animacion.py` | corte 2D: SVG, duración y repetición | 2.109 comprobaciones, todo ok |
| `pruebas_voz_ritmo.py` | lectura natural con whisper y OpenAI simulados | 37 de 37 (15 sep, `2c0e681`) |
| `pruebas_voz_concurrencia.py` | voz: candados, migración e historial | 10 de 10 |
| `pruebas_audio_atomico.py` | caché y escritura atómica del TTS | 4 de 4 |
| `pruebas_api.py` | frontera HTTP para Angular | 55 de 55 (15 sep, `42de4cb`) |
| `pruebas_api_voz_temporal.py` | subida de audio a la API, por AST | pasa |
| `pruebas_portadas.py` | pipeline de portadas, sin GPU ni red | 11 de 11 |
| `pruebas_despliegue.py` | guardas del despliegue del Space | 13 de 13 |
| `pruebas_despliegue_front.py` | publicador del front, sin red | 16 de 16 |
| `pruebas_voz.py` | ciclo de voz; con clave llama a OpenAI | 16 comprobaciones sin red, todo ok (sin clave se omite el ciclo real) |
| `pruebas_lexicon.py --sin-openai` | diccionario real; sin la opción llama a OpenAI | todo ok con --sin-openai |

`pruebas_voz.py` y `pruebas_lexicon.py` sin `--sin-openai` llaman a OpenAI de
verdad si hay clave: no las corras en una revisión sin autorización de gasto.
Las pruebas del front son `npm.cmd test` dentro de `front/`.

## Antes de "arreglar" una llamada a una librería

Este stack va por delante de lo que cualquier modelo recuerda de memoria:
gradio **6.26**, transformers **5.16**, pandas **3.0**, openai **3.8**,
torch 2.14. Verifica la firma real antes de tocarla:

```bash
python -c "import gradio as gr, inspect; print(inspect.signature(gr.Blocks.launch))"
```

Caso comprobado: en Gradio 6 `theme` va en `launch()` y **ya no existe** en el
constructor de `Blocks`; `Textbox` tampoco acepta `show_copy_button`. El código
actual es correcto. Quien lo "corrija" de memoria hacia Gradio 4, lo rompe.

## Despliegue (punto 6, lo único que falta)

Consumo medido en local: **~1,05 GB de RSS** con el modelo y los embeddings
del catálogo cargados; con spaCy y el diccionario encima, pico realista de
**1,2-1,5 GB**. En disco, 576 MB (modelo 332 con su tokenizador + diccionario 243 + CSV 0,9).
Eso descarta cualquier plan de 512 MB (Render free, Koyeb free).

**Hugging Face cambió el tier gratuito a mediados de 2026.** La doc del Hub
dice literalmente: *"Static Spaces are free for everyone. Gradio and Docker
Spaces run on compute and require a paid plan to create: PRO for personal
accounts... Free personal accounts in good standing can still host up to 2
Gradio Spaces running on ZeroGPU."* La guía de Gradio y los artículos de
"pricing 2026" siguen diciendo que es gratis: **están desactualizados**.
CPU Basic es 2 vCPU / 16 GB RAM / 50 GB de disco efímero, y duerme por
inactividad.

Cuatro cosas que hay que resolver antes de subir, sea cual sea la plataforma:

1. ~~`app/` no es un paquete.~~ **RESUELTO:** el punto de entrada mete `app/`
   en `sys.path` y expone `demo`. **Corrección del 10 sep:** aquí decía «no lo
   renombres a `app.py`, chocaría con la carpeta `app/`», y es falso. El Space
   desplegado lleva **`app.py` en la raíz junto a la carpeta `app/`** y arranca
   sin problema, porque ese archivo nunca hace `import app`: mete `app/` en la
   ruta e importa `ui` directamente. En el Space el README declara
   `app_file: app.py`; `main.py` es el equivalente local y no está subido.
2. ~~La ruta del diccionario está clavada.~~ **RESUELTO:** `lexicon.py` lee
   `LITERALEVEL_DICCIONARIO` y cae al valor de siempre si no está. Igual que
   `LITERALEVEL_MODELO` para el modelo.
3. **Los 576 MB están en `.gitignore`** y deben seguir estándolo. Suben como
   repo de modelo y repo de dataset aparte, montados de solo lectura.
4. **Las cachés de `~/.literalevel/`** (lexicon y voz) son disco efímero en un
   Space: se borran en cada reinicio. Es aceptable porque son caché, pero la
   primera consulta tras cada despertar irá lenta.

## ~~Hallazgo abierto para Codex: la eleccion de acepcion falla~~ RESUELTO

Probando en la app real, `lexicon` eligio mal el sentido de **"peeped"** en
*"once or twice she had peeped into the book"*: se quedo con *"To speak briefly
with a quiet voice"* (afinidad **0.23** entre 6 acepciones) en lugar del sentido
de mirar. La explicación de OpenAI lo desmintió sola: *"la definicion dada es
otro sentido de peep y no aplica aqui"*.

O sea, `_elegir_sentido` con coseno sobre glosas cortas se queda sin senal
cuando las glosas son de pocas palabras. Ideas, sin tocarlo yo: comparar contra
`glosa + etiquetas + ejemplos` en vez de solo la glosa, o exigir un margen
minimo entre el primer y el segundo candidato antes de dar uno por bueno.

**RESUELTO en `927b826`** (Codex, verificado por Claude Code). Se enriquecen con
categoria y etiquetas solo las glosas de verbos; extenderlo a adjetivos empeoraba
casos como "free". El ranking enriquecido es interno y `similitud` conserva su
escala, así que `AFINIDAD_DUDOSA = 0.35` en `ui.py` sigue siendo válido. Cuando el
margen entre acepciones baja de 0.05, `lexicon` lo dice en `avisos`; en ese caso
`ui.py` no repite el aviso.

## Datos personales: uno por lector

En local todo vive en `~/.literalevel`. **Desplegada, la app es un solo proceso
para todos los visitantes**, así que `cuaderno.db`, `voz.db`, `perfil.json` y
`sesion.json` se resuelven por sesion de navegador con `_dir_lector(peticion)`
(`ui.py`), que usa `gr.Request.session_hash`. Sin eso, quien entraba se
encontraba el libro que subió otro: `demo.load` corre en cada carga de página.

`lexicon.db` **sí** se comparte y debe seguir así: es caché de definiciones, no
historial, y compartirla ahorra dinero.

Si añades un manejador que escriba o lea datos del lector, dale
`peticion: gr.Request = None` como último parámetro (Gradio lo inyecta solo) y
saca la ruta con `_archivo_lector("loquesea", peticion)`. No uses rutas fijas.

**Y la excepción, que costó un fallo crítico:** «último parámetro» solo vale si
no hay ningún `*args` delante. Gradio inyecta el `Request` únicamente en
parámetros **posicionales**, y su `special_args` corta el recorrido de la firma
en el primero que no lo sea, así que un `peticion` detrás de un `*valores` es
keyword-only, **no se inspecciona nunca y llega `None` siempre**. Eso mandaba el
perfil del cuestionario a `lectores/anonimo/`, una sola carpeta para todos los
visitantes del Space. Si tu manejador recibe `*args`, pon `peticion` **antes**:
`special_args` inserta el Request en el índice de su parámetro, así que las
entradas siguen alineadas. Lo comprueba la prueba «todos los manejadores reciben
la peticion», que pasa cada firma por el `special_args` real.

## Nunca subas el proyecto con upload_folder

`huggingface_hub.upload_folder` **no lee `.gitignore`** (dicho en su propio
docstring). Un `upload_folder(folder_path=".")` subiria `CLAVES.txt` y `.env` a
un repositorio público. El Space se sube con `git push`, o con
`ignore_patterns=[".env", "CLAVES.txt", "*.env"]` explicito.

## Rendimiento: donde se va el tiempo (medido, 7 sep 2026)

**Ningun recurso pesado es caro. Lo caro es importar el stack**, y se paga una
sola vez en el primer clic sea cual sea: torch 2,9 s + transformers 2,1 s +
resolver las clases `Auto*` 5,4 s + sentence_transformers 0,8 s + spaCy 0,5 s
= **~11,8 s**. El marginal de cada recurso es pequeno: Puntuador 0,74 s,
catalogo 3,06 s (casi todo el modelo multilingue), consultor 1,6 s.

**Casi todo el tiempo de una consulta léxica es espera a OpenAI.** La explicación
contextual esta medida en **14,9 s** con `reasoning.effort="low"`, que es el que
corre, y en 67,7 s con el esfuerzo medio de antes. El trabajo local -spaCy,
SQLite, desambiguación, IPA- son **40 ms** en caliente. (Aquí decía "de los 28-44
s, 23-39 son espera": era de antes de bajar el esfuerzo.)
Por eso `_consultar` es generadora: la primera etapa sale al instante.

Medido y **descartado**, para que nadie lo reintente:

- spaCy con tuberias desactivadas ahorra 0,13 s. Solo se puede quitar el NER:
  `_resolver_lema_y_categoria` usa `.lemma_`, `.pos_` y `.dep_`.
- El SQLite de Kaikki ya abre en `mode=ro` y ya tiene `idx_palabra`; la
  primera SELECT sobre 1.487.639 filas tarda **0,001 s**. Los 243 MB son
  inocentes.
- Cambiar el multilingue del catalogo por MiniLM-L6 ahorraria 2,4 s pero
  **rompe la busqueda**: el lector describe en espanol y el catalogo esta en
  ingles. No se toca.

~~Pendiente para Codex~~ **HECHO**: la llamada de `lexicon.py` ya va con
`reasoning.effort="low"` (`ESFUERZO_RAZONAMIENTO`, usado en la llamada). Medido
sobre tres palabras reales: 67,7 s con el esfuerzo medio, **14,9 s con `low`**,
7,4 s con `minimal`. Se queda en `low` y **`minimal` esta descartado**: con el,
"had peeped" se explico como pasado simple cuando es pasado perfecto, y el
análisis gramatical es justo lo que se evalúa.
