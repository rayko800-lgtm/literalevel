# Auditoría 15 (Fable) — la última antes del vídeo

**Fecha:** 11 de septiembre de 2026. **Alcance:** el árbol local de
`C:\Users\laura\literalevel` tal como está (sin `git log`, sin leer
`auditoria/`), el Space `MikeMaki1763/literalevel` cotejado por HTTP, los
entregables de `entrega/`, `README.md` y `PENDIENTES.md`, y la aplicación
abierta en un navegador como la abre un visitante. **No se gastó dinero:**
todas las suites y la app corrieron sin `OPENAI_API_KEY` y con `config.cargar`
anulado; el único cliente de OpenAI que se construyó fue el espía de
`pruebas_lexicon.py`.

**Nada de este informe modifica el repositorio.** Los archivos auxiliares
viven en el scratchpad con prefijo `f15_` (`f15_banco.py`, `f15_mutantes.json`,
`f15_directos.py`, `f15_app.py`, y los `f15_*.log`).

---

## 0. Resumen en diez líneas

1. **El control pasa entero** antes de mutar: 272 extremas, 27 pasos,
   `tests_smoke`, `pruebas_ficha`, `pruebas_perfil`, y además
   `pruebas_lexicon --sin-openai`, `pruebas_desambiguacion` (7),
   `pruebas_audio_atomico` (4) y `pruebas_voz` (parte local), todas en verde
   con la red cortada.
2. **Las cifras publicadas cuadran consigo mismas y con los guiones**:
   `validar_local.py` reproduce hoy 47 · 0,5040 · 0,5561 · 0,9276 · 1,2414 ·
   1,4952 · 0,860 · 0,807 · 0,668 · 0,732 · 36; `tools/contar_guion.py` da 570
   palabras y 3:48; el cuadernillo corre entero en un venv limpio con
   `exit=0` y reproduce el Cuadro 7 (0,313/1,295 · 0,352/1,061 · 0,340/1,081);
   el peor contraste es 4,53 y 3,11 sobre 85 parejas; los 14 archivos de
   código del Space son **idénticos byte a byte** a los locales.
3. **El dinero está bien cerrado**: no encontré ningún camino a la API que
   salte la puerta, y el cupo baja si y solo si se gasta en los caminos que
   ejercité (con perfil y sin clave, `uso_openai.json` queda en `0`).
4. **Los datos de cada lector están bien separados**: dos navegadores
   aislados no se ven el perfil, el libro ni las palabras; `/gradio_api/file=`
   sirve solo la carpeta de audio (403 a `cuaderno.db`, `perfil.json`,
   `lexicon.db`, `.env`, `requirements.txt`).
5. **Lo que sigue mal es lo que se ve en la demo**, no lo que miden las
   suites: el libro de la demo no está en el catálogo ni en Gutenberg y es
   una traducción con *copyright* de 2015; la pantalla dice 129.589 palabras
   donde el guion dice 130.104; la primera palabra del prólogo sale con la
   acepción del pez; la frase para pronunciar es «on the afternoon of May 7,
   1915.»; y «Sorpréndeme» propone un B2 que el modelo mide C1 al clic
   siguiente.
6. **De 30 mutantes propios, 22 sobrevivieron** (8 cazados por su prueba,
   ninguno por otra; tabla en §3). Los que más pesan: nadie prueba que el perfil de pago con el que entra un visitante no
   valga para todos, ni que «Mis libros», los fallos de voz o el perfil por
   muestra sean de cada lector, ni que el recorte a 0–5 vaya por bloque, ni
   que `MAX_BLOCKS_PER_DOC`/`BLOCK_WORDS` valgan lo que dice el documento.
7. **Dos manejadores levantan hacia Gradio** con archivos que la propia app
   escribe: `_de_que_trata` con una sinopsis cuyo campo de texto sea lista, y
   `_analizar_libro` con `NaN`/`1e400` en el análisis guardado.
8. La prosa está limpia salvo una celda del cuadernillo (§7.2) con negritas
   anidadas y sin acentos, y un recuento de correcciones que baila entre
   seis, ocho y nueve según el archivo.
9. `PENDIENTES.md` va por detrás del repositorio en tres líneas.
10. La pregunta del final (§5) está contestada con lo que vi en pantalla, no
    con lo que dicen las pruebas.

---

## 1. Hallazgos

Convención: **CRÍTICO** = se ve en la demo o cuesta dinero; **SERIO** = se ve
en una lectura atenta del PDF, o una red de pruebas que deja pasar un fallo
ya corregido; **MENOR** = cosmético o de mantenimiento. «Sospecha» = sin
salida reproducida.

### S1 · SERIO · El libro de la demo no sale del recorrido que el documento describe, y tiene derechos

**Dónde:** `entrega/documento.md:916-953` (§8.2), `entrega/documento.tex:2193`,
`entrega/guion_video.md:99-118`, `entrega/presentacion.tex:293,309`.

**Cita:** `documento.md:932`: «2. Abre el libro. Se descarga de Project
Gutenberg y se abre dentro de la aplicación, sin salir a buscarlo.» y
`documento.md:950`: «Sobre *Notes from a Dead House*, el modelo recorre **487
ventanas de 130.104 palabras en 86 segundos**». `guion_video.md:112-114`:
«escribo *dostoyevski* mal escrito, y aun así lo encuentra. **Tres.** Abro
*Notes from a Dead House* y aparece su ficha».

**Qué falla.** *Notes from a Dead House* no está en el catálogo ni en Project
Gutenberg (Gutenberg tiene *The House of the Dead*, traducción de Garnett; el
título *Notes from a Dead House* es el de la traducción de Pevear y
Volokhonsky, Knopf, 2015). El archivo con el que se midieron las cifras es
`~/Downloads/dokumen.pub_notes-from-a-dead-house.epub`, cuyo OPF declara
`dc:rights = Copyright © 2015 by Richard Pevear and Larissa Volokhonsky` y
`dc:publisher = Alfred A. Knopf`. O sea: el paso 2 del recorrido (descargar de
Gutenberg) no puede producir el libro de los pasos 3 y 4; en la app hay que
subirlo a mano en «Leer». Y un documento que dedica párrafos a que «ningún
texto con derechos se distribuye» enseña en el vídeo, en la diapositiva 8 y
en el §8.2 un epub pirateado de una traducción con derechos vigentes.

