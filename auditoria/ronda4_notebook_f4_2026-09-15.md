# Ronda 4 · Auditoría a ciegas del cuadernillo (f4)

15 sep 2026. Encargo de la Central. Solo lectura sobre `entrega/notebook_proyecto.py` y `entrega/notebook_proyecto.ipynb`, con cruce de cifras contra `entrega/documento.md` y el código. No se abrió nada de `auditoria/` salvo este informe. Sin Colab ni gasto.

## Qué se comprobó y cómo

- **Lectura completa** de `notebook_proyecto.py` (2.570 líneas, 103 celdas).
- **`.ipynb` frente al `.py`:** 103 de 103 celdas idénticas (markdown y código). El `.ipynb` no guarda salidas: 0 de 57 celdas de código. Metadatos de Colab con `accelerator: GPU` y `gpuType: T4`.
- **URL públicas, con petición HEAD:**
  - CLEAR (`raw.githubusercontent.com/scrosseye/CLEAR-Corpus/main/CLEAR_corpus_final.xlsx`): 200, 3,3 MB.
  - Catálogo de Gutenberg (`pg_catalog.csv`): 200, 21,2 MB.
  - `MikeMaki1763/literalevel-v4` en Hugging Face: público sin token, con `model.safetensors` de 328,5 MB, `tokenizer.json` y `config.json`.
- **Cifras:** cruzadas contra `documento.md` con búsqueda de cada valor y lectura del contexto.
- **Recta de compresión:** recalculada con las cinco medias que imprime el propio cuadernillo.
- **Ejecución local, fuera del repo** (`D:\Temp\auditoria_nb`): las 43 celdas de código anteriores a la carga del v4, con backend Agg, dos veces (con y sin el filtro global de avisos). Resultados abajo.

## Hallazgos

Formato: gravedad · celda o línea · cita · por qué falla · cómo se arregla.

### SERIO

**S1 · §9.2 lim. 7 (l. 2472) y §9.3, primera fila de la tabla (l. 2482), frente a «Antes de ejecutar» (l. 35-37).**
- **Cita:** «Este cuadernillo corre entero en un Colab limpio» y «Ejecutarse de principio a fin sin errores en un Colab limpio | Sí», frente a «La revisión del 14 de septiembre comprueba sincronización y sintaxis de las celdas, no una ejecución nueva en un Colab limpio».
- **Por qué falla:** el propio cuadernillo dice que no se ejecutó en un Colab limpio, y dos apartados después lo da por hecho. La rúbrica pide justo eso (que corra sin errores ni warnings), y el `.ipynb` no guarda ninguna salida que lo demuestre. El documento repite la afirmación (`documento.md` l. 1432: «El cuaderno corre entero en un Colab limpio»).
- **Arreglo:** ejecutar el `.ipynb` de principio a fin en un Colab limpio (CPU basta), guardar las salidas y fechar la ejecución. Si no se puede antes de entregar, rebajar §9.2 lim. 7, la fila de §9.3 y el documento a «diseñado para correr en un Colab limpio; última ejecución completa: <fecha>».

**S2 · Figura 13 (l. 1812-1813) y §9.1 punto 3 (l. 2437).**
- **Cita:** «Contra el ancla real, el ajuste ronda `predicho ≈ 0,72 × real + 0,38`».
- **Por qué falla:** la tabla que imprime la celda anterior (medias 0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952) da, por mínimos cuadrados contra el ancla (0; 0,4; 0,8; 1,2; 1,6), **0,667 × real + 0,411**. Con sus cuatro medias de A2 a C1, 0,783 × real + 0,272. Ninguna da 0,72. `documento.md` (l. 867-872 y 1386) sí explica que 0,7196x + 0,3760 sale de «las cuatro medias por nivel que reportó Colab» en otra tanda y que con las cinco locales sale 0,67x + 0,41; la corrección no llegó al cuadernillo, y quien ejecuta ve una recta que no sale de los datos de la celda.
- **Arreglo:** en las dos líneas, poner la recta de las cinco medias (≈ 0,67 × real + 0,41) con la nota del documento sobre el 0,72 de la tanda de Colab, o calcularla en la celda con `np.polyfit` e imprimirla.

### MENOR

**M1 · §3.1 tabla y celda del catálogo (l. 364-366 y 393).**
- **Cita:** «medidas el 8 de septiembre de 2026».
- **Por qué falla:** el documento fecha la instantánea el **7** de septiembre (`documento.md` l. 232). Además, el feed es vivo: la ejecución local de hoy da 79.381 entradas y 61.675 libros de texto en inglés. La celda lo avisa en un comentario, pero el markdown da 79.337 y 61.642 como cifras fijas y sin fecha.
- **Arreglo:** unificar la fecha y decir en el markdown que las cifras son de esa instantánea y que la celda imprimirá algo mayor.

