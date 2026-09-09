# LiteraLevel: medición automática de la dificultad de lectura en inglés y su entrega a un lector real

**Proyecto integrador — Módulo 5 (Integrador)**
Diplomado en Ciencia de Datos, FES Acatlán (UNAM), Generación 34
Profesor: Mtro. Fernando Barranco Rodríguez
Autor: Miguel Reyes Carrillo
Septiembre de 2026

> La sección **Estrategia** de este trabajo se entrega en un documento aparte,
> `estrategia.md`, por su extensión. En este documento se resume en el
> apartado 3 y se remite allí para el desarrollo completo.

---

## Resumen

Aprender inglés leyendo funciona, pero solo si el libro está al nivel de quien
lo abre. Un lector que elige un libro demasiado difícil no aprende: lo
abandona. Y hoy no hay forma sencilla de saber, antes de empezar, si *ese*
libro concreto está a su alcance.

LiteraLevel es una aplicación que responde esa pregunta. Le da al lector un
número entre 0 y 2 que dice cuánta dificultad tiene un texto en inglés, y lo
hace leyendo el texto de verdad, no contando páginas. Con ese número le busca
libros que pueda terminar, se los abre dentro de la propia aplicación, le
enseña la dificultad capítulo a capítulo —los libros no son igual de difíciles
de principio a fin—, le explica cualquier palabra en la frase en la que
aparece y le corrige la pronunciación cuando lee en voz alta.

Debajo hay un modelo de lenguaje pequeño (`distilroberta-base`) afinado para
predecir dificultad como un número continuo. En validación ciega alcanza una
correlación de Spearman de 0,908 con el nivel de referencia y, sobre un corpus
externo que nunca vio, ordena los niveles del Marco Común Europeo de forma
estrictamente creciente: A1 0,5040 · A2 0,5480 · B1 0,9276 · B2 1,2478 ·
C1 1,4952. Ese orden —no el acierto exacto— es el resultado que sostiene el
trabajo.

Conviene decirlo desde la primera página: **la escala 0–2 es propia y
LiteraLevel no certifica ningún nivel del Marco Común Europeo**. Las letras
A1 a C2 fueron el ancla con la que se entrenó el modelo, no un título que la
aplicación expida. Sirven para elegir qué leer, no para acreditar nada.

El proyecto se cierra con una aplicación funcionando —ocho pestañas en Gradio
6.26, probada por una lectora de quince años ajena al proyecto— y con un
catálogo en curso de remedición: los 61.642 libros en inglés de dominio
público de Project Gutenberg, leídos enteros por el modelo, que a la velocidad
medida en una GPU A100 son unas 6,3 horas de cómputo.

**Palabras clave:** legibilidad automática, MCER, adquisición de segundas
lenguas, lectura extensiva, transformers, Project Gutenberg, Gradio.

---

## 1. Introducción y motivación

Cientos de millones de personas estudian inglés como segunda lengua. De todos
los métodos con respaldo empírico, la **lectura extensiva** —leer mucho, por
gusto, en textos ligeramente por encima del nivel actual— es uno de los que
mejor se sostiene: el metaanálisis de Nakanishi (2015) sobre décadas de
estudios encuentra efectos consistentes en comprensión y vocabulario, y Day y
Bamford (1998) la formalizan como programa de aula. Krashen (1985) llamó a esa
franja «input comprensible»: material que se entiende casi todo, con lo justo
de novedad para aprender.

El problema es operativo, no teórico. Para que la lectura extensiva funcione,
el texto tiene que caer en esa franja, y Hu y Nation (2000) la cuantifican: se
necesita reconocer alrededor del 98 % de las palabras corridas de un texto para
comprenderlo sin ayuda. Un punto porcentual por debajo y la lectura se
convierte en trabajo de diccionario. Es decir: **el mismo libro es excelente
para un lector y una pérdida de tiempo para otro que está dos niveles por
debajo**, y nada en la portada lo dice.

Hoy el lector hispanohablante que quiere leer en inglés se enfrenta a decenas
de miles de libros gratuitos en dominio público y a ninguna señal fiable sobre
cuál le corresponde. Las etiquetas que circulan (A2, B1, C1) casi nunca las
puso alguien que haya leído la obra completa, y además tratan el libro como si
tuviera una sola dificultad, cuando en realidad cambia de capítulo a capítulo.

**Pregunta que guía el trabajo:** ¿es posible estimar automáticamente, con un
modelo de lenguaje entrenado sobre corpus públicos, una medida de dificultad de
un texto en inglés que (a) ordene correctamente los niveles del MCER en
material externo que el modelo nunca vio, y (b) sea lo bastante rápida y
comprensible para ponerse en manos de un lector adolescente sin
entrenamiento previo?

Este documento responde a las dos mitades. La primera es un problema de
modelado y se resuelve en los apartados 4 a 7. La segunda es un problema de
producto y de usabilidad, que es lo que el módulo declara evaluar, y se
desarrolla en el apartado 8 y en el documento de estrategia.

---

## 2. Planteamiento del problema

### 2.1 Formulación

Sea $T$ un texto en inglés en prosa continua. Se busca una función
$f(T) \rightarrow [0, 2]$ tal que, para dos textos $T_i$ y $T_j$ cuyos niveles
oficiales de referencia cumplen $\text{nivel}(T_i) < \text{nivel}(T_j)$, se
cumpla $f(T_i) < f(T_j)$ con la mayor frecuencia posible.

Obsérvese que **el objetivo es ordinal, no de clasificación exacta**. La
frontera entre B1 y B2 es una convención pedagógica, no un hecho físico:
confundir B1 con B2 es un error muy distinto de confundir B1 con C2. Por eso
las métricas principales del trabajo son la correlación de Spearman y el
**error ordinal medio** (distancia media en niveles entre lo predicho y lo
real), y no la exactitud de clase.

Un texto largo no se puntúa de una vez. Se parte en bloques de 250 palabras
(mínimo 150) y se puntúa cada bloque; la salida del documento es la media sin
ponderar de sus bloques. Formalmente, si $B(T) = \{b_1, \dots, b_n\}$ son los
bloques de $T$ y $g$ es el modelo por bloque,

$$f(T) = 0{,}4 \cdot \frac{1}{n}\sum_{k=1}^{n} \text{clip}\big(g(b_k),\ 0,\ 5\big)$$

donde el factor 0,4 convierte la escala interna del modelo (0–5, un valor por
cada nivel A1…C2) en la escala pública 0–2 que ve el usuario.

**El recorte va dentro del sumatorio, y el orden importa.** Cada bloque se
lleva a 0–5 *antes* de promediar, no después. No es un detalle de notación:
la cabeza de regresión no tiene ninguna activación que la obligue a quedarse
en el intervalo, y **el 13,96 % de las ventanas de prosa literaria puntúa por
encima de 5** —medido sobre 530 ventanas de *Alicia*, *Orgullo y prejuicio* y
*Crimen y castigo*; ninguna baja de 0—. Recortar después de promediar dejaría
que un bloque que puntúa 5,3 arrastrase hacia arriba a todo el capítulo. Las
dos versiones de la fórmula llegan a separarse **0,021** en un libro real, que
es cinco veces la diferencia de cualquier otra decisión de agregación del
sistema. Una versión anterior de este documento publicaba el recorte fuera del
sumatorio; el código siempre hizo lo que se describe aquí, y lo detectó una
auditoría externa.

### 2.2 Lo que el problema no es

Tres delimitaciones que evitan malentendidos y que la aplicación repite en
pantalla:

1. **No es certificación.** El modelo se ancló a etiquetas MCER durante el
   entrenamiento; eso no lo convierte en un examinador acreditado. Devuelve una
   posición en una recta continua, y la letra que muestra es simplemente el
   ancla más cercana.
2. **No es un medidor universal de texto.** El modelo solo vio prosa continua.
   Una carta de menú, un horario de vuelos o una tabla no son prosa, y
   puntuarlos daría un número sin significado. La aplicación los rechaza con un
   filtro estructural explícito (apartado 6.1).