**Reproducción:**

```
$ python - (catálogo y buscador real, HF offline)
[dostoyevski] aviso=''
   PG28054      B2  sim=0.77 The Brothers Karamazov — Dostoyevsky, Fyodor
   PG2638       B2  sim=0.77 The Idiot — Dostoyevsky, Fyodor
   PG600        C1  sim=0.77 Notes from the Underground — Dostoyevsky, Fyodor
   PG2554       C1  sim=0.77 Crime and Punishment — Dostoyevsky, Fyodor
   abribles: ['PG28054', 'PG2638', 'PG600', 'PG2554', 'PG13415']
$ (metadatos del epub)
dc:title ['Notes from a Dead House']
dc:creator ['Fyodor Dostoevsky', 'Richard Pevear', 'Larissa Volokhonsky']
dc:publisher ['Alfred A. Knopf']   dc:date ['2015-03-23...']
dc:rights ['Copyright © 2015 by Richard Pevear and Larissa Volokhonsky']
```

**Arreglo.** Antes de grabar, elegir para el recorrido un libro que el
buscador de verdad devuelve y que se abre con «Leerlo ahora» —*Crime and
Punishment* (PG2554) o *The Brothers Karamazov* (PG28054) son Dostoyevski y
están cacheados— y remedir con él las cinco cifras del guion (palabras,
ventanas, segundos, media, 40 ms). Si se conserva *Dead House*, decir en
§8.2 que se **sube** un epub propio (no que se descarga) y no enseñar en
cámara la portada de una edición con derechos. Es la misma regla que el
documento aplica a British Council.

### S2 · SERIO · La pantalla del libro dice 129.589 palabras y el guion dice 130.104

**Dónde:** `app/ui.py:1322` (cabecera), `app/ui.py:1645,1660,1672` (`"palabras":
libro.palabras` en el análisis), `app/ui.py:2008` (resumen de la curva);
`entrega/guion_video.md:100,115`, `documento.md:950`, `presentacion.tex:309`.

**Cita:** `ui.py:1322`: `palabras = ficha.caracteristicas(libro).palabras or
libro.palabras` frente a `ui.py:1660`: `"palabras": libro.palabras, "ventanas":
ventanas,`. `guion_video.md:115`: «aparece su ficha, contada sobre el texto y
no sobre la portada: **130.104 palabras**».

**Qué falla.** La corrección «la pantalla del libro no se contradice» alineó
cabecera y ficha (las dos descuentan la licencia y la portadilla), pero el
resumen de la curva sigue imprimiendo `libro.palabras` crudo. Con el libro de
la demo la misma pantalla dice **129.589** arriba y en la ficha, y «sobre
**130.104** en total» debajo de la gráfica. Y la cifra que se dice a cámara y
la que está en el PDF y en la diapositiva es la que **no** aparece en la
ficha.

**Reproducción** (`ui._abrir` y `ui._resumen_analisis` sobre el epub):

```
CABECERA : **Notes from a Dead House** — Fyodor Dostoevsky · 30 capítulos · 129.589 palabras
FICHA    : - **129.589 palabras** en 30 capítulos · entre 12 h y 19 h 38 min de lectura
RESUMEN  : **1.73 / 2.00** (avanzado) · orientativo **C1** de media, medido leyendo **487 ventanas** de 250 palabras sobre 130.104 en total.
```

Las 487 ventanas sí cuadran (21 capítulos de cuerpo, `fixed_blocks` sin
tope). La prueba `_la_pantalla_del_libro_no_se_contradice`
(`pruebas_extremas.py:3824`) compara cabecera con ficha y no mira el resumen
del análisis, por eso no lo caza.

**Arreglo.** Usar en los tres `datos = {... "palabras": ...}` de
`_analizar_libro` el mismo recuento descontado que la cabecera (o guardar los
dos y decir cuál es cuál), y cambiar el guion, el §8.2 y la diapositiva a la
cifra que la ficha enseña. Añadir el resumen a la prueba de la pantalla.

### S3 · SERIO · La primera palabra consultada del prólogo sale con la acepción del pez, sin aviso, y así se guarda en «Mis palabras»

**Dónde:** `app/lexicon.py` (`_elegir_sentido`), `app/ui.py:2094`
(`AFINIDAD_DUDOSA = 0.35`), `app/ui.py:2124-2126` (aviso «pronunciación de
arriba está generada»), `app/ui.py:2636` (tarjeta del cuaderno).

**Qué falla.** Sin clave (el caso de todo visitante que no entre con perfil),
la ficha de «torpedoes» en el prólogo de *The Secret Adversary* dice:

```
torpedoes · torpedo · noun
Diccionario (Wiktionary): An electric ray of the genus Torpedo.
Elegido entre 15 acepciones, afinidad 0.38.
[!] El diccionario no trae audio de esta palabra, así que la pronunciación de arriba está generada.
[!] Sin clave de OpenAI: no hay explicación de contexto. El resto de la ficha no la necesita.
> The Lusitania had been struck by two torpedoes in succession ...
```

Tres cosas a la vez: (a) la acepción es la del pez eléctrico, en una frase
sobre un barco torpedeado; (b) 0,38 está por encima de `AFINIDAD_DUDOSA` así
que no sale ningún aviso de duda; (c) el aviso habla de «la pronunciación de
arriba» cuando **no hay ninguna** —sin clave no se genera audio y la palabra
tampoco tiene IPA—, porque `_humanizar` traduce «sin audio en el diccionario»
dando por hecho que hubo tts-1. La acepción errónea se guarda en el cuaderno
del lector y así sale en «Mis palabras» y en «Repasa 5»:

