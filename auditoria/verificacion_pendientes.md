# Verificación de los hallazgos pendientes de las dos auditorías

Fecha: 8 de septiembre de 2026. Árbol verificado: `366f087`, limpio.

Alcance: los hallazgos **serios, menores y dudas** que quedaban abiertos en
`auditoria/informe_codex.md` (H05, H11–H24) y en `auditoria/informe_fable.md`
(7 serios, 9 menores, 5 dudas). Quedan fuera, por estar ya corregidos: Codex
H01–H04 y H06–H10; de Fable, los dos críticos y las `axhline` de la figura 13
—esta última reverificada de paso: `entrega/notebook_proyecto.py:1620–1621` ya
dibuja 0,6 y 1,4—.

No se modificó ningún archivo del proyecto. Este documento es la única
escritura. Aritmética recalculada con `python -X utf8`; las líneas citadas son
las **de hoy**, no las de los informes originales.

**Resultado global: 31 CIERTO, 0 YA ARREGLADO, 0 FALSO, 5 NO VERIFICABLE.**
Ninguno de los pendientes ha caducado solo, porque los cinco *commits* de
corrección tocaron otras zonas. Sí hay tres matices donde el auditor acierta en
el fondo y falla en la forma: H12 (la mitad ya está arreglada), H15 (la frase
que cita no existe en el repositorio) y el menor de Fable sobre 286/300 (el 286
sí es una tanda real y medida, y su arreglo es equivocado).

---

## CIERTO — gravedad SERIO

### [CODEX H05 | SERIO] British Council se presenta como corpus ciego que el modelo nunca vio
Veredicto:  CIERTO
Comprobado: `grep -n 'nunca vio\|ciega\|primero para diagnosticar' entrega/documento.md` y lectura de las líneas 30–35, 82, 609 y 824–831.
Evidencia:  doc:32–33 «sobre un corpus **externo que nunca vio**, ordena los niveles del Marco Común Europeo»; doc:828–831 (limitación 6) «El corpus de British Council **se usó primero para diagnosticar** (descubrir que el modelo no sabe leer menús) y después para validar […] el conjunto ha sido mirado y ya no es virgen». Las dos frases siguen conviviendo en el mismo documento.
Arreglo:    En `entrega/documento.md:32–33` (Resumen) y `:82`, sustituir «corpus externo que nunca vio» por «corpus externo, no usado para ajustar los pesos, pero explorado durante el desarrollo (limitación 6)». Reservar «ciega» para el conjunto de 144 del Cuadro 9 —donde tampoco está acreditada la independencia, ver H21—.
Esfuerzo:   trivial

### [CODEX H11 | SERIO] `validar_local.py` puede declarar «orden correcto» sin evaluar ni un texto
Veredicto:  CIERTO
Comprobado: lectura completa de `validar_local.py` (84 líneas) y ejecución de `all(a<b for a,b in zip(m,m[1:]))` con `m=[]` y con `m=[0.5]`.
Evidencia:  ambos casos devuelven `True`. `validar_local.py:82–83` construye `medias` solo con los niveles encontrados; si el glob de la línea 54 (`*LearnEnglish-Reading*.pdf`) no encuentra nada, el guion imprime «orden estrictamente creciente: True» sin haber puntuado un solo texto. Además `validar_local.py:35` hace `" ".join(utiles)`, que **colapsa el cuerpo a una sola línea** y desactiva justo las condiciones de línea y viñeta de `scoring.continuous_prose` (`app/scoring.py:68–71`) cuya reparación destaca el Cuadro 5, T1 (`entrega/documento.md:459`). Y no calcula Spearman, exactitud ni correlación parcial.
Arreglo:    En `validar_local.py`, tras la línea 71, exigir cobertura mínima y los cinco niveles (p. ej. `if len(por_nivel) < 5 or sum(map(len, por_nivel.values())) < 40: sys.exit("validación insuficiente")`) antes del booleano de la línea 83; y no aplanar las líneas en `cuerpo()` (línea 35), o documentar que esta vía aplica otro filtro.
Esfuerzo:   medio

### [CODEX H12 | SERIO] El documento no presenta la comparación clásica más completa
Veredicto:  CIERTO (parcialmente; la mitad más grave ya se corrigió)
Comprobado: comparación de `git show 3016237:entrega/documento.md` (líneas 398–403) con el archivo actual (412–424); `grep -n '0,354\|17 variables\|diecisiete' entrega/notebook_proyecto.py`; lectura del Cuadro 7 (doc:525–533).
Evidencia:  la afirmación de techo **ya no está**: «El techo de las variables clásicas» es hoy «Hasta dónde llegan las variables clásicas», y doc:419–424 añade «Lo que no se demuestra es que exista un límite teórico […] el cuadernillo enseña un caso donde ampliar de tres a diecisiete variables sí mejora. La conclusión honesta es empírica, no un techo». Lo que sigue en pie: el Cuadro 7, rotulado «Progresión **completa** sobre el mismo conjunto de prueba», omite las filas de 17 variables que el propio cuaderno calcula —`notebook_proyecto.py:1325` «Con las **diecisiete**: exactitud **0,352**, error ordinal **1,061**» y `:1327` «XGBoost sobre las mismas diecisiete: 0,340 y 1,081»—, y sigue vivo el «Ganancia nula […] El embedding ya contiene esa información» de doc:687.
Arreglo:    Añadir dos filas al Cuadro 7 (`entrega/documento.md:527–529`) con las 17 variables (0,352 / 1,061 y 0,340 / 1,081), o quitar la palabra «completa» del pie (doc:531).
Esfuerzo:   trivial

