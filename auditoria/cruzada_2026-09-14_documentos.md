# Auditoría cruzada a ciegas: documentos contra código (14–15 sep 2026)

**Auditor:** entrega-4e. **HEAD al empezar:** `804e649`. Los documentos se actualizaron por última vez en `2fbf0d9`.

**Archivos auditados:**
- `entrega/documento.tex` y `documento.md`;
- `entrega/estrategia.md`;
- `entrega/presentacion.tex`;
- `entrega/guion_video.md` y `guion_demo_en_vivo.md`;
- `AGENTS.md` y `README.md`.

**Método:** skill `auditar-proyecto-datos`, con la rúbrica de `modulo-5-literalevel`. Solo lectura; no se abrió nada de `auditoria/`.

## Qué se ejecutó y qué solo se leyó

**Ejecutado:**
- Recuentos con Python sobre:
  - `catalogo_medido.csv`, `catalogo_externo.csv`, `avisos_contenido.csv` y `correcciones_catalogo.csv`;
  - el SQLite de Kaikki;
  - la cabecera JSON de `cara.glb` y `lengua.glb`.
- Cotejo de citas del `.tex` contra `referencias.bib` y lista de sus `\section`.
- Diferencia de cifras entre `documento.md` y `documento.tex`.
- Suites y herramientas:
  - `tools/contar_guion.py`;
  - `pruebas_corpus.py` con `LITERALEVEL_SIN_CLAVES=1`;
  - `pruebas_api.py`: 51 de 51 en la auditoría anterior (`a4e7dd1`, sobre `4d4bb1b`).
- En el Space publicado: `/api/estado` y dos búsquedas de «dostoyevski» con `/api/buscar`, sin coste.

**Solo leído:**
- el código que respalda cada afirmación (`ui.py`, `api.py`, `scoring.py`, `reader.py`, `perfil.py`, `front/src`);
- el README de `boca3d`.

**No verificado:**
- las cifras que piden el filtro literario o datos por capítulo:
  - «3.644 capítulos en 1.499 libros»;
  - 290 y 1.676 libros literarios;
  - 1.442 textos servidos que cambian;
- las mediciones históricas de rendimiento (8,19, 112,7 y 2.022 ventanas/s; 61 libros/min);
- «Doggie is Happy», 0,349 frente a 0,007.

---

## Hallazgos

### [SERIO] El 0,908 se llama «validación ciega» en la portada, el resumen y la respuesta preparada para el profesor

- **Dónde:**
  - `entrega/documento.tex:214`, en la cifra destacada de la portada;
  - `entrega/documento.tex:243` (resumen) y `entrega/documento.md:41-42`;
  - `entrega/guion_demo_en_vivo.md:176`.
- **Qué dice:**
  > `{\scriptsize Spearman, validación ciega}`
  >
  > «En validación ciega alcanza una correlación de Spearman de 0,908 con el nivel de referencia»
  >
  > **Dice:** «En validación ciega tiene una correlación de Spearman de 0,908 …»
- **Por qué:** el propio documento lo desmiente en §7.4 (`documento.md:741-743`): «**no es un conjunto de prueba virgen**, porque el entrenamiento se quedó con el punto de control que mejor puntuaba en esos mismos 144 documentos». Las conclusiones (`documento.md:1492-1494`) lo llaman «interno». La skill `corregir-sin-inventar` ya tenía «validación externa ciega» en su lista de absolutos falsos. Además es la primera respuesta del guion de preguntas: la frase que más probablemente se oiga en voz alta.
- **Arreglo:** decir «validación interna» (144 documentos reservados del corpus de anclaje) en los cuatro sitios, y dejar «ciega» fuera.

### [SERIO] El cuadro contra Lexile pone «~3 h de A100» y que «cabe en la cuota» de 10 USD; el propio documento midió 17 horas

- **Dónde:**
  - `entrega/documento.tex:2876` y `documento.md:1305` (Cuadro 17);
  - `documento.tex:2923` y `documento.md:1313`;
  - `entrega/estrategia.md:474-477`.