```
1 palabras distintas, en 1 consultas sobre 1 libro.
torpedoes · poco frecuente · The Secret Adversary, cap. 3
The Lusitania had been struck by two torpedoes in succession ...
An electric ray of the genus Torpedo.
```

Medido sobre 15 palabras del mismo prólogo (`f15_lex`): 6 acepciones
equivocadas —torpedoes (pez), rebuff («To buff again»), packet (paquete de
red), flushed (tirar de la cadena), nerve (estructuras neurales), starboard
(etiquetado verbo)—; de ellas, **torpedoes y starboard sin ningún aviso**,
las otras cuatro con «La acepción elegida es dudosa» o «Poca confianza».

**Arreglo.** No es de un día: subir `AFINIDAD_DUDOSA` a 0,40 haría avisar en
«torpedoes» (0,38) y «flushed» (0,39) sin tocar `lexicon`; y el aviso de
audio debe distinguir «no hay audio y no se generó» (sin clave) de «se generó
con tts-1». Para el vídeo: elegir de antemano las palabras que se van a tocar.

### S4 · SERIO · La frase para pronunciar y la oración de contexto son fragmentos cuando hay «Mr.», «Mrs.» o «p.m.»

**Dónde:** `app/scoring.py:40` (`SENT_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")`),
`app/ui.py:2436` (`_frase_del_capitulo`), `app/ui.py:2044` (`_oracion_de`).

**Qué falla.** `SENT_RE` corta en cada punto, también en abreviaturas. En la
app, «Traer una frase del capítulo que estoy leyendo» sobre el prólogo de *The
Secret Adversary* rellenó la caja con:

```
Frase que vas a leer en voz alta: "on the afternoon of May 7, 1915."
```

(la primera frase del libro es «It was 2 p.m. on the afternoon of May 7,
1915.»). Medido sobre cuatro libros cacheados (candidatas de 6–25 palabras,
fragmento = empieza en minúscula o sigue a una abreviatura):

```
Secret Adversary       candidatas   3056 | fragmentos   116 (3.8%)
Pride and Prejudice    candidatas   3562 | fragmentos   467 (13.1%)
Alice                  candidatas    487 | fragmentos    17 (3.5%)
Crime and Punishment   candidatas   7653 | fragmentos   335 (4.4%)
primeras frases que ofrece el botón (P&P): ['Walt Whitman has somewhere a fine...', '“Why, my dear, you must know, Mrs.', ...]
primeras frases que ofrece el botón (Alice): ['” thought Alice to herself, “after such a fall as...', ...]
```

Y `_oracion_de` usa el mismo partidor, así que el contexto que se cita en la
ficha —y el que **viaja a OpenAI** en la explicación de pago— también se
rompe: en *Pride and Prejudice* (el libro más descargado del catálogo, 31.755)
consultar «Netherfield» da como contexto
`'Bennet,” said his lady to him one day, “have you heard that Netherfield Park is let at last?'`
y «Bingley», `'All the minor passages—the loves of Jane and Bingley, the advent of Mr.'`.
Ninguna prueba lo mira: `pruebas_integracion.py:186` solo exige entre 6 y 25
palabras.

**Arreglo.** No tocar `SENT_RE` en `scoring` (es del entrenamiento) sino
partir en `ui` con una regla que respete abreviaturas (`Mr.`, `Mrs.`, `Dr.`,
`St.`, `p.m.`, `a.m.`) y descartar candidatas que empiecen en minúscula o con
comilla de cierre. Para el vídeo: la frase del paso cinco, escrita a mano.

### S5 · SERIO · «Sorpréndeme» propone un B2 que el modelo mide C1 al clic siguiente

**Dónde:** `app/ui.py` (`_recomendar` → `catalogo.por_nivel` sobre
`nivel_cefr` heredado), `catalogo_recomendaciones.csv`.

**Qué se ve.** Con perfil 1,20 (el del guion), «Ver libros para mi nivel →»
lista diez títulos, todos B2 («Lo más leído entre 0.95 y 1.45»). Abrí *The
Secret Adversary* (B2) y pulsé «¿Cómo de difícil es este capítulo?» y
«Vistazo rápido»:

```
1.50 / 2.00 (avanzado) · orientativo C1 · 3 bloques · confianza alta
1.77 / 2.00 (avanzado) · orientativo C1 de media, vistazo rápido: 58 ventanas de 250 palabras tomadas de 29 capítulos.
```

El documento ya declara que las etiquetas del catálogo no son fiables
(Cuadro 3, limitación 3), pero en una demo en vivo esto es la recomendación
de la app desmentida por la app cuatro clics después. De los 148 abribles,
124 llevan etiqueta C1 o C2 y solo 12 llevan B2; el único B2 que medí
(Christie) da 1,50 en el prólogo y 1,77 de media en el vistazo. No es un
fallo nuevo; es el que más se nota.

**Arreglo para el fin de semana:** no usar «Sorpréndeme» en el vídeo, o
decir en voz alta que la etiqueta es heredada y que el número es el del
modelo. A medio plazo, A3.

### S6 · SERIO (red de pruebas) · Veintidós de treinta mutantes sobreviven; los que importan son de dinero y de datos

Detalle y tabla en §3. Resumen de lo que ninguna prueba caza:

- `_sesion_de` devolviendo `"local"` para todos (`ui.py:291-306`): el perfil
  de pago con el que entra un visitante pasa a valer para **todos** los
  visitantes del Space. 272 extremas en verde. Ninguna prueba entra con dos
  sesiones distintas y comprueba que la segunda no herede el perfil.
- `_mis_libros`, `_debiles`, `_practicar` (voz.db) y `_abrir` (biblioteca)
  sin `peticion` (`ui.py:2706,2581,2538,1334`): estanterías y fallos de voz
  compartidos entre visitantes. La prueba de aislamiento
  (`pruebas_extremas.py:558` y `:3921`) recorre perfil, marcapáginas y
  cuaderno; no la biblioteca ni la voz. Y la prueba regex de
  `pruebas_extremas.py:728` se salta justo al manejador que deja de pasar la
  petición, como su propio docstring reconoce.
