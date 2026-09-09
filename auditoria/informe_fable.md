# Auditoría externa de LiteraLevel — informe

**Auditor:** externo (Fable). **Fecha:** 8 de septiembre de 2026.
**Método:** `.claude/skills/auditar-proyecto-datos/SKILL.md` (seis frentes por daño, conclusiones primero, documento contra código).
**Regla:** no se modificó ningún archivo del proyecto. No se leyó nada de `auditoria/` salvo para escribir esto.

Lo que se leyó: `entrega/documento.md` (resumen, 2.3, 4, 7, 8.2–8.4, 9–11 y declaración de alcance), `entrega/estrategia.md` (por búsqueda), `entrega/notebook_proyecto.py` (partición, rasgos, Zipf, validación externa, reproducibilidad), `app/scoring.py` entero, `app/ficha.py` (filtro y agregación), `validar_local.py` entero, `pruebas_extremas.py` (envoltorio y pruebas 760–881), `informe_velocidad.md` entero, la rúbrica, y para verificar: `notebook_v4_dump.py`, `modelo_v4/README.md`, `investigacion/transformer_v5.md`, `investigacion/acelerar_precalculo.md`, `colab_precalculo.py`, `arrancar_gpu.py`, `README.md`, `requirements.txt`, `app/ui.py` (conteo de pestañas). Se ejecutó código propio contra `app/scoring.py` y `app/paletas.py` para recalcular bandas, letras y contraste.

**Recuento:** 2 CRÍTICO · 8 SERIO · 9 MENOR · 5 DUDA.

---

## CRÍTICO

### [CRÍTICO] El Cuadro 8 evalúa v2 sobre los textos con los que se afinó v2
**Dónde:** `entrega/documento.md:560` y `:568`; `notebook_v4_dump.py:2219`, `:2236`, `:2392–2395`, `:2415`.
**Qué dice:** «v2 afinado sobre material graduado para aprendices» (doc:560) y «| Periodístico (OneStopEnglish) | 567 | 0,458 | **0,840** |» (doc:568). En el volcado: «modelo v2 (afinado con OneStopEnglish, ranking pairwise) guardado» (dump:2219); «continuar el entrenamiento del RoBERTa de produccion usando los propios textos de OneStopEnglish, sin volver a usarlos despues como validacion (para evitar data leakage)» (dump:2236). La partición fue 151 artículos de entrenamiento y 38 reservados (dump:2210, 2255). Pero la celda que produce la fila del Cuadro 8 hace `ose_v2 = puntuar_doc(m2, rutas_ose)` sobre **las 567 rutas** (dump:2392) y de ahí sale «| Periodistico (OneStopEnglish) | 567 | 0.458 | **0.840** | v2 |» (dump:2415).
**Por qué:** el 0,840 de v2 está medido en un conjunto del que el 80 % (453 de 567 textos) fue su propio entrenamiento. La conclusión de 7.3 —«v2 gana donde la etiqueta es una graduación pensada para aprendices»— se apoya en un número de entrenamiento comparado con un número de test (v1 no vio OneStop). Además, el documento no dice en ningún sitio que v2 se afinó con OneStopEnglish: lo llama «material graduado para aprendices» y en el Cuadro 2 (doc:208) etiqueta OneStopEnglish como «Validación externa ordinal en 3 niveles». El volcado sí contiene una evaluación limpia sobre los 114 textos reservados (dump:2228) que es la que debería figurar.
**Arreglo:** sustituir la fila de OneStop del Cuadro 8 por la métrica sobre los 114 textos reservados (o retirar la fila), declarar en 4.1 y 7.3 que OneStopEnglish fue corpus de afinado de v2, y reescribir la lectura de 7.3 en consecuencia. La «prueba dentro de cada artículo» prometida en doc:232 nunca se reporta: o se reporta o se quita la promesa.