### [CODEX H13 · FABLE SERIO | SERIO] Las «6,3 horas de A100» no salen de ningún cálculo del repositorio
Veredicto:  CIERTO
Comprobado: `python -X utf8 -c "print(61642*350/2022/3600)"`; `grep -n '6,3 hor\|61\.642\|61\.552' entrega/documento.md entrega/estrategia.md colab_precalculo.py investigacion/acelerar_precalculo.md`.
Evidencia:  el resultado es **2,9639 h**, no 6,3. Para que salieran 6,3 h harían falta **743,96 ventanas por libro**, y `colab_precalculo.py:361` fija `VENTANAS_POR_LIBRO = 350  # media razonable`. El propio repositorio ya lo denuncia: `investigacion/acelerar_precalculo.md:62–67` «la estimación de "6,3 horas de A100" para el catálogo entero **no cuadra** con 2.022 ventanas/s […] = **2,96 h**». La cifra sigue en `entrega/documento.md:47`, `:779–780` y `entrega/estrategia.md:182–183`.
Arreglo:    Corregir a ≈3,0 h —con el supuesto de 350 ventanas/libro declarado como supuesto, no como medición— en `documento.md:47`, `documento.md:779–780` y `estrategia.md:182–183`; o medir la media real de ventanas por libro con el código de `acelerar_precalculo.md:70–77`.
Esfuerzo:   trivial (corregir la cifra) / medio (medirla de verdad)

### [CODEX H14 | SERIO] El lote de 64/128 medido no se alcanza en el recorrido de la app
Veredicto:  CIERTO
Comprobado: lectura de `app/ui.py:1079–1099` y de `app/scoring.py:219–241`; contraste con `informe_velocidad.md:104–126`.
Evidencia:  `app/ui.py:1083–1085` recorre `for n, (i, c) in enumerate(cuerpo, 1): vs = p.perfil_de_texto(...)`, es decir **una llamada por capítulo**. `app/scoring.py:224` trocea *dentro* de cada llamada (`for i in range(0, len(bloques), lote)`) y no acumula ventanas entre llamadas. Con los tamaños del propio material —«el mayor de Guerra y Paz son 17 ventanas», commit `f88bc8c`— nunca se forma un lote de 64 ni de 128 en el recorrido interactivo, que es donde `entrega/documento.md:915` atribuye el «+24 % y ×11,7».
Arreglo:    O acumular ventanas entre capítulos antes de llamar a `_puntuar_bloques` (`app/ui.py:1083`), o matizar en `entrega/documento.md:915` y en `informe_velocidad.md` que la cifra es capacidad por lote sobre ventanas ya agrupadas, no rendimiento del manejador interactivo.
Esfuerzo:   trivial (matizar) / alto (reagrupar de verdad)

### [CODEX H15 | SERIO] Ocho ventanas de un capítulo justifican un muestreo de documento entero
Veredicto:  CIERTO (con una corrección al auditor)
Comprobado: `grep -rn 'bastan\|ventanas fijas' entrega/` sobre el árbol actual **y** sobre `3016237`; lectura de doc:456 (Cuadro 5, T7), doc:789–795 y `entrega/estrategia.md:185–189`.
Evidencia:  **la frase que cita Codex —«si ocho ventanas bastan para representar un libro entero. Está medida y la respuesta es sí»— no existe en el repositorio, ni hoy ni en el commit auditado**: es una paráfrasis suya. Pero el fondo se sostiene: doc:456 justifica «**Muestreo de hasta 8 bloques repartidos por el documento**» con una evidencia de capítulo —«8 bloques dan 1,784 y el recorrido completo de **las 23 ventanas del mismo capítulo** da 1,743»—, y `estrategia.md:185–189` describe el vistazo (30 capítulos × 2 ventanas) y remata «Y **el atajo** está cuantificado, no prometido: 8 ventanas dan 1,784…», que es otro estimador. El vistazo de 30×2 no tiene ninguna medición de error en todo el repositorio.
Arreglo:    En `entrega/documento.md:456`, decir que el 0,041 se midió sobre un capítulo, no sobre un documento. En `entrega/estrategia.md:188–189`, separar los dos atajos o retirar «el atajo está cuantificado» del párrafo del vistazo.
Esfuerzo:   trivial (acotar) / medio (medir el vistazo en varios libros)

### [CODEX H16 · FABLE SERIO | SERIO] Cuatro pruebas sustantivas devuelven la lista de violaciones como éxito
Veredicto:  CIERTO
Comprobado: lectura de `pruebas_extremas.py:35–49` y de las cuatro funciones; `grep -c '^prueba(' pruebas_extremas.py` → **191**; `grep -c 'assert ' pruebas_extremas.py` → 15.
Evidencia:  `pruebas_extremas.py:36` «Ejecuta `fn`. **Que devuelva algo es exito**; que lance, es fallo», y las cuatro funciones terminan en `:804` `return malas or "…todas AA"`, `:824` `return malas[:5] or "las 201 puntuaciones concuerdan"`, `:846` `return malas[:5] or "las 50.001 coinciden"` y `:874` `return malas[:3] or "500 libros sinteticos…"`. Una lista no vacía se imprime como `ok` y no entra en `FALLOS`. Y `:878–881` («el caso que destapo la auditoria») llama a `ui.ficha.dificultad_global([...])` sin comparar el resultado con 1,8. De propina: `entrega/estrategia.md:142`, `:218` y `:282` siguen diciendo **183** pruebas cuando el archivo tiene **191**.
Arreglo:    `assert not malas, malas` en `pruebas_extremas.py:804`, `:824`, `:846` y `:874`; `assert ui.ficha.dificultad_global([...]) == 1.8` en `:878–881`. Actualizar 183 → 191 en `estrategia.md:142`, `:218` y `:282`.
Esfuerzo:   trivial

