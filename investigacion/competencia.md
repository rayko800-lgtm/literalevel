# Competencia y estado del arte

**Encargo 1.** Qué hay ahí fuera midiendo dificultad de lectura en inglés, dónde
está el valor real de LiteraLevel y qué nos gana la competencia hoy.

> **Cómo leer las cifras de este documento.** Cada número externo lleva enlace.
> Cuando no pude verificar una cifra en la fuente primaria lo digo en el propio
> renglón con la marca **[no verificado]**. Las cifras internas de LiteraLevel
> salen de `entrega/documento.md`, `README.md` y `app/scoring.py`, que leí
> entero antes de escribir esto.

---

## 1. Resumen ejecutivo

Tres cosas que conviene tener claras antes de la tabla:

1. **0,908 de Spearman está en un rango bueno, pero no es comparable con nada
   publicado**, porque el corpus de validación de 144 documentos es privado. La
   cifra que sí es comparable es otra: en CLEAR, el transformer afinado del
   proyecto da **Pearson 0,89**, y el mejor método *zero-shot* con LLM publicado
   hasta hoy da **0,725** en ese mismo corpus. Ahí sí ganamos, y por bastante.
2. **Un LLM con buen prompt no gana a un encoder afinado en esta tarea.** Hay
   tres evaluaciones publicadas que apuntan en la misma dirección, incluida una
   de Google donde un BERT de 45,7 M de parámetros bate a PaLM 2-L *y al
   anotador humano experto*. Lo que sí gana el LLM es a las fórmulas clásicas,
   sin afinar nada.
3. **Nadie hace lo que hace LiteraLevel de punta a punta, pero casi todos los
   trozos existen por separado y algunos están mejor hechos que los nuestros.**
   El valor no está en el modelo; está en el recorrido completo y en el idioma
   del lector.

---

## 2. Las fórmulas clásicas: qué miden de verdad

### 2.1 Qué hay dentro