### [CRÍTICO] El corpus de anclaje del v4 incluye British Council según el cuaderno; el documento lo presenta como «corpus externo que nunca vio»
**Dónde:** `entrega/notebook_proyecto.py:1970–1972` frente a `entrega/documento.md:33`, `:600`, `:611–620` y `notebook_proyecto.py:1658`.
**Qué dice:** el cuaderno, en 9.3: «depende del **corpus de anclaje MCER**, 654 documentos que incluyen material con derechos —los exámenes de British Council entre ellos— que no se puede redistribuir». El documento, en el Resumen: «sobre un corpus externo que nunca vio, ordena los niveles del Marco Común Europeo de forma estrictamente creciente»; Cuadro 9: «| British Council (externo) | 38 |»; y el cuaderno en 7.2: «textos con nivel MCER oficial, de una fuente ajena al proyecto, que el modelo nunca vio».
**Por qué:** las dos afirmaciones no pueden ser ciertas a la vez. Si los textos de British Council están entre los 654 documentos (510 de entrenamiento + 144 de validación), la «validación externa» está midiendo, al menos en parte, textos de entrenamiento, y el resultado que el propio documento llama «el que sostiene el trabajo» (doc:606–608) deja de ser externo. Si no lo están, el cuaderno afirma algo falso sobre el corpus en la sección que explica por qué no se puede reproducir. La composición del corpus de anclaje no está en ningún archivo del repositorio: `modelo_v4/README.md:97–98` dice solo «un corpus de documentos anclados a niveles MCER» y la tarjeta `metricas_literalevel_v4.json` citada en doc:591 no existe en el repo. Hay indicios circunstanciales de que sí están: 57 documentos «descartados por longitud insuficiente» (doc:593) encaja con los textos A1 fragmentarios de British Council descritos en 4.3(a), y la limitación 6 (doc:812–817) reconoce que el corpus «se usó primero para diagnosticar».
**Arreglo:** publicar la lista de fuentes del corpus de anclaje (nombre, n por fuente, n por nivel) y la regla de partición. Si British Council está dentro, retirar «externo» y «nunca vio» de Resumen, 2.3 (criterio C1), 7.4, 11 y del cuaderno, y reportar la fila de British Council como lo que sea (validación interna o entrenamiento). Si no está dentro, corregir `notebook_proyecto.py:1971`.

---

## SERIO

### [SERIO] El documento se contradice sobre si el filtro de prosa se fijó antes o después de ver resultados, y el guion local aplica un tercer filtro distinto
**Dónde:** `entrega/documento.md:258–262` y `:679` frente a `:812–817`; `validar_local.py:18`, `:67–70`.
**Qué dice:** 4.3(a): «Se definió un filtro de prosa continua **antes de mirar ningún resultado** … por dos vías independientes: por palabras clave del título y por estructura (≥7 palabras por línea y densidad de puntuación … (0, 0,11])». Cuadro 12: «El criterio se fijó a priori». Limitación 6: «El corpus de British Council se usó primero para diagnosticar (descubrir que el modelo no sabe leer menús) y después para validar».
**Por qué:** «descubrir que el modelo no sabe leer menús» es mirar resultados; el filtro que excluye menús se definió después de eso, no antes. Además, el Cuadro 8 (doc:569) evalúa v1/v2 sobre los 59 textos completos, sin filtro. Y `validar_local.py` no aplica ninguna de las «dos vías»: aplica `scoring.continuous_prose` (línea 18, vía `p.puntuar` en 67) más un anclaje «Reading text … Tasks», y descarta por `except Exception` (68–70). Los 45 textos del Cuadro 10 sobreviven a un filtro que no es el descrito en 4.3(a).
**Arreglo:** reescribir 4.3(a) y el Cuadro 12 con la secuencia real (se vio el fallo, se fijó el filtro, se validó), y describir en 7.4 el filtro que de verdad produce los 45 textos.