### [CODEX H17 | SERIO] La ficha y «a tu ritmo» presentan estimaciones como conteos
Veredicto:  CIERTO
Comprobado: lectura de `app/ficha.py:31–32`, `:159–178` y `:181–213`, y de `app/ui.py:1155–1172`.
Evidencia:  `app/ficha.py:159` `def _muestra(libro, tope_palabras: int = 60000)` toma **prefijos** de cada capítulo (`toks[:por_capitulo]`, línea 177) y sobre esa muestra —no sobre la obra— se calculan longitud de frase, diálogo y palabras distintivas (`:194–213`); la riqueza léxica usa además solo `toks[:20000]` (`:203`). Solo `palabras_total` (`:185–191`) recorre todos los capítulos. El tiempo sale de `PPM_COMODO = 180` / `PPM_EXIGENTE = 110` (`:31–32`), constantes; y en `app/ui.py:1163–1168`, sin análisis guardado, `nivel_libro` es `None`, `exigente` es `False` y se imprime igualmente « a tu ritmo de lectura». Frente a eso, `entrega/documento.md:730–731` «todo lo que dice está **contado sobre el fichero**» y `entrega/estrategia.md:71–72` «cuánto tarda en leerlo **a su ritmo** […] todo contado sobre el fichero».
Arreglo:    En `entrega/documento.md:730–731` y `entrega/estrategia.md:71–72`, distinguir «total contado», «estadística sobre una muestra de hasta 60.000 palabras» y «tiempo estimado a 180/110 palabras por minuto». En `app/ui.py:1168`, cambiar « a tu ritmo de lectura» por « a un ritmo de lectura cómodo».
Esfuerzo:   trivial

### [CODEX H18 | SERIO] El salto de «orden por nivel» a «utilidad personal» no está validado
Veredicto:  CIERTO
Comprobado: `grep -n '0.65' app/perfil.py`; lectura de doc:25, doc:97–100, doc:895–897 y de la tabla de métricas de `entrega/estrategia.md:276–285`.
Evidencia:  `app/perfil.py:210` `PESO_FRAGMENTOS = 0.65`, sin justificación empírica en ningún archivo; `entrega/estrategia.md:50` lo defiende con «delante de un texto real la gente se juzga mejor que describiéndose», que no está medido. El documento promete en el Resumen (doc:25) «libros que **pueda terminar**» y concluye (doc:895) «Se cumplió el objetivo ordinal, que era el objetivo», mientras la propia estrategia (`:284`) declara «Impacto | Proporción de libros terminados | **Sin instrumentar** (A9)». El único dato de orden son medias por nivel con n = 3, 7, 12, 11, 12 (`entrega/datos_figuras/validacion.dat`), que no acreditan el orden por parejas de la formulación de doc:97–100.
Arreglo:    En `entrega/documento.md:25`, «le sugiere libros a su nivel» en vez de «que pueda terminar»; en `entrega/estrategia.md:50`, marcar el 0,65 como decisión heurística sin validar.
Esfuerzo:   trivial

### [FABLE SERIO] El filtro de prosa: «a priori» contra «primero para diagnosticar», y un tercer filtro en el guion
Veredicto:  CIERTO
Comprobado: lectura de doc:254–262, doc:693 y doc:828–831; de `validar_local.py:18–35` y `:59–70`; y de `app/scoring.py:52–73`.
Evidencia:  doc:258–259 «Se definió un filtro de prosa continua **antes de mirar ningún resultado**»; doc:693 (Cuadro 12) «El criterio se fijó **a priori** y por dos vías independientes»; doc:829 «se usó **primero para diagnosticar** (descubrir que el modelo no sabe leer menús)». Descubrir el fallo es mirar resultados. Y las «dos vías» —palabras clave del título, y ≥7 palabras por línea con puntuación en (0, 0,11]— **no existen en ningún código ejecutable**: `validar_local.py:18` importa `continuous_prose`, cuyos umbrales reales son otros (`app/scoring.py:61` `< MIN_WORDS`, `:64` `len(frases) < 4`, `:67` `5 <= media_frase <= 55`, `:71` `con_vineta >= 2 or cortas/lineas > 0.35`), más el anclaje «Reading text … Tasks» de `validar_local.py:20–21`. Los 45 textos del Cuadro 10 salen de ese tercer filtro. Y el Cuadro 8 (doc:565–570) evalúa los 59 textos completos, sin filtro alguno.
Arreglo:    Reescribir `entrega/documento.md:258–262` con la secuencia real (se vio el fallo → se fijó el filtro → se validó), quitar «a priori» de doc:693, y describir en 7.4 el filtro que de verdad produce los 45 textos (`app/scoring.py:52–73` más el anclaje de `validar_local.py:20–21`).
Esfuerzo:   medio

### [FABLE SERIO] Las cifras de velocidad del Cuadro 14 no están en el informe que el documento cita como respaldo
Veredicto:  CIERTO
Comprobado: `grep -rn '101,7\|101\.7' --include=*.py --include=*.md --include=*.dat .`; lectura de `informe_velocidad.md:83–126`, `:181` y `:194`; factores recalculados en `python`.
Evidencia:  el 101,7 solo aparece en `arrancar_gpu.py:14`, `entrega/datos_figuras/velocidad.dat:3`, `entrega/documento.md:762`, `entrega/estrategia.md:181` y `entrega/notebook_proyecto.py:1820`; **en `informe_velocidad.md` no aparece ni una vez**, y el informe da 8,19 v/s en CPU (línea 115) y 112,7 en GPU (línea 181). Con esos números el factor es 112,7/8,19 = **13,76×**, no 11,7×. `app/scoring.py:207` dice además «112,7 ventanas/s frente a 8,19 en CPU, **dieciocho** veces mas rapido», que es 112,7/6,16 = 18,30, contra la base *sin* hilos ni lotes. Tres factores para el mismo hecho. Matiz que el auditor no vio: el 8,7 y el 101,7 sí corresponden a una tanda descrita —840 ventanas de punta a punta, `arrancar_gpu.py:10–14`, con 101,7/8,7 = 11,690 coherente con el «11,7×»—, distinta de las 300 ventanas del informe; el defecto es que esa tanda no está registrada donde el documento dice que está.
Arreglo:    Añadir a `informe_velocidad.md` la tanda de 840 ventanas con fecha y condiciones (es la que sostiene el Cuadro 14) y corregir `app/scoring.py:207` para que cite la misma base que el resto.
Esfuerzo:   medio

