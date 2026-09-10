# Cierre de la auditoría 13 (Fable) — hallazgo por hallazgo

Cerrado el **10 de septiembre de 2026** por la tarde, sobre `e630dde` y lo que
vino después. El informe es
[`informe_fable_13.md`](informe_fable_13.md): 0 críticos, 8 serios (S1–S8), 14
menores (m1–m14) y 10 notas, con 15 mutantes vivos de 50.

**Los ocho serios eran ciertos.** Se comprobó cada uno a mano antes de tocar
nada —la regla de `auditar-con-modelo-externo`: un informe no es un resultado—
y ninguno se cayó al comprobarlo. Es el informe con mejor puntería de los trece.

---

## Serios

### S1 · «Sorpréndeme» se contradecía sola — CERRADO

`_tabla_libros(libros, aviso)` añadía el aviso **siempre** que fuera no vacío, y
`_recomendar` le pasaba el «no hay libros en este rango» en todas las llamadas.
La pantalla decía «Lo más leído entre 0.88 y 1.38», listaba diez libros y debajo
«No hay libros etiquetados entre 0.88 y 1.38».

Ahora son dos parámetros con papeles distintos: `vacio` **sustituye** a la tabla
cuando no hay libros y `nota` va al pie cuando sí los hay. `_buscar` pasa el
mismo texto a los dos huecos, y eso es correcto ahí: `catalogo.buscar` devuelve
«ningún libro supera el umbral» cuando la lista sale vacía y «se descartaron N
por parecido bajo» cuando trae resultados, nunca las dos.

### S2 · La cabecera corrida de Gutenberg se colaba como título — CERRADO, y arrastraba más de lo que decía el informe

Los epub de la generación vieja (`pg28xxx`) repiten `<h1>The Project Gutenberg
eBook of X, by Y.</h1>` al principio de **cada archivo**. Como no coincide con
el título del libro, `reader._titulo_capitulo` lo devolvía como título del
capítulo, y con ese título `ficha._es_boilerplate` lo tomaba por licencia.

Medido sobre los nueve epub cacheados del catálogo:

| Libro | Capítulos de cuerpo antes | Después |
|---|---|---|
| *Alicia* ilustrada (PG28885, B1 del catálogo) | **1 de 13** | **12 de 13** |
| *Orgullo y prejuicio* (PG1342, el más descargado) | 14 de 15 | **15 de 15** |
| Los otros siete | sin cambios | sin cambios |

Lo de *Orgullo y prejuicio* **no estaba en el informe**: su primer archivo trae
dentro los cinco primeros capítulos de la novela y se descartaba entero, así que
la curva del «libro entero» empezaba en el capítulo VI.

Dos cambios: `reader` descarta la cabecera como candidata a título, y
`ficha._es_boilerplate` la quita antes de mirar las primeras 400 palabras.

**Y un fallo propio en el arreglo, que se encontró midiendo.** Al limpiar el
título, la portadilla legal dejó de caer por título y pasó a contar como
capítulo en tres libros. El primer parche fue «es portadilla si trae la marca de
licencia y le quedan menos de 1.200 palabras», y una prueba nueva demostró que
eso se llevaba por delante un capítulo de verdad de mil palabras con la
envoltura pegada —el caso que el comentario de `_es_boilerplate` explica que no
hay que romper—. El criterio bueno no es la longitud: es que **lo que queda tras
quitar la licencia no sea prosa corrida**. Un índice de capítulos no lo es, y un
capítulo sí. `continuous_prose` se aplica **solo** al archivo de la licencia, no
a los capítulos, que es lo que lo hacía inservible como filtro general.

### S3 · tts-1 se pagaba sin cobrar el uso — CERRADO

La explicación se guarda en caché por **lema**, y el audio por **la palabra tal
como la escribió el libro**. Así que `Fetters`, `FETTERS` y `fetters.` acertaban
la explicación —`desde_cache=True`, y `ui` devolvía el uso— y pedían un audio
nuevo cada una. Medido con un espía sobre `openai.OpenAI`, sin red:

```
antes:    5 llamadas de pago, 1 uso cobrado
después:  2 llamadas de pago, 1 uso cobrado, y las tres variantes no piden nada
```

Dos arreglos: `ResultadoLexico` trae `llamadas_de_pago`, y `ui` devuelve el uso
si y solo si es 0 —no si `desde_cache`, que solo habla de la explicación—; y la
clave del audio se normaliza (minúsculas, sin puntuación en los bordes), que es
lo que hace que las variantes acierten. tts-1 pronuncia igual las tres.

### S4 · `sqlite3.DatabaseError` se escapaba hacia Gradio — CERRADO

`CacheLexico.__init__` ejecuta un `CREATE TABLE` sobre `~/.literalevel/lexicon.db`,
y un archivo cortado a media escritura —el disco del Space es efímero— lanza
`sqlite3.DatabaseError`, que **no desciende de `OSError`**. El `except` de
`_consultar` atrapaba `(FileNotFoundError, OSError)`. Ahora es `Exception`, con
la misma devolución del uso.

### S5 · «31 textos» donde son 36 — CERRADO

Quedaba en `documento.md`, `documento.tex` y en un comentario de
`validar_local.py`. Los tres a 36. El recuento independiente del auditor
coincide con el nuestro: A1 1, A2 4, B1 9, B2 10, C1 12.

### S6 · Pruebas que no probaban — CERRADO con banco de mutantes propio

Quince pruebas nuevas en `pruebas_extremas.py` (246 → **261**) y una sección
nueva en `pruebas_lexicon.py`. Cada una está comprobada **contra su mutante**:
se rompe la línea a propósito y se exige que falle **esa** prueba y no otra.

**El resultado del banco: 20 mutantes, 20 cazados por la prueba que se
esperaba.** Está en `scratchpad/mutar.py` (17, sobre `pruebas_extremas.py`) y
`scratchpad/mutar_lexicon.py` (3, sobre la sección nueva de `pruebas_lexicon.py`,
con la red cortada por un espía).

Y algo que hay que decir: **tres de mis pruebas nuevas no probaban nada**, y lo
demostró el banco, no la lectura.

- La del recorte de la oración le pasaba una «palabra» de 300 caracteres, que
  `_consultar` rechaza **antes** de llamar al consultor. El doble no se llegaba
  a llamar, `vistas` quedaba vacío y `len("") <= 400` se cumplía sola.
- La de la licencia usaba una envoltura legal de **una sola línea**, y el
  ayudante que quita la cabecera corrida se la llevaba entera.
- La de la portadilla usaba un epub cuya portadilla tenía el título sacado del
  texto legal, así que caía por título y la regla nueva no hacía falta.

Es el mismo fallo que el informe encuentra en otras: **una prueba que pasa no
demuestra que cazaría el fallo**. Las tres están arregladas y sus mutantes
ahora sí caen.

### S7 · Dos pestañas prometiendo rangos distintos — CERRADO

«Mi nivel» anunciaba `rango_recomendado` (nivel −0,10 / +0,15) y «Sorpréndeme»
filtraba y anunciaba nivel ±0,25. Con nivel 1,13: «entre 1.03 y 1.28» en una y
«entre 0.88 y 1.38» en la de al lado, del mismo perfil.

La holgura ahora vive en **un solo sitio**, `perfil.HOLGURA`, y
`ui.HOLGURA_POR_NIVEL` la lee de ahí. Está en `perfil` y no en `ui` porque
`perfil.describir` la anuncia antes de que `ui` filtre nada.

### S8 · Archivos propios bien formados que tumbaban manejadores — CERRADO

Tres:

- `_leer_sesion` llamaba a `os.path.exists(d["ruta"])` sin comprobar el tipo, y
  `{"ruta": ["x"]}` lanzaba `TypeError`. Lo llama `_reanudar`, que corre en
  `demo.load`: **la página entera arrancaba en error** para ese lector.
- `_analisis_guardado` validaba `filas` y no lo que se lee después: sin
  `ventanas`, `_resumen_analisis` reventaba con `KeyError`.
- `dificultad` podía ser una cadena, y `ficha.dificultad_global` la sumaba.

