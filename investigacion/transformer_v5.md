# Diseño de un v5 que le gane al v4

**Encargo 2.** *«Ya tenemos la regresión, interpretable, me gusta. Ahora,
¿tenemos modelos más potentes que le puedan ganar?»*

No entreno nada aquí. Esto es la propuesta y su justificación.

> **Qué está medido y qué no.** Las mediciones marcadas **[medido aquí]** las
> hice yo sobre este equipo y los EPUB de `~/.literalevel/libros`, con un script
> de solo lectura que no tocó el repositorio. Las cifras de VRAM y de velocidad
> de modelos que no he ejecutado están marcadas **[estimado]** y explican de
> dónde sale la aritmética. Todo dato externo lleva enlace.

---

## Resumen: la conclusión antes del razonamiento

1. **El v4 no pierde principalmente por capacidad.** Pierde por tres cosas más
   baratas de arreglar: **el truncado tira entre el 7 % y el 14 % de cada
   ventana** [medido aquí], **la escala está descalibrada de una forma que hace
   que el ancla MCER mienta en los extremos** (reconstruí su recta desde el
   Cuadro 10 y la confirmé), y **el corpus de anclaje son 654 documentos**.
2. **La pérdida es el error de diseño más importante y nadie lo ha tocado.** El
   problema es ordinal y se está optimizando MSE. Hay pérdidas ordinales con
   garantías (CORN) y hay evidencia publicada de que el planteamiento por pares
   funciona muy bien en esta tarea concreta (99,6 % de precisión pareada en
   Newsela).
3. **Lo primero que probaría no es un modelo más grande.** Es recalibrar (cero
   entrenamiento, horas) y luego un único reentrenamiento que arregle el
   truncado y cambie la pérdida, sobre el mismo `distilroberta`. Una A100 hora y
   media. Si eso no mueve la aguja, entonces sí: `deberta-v3-base`.

---

## 1. ¿Por dónde pierde el modelo actual?

### 1.1 El truncado: el 7–14 % de cada ventana se tira a la basura [medido aquí]

`app/scoring.py` fija `BLOCK_WORDS = 250` y `MAX_LENGTH = 256`. El proyecto ya
había medido que el 100 % de las ventanas supera los 256 tokens. Lo que nadie
midió es **cuánto se pierde**. Lo medí con el tokenizador real de `modelo_v4/`
sobre tres libros completos:

| Libro | Ventanas | Tokens por ventana (media) | mín–máx | Palabras que sobreviven a 256 tokens | **Descartado** |
|---|---|---|---|---|---|
| *Pride and Prejudice* | 400 | 273,1 | 254–346 | 233,3 de 250 | **6,7 %** |
| *Alice in Wonderland* | 118 | 284,4 | 252–336 | 225,1 de 250 | **10,0 %** |
| *Crime and Punishment* | 400 | 298,8 | 262–363 | 216,3 de 250 | **13,5 %** |

Tres consecuencias:

1. **El modelo nunca ve el final de ninguna ventana.** Y el final de una ventana
   de 250 palabras suele contener una o dos oraciones completas. Se está tirando
   señal sintáctica, que es justo lo que un transformer aporta sobre un contador
   de sílabas.
2. **`config.json` dice `max_position_embeddings: 514`.** Es decir: **la mitad
   del presupuesto posicional del modelo está sin usar.** No hay ninguna razón
   arquitectónica para el 256; es una constante heredada.
3. **El porcentaje descartado varía por texto**, del 6,7 % al 13,5 %. Un texto
   con vocabulario menos frecuente se fragmenta en más subpalabras y por tanto
   pierde más. Eso significa que **la cantidad de información que ve el modelo
   depende del propio texto**, y no de forma neutral.

**Lo que probé y no puedo afirmar.** Puntué 140 ventanas con el v4 real y
correlacioné tokens-por-ventana con la puntuación interna: Spearman **−0,265**
(p = 0,0015) en agregado, o sea que las ventanas más truncadas puntúan *más
fáciles*. Pero al mirar dentro de cada libro el efecto se desvanece (+0,166 /
+0,034 / +0,101 / −0,467; solo el último es significativo). **Es un efecto entre
libros, no dentro de libros: paradoja de Simpson.** Con 140 ventanas y 4 obras
no puedo establecer que el truncado sesgue la puntuación. Lo dejo como hipótesis
comprobable, no como hallazgo.

### 1.2 La compresión de escala: reconstruida y confirmada

