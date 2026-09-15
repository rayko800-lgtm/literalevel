# LiteraLevel: medición automática de la dificultad de lectura en inglés y su entrega a un lector real

**Proyecto integrador — Módulo 5 (Integrador)**
Diplomado en Ciencia de Datos, FES Acatlán (UNAM), Generación 34
Profesor: Mtro. Fernando Barranco Rodríguez
Autor: Miguel Reyes Carrillo
Septiembre de 2026

> **Dónde vive la Estrategia, que no es lo mismo aquí y en el PDF.** La rúbrica
> la pide como entregable propio *y* como sección del documento. En el PDF
> (`documento.pdf`) está **desarrollada completa** en su apartado, en el lugar
> que le toca por orden. En esta copia de lectura se **resume** en el apartado 3
> y el desarrollo va aparte, en `estrategia.md`, por extensión. No es una
> contradicción: es que el entregable es el PDF y este `.md` es la copia de
> lectura. Si buscas algo de estrategia y no está aquí, está en el PDF o en
> `estrategia.md`.
>
> Este `.md` es la copia de lectura; el entregable es `documento.pdf`. Los
> dos dicen lo mismo, pero **la numeración de los cuadros no coincide**: el
> PDF numera además las tablas que aquí van como listas dentro del texto.
> Las referencias internas de cada archivo apuntan a su propia numeración.

---

## Resumen

Aprender inglés leyendo funciona, pero solo si el libro está al nivel de quien
lo abre. Un lector que elige un libro demasiado difícil no aprende: lo
abandona. Y hoy no hay forma sencilla de saber, antes de empezar, si *ese*
libro concreto está a su alcance.

LiteraLevel es una aplicación que responde esa pregunta. Le da al lector un
número entre 0 y 2 que dice cuánta dificultad tiene un texto en inglés, y lo
hace leyendo el texto de verdad, no contando páginas. Con ese número le busca
libros que le queden a mano, se los abre dentro de la propia aplicación, le
enseña la dificultad capítulo a capítulo —los libros no son igual de difíciles
de principio a fin—, le explica cualquier palabra en la frase en la que
aparece y le corrige la pronunciación cuando lee en voz alta.

Debajo hay un modelo de lenguaje pequeño (`distilroberta-base`) afinado para
predecir dificultad como un número continuo. En la validación interna —144 documentos
reservados del corpus de anclaje, los mismos con los que se eligió el punto de
control— alcanza una correlación de Spearman de 0,908 con el nivel de referencia y, sobre un corpus
externo que no se usó para ajustar los pesos —aunque sí se exploró durante
el desarrollo, y eso se detalla en la limitación 6—, ordena los niveles del
Marco Común Europeo de forma
estrictamente creciente: A1 0,5040 (n=3) · A2 0,5561 (n=8) · B1 0,9276 (n=12) ·
B2 1,2414 (n=12) · C1 1,4952 (n=12). Ese orden —no el acierto exacto— es el
resultado que sostiene el trabajo, **con una salvedad que conviene leer junto
a las cifras**: el escalón A1–A2 es de 0,052 sobre desviaciones de 0,111 y
0,223, y descansa en tres textos. Está dentro del ruido. Los tres escalones
siguientes, no.

Conviene decirlo desde la primera página: **la escala 0–2 es propia y
LiteraLevel no certifica ningún nivel del Marco Común Europeo**. Las letras
A1 a C2 fueron el ancla con la que se entrenó el modelo, no un título que la
aplicación expida. Sirven para elegir qué leer, no para acreditar nada.

La entrega usa **Angular como interfaz y una API FastAPI sobre el motor Python**;
Gradio 6.26 se conserva como respaldo. Las pruebas de usabilidad de la interfaz
anterior con Esmeralda y Laura motivaron esta separación, pero no equivalen a
una validación de usuario de todos los cambios posteriores. El catálogo medido
contiene **53.179 libros** en inglés de
dominio público de Project Gutenberg, leídos enteros por el modelo, capítulo a
capítulo. La última tanda, en una GPU gratuita, tardó 55 minutos: el cuello de
botella nunca fue el modelo, sino leer y guardar los archivos.

**Palabras clave:** legibilidad automática, MCER, adquisición de segundas
lenguas, lectura extensiva, transformers, Project Gutenberg, Angular.

---

## 1. Introducción y motivación

Unos 1.500 millones de personas estudian inglés como segunda lengua. De todos
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
material externo que no intervino en el ajuste de los pesos, y (b) sea lo
bastante rápida y
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
sistema. El recorte va dentro del sumatorio, que es lo que hace el código.

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

C1 y C2 se cumplen y se documentan en 7.4 y 7.5. C3 se cumplió con la interfaz
anterior, de Gradio, y se documenta en el documento de estrategia; sobre el front
de Angular que se entrega está pendiente (accionable A8).

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
- **Ciclo de usuario real.** Una lectora de quince años, prima del autor y ajena
  al proyecto, usó
  la aplicación, dijo *«o yo soy muy tonta para esto»* —que es un fallo de
  diseño, no suyo— y de ahí salieron seis etiquetas reescritas, cinco paletas
  de color, objetivos táctiles de 44 px y esquinas redondeadas.
- **Accionables.** Diez, con coste y criterio de terminado; los
  tres primeros son publicar modelo y diccionario, desplegar en enlace
  permanente y terminar la remedición del catálogo, que se completó el 12 de
  septiembre de 2026.

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
| **OneStopEnglish** | Corpus de **afinado** de la variante v2 (151 artículos), validación ordinal en 3 niveles sobre los 38 reservados y **validación externa del v4** (560 unidades, Cuadro 13b) | 567 textos (189 por nivel) | GitHub (Vajjala & Lučić, 2018) | CC BY-SA 4.0 |
| **British Council LearnEnglish** | Validación externa contra niveles MCER oficiales | 59 textos A1–C1 | Descarga de los PDF públicos, con la URL y el SHA-256 de cada uno en un manifiesto | Con derechos: no se distribuye ni se imprime texto, pero se reconstruye y se verifica byte a byte |
| **SPGC** (Standardized Project Gutenberg Corpus) | Lista global de frecuencia de palabras (solo conteos, sin texto) | 45.345 libros en inglés de 55.905 | Zenodo, registro 2422561 (Gerlach & Font-Clos, 2018, 2020) | Abierta |
| **Project Gutenberg** | Catálogo de obras a medir y a leer dentro de la app | 79.337 entradas; 61.642 libros de texto en inglés, instantánea del 7 de septiembre de 2026 | Catálogo oficial + espejo `gutenberg.pglaf.org` | Dominio público |
| **Kaikki / Wiktionary** | Diccionario, IPA británica y americana, audio | 1.487.639 filas en SQLite (243 MB); IPA en 46.794 y audio en 7.003 (§6.4) | Volcado de kaikki.org (Ylönen, 2022) | Libre |
| **ELG CEFR English** | Corpus de anclaje MCER: afinado y validación interna del v4 | 712 documentos; 654 aceptados | European Language Grid, descargado de Hugging Face (Breuker, 2023) | No comercial: CC BY-NC-SA 4.0 según el guion de entrenamiento; CC BY-NC 4.0 según su ficha en UniversalCEFR |
| **StoryWeaver** (Pratham Books) | Textos libres del catálogo, medidos con el v4 | 14.506 textos | Plataforma abierta (Pratham Books, s. f.) | CC BY 4.0 |
| **Let's Read** (The Asia Foundation) | Textos libres del catálogo, medidos con el v4 | 328 textos | Biblioteca digital (The Asia Foundation, s. f.) | CC BY 4.0 (318) y CC BY 3.0 (10) |
| **African Storybook** (Saide) | Textos libres del catálogo, medidos con el v4 | 280 textos | Biblioteca digital (Saide, s. f.) | CC BY |
| **VOA Learning English** | Textos libres del catálogo, medidos con el v4 | 253 textos | Sitio de Voice of America (Voice of America, s. f.) | Dominio público |
| **Common Pile** (`project_gutenberg`) | Texto de los libros de Gutenberg para medir el catálogo | 57.226 textos descargados | Hugging Face (Kandpal et al., 2025) | Dominio público |
| **CMUdict** | Fonética americana donde Wiktionary no la trae (corrección de voz) | 126.052 palabras | GitHub de Carnegie Mellon University (Carnegie Mellon University, s. f.) | BSD de dos cláusulas |
| **Catálogo heredado** (StoryWeaver / Global Digital Library) | Registros del catálogo anterior, retirado el 12 de septiembre de 2026; no son los 14.506 textos de arriba | 1.049 registros | API pública de contenidos | Abierta, pero sin descarga de texto |

*Cuadro 2. Fuentes de datos, con volumen y procedencia. Los recuentos de textos libres son de `740eb84`, el catálogo publicado en el reinicio 21.*

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
mensajes de texto. Se definió un filtro de prosa continua por dos vías
independientes —por palabras clave del título y por estructura (≥7 palabras por
línea y densidad de puntuación final de frase en el intervalo (0, 0,11])—, que
coinciden en 53 de 59 casos, el 89,8 %.

**Ese filtro es el del análisis, no el que aplica la aplicación**, y conviene no
confundirlos porque dan resultados distintos. Lo que corre en producción es
`scoring.continuous_prose`, con otras reglas: al menos 150 palabras, al menos
cuatro frases, entre 5 y 55 palabras de media por frase, y rechazo si más del
17,5 % de las palabras vive en líneas de maquetado —viñetas o líneas de cuatro
palabras o menos— o si más del 35 % de las líneas son cortas. Coinciden en el
propósito —tirar menús, listas y tablas— pero no en los umbrales.

**Y aquí hay que contar la secuencia real, porque el filtro no se fijó antes de
mirar ningún resultado.** El orden fue el contrario: primero se puntuaron los
59 textos, se vio que el modelo daba resultados absurdos con el menú y el
tablero de salidas, y **de ese diagnóstico salió la idea del filtro**. Que las
dos vías se definieran sin volver a mirar las puntuaciones, y que coincidan
entre sí en el 89,8 % de los casos, es lo que impide que sea un filtro hecho a
medida de las notas. Pero no es un criterio *a priori*, y llamarlo así sería
regalarse una garantía que no se tiene.

**(b) Las etiquetas del catálogo heredado no eran fiables, y por eso se
sustituyó.** El catálogo con el que la aplicación funcionó hasta el 12 de
septiembre de 2026 tenía **1.197 libros** —no
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
121 libros de 1.197. Esas etiquetas servían para ordenar y filtrar de forma
aproximada, **no eran una medida fiable libro a libro**. Es la razón de ser del
precálculo descrito en 8.3: remedir todo el catálogo, libro entero, con el
modelo final.

**Y se remidió.** El 12 de septiembre de 2026 terminó: **53.179 libros de
Project Gutenberg y 585.111 capítulos**, medidos enteros por el v4, sin un solo
libro medido dos veces. Es lo que usa hoy la aplicación, y su reparto dice lo
contrario que el heredado:

| Nivel | Libros medidos | Libros literarios* |
|---|---|---|
| A1 | 1 | 288 entre A1 y B1 |
| A2 | 40 | |
| B1 | 557 | |
| B2 | 3.127 | 1.676 |
| C1 | 23.455 | |
| C2 | 25.999 | |
| **Total** | **53.179** | |

*Cuadro 3b. Reparto del catálogo medido por el v4 (media 1,742 sobre 2), con la corrección de
`correcciones_catalogo.csv` aplicada (PG2242 pasa de B1 a C1), que es como lo cuenta la aplicación.
\*Los que la aplicación ofrece al recomendar por nivel: ficción, cuentos,
lecturas escolares, poesía y teatro. Entre los libros «fáciles» había índices,
anuarios, mapas y tablas de números, que puntúan bajo precisamente porque son
listas.*

La literatura del XIX es, sobre todo, C1–C2, y un lector B1 apenas tiene libros
enteros a su medida. Lo que sí tiene son **capítulos**: 3.644 en 1.499 libros
quedan a su alcance, y la aplicación se los ofrece (8.1). Dos cautelas: la letra
es orientativa, porque la escala del modelo sale comprimida y desplazada hacia
arriba (7.5), y el reparto describe el catálogo de Gutenberg, no la dificultad
de la lectura en inglés en general.

