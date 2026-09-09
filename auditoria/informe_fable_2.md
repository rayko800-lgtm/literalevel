# Auditoría externa de LiteraLevel — informe 2

Auditor: externo, sin autoría en el proyecto. Fecha: 2026-09-09.
Método: `.claude/skills/auditar-proyecto-datos/SKILL.md` (seis frentes, lectura desde
conclusiones y limitaciones hacia atrás, inventario de cifras, documento contra código).
No se ha modificado ningún archivo del proyecto ni se ha leído nada de `auditoria/`.

Todo lo que se pudo recalcular se recalculó (ajustes afines con `numpy.polyfit`,
contraste WCAG sobre `app/paletas.py`, razones de velocidad, horas de A100, sumas de
particiones y cuadros). Lo que no se pudo verificar va como DUDA.

Recuento: **1 CRÍTICO · 8 SERIOS · 8 MENORES · 7 DUDAS.**

---

## CRÍTICO

### [CRÍTICO] El Cuadro 7 y la conclusión 2 usan cifras que el propio cuaderno entregado contradice sobre «la misma partición»

- **Dónde:** `entrega/documento.md:520-525` (§7.1), `:539-545` (Cuadro 7), `:934-939`
  (Conclusiones); `entrega/documento.tex` (mismo cuadro y misma conclusión);
  `entrega/notebook_proyecto.py:1272-1275` y `:1323-1327`.
- **Qué dice:** §7.1: «Todos los modelos comparten la **misma partición agrupada por
  libro** (3.774 extractos de entrenamiento y 950 de prueba) y la misma semilla, de modo
  que las diferencias entre ellos son atribuibles al modelo». Cuadro 7: «Regresión
  logística | 3 variables clásicas | 0,29 | 1,39» y «XGBoost | 3 variables clásicas | 0,28
  | 1,42». Conclusión: «tres variables clásicas dan 1,39 niveles de error ordinal tanto con
  regresión logística como con XGBoost; un embedding lo baja a 0,93».
- **Por qué:** el cuaderno recalcula exactamente ese modelo sobre exactamente esa
  partición (`logistica_tres`, línea 1272, «Regresión logística (3 variables clásicas)») y
  su propia interpretación (línea 1323-1324) reporta **«exactitud 0,313, error ordinal
  1,295 niveles»**, no 0,29 y 1,39. Y XGBoost en el cuaderno corre sobre 17 variables
  (línea 1305, «XGBoost (17 variables)»: 0,340 y 1,081), no sobre 3. El cuaderno además
  obtiene una referencia clásica con 17 variables de **0,352 y 1,061** (línea 1325) que el
  documento no pone en el Cuadro 7 ni en las conclusiones. Consecuencia: el escalón
  «variables clásicas → embedding» que la conclusión cuantifica como 1,39 → 0,93 es, con
  los números del propio cuaderno, 1,295 → 0,93 (o 1,061 → 0,93 frente a una referencia
  clásica bien surtida). La tesis cualitativa sobrevive; la cifra con la que se la vende
  no coincide con el código entregado, y el documento afirma «misma partición, misma
  semilla» precisamente para que se puedan comparar. El propio cuaderno lo reconoce como
  «matiz» (línea 1360-1366); el documento solo lo alude sin cifras («el cuadernillo enseña
  un caso donde ampliar de tres a diecisiete variables sí mejora», `documento.md:437-438`).
- **Arreglo:** o bien el Cuadro 7 reporta los valores que el cuaderno reproduce (0,313 /
  1,295 para logística de 3 variables, y XGBoost sobre las mismas variables que se
  comparan) y añade la fila de 17 variables (0,352 / 1,061), o bien dice explícitamente
  que las dos primeras filas son un experimento histórico no reproducido y retira de §7.1
  la frase «misma partición y misma semilla» para esas filas. En cualquier caso la
  conclusión 2 debe citar el escalón real.

---

## SERIO