- **Qué dice:**
  > `Lexile, tarifa de creador de contenido & \textbf{3.824--54.636} USD/año & ~3 h de A100`
  >
  > «medirlos aquí cabe en la cuota de una suscripción de unos 10 USD al mes»
  >
  > «Medirlos aquí son **unas tres horas de GPU A100** —**diecisiete de reloj** …— y eso cabe en la cuota de una suscripción de Colab Pro de unos 10 USD al mes, pero justo»
- **Por qué:**
  - En §8.3 el mismo documento dice que la estimación de tarjeta «resultó ser la mitad de la respuesta»: el ritmo real fue «**unas 17 horas** … cinco veces la cifra de tarjeta» (`documento.tex:2788`). El Cuadro 17 conserva la cifra que el texto ya ha retirado.
  - Según `estrategia.md:301-303`, la medición real no se hizo en A100: «en una T4 gratuita, en tandas reanudables … la última, 9.795 libros, tardó 55 minutos».
  - Que 17 horas de A100 «quepan» en la cuota de 10 USD no está medido en ningún sitio. Además, desde el 14 de septiembre no hay presupuesto.
- **Arreglo:** en el cuadro, «medido en T4 gratuita (horas de reloj en tandas)» o «~17 h de reloj», y quitar «cabe en la cuota» o sustituirlo por lo que se pagó de verdad (nada).

### [SERIO] El inventario de fuentes no incluye el corpus que entrenó el modelo desplegado ni las cuatro bibliotecas de los 15.357 textos

- **Dónde:** `entrega/documento.tex:1147` (Cuadro 2) y `documento.md:224-232`.
- **Qué dice:**
  > `\textbf{Story\-Weaver / Global Digital Library} & Lecturas graduadas del catálogo heredado, retirado el 12 de septiembre de 2026 & 1.049 registros & API pública de contenidos & Abierta, pero sin descarga de texto`
- **Por qué:**
  - La rúbrica pide «Descripción de los datos (fuente, calidad, relevancia)». En la tabla de fuentes faltan:
    - **ELG CEFR English**: el corpus de anclaje del v4, 712 documentos, CC BY-NC-SA 4.0. Aparece en §7.4 pero no en el inventario.
    - Los textos libres de **StoryWeaver, Let's Read, African Storybook y VOA**. `catalogo_externo.csv` da `storyweaver` 14.500, `letsread` 326, `african_storybook` 278 y `voa` 253.
    - `common-pile/project_gutenberg`, de donde se descargó el texto.
    - **CMUdict**: 126.052 palabras con licencia BSD, que usa la corrección de voz.
  - La única fila de StoryWeaver dice «sin descarga de texto», y la app sirve hoy 14.500 textos de StoryWeaver.
  - Verificado con el recuento del CSV.
- **Arreglo:** añadir al Cuadro 2 una fila por ELG CEFR English, por cada biblioteca libre (con su licencia y recuento), por common-pile y por CMUdict, y marcar la fila de StoryWeaver de 1.049 como «catálogo heredado, retirado».

### [SERIO] Fuentes citadas en el texto que no están en las referencias APA

- **Dónde:**
  - `entrega/documento.tex:2171`;
  - `entrega/estrategia.md:488`;
  - el Cuadro 17 (`documento.tex:2876`) y `presentacion.tex:421-424`.
- **Qué dice:**
  > «de UniversalCEFR (Imperial et al., 2025)»
  >
  > «alcanza **0,725** (Grossman y Chen, n = 1.890, diez modelos abiertos)»
  >
  > «las dos primeras filas vienen de un estudio ajeno sobre el mismo corpus»
- **Por qué:**
  - Las 25 entradas de `referencias.bib` están citadas y no sobra ninguna (comprobado: 27 comandos de cita, 0 claves sin entrada, 0 entradas sin citar).
  - Pero van en texto plano, sin entrada en ninguna lista de referencias:
    - Imperial et al. (2025) y Grossman y Chen;
    - el estudio del Pearson 0,517 y 0,725;
    - «Google publicó algo parecido» (`estrategia.md:489-490`);
    - la tarifa de Lexile, TeakReader y ELG CEFR English;
    - las bibliotecas libres, MakeHuman y CMUdict.
  - La rúbrica califica «Referencias en APA», y un evaluador que busque el 0,725 no encuentra de dónde sale.
- **Arreglo:** entradas `.bib` para Imperial et al. (2025), Grossman y Chen, el conjunto ELG CEFR English, CMUdict y la página de tarifas de Lexile, citadas con `\parencite`; y las mismas en la lista de `estrategia.md`.