**Y fuera de Gutenberg.** A fecha de `740eb84`, publicado en el reinicio 21, el catálogo suma además **15.367 textos de licencia libre** medidos con el v4: 14.506 de StoryWeaver, 328 de Let's Read, 280 de African Storybook y 253 de VOA. Por nivel, 766 A1, 5.696 A2, 5.491 B1, 2.524 B2, 777 C1 y 113 C2. Desde ese reinicio, un bloque de tres o más cuentos se mide también sin cada uno de ellos: si quitar uno solo mueve la medida más de 0,5 (un margen fijado antes de medir la tanda), los demás se quedan con la medida sin él, y ese texto conserva la del bloque entero —la regla no lo baja de nivel— y queda marcado. Son 92 textos, y frente al reinicio 19 cambian de letra 225: 42 suben y 183 bajan. En dos de los bloques cuyos cuentos subieron de A2 a B2, quitar el texto marcado al bloque tal como estaba antes deja la medida en A2, así que esas subidas están por revisar (`54d6591`). Lo que se quedó fuera se contó en `377a650`, cuando eran 15.357: otros 894 textos libres se quedaron fuera; la salida de `cerrar_corpus.py` dice: «medidos: 15357 (texto 11039, bloque 4318) | sin medida, fuera: 894». Recontados sobre las medidas en disco: 776 tienen menos de 150 palabras, 878 cayeron en un bloque que el filtro de prosa continua rechazó (260 bloques: 215 con pinta de lista, menú o tabla, 32 con frases demasiado cortas o largas y 13 con menos de cuatro frases), 15 no llegaron a formar bloque y 1 se rechazó solo; 828 son de StoryWeaver. Es donde está la lectura de nivel bajo que Gutenberg no tiene: 11.953 textos entre A1 y B1, frente a 598 libros. Cuatro decisiones sobre ellos, publicadas a fecha de `7c09d90`. **(1)** Un cuento corto medido dentro de un bloque lleva la dificultad del bloque, no la suya, y la API lo marca (`medido_en_bloque`) para que la tarjeta y la ficha lo digan. **(2)** La atribución que exige su licencia se enseña al final del texto, pero no se puntúa: medida con el cuento, esa línea en español con su URL subía «Doggie is Happy» de 0,007 a 0,349 en «¿Cómo de difícil es?»; en el Space da 0,007. **(3)** El texto que se sirve sale sin caracteres U+FEFF, sin párrafos repetidos seguidos y sin páginas duplicadas dentro de un párrafo; el que se midió no cambia, y `catalogo_externo.csv` sale idéntico byte a byte al regenerarlo. Cambian 1.442 textos servidos, 185 de ellos por repeticiones, y los estribillos de una frase se conservan. **(4)** Como no tienen descargas de Gutenberg, al recomendar por nivel ocupan un tercio de las tarjetas (puestos 2, 5, 8…), ordenados por cercanía al nivel del lector; con 30 tarjetas, A2 recibe 11 y B1 10, sin cuentos en común entre las dos franjas.

**(c) De aquellos 1.197 libros, solo 148 se podían abrir.** Eran los de Project
Gutenberg. Los otros 1.049 provenían de StoryWeaver y no tenían fichero
descargable, de modo que aparecían en el desplegable de lectura como opciones
muertas. Peor aún: su identificador se había usado para construir enlaces a
Gutenberg extrayendo sus dígitos, con lo que `SWgdlgdl201` apuntaba al libro
201 de Gutenberg, que es otra obra. Un enlace al libro equivocado es peor que
ningún enlace. **En el catálogo medido los 53.179 libros se pueden abrir**, y la
aplicación los descarga en `.txt`, el mismo texto con el que se midieron, para
que los capítulos del lector sean los de la curva.

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

**Dificultad frente a longitud, la variable incómoda.** Sobre los 47 textos de
British Council medibles en local, contar las palabras del texto —sin modelo
alguno— alcanza una correlación de Spearman de **0,807** con el nivel oficial.
El modelo alcanza 0,860. Es decir: en ese corpus, nivel y longitud están
confundidos, porque los materiales de examen gradúan también la extensión de la
tarea. Publicar ese *baseline* antes de que lo pregunte el evaluador es más
creíble que omitirlo; en 7.5 se cuantifica cuánta señal aporta el modelo por
encima de él.

**Dificultad frente a dominio.** El nivel del texto está correlacionado con su
tipo documental. Al filtrar los 59 textos de British Council a prosa continua,
el nivel A1 desaparece casi por completo y el rango evaluable **de esa tanda de
análisis** se encoge de cinco niveles a cuatro (A2–C1): el catálogo gratuito de
British Council no tiene C2, así que el corpus nunca tuvo seis. La reproducción
local del Cuadro 11 sí conserva los cinco, con tres textos en A1, porque filtra
con otras reglas. Por eso el *baseline* de contar palabras cae de 0,879
a 0,765 al filtrar: parte de la señal del conjunto completo era simplemente que
los textos A1 son cortos. Las correlaciones antes y después del filtro **no son
comparables entre sí**, y se reportan por separado. Los conjuntos de textos que
aparecen aquí y en el 7.4 están todos, con lo que se puede y no se puede hacer
con cada uno, en el Cuadro 9.

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
Los números están en el Cuadro 8.

---

## 6. Procesamiento de datos

Cada transformación se documenta con su justificación. La regla que se siguió
es la del módulo 1 del diplomado: **no se transforma sin medir qué se rompió**.

### 6.1 Sobre el texto de entrada

| # | Transformación | Por qué | Evidencia / consecuencia |
|---|---|---|---|
| T1 | **Filtro de prosa continua** antes de puntuar: se rechaza si más del 17,5 % de las palabras viven en líneas de maquetado, o si más del 35 % de las líneas son cortas | El modelo solo vio prosa; puntuar un menú da un número sin significado | El filtro estaba muerto en producción: se normalizaba *antes* de comprobar, y `normalize()` colapsa los saltos de línea, así que el detector recibía siempre una sola línea. Una carta de menú de 432 palabras se puntuaba como prosa. Corregido: el filtro va sobre el texto crudo |
| T2 | **Normalización de espacios** (`\s+` → espacio) después del filtro | Estabiliza el troceado en bloques | Sin efecto sobre la puntuación; solo sobre el corte |
| T3 | **Troceado en bloques de 250 palabras, mínimo 150** | Es la unidad con la que se entrenó; un bloque más corto no tiene señal suficiente | Constante del entrenamiento: cambiarla invalidaría las métricas reportadas |
| T4 | **Truncado a 256 tokens** | Límite de contexto del modelo | Medido: de 200 bloques de 250 palabras, el **100 %** llega exactamente a 256 tokens tras truncar, porque en prosa inglesa real 250 palabras superan siempre los 256 BPE. Dentro de un texto troceado así no hay relleno; agrupando ventanas de capítulos distintos sí lo hay, y eso se trata en §8.3 |
| T5 | **Recorte de la licencia de Gutenberg** por las marcas START/END, dentro del capítulo | 2.900 de las 5.042 palabras del capítulo XII de *Alice* son texto legal | Sin esto, el modelo puntuaba texto jurídico como narrativa y la ficha listaba «gutenberg» entre las palabras más frecuentes del libro |
| T6 | **Descarte de portada, índice y portadilla** por la etiqueta «Antes del primer capítulo» | 4.957 palabras de paratexto se puntuaban como novela | Se probó descartar por el filtro de prosa continua y se rechazó: eliminaba dos capítulos reales de *Alice* |
| T7 | **Muestreo de hasta 8 bloques repartidos por el documento** para la puntuación rápida | Dar un número en segundos, no en minutos | Cuantificado: 8 bloques dan 1,784 y el recorrido completo de las 23 ventanas del mismo capítulo da 1,743. El atajo se desvía 0,041 sobre una escala de 0 a 2 |
| T8 | **Recorte de entradas del usuario en el servidor** (40 caracteres por palabra, 400 por oración, 20 MB por fichero y, desde `9eb3c91`, 100 MB descomprimidos por EPUB) | El límite del navegador es una sugerencia, no una defensa | Una cadena de 3.000 caracteres pasaba el filtro de «máximo cuatro palabras» y se pintaba como encabezado: 9.312 caracteres llenando la pantalla del móvil |

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

Dos datos de cobertura que condicionan el diseño de la aplicación. Sobre las
1.487.639 entradas, solo **7.003 (0,5 %) traen audio de pronunciación** y
**46.794 (3,1 %) traen transcripción fonética**; con las dos variantes —la
británica y la americana— quedan **33.635 (2,3 %)**. Pero eso cuenta entradas, y
el diccionario es en su mayoría palabra rara mientras que un libro es en su
mayoría palabra corriente. Medido por el lado del lector —400 palabras tomadas
al azar del texto de *Crime and Punishment* y resueltas por el mismo camino que
usa la aplicación, lematización incluida—, **el 58 % llega con fonética y el
32 % con audio grabado**.

Las dos mediciones apuntan a lo mismo desde sitios distintos: **dos de cada tres
consultas necesitan síntesis de voz**, y esa es la medición que justificó
paralelizar las dos llamadas de red de una consulta en lugar de encadenarlas. La
ficha de la palabra lo dice cuando toca: si no hay ni transcripción ni audio ni
clave para generarlo, escribe *«de esta palabra no hay pronunciación»* en lugar
de dejar el hueco en blanco.

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
cosas son ciertas.

### 7.2 Progresión de modelos

| Modelo | Representación del texto | Exactitud (6 clases) | Error ordinal medio | Tanda |
|---|---|---|---|---|
| Regresión logística | 3 variables clásicas | 0,29 | 1,39 | histórica |
| XGBoost | 3 variables clásicas | 0,28 | 1,42 | histórica |
| Regresión logística | 3 variables clásicas | **0,313** | **1,295** | recalculada |
| Regresión logística | **17 variables** | **0,352** | **1,061** | recalculada |
| XGBoost | **17 variables** | **0,340** | **1,081** | recalculada |
| Regresión logística | Embedding MiniLM (384 d) | 0,37 | 0,93 | histórica |
| Regresión logística | Híbrido (embedding + 3 variables) | 0,37 | 0,91 | histórica |
| **`roberta-base` afinado** | **Texto crudo, atención** | **0,46** | **0,67** | histórica |

*Cuadro 7. Progresión de modelos sobre los mismos 950 extractos reservados,
con la tanda de la que procede cada fila. La mejora acompaña siempre al
enriquecimiento de la
representación, no a la complejidad del clasificador.*

La lectura del cuadro es la tesis metodológica del trabajo: **cada vez que se
le dio al modelo una representación más rica del texto, el desempeño subió; y
cuando solo se aumentó la potencia del clasificador sobre la misma
representación pobre, no subió**. XGBoost sobre tres variables es marginalmente
peor que una regresión logística sobre las mismas tres variables.

El modelo afinado directamente sobre el texto es un **`roberta-base`** de 125
millones de parámetros con cabeza de regresión sobre `BT_easiness`, y alcanza
además **RMSE 0,560** y **correlación de Pearson 0,89** con la etiqueta continua
real.

**Y aquí hay que evitar una confusión que el documento invitaba a hacer.** Ese
`roberta-base` **no es el modelo que se despliega**. El que va en la aplicación
es un `distilroberta-base` —la mitad de capas, 82 millones de parámetros— y se
entrenó sobre otro corpus, el de anclaje MCER, no sobre `BT_easiness`. Las
cifras de este apartado son del experimento sobre CLEAR; las del modelo
desplegado están en el §7.4 y no se pueden encadenar con estas. La diferencia
de calidad entre las dos arquitecturas sobre CLEAR **no se midió**, así que la
decisión de usar la destilada se tomó por tamaño y velocidad, no porque se
comprobara que costaba poco.

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
| Periodístico (OneStopEnglish) | 567 | 0,458 | *no comparable* |
| Exámenes MCER (British Council) | 59 | −0,239 | **0,175** |

