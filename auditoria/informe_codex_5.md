# Informe Codex 5

Fecha: 9 de septiembre de 2026. **Revisión terminada.** Último commit observado: `bbbb04e`.

Recuento de observaciones vigentes: **CRÍTICO 0 · SERIO 10 · MENOR 11**.

- Presentación: **3 SERIOS y 3 MENORES**. Una discrepancia numérica adicional, B2, quedó corregida por un cambio concurrente y se excluye del recuento.
- Inventario: **7 SERIOS y 8 MENORES** todavía abiertos o parciales. **16 YA CERRADOS · 12 CERRADOS A MEDIAS · 3 SIGUEN ABIERTOS · 2 NO VERIFICABLES**. Los dos últimos no se contabilizan como errores demostrados.
- Las cifras cuentan entradas de este informe, no causas independientes: una limitación puede afectar tanto al inventario como a su presentación pública. Gravedad actual según impacto: evidencia y validez del resultado = SERIO; precisión editorial, rotulación y trazabilidad residual = MENOR.

Alcance: presentación frente a `entrega/documento.md` y revisión de los estados abiertos o parciales de `auditoria/estado_real.md`. Consultas mediante `grep`; no se han abierto otros archivos de `auditoria/`, salvo el encargo. La única escritura es este informe. Las referencias son las líneas actuales, no las del inventario antiguo.

Los demás archivos citados se consultaron únicamente como fuentes exigidas por las partes A y B del encargo. No se hicieron cambios en ellos, ni compilaciones, ni ejecuciones de la aplicación, ni llamadas de pago. Los estados remotos de despliegue se contrastan con el documento y el contexto explícito del encargo; no se presentan como una comprobación nueva de disponibilidad en Internet.

## Parte A — Presentación

### A01 · CORREGIDO DURANTE LA REVISIÓN · La media B2 conservaba el valor anterior

La primera consulta de `entrega/presentacion.tex:231` mostró **B2 1,248**, frente a **1,2414** en `entrega/documento.md:42,702,1120`. Durante la auditoría, una modificación concurrente cambió la presentación a **1,241**, el redondeo correcto. **Codex no hizo ese cambio. No se cuenta como defecto vigente.**

La corrección terminó en el commit `bbbb04e` («la presentacion daba la media de B2 anterior»). La revisión final de esa línea ya usa el contenido corregido.

### A02 · MENOR · Tres preguntas frente a seis preguntas y tres fragmentos

`entrega/presentacion.tex:144,251` promete «tres preguntas». `entrega/documento.md:824` describe **«Seis preguntas sobre hábitos observables y tres fragmentos reales en escalera»**. No son dos formas de contar lo mismo: se redujo el cuestionario y se confundieron preguntas con fragmentos. Corrección propuesta: «cuestionario breve y tres fragmentos», o el recuento completo del documento.

### A03 · SERIO · Un ejemplo se presenta como un caso real acreditado

`entrega/presentacion.tex:243` anuncia **«Un caso real, de principio a fin: Ana, 15 años, nivel B1»**; `:251,267-271` le atribuye un perfil **0,93**, diez recomendaciones y el recorrido con *Sherlock Holmes* y *peculiar*. El documento acredita una sola prueba de usuario: **Esmeralda**, n=1 (`entrega/documento.md:1081-1084`), prima del autor (`:54,196`). Su recorrido con números reales parte de **1,20/B2** (`:832-835`) y analiza *Notes from a Dead House* (`:854-858`).

El documento no respalda que el recorrido concreto de Ana haya ocurrido ni que esos números sean resultados observados. Esto **no demuestra que el caso sea inventado**; demuestra que su carácter real no está acreditado por la fuente de verdad del encargo. Corrección propuesta: rotularlo «ejemplo ilustrativo» o reproducir el caso documentado. Si Ana es un seudónimo, declararlo no sustituye la evidencia del recorrido y del 0,93.

### A04 · SERIO · Las 3–5 horas pierden sus supuestos y se leen como plazo de finalización