### [MENOR] `documento.md` §7.4 todavía dice que la remedición está «en curso» y que las etiquetas son las heredadas

- **Dónde:** `entrega/documento.md:702-705`.
- **Qué dice:**
  > «esa remedición está **en curso** (accionable A3), así que las etiquetas que hoy lleva el catálogo siguen siendo las heredadas del v1»
- **Por qué:** contradice la misma copia (§4.3: «Y se remidió. El 12 de septiembre de 2026 terminó»; limitación 3: «Ya no son heredadas»). El `.tex` ya no lo dice: `en curso` y `heredadas del v1` no aparecen en él. La copia de lectura se ha quedado atrás del entregable.
- **Arreglo:** borrar la frase en `.md`, dejándolo como el `.tex`.

### [MENOR] `documento.md` §8.6 dice que las métricas del v4 no se pueden rehacer, y el resto dice que sí

- **Dónde:** `entrega/documento.md:1333-1335`.
- **Qué dice:**
  > «el código y la inferencia desde los pesos públicos se pueden rehacer, **las métricas del v4 no**, porque su corpus de anclaje tiene derechos»
- **Por qué:**
  - Lo contradicen §7.4 («se **recalcularon** con el guion, los pesos publicados y los datos públicos de ELG … idénticas a cuatro decimales»), las limitaciones 9 a 11 y `estrategia.md:533-535` («**y** las métricas internas del v4 se pueden rehacer»).
  - ELG CEFR English está en Hugging Face.
  - `tiene derechos` no aparece en el `.tex`: es otra frase que solo quedó en la copia.
- **Arreglo:** dejar la frase como la del `.tex`.

### [MENOR] El Cuadro 15 dice que la búsqueda está «acotada al rango de lectura», y el mismo apartado dice que «acerca y no filtra»

- **Dónde:** `entrega/documento.tex:2434` y `documento.md:1045`, frente a `documento.md:1069` y `1072-1074`.
- **Qué dice:**
  > «Búsqueda semántica en español sobre el catálogo, acotada al rango de lectura del perfil»
  >
  > «la casilla **acerca y no filtra**» … «Lo que devuelve la búsqueda **no está filtrado por el nivel del lector**»
- **Por qué:**
  - **Verificado en el Space:** «dostoyevski» con nivel 1,20 devuelve seis libros C1 entre 1,700 y 1,711. No hay nada dentro del rango de 0,95 a 1,45.
  - La estrategia ya corrigió dos veces una etiqueta por prometer ese filtro (`estrategia.md:189`).
- **Arreglo:** en el Cuadro 15, «ordenada por significado, con el nivel del lector como criterio de orden».

### [MENOR] La declaración de alcance dice que los datos van «por sesión» y que solo se comparte la caché de definiciones

- **Dónde:** `entrega/documento.tex:3218` y `documento.md:1607-1610`.
- **Qué dice:**
  > «se guardan separados por sesión y no se comparten entre visitantes. Solo la caché de definiciones se comparte»
- **Por qué:**
  - La identidad no es la sesión: es un identificador de navegador (`X-Lector`, en `localStorage`), que sobrevive a cerrar la pestaña.
  - Además de las definiciones, se comparten la carpeta de análisis (curvas y sinopsis, en `ui.RUTA_ANALISIS`, con clave del hash del texto) y la caché de audio TTS.
  - Nada de eso es historial de nadie, pero la frase «solo» es falsa.
  - Leído en `ui._clave_libro`, `api.sinopsis` y `ui._dir_lector`.
- **Arreglo:** «separados por navegador … Se comparten las cachés de contenido (definiciones, audio, curvas y resúmenes de un mismo texto), no el historial».

### [MENOR] «Las tres [condiciones] se cumplen», pero C3 se probó sobre la interfaz que ya no se entrega

- **Dónde:**
  - `entrega/documento.md:177` y su equivalente en el `.tex`;
  - `estrategia.md:619`.
- **Qué dice:**
  > «Las tres se cumplen y se documentan, respectivamente, en 7.4, 7.5 y en el documento de estrategia.»