**M2 · §4.2, markdown del catálogo medido (l. 805).**
- **Cita:** «la aplicación solo ofrece lecturas literarias (290 entre A1 y B1)».
- **Por qué falla:** el documento dice **288** (`documento.md` l. 345 y 1401).
- **Arreglo:** unificar con la cifra verificada y su fecha.

**M3 · §4.2 y §8 (l. 785-809 y 2378-2383).**
- **Cita:** «53.179 libros de Project Gutenberg…», como si fuera todo el catálogo de la app.
- **Por qué falla:** el documento dice que el catálogo suma además 15.367 textos de licencia libre (68.546 en total; `documento.md` l. 367 y 1283). El cuadernillo no los menciona.
- **Arreglo:** una frase en §4.2 u §8.4 con los 15.367 textos libres y el total, fechados.

**M4 · Tabla de §5 (l. 1125) frente a la celda de sextiles (l. 1051-1069).**
- **Cita:** «Discretizar en 6 niveles con `qcut` | Poder comparar contra clasificadores y contra el MCER», frente a «seis clases relativas a este corpus, no niveles del Marco Común Europeo».
- **Por qué falla:** la tabla vuelve a presentarlos como comparables con el MCER, que es justo lo que la celda niega.
- **Arreglo:** en la tabla, «poder comparar clasificadores entre sí (sextiles, no MCER)».

**M5 · Figura 6, interpretación (l. 673-675).**
- **Cita:** «las materias más frecuentes de la §3.3 son ciencia ficción, relatos y aventuras».
- **Por qué falla:** §3.3 es el diccionario de datos. Las materias salen en la interpretación de relevancia del catálogo, que no lleva número.
- **Arreglo:** «las materias más frecuentes del catálogo (§3)».

**M6 · Tabla del bloque B (l. 1703-1720), §6.6 (l. 1412) y §9.1 punto 2 (l. 2431).**
- **Cita:** «exactitud … 0,46» y «error ordinal … 0,67» del transformador.
- **Por qué falla:** la fila de `roberta-base` del bloque B da RMSE y Pearson, y el 0,67 aparece en la columna de error ordinal. La exactitud 0,46 no sale en ninguna tabla. Además, la progresión de §9.1 mezcla 0,29 (experimento histórico con tres variables) con los 0,313 y 0,352 que recalcula el propio cuadernillo.
- **Arreglo:** añadir la exactitud 0,46 a la fila de `roberta-base` del bloque B (o quitarla de §6.6 y §9.1) y citar en §9.1 las cifras recalculadas, marcando las históricas como tales.

**M7 · §9.3, cuarta fila (l. 2485).**
- **Cita:** «Recalcular la validación con British Council (medias por nivel, Cuadro 13) | Sí, reconstruyendo el corpus con su manifiesto de hashes (§7.2)».
- **Por qué falla:** el propio §7.2 dice que los PDF se bajan a mano con el navegador (el CDN responde 403 a código) y que el recálculo se hace con `validar_local.py` desde la raíz del repositorio, con `pypdf` y el modelo, fuera del cuadernillo. La celda solo verifica hashes. «Sí» sin matiz dice más de lo que hace.
- **Arreglo:** «Sí, fuera del cuadernillo: descarga manual de los 59 PDF, verificación de hashes aquí y recálculo con `validar_local.py`».

**M8 · Celda de British Council (l. 2012) y §7.2 paso 1 (l. 1855).**
- **Cita:** «(la lista completa, en entrega/corpus_bc_manifiesto.csv)».
- **Por qué falla:** en un Colab limpio ese archivo no existe. La celda ya lleva el manifiesto entero, pero solo imprime las cinco primeras URL que faltan.
- **Arreglo:** imprimir las que falten (son 59 como mucho) o apuntar a la URL pública del CSV en el repositorio.

**M9 · Metadatos del `.ipynb`.**
- **Cita:** `"accelerator": "GPU"`, `"gpuType": "T4"`.
- **Por qué falla:** nada del cuadernillo necesita GPU: el v4 solo infiere unas ventanas en CPU. En un Colab gratuito sin GPU disponible, pedir T4 puede dar un aviso de «no hay GPU» o dejar al revisor en cola.
- **Arreglo:** quitar el acelerador de los metadatos y regenerar el `.ipynb`.