### [SERIO] Las cifras de velocidad del Cuadro 14 y de las conclusiones no están en el informe de velocidad, y el repositorio da tres factores distintos para la misma medida
**Dónde:** `entrega/documento.md:747–748`, `:895`; `informe_velocidad.md:115–117`, `:134`, `:181`; `app/scoring.py:207–208`; `arrancar_gpu.py:13–14`.
**Qué dice:** doc: «| CPU (Ryzen 5 2600) | 12 hilos, lote 64 | 8,7 | 1× |», «| GPU local … | fp32, lote 128 | 101,7 | 11,7× |», y en 11: «+24 % y ×11,7 respectivamente». `informe_velocidad.md`: lote 64 = **8,19** v/s (línea 115), lote 300 = 8,53 (134), GPU fp32 lote 128 = **112,7** v/s (181). `scoring.py:207`: «112,7 ventanas/s frente a 8,19 en CPU, dieciocho veces mas rapido».
**Por qué:** el 8,7 y el 101,7 del Cuadro 14 solo aparecen en la cadena de documentación de `arrancar_gpu.py:13–14`, no en el informe de mediciones que el documento cita como respaldo. Con los números del informe, el factor es 112,7/8,19 = 13,8×, no 11,7×; y el «dieciocho veces» de `scoring.py` es 112,7/6,16, es decir, contra la línea base *sin* lotes ni hilos. El «+24 %» no se deriva de ninguna pareja publicada (8,19/6,96 = +18 %; 8,19/6,16 = +33 %; 8,7/6,96 = +25 %). Tres cifras para un mismo hecho medido es una cifra que no se sabe cuál es.
**Arreglo:** elegir una tanda de medición, ponerla en `informe_velocidad.md` con fecha y condiciones, y hacer que documento, `scoring.py` y `arrancar_gpu.py` citen esa y solo esa.

### [SERIO] Las «6,3 horas de A100» las contradice el propio repositorio
**Dónde:** `entrega/documento.md:47`, `:765–766`; `investigacion/acelerar_precalculo.md:62–67`; `colab_precalculo.py:360`.
**Qué dice:** doc: «Con 2.022 ventanas por segundo, **medir los 61.642 libros en inglés de Project Gutenberg son unas 6,3 horas de A100**». `acelerar_precalculo.md`: «**la estimación de «6,3 horas de A100» para el catálogo entero no cuadra con 2.022 ventanas/s.** 61.552 libros × 350 ventanas/libro ÷ 2.022 v/s ÷ 3.600 = **2,96 h** … Para que salgan 6,3 h hacen falta o **950 ventanas/s** o **745 ventanas por libro**». `colab_precalculo.py:360`: «VENTANAS_POR_LIBRO = 350  # media razonable».
**Por qué:** la cifra que abre el Resumen sale de un supuesto (350 ventanas/libro, no medido) y ni siquiera con ese supuesto da 6,3. El documento dice 61.642 libros; el código y la investigación, 61.552.
**Arreglo:** calcular la media real de ventanas por libro sobre los libros ya medidos (el propio `acelerar_precalculo.md:70–77` da el código) y rehacer la estimación; unificar 61.642/61.552.

### [SERIO] Cuadro 11 y la recta de compresión no los calcula ningún código del repositorio, y hay dos versiones de la recta y dos Spearman «externos»
**Dónde:** `entrega/documento.md:629–635`, `:642`, `:646`, `:600`; `validar_local.py` (entero); `entrega/notebook_proyecto.py:1721–1728`; `investigacion/transformer_v5.md:261`.
**Qué dice:** doc: «| Modelo v4 | **0,854** | … | Contar las palabras … | 0,807 | … | correlación parcial | **0,657** |», «su salida correlacione 0,730 con ella», «`predicho ≈ 0,72 × real + 0,38`». `transformer_v5.md:261`: «`real ≈ (pred − 0,359)/0,714`», es decir, pred ≈ 0,714·real + 0,359. Cuadro 9: British Council Spearman **0,829** (n=38).
**Por qué:** `validar_local.py` imprime medias y desviaciones por nivel y el booleano de orden; no calcula Spearman, ni correlación con la longitud, ni correlación parcial, ni ajuste lineal. El cuaderno solo los menciona en Markdown. El criterio de éxito C2 (doc:156, «Correlación parcial descontando la longitud») queda sin experimento visible. Dos rectas distintas (0,72/0,38 y 0,714/0,359) y dos Spearman «externos» (0,829 con 38, 0,854 con 45) circulan por documento, README y tarjeta sin que se diga cuál es cuál.
**Arreglo:** añadir a `validar_local.py` el cálculo de Spearman, longitud, parcial y la recta, y que el documento cite esa salida con su n. Decir en el Cuadro 9 que el 0,829 es la tanda de Colab (38, sin A1) y el 0,854 la local (45).

