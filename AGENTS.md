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
- `lexicon.ConsultorLexico().consultar(palabra, oracion, nivel) -> ResultadoLexico`
  — nunca lanza por falta de red o clave; lo que falte va en `.avisos`.
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