*Cuadro 8. Matriz modelo × dominio. Correlación orientada con la dificultad
real; más alto es mejor.*

**Por qué la casilla de OneStopEnglish está vacía para v2, y no es un olvido.**
La cifra que ocupaba ese hueco —un 0,840 que
hacía ganar a v2 con holgura— estaba medida sobre los 567 textos completos,
y **v2 se afinó precisamente con 151 de los 189 artículos de ese corpus**. Es
decir: el 80 % de esos textos eran su propio entrenamiento, y se comparaban
contra un v1 que no los había visto nunca. No es que la cifra fuera falsa; es
que no medía lo que la tabla decía medir. Se retira en lugar de maquillarla.

Eso obliga a rebajar la conclusión que colgaba de ella. Lo que sigue en pie es
que **v1 gana en dificultad de lectura tipo CLEAR** —juicios de lectores
nativos sobre prosa continua—, con ventaja en las cuatro filas medidas
limpiamente. Lo que **ya no se sostiene con esta evidencia** es la afirmación
simétrica de que v2 gane donde la etiqueta es una graduación para aprendices:
la única fila que la respaldaba estaba contaminada, y la de British Council,
donde v2 sí aventaja a v1, tiene una correlación de 0,175 —demasiado baja para
sostener nada por sí sola—.

La decisión de qué escala presentar al usuario precede a la de qué modelo
desplegar; se eligió la escala anclada al MCER, y con ella el modelo
correspondiente. Esa decisión no cambia, pero conviene saber que se tomó con
menos evidencia de la que este cuadro aparentaba dar.

### 7.4 El modelo desplegado y su validación

El modelo en producción, **v4**, es un `distilroberta-base` (seis capas, 82
millones de parámetros) con cabeza de regresión, cuyos pesos ocupan 328 MB en
disco. Puntúa bloques de 250 palabras truncados a 256 tokens y promedia sin
ponderar, con un tope de **ocho ventanas por documento** repartidas a lo
largo del texto: es lo que mantiene el análisis en **alrededor de un segundo**
en una CPU —0,96 a 1,04 s medidos sobre ocho ventanas en el equipo del autor,
un Ryzen 5 2600—, y por eso un vistazo mide una muestra del texto y no el texto
entero. El precálculo del catálogo, en cambio, recorre el libro completo sin
muestrear y publica una dificultad por capítulo; esa remedición **terminó el
12 de septiembre de 2026** (accionable A3), y las letras del catálogo son ya las
medidas por el v4. Su escala interna es 0–5 —un valor por nivel MCER, con posiciones
intermedias (A1+, A2+, B1+, B2+)— y la pública es esa misma escala multiplicada
por 0,4. **El modelo es final y no se reentrena.**

**Antes de las cifras, las reglas del juego.** Por este apartado y por el
siguiente circulan **cinco conjuntos de textos distintos**, y confundirlos es
fácil porque cuatro de los cinco salen del mismo material de British Council. No
son subconjuntos ordenados unos de otros y sus tamaños no se restan entre sí. El
Cuadro 9 dice qué es cada uno, qué se mide con él y qué **no** se puede hacer
con él; el resto del apartado los cita por su nombre.

| Conjunto | n | De dónde sale | Qué se mide con él | Qué **no** se puede hacer con él |
|---|---|---|---|---|
| **Validación interna** | 144 | Partición de validación de ELG CEFR English, el corpus de anclaje MCER: 654 documentos aceptados, 510 de entrenamiento y 144 reservados | Exactitud, acierto dentro de ±1 nivel y Spearman 0,908 del modelo desplegado (Cuadro 10) | Presentarlo como validación externa. Sale del mismo corpus con el que se afinaron los pesos, y sobre él se eligió el punto de control, así que su 0,908 no es comparable con las cifras de British Council |
| **British Council, tanda de Colab** | 38 | Extracción de los PDF hecha en Colab durante el entrenamiento, con su propio filtro | Spearman 0,829 y el 100 % dentro de ±1 (Cuadro 10); las cuatro medias por nivel que ajustan la recta de compresión (7.5) | Restarlo de los 47. Es otra tanda, con otra extracción y otro filtro: la diferencia no son «nueve textos concretos» que se puedan nombrar |
| **British Council, reproducción local** | 47 | Los 59 publicados, menos 2 sin cuerpo localizable al extraer el PDF y 10 rechazados por el filtro de prosa (Cuadro 12) | **El resultado principal**: el orden creciente por nivel (Cuadro 11) y las tres cifras del *baseline* —0,860, 0,807 y 0,668— del Cuadro 13 | Leerlo como «los textos que la aplicación aceptaría». El validador local filtra más flojo que la app (7.7) |
| **Los que pasan el filtro completo** | 36 | Esos mismos 47 refiltrados conservando los saltos de línea, es decir con las cuatro reglas del filtro de prosa continua activas | Cuánto depende el conjunto evaluado de una regla que el validador desactiva: sobreviven 36 y A1 se queda con un solo texto (7.7) | Sostener el orden sobre cinco niveles. No se usa para ninguna cifra publicada en este documento |
| **Publicados por British Council** | 59 | Todos los PDF descargados del catálogo gratuito. Los nombres de los 59 están en `entrega/manifiesto_corpus_externo.md` | El diagnóstico del 4.3(a): que el corpus no es homogéneo, y el 89,8 % de coincidencia entre las dos vías con que se definió el filtro | Usarlo como corpus de validación. Incluye menús, pósters y horarios, y las correlaciones medidas sobre él no se comparan con las de después de filtrar |

*Cuadro 9. Los cinco conjuntos de textos que aparecen en la validación. Cuatro
de los cinco salen del mismo catálogo de British Council, con extracciones y
filtros distintos: no son subconjuntos unos de otros y sus tamaños no se
restan.*

El corpus de anclaje MCER con el que se afinó es **ELG CEFR English** (Breuker, 2023; licencia no
comercial, Cuadro 2), una sola fuente: 712 documentos, de los que se aceptan 654 como prosa —57
son cortos y 1 tiene forma de frase anómala—, repartidos por documento y con
semilla fija en 510 de entrenamiento y 144 de validación. Esos 144 producen las
cifras de la primera fila del Cuadro 10.

**De dónde salen esas cifras, y cómo se comprueban.** Del guion de entrenamiento
del v4 y de su tarjeta de métricas, que desde el 12 de septiembre de 2026 están en
el repositorio (`entrenamiento_v4/`). Ese día se **recalcularon** con el guion, los
pesos publicados y los datos públicos de ELG: la misma partición y las cuatro
métricas idénticas a cuatro decimales (exactitud 0,5347, dentro de un nivel
0,9722, MAE 0,4985, Spearman 0,9084). Las 144 parejas de nivel y predicción están
en `entrenamiento_v4/validacion_144_recalculada.csv`. Y un matiz que no se
esconde: **no es un conjunto de prueba virgen**, porque el entrenamiento se quedó
con el punto de control que mejor puntuaba en esos mismos 144 documentos.

| Conjunto | n | Exacto | Dentro de ±1 nivel | Spearman |
|---|---|---|---|---|
| Validación interna (ELG reservado) | 144 | 53,5 % | **97,2 %** | **0,908** |
| British Council (validación de desarrollo) | 38 | 50,0 % | **100 %** | 0,829 |

*Cuadro 10. Métricas del modelo desplegado. MAE de 0,499 niveles de la escala
interna 0–5 —0,200 en la escala pública 0–2— en el conjunto
de validación.*

**Un 97,2 % suena a mucho, y conviene poner al lado con qué se compara.** Con
seis niveles, acertar «dentro de ±1» es más fácil de lo que parece: contestar
**al azar** acierta el 44,4 % de las veces, y contestar **siempre B1**, sin
mirar el texto, el 50 % —ambas cifras suponiendo el nivel verdadero repartido
por igual entre los seis—. El modelo llega al 97,2 %.

**Esas dos referencias son teóricas y hay que leerlas como tales.** Suponen el
nivel verdadero repartido por igual entre los seis, y **la distribución real de
los 144 documentos de validación no está publicada**. Si ese conjunto estuviera
concentrado en los niveles centrales, «contestar siempre B1» acertaría bastante
más del 50 %. Así que lo honesto es decir que un 97,2 % está muy por encima de
lo que da el azar bajo una hipótesis razonable, no que la ventaja empírica sobre
un predictor constante esté medida: no lo está, porque faltan los recuentos por
nivel de ese conjunto.

**El resultado que de verdad sostiene el trabajo no es ninguno de esos
porcentajes, sino el orden.** Esto es lo que se midió: los **47 textos de la
reproducción local de British Council**, cada uno con un nivel MCER oficial
asignado por la institución que lo publica y ninguno usado para ajustar los
pesos, puntuados con `validar_local.py` y agrupados después por su nivel. Y esto
es lo que salió: **las medias por nivel quedan estrictamente crecientes en los
cinco niveles disponibles**, de A1 a C1 —0,5040 · 0,5561 · 0,9276 · 1,2414 ·
1,4952 en la escala 0–2—, y la correlación de Spearman con el nivel oficial es
de **0,860** (Cuadro 11 y Cuadro 13). Ese orden —no el acierto exacto— es el
resultado que el trabajo afirma haber conseguido, y es el que se cita en las
conclusiones.

| Nivel oficial | n (local) | Media en escala 0–2 | Desviación (poblacional) |
|---|---|---|---|
| A1 | 3 | 0,5040 | 0,111 |
| A2 | 8 | 0,5561 | 0,223 |
| B1 | 12 | 0,9276 | 0,198 |
| B2 | 12 | 1,2414 | 0,236 |
| C1 | 12 | 1,4952 | 0,172 |

*Cuadro 11. Reproducción local de la validación externa, sobre los 47 textos
que quedan tras la extracción de los PDF **y el filtro de prosa continua** (el
balance completo está en el Cuadro 12).*

#### La letra pequeña de ese resultado

**Aquí empieza la letra pequeña, y conviene leerla antes de citar la cifra.**
Son cuatro salvedades. Ninguna anula la afirmación anterior, pero cada una acota
lo que puede hacerse con ella.

**Una: el escalón A1–A2 está dentro del ruido.** Es de 0,052 sobre desviaciones
de 0,111 y 0,223, y descansa en tres textos. Los tres escalones siguientes, no.
Lo que se afirma es el orden global de las cinco medias, no cada comparación por
pares: con n de 3 a 12 textos por nivel, el primer escalón no se sostendría por
sí solo.

**Dos: es una reproducción local, no una reproducción independiente.** El Cuadro
11 se **recalcula** con `validar_local.py` en cualquier máquina que tenga los
mismos PDF y los mismos pesos, pero los PDF de British Council tienen derechos y
no acompañan al repositorio: quien quiera rehacerla los descarga con el
navegador y los verifica por hash con `tools/bajar_corpus_bc.py`. El `.dat` de la figura guarda los agregados, no las entradas. Lo
que se reproduce exactamente es **el orden**; las medias difieren ligeramente de
las obtenidas en Colab (C1 coincide hasta la tercera cifra decimal —1,4952
frente a 1,4950—, A2 se desvía 0,09).

**Tres: los 38 de Colab y los 47 de aquí son dos tandas distintas, y no se
restan.** La diferencia tiene dos causas —otra extracción de los PDF y otro
filtro—, así que 47 − 38 no son nueve textos que se puedan nombrar. Contado
sobre los archivos reales, el balance de esta tanda cierra así:

| | Textos |
|---|---|
| Publicados por British Council | 59 |
| menos: sin cuerpo localizable al extraer el PDF | −2 |
| menos: **rechazados por `scoring.continuous_prose`** | **−10** |
| **Evaluados** | **47** |

*Cuadro 12. De 59 a 47, paso a paso.*

**Y cuatro: el validador local filtra más flojo que la propia aplicación.** Con
el filtro completo de la app sobreviven **36 de esos 47** y A1 se queda con un
solo texto, de modo que el orden creciente sobre cinco niveles está medido sobre
un conjunto que la aplicación habría filtrado más. Por qué ocurre, qué regla se
desactiva y qué textos caen se explica entero en el 7.7, al final del 7.

