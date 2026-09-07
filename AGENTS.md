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
**1,2-1,5 GB**. En disco, 562 MB (modelo 328 + diccionario 233 + CSV 0,9).
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

1. ~~`app/` no es un paquete.~~ **RESUELTO:** `main.py` en la raíz mete `app/`
   en `sys.path` y expone `demo`. **No lo renombres a `app.py`**: chocaría con
   la carpeta `app/`. En un Space hay que declararlo en el README:
   `app_file: main.py`.
2. ~~La ruta del diccionario está clavada.~~ **RESUELTO:** `lexicon.py` lee
   `LITERALEVEL_DICCIONARIO` y cae al valor de siempre si no está. Igual que
   `LITERALEVEL_MODELO` para el modelo.
3. **Los 562 MB están en `.gitignore`** y deben seguir estándolo. Suben como
   repo de modelo y repo de dataset aparte, montados de solo lectura.
4. **Las cachés de `~/.literalevel/`** (lexicon y voz) son disco efímero en un
   Space: se borran en cada reinicio. Es aceptable porque son caché, pero la
   primera consulta tras cada despertar irá lenta.

## ~~Hallazgo abierto para Codex: la eleccion de acepcion falla~~ RESUELTO

Probando en la app real, `lexicon` eligio mal el sentido de **"peeped"** en
*"once or twice she had peeped into the book"*: se quedo con *"To speak briefly
with a quiet voice"* (afinidad **0.23** entre 6 acepciones) en lugar del sentido
de mirar. La explicacion de OpenAI lo desmintio sola: *"la definicion dada es
otro sentido de peep y no aplica aqui"*.

O sea, `_elegir_sentido` con coseno sobre glosas cortas se queda sin senal
cuando las glosas son de pocas palabras. Ideas, sin tocarlo yo: comparar contra
`glosa + etiquetas + ejemplos` en vez de solo la glosa, o exigir un margen
minimo entre el primer y el segundo candidato antes de dar uno por bueno.

**RESUELTO en `927b826`** (Codex, verificado por Claude Code). Se enriquecen con
categoria y etiquetas solo las glosas de verbos; extenderlo a adjetivos empeoraba
casos como "free". El ranking enriquecido es interno y `similitud` conserva su
escala, asi que `AFINIDAD_DUDOSA = 0.35` en `ui.py` sigue siendo valido. Cuando el
margen entre acepciones baja de 0.05, `lexicon` lo dice en `avisos`; en ese caso
`ui.py` no repite el aviso.

## Datos personales: uno por lector

En local todo vive en `~/.literalevel`. **Desplegada, la app es un solo proceso
para todos los visitantes**, asi que `cuaderno.db`, `voz.db`, `perfil.json` y
`sesion.json` se resuelven por sesion de navegador con `_dir_lector(peticion)`
(`ui.py`), que usa `gr.Request.session_hash`. Sin eso, quien entraba se
encontraba el libro que subio otro: `demo.load` corre en cada carga de pagina.

`lexicon.db` **si** se comparte y debe seguir asi: es cache de definiciones, no
historial, y compartirla ahorra dinero.

Si anades un manejador que escriba o lea datos del lector, dale
`peticion: gr.Request = None` como ultimo parametro (Gradio lo inyecta solo) y
saca la ruta con `_archivo_lector("loquesea", peticion)`. No uses rutas fijas.

## Nunca subas el proyecto con upload_folder

`huggingface_hub.upload_folder` **no lee `.gitignore`** (dicho en su propio
docstring). Un `upload_folder(folder_path=".")` subiria `CLAVES.txt` y `.env` a
un repositorio publico. El Space se sube con `git push`, o con
`ignore_patterns=[".env", "CLAVES.txt", "*.env"]` explicito.

## Rendimiento: donde se va el tiempo (medido, 7 sep 2026)

**Ningun recurso pesado es caro. Lo caro es importar el stack**, y se paga una
sola vez en el primer clic sea cual sea: torch 2,9 s + transformers 2,1 s +
resolver las clases `Auto*` 5,4 s + sentence_transformers 0,8 s + spaCy 0,5 s
= **~11,8 s**. El marginal de cada recurso es pequeno: Puntuador 0,74 s,
catalogo 3,06 s (casi todo el modelo multilingue), consultor 1,6 s.

**De los 28-44 s de una consulta lexica, 23-39 s son espera a OpenAI.** Todo el
trabajo local -spaCy, SQLite, desambiguacion, IPA- son **40 ms** en caliente.
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

Pendiente para Codex, sin hacer: la llamada de `lexicon.py` va sin
`reasoning.effort`, o sea esfuerzo medio para cuatro campos cortos de
Structured Outputs. Probar `low` podria quitar 10-20 s, pero hay que
comprobar que no cae la calidad, porque la regla de "OpenAI no redefine la
palabra" depende de que siga las instrucciones al pie de la letra.
