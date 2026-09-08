# Auditoría externa de LiteraLevel

Fecha: 8 de septiembre de 2026. Versión examinada: `3016237` y árbol de trabajo inicialmente limpio.

Método: `.claude/skills/auditar-proyecto-datos/SKILL.md`. Se revisaron los seis archivos encargados y se contrastaron con el cuaderno histórico, la aplicación, el precálculo, las pruebas y los datos de figuras. No se modificó el proyecto; este informe es la única escritura.

**Dictamen:** la aplicación tiene implementaciones reales y varias cifras coherentes, pero la entrega necesita correcciones sustantivas. La independencia de la evaluación histórica está mal descrita; los sextiles de CLEAR se confunden con niveles MCER; el notebook interpreta incorrectamente el PCA; y documento, notebook y aplicación ya no describen exactamente el mismo procedimiento.

Alcance de la verificación: lectura de código y documentos, recuento del CSV con un analizador que respeta campos multilínea, lectura de la cabecera de los pesos, inspección del notebook JSON y recálculo aritmético en PowerShell. No se ejecutaron entrenamientos, inferencia ni llamadas de pago. `python` no está disponible en el PATH de esta sesión y el ejecutable localizado en `D:/ll_bench/venv_cuda` no encuentra su intérprete base. Esto limita la auditoría; **no demuestra que el proyecto falle en la máquina habitual del autor**. Las conclusiones que necesitan una ejecución o datos ausentes se marcan como DUDA. No se abrieron `.env` ni `CLAVES.txt`.

## 1. Hallazgos, por gravedad

### [CRÍTICO] H01. Los 950 extractos de «prueba» seleccionaron la mejor época

Dónde: `entrega/documento.md:485–522`; `entrega/notebook_proyecto.py:1294–1305`; `notebook_v4_dump.py:966–1005`.

Qué dice: «Se comparan sobre el mismo conjunto de prueba de 950 extractos»; «el modelo reportado es el de la época 3, no el de la última».

Por qué: el código histórico construye `dataset_test` con esos 950 extractos, lo entrega a `Trainer` como `eval_dataset`, activa `load_best_model_at_end=True` y selecciona por RMSE. Después vuelve a medir sobre `dataset_test`. No hay un tercer conjunto independiente. RMSE 0,560, Pearson 0,89, exactitud 0,46 y error ordinal 0,67 describen el conjunto usado para elegir el checkpoint. Presentarlos como una prueba final independiente invalida esa interpretación, aunque los números puedan ser los realmente obtenidos. La partición por libro no impide esta forma de fuga. Este hallazgo corresponde al transformer histórico sobre CLEAR; no demuestra lo mismo sobre los 144 documentos del v4.

Arreglo: llamar a esos 950 extractos validación de selección y retirar la interpretación de evaluación final independiente; si se mantiene esa pretensión, evaluar el procedimiento cerrado sobre un conjunto nuevo, separado por grupo. No hace falta reentrenar el v4 para corregir la presentación del experimento histórico.

### [CRÍTICO] H02. El vocabulario del test entra también en modelos evaluados, no solo en una correlación exploratoria

Dónde: `entrega/notebook_proyecto.py:820–824`, `842`, `870–876`, `1041–1063`, `1122–1134`, `1194–1229`; `entrega/documento.md:449`.

Qué dice: «Advertencia sobre ese −0,486, que es optimista»; «el sistema en producción usa una lista externa —el SPGC— precisamente para no incurrir en esto».

Por qué: las 3.000 palabras familiares se calculan con **todo CLEAR antes de la partición**. `palabras_raras` entra después en la regresión de 17 variables, el bosque y los clasificadores, incluida la logística de tres variables. La contaminación afecta a sus métricas de evaluación, no únicamente al −0,486. Su magnitud y dirección no pueden cuantificarse sin repetir la comparación. La excepción es la media y la regresión que selecciona solo las once columnas originales: esa ruta no usa el rasgo contaminado. Además, la app actual puntúa con el transformer y no consulta una lista SPGC: no se encontró esa lista en el camino de inferencia de `app/scoring.py`. **La admisión está en el notebook; no encontré una admisión equivalente en el documento final**, que presenta SPGC como la lista utilizada.

Arreglo: construir la lista exclusivamente en entrenamiento o proporcionar una lista externa versionada; recalcular las métricas afectadas y distinguir el experimento histórico, el reproducido y la inferencia de producción. Hasta entonces, no presentar esas evaluaciones como libres de fuga.

### [CRÍTICO] H03. Los sextiles de CLEAR no son niveles MCER, y sus cortes usan las etiquetas del test

Dónde: `entrega/notebook_proyecto.py:951–954`, `1005`, `1024–1034`, `1045–1046`; `entrega/documento.md:488–500`; `notebook_v4_dump.py:849`, `1009–1013`.

Qué dice: «exactitud sobre seis niveles MCER»; «Un texto que este sistema llama B1 […] cae en el cuarto sextil de facilidad de un corpus de 4.724 extractos».

Por qué: `pd.qcut(clear["BT_easiness"], q=6)` produce seis intervalos relativos al corpus y les asigna nombres A1–C2. No contiene una calibración contra MCER ni anotaciones institucionales de esos niveles. Decir que no certifica no convierte los sextiles en anclas MCER válidas. La explicación citada del notebook describe, además, un etiquetado distinto del v4 desplegado, cuya escala se atribuye a otro corpus. Por separado, los bordes se estiman antes del split con todos los valores objetivo: la definición de clases incorpora las etiquetas reservadas para evaluación. La exactitud sigue pudiendo describir esos sextiles transductivos, pero no un test independiente de clasificación MCER.