### 7.5 El baseline propio, y qué aporta el modelo por encima de él

| Señal | Spearman con el nivel oficial (47 textos) |
|---|---|
| Modelo v4 | **0,860** |
| Contar las palabras del texto, sin modelo | 0,807 |
| Modelo, descontando la longitud (correlación parcial) | **0,668** |

*Cuadro 13. El modelo frente a la señal trivial. Las tres cifras las
calcula `validar_local.py` sobre los mismos 47 textos, con Spearman sobre
rangos y la correlación parcial en la misma escala.*

Un contador de palabras llega casi tan lejos como el modelo en ese corpus, y
omitirlo sería deshonesto. Lo que sostiene al modelo es la tercera fila: **aporta
señal por encima de la longitud**, que es precisamente lo que un contador de
palabras no puede hacer —y conviene decirlo con precisión: no es que su
correlación parcial sea peor, es que **no está definida**, porque descontar la
longitud de la propia longitud deja un residuo de varianza cero—. Además, el modelo no recibe la longitud del documento
como variable —puntúa bloques de tamaño fijo y promedia—, aunque su salida
correlacione 0,732 con ella, porque los corpus de examen gradúan también la
extensión de la tarea.

**La escala está comprimida, y la aplicación lo asume.** Contra el ancla real,
el ajuste ronda `predicho ≈ 0,72 × real + 0,38`. Conviene decir de dónde sale,
porque no es una recta ajustada sobre los textos uno a uno: son **mínimos
cuadrados sobre las cuatro medias por nivel que reportó Colab** (A2 a C1;
el catálogo gratuito de British Council no tiene C2 y aquella tanda no traía
A1), y dan 0,7196x + 0,3760. Rehecha sobre las cinco medias locales de hoy
sale **0,67x + 0,41**: cambian los decimales, no la conclusión, que es que la
pendiente está muy por debajo de 1. De modo que un texto A2 tiende
a puntuar cerca de B1. Por eso la interfaz muestra **bandas** (básico
< 0,6 ≤ intermedio < 1,4 ≤ avanzado) y la letra MCER solo como orientación, en
lugar de fingir una precisión de dos decimales que el modelo no tiene.

Los cortes de esas bandas salen del MCER, y esa es una corrección posterior. Al
principio estaban en 0,8 y 1,6, que además **ni siquiera partían el 0–2 en tres
partes iguales**: dejaban dos tramos de 0,8 y uno de 0,4. Pero
como el modelo comprime sus predicciones, con esos cortes un texto C1 caía en
«intermedio» y «avanzado» solo lo alcanzaba un C2: tres de los cinco niveles
medidos compartían banda. Ahora la banda se deriva del ancla MCER, con el
agrupamiento del propio marco —usuario básico A1–A2, independiente B1–B2,
competente C1–C2—, y las fronteras quedan en **0,6 y 1,4**. Así la palabra y la
letra no pueden contradecirse por construcción. Ninguna puntuación cambió: solo
cambió cómo se agrupan.

**Un intento de ampliar la validación que hubo que retirar, y por qué se deja
escrito.** El 12 de septiembre de 2026 se midió el v4 sobre los dos conjuntos
ingleses de referencia de UniversalCEFR (Imperial et al., 2025),
`cambridge_exams_en` y `elg_cefr_en`: 739 textos, Spearman **0,946**. Era más
alto que la validación interna (0,908), y eso bastó para no creérselo. Leyendo
el guion de entrenamiento del v4 salió la causa: **el v4 se entrenó con ELG CEFR
English**, que es exactamente `elg_cefr_en` (654 aceptados + 57 cortos + 1
descartado = 712, el tamaño del conjunto). Y los 325 textos distintos de
Cambridge están **todos** dentro de él: 130 idénticos y 195 casi idénticos, con
una mediana del 92 % de sus 8-gramas compartidos y el mismo nivel en los 195.
Aquel 0,946 medía el modelo sobre su propio entrenamiento. No hay en
UniversalCEFR un subconjunto inglés limpio para el v4, y la validación de este
apartado sigue siendo la del Cuadro 11.

**Una validación externa de verdad: OneStopEnglish.** Con la composición del
anclaje ya conocida se pudo buscar un corpus que los pesos del v4 no hubieran
visto, y comprobarlo en vez de suponerlo: ninguno de los textos de
OneStopEnglish (Vajjala y Lučić, 2018) comparte con ELG CEFR English ni una
secuencia de ocho palabras. Son 189 artículos de prensa escritos tres veces, en
nivel Elementary, Intermediate y Advanced. Se mide una puntuación por artículo y
nivel —560 unidades— con `validar_onestop.py`, que repite la comprobación de
fuga cada vez que se ejecuta.

| Nivel | n | Media v4 (0–2) |
|---|---|---|
| Elementary | 185 | 0,934 |
| Intermediate | 189 | 1,272 |
| Advanced | 186 | 1,515 |

| Señal | Modelo v4 | Contar palabras |
|---|---|---|
| Spearman con el nivel (560) | **0,800** | 0,692 |
| Correlación parcial, descontando la longitud | **0,688** | indefinida |
| Artículos con sus tres versiones en orden (185) | **183** | 179 |

*Cuadro 13b. Validación externa con OneStopEnglish.*

Las medias suben en los tres niveles y el modelo conserva 0,688 descontando la
longitud: aporta señal propia en un corpus que no vio. **Pero la última fila hay
que leerla con cuidado**, porque es tentadora: dentro de cada artículo el modelo
ordena bien las tres versiones en 183 de 185, y **la longitud sola ya acierta
179**, porque las versiones avanzadas son más largas (523, 667 y 809 palabras de
media). Donde la longitud falla —seis artículos— el modelo acierta en cinco. Es
una ventaja real, y es pequeña. Dos matices más: la escala vuelve a salir
comprimida y desplazada hacia arriba —un texto Elementary puntúa 0,93, en la
banda intermedia—, y OneStopEnglish **sí se usó para desarrollar los modelos
anteriores** (el v2 se afinó con él), así que es externo para los pesos del v4,
no virgen para el proyecto.

**Lectura graduada por sus editores.** Tres bibliotecas infantiles abiertas ponen
a cada libro un nivel propio: StoryWeaver del 1 al 4, African Storybook y Let's
Read del 1 al 5. **No son niveles del MCER**, así que solo se puede validar el
orden. Se midieron con `validar_graduados.py`, con la misma comprobación de fuga
contra ELG CEFR English (0 textos contaminados en las tres) y dos decisiones que
hay que declarar: los cuentos de menos de 250 palabras se unen en bloques de al
menos 250 **sin mezclar fuente ni nivel**, y la longitud que se descuenta es la
natural de los cuentos, no la del bloque. Intervalos bootstrap al 95 % con 2.000
remuestreos.

| Fuente | Unidades | Spearman v4 [IC 95 %] | Longitud | Parcial sin longitud [IC 95 %] | Medias crecientes |
|---|---|---|---|---|---|
| StoryWeaver (1–4) | 467 | **0,426** [0,348; 0,502] | 0,542 | **0,206** [0,111; 0,295] | 99,6 % |
| African Storybook (1–5) | 174 | 0,416 [0,279; 0,537] | 0,810 | 0,133 [−0,029; 0,289] | 54 % |
| Let's Read (1–5) | 1.000 | 0,178 [0,118; 0,235] | 0,620 | −0,083 [−0,144; −0,026] | 1,8 % |

*Cuadro 13c. Validación con lectura graduada por sus editores. «Longitud» es el
Spearman de la longitud natural con el nivel; «Medias crecientes», la proporción
de remuestreos en que las medias por nivel salen en orden. StoryWeaver es una
muestra aleatoria de 649 libros intercalada por niveles.*

Las tres dicen cosas distintas, y conviene no promediarlas. **StoryWeaver
valida**: los cuatro niveles salen separados y en orden, y el modelo aporta orden
*además* de la longitud (la parcial excluye el cero). **En African Storybook la
longitud predice el nivel mucho mejor que el modelo**, y eso describe al corpus:
sus niveles son casi una escala de longitud. El v4 no ve la longitud —puntúa
ventanas fijas de 250 palabras— y dentro de cada nivel su correlación con ella es
prácticamente nula; ordena por contenido, pero no se puede afirmar que aporte
orden más allá de la longitud, y el orden entre los niveles 1 y 2 no está
establecido. **Let's Read no valida, y no por el modelo**: más de la mitad de sus
libros son traducciones al inglés que heredan el nivel del original en laosiano,
jemer o indonesio; en esas 459 traducciones la correlación es 0,023, y en los 360
originales, 0,207. Su etiqueta describe el libro en su idioma.

Esta sección se corrigió tras una revisión metodológica independiente: la primera
redacción leía la parcial de African Storybook como «lo explica sobre todo la
longitud», daba sus medias por «estrictamente crecientes» sin intervalos y no
advertía que el filtro de prosa rechazaba 42 de sus 65 cuentos de nivel 1,
sesgando ese nivel hacia arriba. Los detalles están en
`auditoria/validacion_graduados_2026-09-12.md`.

### 7.6 Cuadro de decisiones metodológicas

Incluye las hipótesis que se probaron y se rechazaron. Reportarlas es parte del
resultado.

| Decisión | Razón | Evidencia / consecuencia |
|---|---|---|
| Regresión, no clasificación | La dificultad es continua; clasificar tira información ordinal | El error ordinal medio baja de 1,39 a 0,67 en la progresión completa |
| Partición agrupada por libro | Evitar fuga de datos entre extractos **del mismo libro**. No separa autores: dos obras del mismo autor pueden caer a ambos lados, y eso no se comprobó | Aplicada a *todos* los modelos comparados, no solo al final |
| `distilroberta` y no `roberta-base` completo | La aplicación debe correr en CPU en el equipo de un estudiante | 328 MB y 0,9 s de carga, frente a 1,5× más parámetros (125 M contra 82 M). **La diferencia de calidad entre las dos no se midió**: la decisión se tomó por tamaño y velocidad, no porque se comprobara que costaba poco |
| Promediar bloques sin ponderar, con la **ventana** como unidad | Simplicidad y reproducibilidad; ponderar por longitud reintroduce la longitud como señal | Constante del entrenamiento. La app y el precálculo del catálogo usan ahora el mismo estimador: durante un tiempo la app promedió las medias de cada capítulo y el catálogo todas las ventanas, y con capítulos de tamaño desigual **no son el mismo número** (0,004 de diferencia máxima sobre cinco libros; la medición se hizo en su momento y **no queda guion que la reproduzca**, así que se da como orden de magnitud, no como cifra auditable) |
| **Rechazada: XGBoost sobre variables clásicas** | Se esperaba que un ensamble superase al modelo lineal | No lo hace: 0,28 frente a 0,29, y error ordinal peor (1,42 vs 1,39). El límite estaba en las variables |
| **Rechazada: modelo híbrido embedding + variables** | Se esperaba complementariedad | Ganancia nula (0,37 y 0,37; 0,91 vs 0,93). El embedding ya contiene esa información |
| **Rechazada: escalar la lista léxica al SPGC completo por rendimiento** | Se esperaba mejorar `rare_word_ratio` | La correlación pasa de −0,330 a −0,326. Se conserva igualmente por cobertura, no por métrica |
| **Rechazada: cuantización dinámica int8** | +18 % de velocidad en CPU | MAE de 0,210 sobre una escala de 0 a 2 y sesgo sistemático de −0,21. Un desplazamiento así cambia la letra MCER en el **52 %** de la escala y la banda en el **21 %**: no degrada la cifra, le cambia la etiqueta al libro. Inaceptable |
| **Rechazada: precisión media (fp16) en la GPU local** | Se esperaba acelerar | Es **4,8× más lenta** que fp32 en una GTX 1650 SUPER: el chip TU116 no tiene *tensor cores*. En una A100 sí compensa, y allí la desviación observada fue de unos 0,00037 de media; **tampoco quedó guardada**: mismo caso que la fila de arriba |
| **Rechazada: `inference_mode` en lugar de `no_grad`** | Se esperaba menos sobrecarga | 0,4 % de diferencia, por debajo del ruido |
| **Rechazado: esfuerzo de razonamiento «mínimo» en la explicación léxica** | Es el doble de rápido (7,4 s frente a 14,9 s) | Con él, «had peeped» se explicó como pasado simple cuando es pasado perfecto. La gramática es justo lo que se evalúa |
| Filtrar prosa continua para la validación externa | Excluir textos porque el modelo falla en ellos invalida la validación | El criterio salió del diagnóstico, no es *a priori*, y así se dice en §4.3(a). Lo que lo sostiene es que se definió por **dos vías independientes** —título y estructura— que coinciden en el 89,8 % sin volver a mirar las puntuaciones |