### [FABLE SERIO] El Cuadro 11 y la recta de compresión no los calcula ningún código del repositorio
Veredicto:  CIERTO
Comprobado: lectura completa de `validar_local.py`; `grep -n 'parcial' entrega/notebook_proyecto.py entrega/documento.md entrega/estrategia.md`; recálculo de la correlación parcial con los coeficientes publicados.
Evidencia:  `validar_local.py:73–83` imprime nivel, n, media, desviación y un booleano; **no hay Spearman, ni correlación con la longitud, ni parcial, ni ajuste lineal** en ningún archivo ejecutable, y `notebook_proyecto.py:1727` solo los menciona en Markdown. La consistencia interna sí se sostiene —(0,854 − 0,807×0,730)/√((1−0,807²)(1−0,730²)) = **0,65630**, compatible con el 0,657 de doc:647—, pero eso es coherencia, no reproducción. Siguen además circulando dos rectas (doc:646 y `app/scoring.py:108`: «0,72 × real + 0,38»; `investigacion/transformer_v5.md:261`: «(pred − 0,359)/0,714») y dos Spearman externos sin etiquetar (doc:614, 0,829 con n=38; doc:643–647, 0,854 con n=45).
Arreglo:    Añadir a `validar_local.py` (tras la línea 71) el cálculo de Spearman contra el nivel, la correlación con el número de palabras, la parcial y la recta, y que `entrega/documento.md:643–649` cite esa salida con su n. En doc:613–614, rotular el 0,829 como la tanda de Colab (38 textos, sin A1).
Esfuerzo:   medio

### [FABLE SERIO] El orden A1 < A2 descansa en 3 textos y 0,044, y el Resumen da las cinco medias sin la n
Veredicto:  CIERTO
Comprobado: lectura de `validar_local.py:74`, doc:33–35, doc:623–631, doc:636 y doc:897; `cat entrega/datos_figuras/validacion.dat`; resta 0,5480 − 0,5040.
Evidencia:  `validar_local.py:74` `esperado = {"A2": 0.6479, "B1": 0.9513, "B2": 1.2883, "C1": 1.4950}` — **sin A1**: la tanda de Colab no tuvo ese nivel. La distancia A1–A2 es **0,0440**, con n = 3 y desviaciones de 0,111 y 0,237 (`validacion.dat`), es decir, solapadas. El Resumen (doc:33–35) y las Conclusiones (doc:897) enumeran las cinco medias sin n; el Cuadro 10 (doc:623–629) sí da la n, pero **no la desviación**, que existe en `validacion.dat` y que el guion imprime. Y doc:636 «C1 coincide hasta la **cuarta** cifra»: 1,4952 frente a 1,4950 coinciden hasta la **tercera** cifra decimal; solo es cierto leyendo «cifra» como cifra significativa, y esa ambigüedad no conviene en un documento evaluado.
Arreglo:    En doc:33–35 y doc:897, dar la n por nivel o acotar a «orden creciente, con A1 apoyado en 3 textos». Añadir la columna de desviación al Cuadro 10 (doc:623–629), copiándola de `validacion.dat`. En doc:636, «hasta la tercera cifra decimal».
Esfuerzo:   trivial

### [FABLE SERIO · CODEX H21] La tarjeta del modelo con el 0,908 y el 97,2 % no está en el repositorio
Veredicto:  CIERTO
Comprobado: `find . -iname "*metricas*" -not -path "./.git/*"` → **sin resultados**; `ls modelo_v4/` → `README.md`, `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json`; lectura de `modelo_v4/README.md:66–70` y `:96–100` y de doc:605–616.
Evidencia:  `entrega/documento.md:605–609` cita «Su tarjeta de modelo (`metricas_literalevel_v4.json`, 5 de septiembre de 2026)» como fuente de las dos cifras centrales del modelo desplegado, y **ese archivo no existe en el repositorio**. `modelo_v4/README.md:96–100` describe el corpus solo como «un corpus de documentos anclados a niveles MCER», sin fuentes, sin n por fuente ni por nivel y sin regla de partición. Lo único coherente y comprobable: 510 + 144 = 654, 77/144 = 53,47 % y 140/144 = 97,22 %.
Arreglo:    Incluir `metricas_literalevel_v4.json` en `modelo_v4/`, con fuentes, n por fuente y por nivel y la regla de partición; o retirar la cita de `entrega/documento.md:605` y decir de dónde salen las cifras.
Esfuerzo:   medio

---

## CIERTO — gravedad MENOR

### [CODEX H19 | MENOR] «Sin clave» se confunde con «sin red»
Veredicto:  CIERTO
Comprobado: lectura de doc:865–868 y `entrega/estrategia.md:210–213`; consulta a `kaikki_diccionario.db` (`select audio_uk, audio_us from entradas where audio_uk<>'' limit 3`); lectura de `app/catalogo.py:64–80` y `:195–199`.
Evidencia:  los audios de la base son URL remotas: `https://upload.wikimedia.org/wikipedia/commons/transcoded/.../En-uk-free.ogg.mp3`; el navegador necesita red para reproducirlos. Y `app/catalogo.py:197–198` carga `SentenceTransformer(_ruta_local(MODELO_EMB))`, que según su propio docstring (`:72–74`) «si no esta cacheado […] se devuelve el nombre y **se descarga** como siempre». Frente a eso, `estrategia.md:212` «diccionario, fonética, audio de Wiktionary, buscador y puntuación, porque **nada de eso usa red**» y doc:866 «en todo lo que no usa red».
Arreglo:    Reescribir `entrega/estrategia.md:210–213` y `entrega/documento.md:865–868` con tres categorías: sin clave de OpenAI, sin conexión con los recursos ya descargados (diccionario, fonética, puntuación) y lo que sigue necesitando red (audio de Wiktionary, primera carga del modelo de búsqueda).
Esfuerzo:   trivial