- `_desde_muestra` guardando el perfil en `anonimo/` (`ui.py:677`): el
  cuestionario está cubierto; «pega un fragmento» no.
- Los dos `cuentas.devolver` de `_de_que_trata` en `ui.py:1807` (falló el
  constructor del consultor) y `ui.py:1822` (`sin_red`/`sin_pasajes`):
  quitarlos cobra un uso por un botón que no salió a la red.
  `_el_cupo_cuadra_con_las_llamadas_de_pago` (`pruebas_extremas.py:2307`)
  dice en `:2387` que prueba «`_de_que_trata` sin diccionario», pero en esta
  máquina el diccionario existe, el espía **sí** recibe la llamada y la rama
  ejercitada es «falló tras salir → se cobra», que es otra.
- `np.clip` por bloque en `scoring.py:344`: el documento §2.1 dedica un
  párrafo a que «el recorte va dentro del sumatorio, que es lo que hace el
  código». Quitarlo pasa las 272 extremas, los 27 pasos y `tests_smoke`.
- `MAX_BLOCKS_PER_DOC = 800` y `BLOCK_WORDS = 200` (`scoring.py:19-21`):
  `tests_smoke.py:47-48` asevera contra la propia constante (`<=
  sc.MAX_BLOCKS_PER_DOC`, `== sc.BLOCK_WORDS`), así que cualquier valor pasa.
  Son constantes del entrenamiento y el documento las publica (250 / 150 / 8).
- `HOLGURA = 0.5` (`perfil.py:33`): las tres pruebas que la miran leen
  `ui.HOLGURA_POR_NIVEL`, que es la misma variable.
- Y las promesas del documento que ninguna prueba sostiene: T5 en el botón
  de medir el capítulo (`ui.py:1405`, la licencia vuelve a puntuarse), T6 en
  los `.txt` (`reader.py:226`, la portada vuelve a ser capítulo), T8 en la voz
  (`ui.py:2513`, la frase viaja sin recorte) y en la sinopsis (`ficha.py:296`,
  90.000 palabras por pasaje pasan), la casilla «Acercar los resultados a mi
  nivel» (`catalogo.py:226`, con peso 0 no acerca nada), el vistazo que
  «muestrea 30 capítulos» (`ui.py:1618`), la rotación de frases de voz
  (`ui.py:2448`), la tabla A1–C2 que ve el lector (`ui.py:1470`), el valor
  de `max_file_size` (`ui.py:74`) y el escape de la frase en la tarjeta del
  cuaderno (`ui.py:2636`).

**Arreglo, por orden de valor.** (1) Una prueba con dos sesiones que entran
con perfiles distintos y comprueban que `_codigo_de` de cada una es el suyo,
y otra que una tercera sesión sin entrar no herede nada. (2) Extender
`_el_marcapaginas_y_el_cuaderno_son_de_cada_lector` a `_mis_libros`,
`_debiles`, `_practicar` (con `voz.registrar_fallos` espiado, que hoy está
anulado en la cabecera de la suite) y `_desde_muestra` con un puntuador
doble. (3) En `tests_smoke.py`, aseverar `MAX_BLOCKS_PER_DOC == 8`,
`BLOCK_WORDS == 250`, `MIN_WORDS == 150` con los literales del documento, y
un caso de `_puntuar_bloques` con un doble que devuelva 5,3 para exigir que
el bloque llegue recortado. (4) Los dos `devolver` de la sinopsis con un
`consultor` que reviente al construirse y un `ficha.sinopsis` que devuelva
`(None, "sin_red")`.

### S7 · SERIO (bajo) · Dos manejadores levantan hacia Gradio con archivos que la app escribe

**Dónde:** `app/ui.py:1743` (`_sinopsis_guardada`: `v if isinstance(v, list)
else str(v)`) y `app/ui.py:1834` (`datos.get("de_que_trata", "").strip()`);
`app/ui.py:1912` y `_resumen_analisis` con `dificultad`/`ventanas` `NaN` o
`inf` (`_es_numero` los da por buenos; `json.loads` acepta `NaN` y `1e400`).

**Reproducción** (`f15_directos.py`, sobre el árbol real con datos en un
temporal):

```
LEVANTA _de_que_trata con sinopsis {"de_que_trata": ["a", "b"], "temas": ["x"]}: AttributeError: 'list' object has no attribute 'strip'
LEVANTA _de_que_trata con sinopsis {"de_que_trata": "ok", "para_quien": ["a"]}: AttributeError: 'list' object has no attribute 'strip'
OK     _de_que_trata con sinopsis {"de_que_trata": "ok", "temas": "una cadena"}: ... **Temas:** u · n · a · c · a · d · e · n · a
LEVANTA _analizar_libro con {"filas": [{"capitulo": 1, "dificultad": NaN, ...: ValueError: cannot convert float NaN to integer
LEVANTA _analizar_libro con {... "ventanas": 1e400 ...}: OverflowError: cannot convert float infinity to integer
LEVANTA _perfil_inicial con perfil.json que es carpeta: PermissionError: [Errno 13] Permission denied
```

La prueba `_analisis_y_sinopsis_mal_formados` (`pruebas_extremas.py:2640`)
prueba `[]`, `"hola"`, `{"de_que_trata": 5}` y `null`, no una lista dentro
de un campo. El caso `NaN` no es solo de disco corrupto: `_analizar_libro`
guarda `round(sum(vs)/len(vs), 3)` y `np.clip(nan)` es `nan`, así que un
`NaN` del modelo se persiste y revienta en la **siguiente** apertura de ese
libro. `_perfil_inicial` corre en `demo.load`.

**Arreglo.** En `_sinopsis_guardada`, `str(v)` también para listas salvo en
`temas` (y `temas` a lista siempre); en `_analisis_guardado`, exigir
`math.isfinite` en `_es_numero`; en `perfil.cargar`, atrapar `OSError`.

### M1 · MENOR · La IPA «británica y americana» existe para el 2,3 % de las palabras del diccionario