*Cuadro 14. Decisiones metodológicas, incluidas las hipótesis rechazadas.*

### 7.7 Qué filtra el validador local y qué filtra la aplicación

Este apartado desarrolla la cuarta salvedad del 7.4: el guion que reproduce el
Cuadro 11 no aplica el mismo filtro que la aplicación, y conviene ponerlo aquí y
no esconderlo en el código.

**Qué regla se desactiva, y por qué.** El guion de reproducción une las líneas
del PDF con un espacio, y eso **desactiva una de las cuatro reglas** de
`scoring.continuous_prose`, la del maquetado de lista: sus dos comprobaciones
—más del 17,5 % de las palabras en líneas de maquetado, o más de un tercio de
líneas muy cortas— necesitan saltos de línea para ver nada. Es decir, este validador filtra **más flojo que la
propia aplicación**, que sí recibe saltos de párrafo. Medido cambiando una cosa
y solo una: con saltos de línea sobreviven **36 textos en vez de 47**, y A1 se
queda con uno solo, con lo que la comprobación de orden creciente ya no se puede
hacer sobre cinco niveles.

**Por qué se conserva así.** Porque la unión con espacio es la que reproduce el
Cuadro 11 de este documento, que es la reproducción local. **No reproduce las
cifras de Colab**, y nada aquí lo hace: aquella tanda son 38 textos y A2 se
desvía 0,09. Pero el guion imprime las dos cuentas en cada ejecución, así que la
diferencia queda a la vista de quien lo ejecute.

**Qué textos se caen, y por qué regla.** En el Cuadro 12, la primera resta es de
extracción. La segunda no: son **diez textos —nueve de A1 y uno de B1— que
rechaza `scoring.continuous_prose`**, y conviene decir con qué regla, porque el
filtro tiene cuatro. Los diez caen por la misma: **se quedan por debajo de las
150 palabras** una vez recortados entre «Reading text» y «Tasks». Son pósters,
menús, horarios y tarjetas, es decir, textos que en el original ya son cortos;
el detector de maquetado de lista ni siquiera llega a dispararse, porque el de
longitud actúa antes. Los dos entornos filtraron con reglas distintas, no solo
extrajeron distinto.

**Lo que esto le hace al resultado principal.** Los tres textos A1 que sostienen
el escalón más débil del Cuadro 11 **no pasan el filtro de la aplicación**:
pasan el de este guion, que es el más flojo de los dos. Con el filtro completo,
dos de los tres caen por maquetado de lista. Dicho de otro modo: una parte de
esos 47 son textos que la app rechazaría por parecer listas, y el escalón A1 es
justo donde más pesa. Los nombres de los 59 archivos están en
`entrega/manifiesto_corpus_externo.md`, y `validar_local.py` imprime los diez
rechazados con su motivo.

---

## 8. Resolución del problema

### 8.1 De la métrica a la decisión del lector

Una correlación de 0,908 no le sirve de nada a un adolescente. Lo que le sirve
son tres decisiones, y el producto está construido para producir exactamente
esas tres:

| Pregunta del lector | Qué la responde | Coste para él |
|---|---|---|
| ¿Cuál es mi nivel? | Seis preguntas sobre hábitos observables y tres fragmentos reales en escalera; o bien subir un libro que ya lee cómodo | Menos de dos minutos |
| ¿Qué leo ahora? | Búsqueda por significado en español sobre el catálogo; el nivel del perfil ordena lo más parecido y lo de otros niveles sale aparte, sin filtrar | Segundos |
| ¿Por dónde se va a complicar? | Curva de dificultad capítulo a capítulo, medida sobre el libro entero sin muestrear | De 12,7 s (vistazo, medido sobre Crime and Punishment) a minutos (libro completo) |
| ¿Qué significa esta palabra *aquí*? | Doble toque sobre la palabra: lema, IPA británica y americana cuando el diccionario la trae (el 58 % de las consultas sobre un libro real, §6.4), definición de Wiktionary, el sentido concreto en esa frase, gramática y audio | Instantáneo en local; la explicación contextual tarda más |
| ¿Lo estoy pronunciando bien? | Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla | Una frase |

*Cuadro 15. Del modelo a las decisiones del usuario.*

### 8.2 Un recorrido completo, con números reales

Tomemos el caso concreto de una lectora cuyo perfil da 1,20 sobre 2 (banda
intermedia, ancla B2).

1. Busca. Escribe *«dostoyevski»*, mal escrito, y el rescate por parecido
   ortográfico la lleva igualmente a quien busca —«chejov» y «Shakespear»
   funcionan igual— sin estorbar a las búsquedas por tema, porque el buscador
   no busca por título sino por significado, sobre embeddings multilingües.
   Podría haber escrito en español lo que le apetece —*«una novela de
   detectives victoriana»*— y el buscador respondería igual. Medido el 11 de
   septiembre de 2026 con su perfil de 1,20 y el ajuste al nivel puesto
   (entonces una casilla; desde el 15 de septiembre *Encontrar* ordena siempre
   por nivel y aparta en otro bloque lo que queda lejos de él), esa frase en
   español devuelve *The Secret Adversary* (Christie,
   B2), un cuento infantil A1 de StoryWeaver, *Great Expectations*, *North
   and South*, *Bleak House* y, en séptimo lugar, *The Memoirs of Sherlock
   Holmes*. Que el segundo puesto sea un A1 para una lectora de 1,20 no es un
   fallo del buscador: es el libro cuyo texto más se parece a la palabra
   «detective», el ajuste **acerca y no filtra**, y su nivel va escrito al
   lado.

   **Y aquí conviene decir algo que el propio recorrido enseña.** Lo que
   devuelve la búsqueda **no está filtrado por el nivel del lector**: ordena
   por cercanía al tema, y la dificultad va al lado de cada resultado para que
   el lector decida. En este recorrido eso importa, porque el libro que abre
   mide 1,70 y ella está en 1,20: le queda por encima, y el valor de la
   herramienta es precisamente que **lo sabe antes de la primera página**.
2. Abre el libro. Se descarga de Project Gutenberg y se abre dentro de la
   aplicación, sin salir a buscarlo.
3. Aparece la ficha, **contada sobre el texto y no sobre metadatos**, aunque
   no toda sobre el libro entero: las palabras y el tiempo de lectura salen
   del fichero completo, y la longitud de frase, el diálogo y el vocabulario
   se calculan sobre una muestra con **tope de 60.000 palabras**, repartido a
   partes iguales entre los capítulos —la variedad léxica, sobre las primeras
   20.000 de esa muestra—, porque recorrer *Guerra y paz* entero para
   pintar una ficha haría esperar al lector. Lo que trae:
   palabras reales, tiempo de lectura estimado a 180 o 110 palabras por
   minuto según el texto le quede por debajo o por encima de su nivel
   —no es su ritmo medido, que la aplicación no conoce—, longitud media de frase,
   proporción de diálogo, variedad de vocabulario y palabras más repetidas.
   La proporción de diálogo distingue de verdad entre obras —*Alice* 73 %,
   *Pride and Prejudice* 28 %, *Crime and Punishment* 31 %—, cosa que no hacía
   cuando se medía por párrafo en lugar de por oración, porque un epub no
   conserva los saltos de párrafo y las tres daban 100 %.
4. Pide la curva de dificultad. Sobre *Crime and Punishment* (PG2554), el
   modelo recorre **840 ventanas de 203.699 palabras en 134 segundos** y
   devuelve una media de **1,70 sobre 2** —orientativo C1—, además de decir si
   el libro se va complicando o soltando y cuáles son su capítulo más
   llevadero (el 19, 1,52) y su capítulo más exigente (el 36, 1,87).
   La segunda vez tarda 0,02 s porque queda guardada.
5. Toca una palabra que no conoce. El trabajo local —lema, categoría
   gramatical, consulta al diccionario, desambiguación por similitud, IPA— son
   **40 milisegundos** *en caliente*; la primera consulta de la sesión carga el
   diccionario, spaCy y el modelo de similitud, y eso tarda. La explicación
   contextual, que sale a la red, es lo único lento siempre, y por eso la ficha
   se pinta en dos etapas: lo local aparece al instante y la explicación se
   añade cuando llega.

   Esa explicación se pide con **salidas estructuradas** (*structured
   outputs*): un esquema Pydantic con un campo por cada cosa que se va a
   pintar —definición en contexto, explicación gramatical, versión adaptada al
   nivel y ejemplo simplificado— en lugar de texto libre que luego haya que
   trocear. El esquema fija la forma de la respuesta, **no garantiza su
   veracidad**. Si Kaikki trae una acepción utilizable, la definición se conserva
   y el servicio explica y traduce el contexto; ante una elección dudosa solo
   puede seleccionar otra glosa existente. Desde el 13 de septiembre, si no hay
   acepción utilizable y se autoriza la llamada, puede ofrecer una definición
   **marcada como generada por IA**, nunca atribuida al diccionario. Sin clave
   se conserva la ficha local y el aviso de ausencia. Y si la elección es
   dudosa —menos de 0,05 de afinidad entre las dos acepciones más cercanas— y
   no hay explicación de OpenAI, desde `bf3a9f2` la ficha no afirma una: dice
   «Puede ser» y enseña la acepción principal de cada entrada del diccionario,
   si hay al menos dos. Las salidas estructuradas
   también se usan en pronunciación y en «¿de qué trata?».
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
| CPU (Ryzen 5 2600) | 12 hilos, lote 64 | 8,19 | 1× |
| GPU local (GTX 1650 SUPER) | fp32, lote 128 | 112,7 | 13,8× |
| GPU A100 (Colab) | fp16, lote grande | 2.022 | 247× |

*Cuadro 16. Rendimiento medido de extremo a extremo, incluida la tokenización
y las transferencias. Son cifras del precálculo, que agrupa en lotes fijos de 64
en CPU y 128 en GPU. **La aplicación en vivo no llega a esos lotes**: agrupa
por capítulo, y no por conveniencia sino para poder ir repintando la curva
mientras mide; un capítulo son unas veinte ventanas, así que el rendimiento interactivo real está más cerca de las
6,96 ventanas/s del agrupado por capítulo que de las 8,19 de esta fila.*

Dos comprobaciones acompañan a ese cuadro, porque acelerar no puede costar
exactitud:

- **La GPU da los mismos números que la CPU.** Sobre 840 ventanas de *Crime and
  Punishment*, 839 son idénticas a tres decimales y una difiere en 0,001; el
  MAE es 0,000001 sobre la escala 0–2.
- **Reagrupar en lotes distintos no mueve ninguna cifra que se publique**, y
  conviene decirlo con precisión, porque hay dos casos y solo uno es exacto.
  Cuando se trocea **un texto de más de 250 palabras**, todas sus ventanas
  miden 250 palabras exactas y, en prosa inglesa real, pasan siempre de 256
  *tokens* BPE, así que se truncan a 256 —comprobado: la ventana más corta
  de un texto de prueba da 258; un texto artificial de 250
  monosílabos daría 252 y no llegaría, pero eso no es prosa—: no
  hay relleno, y la fila de cada ventana no depende de con quién vaya
  agrupada. Es el caso de la comprobación: las mismas **300 ventanas**
  puntuadas de una en una y en un solo lote de 300 salen **300/300 idénticas**,
  con MAE 0,000000. El precálculo del catálogo, en cambio, mete en el mismo
  lote las ventanas de **todos los capítulos** de un libro, y un capítulo de
  menos de 250 palabras aporta una ventana corta: ahí `padding` sí rellena
  hasta la ventana más larga del lote, y el resultado **no es idéntico bit a
  bit**. También está medido, sobre *Alicia en el País de las Maravillas*, 112
  ventanas: **103 coinciden exactamente y el resto difiere como mucho en
  4,8 × 10⁻⁷**. Las cifras del catálogo se guardan con tres decimales, así que
  una diferencia de ese tamaño no puede mover ninguna.