3. **No mide el interés ni la calidad literaria.** Mide dificultad de lectura.
   Un libro fácil puede ser magnífico y uno difícil, aburrido.

### 2.3 Criterio de éxito

El proyecto se considera resuelto si se cumplen tres condiciones simultáneas:

| # | Condición | Cómo se verifica |
|---|---|---|
| C1 | El orden por nivel MCER se conserva en corpus externo no visto | Medias por nivel estrictamente crecientes |
| C2 | La señal supera a la trivial | Correlación parcial descontando la longitud del texto |
| C3 | Un usuario sin formación técnica completa el recorrido | Prueba con lectora ajena al proyecto |

*Cuadro 1. Criterios de éxito del proyecto.*

Las tres se cumplen y se documentan, respectivamente, en 7.4, 7.5 y en el
documento de estrategia.

---

## 3. Estrategia

La estrategia completa —accionables, descripción de usuarios y usabilidad del
modelo— se entrega en el documento **`estrategia.md`**, que forma parte de esta
misma entrega. Se resume aquí en cinco líneas para que el documento se lea
seguido:

- **Usuarios.** Tres perfiles con necesidades distintas: el estudiante
  adolescente de preparatoria que llega desde el móvil y no sabe su nivel; el
  adulto autodidacta que ya lee y quiere subir de escalón sin abandonar; y el
  docente de inglés que necesita repartir lecturas graduadas sin leerse antes
  cuarenta libros.
- **Propuesta.** Convertir una medida continua de dificultad en tres decisiones
  concretas para el lector: *qué leer ahora*, *por dónde se va a complicar* y
  *qué palabra no entendí en esta frase*.
- **Usabilidad del modelo.** Precálculo del catálogo para que la espera sea
  cero en el momento de buscar; dos velocidades de análisis explícitas
  (vistazo y libro entero) diciendo siempre cuál se usó; degradación elegante
  cuando falta red o clave; y la incertidumbre comunicada en bandas, no en
  decimales falsos.
- **Ciclo de usuario real.** Una lectora de quince años ajena al proyecto usó
  la aplicación, dijo *«o yo soy muy tonta para esto»* —que es un fallo de
  diseño, no suyo— y de ahí salieron seis etiquetas reescritas, cinco paletas
  de color, objetivos táctiles de 44 px y esquinas redondeadas.
- **Accionables.** Diez, con responsable, coste y criterio de terminado; los
  tres primeros son publicar modelo y diccionario, desplegar en enlace
  permanente y terminar la remedición del catálogo.

---

## 4. Descripción de los datos

Todos los datos de este trabajo provienen de **corpus académicos publicados,
APIs y descarga directa de repositorios de dominio público**. No se usó Kaggle
como fuente de datos en ningún punto del proyecto, conforme a la restricción
del módulo. Cuando un corpus tiene licencia restrictiva se dice, y su texto
crudo nunca sale del entorno de cómputo: solo estadísticas agregadas.

### 4.1 Inventario de fuentes

| Fuente | Qué aporta | Tamaño | Origen | Licencia / acceso |
|---|---|---|---|---|
| **CLEAR Corpus** | Etiqueta continua de legibilidad (`BT_easiness`) para el modelado supervisado | 4.724 extractos | Repositorio público del proyecto CLEAR (Crossley et al., 2023) | Uso investigador, descarga directa |
| **OneStopEnglish** | Validación externa ordinal en 3 niveles | 567 textos (189 por nivel) | GitHub (Vajjala & Lučić, 2018) | CC BY-SA 4.0 |
| **British Council LearnEnglish** | Validación externa contra niveles MCER oficiales | 59 textos A1–C1 | Descarga de los PDF públicos | Con derechos: no se distribuye ni se imprime texto |
| **SPGC** (Standardized Project Gutenberg Corpus) | Lista global de frecuencia de palabras (solo conteos, sin texto) | 45.345 libros en inglés de 55.905 | Zenodo, registro 2422561 (Gerlach & Font-Clos, 2018, 2020) | Abierta |
| **Project Gutenberg** | Catálogo de obras a medir y a leer dentro de la app | 79.337 entradas; 61.642 libros de texto en inglés | Catálogo oficial + espejo `gutenberg.pglaf.org` | Dominio público |
| **Kaikki / Wiktionary** | Diccionario, IPA británica y americana, audio | 1.487.639 filas en SQLite (243 MB) | Volcado de kaikki.org (Ylönen, 2022) | Libre |
| **StoryWeaver / Global Digital Library** | Lecturas graduadas del catálogo heredado | 1.049 registros | API pública de contenidos | Abierta, pero sin descarga de texto |

*Cuadro 2. Fuentes de datos, con volumen y procedencia.*

### 4.2 Relevancia de cada fuente

**CLEAR** es el corpus central del modelado. Su variable objetivo,
`BT_easiness`, no es una fórmula de legibilidad: es una escala construida a
partir de comparaciones pareadas juzgadas por lectores humanos, lo que evita
que el modelo aprenda a reproducir un contador de sílabas. Además trae
precalculadas once métricas clásicas (Flesch, Flesch-Kincaid, ARI, SMOG,
Dale-Chall, CAREC, CAREC_M, CML2RI, conteos de palabras, oraciones y párrafos)
y dos variables de estratificación —`Categ` (literario/informativo) y
`Lexile Band`— que permiten comprobar si el modelo funciona igual de bien en
narrativa que en divulgación. Esa comprobación por dominio se hizo y aparece en
el apartado 7.3.

**OneStopEnglish** aporta algo que CLEAR no puede: el mismo artículo reescrito
en tres niveles. Como el contenido es idéntico y solo cambia la complejidad
lingüística, permite medir el orden dentro de cada artículo, una prueba mucho
más exigente y limpia que comparar textos distintos entre sí.

**British Council** es la única fuente con niveles MCER asignados por una
institución de enseñanza de idiomas, que es exactamente la escala que el
producto muestra al usuario. Es el juez final.

**SPGC** existe por una razón de higiene: descargar decenas de miles de libros
uno a uno desde `gutenberg.org` viola su política de acceso automatizado. El
SPGC publica los conteos de palabras ya calculados, con lo que se obtiene la
distribución léxica del catálogo completo sin tocar el servidor de Gutenberg.

**Kaikki/Wiktionary** sustituyó a una API comercial de diccionario. La decisión
fue de producto y de derechos: un SQLite local de 1,48 millones de entradas no
tiene límite de peticiones, no cuesta dinero por consulta y no puede
desaparecer si un proveedor cambia sus condiciones. Se descartó
explícitamente Oxford Dictionaries.

### 4.3 Calidad de los datos: lo que está bien y lo que no

Un apartado de calidad que solo diga «los datos están limpios» no informa.
Estos son los problemas reales encontrados y qué se hizo con cada uno.

**(a) El corpus de validación MCER no es homogéneo.** De los 59 textos de
British Council, una parte no es prosa: en A1 hay un menú de restaurante, un
horario de estudio, un tablero de salidas de aeropuerto, tarjetas de visita y
mensajes de texto. Son documentos fragmentarios que el modelo nunca vio. Se
definió un filtro de prosa continua **antes de mirar ningún resultado**, para
no incurrir en elegir el examen después de ver las notas, y por dos vías
independientes: por palabras clave del título y por estructura (≥7 palabras
por línea y densidad de puntuación final de frase en el intervalo (0, 0,11]).
Los dos criterios coinciden en 53 de 59 casos, el 89,8 %.

**(b) Las etiquetas del catálogo heredado no son fiables, y hay que decirlo.**
El catálogo con el que la aplicación funciona hoy tiene **1.197 libros** —no
12.752, como sugiere un `wc -l` ingenuo: el campo `hook` contiene saltos de
línea entrecomillados y hay que contar con un lector de CSV real—. Su columna
`nivel_cefr` **no es anotación humana ni metadato del editor**: son
predicciones de un modelo anterior (v1) sobre las primeras ~190 palabras de
cada obra, con cortes MCER obtenidos por cuantiles. El resultado es un reparto
que no resiste el sentido común:

| Nivel | Libros | % |
|---|---|---|
| A1 | 723 | 60,4 |
| A2 | 185 | 15,5 |
| C2 | 115 | 9,6 |
| B1 | 69 | 5,8 |
| C1 | 53 | 4,4 |
| B2 | 52 | 4,3 |
| **Total** | **1.197** | **100** |

*Cuadro 3. Reparto de niveles del catálogo heredado. Son predicciones de un
modelo v1 sobre las primeras ~190 palabras, no anotación fiable.*

Hay cuentos infantiles etiquetados C1 y clásicos muy distintos entre sí todos
en C2. Y el tramo B1–B2, donde está la mayoría de los lectores reales, son
121 libros de 1.197. Estas etiquetas sirven para ordenar y filtrar de forma
aproximada, **no son una medida fiable libro a libro**, y así se declara tanto
en el repositorio como en la aplicación. Es la razón de ser del precálculo
descrito en 8.3: remedir todo el catálogo, libro entero, con el modelo final.

**(c) De esos 1.197 libros, solo 148 se pueden abrir.** Son los de Project
Gutenberg. Los otros 1.049 provienen de StoryWeaver y no tienen fichero
descargable, de modo que aparecían en el desplegable de lectura como opciones
muertas. Peor aún: su identificador se había usado para construir enlaces a
Gutenberg extrayendo sus dígitos, con lo que `SWgdlgdl201` apuntaba al libro
201 de Gutenberg, que es otra obra. Un enlace al libro equivocado es peor que
ningún enlace. Hoy el desplegable lista solo lo que se puede abrir, la tabla
marca los descargables y una línea dice cuántos de cuántos son.

**(d) La licencia de Project Gutenberg se estaba puntuando como si fuera
novela.** El texto legal viene pegado al último capítulo: en *Alice's
Adventures in Wonderland*, 2.900 de las 5.042 palabras del capítulo XII son
licencia. Eso contaminaba tanto la puntuación como las estadísticas de la
ficha (`gutenberg` y `project` aparecían entre las palabras más repetidas del
libro). Se recorta por las marcas START/END dentro del capítulo, sin descartar
el capítulo, que contiene el final de la obra.

**(e) La portada no es un capítulo.** En un `.txt` de Gutenberg, las 4.957
palabras previas al capítulo I (portada, índice, pies de ilustración) se
estaban puntuando como si fueran la novela. En el análisis de *War and Peace*,
el «capítulo más fácil del libro» resultó ser la portadilla. Se descarta con la
etiqueta que el propio lector de ficheros asigna, «Antes del primer capítulo».
Se probó descartar por el filtro de prosa continua y **no sirve**: se llevaba
por delante dos capítulos reales de *Alice*.

---

## 5. Análisis exploratorio

Siguiendo la organización canónica del módulo, el análisis se presenta en tres
niveles: univariado, bivariado y multivariado. Todas las figuras y tablas
citadas se generan en el cuaderno que acompaña a este documento.

### 5.1 Análisis univariado

**La variable objetivo.** `BT_easiness` es continua y aproximadamente simétrica
alrededor de cero. No hay clases desbalanceadas que corregir porque no hay
clases: el problema es de regresión. Cuando se necesitó una versión categórica
para comparar modelos, se construyó por cuantiles (`qcut`), lo que garantiza
seis grupos equifrecuentes y hace que la exactitud sea comparable entre
modelos.

**Las variables textuales derivadas.** Sobre cada extracto se calcularon, a
partir de sus tokens, seis variables de ingeniería propia: longitud media de
oración, *type-token ratio*, longitud media de palabra, proporción de palabras
raras, sílabas medias por palabra y porcentaje de polisílabos. Todas son
positivas y con cola derecha, como es habitual en variables de conteo sobre
texto.

**La distribución del vocabulario inglés.** El agregado de los 45.345 libros
del SPGC arroja **2.838.258.803 palabras** y un vocabulario único de
**3.295.146 formas**. La distribución sigue la ley de Zipf con precisión: unas
pocas miles de palabras cubren la mayor parte del texto corrido. Este hecho,
que parece de trivia, tiene una consecuencia práctica que se documenta en 5.2.

**El catálogo.** El Cuadro 3 muestra el reparto de niveles del catálogo
heredado. Su forma —60 % en A1— es en sí misma un hallazgo del análisis
exploratorio: una distribución así no describe la literatura en dominio
público, describe el sesgo del clasificador que la produjo.

### 5.2 Análisis bivariado

**Cada variable frente a la dificultad.** La matriz de correlación de las
variables derivadas contra `BT_easiness` confirma el sentido esperado: los
textos más fáciles tienen oraciones más cortas, palabras más cortas, menos
polisílabos y menor proporción de palabras raras. La correlación de
`rare_word_ratio` con `BT_easiness` es negativa, como debe ser.

**El experimento de saturación léxica.** La variable «palabra rara» depende de
qué lista de palabras familiares se use. Se probaron tres, de menor a mayor:

| Lista de palabras familiares | Libros | Correlación de `rare_word_ratio` con `BT_easiness` |
|---|---|---|
| Corpus Gutenberg de NLTK | 18 | −0,379 |
| Muestra propia de Gutenberg | 397 | −0,330 |
| **SPGC completo, en inglés** | **45.345** | **−0,326** |

*Cuadro 4. Efecto de escalar el corpus de referencia léxica. La correlación no
mejora.*

Este es un **resultado negativo y se reporta como tal**: multiplicar por 2.500
el corpus de referencia no mejora la señal, e incluso la baja marginalmente. La
exactitud del clasificador de tres clases se mantuvo en 0,51 con las tres
listas. La explicación está en la ley de Zipf: la distribución de frecuencias
del inglés converge muy rápido, así que las 3.000 palabras más frecuentes de
18 libros y las de 45.345 libros son casi el mismo conjunto. El valor del paso
no está en la métrica sino en la cobertura: la lista del SPGC generaliza mejor
a texto nuevo arbitrario, que es lo que la aplicación recibe.

**Dificultad frente a longitud, la variable incómoda.** Sobre los 45 textos de
British Council medibles en local, contar las palabras del texto —sin modelo
alguno— alcanza una correlación de Spearman de **0,807** con el nivel oficial.
El modelo alcanza 0,854. Es decir: en ese corpus, nivel y longitud están
confundidos, porque los materiales de examen gradúan también la extensión de la
tarea. Publicar ese *baseline* antes de que lo pregunte el evaluador es más
creíble que omitirlo; en 7.5 se cuantifica cuánta señal aporta el modelo por
encima de él.

**Dificultad frente a dominio.** El nivel del texto está correlacionado con su
tipo documental. Al filtrar los 59 textos de British Council a prosa continua,
el nivel A1 desaparece casi por completo y el rango evaluable se encoge de seis
niveles a cuatro (A2–C1). Por eso el *baseline* de contar palabras cae de 0,879
a 0,765 al filtrar: parte de la señal del conjunto completo era simplemente que
los textos A1 son cortos. Las correlaciones antes y después del filtro **no son
comparables entre sí**, y se reportan por separado.

### 5.3 Análisis multivariado

**Las variables clásicas se estorban entre sí.** Las métricas de legibilidad
tradicionales (Flesch, Flesch-Kincaid, ARI, SMOG, Dale-Chall) son
transformaciones distintas de los mismos dos ingredientes —longitud de oración
y longitud de palabra— y por tanto están fuertemente correlacionadas entre
ellas. Meterlas todas en un modelo lineal no añade información: añade
multicolinealidad. Por eso el conjunto de trabajo se redujo a **tres**
variables poco redundantes entre sí y con interpretación distinta:
`avg_sentence_length` (complejidad sintáctica), `rare_word_ratio` (carga
léxica) y `type_token_ratio` (diversidad de vocabulario).

**Hasta dónde llegan las variables clásicas.** Con esas tres variables, un
clasificador de seis clases alcanza 0,29 de exactitud con regresión logística y
0,28 con XGBoost. Que un ensamble de árboles —capaz de capturar interacciones no
lineales arbitrarias— no supere a un modelo lineal es la prueba de que **el
cuello de botella no era el modelo sino la representación del texto**. Tres
números por documento no bastan para separar seis clases.