### [CODEX H20 | MENOR] Quedan errores aritméticos y comparaciones de tandas sin identificar
Veredicto:  CIERTO — los cinco puntos verificados uno a uno
Comprobado: `grep -n` de cada cifra en `entrega/documento.md`; recálculos en `python -X utf8`; lectura del Cuadro 4 (doc:365–369), del Cuadro 7 (doc:525–531) y de `informe_velocidad.md:104–126`.
Evidencia:  (a) doc:394–395 «se encoge de **seis** niveles a cuatro (A2–C1)»: el Cuadro 10 (doc:623–629) tiene **cinco**, A1–C1. (b) doc:904 da 1,39 «tanto con regresión logística como con XGBoost» y el Cuadro 7 (doc:528) da XGBoost **1,42** —el Cuadro 12, doc:686, sí dice «1,42 vs 1,39»—. (c) doc:910–911 empareja −0,330 con «18 libros»; el Cuadro 4 (doc:367–368) asigna **−0,379** a los 18 y −0,330 a los 397. (d) doc:915 «+24 %»: 6,16 → 8,19 es **+32,95 %**, y ninguna pareja publicada da 24 % (8,19/6,96 = +17,7 %; 8,7/6,96 = +25,0 %). (e) doc:776–777 dice 286/286 ventanas idénticas e `informe_velocidad.md:122–124` y `app/scoring.py:240–242` dicen 300/300, sin identificar las tandas.
Arreglo:    doc:395 «cinco niveles»; doc:904 «1,39 y 1,42»; doc:910 «de 397 libros a los 45.345»; doc:915, el porcentaje de la tanda que se cite; y etiquetar cada tanda de ventanas (286 y 300 son dos mediciones reales distintas, ver abajo).
Esfuerzo:   trivial

### [FABLE MENOR] Las conclusiones dan a XGBoost el error ordinal de la regresión logística
Veredicto:  CIERTO
Comprobado: doc:904 frente a doc:527–528.
Evidencia:  doc:904 «tres variables clásicas dan 1,39 niveles de error ordinal tanto con regresión logística como con XGBoost»; doc:528 «| XGBoost | 3 variables clásicas | 0,28 | **1,42** |».
Arreglo:    `entrega/documento.md:904`: «1,39 y 1,42 respectivamente».
Esfuerzo:   trivial

### [FABLE MENOR] 286 ventanas en el documento, 300 en el informe y en `scoring.py`
Veredicto:  CIERTO (pero el arreglo que propone el auditor es incorrecto)
Comprobado: `informe_velocidad.md:83` y `:104–124`; `app/scoring.py:240–242`; doc:776–777; verificación aritmética de ambas tandas; mensaje del commit `f88bc8c`.
Evidencia:  las dos son tandas reales y coherentes: 286/46,4 s = 6,16 v/s (§3.a) y 300/48,7 s = 6,16 v/s (§3.b), con 300/36,6 = 8,19. El commit `f88bc8c` documenta el contraste bit a bit **sobre 286** («286 ventanas de una en una y en un solo lote dan 286/286 identicas, MAE 0,000000000») y el informe lo documenta **sobre 300**. Así que no es cierto que el 286 sea solo el barrido de hilos ni que el arreglo sea «poner 300»: son dos comprobaciones distintas, y el defecto real es que ninguna está identificada.
Arreglo:    En `entrega/documento.md:776–777` y en `informe_velocidad.md:122–124`, decir de qué tanda es cada cifra y con qué fecha, en vez de sustituir una por otra.
Esfuerzo:   trivial

### [FABLE MENOR] fp16 «4,8×» en el documento y «cuatro veces y media» en el código
Veredicto:  CIERTO
Comprobado: doc:690, `app/scoring.py:212–213`, `informe_velocidad.md:181`; cálculos 35,48/7,45 = 4,762 y 36,70/8,47 = 4,333.
Evidencia:  doc:690 «Es **4,8× más lenta** que fp32»; `app/scoring.py:213` «la media precision es **CUATRO VECES Y MEDIA** MAS LENTA». El 4,8 corresponde al lote 128; el 4,5 no corresponde a ninguna de las dos parejas medidas.
Arreglo:    `app/scoring.py:213`: «CASI CINCO VECES MAS LENTA (4,8x con lote 128)».
Esfuerzo:   trivial

### [FABLE MENOR] `validar_local.py` silencia cualquier excepción y la rotula como «sin cuerpo localizable»
Veredicto:  CIERTO
Comprobado: lectura de `validar_local.py:59–70` y `:80`.
Evidencia:  `validar_local.py:68–70` `except Exception as e: saltados += 1; continue` engloba el fallo de `pypdf`, el `ValueError` del filtro de prosa y cualquier fallo del modelo; la línea 80 imprime «textos omitidos (**sin cuerpo localizable**): {saltados}», que solo describe el primero de los tres casos. La n = 45 del Cuadro 10 depende de ese recuento.
Arreglo:    En `validar_local.py:63–70`, contar por motivo —`sin_ancla`, `corto`, `pocas_frases`, `forma_de_frase`, `maquetado_de_lista`, `error_pdf`, `otro`; los cuatro del medio ya los devuelve `continuous_prose`— e imprimir el desglose en la línea 80.
Esfuerzo:   trivial