**Dónde:** `documento.md:229` (Cuadro 2), `documento.md:909` (Cuadro 15),
`README.md:41`, `guion_video.md:122` («la fonética británica y americana y el
audio, todo local»). El §6.4 (`documento.md:531`) cuantifica el audio (0,5 %)
y calla sobre la IPA.

**Medido** sobre `kaikki_diccionario.db`:

```
entradas 1487639 | con alguna IPA 46794 (3.1%) | con UK y US 33635 (2.3%) | palabras 1385953 | palabras con IPA 31866 (2.3%)
3000 palabras mas frecuentes: en diccionario 2897, con IPA 1628 (54.3%)
```

De las 15 palabras del prólogo de la demo, **9 salen «sin IPA»** (torpedo,
cling, rebuff, oilskin, stake, flush, list...). En el vídeo, «la fonética
británica y americana» aparecerá según la palabra que se toque.

**Arreglo.** Una frase en §6.4 con la cobertura de IPA al lado de la del
audio, y elegir palabras con IPA para el vídeo (nerve, packet, muttered,
starboard, perspiration, steadfast la tienen).

### M2 · MENOR · El cuadernillo, §7.2: negritas anidadas y sin acentos

**Dónde:** `entrega/notebook_proyecto.py:1709-1713` (celda markdown, la
misma en el `.ipynb`, que está regenerado del `.py` sin diferencias).

**Cita:** «Es esta: **textos con nivel MCER oficial, de una fuente ajena al
proyecto, que **no se uso para ajustar los pesos** -aunque si se miro durante
el desarrollo, para descubrir que el modelo no sabe leer un menu de
restaurante; eso es explorar, no entrenar, pero tampoco es un conjunto virgen
y conviene decirlo-.»

El `**` abre dentro de otro `**` (Colab lo pinta mal) y faltan cuatro tildes
(usó, sí, miró, menú) en la única celda del cuadernillo escrita sin ellas.

### M3 · MENOR · Seis, ocho o nueve correcciones de Esmeralda, según el archivo

`documento.md:204` y `:1330`: «seis etiquetas reescritas, cinco paletas...»;
`notebook_proyecto.py:1972`: «produjo seis correcciones concretas»;
`estrategia.md:453`: «de esa sesión salieron 8 correcciones»; y el Cuadro 1
de `estrategia.md` lista **nueve** filas (seis etiquetas + paletas + esquinas
+ 44 px). No se contradicen si se lee con cuidado (seis *etiquetas*), pero el
«8» de la métrica de éxito no sale de ninguna tabla.

### M4 · MENOR · `PENDIENTES.md` va por detrás del repositorio

- `PENDIENTES.md:26`: «el banco de mutantes en `scratchpad/mutar.py`» — vive
  en `tools/banco_mutantes.py`, y su docstring cuenta por qué se mudó.
- `PENDIENTES.md:35-36`: «El Space está al día hasta la auditoría 13
  incluida ... Lo de la auditoría 14 se sube con...» — hoy el Space es
  idéntico byte a byte a los 14 archivos locales (comprobado por HTTP, §4).
- `PENDIENTES.md:3`: «Actualizado: 10 de septiembre de 2026, tarde», con
  archivos tocados el 11.
- `documento.md:1132`: «se sometió a **catorce** auditorías externas» — con
  esta son quince, si se actualiza.

### M5 · MENOR · Cobros y frenos de dinero, tres asimetrías

- `_consultar` cuenta `llamadas_de_pago` **antes** de llamar
  (`lexicon.py`, «contado ANTES de pedirlo»): si OpenAI da *timeout* o 401, la
  llamada no cuesta pero el uso se cobra. `_de_que_trata` sí devuelve en
  `sin_red` (`ui.py:1821`). Dos criterios para lo mismo.
- `_entrar` (`ui.py:325`) no tiene freno de intentos por IP: `caja_clave.submit`
  permite probar contraseñas sin límite contra `LITERALEVEL_CUENTAS`. Con
  `compare_digest` el tiempo no filtra nada, pero un diccionario de
  contraseñas corrientes sí entra. La del profesor va por WhatsApp.
- `_diagnostico` (`ui.py:2818`) imprime en la pestaña pública «Estado» los
  **nombres de usuario** de las entradas mal formadas del secreto (por diseño,
  para depurar el Space a ciegas). Solo cuando hay entradas rotas.

Sospecha, no reproducida: el cubo por hora va por `x-forwarded-for`; si el
proxy del Space no la pusiera, todos los visitantes compartirían un solo cubo
de 30 consultas. No lo pude medir sin desplegar.

### M6 · MENOR · Cosas que se ven en la pantalla del libro y del buscador

- «Lo que más se repite: tommy, tuppence, julius, **don’t**, james, **think,
  down**, young, jane, **got**» (`ficha._VACIAS` no incluye contracciones ni
  verbos corrientes).
- El *placeholder* «una novela de detectives victoriana» (`ui.py:2964`,
  `documento.md:923-924`, `documento.tex:2184`) devuelve, con perfil 1,2: Christie 1922 (B2), un cuento
  infantil A1 de StoryWeaver en segundo puesto (sim 0,81, el más alto de la
  lista), Dickens, Gaskell... y **ningún Conan Doyle**, aunque hay seis
  títulos de Holmes en el catálogo (PG1661, PG244, PG2852, PG2097, PG48320,
  PG834). El guion abre con «*El sabueso de los Baskerville* le quedaba
  justo».
- Tras recargar, la caja «Entrar con tu perfil» vuelve vacía y sin el «Has
  entrado como...», aunque la sesión de pago sigue viva (la identidad es del
  navegador). El visitante no sabe si sigue dentro hasta que consulta.
- «Mis puntos débiles» y «Corrígeme» escriben en el mismo `veredicto`: pulsar
  el segundo borra el mensaje del primero.

### N1 · NOTA · `app.py` del Space no está en el repositorio