`entrega/presentacion.tex:328` pone **«Terminar la medición del catálogo / 3–5 h de A100»** sin salvedad. `entrega/documento.md:914-920` explica que es una **extrapolación de cómputo**: el promedio de ventanas del catálogo todavía no está medido; 350 supuestas dan 2,96 h y 606,4 de cinco novelas largas dan 5,14 h. Además `:921-927` separa el cuello de botella de descarga.

La cifra coincide, pero su alcance se amplió: no es un plazo medido para terminar todo el proceso. Corrección propuesta: «≈3–5 h de cómputo A100, estimadas; descarga aparte».

### A05 · MENOR · El catálogo carece de un estado explícito «en curso»

`entrega/presentacion.tex:329` dice **«El catálogo publica niveles medidos, no heredados»**. Es relevante que esté bajo **«Cuándo está hecho»** (`:322`) y que la acción sea **«Terminar»** (`:328`): puede leerse correctamente como criterio futuro, por lo que **no es prueba de que la presentación declare falsamente terminado el catálogo**. Sin embargo, las otras dos filas llevan «Hecho» y esta no dice «en curso» ni identifica las etiquetas actuales.

El documento sí lo explicita: la remedición está **en curso** y las etiquetas actuales son heredadas del v1 (`entrega/documento.md:649-651`), sobre unas 190 palabras (`:296-298`). Corrección propuesta: «En curso. Terminado cuando el catálogo publique niveles v4». Así se elimina la ambigüedad sin cambiar el objetivo.

### A06 · SERIO · Se omiten las salvedades que determinan cómo interpretar la evaluación

Hay dos lugares concretos:

- `entrega/presentacion.tex:157-177` muestra el progreso **1,061 → 0,93 → 0,67** sobre «950 muestras reservadas», sin decir que esas mismas muestras eligieron la época del transformador. `entrega/documento.md:541-549` advierte que son **validación de selección**, no test independiente, y que el error ordinal corresponde a **sextiles de CLEAR**, no a niveles MCER del modelo desplegado.
- `entrega/presentacion.tex:220-223` presenta **97,2 % / 0,908 / n=144** sin la limitación de evidencia. `entrega/documento.md:660-667` dice que no hay en el repositorio un archivo que respalde esas métricas; `:684-690` añade que la ventaja empírica frente a un predictor constante no está medida, porque falta la distribución del conjunto.

Las cifras están copiadas correctamente. El problema es el grado de garantía que su presentación sin estas notas permite atribuirles. Corrección propuesta: dos notas breves: «Validación usada para elegir época; ordinal sobre sextiles CLEAR» y «Métricas internas reportadas; parejas de validación no publicadas». No hace falta trasladar todo el apartado metodológico a una diapositiva.

### A07 · MENOR · «Un atajo que en una biblioteca no existe» no está demostrado

`entrega/presentacion.tex:201-204` convierte el diagnóstico de longitud en exámenes en una negación categórica para bibliotecas. `entrega/documento.md:410-417,757-765` demuestra la confusión **dentro de British Council**, pero no una ausencia de relación entre longitud y dificultad en novelas. Además, el vínculo con elegir/terminar libros queda pendiente (`:1108-1110,1130`). Corrección propuesta: «un atajo ligado al diseño de esos exámenes, cuya utilidad fuera de ese corpus no está demostrada».

### Comprobación de todas las cifras de contenido

Se extrajeron los números del `.tex`, incluidos los de coordenadas de las gráficas, y se separaron de parámetros de maquetación (colores hexadecimales, tamaños, proporciones de columnas, compatibilidad PGFPlots, límites de ejes y numeración de pasos). Esos parámetros no son afirmaciones empíricas que deban aparecer en el documento. También se revisaron cantidades escritas con palabras.