### [FABLE MENOR] `puntuar()` muestrea como máximo 8 ventanas y 7.4 no lo dice
Veredicto:  CIERTO (el documento sí lo dice, pero en otro sitio)
Comprobado: `app/scoring.py:21` y `:76–92`; doc:600 y doc:456.
Evidencia:  `app/scoring.py:21` `MAX_BLOCKS_PER_DOC = 8` y `:91` `idx = np.linspace(0, len(inicios) - 1, cap)`. doc:600 describe el estimador como «Puntúa bloques de 250 palabras truncados a 256 tokens y **promedia sin ponderar**», sin mencionar el tope. El tope sí está declarado en el Cuadro 5, T7 (doc:456), así que no es omisión total; pero el apartado que describe el modelo evaluado no lo recoge, y la validación de 7.4 pasa precisamente por `puntuar()`.
Arreglo:    Una frase en `entrega/documento.md:600`: «hasta 8 ventanas repartidas por documento en validación; todas en el catálogo».
Esfuerzo:   trivial

### [FABLE MENOR] Gradio afirmada pero no fijada, y el mensaje de error apunta a Drive
Veredicto:  CIERTO
Comprobado: doc:43–44, `requirements.txt:5`, `app/scoring.py:183–189`, doc:850–853.
Evidencia:  doc:43 «ocho pestañas en **Gradio 6.26**» frente a `requirements.txt:5` `gradio>=6.0`. Y `app/scoring.py:186–188` manda al usuario a «Descarga la carpeta 'modelo_literalevel_v4_transformer' de **Drive (literalevel_bigdata)**», mientras la limitación 11 (doc:850–852) dice que los pesos están en Hugging Face, `MikeMaki1763/literalevel-v4`, repositorio público.
Arreglo:    `requirements.txt:5` → `gradio==6.26.*`; `app/scoring.py:186–188` → apuntar al repositorio de Hugging Face.
Esfuerzo:   trivial

### [FABLE MENOR] `informe_velocidad.md` está sin terminar y razona con los cortes viejos
Veredicto:  CIERTO
Comprobado: lectura de `informe_velocidad.md:158–160` y `:204–210`; ejecución de `app/scoring.public_band` sobre 0..2 en pasos de 0,001.
Evidencia:  `:204–210` «## 4. Recomendación / _(pendiente)_ / ## 5. Extrapolación / _(pendiente)_». `:159–160` «cruza de "avanzado" a "intermedio" (**el corte está en 1,6**)», cuando las fronteras reales de hoy son exactamente 0,600 y 1,400 (0,59 → básico, 0,60 → intermedio, 1,39 → intermedio, 1,40 → avanzado). El documento cita este informe como respaldo en doc:759–777.
Arreglo:    Completar §4–§5 de `informe_velocidad.md` o rotular el archivo como «mediciones brutas, sin recomendación»; actualizar la nota del corte en `:160`.
Esfuerzo:   trivial

### [FABLE MENOR] El número de libros del catálogo cambia entre documento y código
Veredicto:  CIERTO
Comprobado: `grep -rn '61\.552\|61\.642' colab_precalculo.py investigacion/acelerar_precalculo.md entrega/documento.md`.
Evidencia:  61.642 en doc:45, doc:211, doc:779 y doc:798, en `colab_precalculo.py:187` y en ocho líneas de `acelerar_precalculo.md`; **61.552** solo en `colab_precalculo.py:222` y `acelerar_precalculo.md:65`. Es una cifra rezagada en dos sitios, no una contradicción sistemática.
Arreglo:    Unificar a 61.642, con la fecha del catálogo, en `colab_precalculo.py:222` y `investigacion/acelerar_precalculo.md:65`.
Esfuerzo:   trivial

### [FABLE MENOR] Dos rectas de compresión distintas
Veredicto:  CIERTO
Comprobado: doc:646, `app/scoring.py:108`, `investigacion/transformer_v5.md:261`.
Evidencia:  doc:646 y `app/scoring.py:108` «≈ 0,72x + 0,38»; `transformer_v5.md:261` «`real ≈ (pred − 0,359)/0,714`», es decir pred ≈ 0,714·real + 0,359. La pendiente casi coincide al redondear; la ordenada no: 0,359 redondea a **0,36**, no a 0,38. Ningún código del repositorio ajusta la recta, así que no se puede decidir cuál es la buena.
Arreglo:    Ajustarla en `validar_local.py`, junto con el resto del Cuadro 11, y dejar una sola cifra en doc:646, `app/scoring.py:108` y `transformer_v5.md:261`.
Esfuerzo:   medio (depende del arreglo del Cuadro 11)

---

## CIERTO — gravedad DUDA

### [CODEX H22 | DUDA] Las velocidades finales son consistentes, pero falta su registro experimental
Veredicto:  CIERTO (la afirmación del auditor es verificable y se sostiene)
Comprobado: `grep -rn '101,7\|8,7\|2\.022'` por todo el repositorio; lectura de `informe_velocidad.md` entero (210 líneas); `colab_precalculo.py:349–364`; inspección JSON de los dos cuadernos con `json.load`.
Evidencia:  los tres valores (8,7 / 101,7 / 2.022) se repiten en documento, estrategia, notebook y `entrega/datos_figuras/velocidad.dat`, y son internamente coherentes (101,7/8,7 = 11,690 → «11,7×»; 2.022/8,7 = 232,414 → «232×»). Pero `informe_velocidad.md` no contiene ninguno de los tres, no cubre la A100 (línea 14: torch CPU-only) y termina en «_(pendiente)_». La celda 9 de `colab_precalculo.py:349–364` sí puede medir el 2.022, pero `colab_precalculo.ipynb` tiene **14 celdas, 0 salidas y 0 contadores de ejecución**, así que no acredita ninguna corrida.
Arreglo:    Adjuntar a `informe_velocidad.md` el registro de la tanda de 840 ventanas y de la tanda de A100 (fecha, lote, entorno, tiempos, criterio de agregación).
Esfuerzo:   medio