### [SERIO] Las conclusiones atribuyen el 0,908 y el 97,2 % a «textos externos con nivel MCER oficial»

- **Dónde:** `entrega/documento.md:925-929`; `entrega/documento.tex:2235`.
- **Qué dice:** «Sobre textos externos con nivel MCER oficial, el modelo desplegado ordena
  los niveles de forma estrictamente creciente (0,5040 · … · 1,4952), con una correlación
  de Spearman de 0,908 en validación ciega y el 97,2 % de los documentos dentro de un nivel
  de error.»
- **Por qué:** 0,908 y 97,2 % son del conjunto de validación interno del corpus de anclaje
  (144 documentos, Cuadro 9 primera fila, `documento.md:632-634`). Sobre los textos
  externos las cifras son 0,829 (38 textos, Colab) y 0,854 (45 textos, local). La única
  fuente que nombra la frase es «textos externos», así que quien lea solo las conclusiones
  —que es lo que hace un evaluador con prisa— se lleva una correlación externa de 0,908
  que no existe. Es el caso que la guía de auditoría marca como grave: atribuir a un
  corpus una métrica que viene de otro.
- **Arreglo:** separar en dos frases: orden estrictamente creciente y Spearman 0,854/0,829
  sobre British Council; Spearman 0,908 y 97,2 % sobre los 144 de validación del anclaje.

### [SERIO] `validar_local.py` no aplica el filtro de prosa que aplicó Colab, y la diferencia 45 frente a 38 se atribuye solo a la extracción del PDF

- **Dónde:** `validar_local.py:26-33` (`cuerpo`), `:69` (`p.puntuar(texto)`), `:80`
  (`esperado` sin A1); `app/scoring.py:285-295` (docstring de `puntuar`); `README.md:98`
  («A1 | 3 | 0.5040 | —»); `entrega/documento.md:648-653`.
- **Qué dice:** el documento: «las medias difieren ligeramente de las obtenidas en Colab
  … porque la extracción de texto de los PDF conserva 45 de los 59 textos originales y el
  anclaje de la sección de lectura recorta distinto».
- **Por qué:** (1) `cuerpo()` devuelve `" ".join(utiles)`: **una sola línea**. `puntuar`
  llama a `continuous_prose` sobre ese texto, y el propio docstring de `scoring.py:285-293`
  explica que con una sola línea «sus dos comprobaciones de maquetado —dos o más viñetas,
  seis o más líneas— no podían dispararse jamás. El detector de listas, menús y tablas era
  código muerto». El guion de validación reproduce exactamente ese fallo: el filtro
  estructural no puede actuar. (2) El filtro por título que describe §4.3(a) no está en el
  guion. (3) Colab no reportó A1 (`esperado` no tiene clave A1; README pone «—»), y §4.3(a)
  dice que es en A1 donde están el menú, el horario, el tablero de salidas, las tarjetas y
  los mensajes de texto. Los 3 textos A1 locales que abren el titular «cinco niveles
  estrictamente crecientes» (Resumen, Conclusiones, cuaderno, tarjeta del modelo) son, por
  tanto, textos que la validación de referencia no incluyó, filtrados con un criterio más
  débil, y el documento no lo dice: atribuye toda la diferencia a la extracción del PDF.
  El orden de los cuatro niveles A2–C1 se sostiene en las dos ejecuciones; el quinto punto
  no tiene respaldo equivalente.
- **Arreglo:** que `validar_local.py` conserve los saltos de línea antes de `puntuar` (o
  aplique el mismo filtro de dos vías de §4.3a) y reporte cuántos textos excluye y por
  qué; decir en §7.4 y en la limitación 5 que Colab no tuvo A1 y que los 3 A1 locales
  pasaron por un filtro distinto; o retirar A1 del titular y dejarlo en nota.

### [SERIO] El Cuadro 11 (0,854 · 0,807 · 0,657 · 0,730) no lo calcula ningún guion del repositorio