Ahora el validador exige `dificultad` numérica —y `True` no cuenta como número,
que `isinstance(True, int)` es cierto en Python— rechaza `filas` vacías y
completa con valores sanos lo que falte.

---

## Menores

| | Qué | Estado |
|---|---|---|
| m1 | «232 pruebas» en ocho sitios | **261**, en los ocho |
| m2 | La figura de la escala mezclaba `0.20` y `0,00` | pares valor/etiqueta; comprobado en el PDF |
| m3 | Frase rota en `documento.md` | reescrita |
| m4 | La misma, en el `.tex` | reescrita |
| m5 | «Solo libros que pueda leer» no dejaba fuera nada | ahora dice «Acercar los resultados a mi nivel» |
| m6 | `1,197 libros` y `130,104 palabras` con coma inglesa | `ficha.miles()` en los diez sitios |
| m7 | «Sin clave de OpenAI» dos veces, y mentía en un 401 | avisos sin repetir y mensaje propio para la clave rechazada |
| m8 | `main.py` y el README decían que `app.py` chocaría con `app/` | corregido: el Space lleva los dos y arranca |
| m9 | El guion decía «0 herramientas» y §8.5 reconoce *TeakReader* | «0 de los 61.642 libros gratis traen su nivel medido» |
| m10 | La diapositiva mezclaba dos tandas | las tres barras son de la tanda histórica |
| m11 | «tomando muestras de 8 partes» y usaba una | cuenta las partes de verdad, y con singular |
| m12 | *Orgullo y prejuicio* con títulos de pie de ilustración | se descarta el `<span class="caption">` |
| m13 | El umbral de la cola era `n < 4` con cinco manejadores | constante nombrada y recuento exacto |
| m14 | El comentario de `validar_local.py` | a 36, y reajustado |

**n9** (`sólo` con tilde) también corregido: era el único de cada archivo.

## Notas

- **n2** (`nivel: 1e400` daba «inf / 2.00») — cerrado: `perfil.cargar` exige
  finito y dentro de 0..2.
- **n3** (la poda de sesiones tiraba a lectores vivos) — cerrado: cada uso
  manda la entrada al final de la fila, así que la poda tira las **menos
  usadas** y no las que entraron primero. Reasignar una clave que ya existe
  **no** la mueve al final en un `dict` de Python, que era el fallo. Y la
  prueba nueva encontró de paso que el refresco al consultar **solo corría
  desplegado**: `_dir_lector` se corta antes en local. Se extrajo
  `_lector_de_sesion`, que es la parte que hay que probar.
- **n5** (`_descargar_gutenberg` sin tope y ocupando un hueco de la cola) —
  cerrado: tope de 20 libros **nuevos** por IP y hora. No contradice la regla
  de «lo que no cuesta dinero no se limita» porque esto no es local: son hasta
  tres peticiones de 45 s a gutenberg.org, y es el único camino que puede dejar
  sin servicio a los demás sin gastar un céntimo. Los libros ya descargados no
  gastan ficha.
- **n1** (el aviso de HF Hub en el cuadernillo), **n4** (los topes tras el
  proxy del Space), **n6** (un 401 cobra el uso), **n7**, **n8** y **n10**: se
  dejan como están. n4 no es verificable en local y n6 es una decisión tomada y
  documentada.

---

## Y el despliegue

Los cinco módulos que faltaban se subieron al Space **antes** de esta ronda
(`f14bc3a`): `ui.py`, `reader.py`, `scoring.py`, `lexicon.py`, `voz.py` y
`requirements.txt`. Se encontró de paso que `requirements.txt` **no declaraba
`huggingface_hub`**, que `catalogo.py` y `lexicon.py` usan directamente para
bajar el modelo y el diccionario del Hub: funcionaba de rebote, porque
`transformers` lo arrastra.

**Todo lo de esta ronda vuelve a estar sin desplegar.** Hay que subirlo con
`python tools/desplegar_app.py`, que compara por hash y sube solo lo que cambió,
con lista blanca explícita —`upload_folder` no lee `.gitignore` y subiría
`CLAVES.txt` y `.env` a un Space público—.