Conviene decir qué sostiene ese argumento y qué no. Lo que se comprueba es que
**subir la capacidad del algoritmo sobre estas variables no mueve el
resultado**, y eso se ve en cuatro modelos distintos. Lo que no se demuestra es
que exista un límite teórico: nadie ha probado todas las combinaciones
posibles de conteos, y el cuadernillo enseña un caso donde ampliar de tres a
diecisiete variables sí mejora. La conclusión honesta es empírica, no un techo.

**Representación densa.** Al sustituir las tres variables por un embedding de
384 dimensiones de `all-MiniLM-L6-v2` (Reimers & Gurevych, 2019), la exactitud
salta a 0,37 y el error ordinal medio baja de 1,39 a 0,93 niveles. El modelo
híbrido (embedding + las tres variables clásicas) da 0,37 y 0,91: prácticamente
lo mismo. Esto indica que **el embedding ya contiene la información que
aportaban las tres variables**, y bastante más.

**Estructura por dominio.** La comparación por subconjuntos de CLEAR
(literario frente a informativo, y por banda Lexile) muestra que el rendimiento
no es uniforme: el modelo funciona mejor en texto informativo que en literario,
y peor en la banda más fácil (Lexile 500) que en la más difícil (Lexile 1300).
Los números están en el Cuadro 7.

---

## 6. Procesamiento de datos

Cada transformación se documenta con su justificación. La regla que se siguió
es la del módulo 1 del diplomado: **no se transforma sin medir qué se rompió**.

### 6.1 Sobre el texto de entrada

| # | Transformación | Por qué | Evidencia / consecuencia |
|---|---|---|---|
| T1 | **Filtro de prosa continua** antes de puntuar: se rechaza si hay ≥2 viñetas o ≥6 líneas cortas | El modelo solo vio prosa; puntuar un menú da un número sin significado | El filtro estaba muerto en producción: se normalizaba *antes* de comprobar, y `normalize()` colapsa los saltos de línea, así que el detector recibía siempre una sola línea. Una carta de menú de 432 palabras se puntuaba como prosa. Corregido: el filtro va sobre el texto crudo |
| T2 | **Normalización de espacios** (`\s+` → espacio) después del filtro | Estabiliza el troceado en bloques | Sin efecto sobre la puntuación; solo sobre el corte |
| T3 | **Troceado en bloques de 250 palabras, mínimo 150** | Es la unidad con la que se entrenó; un bloque más corto no tiene señal suficiente | Constante del entrenamiento: cambiarla invalidaría las métricas reportadas |
| T4 | **Truncado a 256 tokens** | Límite de contexto del modelo | Medido: de 200 bloques, el **100 %** llega exactamente a 256 tokens tras truncar, porque 250 palabras inglesas siempre superan 256 BPE. No hay relleno que optimizar |
| T5 | **Recorte de la licencia de Gutenberg** por las marcas START/END, dentro del capítulo | 2.900 de las 5.042 palabras del capítulo XII de *Alice* son texto legal | Sin esto, el modelo puntuaba texto jurídico como narrativa y la ficha listaba «gutenberg» entre las palabras más frecuentes del libro |
| T6 | **Descarte de portada, índice y portadilla** por la etiqueta «Antes del primer capítulo» | 4.957 palabras de paratexto se puntuaban como novela | Se probó descartar por el filtro de prosa continua y se rechazó: eliminaba dos capítulos reales de *Alice* |
| T7 | **Muestreo de hasta 8 bloques repartidos por el documento** para la puntuación rápida | Dar un número en segundos, no en minutos | Cuantificado: 8 bloques dan 1,784 y el recorrido completo de las 23 ventanas del mismo capítulo da 1,743. El atajo se desvía 0,041 sobre una escala de 0 a 2 |
| T8 | **Recorte de entradas del usuario en el servidor** (40 caracteres por palabra, 400 por oración, 20 MB por fichero) | El límite del navegador es una sugerencia, no una defensa | Una cadena de 3.000 caracteres pasaba el filtro de «máximo cuatro palabras» y se pintaba como encabezado: 9.312 caracteres llenando la pantalla del móvil |

*Cuadro 5. Transformaciones sobre el texto, con su justificación y su
evidencia.*

### 6.2 Sobre las variables del modelado clásico

| # | Transformación | Por qué |
|---|---|---|
| T9 | **Partición agrupada por libro** (`GroupShuffleSplit` sobre `Title`, 20 % de prueba, semilla 42) | Un mismo libro aporta varios extractos a CLEAR. Con una partición aleatoria por fila, fragmentos del mismo libro caerían a ambos lados y el modelo memorizaría el estilo del autor en lugar de aprender dificultad. Es fuga de datos por diseño, y se evita por diseño |
| T10 | **Estandarización (`StandardScaler`) ajustada solo en entrenamiento** | Ajustar el escalador con los datos de prueba filtra su distribución al modelo |
| T11 | **Discretización por cuantiles (`qcut`) para las versiones categóricas** | Produce grupos equifrecuentes, con lo que la exactitud entre modelos es comparable y el azar tiene una probabilidad conocida (1/6 = 16,7 %) |
| T12 | **Lista de palabras familiares construida solo con el conjunto de entrenamiento** | Si se cuentan también las palabras de los extractos de prueba, esas palabras entran en la definición de una variable de entrada: es fuga de datos. Medida la diferencia, resulta despreciable —cambian 228 de 3.000 palabras y los resultados se mueven en la tercera decimal—, pero era fuga y se quitó |
| T13 | **Lista alternativa a escala: las 3.000 más frecuentes del SPGC** | Sustituye una lista de 18 libros por una de 45.345. Es un experimento de cobertura, no la lista que usan los modelos de este cuadernillo, y **el sistema desplegado no consulta ninguna lista de palabras**: puntúa con el transformador |

*Cuadro 6. Transformaciones sobre las variables tabulares.*

### 6.3 Sobre el corpus de vocabulario (procesamiento distribuido)

Los conteos del SPGC son 45.345 ficheros pequeños. Agregarlos secuencialmente
es un mal uso del tiempo y del sistema de ficheros, de modo que la agregación se
hizo con **PySpark**: los ficheros se distribuyen en 200 particiones, un
`flatMap` los convierte en pares (palabra, conteo) y un `reduceByKey` los suma
en una única lista global de frecuencia. Es el patrón canónico de conteo
distribuido y es lo que hace tratable un corpus de 2.838 millones de palabras
en una sesión de Colab.

### 6.4 Sobre el diccionario

El volcado de Kaikki llega como JSONL de líneas independientes. Se filtra a
entradas en inglés con palabra no vacía y se ingesta en SQLite con un esquema
plano (`palabra`, `pos`, `sentidos` como JSON, `ipa_uk`, `ipa_us`, `audio_uk`,
`audio_us`) y un índice por `palabra`. La justificación es de latencia: la
primera consulta sobre 1.487.639 filas tarda **0,001 s** con el índice puesto y
la base abierta en modo solo lectura. Los 243 MB del fichero no cuestan nada en
tiempo de respuesta.

Un dato de cobertura que condiciona el diseño de la aplicación: solo **7.003 de
las 1.487.639 entradas (0,5 %) traen audio de pronunciación**. Es decir, casi
cualquier palabra que un lector consulte por primera vez necesitará síntesis de
voz. Esa medición es la que justificó paralelizar las dos llamadas de red de una
consulta en lugar de encadenarlas.

---

## 7. Modelación

### 7.1 Diseño experimental

Todos los modelos comparten la **misma partición agrupada por libro** (3.774
extractos de entrenamiento y 950 de prueba) y la misma semilla, de modo que las
diferencias entre ellos son atribuibles al modelo y no al reparto de los datos.
Se comparan sobre los mismos 950 extractos reservados, con dos métricas:
exactitud sobre seis clases y **error ordinal medio**, que penaliza
proporcionalmente a la distancia del fallo.