- **Dónde:** `entrega/documento.md:665-671` (Cuadro 11), `:881-882` (limitación 7);
  `entrega/notebook_proyecto.py:1726-1732` (solo markdown); `validar_local.py` (no calcula
  Spearman ni recuento de palabras ni correlación parcial); `README.md:62-70`.
- **Qué dice:** «Modelo v4 | 0,854 … Contar las palabras del texto, sin modelo | 0,807 …
  Modelo, descontando la longitud (correlación parcial) | 0,657» sobre «45 textos», y
  «Esta tabla se reproduce en cualquier máquina con el guion `validar_local.py`» (§7.4,
  referido al Cuadro 10, pero el Cuadro 11 va a continuación sin guion propio).
- **Por qué:** se buscó `spearmanr`, `polyfit`, `partial`, `0.807`, `0.854`, `0.657` en
  todos los `.py` del repo (incluido `notebook_v4_dump.py`): el único cálculo parecido es
  el de `notebook_v4_dump.py:2478-2481`, que hace Spearman del número de palabras sobre
  **59** textos con el modelo **v1**, no sobre 45 con v4. El Cuadro 11 es la única defensa
  contra el confusor de longitud (limitación 7), y hoy es una afirmación sin experimento
  rastreable.
- **Arreglo:** añadir a `validar_local.py` (o a un guion hermano) el cálculo de Spearman
  del modelo, del recuento de palabras y de la correlación parcial sobre los mismos 45
  textos, e imprimirlos junto al Cuadro 10.

### [SERIO] La recta «predicho ≈ 0,72 × real + 0,38» no es el ajuste de los puntos sobre los que se dibuja

- **Dónde:** `entrega/documento.tex:1722-1727` y `:1748-1751`; `entrega/documento.md:687-688`,
  `:845-846`; `entrega/notebook_proyecto.py:1717`, `:1926`; `modelo_v4/README.md` (Límites).
- **Qué dice:** en el `.tex`: «% recta ajustada documentada … `{0.72*x+0.38}`» trazada
  sobre `(0.0,0.5040) (0.4,0.5480) (0.8,0.9276) (1.2,1.2478) (1.6,1.4952)`, y en el pie:
  «la pendiente es 0,72 y no 1».
- **Por qué:** recalculado con `numpy.polyfit`: el ajuste por mínimos cuadrados de esos
  cinco puntos es **0,671·x + 0,408** (sin ponderar) o **0,714·x + 0,359** (ponderado por
  n = 3, 7, 12, 11, 12). La recta 0,72/0,38 sale exactamente de las **cuatro medias de
  Colab** (A2–C1: 0,6479, 0,9513, 1,2883, 1,4950 → 0,7196·x + 0,376). Es decir, la figura
  dibuja los puntos locales con la recta de otra ejecución, y ningún archivo dice de dónde
  sale. La conclusión cualitativa (compresión) se mantiene con cualquiera de las tres
  rectas.
- **Arreglo:** declarar la procedencia (Colab, 38 textos, cuatro niveles) o sustituir por
  el ajuste de los datos que se muestran (0,67·x + 0,41).

### [SERIO] El filtro de prosa que describe §4.3(a) no es el que implementa `scoring.continuous_prose`

- **Dónde:** `entrega/documento.md:261-267`; `app/scoring.py:52-73`.
- **Qué dice:** «filtro de prosa continua por dos vías independientes —por palabras clave
  del título y por estructura (≥7 palabras por línea y densidad de puntuación final de
  frase en el intervalo (0, 0,11])—, que coinciden en 53 de 59 casos, el 89,8 %».
- **Por qué:** `continuous_prose` usa otros criterios: mínimo de palabras, ≥4 frases,
  media de palabras por frase entre 5 y 55, ≥2 viñetas o >35 % de líneas de ≤4 palabras.
  No hay umbral de 7 palabras por línea ni densidad de puntuación en (0, 0,11] en ningún
  `.py` del repo. Por tanto el 89,8 % y las «dos vías» —que son lo que, según la
  limitación 6 y el Cuadro 12, acotan la fuga entre diagnóstico y validación— describen un
  filtro que no está en el código entregado, y el que sí está es el que no puede actuar
  en `validar_local.py` (hallazgo anterior).