`tools/desplegar_app.py` no lo toca y `_rutas_permitidas`
(`pruebas_extremas.py:937`) comprueba `main.py`. Lo bajé del Space: pasa
`allowed_paths=ui.RUTAS_PERMITIDAS` y `max_file_size=ui.TAMANO_MAXIMO_SUBIDA`,
fija `LITERALEVEL_MODELO` al repo del Hub y `LITERALEVEL_DICCIONARIO` a la
raíz. Equivalente a `main.py` en lo que importa; solo que ninguna prueba lo
ve. Y el valor de `TAMANO_MAXIMO_SUBIDA` (`ui.py:74`) no lo asevera nadie:
la prueba mira que exista `max_file_size=`, no cuánto vale (mutante F15-22).

### N2 · NOTA · La tabla A1–C2 que ve el lector no está atada al código

`ui.py:1470` (`_TABLA_CEFR`) es texto; `pruebas_extremas.py:1073` comprueba
`_cefr` contra límites escritos en la prueba, no contra la tabla. Cambiar
«1.00 – 1.40» por «1.00 – 1.50» en la tabla no rompe nada (mutante F15-21).

---

## 2. El dinero, camino por camino

| Camino | Puerta | Cupo | Tope/hora | Devuelve si no gasta | Visto en la app |
|---|---|---|---|---|---|
| `_consultar` | `usar_openai=puede` (`ui.py:2340`) | `consumir` atómico | solo si `va_a_costar` | si `llamadas_de_pago == 0`; **no** si la llamada salió y falló | sin perfil: «Sin clave...»; con perfil y sin clave: no cobra |
| `_de_que_trata` | `_puede_pagar` (`ui.py:1779`) | ídem | ídem | sin cliente, constructor roto, `sin_red`/`sin_pasajes` | con perfil y sin clave: «Para el resumen hace falta la clave», `uso_openai.json = {"invitado1": 0}` |
| `_practicar` | `_puede_pagar` (`ui.py:2530`) | ídem | ídem | nunca (documentado: sin transcripción sí paga gpt y tts) | sin audio: «Graba tu voz» antes de cobrar |

No hay un cuarto camino: `voz._cliente` y `lexicon._cliente` solo se llaman
desde esos tres manejadores; `ficha.sinopsis` recibe el cliente de
`_de_que_trata`. `pruebas_lexicon.py` §6 confirma con el espía:
`usar_openai=False -> peticiones: []`, «1a consulta: 2 peticiones | 2a
idéntica: 0», variantes de «Fetters» → `[]`.

---

## 3. Banco de mutantes F15

Método: copia del árbol (`app/`, `pruebas_*.py`, `tests_smoke.py`, `main.py`,
`validar_local.py`, `catalogo_recomendaciones.csv`) en
`scratchpad/f15_arbol/<mutante>/`; `LITERALEVEL_MODELO` y
`LITERALEVEL_DICCIONARIO` apuntando a los reales; sin `OPENAI_API_KEY`;
`HF_HUB_OFFLINE=1`. **Control sin mutar:** `pruebas_extremas.py rc=0 79.5s
(272)`, `pruebas_integracion.py rc=0 22.9s (27)`, `tests_smoke.py`,
`pruebas_ficha.py`, `pruebas_perfil.py` en verde. Ningún mutante repite los
33 de `tools/banco_mutantes.py`; se atribuye el fallo por nombre de prueba.

**Resultado: 8 cazados por su prueba, 22 vivos, 0 cazados por otra prueba.**
(Aviso sobre mi propio arnés: `f15_banco.py` reventó al final al escribir el
JSON de detalle —`Path % int`, un paréntesis mal puesto—, después de haber
corrido y clasificado los 30; la atribución de cada fila sale de las líneas
que imprimió por mutante, que ya llevan el cotejo del nombre esperado.)

