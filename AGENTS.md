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
| `app/scoring.py`, `app/perfil.py`, `app/catalogo.py`, `app/config.py` | compartido | Quien entre, avisa en el commit. |
| `modelo_v4/`, `kaikki_diccionario.db` | nadie | Datos. No se regeneran ni se versionan. |

**Si vas a cambiar la firma pública de un módulo, dilo en el mensaje de commit
en la primera línea.** `ui.py` depende de todas ellas y se rompe en silencio.

## Lo que no se toca

- **El modelo v4 es final y no se reentrena.** La fase es la interfaz.
- **Oxford Dictionaries está descartado** (sus claves dan HTTP 403). El
  diccionario es Kaikki/Wiktionary en SQLite local, sin límites de API. OpenAI
  solo aporta la explicación contextual y gramatical: tiene prohibido
  redefinir la palabra.
- **`app/perfil.py` no puede llamarse `profile.py`**: taparía el módulo
  `profile` de la stdlib y rompe `import cProfile` dentro de torch.
- `CLAVES.txt` y `.env` llevan claves reales y están en `.gitignore`.

## Contrato entre módulos

Escalas: la **pública es 0..2** (la que ve el usuario y la que consumen
`catalogo.buscar`, `lexicon.consultar` y `perfil.Perfil.nivel`); la interna del
modelo es 0..5. `public_score(y) = clip(y,0,5)*0.4`.

- `scoring.Puntuador(ruta).puntuar(texto) -> Resultado` — lanza `ValueError`
  legible si no es prosa continua.
- `reader.cargar(ruta) -> Libro(titulo, autor, capitulos[])`
- `perfil.desde_cuestionario(dict) / desde_muestra(texto, puntuador) -> Perfil`
- `catalogo.Catalogo().buscar(consulta, nivel_lector, n) -> (libros, aviso)` —
  nunca devuelve vacío en silencio. **El catálogo son 1197 libros, no 12752**:
  `wc -l` engaña porque el campo `hook` lleva saltos de línea entrecomillados.
  Cuéntalo con pandas. **Corrección:** antes decía aquí que el sesgo hacia A1
  era deliberado. Era una suposición mía y es falsa. Las etiquetas salieron
  del modelo v1 aplicado a las primeras ~190 palabras de cada obra, con
  cortes CEFR por cuantiles; el propio cuaderno del proyecto concluyó que esa
  correspondencia no se sostiene. Reparto real: A1 723, A2 185, B1 69, B2 52,
  C1 53, C2 115. El tramo B1-B2, donde está la mayoría de los lectores, son
  121 libros de 1.197.
- `lexicon.ConsultorLexico().consultar(palabra, oracion, nivel, usar_openai=True) -> ResultadoLexico`
  — nunca lanza por falta de red o clave; lo que falte va en `.avisos`. `usar_openai=False` es **la puerta de pago**: no construye cliente y no sale nada a la red. `ResultadoLexico.llamadas_de_pago` dice cuántas peticiones de pago salieron de verdad, y es lo que `ui` mira para devolver el uso del cupo — **no `desde_cache`**, que solo habla de la explicación contextual.
- `perfil.HOLGURA` — la holgura de recomendación, la única. La lee `ui.HOLGURA_POR_NIVEL` y la anuncia `perfil.describir`.
- `ficha.miles(n) -> str` — separador de miles en español (1.197). `f"{n:,}"` pone la coma, que aquí es el separador decimal.
- `voz.practicar(ruta_audio, frase) -> SesionVoz`

Regla común: **degradación elegante**. Sin `OPENAI_API_KEY` la app funciona
(diccionario, IPA, audio de Wiktionary, buscador y puntuación no usan red); lo
que se apaga es la explicación contextual y la voz.

## Arranque

```bash
python -X utf8 app/ui.py      # la app
python -X utf8 tests_smoke.py       # lógica sin modelo
python -X utf8 validar_local.py     # la prueba para el profesor
python -X utf8 pruebas_voz.py
python -X utf8 pruebas_lexicon.py
```

`ui.py` carga los tres recursos pesados (modelo 328 MB, embeddings del
catálogo, diccionario 243 MB + spaCy + MiniLM) **al primer uso, no al
arrancar**. No lo cambies a carga anticipada: la demo se vuelve inusable.

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