- **Por qué:**
  - C3 es «Un usuario sin formación técnica completa el recorrido».
  - Esmeralda y Laura usaron Gradio, y el resumen lo reconoce: «no equivalen a una validación de usuario de todos los cambios posteriores».
  - A8, repetir la prueba «sobre Angular», sigue pendiente (`estrategia.md:599`).
- **Arreglo:** «C1 y C2 se cumplen; C3 se cumplió sobre la interfaz anterior y está pendiente sobre el front entregado (A8)».

### [MENOR] Cifras de pruebas con fechas distintas entre archivos, y la tabla de métricas se quedó en 32 de 35

- **Dónde:**
  - `entrega/estrategia.md:621`;
  - `documento.tex` y `.md` §8.5 (`documento.md:1285-1286`);
  - `README.md:195`.
- **Qué dice:**
  > «**Parcial, corte 13–14 sep**: API 32/35 en entorno aislado»
  >
  > «**51 de 51 pruebas API**, las **349 pruebas extremas** del motor y 24 de corpus»
  >
  > `| pruebas_corpus.py | textos libres en catálogo y lector | 25 de 25 |`
- **Por qué:**
  - La tabla de métricas de la estrategia sigue en 32 de 35, cuando la misma estrategia (§4.6) da 51 de 51.
  - Corpus sale 24 en el documento (a `8ee42f0`), 25 en el README (a `74ffffc`) y **27 ejecutado hoy en `804e649`** («Todas las pruebas de corpus pasan (27)»).
  - Cada cifra lleva su fecha, pero la tabla de métricas presenta la vieja como estado.
- **Arreglo:** poner en la tabla de métricas el último recuento con su commit, y actualizar corpus a 27 en el README.

### [MENOR] «El validador garantiza la precisión de lo que se enseña» es un absoluto sacado de diez frases

- **Dónde:** `entrega/documento.tex` §8.5 (`documento.md:1293`) y `entrega/estrategia.md:445`.
- **Qué dice:**
  > «El validador garantiza la precisión de lo que se enseña, no que se enseñe todo.»
- **Por qué:**
  - Lo medido son 2 reducciones y 4 enlaces correctos en 10 frases. Eso no es una garantía.
  - La Central me pasó un hallazgo de e6 sobre esta misma pieza: acepta «gonna» sin verbo detrás. Aquí no lo he comprobado; va en la parte (B) del encargo.
- **Arreglo:** «en esa batería, todo lo que llegó al lector era correcto; el validador filtra con una lista cerrada y con la IPA de diccionario».

### [MENOR] «El acento a 4,5:1» en el lector teñido vale contra el fondo, no contra los chips

- **Dónde:** `entrega/documento.tex` §8.5 (`documento.md:1291`) y `entrega/estrategia.md:443`.
- **Qué dice:**
  > «El lector toma el fondo y el acento de esa paleta, con el texto a 7:1 o más y el acento a 4,5:1»
- **Por qué:** en el Space, la pista del lector (texto de acento sobre `acento-suave`) da 4,17:1 en SWV369 y SWV10029 en tema claro. Está medido en la auditoría `a4e7dd1`.
- **Arreglo:** «el acento a 4,5:1 sobre el fondo», o corregir `tinte.ts` y dejar la frase.

### [MENOR] El reparto por nivel del Cuadro 3b no aplica la corrección de PG2242 y no cuadra con el Space

- **Dónde:** `entrega/documento.md:334-342` y su equivalente en el `.tex`.
- **Qué dice:**
  > `| B1 | 558 | |` … `| C1 | 23.454 | |`
- **Por qué:**
  - **Verificado:** con la regla de `ui._cefr` sobre `catalogo_medido.csv`, B1 da 558 y C1 23.454 **sin** la corrección, y 557 y 23.455 **con** ella (PG2242 pasa de 0,697 a 1,713).
  - El Space aplica la corrección: `/api/estado` da B1 6.100 = 5.543 + 557 y C1 24.249 = 794 + 23.455.
  - El mismo documento cuenta la corrección en §8.5.
- **Arreglo:** 557 y 23.455, con una nota «tras `correcciones_catalogo.csv`».

### [MENOR] La estrategia describe como actual un botón de Gradio que el front no tiene

- **Dónde:** `entrega/estrategia.md:111`.
- **Qué dice:**
  > «Un botón de «Sorpréndeme con algo de mi nivel» además de la búsqueda»