Arreglo: denominar las clases «sextiles de facilidad CLEAR» y el error «distancia entre sextiles»; separar esta tarea de la escala MCER del v4. Para una evaluación independiente, fijar los cortes con entrenamiento y aplicar esos cortes al resto, sin exigir balance perfecto en test.

### [CRÍTICO] H04. El PCA no establece un techo predictivo del 38 %

Dónde: `entrega/notebook_proyecto.py:899–947`, `1800–1805`.

Qué dice: «Ese número es el techo de la aproximación clásica»; «el mejor resumen posible de todas las métricas de legibilidad juntas explica el 38 %».

Por qué: PC1 se ajusta sin la variable objetivo. Maximiza varianza de las entradas, no capacidad para predecir `BT_easiness`. Que su correlación sea 0,614 permite calcular 0,614² = 0,377, pero no demuestra que otros componentes, combinaciones supervisadas o relaciones no lineales carezcan de señal adicional. El 62 % restante tampoco queda identificado como sintaxis, ambigüedad o carga conceptual. Esas variables no se aislaron experimentalmente. La propia matriz del PCA tiene 17 columnas, no solo las once métricas a las que alude la conclusión. La definición oficial de [PCA de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html) confirma que los componentes ordenan varianza de X.

Arreglo: conservar el PCA como descripción de redundancia y geometría de las entradas. Retirar «techo», «mejor resumen posible» y la atribución del residuo; basar las conclusiones predictivas en evaluaciones supervisadas adecuadamente separadas.

### [SERIO] H05. British Council aparece como ciego y nunca visto pese a haber guiado el diagnóstico

Dónde: `entrega/documento.md:30–35`, `242–250`, `772–776`; `entrega/notebook_proyecto.py:234`, `1555–1559`, `1604–1606`; `notebook_v4_dump.py:2475–2478`.

Qué dice: «sobre un corpus externo que nunca vio»; «Se definió un filtro de prosa continua antes de mirar ningún resultado».

Por qué: la limitación 6 del documento reconoce expresamente que British Council se utilizó primero para diagnosticar y luego para validar. El volcado histórico contiene predicciones v1/v2 y análisis del fallo antes de pasos posteriores del desarrollo. No demuestra que esos textos entrenaran los pesos del v4, pero sí que el conjunto influyó en decisiones del sistema. «No usado para ajustar pesos» y «evaluación ciega del procedimiento completo» son cosas diferentes. La coincidencia de dos filtros en 53/59 casos tampoco prueba que fueran fijados antes de explorar los resultados.

Arreglo: describirlo consistentemente como evaluación externa explorada durante el desarrollo. Documentar qué versiones, filtros y decisiones se eligieron antes o después de observarlo. Reservar «ciega» para un protocolo y un conjunto cuya independencia se puedan acreditar.

### [SERIO] H06. No existe una única correspondencia de escala, bandas y empates

Dónde: `app/scoring.py:96–143`; `app/ui.py:934–975`; `entrega/datos_figuras/escala_cefr.dat:1–7`; `entrega/documento.md:614–618`, `634`; `entrega/estrategia.md:196–205`; `entrega/notebook_proyecto.py:1408–1413`.

Qué dice: «básico < 0,8 ≤ intermedio < 1,6 ≤ avanzado»; «Ahora hay una sola regla».