- **Arreglo:** publicar el guion del filtro de dos vías con su 53/59, o reescribir §4.3(a)
  con el filtro real y recalcular el acuerdo.

### [SERIO] Tres pruebas de `pruebas_extremas.py` no pueden fallar, con el mismo patrón que el archivo dice haber corregido

- **Dónde:** `pruebas_extremas.py:963-967`, `:932-935`, `:852-853`; el envoltorio en
  `:37-63`.
- **Qué dice:** `prueba("el caso que destapo la auditoria", lambda:
  ui.ficha.dificultad_global([{"dificultad": 0.0, "ventanas": 1}, {"dificultad": 2.0,
  "ventanas": 9}]))`; `prueba("apuntar en una ruta imposible no revienta", lambda:
  _con_codigos(...) is None)`; `prueba("las tres bandas son alcanzables", lambda:
  sorted({...}))`.
- **Por qué:** `prueba` solo falla si `fn` lanza (línea 57-62). La primera no comprueba
  que el resultado sea 1,8 y no 1,0: si `dificultad_global` volviera a la media de medias,
  devolvería 1,0 sin excepción y la prueba «que destapó la auditoría» seguiría en `ok`. La
  segunda devuelve un booleano: si fuera `False` tampoco lanza. La tercera no comprueba que
  el conjunto tenga tres elementos. Es exactamente lo que el docstring de `prueba`
  (líneas 41-49) describe como «peor que no tenerlas, porque dan confianza sin darla».
  La prueba sustantiva de al lado (`_agregacion_por_ventanas`, 500 libros sintéticos con
  `assert`) sí es real; las tres citadas son decorativas.
- **Arreglo:** `assert abs(resultado - 1.8) < 1e-9`; `assert ... is None`; `assert
  len(bandas) == 3`.

### [SERIO] Cuadro 7 no dice que el «Transformer afinado» es `roberta-base`, no el v4, y §7.2 encadena sus métricas con §7.4

- **Dónde:** `entrega/documento.md:545`, `:553-566`; `entrega/notebook_proyecto.py:1367-1371`.
- **Qué dice:** «**Transformer afinado** | **Texto crudo, atención** | 0,46 | 0,67», y a
  continuación «El modelo afinado directamente sobre el texto … alcanza además RMSE 0,560
  y correlación de Pearson 0,89 … el modelo reportado es el de la época 3».
- **Por qué:** el cuaderno lo identifica: «`roberta-base` afinado en regresión (125 M
  parámetros …) RMSE 0,560 y Pearson 0,89». El modelo desplegado es `distilroberta-base`
  (§7.4). El documento nunca nombra la arquitectura de esa fila ni dice que es un modelo
  distinto del desplegado, y el Cuadro 12 («`distilroberta` y no `roberta-base` completo …
  la diferencia de calidad no justificaba 3× de tamaño») no da la cifra de esa
  «diferencia de calidad». Un lector razonable atribuye 0,560/0,89 y el control de
  sobreajuste al v4.
- **Arreglo:** nombrar `roberta-base` en la fila del Cuadro 7 y en §7.2, y dar la cifra de
  distilroberta sobre CLEAR si existe (o decir que no se midió).

### [SERIO] El 97,2 % «dentro de ±1 nivel» y el 53,5 % exacto no tienen línea base

- **Dónde:** `entrega/documento.md:632-637` (Cuadro 9); limitación 9, `:869-878`.
- **Qué dice:** «Validación ciega | 144 | 53,5 % | **97,2 %** | **0,908**».
- **Por qué:** con seis niveles ordinales, «dentro de ±1» lo cumple cualquier predictor
  que acierte el nivel central para tres de los seis niveles; sin la distribución por
  nivel de los 144 (que la limitación 9 reconoce no publicada) no se puede saber qué daría
  predecir siempre B1 o B2. La guía exige baseline trivial para juzgar cualquier métrica;
  el documento lo hace bien para British Council (Cuadro 11) y no lo hace para el conjunto
  del que salen las dos cifras más repetidas del trabajo. Además el pie «MAE de 0,499
  niveles» no dice si son niveles de la escala interna 0–5 o de la pública 0–2.