- **Por qué:** en `front/src` no aparece «Sorpréndeme». El front tiene la pestaña «A mi nivel» (`encontrar.ts:45`). La tabla de §2.1 es «cómo se atiende» hoy, no la historia del Cuadro 1.
- **Arreglo:** «La pestaña «A mi nivel» de *Encontrar* propone lecturas sin buscar».

### [MENOR] Cambios posteriores a `2fbf0d9` que los documentos no recogen, y un dato del guion del vídeo que ya no se reproduce

- **Dónde:**
  - `documento.md:1272-1274` y `estrategia.md:597` («A fecha de `db366b8` se excluyen … 600 que no son lectura»);
  - `entrega/guion_video.md:162-164`.
- **Qué dice:**
  > «sin perfil sale tercero, tras *The Idiot* y *The House of the Dead*»
- **Por qué:**
  - `3524357` y el reinicio 16 (`804e649`) sacan además 163 textos libres de buscar y recomendar, y cambian cómo ordena el nivel.
  - **Verificado en el Space:** sin nivel, «dostoyevski» devuelve Best Russian Short Stories, The Idiot, Stavrogin's Confession, Uncle's Dream, The House of the Dead y Poor Folk, y *Crime and Punishment* no está en los seis primeros.
  - Con nivel 1,20 sale segundo, como dice el guion, y ese es el caso que se enseña.
- **Arreglo:** añadir los 163 con su commit donde se citan los 600, y quitar del guion la frase de «sin perfil».

### [DUDA] «La franja B1 tiene 1 título y la B2, 28»: con la regla que da el propio texto salen 2 y 31

- **Dónde:** `entrega/documento.md:1440` y `entrega/estrategia.md:447`.
- **Qué dice:**
  > «con *love*, *romance* o *courtship* en los temas o el gancho, la franja de recomendación de B1 (0,55 a 1,05) tiene 1 título y la de B2, 28»
- **Por qué:** con esa regla literal sobre los dos CSV (`\b(love|romance|courtship)` en `temas` y `hook`, y dificultad dentro de la franja) salen **2** en B1 y **31** en B2 en Gutenberg, y 0 en libres. La diferencia puede venir del filtro literario y de los 600 excluidos que usa la recomendación, pero el texto no lo dice, y con lo escrito no se reproduce. La franja sí es correcta: `perfil.HOLGURA` = 0,25 alrededor de 0,8.
- **Arreglo:** añadir «entre las lecturas literarias que ofrece la recomendación», si ese es el filtro, o corregir las cifras.

### [DUDA] Los empates de nivel caen hacia arriba solo por accidente de coma flotante

- **Dónde:** `app/ui.py:2124-2141`, que es la regla con la que se cuentan los Cuadros 3 y 3b.
- **Qué dice:**
  > «Redondea los empates HACIA ARRIBA» … `i = int(math.floor(min(5.0, max(0.0, interno)) + 0.5))`
- **Por qué:**
  - Comprobado: 1,4 × 2,5 da 3,5 y cae en C1, igual que 0,6 y 1,8. La regla funciona.
  - Pero 20 libros del catálogo miden exactamente 1,4, así que el recuento de B2 y C1 depende de ella. Si alguien la cambia por `round`, el Cuadro 3b se mueve 20 libros sin tocar ningún dato.
  - No es un error, es fragilidad. Queda como DUDA para quien toque `ui.py`.
- **Arreglo:** una prueba que fije `_cefr(1.4) == "C1"` y `_cefr(1.0) == "B2"`.

---

## Rúbrica del Módulo 5: qué hay y qué falta en estos archivos