### [SERIO] La «validación externa ciega» del cuaderno es una tabla tecleada a mano, y su figura traza los cortes viejos
**Dónde:** `entrega/notebook_proyecto.py:1654–1676`, `:1689–1690`, `:1701`.
**Qué dice:** «## 7.2 Validación externa ciega … `validacion_externa = pd.DataFrame({"Nivel oficial": [...], "n": [3, 7, 12, 11, 12], "Media v4 (escala 0-2)": [0.5040, 0.5480, 0.9276, 1.2478, 1.4952]})` … `print("Orden estrictamente creciente de A1 a C1:", all(a < b ...))`». Luego «`plt.axhline(0.8, …)` `plt.axhline(1.6, …)`» y el pie: «Las líneas punteadas son los cortes de las bandas públicas: 0,6 y 1,4».
**Por qué:** la celda imprime «True» sobre constantes escritas por el autor; no ejercita el modelo ni el corpus. Se entiende que el corpus no se puede redistribuir (y 9.3 lo dice con honestidad), pero la sección se titula «validación» y el lector de un cuaderno espera que una celda que imprime un resultado lo haya calculado. La figura dibuja 0,8 y 1,6 (los cortes que el documento dice haber corregido) mientras el pie afirma 0,6 y 1,4: el código y el texto se contradicen en la «curva que sostiene el proyecto».
**Arreglo:** titular la celda como «cifras citadas de `validar_local.py`, no recalculadas aquí» (o cargarlas de un CSV generado por ese guion) y corregir las dos `axhline` a 0,6 y 1,4.

### [SERIO] El orden A1 < A2 descansa en tres textos y 0,044 de diferencia; en Colab no hubo A1, y el Resumen presenta las cinco medias sin la n
**Dónde:** `validar_local.py:74`; `entrega/documento.md:33–36`, `:611–612`, `:622`, `:875–878`.
**Qué dice:** `esperado = {"A2": 0.6479, "B1": 0.9513, "B2": 1.2883, "C1": 1.4950}` —sin A1—. Doc, Resumen: «A1 0,5040 · A2 0,5480 · B1 0,9276 · B2 1,2478 · C1 1,4952. Ese orden … es el resultado que sostiene el trabajo». Cuadro 10: «| A1 | 3 | 0,5040 |». Conclusiones: «ordena los niveles de forma estrictamente creciente (0,5040 · 0,5480 · …)».
**Por qué:** la tanda de Colab (n=38) no tenía nivel A1; el «orden estrictamente creciente en los cinco niveles» solo se ha observado en local, donde A1 son 3 textos y la distancia A1–A2 es 0,044 (la desviación por nivel que imprime el guion no se reporta en el Cuadro 10). La limitación 5 (doc:807–811) lo reconoce; el Resumen, el Cuadro 9 y las Conclusiones no, y citan las cinco cifras locales como si fueran «la» validación externa. Además, «C1 coincide hasta la cuarta cifra» (doc:622) es falso: 1,4952 frente a 1,4950 coincide hasta la tercera.
**Arreglo:** en Resumen y Conclusiones, dar la n por nivel o limitarse a «orden creciente en cuatro niveles con n ≥ 7 y en A1 con n = 3»; reportar la desviación por nivel en el Cuadro 10; corregir «cuarta» por «tercera».