- **Arreglo:** publicar los recuentos por nivel de los 144 (no exige texto) y el ±1 de la
  clase modal; aclarar la unidad del MAE.

---

## MENOR

### [MENOR] 286 ventanas donde la fuente dice 300

- **Dónde:** `entrega/documento.md:798-799`; `entrega/documento.tex:2102-2103`;
  `informe_velocidad.md:121-124` y `:83`.
- **Qué dice:** «286 ventanas puntuadas de una en una y en un solo lote dan 286/286
  valores idénticos con MAE 0,000000000».
- **Por qué:** el informe de velocidad mide la identidad de reagrupado sobre «las mismas
  300 ventanas … 300/300 valores idénticos bit a bit». Las 286 son del experimento de
  hilos (§3.a, 14 capítulos). Mismo resultado, número equivocado.
- **Arreglo:** 300/300.

### [MENOR] MAE 0,0000012 con un decimal que la fuente no tiene

- **Dónde:** `entrega/documento.md:795`; `entrega/documento.tex:2099`; `informe_velocidad.md:178,181,193`.
- **Qué dice:** «el MAE es 0,0000012 sobre la escala 0–2».
- **Por qué:** el informe reporta «MAE 0,000001» en las tres menciones. No hay archivo con
  el séptimo decimal.
- **Arreglo:** citar 0,000001 o adjuntar la medida cruda.

### [MENOR] 5,14 h no sale de 606 ventanas

- **Dónde:** `entrega/documento.md:803-806`.
- **Qué dice:** «con las 606 que promedian las cinco novelas largas medidas en local …
  salen **5,14 h**».
- **Por qué:** 61.642 × 606 / 2.022 / 3.600 = **5,13 h**. Cuadra solo si el promedio real
  es ≈606,6 y se redondeó al citarlo. Las 2,96 h con 350 sí cuadran (2,964).
- **Arreglo:** dar el promedio con un decimal o poner 5,13.

### [MENOR] `informe_velocidad.md` razona con el corte de banda viejo (1,6)

- **Dónde:** `informe_velocidad.md:158-160`; `app/scoring.py:101-135`.
- **Qué dice:** «un texto de 1,68 pasa a 1,47, o sea cruza de "avanzado" a "intermedio"
  (el corte está en 1,6)».
- **Por qué:** el corte vigente es 1,4 (`public_band`); con él 1,47 sigue en «avanzado» y
  el ejemplo ya no ilustra nada. El documento (§7.6) usa el argumento corregido (52 % de la
  escala cambia de letra, 21 % de banda; ambos recalculados y correctos), pero el informe
  que lo respalda está desactualizado.
- **Arreglo:** actualizar el párrafo o fecharlo como anterior al cambio de cortes.

### [MENOR] «La peor paleta, 9,51» no es la peor pareja

- **Dónde:** `entrega/estrategia.md:282`; `app/paletas.py`; `pruebas_extremas.py:778-822`.
- **Qué dice:** «**Cumplido**: las cinco paletas superan WCAG AA; la peor, 9,51».
- **Por qué:** recalculado con la misma fórmula de luminancia de la prueba sobre los
  cuatro pares que la prueba mide: la peor razón es **4,53** (hielo, texto de botón sobre
  la parte alta del degradado); los botones de las cinco paletas están entre 4,53 y 4,74.
  9,51 es la peor solo del par interfaz (menta). Todas pasan AA, pero la que se cita como
  «peor» está al doble de la que de verdad lo es, y el margen real es 0,03.
- **Arreglo:** «la peor pareja, 4,53 (botón); la peor de interfaz, 9,51».