Dos precisiones sobre ese conjunto, porque cambian cómo hay que leer las
cifras. La primera: esos 950 extractos son también los que sirvieron para
**elegir la época** del transformador, de modo que funcionan como validación de
selección y no como un test independiente; sus números pueden ser algo
optimistas. La segunda: las seis clases salen de partir `BT_easiness` en
**sextiles de este corpus**, no de anotaciones del Marco Común Europeo. Se les
dan nombres A1–C2 para poder ordenarlos, pero no son niveles MCER certificados
ni equivalen a los del modelo desplegado, que se ancla con otro corpus. Ambas
cosas las señaló una auditoría externa y ambas son ciertas.

### 7.2 Progresión de modelos

| Modelo | Representación del texto | Exactitud (6 niveles) | Error ordinal medio |
|---|---|---|---|
| Regresión logística | 3 variables clásicas | 0,29 | 1,39 |
| XGBoost | 3 variables clásicas | 0,28 | 1,42 |
| Regresión logística | Embedding MiniLM (384 d) | 0,37 | 0,93 |
| Regresión logística | Híbrido (embedding + 3 variables) | 0,37 | 0,91 |
| **Transformer afinado** | **Texto crudo, atención** | **0,46** | **0,67** |

*Cuadro 7. Progresión completa sobre el mismo conjunto de prueba (950
extractos). La mejora acompaña siempre al enriquecimiento de la
representación, no a la complejidad del clasificador.*

La lectura del cuadro es la tesis metodológica del trabajo: **cada vez que se
le dio al modelo una representación más rica del texto, el desempeño subió; y
cuando solo se aumentó la potencia del clasificador sobre la misma
representación pobre, no subió**. XGBoost sobre tres variables es marginalmente
peor que una regresión logística sobre las mismas tres variables.

El modelo afinado directamente sobre el texto, con cabeza de regresión sobre
`BT_easiness`, alcanza además **RMSE 0,560** y **correlación de Pearson 0,89**
con la etiqueta continua real, que es un resultado sólido para este problema.

**Sobreajuste, visto y controlado.** El entrenamiento corrió seis épocas con
tasa de aprendizaje 2e-5, decaimiento de pesos 0,01, calentamiento y precisión
mixta. El RMSE de validación mejoró hasta la época 3 (0,560) y a partir de ahí
empeoró de forma monótona —época 4: 0,578; época 5: 0,637; época 6: 0,660—
mientras la pérdida de entrenamiento seguía bajando. Es un caso de libro. Como
se guardaba un punto de control por época y se cargaba automáticamente el mejor
al terminar, **el modelo reportado es el de la época 3, no el de la última**.

### 7.3 Dónde funciona y dónde no: análisis por dominio

Un modelo que se evalúa solo en agregado esconde sus propios puntos ciegos. Se
midió la correlación con la dificultad real por subconjunto, comparando dos
variantes del modelo entrenadas sobre corpus distintos (v1 sobre
`BT_easiness`, v2 afinado sobre material graduado para aprendices):

| Dominio | n | v1 | v2 |
|---|---|---|---|
| Literatura (CLEAR, `Lit`) | 461 | **0,848** | 0,760 |
| Informativo (CLEAR, `Info`) | 489 | **0,905** | 0,837 |
| Banda Lexile 500 (más fácil) | 62 | **0,651** | 0,459 |
| Banda Lexile 1300 (más difícil) | 272 | **0,877** | 0,773 |
| Periodístico (OneStopEnglish) | 567 | 0,458 | **0,840** |
| Exámenes MCER (British Council) | 59 | −0,239 | **0,175** |

*Cuadro 8. Matriz modelo × dominio. Correlación orientada con la dificultad
real; más alto es mejor.*

La conclusión no es que uno sea bueno y otro malo: **miden cosas distintas**.
v1 gana en dificultad de lectura tipo CLEAR —juicios de lectores nativos sobre
prosa continua— y v2 gana donde la etiqueta es una graduación pensada para
aprendices de segunda lengua, que es la misma construcción que mide el MCER.
La decisión de qué escala presentar al usuario precede a la decisión de qué
modelo desplegar; se eligió la escala anclada al MCER, y con ella el modelo
correspondiente.

### 7.4 El modelo desplegado y su validación

El modelo en producción, **v4**, es un `distilroberta-base` (seis capas, 82
millones de parámetros) con cabeza de regresión, cuyos pesos ocupan 328 MB en
disco. Puntúa bloques de 250 palabras truncados a 256 tokens y promedia sin
ponderar. Su escala interna es 0–5 —un valor por nivel MCER, con posiciones
intermedias (A1+, A2+, B1+, B2+)— y la pública es esa misma escala multiplicada
por 0,4. **El modelo es final y no se reentrena.**

Su tarjeta de modelo (`metricas_literalevel_v4.json`, 5 de septiembre de 2026)
registra el corpus de anclaje MCER con el que se afinó: 654 documentos
aceptados —57 descartados por longitud insuficiente—, repartidos en 510 de
entrenamiento y 144 de validación. Esos 144 documentos son el conjunto de
validación ciega que produce las cifras de la primera fila del Cuadro 9.

| Conjunto | n | Exacto | Dentro de ±1 nivel | Spearman |
|---|---|---|---|---|
| Validación ciega | 144 | 53,5 % | **97,2 %** | **0,908** |
| British Council (externo) | 38 | 50,0 % | **100 %** | 0,829 |

*Cuadro 9. Métricas del modelo desplegado. MAE de 0,499 niveles en el conjunto
de validación.*

**El resultado que de verdad sostiene el trabajo no es ninguno de esos
porcentajes, sino el orden.** Sobre textos externos con nivel MCER oficial, las
medias por nivel quedan estrictamente crecientes:

| Nivel oficial | n (local) | Media en escala 0–2 |
|---|---|---|
| A1 | 3 | 0,5040 |
| A2 | 7 | 0,5480 |
| B1 | 12 | 0,9276 |
| B2 | 11 | 1,2478 |
| C1 | 12 | 1,4952 |

*Cuadro 10. Reproducción local de la validación externa, sobre los 45 textos
que sobreviven a la extracción de los PDF.*

Esta tabla se reproduce en cualquier máquina con el guion `validar_local.py`.
Lo que se reproduce exactamente es **el orden**; las medias difieren
ligeramente de las obtenidas en Colab (C1 coincide hasta la cuarta cifra, A2 se
desvía 0,10) porque la extracción de texto de los PDF conserva 45 de los 59
textos originales y el anclaje de la sección de lectura recorta distinto. Se
reporta la discrepancia en lugar de citar solo la cifra que coincide.

### 7.5 El baseline propio, y qué aporta el modelo por encima de él

| Señal | Spearman con el nivel oficial (45 textos) |
|---|---|
| Modelo v4 | **0,854** |
| Contar las palabras del texto, sin modelo | 0,807 |
| Modelo, descontando la longitud (correlación parcial) | **0,657** |

*Cuadro 11. El modelo frente a la señal trivial.*

Un contador de palabras llega casi tan lejos como el modelo en ese corpus, y
omitirlo sería deshonesto. Lo que sostiene al modelo es la tercera fila: **aporta
señal por encima de la longitud**, que es precisamente lo que un contador de
palabras no puede hacer. Además, el modelo no recibe la longitud del documento
como variable —puntúa bloques de tamaño fijo y promedia—, aunque su salida
correlacione 0,730 con ella, porque los corpus de examen gradúan también la
extensión de la tarea.

**La escala está comprimida, y la aplicación lo asume.** Contra el ancla real,
el ajuste ronda `predicho ≈ 0,72 × real + 0,38`, de modo que un texto A2 tiende
a puntuar cerca de B1. Por eso la interfaz muestra **bandas** (básico
< 0,6 ≤ intermedio < 1,4 ≤ avanzado) y la letra MCER solo como orientación, en
lugar de fingir una precisión de dos decimales que el modelo no tiene.