**M10 · Celda de descargas (l. 291-292 y 370-371).**
- **Cita:** `urllib.request.urlretrieve(URL_CLEAR, RUTA_CLEAR)`.
- **Por qué falla:** sin tiempo de espera ni reintento. Si GitHub o gutenberg.org fallan, la celda lanza una excepción y el resto del cuadernillo se cae, al contrario que la del v4, que degrada con aviso. Además, si una descarga anterior quedó a medias, `os.path.exists` la da por buena.
- **Arreglo:** envolver en `try` con un mensaje claro y comprobar el tamaño o la lectura antes de dar el archivo por bueno.

**M11 · Encabezado (l. 10) y §8.4 (l. 2378-2398).**
- **Cita:** «Entrega web al 14 de septiembre de 2026».
- **Por qué falla:** fechado antes del cierre. Hoy el Space ya lleva los reinicios 28-30 y la precarga del modelo del buscador. No es un error de cifra, pero la narrativa se desfasa respecto al documento.
- **Arreglo:** actualizar la fecha de sincronización al entregar.

**M12 · Rasgos propios (l. 861-864 y 900-903).**
- **Cita:** «Se usan las MISMAS expresiones regulares que `app/scoring.py`, no otras parecidas: si el troceado del cuadernillo divergiera del de la aplicación, los números dejarían de significar lo mismo».
- **Por qué falla:** las dos expresiones sí son idénticas (`PALABRA_RE` = `WORD_RE` y `FRASE_RE` = `SENT_RE`, `app/scoring.py` l. 39-40). Pero la aplicación solo cuenta como frase la que tiene al menos 3 palabras (`len(words(s)) >= 3`, l. 92), y el cuadernillo cuenta cualquier frase con una palabra (`if PALABRA_RE.findall(f)`). Con la misma expresión, `palabras_por_frase` sale distinto que en la app. No afecta al v4, que no usa estos rasgos, pero la frase dice más de lo que se cumple.
- **Arreglo:** aplicar el mismo filtro de 3 palabras en `rasgos_de_texto`, o decir «las mismas expresiones regulares; el filtro de frases cortas es propio de la app».

### DUDA

**D1 · Filtro global de avisos (l. 129-130).**
- **Cita:** `warnings.filterwarnings("ignore")`, y en la celda del v4 (l. 1498-1505) también se silencian los registros del Hub y de transformers.
- **Por qué es duda:** la rúbrica pide «sin warnings». Silenciarlos todos cumple la letra, pero oculta avisos útiles.
- **Qué oculta hoy**, medido en la ejecución local sin el filtro: un solo aviso real, `PendingDeprecationWarning: vert: bool will be deprecated in a future version. Use orientation…`, 3 veces, en los `sns.boxplot` de las Figuras 1, 6 y 7 (seaborn 0.13.2 con matplotlib 3.10.8). Los demás son `FigureCanvasAgg is non-interactive`, un artefacto de ejecutar sin pantalla que en Colab no aparece. En un Colab con esas versiones o más nuevas, ese aviso anuncia que los boxplots dejarán de funcionar igual.
- **Arreglo propuesto:** filtrar solo esa categoría y ese mensaje en vez de todos los avisos, o declarar el filtro global en «Antes de ejecutar».

La duda D2 de la primera versión del borrador (cifras escritas a mano en §4-§7.1 sin contraste en el documento) queda **resuelta**: la ejecución local las reproduce todas; ver abajo.

## Orden de la rúbrica

Datos (§3) → EDA (§4) → preparación (§5) → modelado (§6) → evaluación (§7) → negocio (§8) → conclusiones (§9): **correcto**.

Dos matices, sin hallazgo:
- La partición y la lista de palabras familiares se calculan dentro del EDA (§4.3), antes de §5, y está justificado en la celda (evita fuga en `palabras_raras`).
- El catálogo medido por el v4 (Figura 8 y la tabla siguiente) aparece en el EDA aunque es un resultado del modelo. Se lee bien como contraste con el catálogo v1.

## Comprobado y correcto