El documento reporta `predicho ≈ 0,72 × real + 0,38` sin decir cómo se obtuvo.
La reconstruí ajustando por mínimos cuadrados las medias del Cuadro 10,
ponderadas por su *n* (3, 7, 12, 11, 12):

> **predicho_público ≈ 0,714 × real_público + 0,359** (R² = 0,96)

Coincide con la recta publicada. **La cifra del documento es correcta y ahora es
verificable**, cosa que antes no era.

Y de ahí sale el diagnóstico concreto, aplicando `anchor_cefr()` a la predicción
media de cada nivel real:

| Nivel real | Interno predicho | Ancla que devuelve la app | ¿Correcta? |
|---|---|---|---|
| A1 (0,0) | 0,90 | **A2** | ✗ un nivel de más |
| A2 (1,0) | 1,61 | **B1** | ✗ un nivel de más |
| B1 (2,0) | 2,33 | B1 | ✓ |
| B2 (3,0) | 3,04 | B2 | ✓ |
| C1 (4,0) | 3,75 | C1 | ✓ |
| C2 (5,0) | 4,47 | **C1** | ✗ **C2 es inalcanzable** |

**Tres defectos concretos, derivados de la propia tabla del proyecto:**
un texto A1 se anuncia como A2, un A2 como B1, y **el ancla C2 no puede salir
nunca** en el caso medio.

**Y hay un cuarto, que es el que más afecta al lector: las bandas están mal
puestas.** Con esa recta, los umbrales actuales (0,8 y 1,6) reparten los niveles
reales así:

| Banda | Umbral actual | Niveles MCER reales que caen dentro |
|---|---|---|
| básico | < 0,8 | A1, A2 |
| intermedio | 0,8 – 1,6 | **B1, B2, C1** |
| avanzado | ≥ 1,6 | **solo C2** |

Cuatro de los seis niveles se llaman «intermedio» y «avanzado» prácticamente no
se usa. Si se quiere un reparto 2/2/2, el umbral superior debería estar en
**1,36**, no en 1,6 — es una línea de código en `public_band()` y cero
entrenamiento.

**Caveat obligatorio antes de tocarlo.** Esa recta se ajustó sobre **textos
cortos de examen A1–C1**. Los libros del catálogo están fuera de ese rango: en
mi medición, *Pride and Prejudice* puntúa 1,84 y *Alice* 1,50 [medido aquí],
ambos por encima de la media C1 del corpus (1,495). **Aplicar la calibración
inversa a una novela victoriana es extrapolar.** Antes de mover el umbral hay
que comprobar qué le hace al reparto de los 1.197 libros del catálogo, no solo
al corpus de examen.

### 1.3 El corpus: 654 documentos, y ese es el techo real

510 de entrenamiento y 144 de validación. Es el eslabón que el propio documento
llama «el más delgado» (limitación 9), y estoy de acuerdo. Referencias abiertas
que **no se están usando**:

- **CEFR-SP**: 17.000 oraciones anotadas A1–C2 por profesionales de la enseñanza
  del inglés, abierto en [GitHub](https://github.com/yukiar/CEFR-SP)
  ([Arase et al., EMNLP 2022](https://aclanthology.org/2022.emnlp-main.416/)).
  Es granularidad de oración, no de documento — sirve para preentrenar la cabeza
  o como tarea auxiliar, no como sustituto.
- **OneStopEnglish**, ya en casa: 189 artículos × 3 niveles. Eso son
  **567 pares ordenados con contenido idéntico**. Para una pérdida por pares es
  material perfecto: el confusor de tema está controlado por construcción.
- **CLEAR**, 4.724 extractos, ya usado en v1/v2.
- **Ace-CEFR**, 890 pasajes MCER abiertos
  ([arXiv 2506.14046](https://arxiv.org/html/2506.14046v1)).

### 1.4 Diagnóstico: ¿capacidad, contexto, corpus, pérdida o agregación?

Mi respuesta, ordenada por cuánto pesa:

| Sospechoso | ¿Culpable? | Argumento |
|---|---|---|
| **Pérdida** | **Sí, el principal** | Se optimiza MSE para un objetivo declarado ordinal (§2.1 del documento). MSE optimiza la media condicional, y la media condicional bajo ruido de etiqueta **encoge hacia el centro**: eso *es* la compresión de escala. No es un accidente, es lo que MSE hace |
| **Corpus** | **Sí, casi empatado** | 654 documentos. Con ese *n*, cualquier modelo grande se sobreajusta antes de aprovechar su capacidad. Y ya se vio: el mejor punto de control fue la época 3 de 6 |
| **Longitud de contexto** | **Sí, pero por truncado, no por contexto corto** | No hace falta leer 4.096 tokens. Hace falta leer los 256 que ya se tiran. Longformer resuelve un problema que no tenemos |
| **Agregación** | Parcialmente | Ver §4. Promediar es defendible para «dificultad media» y malo para «¿puedo con este libro?» |
| **Capacidad** | **El menos culpable** | El Cuadro 7 del documento ya demostró que subir potencia sobre la misma representación no sirve (XGBoost 0,28 vs logística 0,29). Y `distilroberta` no está saturado: está sobreajustando a los 3 epochs |

---

## 2. Candidatos concretos

Ninguna cifra de VRAM de esta tabla la he medido. Salen de la aritmética
estándar de entrenamiento con AdamW y precisión mixta (≈16 bytes por parámetro
entre pesos maestros, gradientes y los dos momentos, más activaciones), a
`seq_len` 512 y lote 16. **Verificar antes de reservar la máquina.** [estimado]

| Modelo | Parámetros | Contexto | VRAM entrenamiento | ¿A100 40 GB? | Coste en CPU vs v4 | Qué esperaría |
|---|---|---|---|---|---|---|
| **`distilroberta-base` (v4)** | 82 M, 6 capas, h=768 | 514 | ~3–4 GB | Sobra | 1× (**8,7 vent./s medido**) | Referencia |
| **`distilroberta` + `MAX_LENGTH=512`** | 82 M | 512 usados | ~5–7 GB | Sobra | **~2,2×** (~4 vent./s) | Recupera el 7–14 % perdido. **La mejor relación ganancia/coste de la lista** |
| **`distilroberta` + ventana de 190 palabras** | 82 M | 256, **sin truncar** | ~3–4 GB | Sobra | **1×, sin coste** | Misma idea, coste cero: ajustar la ventana al presupuesto en vez de al revés |
| **`roberta-base`** | 125 M, 12 capas | 514 | ~5–6 GB | Sobra | ~2× | Poco. El documento ya lo descartó por tamaño y la evidencia le da la razón |
| **`deberta-v3-base`** | **184 M** (86 M backbone + 98 M de embeddings, vocab 128 k) | 512, posiciones relativas | ~9–12 GB | Sobra | ~2,5–3,5× | **El mejor salto arquitectónico real.** SQuAD 2.0 F1 88,4 vs 83,7 de RoBERTa-base ([HF](https://huggingface.co/microsoft/deberta-v3-base)). Y con 654 documentos lo que importa es la eficiencia muestral, donde DeBERTaV3 sigue liderando ([arXiv 2504.08716](https://arxiv.org/abs/2504.08716)) |
| **`ModernBERT-base`** | 149 M | **8.192** | ~6–8 GB | Sobra | ~2× | Rápido y de contexto largo. Pero [arXiv 2504.08716](https://arxiv.org/abs/2504.08716) demuestra en experimento controlado que su ventaja sobre DeBERTaV3 **venía de los datos, no de la arquitectura**, y que DeBERTaV3 gana en eficiencia muestral. Con 510 documentos de entrenamiento, eso decide |
| **`longformer-base-4096`** | 149 M | 4.096 | ~14–20 GB (menos con *gradient checkpointing*, [5× según allenai](https://github.com/allenai/longformer)) | Sí | ~4–8× | **No lo haría.** Resuelve el problema equivocado: la señal de legibilidad es local (léxico y sintaxis), no discursiva a 4.000 tokens. Y es un modelo de 2020 inicializado desde `roberta-base` |
| **`roberta-large`** | 355 M, 24 capas, h=1024 | 514 | ~18–24 GB | Sí, justo | **~7×** (~1,2 vent./s) | Techo más alto, pero afinar un *large* con 510 documentos es el caso clásico de entrenamientos degenerados. Necesitaría 5 semillas y calentamiento largo solo para no fallar |
| **`deberta-v3-large`** | 434 M | 512 | ~28–36 GB | Sí, con acumulación de gradiente | ~8–10× | El techo. Y el riesgo. Solo después de 1–4 |
| **LLM 8 B + QLoRA (r=16, 4 bits)** | 8 B, ~40 M entrenables | 8 k+ | ~14–20 GB | Sí | **Imposible en CPU** | La evidencia dice que **iguala pero no bate** a un encoder afinado, con «una ventaja decisiva de rendimiento» para los encoders ([arXiv 2512.12677](https://arxiv.org/html/2512.12677v1)). Y no cabe en el presupuesto de despliegue |

### 2.1 La restricción que decide de verdad, y que no es la exactitud

El despliegue vive con **1,05 GB de RSS medidos, pico realista 1,2–1,5 GB, sin
GPU**, y ya descarta todos los planes gratuitos de 512 MB (`DESPLIEGUE.md`). El
«vistazo» son ~60 ventanas: a 8,7 vent./s son 7 s. Con `deberta-v3-base` a 512
tokens serían ~6× más, o sea **~42 s de espera para un vistazo**. Eso mata la
demo.

**Por eso el orden de la §6 no está ordenado por exactitud.** Un v5 que mida
0,03 mejor y convierta la app en inusable es un v5 peor. Las dos salidas son:
(a) precalcular el catálogo entero en GPU —que ya está en marcha— y dejar en
tiempo real solo el texto que sube el usuario; o (b) elegir palancas que no
cuesten inferencia, que es justo lo que hacen la calibración y la ventana de 190
palabras.

**Y el precálculo también tiene precio.** Hoy son entre tres y cinco horas de A100 para 61.642
libros. Con un modelo 6× más caro son ~38 h. Colab Pro+ da 500 unidades de
cómputo al mes por 49,99 USD, con extras a 9,99 USD por 100
([Colab](https://colab.research.google.com/signup)). No verifiqué cuántas
unidades por hora consume una A100: **compruébalo antes de comprometer el
experimento**, porque puede ser el mes entero.

---

## 3. La pérdida: lo importante, y lo que nadie ha tocado

### 3.1 Por qué MSE es la elección equivocada

El documento lo dice en §2.1: *«el objetivo es ordinal, no de clasificación
exacta»*, y la métrica principal es Spearman. Pero se entrena con MSE sobre una
etiqueta 0–5. Tres problemas:

1. **MSE encoge.** Estima E[y|x]. Con ruido en la etiqueta, esa esperanza está
   más cerca de la media global que la etiqueta verdadera. **La compresión
   `0,714x + 0,359` no es un defecto del modelo: es el comportamiento correcto
   de MSE bajo ruido de etiqueta.** Cambiar de modelo no la arreglará.
2. **MSE no es el sustituto de Spearman.** Optimiza distancias absolutas, no el
   orden. Se está entrenando una cosa y evaluando otra.
3. **MSE trata la etiqueta como métrica.** La distancia A1→A2 y la distancia
   C1→C2 son ambas «1», pero no son el mismo salto pedagógico.

### 3.2 Lo que propongo: CORN + un término por pares

**Cabeza CORN** ([Shi, Cao & Raschka, *Pattern Analysis and Applications*
2023](https://link.springer.com/article/10.1007/s10044-023-01181-9), código en
[coral-pytorch](https://github.com/Raschka-research-group/coral-pytorch)):
K−1 = 5 salidas binarias condicionales que estiman P(y > k). La predicción es
**ŷ = Σₖ P(y > k)**, que sigue siendo un número continuo — o sea que **no se
pierde la interpretabilidad que a Miguel le gusta**, y la escala 0–5 y el
`public_score(y) = clip(y,0,5)*0.4` siguen valiendo tal cual.

**CORN y no CORAL**: CORAL impone pesos compartidos entre los umbrales, y los
propios autores documentan que quitar esa restricción «mejora sustancialmente»
el rendimiento. CORN garantiza igualmente la consistencia de rango (nunca dirá
P(y>3) > P(y>2)), que es exactamente la propiedad que una escala ordinal
necesita.

**Más un término por pares.** El planteamiento pareado tiene la mejor evidencia
publicada en *esta* tarea concreta: una red siamesa con *margin ranking loss*
alcanza **99,6 % de precisión pareada en Newsela y 98,7 % en OneStopEnglish**
([Lee & Vajjala, Findings ACL 2022](https://aclanthology.org/2022.findings-acl.300/)),
y transfiere a francés y español a más del 80 % sin ver un ejemplo. Y para
LiteraLevel los pares son **gratis**: los 189 artículos de OneStopEnglish dan
567 pares ordenados con el contenido controlado.

**La pérdida completa:**

```
L = L_CORN(ŷ, y)  +  λ · L_rank(margin, pares del mismo artículo)
```

con λ ajustado en validación, arrancando por λ = 0,3. La combinación soft-labels
ordinales + preentrenamiento por pares ya se ha publicado para legibilidad
([Zeng et al., Findings EMNLP 2022](https://aclanthology.org/2022.findings-emnlp.334/)),
aunque **no pude extraer sus cifras del PDF y no las cito**.

**Honestidad obligatoria:** no encontré ningún trabajo publicado que compare
CORN contra MSE *específicamente en legibilidad*. Mi argumento es teórico (MSE
encoge, CORN no optimiza la media condicional) más analogía con el trabajo de
Zeng et al. **Es una hipótesis fundamentada, no un resultado esperado con
número.**

### 3.3 Cómo arreglar la compresión: las tres opciones, con veredicto

| Opción | Qué hace | Veredicto |
|---|---|---|
| **Recalibración lineal inversa** (2 parámetros) | `real ≈ (pred − 0,359)/0,714` ajustado sobre un *fold* de entrenamiento | **La que haría.** Con n=144 en validación, dos parámetros es lo único que no se sobreajusta. Extrapola fuera del rango observado, que es lo que hace falta para libros. Es lo que el documento ya propone como trabajo futuro (§10.4) |
| **Regresión isotónica** | Transformación monótona libre | **No, todavía no.** Con 144 puntos y solo 6 valores distintos de etiqueta, la isotónica degenera en «devolver la media de cada grupo»: sobreajusta en los extremos y **no puede extrapolar**, así que ningún libro puntuaría por encima de la media C1 del corpus. Vuélvase a considerar con ≥1.000 documentos etiquetados |
| **Cambiar la pérdida (CORN)** | Elimina la causa en vez del síntoma | **Sí, pero no basta.** CORN reduce el encogimiento, no lo anula: las probabilidades siguen estando calibradas a la distribución condicional. Se necesita calibración *además* |
| **Mover los umbrales de banda** | 1,6 → 1,36 en `public_band()` | **Sí, y es de hoy.** Cero entrenamiento. Pero validar antes contra el catálogo (§1.2) |

### 3.4 La trampa que hay que decir en voz alta

**Ninguna calibración monótona cambia el Spearman.** Es invariante a
transformaciones monótonas: recalibrar dará exactamente 0,908 otra vez. Si el
protocolo evalúa la calibración con Spearman, concluirá «no sirve de nada» y se
tirará la mejora más valiosa del proyecto.

**La calibración se evalúa con: MAE en niveles, exactitud exacta, exactitud
±1 nivel, y la pendiente de la recta predicho-vs-real (objetivo: 1,00).** Nunca
con Spearman.

---

## 4. Agregación de ventanas

Hoy: `interno = mean(por_bloque)` sobre hasta 8 bloques en `puntuar()`, y sobre
todas las ventanas en `perfil_de_texto()`.

### 4.1 Lo que está bien y no hay que tocar

El muestreo de 8 bloques ya está validado: 1,784 frente a 1,743 del recorrido
completo, una desviación de 0,041 sobre 0–2 (T7 del Cuadro 5). **El atajo no es
el problema.** El problema es qué estadístico se calcula.

### 4.2 Por qué la media es el estadístico equivocado para un libro

Un lector no abandona un libro por su dificultad media. Lo abandona en el
capítulo que no puede con él. La media diluye exactamente la señal que decide si
termina el libro: un libro con 90 % de capítulos B1 y 10 % de capítulos C1
promedia B1 y se abandona en el capítulo 12.

Además, promediar *reduce la varianza* de la estimación del documento, lo que
**suma a la compresión de escala** de §1.2: los libros difíciles se vuelven
menos difíciles y los fáciles menos fáciles al promediar.

### 4.3 Qué proponer

Calcular las cinco y elegir con datos, no con opinión:

| Estadístico | Qué responde | Coste |
|---|---|---|
| media (actual) | «¿de qué dificultad es este libro en promedio?» | 0 |
| media podada al 10 % | lo mismo, robusto a un capítulo raro (una dedicatoria, un apéndice) | 0 |
| **percentil 75** | **«¿con qué me voy a encontrar en un cuarto del libro?»** | 0 |
| percentil 90 | «¿cuál es el pico que me va a frenar?» | 0 |
| *attention pooling* sobre las ventanas | aprendido | **Necesita etiquetas a nivel de documento; con 654 se sobreajusta.** No lo haría todavía |

Es literalmente el problema que estudia
[*Going Beyond Passages: Readability Assessment for Book-level Long Texts*
(CCL 2024)](https://aclanthology.org/2024.ccl-1.100.pdf), que compara media,
máximo, percentiles y atención. **No conseguí extraer sus cifras del PDF (viene
comprimido y el texto no es recuperable con las herramientas que tengo). Hay que
leerlo antes de decidir.**

### 4.4 El problema honesto: no hay verdad a nivel de libro

No existe corpus de libros completos con nivel MCER anotado. **Así que la
elección de agregador no se puede validar del modo en que se validó el modelo.**
Lo que sí se puede hacer, y es gratis:

- **En OneStopEnglish**, agregar las ventanas de cada artículo y exigir que el
  orden de los tres niveles **dentro del mismo artículo** se conserve. El
  contenido es idéntico, así que es la prueba más limpia que hay. Gana el
  agregador que preserve el orden en más de los 189 tríos.
- **En British Council**, la misma métrica que ya se usa (Spearman con el nivel
  oficial), agregador por agregador.

**Mi apuesta, y la digo como apuesta:** la media podada ganará a la media por
poco, el p75 ganará en British Council y perderá en OneStopEnglish (donde los
textos son homogéneos y el pico no aporta). Si es así, la respuesta de producto
no es elegir uno, sino **mostrar dos números: «dificultad media» y «los pasajes
más duros»**, que es información que ningún competidor da.

---

## 5. Protocolo experimental honesto

Escrito para poder decir «el nuevo gana» sin engañarse.

### 5.1 Reglas fijadas antes de correr nada

1. **Partición idéntica.** `GroupShuffleSplit` por `Title`, semilla 42, la misma
   del v4 (T9, Cuadro 6). **Nunca se vuelve a particionar.** Reparticionar y
   quedarse con la partición favorable es la forma más común de engañarse.
2. **El conjunto ciego de 144 documentos se toca una vez, al final.** Todo el
   desarrollo va contra un *fold* de validación sacado del entrenamiento.
3. **British Council se sigue reportando por separado y con el filtro de prosa
   fijado a priori.** El documento ya advierte (limitación 6) que ese conjunto
   «ya ha sido mirado». Sigue sirviendo, pero como corroboración, no como juez.
4. **Ningún hiperparámetro se elige mirando el test.**

### 5.2 Qué métrica decide

**Métrica primaria:** Spearman en el conjunto ciego de 144.

**Y tres métricas de guardia que pueden vetar un ganador:**

| Métrica | Umbral | Por qué veta |
|---|---|---|
| Correlación parcial descontando longitud (Cuadro 12) | no puede bajar de 0,665 | Un modelo que sube Spearman bajando la parcial **no ha aprendido dificultad: ha aprendido a contar palabras mejor**. Eso es peor, no mejor |
| Pendiente predicho-vs-real tras calibrar | ≥ 0,90 | Sin esto, se cambia un modelo comprimido por otro comprimido |
| Latencia del vistazo en la CPU de referencia | ≤ 20 s | Un v5 que rompe la demo no es un v5 |

Se reportan siempre las cuatro. Y además MAE en niveles y exactitud ±1, que son
las que el lector nota.

### 5.3 Semillas y qué diferencia es real

- **5 semillas mínimo**, no 3. Se reporta media ± desviación típica de las cinco,
  no la mejor. Publicar la mejor de cinco semillas es una forma de mentir.
- **Cuánto ruido hay.** El error típico de un Spearman de 0,908 con n = 144 es
  aproximadamente (1 − ρ²)/√(n−1) = (1 − 0,824)/11,96 ≈ **0,015**. Para comparar
  dos correlaciones *independientes*, el error de la diferencia es √2 veces eso,
  ≈ 0,021, con un intervalo del 95 % de ancho ≈ ±0,041.

  **Regla práctica: sobre 144 documentos, una diferencia de Spearman menor que
  ~0,04 medida de forma ingenua es indistinguible del ruido.** Es decir: pasar
  de 0,908 a 0,93 **no es un resultado** si se mide así.

- **Cómo resolver diferencias más pequeñas: bootstrap pareado.** Los dos modelos
  se evalúan sobre los mismos 144 documentos, así que sus errores están
  correlacionados y el contraste pareado es mucho más sensible. Procedimiento:
  10.000 remuestreos con reemplazo de los 144 documentos; en cada uno se calcula
  Spearman de ambos modelos y su diferencia; **se exige que el v5 gane en ≥ 95 %
  de los remuestreos.** Con eso se resuelven diferencias del orden de 0,015.
  Alternativa cerrada: el test de Steiger para correlaciones dependientes.

### 5.4 La regla de decisión, escrita antes del experimento

> **El v5 sustituye al v4 si y solo si se cumplen las cuatro:**
> (a) tasa de victoria en el bootstrap pareado ≥ 95 % en Spearman;
> (b) la correlación parcial descontando longitud no baja;
> (c) la pendiente de calibración es ≥ 0,90;
> (d) el vistazo sigue por debajo de 20 s en la CPU de referencia.
>
> **Si (a) se cumple pero (b) no, el v5 se descarta.** Si ninguna se cumple, se
> publica el resultado negativo, que es lo que este proyecto lleva haciendo bien
> desde el principio (Cuadro 12).

### 5.5 Un contraste externo que falta y es barato

Nadie ha medido **al v4 contra un LLM sobre el corpus propio**. Es un experimento
de una tarde y responde a la pregunta que va a hacer el evaluador. Referencia
publicada: un LLM zero-shot llega a Pearson **0,888** en textos de examen tipo
Cambridge ([Grossman & Chen, ACL 2026](https://arxiv.org/abs/2604.24470)).
Hasta que se mida, no se puede afirmar que el v4 gana ahí.

---

## 6. Recomendación, ordenada por (ganancia esperada / esfuerzo)

| # | Qué | Esfuerzo | Ganancia esperada | Riesgo |
|---|---|---|---|---|
| **1** | **Recalibrar la escala** (2 parámetros) y **mover el umbral de banda a ~1,36** | Horas. **Cero entrenamiento** | Spearman: **ninguna, por construcción**. MAE en niveles, exactitud exacta y bandas: mucha. Arregla que A1 se anuncie como A2 y que C2 sea inalcanzable | Bajo. Validar antes contra el catálogo (§1.2) |
| **2** | **Arreglar el truncado.** Dos brazos: (a) ventana de 190 palabras, sin truncar, coste de inferencia cero; (b) `MAX_LENGTH = 512`, ~2,2× de coste | 1 h de A100 por brazo | Recupera el 7–14 % del texto que hoy se tira. **La mayor ganancia por unidad de esfuerzo de la lista.** No pongo cifra: no la tengo | Bajo. El brazo (b) reabre el presupuesto de CPU |
| **3** | **Cambiar la pérdida a CORN + término por pares** con OneStopEnglish | 2 h de A100 | Ataca la causa de la compresión, no el síntoma. Alinea entrenamiento y evaluación | Medio. **No hay evidencia publicada específica de legibilidad** |
| **4** | **Estudio de agregación** (media / podada / p75 / p90) validado en OneStopEnglish y British Council | 1 día, **sin entrenar** | Producto: alto. Métrica: incierto. Puede dar dos números en vez de uno | Bajo |
| **5** | **Ampliar el corpus** con CEFR-SP y Ace-CEFR como tareas auxiliares | 2–3 días | Es el eslabón más delgado. La ganancia debería ser la mayor de todas, pero es la más difícil de acotar | Medio. Granularidades distintas (oración vs documento) |
| **6** | **Cambiar a `deberta-v3-base`** | 2–4 h de A100 | El mejor salto arquitectónico con evidencia: SQuAD 2.0 F1 88,4 vs 83,7, y mejor eficiencia muestral, que con 510 documentos es lo que decide | **Alto en despliegue**: ~2,5–3,5× de coste en CPU |
| **7** | **Multitarea: cabeza CLEAR + cabeza MCER** sobre un encoder | 4 h de A100 | Responde directamente al Cuadro 8: v1 y v2 miden cosas distintas y cada uno gana en su dominio. **Nadie lo ha probado** | Medio-alto |
| **8** | **`roberta-large` o `deberta-v3-large`** | 8 h + inestabilidad | Techo más alto | **Alto.** Afinar un *large* con 510 documentos falla a menudo. Y ~7–10× de coste en CPU |
| **9** | **LLM 8 B con QLoRA** | Días | La evidencia dice que **iguala, no bate**, a un encoder afinado ([arXiv 2512.12677](https://arxiv.org/html/2512.12677v1)) | **No desplegable.** Útil solo como generador de etiquetas para ampliar los 654 documentos, nunca como modelo servido |

### 6.1 Qué probaría primero, y qué esperaría ganar

**Hoy mismo, sin GPU: el punto 1.** Recalibración lineal inversa y umbral de
banda a 1,36. Esperado: **el Spearman no se mueve ni un decimal** —y hay que
decirlo antes de correrlo, para que nadie lo interprete como fracaso—, pero
desaparecen tres defectos concretos y verificables: A1 deja de anunciarse como
A2, A2 deja de anunciarse como B1, y el ancla C2 pasa a ser alcanzable. Es la
única intervención de la lista que mejora lo que el lector ve sin tocar los
pesos, y el propio documento ya la tiene apalabrada como trabajo futuro (§10.4).

**Después, en un solo reentrenamiento de ~1,5 h de A100: los puntos 2a + 3
juntos.** Ventana de 190 palabras (truncado cero, coste de inferencia cero) con
pérdida CORN más término por pares de OneStopEnglish, sobre el mismo
`distilroberta-base`. Van juntos porque son independientes del encoder y porque
comparten el mismo entrenamiento.

**Qué esperaría, dicho con la incertidumbre que tiene:**
- **MAE en niveles: bajada clara.** Es lo que ataca directamente CORN, y es la
  métrica que hoy está en 0,499.
- **Pendiente de calibración: hacia 0,85–0,95** antes incluso de calibrar.
- **Spearman: plano, o subida por debajo del umbral de ruido.** Ya está en 0,908
  sobre 6 niveles bien separados, y ese conjunto tiene poco margen arriba —
  recuérdese que en Ace-CEFR un modelo pequeño ya bate al **anotador humano
  experto** (MSE 0,37 vs 0,75,
  [arXiv 2506.14046](https://arxiv.org/html/2506.14046v1)). **Si el Spearman
  sale plano, eso no es un fracaso: es el resultado, y hay que publicarlo así.**

**Y lo que *no* haría primero:** cambiar de modelo. El Cuadro 7 del propio
proyecto ya demostró que subir potencia sobre una representación que no ha
cambiado no sirve. Aquí la representación no ha cambiado —sigue truncándose a
256 tokens y sigue optimizando MSE—, así que `deberta-v3-base` heredaría los
mismos tres defectos, más caros de servir.

---

## Fuentes

- Shi, X., Cao, W. & Raschka, S. (2023). *Deep neural networks for rank-consistent ordinal regression based on conditional probabilities* (CORN). Pattern Analysis and Applications. https://link.springer.com/article/10.1007/s10044-023-01181-9 · https://arxiv.org/abs/2111.08851
- Cao, W., Mirjalili, V. & Raschka, S. (2020). *Rank consistent ordinal regression for neural networks* (CORAL). Pattern Recognition Letters. https://arxiv.org/abs/1901.07884
- Implementación: https://github.com/Raschka-research-group/coral-pytorch
- Lee, J. & Vajjala, S. (2022). *A Neural Pairwise Ranking Model for Readability Assessment.* Findings of ACL 2022. https://aclanthology.org/2022.findings-acl.300/
- Zeng, J. et al. (2022). *Enhancing Automatic Readability Assessment with Pre-training and Soft Labels for Ordinal Regression.* Findings of EMNLP 2022. https://aclanthology.org/2022.findings-emnlp.334/
- *Going Beyond Passages: Readability Assessment for Book-level Long Texts.* CCL 2024. https://aclanthology.org/2024.ccl-1.100.pdf
- Arase, Y. et al. (2022). *CEFR-Based Sentence Difficulty Annotation and Assessment.* EMNLP 2022. https://aclanthology.org/2022.emnlp-main.416/ · corpus: https://github.com/yukiar/CEFR-SP
- Kogan, D. et al. (2026). *Ace-CEFR.* https://arxiv.org/html/2506.14046v1
- Grossman, R. & Chen, Y. (2026). *Zero-shot Large Language Models for Automatic Readability Assessment.* ACL 2026. https://arxiv.org/abs/2604.24470
- *ModernBERT or DeBERTaV3? Examining Architecture and Data Influence on Transformer Encoder Models Performance.* https://arxiv.org/abs/2504.08716
- Warner, B. et al. (2024). *ModernBERT.* https://arxiv.org/html/2412.13663v2 · https://huggingface.co/blog/modernbert
- He, P. et al. *DeBERTaV3.* https://huggingface.co/microsoft/deberta-v3-base
- Beltagy, I. et al. (2020). *Longformer.* https://github.com/allenai/longformer
- *Fine-Tuning Causal LLMs for Text Classification: Embedding-Based vs. Instruction-Based Approaches.* https://arxiv.org/html/2512.12677v1
- Google Colab. *Precios y unidades de cómputo.* https://colab.research.google.com/signup