Los cortes de esas bandas no son tercios de la escala, y esa es una corrección
posterior. Al principio estaban en 0,8 y 1,6 —el 0–2 partido en tres—, pero
como el modelo comprime sus predicciones, con esos cortes un texto C1 caía en
«intermedio» y «avanzado» solo lo alcanzaba un C2: tres de los cinco niveles
medidos compartían banda. Ahora la banda se deriva del ancla MCER, con el
agrupamiento del propio marco —usuario básico A1–A2, independiente B1–B2,
competente C1–C2—, y las fronteras quedan en **0,6 y 1,4**. Así la palabra y la
letra no pueden contradecirse por construcción. Ninguna puntuación cambió: solo
cambió cómo se agrupan.

### 7.6 Cuadro de decisiones metodológicas

Incluye las hipótesis que se probaron y se rechazaron. Reportarlas es parte del
resultado.

| Decisión | Razón | Evidencia / consecuencia |
|---|---|---|
| Regresión, no clasificación | La dificultad es continua; clasificar tira información ordinal | El error ordinal medio baja de 1,39 a 0,67 en la progresión completa |
| Partición agrupada por libro | Evitar fuga de datos entre extractos del mismo autor | Aplicada a *todos* los modelos comparados, no solo al final |
| `distilroberta` y no `roberta-base` completo | La aplicación debe correr en CPU en el equipo de un estudiante | 328 MB y 0,9 s de carga; la diferencia de calidad no justificaba 3× de tamaño |
| Promediar bloques sin ponderar, con la **ventana** como unidad | Simplicidad y reproducibilidad; ponderar por longitud reintroduce la longitud como señal | Constante del entrenamiento. La app y el precálculo del catálogo usan ahora el mismo estimador: hasta que una auditoría externa lo detectó, la app promediaba las medias de cada capítulo y el catálogo todas las ventanas, y con capítulos de tamaño desigual **no son el mismo número** (0,004 de diferencia máxima medida en cinco libros reales) |
| **Rechazada: XGBoost sobre variables clásicas** | Se esperaba que un ensamble superase al modelo lineal | No lo hace: 0,28 frente a 0,29, y error ordinal peor (1,42 vs 1,39). El límite estaba en las variables |
| **Rechazada: modelo híbrido embedding + variables** | Se esperaba complementariedad | Ganancia nula (0,37 y 0,37; 0,91 vs 0,93). El embedding ya contiene esa información |
| **Rechazada: escalar la lista léxica al SPGC completo por rendimiento** | Se esperaba mejorar `rare_word_ratio` | La correlación pasa de −0,330 a −0,326. Se conserva igualmente por cobertura, no por métrica |
| **Rechazada: cuantización dinámica int8** | +18 % de velocidad en CPU | MAE de 0,210 sobre una escala de 0 a 2 y sesgo sistemático de −0,21. Un desplazamiento así cambia la letra MCER en el **52 %** de la escala y la banda en el **21 %**: no degrada la cifra, le cambia la etiqueta al libro. Inaceptable |
| **Rechazada: precisión media (fp16) en la GPU local** | Se esperaba acelerar | Es **4,8× más lenta** que fp32 en una GTX 1650 SUPER: el chip TU116 no tiene *tensor cores*. En una A100 sí compensa, y allí la desviación medida es 0,00037 de media |
| **Rechazada: `inference_mode` en lugar de `no_grad`** | Se esperaba menos sobrecarga | 0,4 % de diferencia, por debajo del ruido |
| **Rechazado: esfuerzo de razonamiento «mínimo» en la explicación léxica** | Es el doble de rápido (7,4 s frente a 14,9 s) | Con él, «had peeped» se explicó como pasado simple cuando es pasado perfecto. La gramática es justo lo que se evalúa |
| Filtrar prosa continua *antes* de ver resultados | Excluir textos porque el modelo falla en ellos invalida la validación | El criterio se fijó a priori y por dos vías independientes que coinciden en 89,8 % |

*Cuadro 12. Decisiones metodológicas, incluidas las hipótesis rechazadas.*

---

## 8. Resolución del problema

### 8.1 De la métrica a la decisión del lector

Una correlación de 0,908 no le sirve de nada a un adolescente. Lo que le sirve
son tres decisiones, y el producto está construido para producir exactamente
esas tres:

| Pregunta del lector | Qué la responde | Coste para él |
|---|---|---|
| ¿Cuál es mi nivel? | Seis preguntas sobre hábitos observables y tres fragmentos reales en escalera; o bien subir un libro que ya lee cómodo | Menos de dos minutos |
| ¿Qué leo ahora? | Búsqueda semántica en español sobre el catálogo, acotada al rango de lectura del perfil | Segundos |
| ¿Por dónde se va a complicar? | Curva de dificultad capítulo a capítulo, medida sobre el libro entero sin muestrear | De 12,7 s (vistazo, medido sobre Crime and Punishment) a minutos (libro completo) |
| ¿Qué significa esta palabra *aquí*? | Doble toque sobre la palabra: lema, IPA británica y americana, definición de Wiktionary, el sentido concreto en esa frase, gramática y audio | Instantáneo en local; la explicación contextual tarda más |
| ¿Lo estoy pronunciando bien? | Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla | Una frase |

*Cuadro 13. Del modelo a las decisiones del usuario.*

### 8.2 Un recorrido completo, con números reales

Tomemos el caso concreto de un lector cuyo perfil da 1,20 sobre 2 (banda
intermedia, ancla B2).

1. Describe en español lo que le apetece: *«una novela de detectives
   victoriana»*. El buscador no busca por título sino por significado, sobre
   embeddings multilingües, y le devuelve obras dentro de su rango. Un rescate
   por parecido ortográfico atiende además los nombres mal escritos —
   «dostoyevski», «chejov», «Shakespear» encuentran a quien deben— sin estorbar
   a las búsquedas por tema.
2. Abre el libro. Se descarga de Project Gutenberg y se abre dentro de la
   aplicación, sin salir a buscarlo.
3. Aparece la ficha, y todo lo que dice está **contado sobre el fichero**:
   palabras reales, tiempo de lectura a su ritmo, longitud media de frase,
   proporción de diálogo, variedad de vocabulario y palabras más repetidas.
   La proporción de diálogo distingue de verdad entre obras —*Alice* 73 %,
   *Pride and Prejudice* 28 %, *Crime and Punishment* 31 %—, cosa que no hacía
   cuando se medía por párrafo en lugar de por oración, porque un epub no
   conserva los saltos de párrafo y las tres daban 100 %.
4. Pide la curva de dificultad. Sobre *Notes from a Dead House*, el modelo
   recorre **487 ventanas de 130.104 palabras en 86 segundos** y devuelve una
   media de 1,73 sobre 2, además de decir si el libro se va complicando o
   soltando y cuáles son su capítulo más llevadero y su capítulo más exigente.
   La segunda vez tarda 0,02 s porque queda guardada.
5. Toca una palabra que no conoce. El trabajo local —lema, categoría
   gramatical, consulta al diccionario, desambiguación por similitud, IPA— son
   **40 milisegundos**. La explicación contextual, que sale a la red, es lo
   único lento, y por eso la ficha se pinta en dos etapas: lo local aparece al
   instante y la explicación se añade cuando llega.
6. Lee una frase en voz alta y recibe la corrección palabra por palabra.

Ese recorrido es la unidad de valor del producto: **no es un modelo con una
interfaz encima, es una secuencia de decisiones que el lector no podía tomar
antes**.

### 8.3 Escalado: el catálogo entero, precalculado

La curva de dificultad de un libro largo son minutos de cómputo. Hacer esperar
eso a cada visitante no es aceptable, de modo que el catálogo se precalcula.
Las mediciones que hicieron viable esa decisión:

| Entorno | Configuración | Ventanas/s | Factor |
|---|---|---|---|
| CPU (Ryzen 5 2600) | 12 hilos, lote 64 | 8,7 | 1× |
| GPU local (GTX 1650 SUPER) | fp32, lote 128 | 101,7 | 11,7× |
| GPU A100 (Colab) | fp16, lote grande | 2.022 | 232× |

*Cuadro 14. Rendimiento medido de extremo a extremo, incluida la tokenización
y las transferencias.*

Dos comprobaciones acompañan a ese cuadro, porque acelerar no puede costar
exactitud:

- **La GPU da los mismos números que la CPU.** Sobre 840 ventanas de *Crime and
  Punishment*, 839 son idénticas a tres decimales y una difiere en 0,001; el
  MAE es 0,0000012 sobre la escala 0–2.
- **Reagrupar en lotes distintos no puede mover un decimal**, y no es una
  suposición: como todas las ventanas ocupan exactamente 256 tokens tras
  truncar, no hay relleno, y 286 ventanas puntuadas de una en una y en un solo
  lote dan 286/286 valores idénticos con MAE 0,000000000.

Con 2.022 ventanas por segundo, **medir los 61.642 libros en inglés de Project
Gutenberg son unas 6,3 horas de A100**. El cuello de botella real resultó no
ser el modelo sino la descarga: en serie, a 0,3 libros/s, los libros tardarían
57 horas en bajar. Y no era la pausa de cortesía entre peticiones, era la
latencia —cada petición al espejo se pasa casi todo su tiempo esperando la ida
y vuelta—, así que con seis hilos esas esperas se solapan. Seis y no treinta a
propósito: el espejo lo mantiene alguien de forma gratuita, y cada hilo conserva
su pausa.

### 8.4 Dos decisiones de producto que merecen argumento

**Se ofrecen dos velocidades de análisis y siempre se dice cuál se usó.** El
vistazo rápido toma 30 capítulos repartidos por la obra y 2 ventanas de cada
uno; el análisis completo no muestrea. El número 30 no es redondo por gusto:
sale de la velocidad medida de la máquina. Y el resumen declara cuál de los dos
se ejecutó, porque un vistazo que presumiera de haber leído el libro entero
acabaría citado como si lo hubiera hecho.

**No se filtra el catálogo por contenido.** Se implementó un filtro basado en
las materias que asigna el propio Project Gutenberg —90 libros de 61.642— y
después se retiró, deliberadamente. El razonamiento: esto es una plataforma de
literatura, y la literatura es donde esas cosas aparecen. Filtrar por etiqueta
habría eliminado también obras que son literatura por derecho propio, como
*Fanny Hill*, perseguida judicialmente y relevante precisamente por eso. En su
lugar se usa un mecanismo que ya existía: la ficha de cada libro trae un campo
de aviso que se muestra como «Antes de empezar». **Se informa al lector y se le
deja elegir; no se elige por él.** Es una decisión discutible y por eso se
argumenta en lugar de ocultarse.

---

## 9. Limitaciones

1. **La escala 0–2 es propia y no es una certificación.** El MCER fue el ancla
   del entrenamiento. LiteraLevel no acredita ningún nivel, y decirlo en el
   documento no basta: la aplicación lo repite en pantalla.
2. **La escala está comprimida.** El ajuste contra el ancla real ronda
   `predicho ≈ 0,72 × real + 0,38`, así que los niveles bajos se sobreestiman y
   los altos se subestiman. Es la razón de mostrar bandas y no decimales.
3. **Las etiquetas del catálogo heredado no son fiables** (Cuadro 3). Son
   predicciones de un modelo v1 sobre las primeras ~190 palabras. La remedición
   está en curso y es el trabajo pendiente más importante.
4. **De los 1.197 libros del catálogo actual, solo 148 son descargables.** Los
   1.049 de StoryWeaver no tienen fichero que abrir.
5. **Los tamaños muestrales de la validación externa son pequeños**: 38 textos
   en Colab, 45 en local, con 3 textos en A1. Una diferencia de 0,05 entre dos
   niveles adyacentes con esas *n* no es significativa; lo que se afirma es el
   orden global, no cada comparación por pares.
6. **La validación no es enteramente independiente de la exploración.** El
   corpus de British Council se usó primero para diagnosticar (descubrir que el
   modelo no sabe leer menús) y después para validar. El filtro de prosa se
   fijó a priori precisamente para acotar ese problema, pero el conjunto ha
   sido mirado y ya no es virgen.
7. **La longitud del texto es un confusor en el corpus de examen.** Contar
   palabras alcanza 0,807 donde el modelo alcanza 0,854 (Cuadro 11).
8. **El modelo solo mide prosa continua en inglés.** Poesía, teatro, diálogo
   muy fragmentado y cualquier lengua distinta del inglés quedan fuera.
9. **El corpus de anclaje MCER es pequeño** (654 documentos aceptados) y el
   guion de entrenamiento del v4 vive en Google Drive, no en el repositorio.
   Las cifras del apartado 7.4 se reportan tal como constan en la tarjeta del
   modelo.
10. **Dos corpus no se pueden redistribuir**: British Council tiene derechos y
    el corpus de validación de 144 documentos no acompaña al repositorio, de
    modo que las cifras de 0,908 y 97,2 % **no son verificables clonando el
    proyecto**. Lo que sí se reproduce en cualquier máquina es el Cuadro 10.
11. **El cuaderno corre entero en un Colab limpio, pero correr no es
    recalcular.** Los pesos del v4 están publicados en Hugging Face
    (`MikeMaki1763/literalevel-v4`, repositorio público, descarga sin
    credenciales), así que el cuaderno se ejecuta de principio a fin y demuestra
    la inferencia sobre texto real. Lo que **no** recalcula son las métricas del
    v4 —el 0,908 y el 97,2 %—, y eso no se arregla publicando nada: depende del
    corpus de anclaje MCER, que incluye material con derechos y no se puede
    redistribuir.
12. **La aplicación no está desplegada de forma permanente.** El enlace actual
    es un túnel temporal. El consumo medido —1,05 GB de memoria residente, con
    picos realistas de 1,2 a 1,5 GB— descarta cualquier plan gratuito de 512 MB.
13. **La prueba de usuario tiene n = 1.** Esmeralda es una sola lectora. Su
    valor es cualitativo y de diagnóstico, no estadístico: sirve para encontrar
    fallos de usabilidad graves —y encontró varios—, no para estimar
    satisfacción media.
14. **La explicación contextual depende de un servicio externo de pago.** Sin
    clave, la aplicación sigue funcionando en todo lo que no usa red
    —diccionario, fonética, audio de Wiktionary, buscador y puntuación— pero se
    apagan la explicación en contexto y la corrección de pronunciación.

---

## 10. Trabajo futuro

1. Terminar la remedición del catálogo completo y sustituir las etiquetas
   heredadas por medidas del v4 sobre el libro entero.
2. Reunir un corpus de anclaje MCER redistribuible, que es lo único que
   permitiría recalcular las métricas del v4 en lugar de citarlas. Los pesos ya
   están publicados; el corpus es el que no puede estarlo.
3. Ampliar el corpus de anclaje MCER, que hoy es el eslabón más delgado de la
   cadena de evidencia.
4. Calibrar explícitamente la escala comprimida (una transformación afín de dos
   parámetros ajustada sobre entrenamiento, sin tocar los pesos) y comprobar si
   el orden se conserva tras calibrar.
5. Repetir la prueba de usuario con cinco o seis lectores de perfiles
   distintos, que según Nielsen (2000) es donde se detecta la mayor parte de los
   problemas de usabilidad.
6. Medir el efecto real sobre el abandono: comparar la tasa de libros
   terminados entre lectores que eligen con recomendación y sin ella. Es la
   única métrica que verdaderamente valida la propuesta.

---

## 11. Conclusiones

**Se cumplió el objetivo ordinal, que era el objetivo.** Sobre textos externos
con nivel MCER oficial, el modelo desplegado ordena los niveles de forma
estrictamente creciente (0,5040 · 0,5480 · 0,9276 · 1,2478 · 1,4952), con una
correlación de Spearman de 0,908 en validación ciega y el 97,2 % de los
documentos dentro de un nivel de error. Para el problema planteado —elegir qué
leer— acertar el orden es lo que importa; acertar la letra exacta es un lujo.

**El cuello de botella nunca fue el algoritmo, fue la representación del
texto.** La progresión completa lo demuestra sobre un mismo conjunto de prueba:
tres variables clásicas dan 1,39 niveles de error ordinal tanto con regresión
logística como con XGBoost; un embedding lo baja a 0,93; leer el texto crudo
con atención lo baja a 0,67. Aumentar la potencia del clasificador sobre una
representación pobre no sirvió de nada, y eso también es un resultado.