### [MENOR] README dice «hasta la cuarta cifra» donde el documento dice tercera

- **Dónde:** `README.md:104`; `entrega/documento.md:650`.
- **Qué dice:** README: «C1 coincide hasta la cuarta cifra»; documento: «coincide hasta la
  tercera cifra decimal —1,4952 frente a 1,4950—».
- **Por qué:** 1,4952 y 1,4950 coinciden en tres decimales; la cuarta difiere.
- **Arreglo:** corregir el README.

### [MENOR] «La misma unidad, la ventana» en el Cuadro 12 frente al muestreo de 8 en `puntuar`

- **Dónde:** `app/scoring.py:21` (`MAX_BLOCKS_PER_DOC = 8`), `:89-93`; `entrega/documento.md:612-616`.
- **Qué dice:** §7.4: «Puntúa bloques de 250 palabras truncados a 256 tokens y promedia
  sin ponderar».
- **Por qué:** `Puntuador.puntuar` (el camino que usa `validar_local.py`) muestrea como
  máximo 8 ventanas repartidas por el documento; §6.1 (T7) lo declara para «la puntuación
  rápida», pero §7.4 describe el estimador del modelo desplegado sin esa salvedad. Para
  British Council no importa (textos de 1–3 ventanas); para la ficha rápida de un libro sí.
- **Arreglo:** una frase en §7.4 remitiendo a T7.

### [MENOR] Cifra interna distinta para el catálogo: 61.552 frente a 61.642

- **Dónde:** `colab_precalculo.py:222`; `entrega/documento.md:217`, `:801`.
- **Qué dice:** el guion: «**57 horas** para los 61.552»; el documento: «61.642 libros … 57
  horas en bajar».
- **Por qué:** las 57 h salen con las dos cifras (61.642/0,3/3.600 = 57,08), así que no
  cambia nada, pero el repo maneja dos totales para la misma cosa.
- **Arreglo:** unificar.

---

## DUDA

### [DUDA] 0,00037 de desviación fp16 en A100 no aparece en ningún archivo

- **Dónde:** `entrega/documento.md:714` (Cuadro 12); `investigacion/acelerar_precalculo.md`.
- **Qué dice:** «En una A100 sí compensa, y allí la desviación medida es 0,00037 de media».
- **Por qué:** se buscó `00037` en todo el repo: solo está en el documento. La cifra vecina
  más parecida es el fp16 **local** (`informe_velocidad.md:182`: «MAE 0,00035»). No puedo
  afirmar que sea una confusión, pero no hay medida en A100 que la respalde.

### [DUDA] «0,004 de diferencia máxima medida en cinco libros reales»

- **Dónde:** `entrega/documento.md:709` (Cuadro 12).
- **Por qué:** no hay archivo con esa medición (`0.004`/`0,004` solo aparece en el
  documento). La prueba `_agregacion_por_ventanas` demuestra la identidad matemática, no
  la magnitud sobre libros reales.

### [DUDA] Partición 510/144 del corpus de anclaje: ¿por documento o por fuente? ¿Eligió época?

- **Dónde:** `entrega/documento.md:619-630`, `:869-878`.
- **Por qué:** el documento reconoce que la composición no está publicada y que el guion
  vive en Drive. Si los 144 eligieron el punto de control —como los 950 de CLEAR— entonces
  «validación ciega» no es la palabra, igual que el documento ya admite para §7.2. No hay
  forma de comprobarlo desde el repo. La tarjeta `modelo_v4/README.md` repite las cifras
  sin añadir procedencia.

### [DUDA] Las filas del Cuadro 8 están escritas a mano en el volcado del cuaderno v4

- **Dónde:** `notebook_v4_dump.py:2481` (`filas.append(('Literatura (CLEAR Lit)', 461,
  0.848, 0.760))` …).