| Sistema | Ingredientes reales | Qué sabe hacer | Qué no |
|---|---|---|---|
| **Flesch / Flesch-Kincaid** | Longitud media de oración + sílabas por palabra. Dos variables | Ordenar textos muy distintos; es gratis e instantáneo | No sabe qué significa una palabra. Ni sintaxis, ni cohesión, ni ambigüedad |
| **Dale-Chall** | Longitud de oración + % de palabras fuera de una lista de 3.000 palabras que alumnos de 4.º de primaria estadounidense reconocían ([Wikipedia](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)) | Introduce la carga léxica de forma explícita e interpretable | La lista es de 1948 (revisada 1995) y de un solo país. «Palabra difícil» = «no está en mi lista» |
| **Lexile** | Dificultad semántica (frecuencia inversa de las palabras en un corpus) + complejidad sintáctica (**medida como longitud de oración**) ([MetaMetrics](https://metametricsinc.com/wp-content/uploads/2017/07/The-Lexile-Framework-for-Reading.pdf)) | Pone lector y texto en la **misma** escala; es el estándar de facto en EE. UU. | Son las mismas dos variables de Flesch, mejor calibradas. Ver §3 |
| **ATOS** (Accelerated Reader) | Longitud media de oración + longitud media de palabra + nivel de vocabulario + **número de palabras del libro entero** ([informe ATOS, ERIC ED449468](https://files.eric.ed.gov/fulltext/ED449468.pdf)) | **Es la única fórmula clásica que mide el libro completo**, no una muestra | El «nivel» de un libro sigue siendo un solo número para 500 páginas |
| **Coh-Metrix** | ~100 índices de cohesión y coherencia: correferencia, conectores, solapamiento semántico LSA, densidad de ideas | Es lo único clásico que mide **coherencia del discurso**, no superficie | Necesita interpretación experta; no da un número accionable para un lector |

### 2.2 La crítica documentada

- **Miden dos cosas y las llaman «dificultad».** Flesch-Kincaid trata *tort*
  como palabra fácil (una sílaba) e *hippopotamus* como difícil (cinco). El
  ejemplo es de Language Log, recogido en
  [Effortmark, «Readability formulas: seven reasons to avoid them»](https://www.effortmark.co.uk/readability-formulas-seven-reasons-to-avoid-them-and-what-to-do-instead/).
- **Ni siquiera son consistentes consigo mismas.** Un estudio de 2023 en *JAMA
  Network Open* reporta que el mismo texto varía hasta **12,9 niveles de curso**
  entre ocho herramientas que dicen aplicar la misma fórmula. **[no verificado:
  lo encontré citado en fuentes secundarias, no pude abrir el artículo
  original]**.
- **Sus autores nunca las pensaron para esto.** Se calibraron para *predecir
  comprensión de escolares nativos*, no para graduar material de aprendices de
  segunda lengua. El MCER no interviene en ninguna de ellas.
- **El propio proyecto lo midió.** En `entrega/documento.md`, §5.3: las métricas
  clásicas son transformaciones distintas de los mismos dos ingredientes y por
  eso se estorban entre sí; con tres variables clásicas, un clasificador de seis
  niveles llega a **0,29 de exactitud** y XGBoost a **0,28**. El techo no era el
  clasificador, era la representación.

**Dato honesto en contra nuestra:** en el corpus CLEAR, las fórmulas clásicas
alcanzan **Pearson 0,517** contra el juicio humano
([Grossman & Chen, ACL 2026, tabla 3](https://arxiv.org/abs/2604.24470)).
Eso no es basura: es la mitad del camino, gratis, en microsegundos y sin GPU.
Cualquier argumento nuestro tiene que superar ese listón, no ignorarlo.

---

## 3. Lexile: el competidor comercial serio

### 3.1 Cómo funciona

Dos componentes, y solo dos: **dificultad semántica** (frecuencia inversa de las
palabras en un corpus de referencia) y **complejidad sintáctica** (aproximada
por la longitud de oración). Con ellos sitúa texto y lector en una escala común
(típicamente 200L–1600L), que es su verdadera innovación: no dice «este libro es
difícil», dice «este libro es para este lector».
Fuente: [The Lexile Framework as an Approach for Reading Measurement (MetaMetrics)](https://metametricsinc.com/wp-content/uploads/2017/07/The-Lexile-Framework-for-Reading.pdf).

### 3.2 Qué cubre

- **Base de títulos:** el titular de la nota de prensa de MetaMetrics habla de
  **más de 470.000 medidas** en la Lexile Titles Database; otras páginas de la
  propia empresa hablan de ~300.000 libros. No conseguí una cifra vigente
  autoritativa: la URL de la nota redirige a un índice genérico.
  **[cifra no verificada; el orden de magnitud, centenares de miles, sí]**
- **Alcance total declarado:** «más de 100 millones de libros, artículos y
  sitios web» han recibido una medida Lexile. **[no verificado, es cifra de
  marketing de la propia empresa]**
- Está integrado en catálogos de bibliotecas escolares, en pruebas
  estandarizadas de EE. UU. y en los principales editores educativos.

### 3.3 Qué cuesta

Esta sí la verifiqué, y es el dato más útil del apartado
([MetaMetrics, precios anuales de creador de contenido](https://www2.metametricsinc.com/content-creator-annual-pricing)):

| Tramo | Envíos a analizar / año | Precio 2026 |
|---|---|---|
| 1 | hasta 500 | **3.824 USD** |
| 2 | 501 – 3.000 | 5.463 USD |
| 3 | 3.001 – 5.000 | 8.196 USD |
| 4 | 5.001 – 10.000 | 13.659 USD |
| 5 | 10.001 – 20.000 | 21.855 USD |
| 6 | 20.001 – 35.000 | 32.782 USD |
| 7 | 35.001 – 50.000 | 43.709 USD |
| Enterprise | 50.001 – 65.000 | **54.636 USD** |

Sube un 3 % al año. Por encima de 65.000 envíos, precio a medida.

**Lo que esto significa para nosotros, dicho con números:** LiteraLevel está
remidiendo **61.642 libros** de Project Gutenberg. En el tramo Enterprise de
Lexile eso son **~54.600 USD/año**. Nuestro coste estimado es **entre tres y cinco horas de una
A100** (§8.3 del documento). Aunque se pague la A100 a precio de mercado, la
diferencia es de tres órdenes de magnitud. **Ese es el argumento económico, y es
el más sólido que tenemos.**

Hay también un analizador gratuito, pero da medidas «estimadas» explícitamente
no certificadas ([Lexile Hub FAQ](https://hub.lexile.com/faqs/)).

### 3.4 Qué NO hace Lexile

Esto es lo que abre el hueco:

1. **No mide capítulo a capítulo.** Da un número por obra. Un libro que empieza
   fácil y se complica en el capítulo 12 tiene una sola cifra Lexile.
2. **No mide prosa no continua** — y lo dice ella misma: no es fiable con
   «escritura de estudiantes, poesía, fichas de aula, obras de teatro, letras de
   canciones, recetas u otro texto que no sea prosa»
   ([Lexile Hub FAQ](https://hub.lexile.com/faqs/)). Exactamente la misma
   limitación que declara `scoring.continuous_prose`. Empate.
3. **No está anclado al MCER.** Es una escala estadounidense pensada para
   lectores nativos por curso escolar. La conversión Lexile→MCER no es oficial.
4. **No es para hispanohablantes.** Ni la interfaz, ni la búsqueda, ni el
   diccionario, ni el concepto.
5. **Es opaco y propietario.** No se puede auditar la fórmula ni reproducir el
   número. Nosotros publicamos la arquitectura, la escala y hasta los resultados
   negativos.
6. **La crítica académica lleva veinticinco años sobre la mesa.** El panel
   convocado por el NCES ya en 2001 señalaba «la adecuación de la longitud de
   oración como sustituto de la complejidad sintáctica» y «el efecto de la
   pragmática y de los rasgos del discurso» como problemas abiertos
   ([NCES 2001-08](https://nces.ed.gov/pubs2001/200108.pdf)). Siguen abiertos.

---

## 4. El estado del arte académico

### 4.1 Los corpus, y en cuál jugamos

| Corpus | Qué es | Tamaño | Acceso | ¿Lo usamos? |
|---|---|---|---|---|
| **CLEAR / CommonLit** | Etiqueta continua `BT_easiness` de comparaciones pareadas juzgadas por humanos ([Crossley et al. 2023](https://doi.org/10.3758/s13428-022-01802-x)) | 4.724 extractos | Abierto | **Sí, es el nuestro** |
| **OneStopEnglish** | El mismo artículo reescrito en 3 niveles ([Vajjala & Lučić 2018](https://doi.org/10.18653/v1/W18-0535)) | 567 textos | CC BY-SA | Sí, validación |
| **WeeBit** | Artículos BBC/Weekly Reader en 5 niveles de edad | ~3.000 | Bajo petición | No |
| **Newsela** | 1.130 noticias reescritas por editores profesionales en 4 niveles | ~5.000 textos | **Requiere firmar un NDA** ([Newsela](https://newsela.com/legal/data)) | No |
| **CEFR-SP** | 17k oraciones etiquetadas A1–C2 por profesionales de la enseñanza ([Arase et al., EMNLP 2022](https://aclanthology.org/2022.emnlp-main.416/)) | 17.000 oraciones | Abierto, [GitHub](https://github.com/yukiar/CEFR-SP) | **No, y debería** |
| **Ace-CEFR** | 890 pasajes conversacionales cortos, MCER, de Google ([arXiv 2506.14046](https://arxiv.org/html/2506.14046v1)) | 890 | Abierto | No |

### 4.2 Qué cifras se consideran buenas — la respuesta a «¿0,908 es bueno?»

Aquí está el listón, y hay que leerlo con cuidado porque **casi ninguna cifra
publicada es directamente comparable con la nuestra**.

**En CLEAR (regresión, correlación con juicio humano):**

| Método | Métrica | Valor | Fuente |
|---|---|---|---|
| Fórmula clásica | Pearson | 0,517 | [Grossman & Chen, ACL 2026](https://arxiv.org/abs/2604.24470) |
| RSRS (métrica basada en sorpresa) | Pearson | 0,484 | ídem |
| LLM zero-shot (mejor prompting publicado) | Pearson | 0,725 | ídem |
| LAURAE (LLM + fórmulas combinadas) | Pearson | 0,735 | ídem |
| **LiteraLevel, transformer afinado** | **Pearson** | **0,89** | `entrega/documento.md` §7.2 |
| Kaggle CommonLit Readability Prize, top-5 | RMSE | ~0,447 (privado) | [4.º puesto](https://github.com/Anjum48/commonlitreadabilityprize) — verifiqué 0,451 público / 0,447 privado del 4.º; **no verifiqué la cifra exacta del 1.º** |
| **LiteraLevel** | **RMSE** | **0,560** | `entrega/documento.md` §7.2 |
| GCN sobre distancia sintáctica POS | R² 0,9729 / RMSE 0,1668 | — | [Sci. Reports 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13049047/) — **cifra sospechosa: ver aviso abajo** |

> **Aviso sobre esa última fila.** Un RMSE de 0,1668 sobre `BT_easiness` sería
> 2,7 veces mejor que el ganador de una competición Kaggle con ensembles de
> `deberta-v3-large`. Cuando una publicación bate un leaderboard maduro por ese
> margen, lo primero que hay que sospechar es la partición: si los extractos del
> mismo libro caen a los dos lados, hay fuga. **No lo pude verificar. No lo uses
> como referencia sin comprobar cómo particionaron.** Nuestro proyecto sí evita
> esa fuga (`GroupShuffleSplit` por `Title`, T9 del Cuadro 6).

**En clasificación por niveles (los benchmarks clásicos están casi saturados):**

| Corpus | Mejor resultado publicado | Fuente |
|---|---|---|
| OneStopEnglish, 3 clases | F1 99,41 % | [Sci. Reports 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13049047/) — mismo aviso |
| OneStopEnglish, precisión pareada | 98,7 % | [Lee & Vajjala, Findings ACL 2022](https://aclanthology.org/2022.findings-acl.300/) |
| Newsela, precisión pareada | 99,6 % | ídem |
| WeeBit, F1 | 92,73 % | [Sci. Reports 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13049047/) |
| CEFR-SP, macro-F1 (oración, 6 niveles) | 84,5 % | [Arase et al. 2022](https://aclanthology.org/2022.emnlp-main.416/) |

**Veredicto sobre el 0,908.** Mi lectura, argumentada:

- **Como cifra de correlación ordinal sobre 6 niveles bien separados, 0,908 es
  buena pero no excepcional.** El rango publicado en tareas comparables
  (Cambridge, textos de examen) llega a Pearson 0,888 solo con *zero-shot*
  ([Grossman & Chen](https://arxiv.org/abs/2604.24470), tabla 3). Con n=144 y
  seis grupos separados por diseño, una correlación de rango alta es lo
  esperable, no lo sorprendente.
- **El 0,89 de Pearson en CLEAR sí es un resultado sólido y comparable**, porque
  CLEAR es público y hay contra qué medirlo. Ese es el número que hay que
  defender ante un evaluador, no el 0,908.
- **El número que de verdad debería preocupar es otro:** en British Council,
  contar palabras sin modelo da **0,807** y el modelo da **0,860** (Cuadro 12).
  El modelo aporta señal por encima de la longitud (parcial 0,668), pero el
  margen sobre la señal trivial es de 0,053. El proyecto ya lo publica, y eso es
  lo correcto. Pero es la cifra que un revisor exigente atacará primero.
- **Lo que sí es un resultado poco común y está infravalorado en el documento:
  el orden estricto de las medias por nivel en corpus externo**
  (0,504 · 0,556 · 0,928 · 1,241 · 1,495). Vajjala documenta que *los modelos de
  legibilidad no transfieren bien entre corpus* como uno de los problemas
  abiertos del campo ([LREC 2022](https://aclanthology.org/2022.lrec-1.574/)).
  Que un modelo entrenado con un ancla MCER conserve el orden en material de
  British Council que nunca vio es exactamente lo que la literatura dice que
  suele fallar. **Ese es el hallazgo, no el 0,908.**

### 4.3 Lo que el campo critica de sí mismo

[Vajjala, LREC 2022](https://aclanthology.org/2022.lrec-1.574/) — la referencia
que hay que citar en la defensa:

- Los modelos **no transfieren entre corpus**.
- Los números publicados **no son comparables entre sí**: cada estudio usa un
  corpus, una partición y una métrica distintos.
- Las particiones y las prácticas de evaluación no están estandarizadas.

Traducción para LiteraLevel: **cualquier tabla que compare nuestro 0,908 con un
número de un paper es engañosa por construcción**, y el documento hace bien en no
intentarlo. Lo que sí se puede afirmar es la comparación interna (Cuadro 7) y la
comparación en CLEAR, que es corpus compartido.

---

## 5. ¿Y los LLM? ¿Gana un GPT-5 con buen prompt?

Es la pregunta más importante del encargo, así que la respuesta va con las tres
evidencias que encontré, no con una opinión.

### 5.1 Evidencia 1 — En CLEAR, no gana

[Grossman & Chen, «Zero-shot Large Language Models for Automatic Readability
Assessment», ACL 2026](https://arxiv.org/abs/2604.24470). Diez LLM abiertos
(Llama 3.1/3.2, Gemma 2, Aya Expanse, Mixtral 8x7B, Phi-4) sobre 14 corpus, con
la metodología de prompting más cuidada publicada hasta la fecha.

| Corpus | Su mejor LLM zero-shot | Fórmulas | LiteraLevel afinado |
|---|---|---|---|
| CLEAR | 0,725 | 0,517 | **0,89** |
| OneStop | 0,488 | 0,577 | — |
| Cambridge (examen) | **0,888** | 0,702 | — |
| Media (14 corpus) | 0,595 | 0,599 | — |

Dos lecturas, ambas honestas:
- **A favor nuestro:** en CLEAR, que es nuestro corpus, un encoder de 82 M
  afinado (0,89) supera claramente al mejor LLM zero-shot (0,725).
- **En contra nuestra:** la media de los LLM sobre 14 corpus (0,595) es
  prácticamente igual a la de las fórmulas clásicas (0,599). Es decir: **un LLM
  con buen prompt, sin entrenar nada, iguala a Flesch en promedio y arrasa en
  algunos dominios.** En Cambridge —textos de examen, que es *nuestro* caso de
  uso— llega a 0,888 sin ver un solo ejemplo etiquetado.

### 5.2 Evidencia 2 — Google lo midió y el encoder ganó

[Ace-CEFR, Kogan et al., arXiv 2506.14046](https://arxiv.org/html/2506.14046v1),
890 pasajes conversacionales con nivel MCER:

| Sistema | MSE (menor es mejor) |
|---|---|
| **BERT afinado, 45,7 M parámetros** | **0,37** |
| PaLM 2-L, few-shot optimizado | 0,48 |
| Anotador humano experto | 0,75 |

Los autores concluyen que el BERT es «sustancialmente mejor» y que su latencia
sirve para tiempo real, mientras que el LLM «solo sirve para etiquetado
offline». Es la evidencia más directa que encontré, y valida la arquitectura de
LiteraLevel casi literalmente. **Nota adicional que vale su peso: el modelo bate
al humano experto.** Eso sitúa el techo de la tarea.

### 5.3 Evidencia 3 — Con niveles MCER, tampoco

Yancey et al. (2023) usaron GPT-4 few-shot para predecir MCER en redacciones de
aprendices; los QWK no superaron ni a un XGBoost de referencia ni a los
anotadores humanos. **[cita secundaria: lo encontré en revisiones, no abrí el
artículo original]**. En la misma línea, en *automated essay scoring* GPT-4
few-shot queda por debajo del baseline BERT incluso dándole rúbrica y ejemplos
([arXiv 2401.06431](https://arxiv.org/html/2401.06431v1)).

### 5.4 La evidencia en contra, que también hay que decir

[«Readability Reconsidered», arXiv 2510.15345](https://arxiv.org/html/2510.15345v1)
compara métricas *sin referencia* sobre 5 corpus con Kendall tau-b: **LLM como
juez, zero-shot, queda en rango medio 2,4 sobre todas las métricas evaluadas**,
5-shot en 3,2, y la mejor fórmula clásica («número de palabras difíciles») en
8,6. Las métricas basadas en modelo superan a las de superficie por hasta 0,24
absolutos.

Ojo con la comparación: ese trabajo enfrenta LLM contra *métricas sin
referencia*, no contra un transformer afinado con etiquetas. No contradice §5.1
ni §5.2, pero deja claro que **un LLM es hoy mejor que cualquier fórmula clásica
sin entrenar nada.**

### 5.5 Conclusión sobre los LLM

**Un LLM con buen prompt no mide mejor que nuestro distilroberta afinado en el
corpus donde tenemos evidencia (0,725 frente a 0,89 en CLEAR), y la literatura
independiente apunta en la misma dirección.** Pero hay tres matices que hay que
decir en voz alta:

1. **En dominio de examen (Cambridge) el LLM zero-shot llega a 0,888.** No
   tenemos evidencia de que le ganemos ahí. Es el experimento que falta.
2. **El LLM no necesita corpus.** Nuestro eslabón más débil son 654 documentos
   de anclaje. El suyo son cero.
3. **Y aun así el LLM pierde por otra razón, que es la que nos salva:
   la economía.** Puntuar 61.642 libros son ~2,7 millones de ventanas. A ese
   volumen, cualquier API de pago es un presupuesto y no un proyecto de módulo;
   nuestro modelo lo hace en entre tres y cinco horas de A100. Y la app tiene que correr en la
   CPU del equipo de un estudiante con 1,05 GB de RSS. **Un LLM no cabe ahí ni
   aunque midiera mejor.**

---

## 6. Productos existentes

| Producto | Qué hace | Cómo estima dificultad | Qué NO hace |
|---|---|---|---|
| **Lexile / Find a Book** | Escala común lector-texto, base de cientos de miles de títulos | 2 variables (frecuencia léxica + longitud de oración) | Capítulo a capítulo, MCER, español, gratis |
| **TeakReader** ([web](https://teakreader.com/english-reading-level-checker-for-books)) | Analiza EPUB, clásicos de Gutenberg y subtítulos; **da comprensión y distribución MCER por capítulo** | **Basado en vocabulario**: reparte las palabras del libro por nivel MCER y cruza con lo que el usuario marca como conocido | No usa modelo de lenguaje; no es sintáctico. Interfaz en inglés, sin soporte declarado a hispanohablantes. Precio no publicado en esa página |
| **LoreGlide** ([web](https://www.loreglide.com/use-cases/graded-readers)) | Importas un texto de Gutenberg, eliges nivel A2–C2 y te lo **adapta** | Adapta, no mide | No te dice si el libro original es para ti; te lo reescribe |
| **LingQ** | Biblioteca enorme de importación, audio, seguimiento de vocabulario | Conteo de palabras conocidas/desconocidas | No estima dificultad del libro antes de abrirlo; de pago |
| **Readlang** | Extensión de navegador: clic en palabra → traducción → flashcard | No estima dificultad | Nada de nivel de texto, nada de libro completo |
| **Beelinguapp** | Textos en paralelo con audio nativo | Niveles editoriales fijos | Catálogo cerrado y pequeño; no analiza tu libro |
| **Cathoven CEFR Checker** ([web](https://www.cathoven.com/cefr-checker/)) | Analiza un texto y colorea **cada palabra por nivel MCER**; 11 API REST de pago por llamada | Léxico + rasgos, orientado a MCER | Un texto por vez, no un libro; sin lector integrado |
| **Text Inspector** ([web](https://textinspector.com/cefr-level-checker/)) | Perfil léxico y *scorecard* MCER; añade grados D1/D2 por encima de C2 | Perfil léxico académico | El scorecard es solo para suscriptores; herramienta de analista, no de lector |
| **Wikipedia simple / lecturas graduadas de editorial** (Oxford, Penguin…) | Texto ya escrito al nivel | Anotación editorial humana | Catálogo cerrado, de pago, y no mide *tu* libro |

**El que más se nos parece es TeakReader**, y hay que reconocerlo: da nivel MCER
y comprensión **por capítulo**, sobre EPUB y sobre Gutenberg, en móvil, y avisa
explícitamente de que no es un test MCER oficial —el mismo escrúpulo que
nosotros—. La diferencia técnica real: **ellos cuentan vocabulario, nosotros
leemos el texto con atención.** Nuestra propia progresión (Cuadro 7) muestra que
las variables léxicas se quedan en 0,29 de exactitud y el texto crudo llega a
0,46. Ese es el argumento, y es medible.

---

## 7. Tabla comparativa: LiteraLevel frente a cada alternativa

| Alternativa | Dónde ganamos | Dónde perdemos |
|---|---|---|
| **Fórmulas clásicas** (Flesch, Dale-Chall, ATOS) | Leemos el texto con atención, no contamos sílabas. 0,89 vs 0,517 en CLEAR | Ellas son instantáneas, interpretables al 100 %, no necesitan 328 MB ni GPU, y llevan 70 años validadas en aula. ATOS además mide el libro entero desde 2000 |
| **Lexile** | Anclaje MCER; capítulo a capítulo; gratis frente a 3.824–54.636 USD/año; abierto y auditable; en español | Escala validada durante 30 años, base de cientos de miles de títulos, integración con bibliotecas y pruebas oficiales, **y una escala común lector-texto que nosotros solo aproximamos**. Su medida la acepta un colegio; la nuestra no |
| **LLM con prompt (GPT-5, Claude)** | 0,89 vs 0,725 en CLEAR; corre en CPU; coste ~0 por libro; determinista y reproducible | No necesitan corpus etiquetado (nosotros dependemos de 654 documentos); explican su juicio; llegan a 0,888 en dominio de examen sin entrenar; mejoran solos cada seis meses sin que hagamos nada |
| **TeakReader** | Modelo de lenguaje frente a conteo léxico; búsqueda semántica en español; app web sin instalar | Producto móvil terminado y publicado en dos tiendas; nosotros, una web en Hugging Face Spaces sobre CPU, con una cuenta Pro de 7 USD/mes. Su señal de vocabulario es **personalizada al usuario**, la nuestra no |
| **LingQ / Readlang / Beelinguapp** | Somos los únicos que dicen la dificultad **antes** de abrir el libro y **por capítulo** | Productos maduros, con años de contenido, audio, comunidad y sincronización entre dispositivos. Nuestro cuaderno y biblioteca son un prototipo al lado |
| **Cathoven / Text Inspector** | Libro completo frente a texto suelto; lector integrado; gratis | Herramientas de profesor pulidas, con API comercial, MCER por palabra y validación externa declarada |
| **Lecturas graduadas de editorial** | 61.642 libros de dominio público frente a un catálogo cerrado; literatura de verdad, no textos escritos para el ejercicio | Su nivel lo puso un humano que leyó la obra. El nuestro lo puso un modelo con una escala comprimida |

---

## 8. Dónde está nuestro valor real

Argumentado, no proclamado. Tres cosas, y solo tres:

### 8.1 Recorremos el libro entero, capítulo a capítulo

**Casi todo el mundo mide *un texto*. Nosotros medimos *un libro*, por dentro.**

- Lexile da un número por obra. Las fórmulas clásicas también (ATOS incluida,
  aunque lea el libro completo). Los LLM no pueden por coste. Cathoven y Text
  Inspector trabajan sobre un texto pegado en una caja.
- TeakReader sí da comprensión por capítulo, pero por conteo de vocabulario.
- La literatura académica lo confirma como hueco: *«la evaluación de
  legibilidad a nivel de libro se necesita mucho en aplicaciones educativas
  reales, pero la mayor parte de la investigación actual se centra en pasajes»*
  ([Going Beyond Passages, CCL 2024](https://aclanthology.org/2024.ccl-1.100.pdf)).

Y no es una capacidad declarada, está medida: 487 ventanas y 130.104 palabras de
*Notes from a Dead House* en 86 segundos, sin muestrear (§8.2).

### 8.2 Está pensado para un hispanohablante que quiere elegir *qué* leer

Esto es más raro todavía que lo anterior. Ninguna de las alternativas de la §6
resuelve la pregunta «no sé qué leer, descríbemelo tú». LiteraLevel sí:
**búsqueda semántica en español sobre embeddings multilingües**, acotada al
rango del perfil. El propio proyecto midió que cambiar el modelo multilingüe por
MiniLM ahorraría 2,4 s pero rompe la búsqueda, porque *el lector describe en
español y el catálogo está en inglés* (AGENTS.md). Esa frase es la propuesta de
valor entera.

Y la cadena no se corta en la recomendación: perfil → búsqueda en español →
libro abierto dentro de la app → curva por capítulo → doble clic en la palabra
con explicación **en español** → pronunciación corregida. **Nadie más cierra ese
circuito, y menos gratis.**

### 8.3 El precio y la auditabilidad

Ya está en §3.3: tres órdenes de magnitud contra Lexile, para el mismo volumen.
Y a diferencia de Lexile, nuestra escala, arquitectura, métricas **y resultados
negativos** están publicados. En un campo donde Vajjala señala la
incomparabilidad de los resultados como problema estructural, publicar los
experimentos rechazados es una ventaja real, no un adorno.

---

## 9. Qué nos gana la competencia hoy

Este apartado vale más que el anterior. Sin adornos:

1. **Lexile tiene una escala común lector-texto validada durante treinta años; nosotros tenemos una escala propia comprimida.**
   El documento lo admite: `predicho ≈ 0,72 × real + 0,38` (§7.5). Una medida
   Lexile la acepta un colegio para asignar lecturas. La nuestra dice
   explícitamente que no sirve para eso. Esa es la diferencia entre una medida y
   una orientación, y hoy tenemos lo segundo.

2. **El corpus de anclaje son 654 documentos. Es ridículamente pequeño y es el eslabón que rompe todo lo demás.**
   CEFR-SP publica 17.000 oraciones anotadas por profesionales y está en GitHub
   abierto. Ace-CEFR publica 890 pasajes. Newsela tiene 5.000 textos con NDA.
   Nosotros no usamos ninguno. **Ese es el fallo más grave del proyecto y no
   requiere ninguna idea nueva para arreglarlo, solo trabajo.**

3. **Un LLM zero-shot llega a 0,888 en textos de examen sin entrenar nada.**
   No hemos medido a nuestro modelo contra un LLM en nuestro propio corpus.
   Mientras no lo hagamos, no podemos afirmar que ganamos: solo que ganamos en
   CLEAR. Y el LLM mejora solo cada seis meses; nuestro modelo es final por
   decreto.

4. **En British Council, contar palabras da 0,807 y nosotros 0,860.**
   El proyecto lo publica y hace bien. Pero un revisor que solo lea esa tabla
   concluirá que 328 MB de transformer compran 0,053 de Spearman. La defensa
   —la correlación parcial de 0,668— es correcta pero requiere explicar qué es
   una correlación parcial, y eso ya es terreno perdido.

5. **Las etiquetas de nuestro catálogo son peores que las de cualquier competidor.**
   1.197 libros con `nivel_cefr` producido por el modelo v1 sobre las primeras
   ~190 palabras, con cortes por cuantiles: 60,4 % en A1, y solo 121 libros en
   el tramo B1–B2 donde está la mayoría de los lectores. TeakReader analiza el
   EPUB completo del usuario. Lexile tiene anotación validada. **Hoy nuestro
   catálogo es lo más flojo del producto, no el modelo.**

6. **Ellos están en las tiendas y nosotros en una web de 7 USD al mes.**
   TeakReader está en App Store y Google Play. LingQ y Readlang llevan años.
   Nosotros ya estamos desplegados —Hugging Face Spaces, público, dirección
   fija, 7 USD/mes— pero sobre CPU y **sin disco persistente**: el servicio se
   suspende por inactividad, el primer visitante después paga un arranque en
   frío, y lo que el lector guarda no sobrevive a un reinicio del contenedor.
   Se puede abrir; todavía no se puede confiar en que recuerde nada.

7. **No medimos poesía, teatro, ni diálogo fragmentado; ni nada que no sea inglés.**
   Lexile tampoco, pero Lexile no promete acompañar a un lector por un libro
   entero. Nuestra promesa es más ambiciosa y por eso el hueco se nota más:
   *Alice* tiene 73 % de diálogo y buena parte de la literatura que un lector
   quiere leer no es prosa continua limpia.

8. **La prueba de usuario tiene n=1.**
   Es honesto y está bien documentado, pero cualquier competidor comercial tiene
   telemetría de miles de lectores.

---

## 10. Números de referencia, para tenerlos a mano

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Qué da una fórmula clásica en CLEAR? | Pearson 0,517 | [ACL 2026](https://arxiv.org/abs/2604.24470) |
| ¿Qué da un LLM zero-shot en CLEAR? | Pearson 0,725 | ídem |
| ¿Qué damos nosotros en CLEAR? | Pearson 0,89 / RMSE 0,560 | `documento.md` §7.2 |
| ¿Qué da el mejor Kaggle en CLEAR? | RMSE ~0,447 (con ensembles grandes) | [4.º puesto](https://github.com/Anjum48/commonlitreadabilityprize) |
| ¿Qué da un LLM zero-shot en textos de examen? | Pearson 0,888 (Cambridge) | [ACL 2026](https://arxiv.org/abs/2604.24470) |
| ¿Un encoder pequeño afinado gana a un LLM? | Sí: MSE 0,37 vs 0,48 (y humano experto 0,75) | [Ace-CEFR](https://arxiv.org/html/2506.14046v1) |
| ¿Cuánto es «bueno» en MCER a nivel de oración? | macro-F1 84,5 % sobre 6 niveles | [Arase et al. 2022](https://aclanthology.org/2022.emnlp-main.416/) |
| ¿Están saturados los benchmarks de 3 clases? | Sí: 98,7–99,4 % en OneStopEnglish | [Lee & Vajjala 2022](https://aclanthology.org/2022.findings-acl.300/) |
| ¿Cuánto cuesta medir 61.642 libros con Lexile? | ~54.636 USD/año (tramo Enterprise) | [MetaMetrics](https://www2.metametricsinc.com/content-creator-annual-pricing) |
| ¿Cuánto nos cuesta a nosotros? | entre 3 y 5 horas de A100 | `documento.md` §8.3 |

---

## Fuentes

- Crossley, S. et al. (2023). *A large-scaled corpus for assessing text readability.* Behavior Research Methods. https://doi.org/10.3758/s13428-022-01802-x
- Grossman, R. & Chen, Y. (2026). *Zero-shot Large Language Models for Automatic Readability Assessment.* ACL 2026. https://arxiv.org/abs/2604.24470
- Kogan, D. et al. (2026). *Ace-CEFR — A Dataset for Automated Evaluation of the Linguistic Difficulty of Conversational Texts for LLM Applications.* https://arxiv.org/html/2506.14046v1
- Lee, J. & Vajjala, S. (2022). *A Neural Pairwise Ranking Model for Readability Assessment.* Findings of ACL 2022. https://aclanthology.org/2022.findings-acl.300/
- Arase, Y. et al. (2022). *CEFR-Based Sentence Difficulty Annotation and Assessment.* EMNLP 2022. https://aclanthology.org/2022.emnlp-main.416/
- Vajjala, S. (2022). *Trends, Limitations and Open Challenges in Automatic Readability Assessment Research.* LREC 2022. https://aclanthology.org/2022.lrec-1.574/
- Vajjala, S. & Lučić, I. (2018). *OneStopEnglish corpus.* https://doi.org/10.18653/v1/W18-0535
- *Going Beyond Passages: Readability Assessment for Book-level Long Texts.* CCL 2024. https://aclanthology.org/2024.ccl-1.100.pdf
- *Readability Reconsidered: A Cross-Dataset Analysis of Reference-Free Metrics.* https://arxiv.org/html/2510.15345v1
- MetaMetrics. *The Lexile Framework as an Approach for Reading Measurement.* https://metametricsinc.com/wp-content/uploads/2017/07/The-Lexile-Framework-for-Reading.pdf
- MetaMetrics. *Lexile Text Analyzer Content Creator Annual Pricing.* https://www2.metametricsinc.com/content-creator-annual-pricing
- Lexile Hub. *FAQs.* https://hub.lexile.com/faqs/
- NCES (2001). *Assessing the Lexile Framework: Results of a Panel Meeting.* https://nces.ed.gov/pubs2001/200108.pdf
- *The ATOS Readability Formula for Books and How It Compares to Other Formulas.* ERIC ED449468. https://files.eric.ed.gov/fulltext/ED449468.pdf
- Effortmark. *Readability formulas: seven reasons to avoid them.* https://www.effortmark.co.uk/readability-formulas-seven-reasons-to-avoid-them-and-what-to-do-instead/
- Newsela. *Request access to the Newsela Corpus.* https://newsela.com/legal/data
- TeakReader. https://teakreader.com/english-reading-level-checker-for-books
- Cathoven. *CEFR Checker.* https://www.cathoven.com/cefr-checker/
- Text Inspector. *CEFR Level Checker.* https://textinspector.com/cefr-level-checker/