### [CODEX H23 | DUDA] El baseline de longitud es pertinente, pero sus datos y su incertidumbre no están
Veredicto:  CIERTO
Comprobado: recálculo de la correlación parcial con los coeficientes publicados; `ls entrega/datos_figuras/` y `cat validacion.dat`; lectura de `validar_local.py:73–83` y de `entrega/notebook_proyecto.py:1722–1728`.
Evidencia:  la consistencia se sostiene: (0,854 − 0,807×0,730)/√((1−0,807²)(1−0,730²)) = **0,65630**, compatible con el 0,657 de doc:647. Lo que no existe en el repositorio son las 45 longitudes, etiquetas y predicciones: `validacion.dat` guarda solo agregados (nivel, n, media, desv) y `validar_local.py` solo imprime eso. Sin ellas no se puede contrastar 0,854 frente a 0,807 ni afirmar nada sobre significación. Punto adicional confirmado: `notebook_proyecto.py:1728` dice que «un contador de palabras, **por construcción, se queda en cero**» al descontar la longitud; al controlar una variable por sí misma el residuo es constante y esa correlación parcial **no está definida**, no vale cero.
Arreglo:    Publicar una tabla por documento (identificador, nivel, palabras, predicción) en `entrega/datos_figuras/`, y reescribir `entrega/notebook_proyecto.py:1728` como «un contador de palabras no conserva ninguna señal al descontar la longitud, porque es la longitud».
Esfuerzo:   medio

### [CODEX H24 | DUDA] La matriz de estado de la rúbrica está desactualizada
Veredicto:  CIERTO
Comprobado: lectura de `.claude/skills/modulo-5-literalevel/SKILL.md:20–29` y `:98–104`; `ls entrega/`.
Evidencia:  SKILL.md:25–26 marca Documento y Estrategia como «**no empezado**» y existen `entrega/documento.md`, `entrega/documento.pdf` y `entrega/estrategia.md`. SKILL.md:29 marca el Notebook «⚠️ no es reproducible: el modelo no está publicado» y el modelo se publicó en el commit `26d6784`. SKILL.md:103 dice «**Falta el notebook limpio del proyecto**» y existe `entrega/notebook_proyecto.ipynb`, con 92 celdas. Siguen siendo correctos: Presentación «no empezado» (no hay archivo en `entrega/`) y Vídeo «falta grabar» (solo `guion_video.md`). El requisito de SKILL.md:44 —«correr sin errores ni warnings»— sigue sin acreditarse: el `.ipynb` no conserva ninguna salida.
Arreglo:    Actualizar la tabla de `.claude/skills/modulo-5-literalevel/SKILL.md:22–30` y el párrafo `:101–104`. Es un archivo de la *skill*, no un entregable: gravedad DUDA de verdad.
Esfuerzo:   trivial

### [FABLE DUDA] «Lectora ajena al proyecto» y «prima del autor» son la misma persona
Veredicto:  CIERTO (la discrepancia existe y es verificable)
Comprobado: doc:43–44 y `entrega/estrategia.md:103`.
Evidencia:  doc:44 «probada por una **lectora de quince años ajena al proyecto**»; `estrategia.md:103` «**Esmeralda, 15 años**, estudiante de preparatoria, **prima del autor**, fue…». Ajena al proyecto, sí; ajena al autor, no. La estrategia lo declara y el documento no.
Arreglo:    En `entrega/documento.md:44`, añadir el vínculo o remitir a la estrategia, para que un evaluador no lea una independencia que no hay.
Esfuerzo:   trivial

---

## NO VERIFICABLE

### [CODEX H21 | DUDA] No se puede verificar la independencia ni recalcular las métricas de los 144 documentos
Veredicto:  NO VERIFICABLE
Comprobado: `find . -iname "*metricas*"` (nada fuera de `auditoria/`); `ls modelo_v4/` (solo pesos, configuración y tokenizadores); lectura de `modelo_v4/README.md:66–70` y `:96–100`, y de doc:605–616.
Evidencia:  no hay manifiesto de los 654 documentos, ni grupos, ni los 144 pares real/predicho. Lo único comprobable es la coherencia aritmética: 510 + 144 = 654, 77/144 = 53,47 % ≈ 53,5 %, 140/144 = 97,22 % ≈ 97,2 %. Ni Spearman 0,908 ni MAE 0,499 se pueden recalcular desde el repositorio.
Haría falta:  el JSON de la tarjeta y una tabla por documento (identificador, grupo, fuente, nivel, predicción). Publicar recuentos y predicciones no exige redistribuir texto con derechos.
Esfuerzo:   medio (para quien tenga el corpus en Drive)

### [FABLE DUDA] Si los 59 textos de British Council están entre los 654 del corpus de anclaje
Veredicto:  NO VERIFICABLE
Comprobado: `find . -iname "*metricas*"`; lectura de `modelo_v4/README.md:96–104` (no enumera fuentes); doc:850–853 confirma que el guion de entrenamiento del v4 no está en el repositorio.
Evidencia:  ningún archivo del repositorio enumera las fuentes del corpus de anclaje. Es la pregunta de la que depende el segundo crítico de Fable, y el commit `366f087` la deja explícitamente reconocida como hueco abierto en lugar de taparla.
Haría falta:  la composición del corpus de anclaje (n por fuente y por nivel), que vive en Drive.
Esfuerzo:   medio

### [FABLE DUDA] Si la partición 510/144 del corpus de anclaje es por grupo
Veredicto:  NO VERIFICABLE
Comprobado: lectura de `modelo_v4/README.md:96–100` y de doc:605–609; contraste con `entrega/notebook_proyecto.py:838–843`.
Evidencia:  `modelo_v4/README.md:97–100` describe el entrenamiento —«Seis épocas, learning rate 2e-5, weight decay 0,01, calentamiento y precisión mixta. Se conservó el punto de control de la época 3»— pero **no dice cómo se partió**. Con CLEAR sí consta la partición por `Title` (`notebook_proyecto.py:840–842`, verificada); con el corpus que produce el 0,908, no consta.
Haría falta:  el guion de entrenamiento del v4, o la tarjeta con la regla de partición.
Esfuerzo:   trivial (una línea, para quien lo sepa)