### [SERIO] La tarjeta del modelo citada como fuente de 0,908 y 97,2 % no está en el repositorio, y no se dice cómo se partió el corpus de anclaje
**Dónde:** `entrega/documento.md:591–597`, `:822–825`; `modelo_v4/README.md:67–70`, `:97–100`.
**Qué dice:** doc: «Su tarjeta de modelo (`metricas_literalevel_v4.json`, 5 de septiembre de 2026) registra el corpus de anclaje … 510 de entrenamiento y 144 de validación». `modelo_v4/README.md` repite las cifras y describe el corpus solo como «un corpus de documentos anclados a niveles MCER».
**Por qué:** `find . -name "metricas_literalevel_v4*.json"` no devuelve nada fuera de `auditoria/`. Las dos cifras centrales del modelo desplegado se citan de un archivo que el lector no puede abrir. Tampoco se dice si la partición 510/144 es por documento o por grupo: si el corpus contiene versiones del mismo texto a varios niveles (como OneStopEnglish, que `transformer_v5.md:134` dice que *no* se usa, o material de examen con variantes), una partición por fila filtra contenido al conjunto «ciego». Con CLEAR el proyecto sí lo hizo bien (véase «Lo que está bien»); con el corpus que importa no se puede saber.
**Arreglo:** incluir la tarjeta JSON en el repo (o en `modelo_v4/`), y añadirle fuentes, n por fuente y nivel, y la regla de partición.

### [SERIO] Las pruebas sustantivas de `pruebas_extremas.py` no pueden fallar: devuelven la lista de violaciones como éxito
**Dónde:** `pruebas_extremas.py:37–50`, `:788`, `:811`, `:834`, `:862`, `:866–870`; `entrega/estrategia.md:132`.
**Qué dice:** «def prueba(nombre, fn): "Ejecuta `fn`. Que devuelva algo es exito; que lance, es fallo."». `_contraste_suficiente` termina en «return malas or "las cinco pasan AA"»; `_bandas_coherentes` en «return malas[:5] or "las 201 puntuaciones concuerdan"»; `_una_sola_letra` en «return malas[:5] or "las 50.001 coinciden"»; `_agregacion_por_ventanas` en «return malas[:3] or "500 libros sinteticos, …"». «el caso que destapo la auditoria» es `lambda: ui.ficha.dificultad_global([...])` sin comparar con 1,8. Estrategia: «Una prueba automática comprueba las cinco contra el criterio de contraste **WCAG AA (4,5:1)**. Las cinco pasan; la peor mide **9,51**».
**Por qué:** si una paleta bajara de 4,5:1, `malas` sería una lista no vacía, la función la devolvería y `prueba()` imprimiría «ok» con la lista como resumen. Lo mismo para bandas, letras y agregación. De 191 llamadas a `prueba(`, 180 son lambdas que solo comprueban que un manejador no lanza excepción; de las 12 funciones con nombre, 6 tienen `assert`. La línea final es honesta («ningun manejador lanzo excepcion»), pero la estrategia presenta la batería como prueba de que las paletas *pasan*, y la batería no puede decir lo contrario. **He recalculado las cuatro comprobaciones por mi cuenta y las afirmaciones son ciertas** (peor contraste 9,51 en *menta*/interfaz; 0 incoherencias banda–letra en 201 puntos; 0 desacuerdos letra pública/interna en 50.001 puntos; cortes en 0,6 y 1,4). El problema es la prueba, no el hecho.
**Arreglo:** `assert not malas, malas` en las cuatro funciones y una comparación explícita (`== 1.8`) en el caso de la auditoría.

---

## MENOR

### [MENOR] Las conclusiones dan a XGBoost el error ordinal de la regresión logística
**Dónde:** `entrega/documento.md:884` frente a `:527–528`.
**Qué dice:** «tres variables clásicas dan 1,39 niveles de error ordinal tanto con regresión logística como con XGBoost». Cuadro 7: LR 1,39; «| XGBoost | 3 variables clásicas | 0,28 | 1,42 |».
**Por qué:** 1,42 ≠ 1,39. El Cuadro 12 (doc:671) sí dice «1,42 vs 1,39».
**Arreglo:** «1,39 y 1,42».

### [MENOR] 286 ventanas en el documento, 300 en el informe y en `scoring.py`
**Dónde:** `entrega/documento.md:762–763`; `informe_velocidad.md:122–124`; `app/scoring.py:240–242`.
**Qué dice:** doc: «286 ventanas puntuadas de una en una y en un solo lote dan 286/286 valores idénticos». Informe: «las mismas 300 ventanas … 300/300 valores idénticos bit a bit». `scoring.py`: «las mismas 300 ventanas … 300/300».
**Por qué:** 286 es el conjunto del barrido de hilos (informe §3.a), no el del reagrupado.
**Arreglo:** 300.