- **Documento (15).** Tiene todas las secciones en el orden exigido: Resumen, Introducción, Planteamiento, Estrategia, Datos, Exploratorio (univariado, bivariado y multivariado), Procesamiento con justificación por transformación, Modelación, Resolución, Limitaciones, Trabajo futuro, Conclusiones, Declaración de alcance y Referencias. Lo comprobé con las `\section` y `\printbibliography`. **Faltan** las entradas APA del hallazgo SERIO de referencias, y las fuentes del inventario.
- **Estrategia (15).** Están los usuarios (§2), la usabilidad (§4), los diez accionables con coste y criterio de terminado (§6) y la compañía ficticia (Peldaño). **Falta** actualizar la tabla de métricas (32 de 35).
- **Presentación (10).** Tiene 15 diapositivas con la paleta del documento; las cifras cuadran con el documento. La diapositiva «Contra quién compite» avisa bien de que «No son comparaciones cara a cara», pero **no cita** de dónde salen el 0,517 y el 0,725.
- **Vídeo (20).** El guion cumple los 5 minutos: `tools/contar_guion.py` da 496 palabras, 3:18 a 150 palabras por minuto, que es lo que publica el guion. Grabarlo queda fuera de estos archivos.
- **Demo en vivo (25).** El objetivo de 4:00 cabe entre 3 y 5 minutos, y hay plan B y preguntas preparadas. **Corregir** «validación ciega» en la primera respuesta.

## Comprobado y correcto

- **Diccionario Kaikki** (ejecutado): 1.487.639 filas, 243 MB, IPA en 46.794, audio en 7.003 e IPA británica y americana en 33.635.
- **Catálogo** (ejecutado):
  - Gutenberg: 53.179 IDs únicos, 585.111 capítulos y media 1,742.
  - Externo: 15.357 textos (StoryWeaver 14.500, Let's Read 326, African Storybook 278 y VOA 253; 11.039 por texto y 4.318 por bloque). Por nivel, 749, 5.580, 5.543, 2.578, 794 y 113.
  - 11.872 textos libres entre A1 y B1 frente a 599 libros de Gutenberg.
  - El Space cuenta 68.536.
- **Avisos y correcciones** (ejecutado): los avisos son 2 (PG17824 y PG1330) y la corrección de PG2242 pasa de 0,697 a 1,713, como dicen los documentos.
- **API** (ejecutado): 40 rutas bajo `/api`, contadas con `grep`, y 51 de 51 pruebas.
- **Límites** (leído en el código):
  - de la tabla T8: 40 caracteres por palabra, 400 por oración, 20 MB por fichero y 100 MB descomprimidos por EPUB;
  - de la puerta: 15 intentos por IP y 20 por usuario;
  - de medir: 40 medidas, 6 curvas y 4 curvas en cola;
  - del vistazo: 30 capítulos y 2 ventanas de cada uno.
- **Filtro de prosa** (leído en `scoring.py`): 4 o más frases, entre 5 y 55 palabras de media y 35 % de líneas cortas, como dice §4.3(a).
- **Nivel del lector** (ejecutado): 6 preguntas y 3 fragmentos, y la holgura de 0,25 que da la franja B1 de 0,55 a 1,05.
- **Boca 3D:** 72 mallas (71 en `cara.glb` y 1 en `lengua.glb`, ejecutado); las 53 poses están en el README de `boca3d` (leído).
- **Gradio 6.26.0** instalado y fijado en requirements (ejecutado).
- **Recorrido del guion en el Space** (ejecutado): «dostoyevski» con nivel 1,20 devuelve *Crime and Punishment* en segundo lugar, como dice el guion del vídeo.
- **Botones que nombran los guiones** (`grep` en `front/src`): existen todos. Escuchar y ver, Más lento, Boca en 3D, Corrígeme, Una frase de mi libro, Escúchalo natural, Afinar, Mídeme con un texto, Mídeme con un libro que ya leí, Tu perfil, Ver cómo se mueve la boca, En español, Aquí significa, Puede ser, «aquí sin pausa», Otra frase, Repasa cinco y Recargar y reintentar.
- **«Mis palabras» enseña lo que se pronunció mal,** como dice la demo (leído en `palabras.ts`).
- **La presentación ya no promete *with us*:** usa *sorts of*, de la batería. La demo dice «No sale ningún enlace».
- **Bibliografía** (ejecutado): las 25 entradas de `referencias.bib` están citadas y no hay claves sin entrada.
- **Cifras del modelo:** son las mismas en documento, estrategia, presentación y guiones: 0,908, 97,2 %, 0,829, 0,860, 0,807, 0,668, las medias 0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952, 654 documentos y 82 M de parámetros.
- **Mensaje de presupuesto agotado:** el texto que cita la estrategia existe en `ui.py:3146` y la API lo pasa por `_humanizar`.