- **Sincronía:** el `.ipynb` coincide con el `.py` en las 103 celdas.
- **URL:** las dos descargas públicas responden 200, y el repositorio del v4 es público y se descarga sin token.
- **Sin llamadas a OpenAI**, sin `drive.mount`, sin rutas locales `C:\` o `D:\` y sin `!pip install`.
- **Constantes del troceado:** `BLOCK_WORDS = 250`, `MIN_WORDS = 150`, `MAX_BLOCKS_PER_DOC = 8` y `MAX_LENGTH = 256`, idénticas a `app/scoring.py` l. 19-22.
- **Expresiones regulares:** `PALABRA_RE` y `FRASE_RE` son las mismas que `WORD_RE` y `SENT_RE` de `app/scoring.py` (l. 39-40). El filtro de frases cortas difiere: ver M12.
- **Letra MCER con empate hacia arriba:** `floor(x · 2,5 + 0,5)` en `ancla_publica`, la misma regla que `app/scoring.py` l. 166.
- **El modelo es opcional:** la celda del v4 captura cualquier excepción y sigue; `puntuar_ventanas` se salta sin modelo; XGBoost se importa con `try`.
- **Validación externa:** n = 3 + 8 + 12 + 12 + 12 = 47 textos, y las medias por nivel coinciden con `documento.md`. Spearman 0,860 del v4, 0,807 de contar palabras y 0,668 de la correlación parcial, como en `documento.md` (l. 730 y 846-850).
- **Validación interna del v4:** 0,908 y 97,2 % sobre 144 documentos; partición 510 / 144 de ELG CEFR English (`documento.md` l. 728 y 742).
- **Catálogo medido:** 1 + 40 + 558 + 3.127 + 23.454 + 25.999 = 53.179, con 93,0 % en C1-C2 y 599 en A1-B1. 3.644 capítulos en 1.499 libros y 585.111 capítulos, como en el documento.
- **UniversalCEFR retirado:** 0,946 sobre 739 textos, como en el documento.
- **OneStopEnglish:** 560 unidades; Spearman 0,800, parcial 0,688, 183 y 179 de 185, como en el documento.
- **Graduados:** StoryWeaver 0,426 / 0,206, African Storybook 0,416 y Let's Read 0,178, presentes en el documento.
- **Coste de la cuenta:** 7 USD/mes de cuenta Pro, como en el documento.

## Ejecución local de las celdas ligeras

- **Qué y dónde:** las 43 celdas de código anteriores a la carga del v4 (§3 a §6.5; incluye CLEAR, catálogo, EDA, rasgos, PCA, partición y los siete modelos clásicos), en `D:\Temp\auditoria_nb`, fuera del repositorio. Las celdas se convirtieron a un guion con backend Agg y las expresiones sueltas finales envueltas en `print`.
- **Entorno:** no es Colab: Python 3.11, numpy 2.4.2, pandas 3.0.0, matplotlib 3.10.8, scipy 1.17.1, scikit-learn 1.9.0, openpyxl 3.1.5, xgboost 3.2.0. seaborn 0.13.2 se instaló aparte en una carpeta temporal, sin tocar el entorno global.
- **Resultado:** terminan sin errores en 21 s, con las dos descargas públicas incluidas. No se ejecutaron la carga del v4 (328 MB), su demostración de inferencia, la celda de British Council ni la de graduados.
- **Cifras escritas a mano que se reproducen:**
  - BT_easiness: media −0,958, mediana −0,909, desviación 1,034, asimetría −0,134, curtosis −0,486 y rango −3,676 a 1,711.
  - Extractos: de 129 a 205 palabras, media 173,3 y desviación 17,0.
  - Ausentes: `Sub Cat` 87,6 %, `License` 70,3 % y `Anthology` 42,6 %; 4.658 títulos.
  - Dominio: 2.420 Lit y 2.304 Info, medianas −0,636 y −1,314, p = 4,01·10⁻⁸⁸.
  - Métricas clásicas: `CAREC_M` −0,582, `SMOG` −0,563, `New Dale-Chall` −0,557, `CML2RI` +0,563, `Flesch-Reading-Ease` +0,547, `Google WC` −0,125, `Sentence Count` +0,362 y `Paragraphs` +0,250.
  - Lexile: Spearman −0,504.
  - Rasgos propios: `palabras_raras` −0,490, `polisilabas` −0,477 y `silabas_por_palabra` −0,447.
  - PCA: 55,1 % y 14,9 %, con PC1 a 0,614 de BT_easiness.
  - Sextiles de 787 y 788 extractos; partición 3.774 / 950 con 0 títulos compartidos.
  - Regresión, RMSE: media 1,048, lineal con 11 variables 0,764, con 17 variables 0,748 y Random Forest 0,767 («≈0,77»). Spearman 0,707 y 0,686.
  - Importancias del Random Forest: `New Dale-Chall` 0,348 («alrededor del 35 %») y `CML2RI` 0,125.
  - Clasificación, exactitud y error ordinal: logística con 3 variables 0,313 y 1,295; con 17 variables 0,352 y 1,061; XGBoost 0,340 y 1,081.
  - Catálogo v1: 723 de 1.197 en A1 y 121 en B1-B2.
- **Diferencia esperada:** el catálogo vivo de Gutenberg ya da 79.381 entradas y 61.675 libros de texto en inglés, frente a los 79.337 y 61.642 del texto. La celda lo avisa en un comentario; el markdown no (ver M1).
- **Avisos:** con el filtro global, ninguno. Sin él, el `PendingDeprecationWarning` de seaborn de D1.