### [MENOR] fp16 «4,8×» en el documento, «cuatro veces y media» en el código
**Dónde:** `entrega/documento.md:676`; `app/scoring.py:212–213`; `informe_velocidad.md:181–183`.
**Qué dice:** doc y informe: «4,8× más lenta»; `scoring.py`: «CUATRO VECES Y MEDIA MAS LENTA».
**Por qué:** 35,48/7,45 = 4,76 (lote 128) y 36,70/8,47 = 4,33 (lote 16). El 4,8 es correcto para lote 128; el comentario del código redondea otra cosa.
**Arreglo:** unificar en 4,8× (lote 128).

### [MENOR] `validar_local.py` silencia cualquier excepción y la reporta como «sin cuerpo localizable»
**Dónde:** `validar_local.py:67–70`, `:80`.
**Qué dice:** «`r = p.puntuar(texto)` / `except Exception as e: saltados += 1; continue`» y «`print(f"\ntextos omitidos (sin cuerpo localizable): {saltados}")`».
**Por qué:** un `ValueError` del filtro de prosa, un fallo de `pypdf` y un fallo del modelo se cuentan igual y bajo un rótulo que solo describe el primero de los tres casos. La n=45 del Cuadro 10 depende de qué se descartó y por qué, y el guion no lo dice.
**Arreglo:** contar por motivo (`corto`, `pocas_frases`, `maquetado_de_lista`, error de PDF, otro) e imprimirlos.

### [MENOR] `puntuar()` muestrea como máximo 8 ventanas y el documento no lo dice al describir el estimador
**Dónde:** `app/scoring.py:21`, `:90–92`, `:293`; `entrega/documento.md:586–587`; `.claude/skills/modulo-5-literalevel/SKILL.md:156–157`.
**Qué dice:** `MAX_BLOCKS_PER_DOC = 8`; en `fixed_blocks`: «if len(inicios) > cap: idx = np.linspace(0, len(inicios) - 1, cap)». Doc: «Puntúa bloques de 250 palabras truncados a 256 tokens y promedia sin ponderar». Rúbrica: «8 ventanas dan 1.784 y el recorrido completo 1.743».
**Por qué:** la validación (vía `puntuar`) usa ≤ 8 ventanas repartidas; el catálogo (vía `perfil_de_texto`) usa todas. Son dos estimadores que difieren en 0,04 sobre un libro real, y 7.4 describe uno solo. Para los textos cortos de British Council no importa; para los 144 del corpus de anclaje no se sabe.
**Arreglo:** una frase en 7.4: «hasta 8 ventanas repartidas por documento en validación; todas en el catálogo».

### [MENOR] Versión de Gradio afirmada pero no fijada; mensaje de error del modelo apunta a Drive y no a Hugging Face
**Dónde:** `entrega/documento.md:43–44`; `requirements.txt:5`; `app/scoring.py:183–186`.
**Qué dice:** doc: «ocho pestañas en Gradio 6.26»; `requirements.txt`: «gradio>=6.0»; `scoring.py`: «Descarga la carpeta 'modelo_literalevel_v4_transformer' de Drive (literalevel_bigdata)».
**Por qué:** quien clone el repo instalará la Gradio que haya ese día, y si le falta el modelo el código le manda a un Drive privado mientras el documento (limitación 11) dice que está en HF público.
**Arreglo:** `gradio==6.26.x` y mensaje con el repo de HF.

### [MENOR] `informe_velocidad.md` está sin terminar y razona con los cortes viejos
**Dónde:** `informe_velocidad.md:204–210`, `:158–160`.
**Qué dice:** «## 4. Recomendación / _(pendiente)_ / ## 5. Extrapolación / _(pendiente)_»; «cruza de "avanzado" a "intermedio" (el corte está en 1,6)».
**Por qué:** el documento cita este informe como respaldo de mediciones (doc:745–763) y el informe no tiene recomendación ni extrapolación; el argumento del int8 usa el corte 1,6 que 7.5 dice haber sustituido por 1,4. El documento recalcula el efecto (52 %/21 %) correctamente, pero el informe fuente queda desactualizado.
**Arreglo:** completar §4–5 o marcar el informe como «mediciones brutas, sin recomendación»; actualizar la nota del corte.