| Mutante | Dónde | Qué rompe | Prueba que debería cazarlo | Suites | Resultado |
|---|---|---|---|---|---|
| F15-01 | `ui.py:305-306` | `_sesion_de` devuelve `"local"` para todos: **el perfil de pago de uno vale para todos** | ninguna existe («la sesión de pago es de cada visitante») | extremas | **VIVO** |
| F15-02 | `ui.py:2706` | `_mis_libros` lee `biblioteca.json` sin `peticion` (una estantería para todos) | ninguna («mis libros son de cada lector») | extremas | **VIVO** |
| F15-03 | `ui.py:2581` | `_debiles` lee `voz.db` sin `peticion` | ninguna | extremas | **VIVO** |
| F15-04 | `ui.py:2538-2539` | `_practicar` escribe los fallos en `voz.db` sin `peticion` | ninguna | extremas | **VIVO** |
| F15-05 | `ui.py:1334` | `_abrir` anota la biblioteca sin `peticion` | ninguna | extremas | **VIVO** |
| F15-06 | `ui.py:677` | `_desde_muestra` guarda `perfil.json` sin `peticion` | ninguna | extremas, integración | **VIVO** |
| F15-07 | `ui.py:1798` | `_de_que_trata` no devuelve el uso cuando no hay cliente | «el cupo cuadra con las llamadas de pago» | extremas | CAZADO |
| F15-08 | `ui.py:1807` | ídem cuando el constructor del consultor revienta | ídem | extremas | **VIVO** |
| F15-09 | `ui.py:1821` | ídem en `sin_red` / `sin_pasajes` (`if False:`) | ídem | extremas | **VIVO** |
| F15-10 | `ui.py:2353` | `_consultar` no devuelve el uso tras una excepción | ídem | extremas | CAZADO |
| F15-11 | `ui.py:2342` | `usar_openai=True` siempre (la puerta de perfil no cierra) | «la consulta lexica pide codigo» | extremas | CAZADO |
| F15-12 | `lexicon.py:713` | nunca mira la caché de explicaciones (`extra = None`) | `pruebas_lexicon` §6 «volvió a pagar» y `test_cache_separa_idioma_y_acepcion` | lexicon `--sin-openai`, desambiguación | CAZADO |
| F15-13 | `lexicon.py:686` | clave del audio con la superficie cruda («Fetters» ≠ «fetters.») | `pruebas_lexicon` §6 «las variantes de la misma palabra pagan» | lexicon, audio_atómico | CAZADO |
| F15-14 | `scoring.py:344` | sin `np.clip` por bloque (el recorte deja de ir dentro del sumatorio, §2.1 del documento) | ninguna | extremas, integración, smoke | **VIVO** |
| F15-15 | `scoring.py:21` | `MAX_BLOCKS_PER_DOC = 800` | `tests_smoke.py:47` («excede el tope de bloques», cota autorreferente) | smoke, integración, extremas | **VIVO** |
| F15-16 | `scoring.py:19` | `BLOCK_WORDS = 200` | `tests_smoke.py:48` («bloque de tamano incorrecto», ídem) | smoke, integración, extremas | **VIVO** |
| F15-17 | `perfil.py:33` | `HOLGURA = 0.5` | «las dos pestanas prometen el mismo rango» (lee la misma variable) | extremas, perfil, integración | **VIVO** |
| F15-18 | `reader.py:226` | la portada de un `.txt` deja de llamarse «Antes del primer capítulo» (T6 deja de descartarla) | ninguna | extremas, integración, ficha, smoke | **VIVO** |
| F15-19 | `ui.py:1405` | «¿Cómo de difícil es este capítulo?» puntúa con la licencia dentro (T5) | ninguna | extremas, integración | **VIVO** |
| F15-20 | `ui.py:2636` | la frase del cuaderno se pinta sin `_html.escape` | «html y comillas en la frase» solo prueba `cuaderno.registrar`, no la tarjeta | extremas, integración | **VIVO** |
| F15-21 | `ui.py:1470` | la tabla A1–C2 que ve el lector dice «1.00 – 1.50» | «los limites de la tabla son los del codigo» (no lee la tabla) | extremas | **VIVO** |
| F15-22 | `ui.py:74` | `TAMANO_MAXIMO_SUBIDA = "20gb"` | «allowed_paths: sirve el audio y nada mas» (mira que exista el parámetro) | extremas | **VIVO** |
| F15-23 | `catalogo.py:226` | `peso_nivel = 0.0` (la casilla «Acercar los resultados a mi nivel» no hace nada) | ninguna llama a `buscar` con perfil | extremas, integración | **VIVO** |
| F15-24 | `ui.py:221` | `LIMITE_DESCARGAS_HORA = 0` | «las descargas nuevas tienen tope por hora» | extremas | CAZADO |
| F15-26 | `ui.py:143` | la identidad del navegador no se sanea | «sin localStorage no revienta» | extremas | CAZADO |
| F15-30 | `lexicon.py:675` | `lexicon` ignora `usar_openai` | `pruebas_lexicon` §6 «la puerta de pago de lexicon no cierra» | lexicon, desambiguación | CAZADO |
| F15-31 | `ficha.py:296` | 90.000 palabras por pasaje a la API en la sinopsis | «lo que viaja a OpenAI va recortado» (solo cubre `_consultar`) | extremas, ficha | **VIVO** |
| F15-32 | `ui.py:2513` | la frase de voz viaja sin `[:LIMITE_FRASE_VOZ]` (T8 promete 300) | ídem | extremas | **VIVO** |
| F15-39 | `ui.py:2448` | «Traer una frase» devuelve siempre la primera | `pruebas_integracion.py:186` solo mide la longitud | extremas, integración | **VIVO** |
| F15-40 | `ui.py:1618` | el vistazo rápido deja de muestrear capítulos (lee todos) | ninguna con modelo | extremas, integración | **VIVO** |

Lectura: los ocho cazados cubren exactamente las correcciones de las
auditorías 12–14 que ya tenían prueba (puerta de perfil, caché, variantes del
audio, tope de descargas, saneado de identidad). Los veintidós vivos se
reparten en cuatro familias: **datos por lector fuera del perfil/cuaderno/
marcapáginas** (01–06), **devoluciones del cupo en la sinopsis** (08, 09),
**constantes del modelo aseveradas contra sí mismas** (14–17), y
**promesas del documento sin prueba** (18–23, 31, 32, 39, 40).

---

## 4. Lo que comprobé y estaba bien

**Cifras (cada una en todos los archivos donde vive, PDF incluido):**
272 pruebas y 27 pasos (README, documento.tex/pdf, estrategia); 85 parejas /
17 por paleta, peores 4,53 (hielo/botón) y 3,11 (menta/título-3), recalculadas
sobre `paletas.py`; 0,860 / 0,807 / 0,668 / 0,732 (md, tex, pdf, estrategia,
presentación, README, PENDIENTES, cuadernillo); 47 / 36 / 38 / 59 y 2+10;
0,908 / 97,2 % / 0,829 y 654 = 510 + 144; las cinco medias por nivel; 1.197,
148 y 1.049 (recontados con pandas: 1197 filas, 148 `PG`, reparto A1 723 · A2
185 · B1 69 · B2 52 · C1 53 · C2 115); 61.642 / 79.337 (el cuadernillo los
recuenta hoy sobre el catálogo vivo y da 61.642); 487 ventanas y 130.104
palabras crudas del epub; 570 palabras = 3:48 (`tools/contar_guion.py`
reproduce la cifra); 328/332/243 MB con su matiz declarado; 7 USD, 31 s /
32 s, 48 h, 8,19 / 112,7 / 2.022 / 13,8× / 247×, 0,72x+0,38 y 0,67x+0,41;
ocho pestañas (contadas en `ui.py`), seis preguntas y tres fragmentos;
Cuadro 11/13 del `.md` = 16/18 del PDF, como dicen `validar_local.py` y el
README; 13 diapositivas y 92 celdas (53 de código); el `.ipynb` es exactamente
lo que genera `tools/a_notebook.py` del `.py`.

**`validar_local.py`** con los 59 PDF de `~/Downloads`: `VALIDACION CORRECTA:
47 textos, 5 niveles, medias estrictamente crecientes`, los diez rechazados
con su motivo (nueve A1 y un B1, todos «muy corto»), 36 con el filtro
completo, y las tres cifras del baseline.