- **Por qué:** la celda que imprime la «MATRIZ FINAL» tiene los valores tecleados, no
  calculados; la celda anterior (`:2395`) sí los calcula, pero no puedo comprobar que
  coincidan sin ejecutar el volcado con los pesos v1/v2.

### [DUDA] «El Cuadro 10 se reproduce en cualquier máquina» exige 59 PDF que no se listan

- **Dónde:** `validar_local.py:57`; `README.md:166-169`; `entrega/documento.md:894-895`.
- **Por qué:** el guion busca `*LearnEnglish-Reading*.pdf` en `~/Downloads`. No hay lista
  de los 59 archivos, ni sus URL, ni instrucciones de descarga. Que los PDF sean públicos
  hace la reproducción posible; que no estén enumerados la hace improbable.

### [DUDA] Las desviaciones del Cuadro 10 son poblacionales (`np.std`, ddof=0)

- **Dónde:** `validar_local.py:85`; `entrega/documento.md:641-647`.
- **Por qué:** con n = 3 la diferencia entre ddof=0 y ddof=1 es un factor 1,22. El
  documento dice solo «Desviación». No es un error, pero con esas n conviene decir cuál.

### [DUDA] El Colab de referencia y la ejecución local usan distinto estimador por texto

- **Dónde:** `notebook_v4_dump.py:2270` (`puntajes_crudos_por_ventana`, todas las
  ventanas); `app/scoring.py:89-93` (tope de 8).
- **Por qué:** para textos de British Council (cortos) es indiferente; lo anoto porque el
  documento presenta las dos ejecuciones como el mismo procedimiento y no lo son
  exactamente.

---

## Lo que se comprobó y está bien

Aritmética y coherencia interna del documento:

- 510 + 144 = 654; 77/144 = 53,47 %; 140/144 = 97,22 %; 148 + 1.049 = 1.197; el Cuadro 3
  suma 1.197 y 100,0 %; 461 + 489 = 950; 3.774 + 950 = 4.724 (CLEAR completo);
  151 + 38 = 189 y 453/567 = 79,9 % («el 80 %»); 53/59 = 89,8 %; 3 + 7 + 12 + 11 + 12 = 45;
  el escalón A1–A2 es 0,044; 45.345/18 ≈ 2.519 («×2.500»).
- Velocidad: 8,19/6,16 = +33 %; 112,7/8,19 = 13,8×; 2.022/8,19 = 247×; 10,06/8,53 = +18 %;
  2,96 h con 350 ventanas; 57 h de descarga a 0,3 libros/s; 487 ventanas en 86 s = 5,66
  v/s, coherente con los ~5,7 del informe. 839/840 y 0,210 y 4,8× coinciden con
  `informe_velocidad.md`.
- Argumento del int8 (§7.6): 0,21/0,4 = 52,5 % de la escala cambia de letra; 0,42/2 = 21 %
  cambia de banda. Ambos correctos.
- Bandas: `public_band` corta en 0,6 y 1,4; con los cortes viejos 0,8/1,6, B1 (0,928), B2
  (1,248) y C1 (1,495) caían en «intermedio» —tres de cinco, como dice el documento—; con
  los nuevos, A1–A2 básico, B1–B2 intermedio, C1 avanzado. `ANCHORS` y `LEVEL_VALUE`
  (A1 = 0 … C2 = 5, ×0,4) coinciden con el eje de la figura del `.tex`.
- Fuga de datos en el cuaderno: la partición es `GroupShuffleSplit` por `Title` con
  semilla (`notebook_proyecto.py:840-843`); la lista de 3.000 palabras familiares se
  construye **solo con el entrenamiento** y después de partir (`:846-850`), y el cuaderno
  cuantifica el efecto de haberla contaminado (`:903-912`). Bien hecho y bien contado.
- `ficha.dificultad_global` pondera por ventanas (`app/ficha.py:336-363`) y la prueba
  `_agregacion_por_ventanas` (500 libros sintéticos, `assert`) lo verifica de verdad.