### [MENOR] El número de libros del catálogo cambia entre documento y código
**Dónde:** `entrega/documento.md:47`, `:765`; `colab_precalculo.py:222`; `investigacion/acelerar_precalculo.md:65`.
**Qué dice:** doc: «61.642 libros»; código e investigación: «61.552».
**Arreglo:** una cifra, con su fecha de catálogo.

### [MENOR] Dos rectas de compresión distintas en el repositorio
**Dónde:** `entrega/documento.md:646`; `app/scoring.py:108`; `investigacion/transformer_v5.md:261`.
**Qué dice:** «0,72 × real + 0,38» (doc, código) frente a «(pred − 0,359)/0,714» (investigación).
**Por qué:** la pendiente coincide en redondeo; la ordenada (0,38 vs 0,359) no. Sin el código que la ajusta no se puede saber cuál es la buena (véase el SERIO sobre el Cuadro 11).
**Arreglo:** la que salga del guion.

---

## DUDA

### [DUDA] Si los 59 textos de British Council están, literalmente, entre los 654 del corpus de anclaje
**Dónde:** `entrega/notebook_proyecto.py:1971`; ausencia de la tarjeta JSON y del guion de entrenamiento (doc:822–824: «el guion de entrenamiento del v4 vive en Google Drive, no en el repositorio»).
**Por qué:** es la pregunta de la que depende el segundo CRÍTICO y no hay archivo en el repositorio que la responda. Lo señalo como duda porque no lo pude verificar; lo he elevado a crítico porque cualquiera de las dos respuestas invalida una afirmación publicada.

### [DUDA] Si la partición 510/144 del corpus de anclaje es por grupo
**Dónde:** `entrega/documento.md:593–597`; `modelo_v4/README.md:97–100`.
**Por qué:** ningún archivo lo dice. Con CLEAR se partió por `Title` (verificado); con el corpus que produce el 0,908, no consta.

### [DUDA] Las 2.022 ventanas/s y la desviación fp16 de 0,00037 en A100
**Dónde:** `entrega/documento.md:676`, `:749`; `colab_precalculo.py:322–349`, `:352–363`.
**Por qué:** el código mide sobre 300 ventanas de 5 libros con lote 256 y el informe local no lo cubre (`informe_velocidad.md:14`: torch CPU-only). Es plausible y está instrumentado; no lo pude reproducir aquí. El «+24 %» de doc:895 tampoco lo pude derivar de ninguna pareja de cifras publicada.

### [DUDA] Que el transformador del Cuadro 7 use exactamente la misma partición que los siete modelos clásicos
**Dónde:** `entrega/documento.md:506–509`; `notebook_v4_dump.py:415–417`, `:545–547`.
**Por qué:** el volcado usa `GroupShuffleSplit` por `Title`, semilla 42, para los clásicos, y el cuaderno de entrega reproduce eso (`notebook_proyecto.py:840–843`). El entrenamiento del transformador v1 no está en el repo; la afirmación «misma partición» para él es verosímil pero no se puede leer.

### [DUDA] Que «lectora ajena al proyecto» y «prima del autor» sean la misma condición
**Dónde:** `entrega/documento.md:44`; `entrega/estrategia.md:103`.
**Por qué:** «ajena al proyecto» es cierto; «ajena al autor» no. La estrategia lo declara (103: «prima del autor»); el documento no. No es un error, pero un evaluador puede leerlo como independencia que no hay.

---

## Lo que está bien y podía estar mal

Se verificó y se sostiene:

- **Partición sin fuga en CLEAR.** `GroupShuffleSplit` por `Title` con semilla (`notebook_proyecto.py:840–843`); la lista de 3.000 palabras familiares se cuenta **solo sobre entrenamiento** (846–849); la fuga anterior se midió y se reporta con su efecto (900–920: «solo 228 de las 3.000 palabras cambian»). Es exactamente lo que pide el frente 1 y está bien hecho.
- **Escalador ajustado solo con entrenamiento** para los modelos (`notebook_proyecto.py:1136`). El de la PCA (947) usa todo, pero es exploratorio, no de modelado.
- **7.1 reconoce que los 950 extractos eligieron la época** (doc:513–516). Es la confesión correcta y poco frecuente.
- **Sumas y divisiones**: Cuadro 3 (723+185+115+69+53+52 = 1.197; porcentajes 100,0); 148+1.049 = 1.197; Cuadro 8 (461+489 = 950); 3.774+950 = 4.724; 53/59 = 89,8 %; 77/144 = 53,5 %; 140/144 = 97,2 %; 19/38 = 50 %; 45.345/18 ≈ 2.519 («por 2.500»).
- **Aritmética del int8**: desplazamiento 0,21 sobre letras de anchura 0,4 → 52,5 % de la escala; sobre dos cortes de banda → 2×0,21/2 = 21 %. Correcto (doc:674).
- **Bandas y letras**: recalculado con `app/scoring.py`: cortes en 0,6 y 1,4 (0,59→básico, 0,60→intermedio, 1,39→intermedio, 1,40→avanzado); 0 incoherencias banda–letra en 201 puntos; 0 desacuerdos letra pública/interna en 50.001 puntos.
- **Paletas**: 5 en `app/paletas.py`; contraste mínimo 9,51 (*menta*/interfaz), como dice la estrategia.
- **`dificultad_global`** pondera por ventanas (`app/ficha.py:359–363`), coherente con «la ventana como unidad» del Cuadro 12.
- **Ocho pestañas** en `app/ui.py` (8 `gr.Tab(`).
- **328 MB** = 82 M parámetros × 4 bytes.
- **Baseline de longitud presente** (Cuadro 11) y **limitaciones específicas**, no fórmulas: 14 numeradas con cifras.
- **Hipótesis rechazadas reportadas** (Cuadro 12), incluida la que no mejoró (SPGC: −0,330 → −0,326, que el cuaderno respalda en 926–931).

---

## Veredicto

**Sólido:** todo lo que pasa por CLEAR —partición por obra, rasgos sin fuga, escalado correcto, comparación de siete modelos con la métrica ordinal adecuada, sobreajuste detectado y controlado— y la ingeniería de la aplicación —bandas, letras, agregación, contraste—, que se puede recalcular y da lo que el documento dice. La prosa sobre limitaciones es de las mejores que he auditado.

**Hay que arreglar antes de entregar:**
1. El Cuadro 8: el 0,840 de v2 sobre OneStopEnglish es un número de entrenamiento. Sustituir por la evaluación sobre los 114 reservados y declarar que OneStop fue corpus de afinado.
2. La contradicción sobre British Council: o está en el corpus de anclaje o no. Publicar la composición y la partición del corpus de anclaje y reescribir «externo / nunca vio» según corresponda. Es el resultado que el documento dice que sostiene el trabajo.
3. La coherencia de cifras de velocidad (8,7/101,7/11,7× frente a 8,19/112,7/13,8× frente a «dieciocho veces») y las 6,3 horas, que el propio repositorio dice que no cuadran.
4. Que `validar_local.py` calcule lo que el Cuadro 11 afirma (Spearman, longitud, parcial, recta).
5. Que las cuatro pruebas sustantivas puedan fallar (`assert not malas`).
6. El filtro de prosa: contar la secuencia real y describir el filtro que produce los 45 textos.

**Opcional:** los MENOR (XGBoost 1,42; 286/300; 4,8×/4,5×; «cuarta» cifra; Gradio fijada; mensaje de Drive; informe de velocidad sin terminar; 61.642/61.552; dos rectas).

El proyecto no está invalidado: lo que falla es la cadena de evidencia alrededor del modelo desplegado, no el trabajo con el corpus principal ni la aplicación. Pero esa cadena es justo la que el documento pone en primera página.