| Cifra o grupo | Presentación | Contraste y resultado |
|---|---|---|
| Módulo 5, generación 34, septiembre 2026 | `entrega/presentacion.tex:71,98` | Coinciden con `entrega/documento.md:3-7`. |
| 4.724 extractos | `:122` | Coincide con `entrega/documento.md:219`. |
| 654 documentos | `:125` | Coincide con `entrega/documento.md:655-658`; la composición pendiente se trata en B26. |
| 61.642 libros | `:128` | Coincide con `entrega/documento.md:223`; es el catálogo objetivo, no un recuento de libros ya medidos. Véase A05. |
| 950 muestras; 17 variables; embedding de 384 dimensiones | `:157,167` | Coinciden con `entrega/documento.md:535,558,560`; salvedad metodológica A06. |
| 1,061; 0,93; 0,67 | `:175-177` | Coinciden con `entrega/documento.md:558,560,562`. El gráfico configura dos decimales (`presentacion.tex:171`), por lo que 1,061 se muestra como 1,06: redondeo correcto. |
| XGBoost de 300 árboles | `:184` | `entrega/documento.md:572-573,801` respalda la comparación, pero **no especifica 300**. Comprobación complementaria en el cuaderno ya consultado: `entrega/notebook_proyecto.py:1296-1297`, `n_estimators=300`. Sin discrepancia demostrada. |
| 0,855 modelo; 0,799 palabras; 0,665 parcial; 46 textos | `:193,196,204` | Coinciden con `entrega/documento.md:747-755`. |
| 82 millones de parámetros | `:216` | Coincide con `entrega/documento.md:641-642`. |
| ±1 nivel; 144; 97,2 %; 0,908 | `:220-222` | Coinciden con `entrega/documento.md:669-675`; evidencia limitada, A06. |
| 38 externos; 100 %; 0,829 | `:223` | Coinciden con `entrega/documento.md:672`. Son los resultados históricos de Colab, distintos de los 46 locales (`:1025-1026,1120-1121`); el 45 residual de esa limitación se registra en B02. |
| A1 0,504; A2 0,548; B1 0,928; B2 1,241; C1 1,495 | `:230-231` | Todos son redondeos correctos de `entrega/documento.md:699-703` tras la corrección concurrente A01. |
| Tres textos A1; «los otros cuatro» | `:236` | Tres textos: `entrega/documento.md:699`. La expresión sobre los escalones también está en `:44-45`; no es una afirmación más fuerte introducida por la presentación. |
| Tres preguntas; 15 años; 0,93; 0–2; diez recomendaciones | `:144,243,251,267-268` | Escala 0–2 correcta (`entrega/documento.md:48,651-653`); edad compatible con la lectora documentada (`:54`). El recuento de preguntas contradice `:824`; el perfil y las diez recomendaciones de ese caso no están acreditados: A02–A03. |
| Pearson 0,517 / 0,725 / 0,89 | `:294-296` | Coinciden con `entrega/documento.md:958-965`. El 0,89 corresponde al modelo CLEAR descrito en `:575-582`, no es una nueva métrica externa del v4. La advertencia sobre no comparar cara a cara se conserva. |
| Treinta años de Lexile | `:308` | Coincide con `entrega/documento.md:975`. Concordancia documental, no investigación histórica independiente. |
| 30 min; publicación gratuita | `:324` | El documento confirma la publicación (`entrega/documento.md:1053-1056`) pero **no cuantifica 30 minutos**. La estimación procede de la estrategia: `entrega/estrategia.md:363`, «~30 min; gratuito». No es duración medida acreditada por el documento. |
| 7 USD/mes | `:326` | Coincide con `entrega/documento.md:1068`. El despliegue está hecho según `:1065-1069` y el contexto del encargo. |
| 3–5 h de A100 | `:328` | Coincide numéricamente con `entrega/documento.md:915-920`, pero faltan los supuestos: A04. |
| 328 MB y número de pruebas | No aparecen como cifras de contenido en la presentación | No hay valor que corregir en ella. Se verificaron expresamente **328 MB**, **205 pruebas** y **27 pasos** en el inventario: B19 y B21. |

Las cifras **0,854 / 0,807 / 0,657 / 45** no aparecen como resultados antiguos en la presentación revisada. Los dígitos que coinciden dentro de colores, tamaños o identificadores no son residuos estadísticos.

## Parte B — Inventario