Con 2.022 ventanas por segundo, medir los 61.642 libros en inglés de Project
Gutenberg salían **entre 3 y 5 horas de A100**, y en su momento se dijo de qué
dependía esa horquilla en vez de dar una cifra sola: del número medio de
ventanas por libro. Con las 350 que asume el código del precálculo salen
**2,96 h**; con las 606,4 que promedian las cinco novelas largas medidas en
local —una muestra sesgada hacia arriba, porque son clásicos extensos— salen
**5,14 h**.

**Después se ejecutó, y la estimación resultó ser la mitad de la respuesta.** El
ritmo real medido en la A100 fue de **61 libros por minuto**, o sea **unas 17
horas** para los 61.642 —cinco veces la cifra de tarjeta—. Y el desglose dice
exactamente dónde se va el tiempo: un libro medio son **0,17 s de GPU** contra
**~1 s de reloj**, así que **el 80 % del tiempo la tarjeta está parada**
esperando a que el sistema de archivos de Google Drive entregue el `.txt`.

La estimación no era falsa: era **incompleta**, y de una manera que conviene
nombrar porque es un error de método y no de aritmética. Medía la parte del
sistema que se sabía medir —el modelo— y daba por supuesto que era la que
manda. No lo era. Es la misma lección que la agrupación por capítulo en vez de
por libro, y la misma que la descarga: **el cuello de botella de este proyecto
nunca ha estado en el modelo**. En serie, a 0,3 libros/s, la descarga tardaría
57 horas. Y no era la pausa de cortesía entre peticiones, era la
latencia —cada petición al espejo se pasa casi todo su tiempo esperando la ida
y vuelta—, así que con seis hilos esas esperas se solapan. Seis y no treinta a
propósito: el espejo lo mantiene alguien de forma gratuita, y cada hilo conserva
su pausa.

**Después se buscó una vía más rápida, y la decisión que importa no fue
técnica.** El archivo único de Gutenberg —11,3 GB, una petición en lugar de las
29.668 que faltaban el 9 de septiembre— parecía el atajo evidente y no lo era: medido en dos
máquinas distintas, el espejo entrega **0,29 MB/s**, o sea **casi once horas**,
y con seis conexiones simultáneas sube a 0,46 y rechaza la séptima. No es el
ancho de banda de nadie: es un servidor que mantiene un voluntario. La lección
es del mismo tipo que las dos anteriores: **un atajo no es un atajo hasta que
se cronometra**.

La vía rápida existe y también se midió: pedir los libros uno a uno a
`www.gutenberg.org` con treinta y dos hilos da **3.362 libros por minuto**,
unos nueve minutos para lo que faltaba. **Se descartó.** La política del sitio
lo dice sin ambigüedad —«está pensado para usuarios humanos; cualquier uso
aparente de herramientas automatizadas resultará en el bloqueo de su dirección
IP»— y autoriza tres caminos: un espejo privado, el punto de acceso
`/robot/harvest` con dos segundos de espera entre ficheros, o el catálogo. Que
una puerta esté abierta y sea rápida no la convierte en una entrada.

Lo que sí resuelve el problema es no pedirle nada a Gutenberg.
`common-pile/project_gutenberg` (Kandpal et al., 2025) es un volcado ya publicado de esos mismos
textos de dominio público, servido por una red de distribución de contenidos.
Medido sobre el primer fragmento: **8,0 MB/s**, unos **veintidós minutos** para
los 10,5 GB, y el identificador de cada documento **es** el número de Gutenberg
—239 de 239 cruzaron con el catálogo oficial en la comprobación, sin una sola
excepción—. Veintisiete veces más rápido que el archivo único, y con la
infraestructura de los voluntarios intacta.

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
lugar se avisa, y el aviso ya está en la aplicación: una lista curada a mano
(`avisos_contenido.csv`) pone en la ficha del libro un recuadro «Aviso sobre el
contenido» antes de abrirlo, sin bloquear nada. A fecha de `db366b8` lleva 2
títulos, las dos ediciones de *Little Black Sambo* de Helen Bannerman (PG17824
y PG1330), por estereotipos raciales. El buscador no cambia de orden por el
aviso; al recomendar por nivel, los 5 primeros puestos son para títulos sin
aviso y los que lo llevan siguen detrás, sin quitar ninguno. Aparte, el resumen
que escribe el modelo puede añadir su propio «Antes de empezar». **Se informa al lector y se le
deja elegir; no se elige por él.** Es una decisión discutible y por eso se
argumenta en lugar de ocultarse.


### 8.5 Entrega web y corte de verificación

**Estado documental al 14 de septiembre de 2026.** El enlace para el lector es
https://mikemaki1763-literalevel-front.static.hf.space/ . Es el front Angular;
el Space `MikeMaki1763/literalevel` aloja FastAPI y conserva Gradio como respaldo.
La API tiene **40 rutas bajo `/api`** a fecha de `8ee42f0` (el `app/` que publica el Space en `7c09d90`), contadas en el
código local, y reutiliza
los módulos Python y ayudantes de acceso. Sus adaptadores tienen lógica propia
y se prueban por separado: compartir funciones no garantiza por sí solo que
ambas interfaces cobren, almacenen o respondan igual. El inicio de sesión
frena los intentos fallidos en una hora: 15 por IP y, desde `514786b`, 20 por
usuario, porque la IP sale de una cabecera que puede escribir el cliente. Solo
cuentan los que fallan, y son valores por defecto que se cambian por variable
de entorno. Medir tampoco es ilimitado: cada medida ocupa la CPU del único proceso del Space, así que desde el 14 de septiembre hay topes por IP y hora —40 medidas de nivel o de capítulo y 6 curvas nuevas— y como mucho 4 curvas en cola a la vez; lo ya medido no gasta ficha. En el Space, a fecha de `2bb1276`, la séptima curva seguida dio 429 y un libro ya medido siguió respondiendo.

El catálogo local se volvió a contar con pandas: **53.179 IDs únicos y 585.111 capítulos**. A fecha de `740eb84`, el catálogo externo de textos libres tiene 15.367 filas y los vectores de búsqueda suman 68.546 (53.179 + 15.367). El Space publicado cuenta los mismos 68.546 libros en `/api/estado` a fecha de `384a206`, el reinicio 21. Esto confirma el tamaño del artefacto, no repite su inferencia ni
garantiza que toda descarga futura esté disponible. A fecha de `db366b8` se
excluyen al recomendar y al buscar 600 que no son lectura (índices, catálogos,
directorios) y 200 textos libres que no son lectura (relleno, otra lengua,
anuncios o un texto que dice tener derechos; eran 163 en `3524357`, 185 en
`a557288` y son 200 desde `740eb84`), y por nivel solo se ofrecen obras literarias. Una medida del
precálculo se corrige al cargar (`correcciones_catalogo.csv`): PG2242, *A
Midsummer Night's Dream* del First Folio, guardó 0,697 y releída por el mismo
camino da 1,713 (C1).

El despliegue del backend `e56cf08` fue cotejado por hash el 13 de septiembre:
salud JSON, lectura de Alicia desde Angular, diccionario sin perfil y rechazo
de voz anónima. En el entorno local aislado pasaron **32 de 35 pruebas API**;
tres quedaron sin validar por dependencias NLP ausentes. También pasaron 7
pruebas de concurrencia de voz, 10 de despliegue y 11 de portadas, con sus
alcances separados. No se probó OpenAI real ni micrófono físico en ese cierre.
Recuento sin claves del 15 de septiembre sobre `d58b0be`: **52 de 52 pruebas API**, las
**349 de 349 pruebas extremas** del motor, 34 de 34 de corpus y 34 de 34 de lectura natural.
La consulta de *house* eligió un sentido no adecuado al contexto: disponibilidad
del diccionario no demuestra que su desambiguación sea correcta en todos los
casos. Evidencia: `auditoria/despliegue_codex_2026-09-13_noche.md`.

**Boca 3D y portadas, a fecha del front `ec957d0` (repositorio `4e6276e`).** La boca 3D ya está publicada: el front sirve `boca3d/cara.glb` y `lengua.glb`, idénticos byte a byte a los del repositorio, con 72 mallas entre los dos y respaldo 2D si no cargan. La piel de la media cabeza sale de la malla base de MakeHuman 1.3.0, publicada bajo CC0 1.0 (no obliga a atribuir; MakeHuman Community, s. f.); paladar, velo, encías, dientes y lengua son modelos propios, y sus 53 poses se validan contra ellos. Es un corte esquemático, no anatomía validada clínicamente. Las portadas publicadas son **tipográficas**: una de 12 familias según los temas del catálogo, con una paleta de cinco colores sacada de la huella del identificador y el título a un contraste de al menos 4,5:1. El lector toma el fondo y el acento de esa paleta, con el texto a 7:1 o más y el acento a 4,5:1 sobre el fondo (sobre el color suave del acento, la pista del lector baja a 4,17:1 en algunos libros en tema claro, como SWV369), y el ajuste «Color del libro en el lector» lo apaga; la prueba del front que fija esos contrastes recorre 12 familias, 200 libros y dos temas (`b2003e5`). El pipeline de portadas FLUX está bloqueado por defecto; no generó imágenes nuevas ni consumió GPU. Sus 1.200 candidatos tienen 746 motivos temáticos y 454 genéricos, pendientes de muestra y revisión visual.

**Lectura natural, medida con diez frases.** En *Pronunciar*, además del sonido que falla, la aplicación mide el ritmo de la lectura y enseña cómo se dice la frase de corrido: énfasis, enlaces entre palabras y reducciones (*want to* → *wanna*). Lo propone un modelo generativo y lo filtra un validador: las reducciones solo salen de una lista cerrada y los enlaces se comprueban con la pronunciación de diccionario. Con diez frases reales del catálogo evaluadas a mano (`auditoria/bateria_lectura_natural_2026-09-14.md`), el modelo propuso 11 reducciones y 29 enlaces; llegaron al lector 2 reducciones y 4 enlaces, **todos correctos**, y las diez versiones naturales quedaron fieles a la frase (8 reconstruidas por el validador). La exhaustividad es baja: se quedan fuera enlaces claros como *an argument*. En esa batería todo lo que llegó al lector era correcto, y eso no es una garantía: desde el 15 de septiembre el validador exige además un verbo detrás de *gonna*, *wanna* o *gotta* (antes aceptaba «I am gonna school» si el modelo lo proponía) y no enlaza a través de un punto. La frase de la demostración, «Don't you want to come with us?», da en el Space a fecha de `7c09d90` las reducciones *doncha* y *wanna*, marcadas como generadas por IA, y ningún enlace.

### 8.6 Contra quién compite esto

Un proyecto que no sabe contra qué compite no puede decir qué aporta. La versión
larga está en el documento de estrategia; aquí van las tres alternativas reales
y la cifra que resume cada una.

| Alternativa | Cifra publicada | La nuestra |
|---|---|---|
| Fórmulas clásicas (FKGL, ARI) | Pearson **0,517** en CLEAR | **0,89** |
| Mejor LLM *zero-shot* publicado | Pearson **0,725** en CLEAR | **0,89** |
| Lexile, tarifa de creador de contenido (MetaMetrics, 2026) | **3.824–54.636 USD/año** | A100 de pago hasta el 10 sep y T4 gratuita después; sin coste en USD registrado |