Por qué: `public_score` sí aplica `clip(y,0,5)*0.4`. Sin embargo, `public_band` actual agrupa las letras calculadas con empate hacia arriba: sus fronteras son **0,6 y 1,4**. Documento, estrategia y notebook conservan **0,8 y 1,6**. A 0,7 el notebook da básico y la app intermedio; a 1,5 da intermedio y la app avanzado. Las seis fronteras numéricas de la figura coinciden con la tabla de la UI, pero el `.dat` no especifica qué extremo incluye. `anchor_cefr` sigue usando `round`, que resuelve los empates al par: interno 0,5 → A1, 2,5 → B1 y 4,5 → C1; la UI, para públicos 0,2, 1,0 y 1,8, devuelve A2, B2 y C2. La [regla documentada de Python](https://docs.python.org/3/library/functions.html#round) permite verificarlo sin inferencia del modelo. La UI evita usar `nivel_orientativo` en esa presentación, pero el contrato público de `Resultado` sigue discrepando. El ejemplo int8 1,68 → 1,47 ya **no cruza de banda** con el código actual: ambos valores son avanzados.

Arreglo: definir explícitamente bandas, intervalos semiabiertos y regla de empates; sincronizar documentación, figura, notebook y contrato público. Identificar el rechazo de int8 como una decisión tomada con las bandas anteriores, o revisar su justificación sin alterar las cifras medidas.

### [SERIO] H07. La dificultad global del libro cambia entre la app y el precálculo

Dónde: `entrega/documento.md:109–114`, `630`; `app/ui.py:1088–1091`, `1286–1289`; `colab_precalculo.py:397–415`.

Qué dice: «la salida del documento es la media sin ponderar de sus bloques»; «replicada literalmente en la app».

Por qué: el precálculo concatena todas las ventanas y obtiene su media; la UI calcula la media de las medias de los capítulos. Los dos estimadores coinciden solo bajo condiciones particulares. Ejemplo algebraico: un capítulo de una ventana con valor 0 y otro de nueve ventanas con valor 2 dan **1,0 en la UI y 1,8 en el precálculo**. No se ha medido aquí la discrepancia en libros reales; el desacuerdo del procedimiento sí está probado por código. La ficha vuelve a usar la media de capítulos para decidir si la lectura es exigente (`app/ui.py:1137–1141`).

Arreglo: elegir y documentar la unidad de ponderación; aplicar la misma agregación en cálculo en vivo, ficha y catálogo. Si se necesitan ambas medidas, darles nombres distintos y no afirmar equivalencia literal.

### [SERIO] H08. La fórmula publicada recorta después de promediar; la implementación recorta antes

Dónde: `entrega/documento.md:114`; `app/scoring.py:242–249`, `287–290`; `entrega/notebook_proyecto.py:198–204`.

Qué dice: `f(T) = 0,4 · clip((1/n) Σ g(b_k), 0, 5)`.

Por qué: `_puntuar_bloques` recorta cada logit a [0,5] antes de calcular la media. En general, `clip(mean(x))` y `mean(clip(x))` son distintos. Con logits −1 y 3, la fórmula produce 0,4 y el código 0,6. La cabeza de regresión no incorpora por sí misma una activación que garantice el intervalo. Puede resolverse definiendo explícitamente `g` como la salida ya recortada; actualmente esa distinción no está expresada. No se afirma que la discrepancia haya cambiado una métrica publicada: faltan logits para comprobarlo.

Arreglo: hacer explícito el recorte por bloque en la definición matemática y contrastarlo con el procedimiento original de validación.

### [SERIO] H09. Ventanas fijas no significa longitud invisible ni lectura literal de todas las palabras

Dónde: `entrega/notebook_proyecto.py:206–211`, `1442–1445`; `app/scoring.py:76–93`, `242–243`; `entrega/documento.md:433`, `735–740`.

Qué dice: «todas las ventanas miden exactamente 250 palabras, sin excepción»; «la longitud del documento no puede entrar como señal».

Por qué: `fixed_blocks` devuelve una ventana de longitud variable para documentos de **150 a 250 palabras**, y el tokenizador trunca a 256 subtokens. Un recorrido sin límite de ventanas recorre todos sus inicios, pero no garantiza que el modelo vea las últimas palabras de cada bloque: las que excedan el límite se eliminan. El muestreo, el solapamiento final y las ventanas cortas tampoco establecen independencia estadística respecto de la longitud. El documento reconoce correctamente la correlación 0,730 con longitud, mientras el notebook usa una formulación absoluta incompatible. La observación de 200 ventanas saturadas es evidencia de esa muestra, no una demostración universal.

Arreglo: decir que la longitud total no se proporciona como variable explícita; documentar ventanas cortas, solapamiento y truncado. Usar «todas las ventanas elegibles» para el recorrido completo y cuantificar cobertura de tokens si se desea afirmar lectura íntegra.

### [SERIO] H10. Publicar los pesos no vuelve reproducible toda la evaluación

Dónde: `entrega/notebook_proyecto.py:27–60`, `119–120`, `1336–1368`, `1470–1483`, `1509–1571`, `1842–1855`; `entrega/documento.md:789–792`, `811–812`; `requirements.txt:3–26`.

Qué dice: «Una sola cosa […] publicar los pesos del v4»; «No hace falta cambiar ninguna otra línea».

Por qué: con `URL_MODELO` rellenada, el notebook carga el modelo y puntúa dos extremos de CLEAR. No incorpora el corpus MCER, sus particiones, el entrenamiento ni el recálculo de 0,908/97,2 %. La validación externa se crea con una tabla de números literales. El diccionario, al contrario de lo que dice el documento, no es necesario para las celdas del cuaderno. El código principal sí evita `drive.mount` y rutas privadas: no debe atribuírsele el problema de rutas del volcado histórico. Pero depende de una imagen de Colab no fijada, de descargas sin versión inmutable y de bibliotecas sin manifiesto exacto. `warnings.filterwarnings("ignore")` oculta advertencias; no demuestra que no existan. El `.ipynb` entregado contiene 92 celdas y **cero celdas con contador de ejecución o salidas**, de modo que tampoco conserva una corrida verificable.

Arreglo: separar «ejecuta sin interrumpirse», «reproduce modelos clásicos», «demuestra inferencia v4» y «reproduce la evaluación v4». Publicar manifiesto y revisión de artefactos, exportar una ejecución limpia y proporcionar datos o predicciones auditables para cada métrica. No prometer reproducibilidad completa con la mera carga de pesos.

### [SERIO] H11. El validador puede declarar orden correcto sin evaluar ningún texto

Dónde: `validar_local.py:43–45`, `54–70`, `80–83`; `entrega/documento.md:589`, `788`.

Qué dice: «Esta tabla se reproduce en cualquier máquina con el guion `validar_local.py`»; `all(a < b for a, b in zip(medias, medias[1:]))`.

Por qué: el script busca PDF en Downloads o en una carpeta suministrada, sin manifestar cuáles son los 59 originales. Si el modelo carga pero no hay PDF coincidentes, `medias` queda vacía y `all(...)` devuelve `True`; sucede también con un único nivel. Si una inferencia falla, se descarta como si faltara cuerpo localizable. No verifica los cinco niveles ni las n esperadas. Además, `cuerpo` une todas las líneas con espacios antes de `puntuar`, anulando para esta validación las condiciones basadas en líneas y viñetas cuya reparación destaca el documento. El script no calcula Spearman, exactitud ni correlación parcial.

Arreglo: exigir cobertura mínima y niveles esperados, informar por separado extracción e inferencia fallidas y rechazar una validación vacía. Proporcionar un manifiesto de entradas y preservar la estructura que usa el filtro, o documentar explícitamente que este pipeline aplica otro filtro.

### [SERIO] H12. Hay baselines reales, pero el documento no presenta la comparación clásica más completa

Dónde: `entrega/documento.md:389–411`, `494–514`, `627–632`; `entrega/notebook_proyecto.py:1087–1124`, `1234–1253`, `1283–1288`.

Qué dice: «El techo de las variables clásicas»; «Ganancia nula […] El embedding ya contiene esa información».

Por qué: el notebook sí implementa media de entrenamiento, regresiones lineales, bosque, logística y referencia de clase mayoritaria; también reconoce que 17 variables ofrecen 0,354 de exactitud y error 1,059 frente al 0,37/0,93 reportado del embedding. El documento sostiene el argumento casi exclusivamente con la referencia antigua de tres variables (0,29/1,39). No es una cifra inventada: existe en el volcado histórico, pero representa un experimento distinto del recalculado, que declara 0,312/1,293 para tres variables. Sin intervalos, réplica y evaluación independiente no queda demostrado un «techo», la equivalencia de los modelos ni que el embedding contenga toda la información de los rasgos. Cambiar de clasificador a transformer cambia simultáneamente representación, preentrenamiento, objetivo y arquitectura: tampoco aísla el efecto causal de «regresión, no clasificación».

Arreglo: presentar juntos los baselines relevantes, con versión de rasgos, corpus, partición, métrica y estado de ejecución. Limitar la conclusión a las configuraciones comparadas. No afirmar ausencia de ganancia o causalidad a partir de puntos únicos redondeados.

### [SERIO] H13. La extrapolación de 6,3 horas no sale del cálculo entregado

Dónde: `entrega/documento.md:45–47`, `704–725`; `entrega/estrategia.md:181–189`, `255`; `entrega/notebook_proyecto.py:1705–1757`; `colab_precalculo.py:354–357`.

Qué dice: «medir los 61.642 libros […] son unas 6,3 horas de A100».

Por qué: el supuesto explícito en ambos cuadernos es 350 ventanas por libro. Con las cifras publicadas: 61.642 × 350 = 21.574.700 ventanas; dividir por 2.022 y por 3.600 da **2,964 horas**, no 6,3. En CPU da **688,847 horas**, que sí coincide con las 689 del notebook. Las 6,3 horas implicarían aproximadamente **744 ventanas por libro**, supuesto o medición que no acompaña al cálculo. Los factores sí son correctos: 101,7/8,7 = 11,6897 y 2.022/8,7 = 232,4138. El propio notebook declara que 350 es un supuesto; llamarlo además «conservador» requiere medir la distribución del catálogo.

Arreglo: unificar el supuesto o publicar la medición que lo sustituye. Separar tiempo de inferencia, descarga y proceso completo; reportar la extrapolación como estimación condicionada, no como duración medida de los 61.642 libros.

### [SERIO] H14. El lote medido de 64/128 no se alcanza por reagrupar capítulos en la app

Dónde: `informe_velocidad.md:33–39`, `104–126`; `app/ui.py:1083–1085`; `app/scoring.py:219–241`; `entrega/documento.md:848–850`.

Qué dice: «Doce hilos y lotes de 64 en CPU, fp32 con lote 128 en GPU».

Por qué: el informe señala correctamente que reagrupar ventanas de varios capítulos exige cambiar la organización del trabajo; mide el rendimiento usando ventanas agrupadas. La UI actual sigue llamando `perfil_de_texto` **capítulo por capítulo**. `_puntuar_bloques` trocea cada llamada en lotes máximos, pero no acumula ventanas entre llamadas. Con los tamaños del propio informe —máximo 31 ventanas por capítulo en C&P y 17 en W&P— no se forman lotes de 64/128. Los números de un benchmark de lotes grandes no acreditan por sí solos esa aceleración en el recorrido interactivo.

Arreglo: distinguir el benchmark de capacidad por lote del rendimiento del manejador real; medir este último con su forma efectiva de agrupar y repintar. Si se conserva el código, corregir la atribución de la mejora sin dar por implementado el reagrupado entre capítulos.

### [SERIO] H15. Una comparación de ocho ventanas en un capítulo no valida el vistazo de libros completos

Dónde: `entrega/documento.md:436`, `735–740`; `entrega/estrategia.md:185–189`; `entrega/notebook_proyecto.py:1447–1455`, `1819–1823`.

Qué dice: «si ocho ventanas bastan para representar un libro entero. Está medida y la respuesta es sí»; «El troceado en ventanas fijas lo corrigió sin tocar los pesos».

Por qué: la evidencia que identifica el documento es **un capítulo de 23 ventanas**, con medias 1,784 y 1,743. No valida el muestreo de una novela completa ni el otro atajo de **30 capítulos × 2 ventanas**. Tampoco prueba que cambiar el troceado haya corregido el catálogo: la entrega afirma a la vez que la remedición sigue en curso y cambia de v1 a v4. Sin comparar el mismo modelo bajo ambos protocolos y contar resultados terminados, no puede aislarse esa causa ni declarar la corrección completa.

Arreglo: circunscribir el 0,041 al capítulo medido; distinguir los dos atajos y evaluar sus errores en varios libros, incluidos cambios de banda y casos heterogéneos. Presentar la reparación del catálogo con su estado real y sin atribución causal no probada.

### [SERIO] H16. Varias «pruebas» informan éxito aunque devuelvan errores de comprobación

Dónde: `pruebas_extremas.py:37–49`, `706–710`, `778–791`, `800–811`; `entrega/estrategia.md:132`, `204–205`, `280–281`.

Qué dice: «una prueba fija los cinco límites»; «Las cinco pasan»; «183 pruebas de estrés […] ningún manejador lanza hacia la interfaz».

Por qué: `prueba` considera fallo únicamente una excepción. La prueba de límites devuelve una lista de discrepancias; la de contraste devuelve `malas`; la de bandas también devuelve una lista. Si esas listas contienen errores, el envoltorio imprime `ok` y no los registra en `FALLOS`. Hay otras pruebas con aserciones reales: no se invalida toda la batería. Pero esos casos no establecen las garantías semánticas citadas. La comprobación de color, además, examina solo dos pares de colores por paleta; no certifica todos los componentes o estados de la interfaz. No se afirma que los colores actuales incumplan el contraste: se cuestiona qué certifica la prueba.

Arreglo: hacer que una discrepancia falle efectivamente y separar pruebas de «no lanza» de pruebas de comportamiento. Limitar la afirmación de contraste a los pares y estados comprobados; conservar resultados de una ejecución de la revisión entregada.

### [SERIO] H17. Las estadísticas de la ficha y «tu ritmo» necesitan declarar sus estimaciones

Dónde: `entrega/documento.md:675–681`; `entrega/estrategia.md:70–72`, `223–228`; `app/ficha.py:31–32`, `159–218`; `app/ui.py:1131–1158`.

Qué dice: «cuánto tarda en leerlo a su ritmo»; «todo contado sobre el fichero».

Por qué: el total de palabras sí recorre los capítulos pertinentes, pero longitud de frase, diálogo y palabras frecuentes se calculan sobre `_muestra`, que toma prefijos de capítulos con objetivo aproximado de 60.000 palabras; riqueza léxica usa solo los primeros 20.000 tokens de esa muestra. No son estadísticas necesariamente globales de la obra. El tiempo usa **180 o 110 palabras/minuto**, no una velocidad observada del lector. Sin análisis previo del libro, incluso un perfil bajo cae por defecto en la velocidad cómoda. Son aproximaciones razonables de producto, pero «a tu ritmo» y una ficha sin identificar el muestreo les atribuyen más precisión de la implementada.

Arreglo: distinguir total contado, estadística de muestra y tiempo estimado bajo una velocidad supuesta. Informar las condiciones de la muestra y reservar «tu ritmo» para una velocidad realmente calibrada al lector.

### [SERIO] H18. El salto de orden por nivel a utilidad personal no está validado

Dónde: `entrega/documento.md:22–28`, `97–100`, `139–147`, `829–834`; `entrega/estrategia.md:49–50`, `277–284`; `app/perfil.py:210`.

Qué dice: «le busca libros que pueda terminar»; «Se cumplió el objetivo ordinal, que era el objetivo»; «delante de un texto real la gente se juzga mejor que describiéndose».

Por qué: medias crecientes de grupos no garantizan el orden de cada pareja de documentos, y ordenar textos de examen tampoco valida la combinación libro–lector. No se presenta validación del cuestionario, del peso 0,65 de los fragmentos, de la comprensión o de libros terminados. La estrategia reconoce correctamente que el impacto está «Sin instrumentar». El criterio empírico es más débil que la formulación por pares y que la promesa de terminar libros. La conclusión legítima es evidencia preliminar sobre orden y funcionamiento del prototipo, no eficacia personal demostrada.

Arreglo: presentar la utilidad como hipótesis de producto y el 0,65 como decisión heurística hasta validarlo. Mantener separados orden individual, medias por nivel, usabilidad cualitativa e impacto sobre lectura; añadir una evaluación adecuada antes de afirmar el resultado personal.

### [MENOR] H19. «Sin clave» se confunde con «sin red»

Dónde: `entrega/documento.md:800–803`; `entrega/estrategia.md:209–215`; `app/ui.py:1504–1515`; `app/catalogo.py:195–198`.

Qué dice: «audio de Wiktionary, buscador y puntuación, porque nada de eso usa red».

Por qué: el audio de Wiktionary se incrusta con una URL HTTP y el navegador necesita obtenerlo. No requiere clave de OpenAI, pero sí conectividad salvo caché ajena a esta garantía. La búsqueda también necesita disponer previamente del modelo de embeddings; no basta con el CSV. La separación entre explicación de pago y diccionario local sí existe.

Arreglo: especificar qué funciona sin clave, qué funciona sin conexión con recursos ya descargados y qué todavía requiere red.

### [MENOR] H20. Quedan errores aritméticos y comparaciones de versiones sin identificar

Dónde: `entrega/documento.md:381–382`, `591–593`, `719–722`, `838–845`, `849`; `entrega/notebook_proyecto.py:1646`; `informe_velocidad.md:92–126`, `187`.

Qué dice: «se encoge de seis niveles a cuatro (A2–C1)»; «1,39 niveles […] tanto con regresión logística como con XGBoost»; «+24 %».

Por qué: A1–C1 son **cinco** niveles iniciales. El Cuadro 7 da XGBoost **1,42**, no 1,39. La conclusión de saturación compara 18 → 45.345 libros pero empareja −0,330 con 18; esa correlación corresponde a **397**, y la de 18 es −0,379. CPU 6,16 → 8,19 es **+32,95 %**, no +24 %; falta identificar otra base si se usó. El documento cita 286/286 ventanas idénticas, el informe 300/300; pueden ser tandas distintas, pero no se documenta el cambio. El notebook dice fp16 4,5 veces más lento; la tabla del informe da 112,7/23,7 = **4,755**, consistente con 4,8 del documento. C1 local 1,4952 y Colab 1,4950 no coinciden hasta la cuarta cifra decimal; sí hasta la tercera.

Arreglo: corregir los cruces de fila y redondeos; identificar cada tanda y el denominador de cada porcentaje. No sustituir una medición por otra sin indicar su origen.

### [DUDA] H21. No se puede verificar la independencia ni recalcular las métricas de los 144 documentos

Dónde: `entrega/documento.md:560–572`, `781–788`; `entrega/notebook_proyecto.py:1522–1525`, `1842–1846`; `modelo_v4/`.

Qué dice: «Su tarjeta de modelo (`metricas_literalevel_v4.json`, 5 de septiembre de 2026) registra […] 654 documentos».

Por qué: no se localizó esa tarjeta en el repositorio ni el manifiesto de los 654 documentos, sus grupos o los 144 valores reales y predichos. En `modelo_v4` están configuración, pesos y tokenizadores. No puedo determinar si el split v4 es por documento, título, fuente o versión de una misma lectura; si comparte textos con British Council; ni si los 144 intervinieron en selección. 510 + 144 = 654 es coherente y 53,5 % / 97,2 % son compatibles, por redondeo, con 77/144 y 140/144. Eso no verifica Spearman 0,908 ni MAE 0,499. El inventario de fuentes del documento tampoco incluye una fila que identifique la procedencia de este corpus final.

Arreglo: incorporar tarjeta, revisión de pesos, procedimiento de partición y manifiesto por identificador/grupo/fuente. Publicar al menos etiquetas y predicciones por documento, junto con la definición exacta de «±1 nivel» y el redondeo utilizado, sin necesidad de redistribuir texto restringido.

### [DUDA] H22. Las velocidades finales tienen consistencia interna, pero falta su registro experimental

Dónde: `informe_velocidad.md:7–18`, `104–126`, `167–201`, `204–210`; `entrega/documento.md:704–711`; `entrega/datos_figuras/velocidad.dat:1–4`; `colab_precalculo.py:343–357`.

Qué dice: «Rendimiento medido de extremo a extremo» con 8,7 / 101,7 / 2.022 ventanas/s.

Por qué: documento, estrategia, notebook y `.dat` repiten esos tres valores. El informe de velocidad contiene **8,19 CPU y 112,7 GPU**, entre otras tandas, y termina con recomendación y extrapolación pendientes; no contiene la medición A100. El precálculo sí tiene una celda capaz de medirla, pero una celda sin su salida no acredita 2.022. No encontré en los materiales revisados una tabla final con entradas, lote A100 concreto, entorno, tiempos individuales y criterio de agregación que enlace las tandas. Las diferencias podrían ser perfectamente legítimas. No son motivo para acusar de cifras inventadas; sí impiden verificarlas como una única comparación reproducible.

Arreglo: adjuntar el registro de la tanda final y conservar las históricas con fecha y configuración. Separar mejor pasada, promedio y variación; identificar si se incluyen carga, tokenización, transferencias, extracción y descarga.

### [DUDA] H23. El baseline de longitud es pertinente; sus datos y la incertidumbre no están disponibles

Dónde: `entrega/documento.md:598–617`, `768–771`; `entrega/notebook_proyecto.py:1621–1627`; `validar_local.py:73–83`; `entrega/datos_figuras/validacion.dat:1–6`.

Qué dice: «Modelo, descontando la longitud (correlación parcial) […] 0,657»; «Una diferencia de 0,05 […] no es significativa».

Por qué: con los coeficientes redondeados publicados, la fórmula de correlación parcial da aproximadamente **0,6563**, compatible con 0,657 calculado con más precisión. Es una comprobación de consistencia, no un recálculo a partir de observaciones. Faltan las 45 longitudes, etiquetas y predicciones, la especificación de si se residualizaron rangos y los intervalos o contrastes. `validar_local.py` solo imprime medias y dispersión; el `.dat` conserva agregados. No puede verificarse ni la diferencia 0,854 frente a 0,807 ni la afirmación formal de ausencia de significación. Además, al controlar una variable idéntica al propio contador, su correlación parcial no «se queda en cero»: el residuo del contador es constante y esa correlación no está definida.

Arreglo: proporcionar una tabla numérica por documento y el cálculo exacto, con incertidumbre apropiada; cambiar «no significativa» por «no se evaluó su significación» si no existe contraste. Retirar la comparación con una correlación parcial nula del contador.

### [DUDA] H24. La rúbrica sirve como lista de requisitos, pero su estado de entrega está desactualizado

Dónde: `.claude/skills/modulo-5-literalevel/SKILL.md`, apartados 1, 2, 5 y 9; `entrega/`.

Qué dice: «Documento […] no empezado»; «Falta el notebook limpio del proyecto»; «debe correr desde cualquier Colab sin errores ni warnings».

Por qué: documento, estrategia y notebook existen; esas marcas de estado no reflejan el repositorio examinado. Sí se comprueba la estructura documental exigida, la estrategia con usuarios/usabilidad/acciones y un notebook organizado con EDA y modelado. No se ha acreditado la ejecución limpia exigida, y la omisión controlada de modelos no demuestra reproducibilidad completa. No se verificaron una demo remota, un vídeo final ni una presentación entregada; no corresponde deducir su inexistencia fuera del repositorio. Los puntos y requisitos se toman de la rúbrica suministrada, no de una comprobación con el profesor.

Arreglo: actualizar la matriz de estado con enlaces a los entregables y evidencias de ejecución; comprobar por separado demo, vídeo y presentación antes de declarar la entrega completa.

## 2. Lo comprobado que sí se sostiene

Estas comprobaciones delimitan los hallazgos: no todo está mal ni todo está sin revisar.

| Comprobación | Resultado y evidencia |
|---|---|
| Transformación numérica pública | `app/scoring.py:96–98` aplica exactamente `clip(y,0,5)*0.4`. El desacuerdo está en bandas, empates y agregación, no en el factor 0,4. |
| Corpus de las métricas principales | El cuerpo del documento sí separa CLEAR en §7.1–7.3 y el v4/654 documentos en §7.4. **No atribuye explícitamente 0,908 a CLEAR.** El notebook separa la fila v4 y advierte que no es comparable (`1548–1552`). Hay confusión conceptual de etiquetas, pero no debe inventarse una mezcla numérica que no aparece. |
| Partición por título | El notebook usa `GroupShuffleSplit` sobre `Title`, semilla 42, y calcula la intersección. El histórico utiliza los mismos índices para clásicos, embeddings y transformer. Esto está bien implementado por lectura; no se recalculó la partición sin CLEAR local. Agrupar por título no acredita separación por autor o duplicados bajo títulos distintos. |
| Escalador predictivo | `StandardScaler` de los modelos nuevos se ajusta en train (`1060`). El PCA global se usa en EDA y no alimenta esos modelos; no lo clasifico como fuga directa a sus predicciones. La fuga del vocabulario es otra ruta. |
| Baseline real | Media de entrenamiento y clase mayoritaria están implementadas; la correlación de la predicción constante se marca «no aplica». El contador de palabras se reporta aunque se acerque al v4. No sería correcto concluir «no hay baseline». |
| Catálogo heredado | Recuento independiente con `Import-Csv`: **1.197 registros**, A1 723, A2 185, B1 69, B2 52, C1 53, C2 115. Suma 1.197; B1+B2 = 121. StoryWeaver/GDL tiene 1.049 registros y quedan 148. No se contó por saltos de línea. |
| Porcentajes del catálogo | A1 = 60,401 %; B1+B2 = 10,109 %; StoryWeaver = 87,636 %. Los porcentajes del Cuadro 3 redondean coherentemente y suman 100,0 %. La distribución no demuestra por sí sola que las etiquetas sean erróneas; sí coincide con el CSV. |
| Dimensiones de los pesos | Lectura de cabecera safetensors, sin cargar el modelo: **82.119.169 elementos de parámetros**, incluida cabeza `classifier`; archivo **328.489.204 bytes**. La aproximación de 82 millones y 328 MB decimales es correcta. `config.json` declara seis capas y regresión. Esto no valida su calidad. |
| Validación agregada de figura | `validacion.dat` reproduce n = 3, 7, 12, 11, 12 y medias 0,5040; 0,5480; 0,9276; 1,2478; 1,4952. Suman 45 y las medias crecen estrictamente. Se verificó la tabla, no las predicciones que la originaron. |
| Proporciones de evaluación | 510+144 = 654; con 57 descartes el total previo sería 711. 53/59 = 89,831 %, coherente con 89,8 %. 53,5 % y 97,2 % de 144 admiten conteos enteros coherentes. |
| Razones de velocidad | 101,7/8,7 = 11,6897; 2.022/8,7 = 232,4138. El 11,7× y el 232× están bien redondeados. 61.642/0,3/3.600 = 57,076 horas de descarga serial, coherente con 57 horas. |
| Precisión CPU/GPU declarada | Una diferencia de 0,001 entre 840 ventanas y 839 idénticas implica MAE de 0,0000011905 sobre los valores comparados, compatible con 0,0000012. No se volvieron a comparar los vectores. |
| Funciones de producto presentes | Hay ocho pestañas (`app/ui.py:1990–2289`), seis preguntas y tres fragmentos (`app/perfil.py`), apertura de libros, búsqueda multilingüe, consulta léxica, práctica de voz, biblioteca, cuaderno y cambio de paleta. Se identificaron manejadores reales; no son meros nombres en el documento. No se ensayó su funcionamiento de extremo a extremo. |
| Carga diferida y modos | Los accesores de recursos pesados son diferidos (`app/ui.py:325–349`). Existen el modo rápido de 30 capítulos × 2 ventanas y el completo sin tope de ventanas, con avisos distintos. La docstring que todavía dice 40 capítulos no gobierna la constante ejecutada. |
| Separación entre definición y explicación | La arquitectura obtiene la definición del diccionario y reserva la llamada generativa para contexto/gramática; existe manejo de ausencia de clave. Se verificó la intención y la ruta de código, no el cumplimiento lingüístico de todas las respuestas. |
| Limitaciones explícitas | El documento declara compresión, catálogo heredado, n pequeña, falta de independencia externa, artefactos no publicados, enlace temporal e impacto sin medir. Son limitaciones concretas útiles, aunque algunas contradicen formulaciones más fuertes del resumen o del notebook. |
| Fuente pública de CLEAR | El archivo citado existe en el [repositorio público de los autores](https://github.com/scrosseye/CLEAR-Corpus). No se detectó una descarga desde Kaggle en el notebook entregado. Mencionar un concurso como antecedente en el histórico no equivale a usarlo como fuente de datos. |

## 3. Correspondencia de escala reconstruida

La tabla siguiente distingue magnitudes que la entrega trata a veces como si fueran la misma. Los intervalos son los de la **UI actual**, con empate hacia arriba, para una puntuación pública exacta.

| Pública | Letra UI | Banda actual `public_band` |
|---|---|---|
| [0,00; 0,20) | A1 | básico |
| [0,20; 0,60) | A2 | básico |
| [0,60; 1,00) | B1 | intermedio |
| [1,00; 1,40) | B2 | intermedio |
| [1,40; 1,80) | C1 | avanzado |
| [1,80; 2,00] | C2 | avanzado |

`escala_cefr.dat` contiene esos límites, pero no la convención de inclusión. En el texto final no se localizó una tabla completa de seis intervalos que defina los empates; sí aparecen las bandas antiguas. Por tanto, la respuesta al encargo de «¿son los mismos cortes?» es: **el factor de escala sí; los límites numéricos de letras entre figura y UI sí; las bandas entre documentación y código no; los empates entre `anchor_cefr` y UI tampoco**.

| Empate público | Interno exacto | `anchor_cefr(interno)` | `_cefr(público)` |
|---|---:|---|---|
| 0,20 | 0,5 | A1 | A2 |
| 0,60 | 1,5 | B1 | B1 |
| 1,00 | 2,5 | B1 | B2 |
| 1,40 | 3,5 | C1 | C1 |
| 1,80 | 4,5 | C1 | C2 |

Los resultados de esta tabla se reconstruyeron con las reglas matemáticas del código y redondeo al par en .NET, contrastado con la documentación de Python. No se presentan como una ejecución de `Puntuador`. Al evaluar casos cercanos a las fronteras hay que considerar también que `Resultado.puntuacion` se redondea a tres decimales y la UI imprime dos, mientras la banda se determina antes de ese redondeo.

## 4. Veredicto final — una página

**LiteraLevel es un prototipo de producto sustantivo cuya evidencia científica está peor cerrada que su interfaz.** Hay pesos reales, un sistema de lectura implementado, fuentes identificadas para buena parte del trabajo, baselines efectivos y un esfuerzo explícito por reconocer limitaciones. El recuento del catálogo, las dimensiones del modelo, el factor de escala y varias razones de rendimiento resisten la comprobación. La estructura del documento y de la estrategia responde en buena medida a la rúbrica. No corresponde reducir todo esto a una demostración ficticia ni afirmar que no existe evaluación.

**Lo que no se sostiene es presentar la cadena experimental como una prueba independiente y completamente reproducible.** Los 950 extractos de CLEAR también seleccionaron la época del transformer. El vocabulario del test interviene en varios modelos del notebook. Los sextiles de facilidad reciben nombres MCER sin una calibración que justifique esa equivalencia. El PCA no demuestra el techo predictivo que se le atribuye. Estos puntos afectan al significado de los resultados y deben corregirse antes de entregar, no relegarse a una nota de estilo. Para los 144 documentos del v4 falta evidencia suficiente: 0,908 puede ser correcto, pero esta auditoría no puede certificarlo ni verificar que la evaluación fuera ciega.

**La primera prioridad es ajustar las afirmaciones a la evidencia disponible.** Separar claramente el experimento histórico sobre CLEAR, la reproducción clásica nueva, el entrenamiento MCER del v4 y la evaluación externa explorada. Identificar las cifras reportadas frente a las recalculadas. Conservar las métricas históricas como resultados de validación de selección cuando corresponda. Publicar tarjeta, identificadores de partición y predicciones numéricas permitiría una auditoría mucho mejor sin redistribuir textos restringidos ni reentrenar el modelo final.

**La segunda prioridad es conseguir que todos los entregables describan el mismo producto.** Hay que unificar bandas y empates, explicar el recorte por bloque y resolver o declarar la diferencia entre media de ventanas y media de capítulos. La estimación de 6,3 horas necesita un supuesto verificable; el cálculo entregado da 2,96. Los rendimientos de lotes agrupados no deben atribuirse automáticamente al manejador que procesa capítulos separados. El vistazo de 30×2 no queda validado por un ensayo de 8 ventanas en un capítulo. También deben declararse las muestras de la ficha y las velocidades de lectura supuestas.

**La tercera prioridad es aportar evidencia de ejecución.** Publicar pesos no recalcula por sí solo las métricas. Se necesita una corrida limpia del notebook, dependencias y artefactos identificables y un validador que falle ante un corpus vacío. Las pruebas que devuelven listas de errores deben dejar de contarse como éxito. Para la rúbrica, demo remota, vídeo y presentación requieren comprobación propia; esta auditoría no los da por terminados ni por inexistentes.

**Es opcional para esta entrega** explorar nuevas arquitecturas, añadir variables o ampliar el catálogo hasta su máximo teórico. La validación con más lectores, más libros y un conjunto externo verdaderamente reservado mejoraría la evidencia, pero no es necesario prometerla como trabajo ya realizado. El proyecto puede defenderse como herramienta funcional con resultados preliminares y límites precisos. **No debería entregarse aún con las afirmaciones actuales de independencia, techo de las métricas clásicas, uniformidad de escala y reproducibilidad completa.**