### [FABLE DUDA] Las 2.022 ventanas/s y la desviación fp16 de 0,00037 en A100
Veredicto:  NO VERIFICABLE
Comprobado: lectura de `colab_precalculo.py:322–364`; `informe_velocidad.md:14` (torch CPU-only); inspección JSON de `colab_precalculo.ipynb` (14 celdas, 0 salidas).
Evidencia:  el código que las mediría existe y está bien planteado —celda 8 para la desviación fp16 contra fp32, celda 9 para las ventanas/s—, pero no hay ninguna salida guardada y esta máquina no tiene A100. Plausible e instrumentado; no reproducible aquí.
Haría falta:  ejecutar `colab_precalculo.ipynb` en una A100 y conservar la salida de las celdas 8 y 9.
Esfuerzo:   trivial (una corrida en Colab Pro)

### [FABLE DUDA] Que el transformador del Cuadro 7 use exactamente la misma partición que los siete modelos clásicos
Veredicto:  NO VERIFICABLE (con evidencia parcial a favor, más fuerte de la que vio el auditor)
Comprobado: `grep -n 'GroupShuffleSplit' notebook_v4_dump.py entrega/notebook_proyecto.py`; lectura de `notebook_v4_dump.py:2400` y de `entrega/notebook_proyecto.py:838–843`.
Evidencia:  `notebook_v4_dump.py:2400` afirma que «se reprodujo el conjunto de prueba original del v1 (CLEAR Corpus, GroupShuffleSplit por titulo de libro, test_size=0.2, random_state=42) obteniendo **exactamente las mismas 3774 filas de entrenamiento y 950 de prueba**», y las líneas 416, 448 y 546 usan esa misma semilla y proporción para los clásicos. Es más de lo que Fable dice haber encontrado, pero sigue siendo una afirmación del volcado: el guion que entrenó el transformador v1 no está en el repositorio, así que no se puede leer que usara esa partición.
Haría falta:  el guion de entrenamiento del v1, o la lista de identificadores de su conjunto de prueba.
Esfuerzo:   medio

---

## Tabla resumen

| Origen | Título corto | Veredicto | Esfuerzo |
|---|---|---|---|
| Codex H05 (SERIO) | British Council como corpus «ciego» | CIERTO | trivial |
| Codex H11 (SERIO) | El validador aprueba con cero textos | CIERTO | medio |
| Codex H12 (SERIO) | Cuadro 7 sin las 17 variables | CIERTO (mitad ya arreglada) | trivial |
| Codex H13 · Fable (SERIO) | Las 6,3 horas de A100 | CIERTO | trivial |
| Codex H14 (SERIO) | El lote 64/128 no se alcanza en la app | CIERTO | trivial / alto |
| Codex H15 (SERIO) | 8 ventanas de un capítulo justifican el muestreo del documento | CIERTO (la cita no existe) | trivial |
| Codex H16 · Fable (SERIO) | Cuatro pruebas que no pueden fallar | CIERTO | trivial |
| Codex H17 (SERIO) | Ficha de muestra y «a tu ritmo» | CIERTO | trivial |
| Codex H18 (SERIO) | De orden por nivel a utilidad personal | CIERTO | trivial |
| Fable (SERIO) | El filtro de prosa: «a priori» y un tercer filtro | CIERTO | medio |
| Fable (SERIO) | 8,7 y 101,7 no están en el informe de velocidad | CIERTO | medio |
| Fable (SERIO) | Cuadro 11 sin código que lo calcule | CIERTO | medio |
| Fable (SERIO) | A1 con n=3, sin desviación, y «cuarta cifra» | CIERTO | trivial |
| Fable · Codex H21 (SERIO) | La tarjeta del modelo no está en el repositorio | CIERTO | medio |
| Codex H19 (MENOR) | «Sin clave» no es «sin red» | CIERTO | trivial |
| Codex H20 (MENOR) | Cinco errores aritméticos y de tanda | CIERTO | trivial |
| Fable (MENOR) | XGBoost 1,42, no 1,39 | CIERTO | trivial |
| Fable (MENOR) | 286 frente a 300 ventanas | CIERTO (arreglo del auditor, erróneo) | trivial |
| Fable (MENOR) | fp16 4,8× frente a «cuatro y media» | CIERTO | trivial |
| Fable (MENOR) | `validar_local.py` silencia excepciones | CIERTO | trivial |
| Fable (MENOR) | El tope de 8 ventanas no está en 7.4 | CIERTO | trivial |
| Fable (MENOR) | Gradio sin fijar y mensaje que apunta a Drive | CIERTO | trivial |
| Fable (MENOR) | `informe_velocidad.md` sin terminar y con el corte 1,6 | CIERTO | trivial |
| Fable (MENOR) | 61.642 frente a 61.552 | CIERTO | trivial |
| Fable (MENOR) | Dos rectas de compresión | CIERTO | medio |
| Codex H22 (DUDA) | Falta el registro experimental de las velocidades | CIERTO | medio |
| Codex H23 (DUDA) | Faltan los datos del baseline de longitud | CIERTO | medio |
| Codex H24 (DUDA) | Matriz de estado de la rúbrica desactualizada | CIERTO | trivial |
| Fable (DUDA) | «Ajena al proyecto» y «prima del autor» | CIERTO | trivial |
| Codex H21 (DUDA) | No se pueden recalcular las métricas de los 144 | NO VERIFICABLE | medio |
| Fable (DUDA) | British Council entre los 654 | NO VERIFICABLE | medio |
| Fable (DUDA) | Partición 510/144 por grupo | NO VERIFICABLE | trivial |
| Fable (DUDA) | 2.022 v/s y fp16 en A100 | NO VERIFICABLE | trivial |
| Fable (DUDA) | Misma partición para el transformador del Cuadro 7 | NO VERIFICABLE | medio |