*Cuadro 17. Cifras publicadas frente a las de este proyecto. **No son
comparaciones cara a cara**: las dos primeras filas vienen de un estudio ajeno
(Grossman y Chen, 2026) sobre el mismo corpus, con otra partición y otro protocolo. Justifican la
decisión de afinar un codificador; no demuestran una victoria medida.*

Los 53.179 libros del catálogo medido caen en el tramo más alto de la tarifa de Lexile.
Medirlos aquí sí usó cómputo de pago, y no hay cifra en dólares que dar: no
quedó registrado cuántas unidades se gastaron. Hasta el 10 de septiembre de 2026
el cuaderno de Colab se abría con una A100, que consume unidades de pago de la
cuenta Colab Pro, y hasta esa tarde se midieron 27.776 libros (los 29.875 medidos
el 10 menos los 2.099 de la primera tanda en T4); el 9 de septiembre quedaban 1,9
unidades (`colab_precalculo.py:903`). Desde entonces se midió en una T4 gratuita, en tandas reanudables
—la primera, 2.099 libros; la última, 9.795 en 55 minutos—, y los textos libres
en la CPU local. Las «2,8 h de A100» del registro del proyecto no son horas
gastadas: son la estimación de tarjeta para los 61.642 libros (332,3 ventanas por
libro a 2.022 por segundo). Al ritmo medido en la A100, 61 libros por minuto, los
53.179 habrían sido unas 14,5 horas de reloj (§8.3 da 17 para los 61.642). **No es
una razón monetaria estricta** —una licencia anual y unas horas de cómputo no se
dividen— y tampoco son servicios equivalentes: Lexile vende una escala aceptada
por instituciones. Lo que sí se sostiene es que el **coste de procesamiento está
en otro orden de magnitud**, y eso es lo que hace viable medir un catálogo
entero en un trabajo de estudiante.

**Dónde se pierde, que también hay que decirlo.** Lexile tiene treinta años de
validación y una escala que **acepta un colegio**; la de aquí no la acepta
nadie. *TeakReader* (TeakReader, s. f.) ya da nivel MCER por capítulo y es una aplicación publicada
en dos tiendas, mientras esto vive en un enlace. Y las lecturas graduadas de
editorial tienen algo que ningún modelo da: el nivel se lo puso una persona que
leyó la obra.

**Lo que queda, y basta para justificar el trabajo**, son tres cosas: se recorre
el libro **entero, capítulo a capítulo**, en lugar de dar un número global; está
escrito para un **hispanohablante que elige qué leer**, no para un profesor que
clasifica textos; y es **auditable en lo que se puede auditar y de acceso
gratuito para el lector**, con el modelo publicado y el código a la vista.

Esa tercera hay que acotarla: el código, la inferencia desde los pesos públicos
**y** las métricas internas del v4 se pueden rehacer —recalculadas el 12 de
septiembre de 2026, idénticas a cuatro decimales—. Y las fórmulas clásicas también son gratuitas y reproducibles, así que
la ventaja no está en la auditabilidad sola, sino en tenerla junto con un modelo
que lee el texto. Lo que ninguna alternativa reúne son las **tres a la vez**.

---

## 9. Limitaciones

**Antes de la lista, de dónde sale.** Este trabajo se sometió a **quince
auditorías externas** hechas por modelos de dos familias distintas, con el
encargo explícito de ser duros y **a ciegas**: sin decirles qué se había
corregido antes, para que lo que volviera a salir fuera lo que seguía mal.
Entre todas señalaron más de un centenar de hallazgos: fugas de datos,
cifras que no cuadraban entre archivos, métricas atribuidas al corpus
equivocado, pruebas que no podían fallar y conclusiones más fuertes que su
evidencia. Los informes están en `auditoria/` y las correcciones, en el
historial del repositorio.

Varias de las limitaciones que siguen no las encontró el autor, y algunas
contradicen lo que este mismo documento afirmaba en una versión anterior.
Parece razonable decirlo una vez, al principio de la lista, en lugar de
repetirlo en cada párrafo corregido.

1. **La escala 0–2 es propia y no es una certificación.** El MCER fue el ancla
   del entrenamiento. LiteraLevel no acredita ningún nivel, y decirlo en el
   documento no basta: la aplicación lo repite en pantalla.
2. **La escala está comprimida.** El ajuste contra el ancla real ronda
   `predicho ≈ 0,72 × real + 0,38` (mínimos cuadrados sobre las cuatro medias
   por nivel de Colab; con las cinco locales sale 0,67x + 0,41), así que los
   niveles bajos se sobreestiman y
   los altos se subestiman. Es la razón de mostrar bandas y no decimales.
3. **Las letras del catálogo son orientativas.** Ya no son heredadas: los
   53.179 libros están medidos enteros por el v4 (Cuadro 3b). Pero la escala
   del modelo sale comprimida y desplazada hacia arriba —un texto Elementary de
   OneStopEnglish puntúa 0,93—, así que la letra de un libro fácil tiende a
   subir. La aplicación lo dice al pie de cada tabla, en la pantalla y no solo
   en el PDF. Hasta el 12 de septiembre de 2026 esta limitación era peor: con
   perfil 1,20, «Sorpréndeme» proponía *The Secret Adversary* con etiqueta
   heredada **B2**, y el v4 leyendo el texto devolvía **C1**.
4. **La literatura del catálogo es, en su inmensa mayoría, C1–C2**: 1 libro A1,
   40 A2 y 557 B1 de 53.179. Para un lector B1 la respuesta no son libros
   enteros sino capítulos (3.644 en 1.499 libros), y por nivel solo se ofrecen
   lecturas literarias: 288 entre A1 y B1.
5. **Los tamaños muestrales de la validación externa son pequeños**: 38 textos
   en Colab, 47 en local, con 3 textos en A1. Una diferencia de 0,05 entre dos
   niveles adyacentes con esas *n* no es significativa; lo que se afirma es el
   orden global, no cada comparación por pares.
6. **La validación no es enteramente independiente de la exploración.** El
   corpus de British Council se usó primero para diagnosticar (descubrir que el
   modelo no sabe leer menús) y después para validar. El filtro de prosa se
   definió por dos vías independientes precisamente para acotar ese problema,
   pero salió del diagnóstico y el conjunto ha
   sido mirado y ya no es virgen.
7. **La longitud del texto es un confusor en el corpus de examen.** Contar
   palabras alcanza 0,807 donde el modelo alcanza 0,860 (Cuadro 13).
8. **El modelo solo mide prosa continua en inglés.** Poesía, teatro, diálogo
   muy fragmentado y cualquier lengua distinta del inglés quedan fuera.
9. **El corpus de anclaje MCER es pequeño y de una sola fuente**: 654
   documentos aceptados de ELG CEFR English. Hasta el 12 de septiembre de 2026
   ni su composición ni el guion de entrenamiento estaban en el repositorio, y
   una auditoría externa lo señaló con razón: sin esa lista nadie podía
   comprobar que las fuentes de validación fueran ajenas a las de
   entrenamiento. **Ya están**: guion, tarjeta de métricas y las 144
   predicciones, en `entrenamiento_v4/`. Y la comprobación resultó necesaria de
   verdad: la primera validación con UniversalCEFR del apartado 7.5 se hizo
   sobre este mismo corpus y hubo que retirarla.
10. **British Council no se puede redistribuir, pero sí reconstruir.** Tiene
    derechos y no acompaña al repositorio; se reconstruye desde su manifiesto
    de URLs y SHA-256 y se verifica archivo por archivo con
    `tools/bajar_corpus_bc.py`. Comprobado desde una carpeta vacía el 12 de
    septiembre de 2026: da las mismas cifras del Cuadro 11. Las cifras internas
    del v4 (0,908 y 97,2 %) **también se recalculan** desde el repositorio
    (limitación 9).
11. **El cuaderno corre entero en un Colab limpio, pero correr no es
    recalcular.** Los pesos del v4 están publicados en Hugging Face
    (`MikeMaki1763/literalevel-v4`, repositorio público, descarga sin
    credenciales), así que el cuaderno se ejecuta de principio a fin y demuestra
    la inferencia sobre texto real. El cuaderno no reentrena el v4, que pide una
    GPU, pero **sus métricas sí se recalculan fuera de él**: los datos de
    entrenamiento son públicos (ELG CEFR English, en Hugging Face), el guion
    está en `entrenamiento_v4/` y las 144 parejas de nivel y predicción están
    publicadas. Recalculadas en CPU en menos de un minuto, dan las mismas
    cifras a cuatro decimales.
12. **El despliegue está en el escalón más barato, y eso tiene dos
    consecuencias.** La aplicación está publicada en Hugging Face Spaces
    (`MikeMaki1763/literalevel`), con dirección fija que sobrevive a apagar el
    equipo del autor. Cuesta **7 USD al mes**: un Space de Gradio exige cuenta
    Pro, y el hardware elegido, `cpu-basic`, es el que no añade coste sobre esa
    suscripción. Pero ese hardware **suspende el servicio tras 48 h sin
    visitas** (`gcTimeout` = 172.800 s según la API de
    Hugging Face), de modo que el primer visitante después de una pausa paga
    un arranque en frío mientras se cargan *torch* y los 328 MB del modelo.
    Está medido: reiniciando el Space, **31 s hasta que el runtime dice
    `RUNNING` y 32 s hasta que la página responde**. Es la cota inferior,
    porque ahí la imagen del contenedor ya estaba construida; despertar de
    una suspensión de 48 h añade traerla. El disco del contenedor **sí es
    efímero**, y por eso la estantería, el avance de lectura, el cuaderno y el
    perfil del lector se guardan en un **bucket de almacenamiento montado en
    `/data`** (18 USD por TB y mes en repositorio privado, y esto ocupa
    megas). Verificado de punta a punta: se fijó un perfil, se reinició el
    Space y el perfil seguía ahí. Era la acción A4 de la estrategia y está
    cerrada.
13. **La prueba de usuario tiene n = 2.** Esmeralda y Laura son dos lectoras.
    Su valor es cualitativo y de diagnóstico, no estadístico: sirve para
    encontrar fallos de usabilidad graves —y encontraron varios—, no para
    estimar satisfacción media. Desde el 14 de septiembre hay cuentas repartidas a los primeros usuarios (`auditoria/feedback_usuarios_2026-09-14.md`), y la primera respuesta ya enseñó un hueco: una lectora B1 buscó libros de amor y encontró pocos. El catálogo le da la razón: entre las lecturas que ofrece la recomendación por nivel —literarias, sin las excluidas y a 0,25 del nivel— y con *love*, *romance* o *courtship* al principio de alguna palabra de sus temas de catálogo, la franja de B1 (0,55 a 1,05) tiene 1 libro y la de B2 (0,95 a 1,45), 31, que son 29 títulos distintos, porque la novela romántica de Gutenberg está casi toda en C1 y C2; ningún texto libre lleva esas palabras en sus temas. Recontado el 15 de septiembre con el catálogo que carga la aplicación. Es un hueco de composición del catálogo, no de tamaño.
14. **La explicación contextual depende de un servicio externo de pago.** Sin
    clave, la aplicación sigue funcionando en todo lo que no sale a la red
    desde el servidor: diccionario, fonética, buscador y puntuación. Los
    enlaces de audio de Wiktionary son aparte —los descarga el navegador del
    lector, así que necesitan conexión, aunque no clave—. Lo que se apaga sin
    clave son tres cosas: la explicación en contexto, la corrección de
    pronunciación y el resumen de «¿de qué trata?» de la ficha.

---

## 10. Trabajo futuro

1. **Hecho el 12 de septiembre de 2026:** remedir el catálogo completo y
   sustituir las etiquetas heredadas por medidas del v4 sobre el libro entero
   (53.179 libros, 585.111 capítulos).