- `validar_local.py` ya suspende si falta un nivel, si un nivel tiene menos de 2 textos o
  si las medias no crecen (`:96-122`); antes no podía suspender y el archivo lo cuenta.
- Paletas: 5 (`hielo, amanecer, menta, papel, medianoche`); recalculado el contraste de los
  cuatro pares en las cinco: todas ≥ 4,5 (mínimo 4,53).
- Interfaz: Gradio instalado 6.26.0; `app/ui.py` tiene 8 `gr.Tab(`, como dice el Resumen.
- Modelo: `modelo_v4/config.json` → `num_hidden_layers: 6`; `model.safetensors` =
  328.489.204 B = 328 MB (decimal), como dice §7.4.
- `app/cuentas.py`: códigos fuera del repo (variable de entorno), comparación con
  `hmac.compare_digest`, cupo probado con `assert v == [True, True, False, False]`; sus
  límites (sin bloqueo entre procesos, almacenamiento efímero) están declarados en el
  docstring. Sin `OPENAI_API_KEY` la puerta no existe y todo pasa, como pide `CLAUDE.md`.
- `.tex` frente a `.md`: se contrastaron ~70 cifras clave y coinciden (las que parecían
  faltar —0,326, 0,330, 0,72, 0,38, 0,239, 52 %, 21 %, 13,8— están con tipografía LaTeX,
  `0{,}326`, `\pct`, etc.); 14 limitaciones y 6 trabajos futuros en ambos; la casilla
  OneStopEnglish/v2 dice «no comparable» en ambos; la conclusión problemática (SERIO 1)
  está idéntica en los dos, es decir, el `.tex` dice lo mismo que el `.md`, para bien y
  para mal.
- Referencias: Nielsen (2000), Crossley et al., Vajjala & Lučić, Gerlach & Font-Clos,
  Ylönen, Reimers & Gurevych y Zipf están en la lista de referencias.
- La retirada del 0,840 de OneStopEnglish para v2 (§7.3) está bien argumentada y bien
  cuantificada (151 de 189 artículos × 3 niveles = 453 de 567 textos).
- Las limitaciones son específicas, no fórmulas: tamaños muestrales, corpus no
  redistribuible, n = 1 de usuario, filtro salido del diagnóstico. Y la sección de
  «hipótesis rechazadas» del Cuadro 12 es una buena práctica poco habitual.

---

## Veredicto

**Sólido:** el diseño anti-fuga del cuaderno (partición por obra, vocabulario solo de
entrenamiento), la honestidad de las limitaciones, la retirada del 0,840, la aritmética
de velocidad y del int8, la coherencia `.md`/`.tex`, la agregación por ventanas y su
prueba, y el control de acceso. El resultado ordinal A2–C1 se sostiene en dos ejecuciones
independientes.

**Arreglar antes de entregar:**

1. Cuadro 7 y conclusión 2: poner las cifras que el cuaderno reproduce (0,313 / 1,295;
   17 variables 0,352 / 1,061) o dejar de decir «misma partición y misma semilla».
2. La frase de conclusiones que cuelga el 0,908 y el 97,2 % de los «textos externos».
3. `validar_local.py`: que el filtro de prosa pueda actuar (no unir líneas) y que el
   documento diga que Colab no tuvo A1 y que los 3 A1 locales pasaron otro filtro.
4. Un guion que calcule el Cuadro 11 (Spearman, recuento de palabras, correlación parcial),
   o rebajar la limitación 7 a «no reproducible».
5. Procedencia de la recta 0,72/0,38 (o el ajuste real de los puntos dibujados).
6. Las tres pruebas decorativas: un `assert` en cada una.

**Opcional:** los MENORES (286→300, 0,000001, 5,13 h, corte 1,6 en el informe, 4,53 en
estrategia, README «cuarta cifra», nota sobre el tope de 8 ventanas, 61.552) y documentar
las DUDAS que se puedan cerrar sin redistribuir texto (recuentos por nivel de los 144,
lista de los 59 PDF, ddof de la desviación).