Se revisaron las **33 entradas detalladas** cuyo veredicto contiene `ABIERTO` o `CERRADO A MEDIAS`, incluida H23, que mezcla cerrado y abierto. No se revisaron de nuevo las entradas cerradas, falsas o no verificables. Las listas-resumen finales del inventario no se cuentan otra vez.

El recuento inicial de `auditoria/estado_real.md:14` dice **29 abiertos + 9 parciales**, pero no coincide con estas 33 entradas detalladas seleccionables. Se siguieron los veredictos de cada entrada, no ese total desactualizado. No quedaron entradas seleccionadas sin revisar. Para reproducir el recuento de gravedad: SERIOS vigentes B05, B06, B09, B10, B12, B26 y B29; MENORES vigentes B02, B07, B13, B15, B16, B18, B23 y B32.

En la columna de origen, `ER` significa `auditoria/estado_real.md`; la línea identifica el veredicto antiguo. «YA CERRADO» significa que se resolvió la objeción concreta, no que se hayan reproducido todos los experimentos. La revisión es estática: no se ejecutaron pruebas que escriben datos, cachés o resultados.

| # | Hallazgo | Veredicto HOY | Dónde y cita |
|---|---|---|---|
| B01 | Las 6,3 h de A100 (ER:85) | **YA CERRADO** | `investigacion/competencia.md:119,326,483` y `investigacion/transformer_v5.md:190` ya dicen «entre tres y cinco horas». `entrega/documento.md:915-920` declara los supuestos de la horquilla. |
| B02 | Filtro de prosa y balance de textos (ER:107) | **CERRADO A MEDIAS** | El pie ya dice «46 textos» y «extracción […] y el filtro» (`entrega/documento.md:705-707`); el balance y sus causas están en `:725-743`, y `README.md:113-115` cierra 59−1−2−10=46. Persiste «45 en local» en `entrega/documento.md:1026` y `entrega/documento.tex:2371`. La pérdida de saltos de línea se trata por separado en B10. |
| B03 | Lotes de 64/128 atribuidos al recorrido interactivo (ER:222) | **YA CERRADO** | `entrega/documento.md:883-887`: «La aplicación en vivo no llega a esos lotes», con rendimiento interactivo separado; `entrega/documento.tex:2143-2144` lo repite. Es coherente con `app/ui.py:1197-1199`, que llama por capítulo. |
| B04 | Ocho ventanas presentadas como validación de un libro entero (ER:237) | **YA CERRADO** | `entrega/notebook_proyecto.py:1573-1578` ahora dice «Hay una medición […] de un solo texto» y «no se puede afirmar que ocho ventanas basten en general». `entrega/documento.md:484` identifica expresamente el capítulo de 23 ventanas. La afirmación universal objetada desapareció. |
| B05 | Ficha de muestra y tiempo «a tu ritmo» (ER:260) | **CERRADO A MEDIAS** | Tiempo corregido: `entrega/documento.md:846-848`, «180 o 110 […] no es su ritmo medido». Sigue «todo […] contado sobre el fichero» (`:845`) sin declarar el muestreo para las otras estadísticas. `app/ficha.py:159,183,203-204`: `_muestra`, objetivo 60.000 palabras y riqueza sobre los primeros 20.000 tokens. |
| B06 | Utilidad personal y peso heurístico (ER:276) | **CERRADO A MEDIAS** | El resumen ya promete «libros que le queden a mano» (`entrega/documento.md:29-30`), y medir el abandono sigue siendo trabajo futuro (`:1108-1110`). El peso `PESO_FRAGMENTOS = 0.65` sigue en `app/perfil.py:210,243-244`; `entrega/estrategia.md:50` lo publica pero lo justifica con «la gente se juzga mejor», sin presentarlo como peso heurístico no validado. |
| B07 | Velocidades contradictorias (ER:287) | **CERRADO A MEDIAS** | `arrancar_gpu.py:13-14` ya unifica **8,19 / 112,7 / 13,8×**. Queda el residuo **MAE 0,0000012** en `:17`, frente a **0,000001** en `app/scoring.py:209-210` e `informe_velocidad.md:189`. El problema de velocidad está cerrado; queda un decimal sin respaldo en la misma corrección. |
| B08 | Cuadro del baseline sin guion (ER:298) | **YA CERRADO** | `validar_local.py:89` recoge puntuación y longitud; `:139-164` calcula Spearman y parcial, e imprime los coeficientes. `entrega/documento.md:753-755` atribuye el cálculo al guion. El cuadro ahora es el **12** en el documento; la cadena del guion aún lo llama 11 (`:160`), pero el cálculo ya existe. No se afirma haber reproducido sus valores en esta auditoría. |
| B09 | Recta 0,72x+0,38 sobre puntos que no la ajustan (ER:314) | **CERRADO A MEDIAS** | `entrega/documento.md:767-773` y `entrega/documento.tex:1768-1773` ya explican «cuatro medias […] Colab». La figura aún dibuja esa recta (`.tex:1816`) junto a las cinco medias locales (`:1821`), y el pie vuelve a decir que «la pendiente es 0,72» sin distinguir procedencias (`:1841-1845`). Falta la aclaración en el propio gráfico/pie. |
| B10 | El validador une líneas y anula el detector de listas (ER:329) | **SIGUE ABIERTO** | `validar_local.py:40-44` conserva `return " ".join(utiles) or None` y lo justifica por el contador de palabras. Pero `app/scoring.py:68-72` usa `splitlines()`, dos viñetas o seis líneas para detectar maquetado. Esos dos caminos no pueden dispararse sobre una sola línea. Los demás filtros sí pueden actuar; no se afirma que todo el filtro esté inerte. |
| B11 | Escala del MAE 0,499 (ER:347) | **YA CERRADO** | `entrega/documento.md:674-676` y `entrega/documento.tex:1602-1604`: «escala interna 0–5 —0,200 en la escala pública 0–2—». |
| B12 | Validación externa del cuaderno tecleada como si fuera cálculo (ER:356) | **CERRADO A MEDIAS** | El título ahora dice «no del todo ciega» (`entrega/notebook_proyecto.py:1684`). La celda aún construye constantes en `:1699-1703`, sin identificarse allí como tabla citada, y evalúa sus medias (`:1708`). Además `n=[3,7,12,11,12]` suma **45**, aunque imprime **46** (`:1701,1704`) y B2 ya usa la media nueva. |
| B13 | Audio de Wiktionary confundido con funcionamiento sin red (ER:412) | **CERRADO A MEDIAS** | `README.md:191-192`, `entrega/estrategia.md:213-216` y `entrega/documento.tex:743-746` ya separan la descarga del navegador. La limitación todavía incluye «los enlaces de audio […] que descarga el navegador» dentro de «todo lo que no usa red» (`entrega/documento.md:1085-1088`; `.tex:2429`). `app/ui.py:1638-1645` genera un `<audio>` con URL HTTP. |
| B14 | 286 frente a 300 ventanas (ER:426) | **YA CERRADO** | `entrega/documento.md:903-905` y `entrega/documento.tex:2209-2210` ya dicen **300/300**, concordando con `app/scoring.py:257`. |
| B15 | «No hay relleno» como afirmación general (ER:436) | **CERRADO A MEDIAS** | §8.3 ya distingue ventanas completas y cortas: `entrega/documento.md:903-911` reconoce `padding` y diferencias no idénticas bit a bit. Subsiste en T4 «250 palabras inglesas siempre superan 256 BPE. No hay relleno que optimizar» (`:481`; `entrega/documento.tex:1239`), sin acotar esa conclusión al ensayo de 200 bloques. |
| B16 | «Sin mover un decimal» (ER:447) | **SIGUE ABIERTO** | El titular ahora es «sin mover ninguna cifra que se publique» (`entrega/documento.md:1177`), pero la misma explicación admite una ventana distinta en **0,001**, con **839/840** iguales a tres decimales (`:1179-1181`). `:911` fija en tres decimales lo guardado. La salvedad numérica contradice todavía el absoluto del titular. |
| B17 | −0,330 atribuido a 18 libros (ER:456) | **YA CERRADO** | `entrega/documento.md:1172-1174` separa el paso desde 18 libros y la muestra de **397**, a la que atribuye **−0,330**; `:395` mantiene esa correspondencia en la tabla. |
| B18 | «De seis niveles a cuatro» (ER:466) | **CERRADO A MEDIAS** | `entrega/documento.md:421-423` y `entrega/documento.tex:1155-1157` ya dicen **cinco**, no seis. Falta especificar en esa frase que los cuatro A2–C1 corresponden a la tanda/filtro del análisis: el Cuadro 10 actual conserva A1 y cinco niveles (`documento.md:697-703`). |
| B19 | Recuentos de pruebas (ER:475) | **YA CERRADO** | `README.md:152-153`, `entrega/estrategia.md:143,223,391` y `entrega/documento.tex:678,752,838` coinciden en **205 pruebas / 27 pasos**. `grep` cuenta 205 líneas de llamadas `prueba(` y 27 de `paso(`, excluyendo las definiciones (`pruebas_extremas.py:37`; `pruebas_integracion.py:37`). Los bucles inspeccionados recorren casos dentro de pruebas, no añaden llamadas al contador. La objeción antigua de «28 pasos» era falsa: incluía `def paso`. Se verificó el recuento estático, no el éxito de ejecución. |
| B20 | «Peor paleta 9,51» (ER:486) | **YA CERRADO** | `entrega/estrategia.md:133,390` ya distingue **4,53 texto / 3,11 título**, y 40 parejas. `pruebas_extremas.py:818-823` incluye pestaña elegida y los tres colores del título, con umbral 3,0 para estos últimos. Se verificó la corrección documental y el alcance de la prueba, sin repetir la medición de color. |
| B21 | 328 MB frente a 317 MB (ER:497) | **YA CERRADO** | `README.md:169` ahora dice **328 MB**, igual que `entrega/documento.md:642`. Se cerró la discrepancia publicada; no se inspeccionaron ni regeneraron los pesos. |
| B22 | Descarga privada en Drive frente a modelo público (ER:504) | **YA CERRADO** | `app/scoring.py:185-187` remite a `MikeMaki1763/literalevel-v4`, «repositorio publico, sin credenciales». `README.md:169,178-180` coincide con `entrega/documento.md:1053-1056`. Es concordancia local, no nueva comprobación del servicio remoto. |
| B23 | Gradio no fijado a la versión declarada (ER:518) | **CERRADO A MEDIAS** | `requirements.txt:7` identifica la versión probada **6.26.0** y `:12` acota `gradio>=6.26,<7`; ya no admite 6.0 ni futuras mayores. Sigue permitiendo menores posteriores a 6.26. El pin exacto solicitado por el inventario no está implementado; no se afirma que una versión futura haya roto la aplicación. |
| B24 | Informe de velocidad sin terminar (ER:525) | **YA CERRADO** | `informe_velocidad.md:214-220` explica que recomendación y extrapolación se trasladaron a §8.3, y `:224` remite a esa nota. Ya no son apartados «pendientes» sin explicación. |
| B25 | Tope de ocho ventanas omitido en §7.4 (ER:536) | **YA CERRADO** | `entrega/documento.md:643-650`: «tope de ocho ventanas por documento» y distinción frente al recorrido completo del catálogo. Concuerda con `app/scoring.py:21`. |
| B26 | Composición y partición del anclaje MCER (ER:596) | **SIGUE ABIERTO** | `entrega/documento.md:1039-1048` sigue declarando «su composición no está publicada»; `entrega/notebook_proyecto.py:2015-2021` reconoce la ausencia de composición por fuente/nivel. El documento pide publicar las 144 parejas anónimas en `:1062-1064` y dice «No está hecho». Falta la evidencia; no se infiere que exista fuga de datos. |
| B27 | Desviación fp16 A100 = 0,00037 sin registro (ER:611) | **NO VERIFICABLE** | `entrega/documento.md:805` y `entrega/documento.tex:1887` ya dicen «tampoco quedó guardada». `informe_velocidad.md:190-191` respalda **0,00035 local**, no 0,00037 A100. Mejoró la declaración de incertidumbre, pero no apareció evidencia que permita certificar la cifra. |
| B28 | Máximo 0,004 en cinco libros sin registro (ER:619) | **NO VERIFICABLE** | `entrega/documento.md:800` y `entrega/documento.tex:1877` ahora declaran «no queda guion que la reproduzca» y «orden de magnitud, no […] cifra auditable». No se transforma esa admisión en una verificación positiva. |
| B29 | Parejas individuales del baseline (ER:634) | **CERRADO A MEDIAS** | `validar_local.py:62,89,143-164` ya reúne en memoria nivel, puntuación y palabras y calcula las correlaciones. Solo imprime agregados: las salidas están en `:94-104,160-166`; no publica las filas con identificadores. La aritmética puede recalcularse reuniendo los PDF, pero sigue sin quedar la tabla individual pedida. |
| B30 | Parentesco de la lectora omitido (ER:641) | **YA CERRADO** | `entrega/documento.md:54,196` ya dice «prima del autor y ajena al proyecto»; `:1081-1084` conserva n=1 y el alcance cualitativo. |
| B31 | Desviaciones poblacionales sin identificar (ER:650) | **YA CERRADO** | `entrega/documento.md:697`: «Desviación (poblacional)». `validar_local.py:91-99` explica `ddof=0` y rotula «desv (pobl.)». |
| B32 | Manifiesto de los 59 PDF (ER:656) | **CERRADO A MEDIAS** | `entrega/documento.md:741-743` ya enlaza `entrega/manifiesto_corpus_externo.md`. Este enumera **58** archivos (`:16-18`, secciones desde `:23`), pero el supuesto documento 59 sigue descrito solo como «uno que ya no está disponible […] del que solo queda la referencia» (`:20-21`), sin identificarlo allí. Está resuelta la lista disponible, no el inventario completo de 59 con procedencia. |
| B33 | Frase rota «Lo detectó una» (ER:678) | **YA CERRADO** | `entrega/documento.md:665-667` ahora termina «[…] rehacerla. Se corrige diciéndolo, no citando un archivo que no existe». Ya no hay fragmento sin sujeto. |