**Escalar el corpus no siempre mejora nada, y conviene decirlo.** Multiplicar
por 2.500 el corpus de referencia léxica —de 18 libros a los 45.345 del SPGC—
dejó la correlación en −0,326 frente a −0,330. La ley de Zipf explica por qué.
El paso se conservó por cobertura, no por métrica, y así se reporta.

**La velocidad se ganó sin mover un decimal, y se demostró.** Doce hilos y
lotes de 64 en CPU, fp32 con lote 128 en GPU: +24 % y ×11,7 respectivamente,
con 839 de 840 ventanas idénticas a tres decimales. Y se rechazaron dos
palancas más rápidas —int8 y fp16 en la tarjeta local— porque una desviaba
0,210 sobre una escala de 0 a 2 y la otra era 4,8 veces más lenta. **Medir
antes de optimizar, y medir también lo que se descarta.**

**Lo que convierte esto en un producto no es el modelo, es lo que se hizo con
lo que dijo una lectora de quince años.** Un ciclo completo —observar, escuchar
la queja, diagnosticar el fallo propio y corregirlo— vale más que un punto de
correlación. Ese ciclo se documenta en el documento de estrategia, y su
resultado son seis etiquetas reescritas, cinco paletas verificadas contra el
criterio de contraste WCAG AA y una interfaz que se puede usar con el pulgar.

**Y queda pendiente lo que más pesa.** La aplicación funciona, pero su enlace
es temporal; el catálogo se está remidiendo; y el cuaderno, aunque ya corre
entero desde los pesos publicados, cita las métricas del v4 en vez de
recalcularlas, porque su corpus de anclaje no es redistribuible. Las tres cosas están
planificadas con coste y criterio de terminado en el documento de estrategia.

---

## Declaración de alcance

LiteraLevel es una herramienta de apoyo a la lectura. **No es un instrumento de
evaluación ni de certificación lingüística.** No debe usarse para asignar
calificaciones, para decidir la admisión de una persona a un programa, para
acreditar un nivel del Marco Común Europeo de Referencia ni para ninguna
decisión con consecuencias para el evaluado. La escala 0–2 es propia; las
letras A1 a C2 son el ancla con la que se entrenó el modelo y se muestran
únicamente como orientación.

El sistema mide dificultad lingüística de prosa continua en inglés. No mide
calidad literaria, no mide comprensión del lector y no emite juicios sobre el
contenido de las obras. El catálogo no se filtra por contenido: se informa al
lector mediante un aviso en la ficha del libro y la decisión queda en sus
manos.

Los datos personales del lector —los libros empezados, el vocabulario
consultado y el perfil de nivel— se guardan separados por sesión y no se
comparten entre visitantes. Solo la caché de definiciones se comparte, por ser
contenido de diccionario y no historial de nadie. Ningún texto con derechos se
distribuye ni se imprime fuera del entorno de cómputo: de los corpus con
licencia restrictiva solo salen estadísticas agregadas.

---

## Referencias

Abid, A., Abdalla, A., Abid, A., Khan, D., Alfozan, A., & Zou, J. (2019).
*Gradio: Hassle-free sharing and testing of ML models in the wild*
(arXiv:1906.02569). arXiv. https://arxiv.org/abs/1906.02569

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. En
*Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge
Discovery and Data Mining* (pp. 785–794). ACM.
https://doi.org/10.1145/2939672.2939785

Council of Europe. (2020). *Common European Framework of Reference for
Languages: Learning, teaching, assessment — Companion volume*. Council of
Europe Publishing.

Crossley, S., Heintz, A., Choi, J. S., Batchelor, J., Karimi, M., &
Malatinszky, A. (2023). A large-scaled corpus for assessing text readability.
*Behavior Research Methods, 55*(2), 491–507.
https://doi.org/10.3758/s13428-022-01802-x

Day, R. R., & Bamford, J. (1998). *Extensive reading in the second language
classroom*. Cambridge University Press.

Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of
experiments examining the effects of extrinsic rewards on intrinsic motivation.
*Psychological Bulletin, 125*(6), 627–668.
https://doi.org/10.1037/0033-2909.125.6.627

Gerlach, M., & Font-Clos, F. (2018). *Standardized Project Gutenberg Corpus
(SPGC)* [Conjunto de datos]. Zenodo. https://doi.org/10.5281/zenodo.2422561

Gerlach, M., & Font-Clos, F. (2020). A standardized Project Gutenberg corpus
for statistical analysis of natural language and quantitative linguistics.
*Entropy, 22*(1), 126. https://doi.org/10.3390/e22010126

Hu, M., & Nation, P. (2000). Unknown vocabulary density and reading
comprehension. *Reading in a Foreign Language, 13*(1), 403–430.

Krashen, S. D. (1985). *The input hypothesis: Issues and implications*.
Longman.

Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M.,
Zettlemoyer, L., & Stoyanov, V. (2019). *RoBERTa: A robustly optimized BERT
pretraining approach* (arXiv:1907.11692). arXiv.
https://arxiv.org/abs/1907.11692

Nakanishi, T. (2015). A meta-analysis of extensive reading research. *TESOL
Quarterly, 49*(1), 6–37. https://doi.org/10.1002/tesq.157

Nation, I. S. P. (2013). *Learning vocabulary in another language* (2ª ed.).
Cambridge University Press.

Nielsen, J. (2000, 18 de marzo). *Why you only need to test with 5 users*.
Nielsen Norman Group.
https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel,
O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J.,
Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011).
Scikit-learn: Machine learning in Python. *Journal of Machine Learning
Research, 12*, 2825–2830.

Project Gutenberg. (2026). *Project Gutenberg* [Biblioteca digital].
https://www.gutenberg.org

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using
Siamese BERT-networks. En *Proceedings of the 2019 Conference on Empirical
Methods in Natural Language Processing* (pp. 3982–3992). Association for
Computational Linguistics. https://doi.org/10.18653/v1/D19-1410

Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). *DistilBERT, a distilled
version of BERT: Smaller, faster, cheaper and lighter* (arXiv:1910.01108).
arXiv. https://arxiv.org/abs/1910.01108

Vajjala, S., & Lučić, I. (2018). OneStopEnglish corpus: A new corpus for
automatic readability assessment and text simplification. En *Proceedings of
the 13th Workshop on Innovative Use of NLP for Building Educational
Applications* (pp. 297–304). Association for Computational Linguistics.
https://doi.org/10.18653/v1/W18-0535

Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P.,
Rault, T., Louf, R., Funtowicz, M., Davison, J., Shleifer, S., von Platen, P.,
Ma, C., Jernite, Y., Plu, J., Xu, C., Le Scao, T., Gugger, S., … Rush, A. M.
(2020). Transformers: State-of-the-art natural language processing. En
*Proceedings of the 2020 Conference on Empirical Methods in Natural Language
Processing: System Demonstrations* (pp. 38–45). Association for Computational
Linguistics. https://doi.org/10.18653/v1/2020.emnlp-demos.6

World Wide Web Consortium. (2023). *Web Content Accessibility Guidelines (WCAG)
2.2*. W3C. https://www.w3.org/TR/WCAG22/

Ylönen, T. (2022). Wiktextract: Wiktionary as machine-readable structured data.
En *Proceedings of the 13th Language Resources and Evaluation Conference*
(pp. 1317–1325). European Language Resources Association.

Zaharia, M., Xin, R. S., Wendell, P., Das, T., Armbrust, M., Dave, A., Meng,
X., Rosen, J., Venkataraman, S., Franklin, M. J., Ghodsi, A., Gonzalez, J.,
Shenker, S., & Stoica, I. (2016). Apache Spark: A unified engine for big data
processing. *Communications of the ACM, 59*(11), 56–65.
https://doi.org/10.1145/2934664

Zipf, G. K. (1949). *Human behavior and the principle of least effort*.
Addison-Wesley.