2. **Hecho el 12 de septiembre de 2026:** publicar el guion de entrenamiento y
   la composición del corpus de anclaje, que resultó ser público (ELG CEFR
   English). Las métricas del v4 ya se recalculan en lugar de citarse.
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
7. **Convertir las cinco acciones en herramientas de un agente**
   (*function calling*). Hoy cada una tiene su botón: medir un capítulo,
   buscar por significado, abrir un libro, explicar una palabra y corregir la
   pronunciación. Las cinco ya son funciones con argumentos y salida
   tipada —que es justo lo que un esquema de herramienta necesita—, así que
   el trabajo no sería reescribirlas sino declararlas y dejar que el modelo
   elija: «quiero algo de misterio victoriano que pueda leer» debería
   encadenar la búsqueda, el filtro por nivel y la ficha sin que el lector
   sepa que hay tres pasos. **No se hizo por una razón de calendario, no de
   diseño**: la aplicación llevaba dos días congelada y auditada cuando esto
   se planteó, y meter un bucle de herramientas en el camino que ya funciona
   habría cambiado el riesgo de la entrega por una mejora que no estaba
   medida.

---

## 11. Conclusiones

**Se cumplió el objetivo ordinal, que era el objetivo.** Hay dos resultados y
vienen de corpus distintos, así que conviene no mezclarlos. Sobre **textos externos con nivel MCER oficial** —los 47 de British
Council— el modelo ordena los niveles de forma estrictamente creciente
(0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952) y alcanza Spearman **0,829** con
38 textos, **0,860** con los 47. El **0,908 y el 97,2 %** son otra cosa: salen
del conjunto de validación de **144 documentos del propio corpus de anclaje**,
que es interno. Atribuirlos a los externos sería un error. Para el problema planteado —elegir qué
leer— acertar el orden es lo que importa; acertar la letra exacta es un lujo.

**Y aquí hay que poner un límite que el documento no ponía.** Ese orden está
medido sobre **textos de examen**, de A1 a C1 y sin C2, no sobre novelas. La
aplicación puntúa novelas y dibuja sus curvas, pero **la dificultad de una
novela no se ha contrastado contra ninguna etiqueta externa ni contra ningún
lector**. Que el modelo ordene bien cinco niveles de material de examen es una
señal razonable de que la escala tiene sentido; no es una demostración de que
ayude a elegir mejor un libro. Ese vínculo queda pendiente, y es lo que mediría
el accionable de comparar la tasa de libros terminados con recomendación y sin
ella.

**En las configuraciones probadas, el cuello de botella no estuvo en el
algoritmo sino en la representación del texto.** Aumentar la potencia del
clasificador sobre las mismas variables no mejoró nada —XGBoost con trescientos
árboles queda por detrás de una regresión logística, en las dos tandas—,
mientras que cada vez que se enriqueció la representación el resultado subió: de
conteos a *embedding* y de ahí a leer el texto crudo con atención, hasta 0,67
niveles de error ordinal.

**Dicho eso, esto no es un experimento controlado y no conviene venderlo como
tal.** Entre la fila del *embedding* y la del transformador cambian a la vez la
representación, la arquitectura, el preentrenamiento y el objetivo —clasificación
de seis clases frente a regresión—, así que el salto no se puede atribuir a un
solo factor. Lo que la evidencia sostiene es la observación: **subir la potencia
del clasificador no movió el resultado y cambiar la representación sí**. Aislar
cuál de los cuatro factores pesa más exigiría comparaciones que este trabajo no
hizo.

**Sobre el tamaño de ese salto conviene ser preciso**, porque el cuadro 7 tiene
dos tandas y es fácil restar filas que no se pueden restar. Contra las tres
variables clásicas de la tanda histórica, el paso al *embedding* va de 1,39 a
0,93. Pero el cuadernillo entregado ejecuta una regresión logística sobre tres
variables clásicas, sobre esa misma partición, y obtiene **1,295**; con
diecisiete variables en vez de tres baja a **1,061**.

**No son exactamente el mismo modelo, y decir que sí lo eran era impreciso.**
Las tres variables se llaman igual en las dos tandas, pero `palabras_raras` no
contiene lo mismo: en el cuadernillo se calcula contra las 3.000 palabras más
frecuentes **del entrenamiento de CLEAR**, y en la tanda histórica contra las
listas externas de NLTK y del SPGC (Cuadro 4). Misma partición y misma semilla,
sí; misma definición de las variables, no. Esa es la razón más probable de los
0,10 de diferencia. Medido así, contra unas variables clásicas bien surtidas, la ventaja
del *embedding* es bastante menor de lo que sugiere la comparación con tres.
**La brecha que no se cierra con más conteos es la del transformador.** La conclusión cualitativa se sostiene; la cifra con la
que se vendía, no.

**Escalar el corpus no siempre mejora nada, y conviene decirlo.** Multiplicar
por 2.500 el corpus de referencia léxica —de 18 libros a los 45.345 del SPGC—
llevó la correlación de −0,379 a −0,326: **empeoró**. La muestra intermedia de
397 libros daba −0,330. La ley de Zipf explica por qué.
El paso se conservó por cobertura, no por métrica, y así se reporta.

**La velocidad se ganó sin mover ninguna cifra publicada, y con la salvedad
dicha.** Doce hilos y lotes de 64 en CPU, fp32 con lote 128 en GPU: +33 % y
×13,8 respectivamente, con 839 de 840 ventanas idénticas a tres decimales y la
restante a 0,001. No es exactitud bit a bit —eso sería falso— sino diferencias
por debajo del redondeo con el que se guarda todo. Y se rechazaron dos
palancas más rápidas —int8 y fp16 en la tarjeta local— porque una desviaba
0,210 sobre una escala de 0 a 2 y la otra era 4,8 veces más lenta. **Medir
antes de optimizar, y medir también lo que se descarta.**

**Lo que convierte esto en un producto no es el modelo, es lo que se hizo con
lo que dijo una lectora de quince años.** Un ciclo completo —observar, escuchar
la queja, diagnosticar el fallo propio y corregirlo— vale más que un punto de
correlación. Ese ciclo se documenta en el documento de estrategia, y su
resultado son seis etiquetas reescritas, cinco paletas verificadas contra el
criterio de contraste WCAG AA y una interfaz que se puede usar con el pulgar.

**Y queda pendiente lo que más pesa.** La aplicación funciona y ya tiene
dirección fija, pero sobre el hardware más barato: se suspende por
inactividad, y el primer visitante tras la siesta paga el arranque en frío.
El catálogo ya está medido entero —53.179 libros— y las métricas del v4, que
el documento citaba sin poder recalcular, ya se recalculan desde el
repositorio. Lo que queda está planificado con coste y criterio de terminado
en el documento de estrategia.

**Y para qué sirve esto, dicho como decisión y no como métrica.** Un lector que
hoy elige libro por la portada puede, con esta herramienta, hacer tres cosas
que antes no podía: saber **antes de empezar** si un libro concreto le queda
grande, ver **en qué capítulo** se va a atascar y decidir si lo salta o lo
prepara, y llevarse las palabras que consultó **con la frase en la que
aparecieron**, que es la unidad con la que se recuerda un idioma. Para quien
enseña, el cambio es de otro tipo: un catálogo de dominio público con
dificultad medida convierte «lee algo de tu nivel» en una lista concreta, y el
coste marginal de añadir un libro es de segundos de cómputo, no de una tarifa
por título.

**Lo que este proyecto recomienda hacer a continuación, en orden de valor por
hora de trabajo**, está en el documento de estrategia con coste y criterio de
terminado. La remedición del catálogo, que era lo que separaba un prototipo de
un producto, ya está hecha; lo siguiente es calibrar la escala, que es la
diferencia entre decirle a alguien que un libro es A2 y que lo sea.

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
consultado y el perfil de nivel— se guardan separados por navegador y no se
comparten entre visitantes. Sí se comparten las cachés de contenido —definiciones,
audio generado, curvas y resúmenes de un mismo texto y el análisis de lectura
natural de una frase—, que no son historial de nadie. Ningún texto con derechos se
distribuye ni se imprime fuera del entorno de cómputo: de los corpus con
licencia restrictiva solo salen estadísticas agregadas.

---

## Referencias

Abid, A., Abdalla, A., Abid, A., Khan, D., Alfozan, A., & Zou, J. (2019).
*Gradio: Hassle-free sharing and testing of ML models in the wild*
(arXiv:1906.02569). arXiv. https://arxiv.org/abs/1906.02569

Breuker, M. (2023). CEFR labelling and assessment services. En G. Rehm (Ed.),
*European Language Grid* (pp. 277–282). Springer.
https://doi.org/10.1007/978-3-031-17258-8_16

Carnegie Mellon University. (s. f.). *The CMU Pronouncing Dictionary*
[Conjunto de datos]. https://github.com/cmusphinx/cmudict

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

Grossman, R., & Chen, Y. (2026). *Zero-shot large language models for automatic
readability assessment* (arXiv:2604.24470). arXiv.
https://arxiv.org/abs/2604.24470

Hu, M., & Nation, P. (2000). Unknown vocabulary density and reading
comprehension. *Reading in a Foreign Language, 13*(1), 403–430.

Imperial, J. M., Barayan, A., Stodden, R., Wilkens, R., Muñoz Sánchez, R., Gao,
L., Torgbi, M., Knight, D., Forey, G., Jablonkai, R. R., Kochmar, E., Reynolds,
R. J., Ribeiro, E., Saggion, H., Volodina, E., Vajjala, S., François, T.,
Alva-Manchego, F., & Tayyar Madabushi, H. (2025). UniversalCEFR: Enabling open
multilingual research on language proficiency assessment. En *Proceedings of the
2025 Conference on Empirical Methods in Natural Language Processing* (pp.
9703–9755). Association for Computational Linguistics.
https://doi.org/10.18653/v1/2025.emnlp-main.491

Kandpal, N., Lester, B., Raffel, C., Majstorovic, S., Biderman, S., Abbasi, B.,
Soldaini, L., Shippole, E., Cooper, A. F., Skowron, A., Kirchenbauer, J.,
Longpre, S., Sutawika, L., Albalak, A., Xu, Z., Penedo, G., Ben Allal, L.,
Bakouch, E., Pressman, J. D., … Murray, T. (2025). *The Common Pile v0.1: An 8TB
dataset of public domain and openly licensed text* (arXiv:2506.05209). arXiv.
https://arxiv.org/abs/2506.05209

Krashen, S. D. (1985). *The input hypothesis: Issues and implications*.
Longman.

Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M.,
Zettlemoyer, L., & Stoyanov, V. (2019). *RoBERTa: A robustly optimized BERT
pretraining approach* (arXiv:1907.11692). arXiv.
https://arxiv.org/abs/1907.11692

MakeHuman Community. (s. f.). *License*.
https://static.makehumancommunity.org/about/license.html

MetaMetrics. (2026). *Lexile® Text Analyzer content creator annual tiered pricing
program*. https://www2.metametricsinc.com/content-creator-annual-pricing

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

Pratham Books. (s. f.). *StoryWeaver* [Biblioteca digital].
https://storyweaver.org.in

Project Gutenberg. (2026). *Project Gutenberg* [Biblioteca digital].
https://www.gutenberg.org

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using
Siamese BERT-networks. En *Proceedings of the 2019 Conference on Empirical
Methods in Natural Language Processing* (pp. 3982–3992). Association for
Computational Linguistics. https://doi.org/10.18653/v1/D19-1410

Saide. (s. f.). *African Storybook* [Biblioteca digital].
https://www.africanstorybook.org

Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). *DistilBERT, a distilled
version of BERT: Smaller, faster, cheaper and lighter* (arXiv:1910.01108).
arXiv. https://arxiv.org/abs/1910.01108

TeakReader. (s. f.). *English reading level checker for books*.
https://teakreader.com/english-reading-level-checker-for-books

The Asia Foundation. (s. f.). *Let's Read* [Biblioteca digital].
https://www.letsreadasia.org

Vajjala, S., & Lučić, I. (2018). OneStopEnglish corpus: A new corpus for
automatic readability assessment and text simplification. En *Proceedings of
the 13th Workshop on Innovative Use of NLP for Building Educational
Applications* (pp. 297–304). Association for Computational Linguistics.
https://doi.org/10.18653/v1/W18-0535

Voice of America. (s. f.). *VOA Learning English*.
https://learningenglish.voanews.com

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