## Lo que está bien y podía estar mal

- Modelo **0,855**, contador **0,799**, parcial **0,665** y **46 textos**: `entrega/presentacion.tex:193,196,204`; `entrega/documento.md:747-754`.
- Despliegue **7 USD/mes**: `entrega/presentacion.tex:326`; `entrega/documento.md:1068`.
- **0,908 / 97,2 % / 144** internos y **0,829 / 100 % / 38** externos de la tanda histórica: `entrega/presentacion.tex:222-223`; `entrega/documento.md:671-672`. El 38 pertenece a otra tanda: no debe reemplazarse mecánicamente por 46.
- La comparación competitiva sí avisa «No son comparaciones cara a cara» y «no demuestran una victoria medida»: `entrega/presentacion.tex:302-305`.
- La presentación declara que no certifica el MCER (`entrega/presentacion.tex:344-349`), como exige `entrega/documento.md:48-51`.
- El reconocimiento de la debilidad A1–A2 acompaña las medias (`entrega/presentacion.tex:235-237`), coherente con `entrega/documento.md:43-45`.
- La publicación del modelo y el enlace de despliegue se presentan como hechos (`entrega/presentacion.tex:324-327,359-362`), coherentes con los apartados actualizados del documento (`entrega/documento.md:1053-1069`). Se detectó que la conclusión de este último todavía dice «su enlace es temporal» (`:1193-1194`): es un residuo en la fuente, **no un error que deba copiarse a la presentación**, dado el contexto explícito del encargo. Se deja constancia sin abrir otra auditoría ni añadirlo al recuento.

## Límites de la comprobación

Se verificaron afirmaciones, cifras y código por inspección localizada. No se reprodujeron métricas del modelo, sesiones de usuario, rendimiento de GPU, ni resultados de ejecución de las pruebas. «Coincide» significa concordancia con la fuente indicada; no convierte una métrica reportada en una medición independiente. El estado final de Git solo mostraba este informe sin seguimiento; la modificación concurrente de presentación ya estaba incorporada en `bbbb04e`.