**El cuadernillo** en un venv aislado con `--system-site-packages` +
`seaborn xgboost openpyxl` (no se tocó el entorno del autor): `exit=0`,
stderr con una sola línea (la barra «Loading weights» de transformers, no un
warning); reproduce 0,313/1,295, 0,352/1,061, 0,340/1,081, RMSE 0,764 /
0,748 / 0,767, Spearman 0,693 / 0,707 / 0,686, «Orden estrictamente creciente:
True», factor 247×.

**El Space:** `RUNNING` en `cpu-basic`, `gcTimeout 172800`, HTTP 200 en
0,96 s; `README` con `app_file: app.py` y `sdk_version: 6.26.0`; los 14
archivos de la lista blanca de `desplegar_app.py` idénticos byte a byte;
`kaikki_diccionario.db`, el CSV y el `.npy` en la raíz del Space como dice
`DESPLIEGUE.md`.

**Datos de los lectores:** dos contextos de navegador aislados sobre la misma
instancia (SPACE_ID simulado): el segundo ve «Todavía no has fijado tu nivel»
y «Todavía no has abierto ningún libro»; en disco, `lectores/<uuid-1>/` con
`perfil.json`, `sesion.json`, `biblioteca.json`, `cuaderno.db` y
`lectores/<uuid-2>/` vacía; `lexicon.db` y `analisis/` compartidos, como
declara AGENTS.md. Recargar la página conserva perfil y libro («seguías en el
capítulo 3 de 31: PROLOGUE»). `/gradio_api/file=`: 200 solo bajo `audio/`;
403 a `cuaderno.db`, `perfil.json`, `lexicon.db`, `analisis/*.json`, a un
archivo del cwd, a `requirements.txt` y a `.env` del repo. Gradio 6.26 valida
en el servidor `Radio`/`Dropdown` contra las `choices` de **esa sesión**
(`Blocks.preprocess_data` usa `state[block._id]`) y `Number` contra
`minimum`/`maximum`, así que forjar una ruta en «Seguir leyendo» o un `n`
infinito no llega al manejador. Un `session_hash` o una identidad de
`localStorage` con `../` no salen de `lectores/`.

**Excepciones hacia Gradio:** probé a mano `_desde_cuestionario`,
`_recomendar`, `_buscar`, `_entrar`, `_seguir_leyendo`, `_capitulo`,
`_frase_del_capitulo`, `_medir` y `_practicar` con `None`, cadenas, listas,
`True`, `-0.0`, `1.7`, `inf`, `nan`, rutas de directorio: todo vuelve como
texto salvo lo listado en S7 (y las entradas que Gradio rechaza antes).
Consola del navegador sin errores ni avisos tras los tres primeros clics (no
la volví a mirar después).

**Pruebas que sí prueban lo que dicen** (ejecutadas contra sus mutantes):
«la consulta léxica pide código» (F15-11), «el cupo cuadra con las llamadas
de pago» para el cliente `None` y para la excepción de `_consultar` (F15-07,
F15-10), «la puerta de pago de lexicon no cierra» y «volvió a pagar» de
`pruebas_lexicon` §6 más `test_cache_separa_idioma_y_acepcion` (F15-12,
F15-30), «las variantes de la misma palabra pagan» (F15-13), «las descargas
nuevas tienen tope por hora» (F15-24) y «sin localStorage no revienta»
(F15-26).

**Prosa:** sin palabras dobles ni tildes ausentes en `documento.md`,
`estrategia.md`, `guion_video.md`, `mensaje_profesor.md`, el manifiesto ni el
README (barrido de 80 palabras corrientes con y sin tilde); el PDF de 47
páginas contiene la estrategia desarrollada (Esmeralda, Accionables, Cuadro
«Accionables, con coste y criterio de terminado»); la nota inicial del `.md`
sobre la numeración distinta de cuadros es cierta y las referencias cruzadas
de cada archivo apuntan a su propia numeración.

---

## 5. La pregunta que importa

**Tres primeros clics delante de un profesor**, tal como los hice yo (perfil
1,20 → «Ver libros para mi nivel →» → «Leerlo ahora»):

1. *Estimar mi nivel* funciona en el acto y bien: «1.20 / 2.00 (intermedio)
   ... entre 0.95 y 1.45 ... Guardado».
2. *Sorpréndeme* enseña diez B2 abribles. Bien. Pero si el profesor pregunta
   «¿y esto lo mide el modelo?», la respuesta es que no: es la etiqueta v1, y
   el cuarto clic (medir el capítulo: **1.50 / C1**; vistazo: **1.77 / C1**)
   lo pone en pantalla. Conviene tener la frase preparada, o no usar
   «Sorpréndeme» y buscar un título concreto.
3. *Leerlo ahora* abre el libro en el prólogo con su ficha y sin
   contradicciones de cifras... salvo que el libro sea el del guion: ahí la
   ficha dirá **129.589** y el resumen de la curva **130.104**, y Miguel
   estará diciendo 130.104 a cámara (S2). Y el libro del guion **no se puede
   abrir desde el buscador**: hay que subirlo (S1).

Si el cuarto clic es una palabra, que sea una elegida antes (S3): de las 15
que probé en el prólogo, dos salen con una definición equivocada y sin aviso,
nueve sin IPA, y las 14 que no traen audio de Wiktionary con un aviso que
habla de una «pronunciación de arriba» que no existe (comprobado literal en
«torpedoes»; en las demás, por el mismo camino de `_humanizar`). Si el quinto es «Traer una frase», la primera que trae en ese
libro es «on the afternoon of May 7, 1915.» (S4): escribir la frase a mano.

**Primera lectura atenta del PDF:** el §8.2 dice que el libro «se descarga de
Project Gutenberg» y el libro no está en Gutenberg; la cifra de la ficha no
es la que la ficha enseña; y el libro es una traducción con *copyright*
bajada de dokumen.pub, en un documento que hace bandera de no distribuir texto
con derechos. Ninguna de las tres cosas la ve una prueba automática, y las
tres están en la misma página.

Todo lo demás —las cifras, los guiones que las producen, el cuadernillo, el
despliegue, el dinero y los datos— aguantó lo que le eché.
