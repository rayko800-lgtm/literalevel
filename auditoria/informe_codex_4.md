# Auditoría externa de estrategia y cuadernillo

Fecha: 9 de septiembre de 2026. Alcance: `entrega/estrategia.md` completo y celdas de texto de `entrega/notebook_proyecto.py`. El código se consulta únicamente para contrastar afirmaciones. No se han leído revisiones de `auditoria/` ni modificado los archivos examinados. Las referencias a investigación son evidencia de contraste, no una auditoría adicional.

## Hallazgos SERIOS

[SERIO] La comparación con los LLM se presenta como una victoria experimental que no se ha medido
Dónde:      entrega/estrategia.md:272-277
Qué dice:   «la evidencia publicada dice que **no gana en esta tarea**: el mejor método *zero-shot* documentado alcanza **0,725** en CLEAR, frente al 0,89 de un codificador afinado».
Por qué:    La fuente existe, pero no es una evaluación cara a cara del proyecto. Grossman y Chen evalúan CLEAR con n = 1.890 y diez LLM abiertos; no evalúan LiteraLevel ni todos los LLM disponibles. Compartir el nombre del corpus no equivale a compartir los textos de prueba. Además, `investigacion/competencia.md:168-169` advierte de la comparabilidad limitada y `:319-320` reconoce que falta el experimento en Cambridge. La estrategia elimina esas reservas. El mismo estudio compara fórmulas inglesas FKGL y ARI: su 0,517 tampoco establece un techo universal para Flesch, Dale-Chall y ATOS, como sugiere `estrategia.md:256-260`. Fuente primaria: [Grossman y Chen, tablas 1 y 3 y §4.1](https://arxiv.org/html/2604.24470v1).
Arreglo:    Presentar cifras como referencias publicadas con corpus, n, método y protocolo; sustituir «no gana» por «estas referencias motivan la elección de un codificador; falta comparación bajo el mismo protocolo». Identificar las fórmulas realmente evaluadas y enlazar el artículo en las referencias de la estrategia.

[SERIO] La ventaja económica mezcla una licencia anual con horas de inferencia sin precio
Dónde:      entrega/estrategia.md:266-270
Qué dice:   «sus licencias institucionales van de **3.824 a 54.636 USD al año**»; «medirlos con este proyecto son entre tres y cinco horas de una GPU alquilada. Esa diferencia de tres órdenes de magnitud es el argumento económico del trabajo».
Por qué:    Los importes están respaldados: son los tramos del Text Analyzer para creadores de contenido, no el precio general que debe pagar cualquier lector por usar Lexile. 61.642 envíos caben en el tramo 50.001–65.000. Sin embargo, dólares/año y horas de GPU no permiten calcular una razón monetaria. Para un ahorro de al menos 1.000 veces frente a 54.636 USD, el coste comparable de LiteraLevel tendría que ser ≤54,636 USD, cifra que aquí no se calcula. La investigación cita 6,3 horas (`investigacion/competencia.md:117-121`), no 3–5, mientras la propia estrategia admite que desconoce el número medio de ventanas (`:183-184`). Tampoco son prestaciones equivalentes: la estrategia reconoce que su escala no tiene la aceptación institucional de Lexile. Fuente primaria: [MetaMetrics, tarifas de creador de contenido 2026](https://www2.metametricsinc.com/content-creator-annual-pricing).
Arreglo:    Mantener la tabla de precios, con su producto y alcance. Separar estimación y medición, reconciliar 3–5 y 6,3 horas, añadir tarifa de GPU y supuestos de coste y describir el resultado como comparación de costes de procesamiento bajo esos supuestos, no de servicios equivalentes.

[SERIO] Se promete una exclusividad de auditabilidad y gratuidad que el propio texto desmiente
Dónde:      entrega/estrategia.md:310-313
Qué dice:   «**Es auditable y cuesta cero.** [...] cualquiera puede comprobar los números o rehacerlos. De las alternativas de esta sección, ninguna permite eso».
Por qué:    La misma estrategia reconoce que las fórmulas clásicas son gratuitas e interpretables (`:256-257`); su cálculo se puede reproducir. Por otra parte, el cuadernillo declara que no se pueden recalcular las métricas del v4 por ausencia del corpus de evaluación y del entrenamiento (`notebook_proyecto.py:1953-1957, 1968-1985`). Publicar pesos permite inferencia, no rehacer esos resultados. «Cuesta cero» tampoco distingue gratuidad para el lector de los costes de alojamiento y servicio externo que el propio documento contempla en A2, A4 y riesgos.
Arreglo:    Decir qué está abierto y qué se reproduce: código e inferencia desde pesos públicos; métricas del v4 reportadas, no reproducibles con los materiales entregados. Limitar «gratis» al acceso del lector si esa es la política prevista. Retirar «ninguna».

[SERIO] Descontar una variable de sí misma deja la correlación indefinida, no igual a cero
Dónde:      entrega/notebook_proyecto.py:1725-1731; entrega/estrategia.md:322-323
Qué dice:   «descontándola por correlación parcial, el modelo conserva 0,657, y un contador de palabras, por construcción, se queda en cero»; «la del contador de palabras, no».
Por qué:    Al residualizar el contador de palabras respecto de ese mismo contador, su residuo es cero y su varianza es cero. Pearson entre ese residuo y cualquier otra variable no está definido: el denominador contiene una desviación típica nula. La correlación parcial positiva del modelo puede indicar asociación adicional bajo el control utilizado; no existe una correlación parcial nula del contador con la que compararla como si fueran dos resultados calculados.
Arreglo:    Conservar el 0,657 identificando qué correlación se calculó y cómo. Sustituir la comparación por «el contador no aporta una señal adicional a la variable longitud porque es esa misma variable».

[SERIO] A4 confunde conservar archivos con recuperar los datos del mismo lector
Dónde:      entrega/estrategia.md:338
Qué dice:   «**Montar almacenamiento persistente** para los datos del lector»; «Cerrar y reabrir tras un reinicio conserva libros, avance, cuaderno y perfil».
Por qué:    En el despliegue, la ruta depende de `gr.Request.session_hash` (`app/ui.py:107-119`). Montar un volumen conserva bytes, pero A4 no incluye un mecanismo para recuperar la identidad del lector al crear otra sesión. La propia función distingue aislamiento por sesión de autenticación. El criterio mezcla reinicio del servidor, cierre del navegador y recuperación de identidad sin especificar cuál se verifica. También usa 7,4 MB actuales para justificar el coste futuro, aunque se pretende conservar libros y datos de múltiples lectores.
Arreglo:    Añadir recuperación de identidad y vinculación a los archivos como parte explícita de A4, con coste y dependencia. Probar por separado reinicio del servidor y nueva sesión del lector, y comprobar aislamiento entre dos lectores. Dimensionar almacenamiento por lector y libros retenidos, no solo por la ocupación actual.

[SERIO] A9 no define una métrica de impacto verificable ni una comparación válida
Dónde:      entrega/estrategia.md:343; entrega/estrategia.md:366
Qué dice:   «proporción de libros empezados que se terminan, con recomendación y sin ella»; «Esta es la única que valida la propuesta de valor»; «Hay una cifra base con la que comparar dentro de un mes».
Por qué:    Faltan definiciones de empezado y terminado, ventana de seguimiento, denominador, tratamiento de abandonos y asignación a los grupos. El progreso existente no certifica lectura: `app/biblioteca.py:40-44` calcula el avance por índice de capítulo; llegar al último devuelve 100 % aunque apenas se abra. La identidad por sesión y la persistencia pendiente de A4 dificultan seguir a una misma persona durante un mes. Además, quienes aceptan recomendaciones pueden diferir de quienes no las aceptan; una diferencia de porcentajes no atribuye por sí sola el efecto al recomendador. La tasa de terminación tampoco mide necesariamente comprensión o aprendizaje.
Arreglo:    Definir eventos y cohortes, recuperación de identidad, horizonte y umbral de éxito. Separar la tarea de instrumentar de la espera para reunir datos. Definir una comparación controlada o declarar que será descriptiva, y añadir una medida breve de adecuación/comprensión. Retirar «la única que valida».

[SERIO] Los riesgos omiten dependencias que impiden cumplir las promesas centrales
Dónde:      entrega/estrategia.md:376-381
Qué dice:   «El enlace de la demostración muere durante la evaluación»; «Que la letra MCER se lea como una certificación»; «Contenido inapropiado para una lectora menor de edad».
Por qué:    Las seis filas cubren disponibilidad, presupuesto externo, certificación, retraso del catálogo, descargas y contenido. No incorporan la pérdida o irrecuperabilidad de datos que A4 reconoce, ni la falta de validación del ajuste lector–libro que exige la pregunta «¿puedo leer esto yo, hoy?» (`:305-308`). El cuadernillo admite que falta la composición del corpus necesaria para comprobar independencia de la validación (`:1979-1985`), y la estrategia reconoce una escala comprimida y etiquetas heredadas. Son riesgos de que una recomendación resulte inadecuada, aunque nadie la confunda con una certificación. Tampoco se explicita el manejo de grabaciones e historial de lectores menores en una aplicación compartida; el riesgo no se agota en el contenido de los libros.
Arreglo:    Añadir filas separadas para continuidad e identidad, recomendaciones inadecuadas y conservación/acceso a datos personales y audio, con responsable, comprobación y alternativa para la entrega. No presentar «no certificamos» como mitigación suficiente de una recomendación equivocada.

[SERIO] Una comparación entre grupos se interpreta como efecto a igualdad de sintaxis y como calibración
Dónde:      entrega/notebook_proyecto.py:652-659; entrega/notebook_proyecto.py:1948-1950
Qué dice:   «Un ensayo y una novela con la misma sintaxis reciben puntuaciones distintas de los lectores porque la carga conceptual es distinta»; «el subconjunto donde el modelo está mejor calibrado»; «El texto informativo puntúa medio punto más difícil que el literario con la misma sintaxis (Figura 6)».
Por qué:    La celda de la Figura 6 (`:614-626`) compara directamente `BT_easiness` entre `Lit` e `Info` con Mann–Whitney. No empareja textos por sintaxis, no ajusta covariables y no mide carga conceptual. Tampoco calcula predicciones ni errores del modelo por dominio: no puede establecer cuál está mejor calibrado. El contraste observado corresponde a etiquetas humanas del corpus, no a un desplazamiento del v4. La frase final cambia tanto el control estadístico como el objeto medido.
Arreglo:    Limitar la interpretación a una diferencia marginal de dificultad etiquetada entre los dos grupos de CLEAR. Presentar sintaxis y carga conceptual como explicaciones posibles, y la calibración por dominio como evaluación pendiente. Eliminar esas conclusiones de las recomendaciones hasta contar con el análisis pertinente.

[SERIO] Un único caso no demuestra que ocho ventanas representen un libro entero
Dónde:      entrega/notebook_proyecto.py:1546-1549
Qué dice:   «La pregunta de producto es si ocho ventanas bastan para representar un libro entero. **Está medida y la respuesta es sí:** sobre un mismo texto, el muestreo de 8 ventanas da **1,784** y el recorrido completo da **1,743**».
Por qué:    La diferencia recalculada es 0,041, pero solo hay una pareja de valores. La estrategia identifica ese caso como un capítulo (`estrategia.md:189-190`), no como un conjunto de libros representativo. La celda contigua (`notebook_proyecto.py:1569-1578`) puntúa dos extractos de CLEAR; no vuelve a medir ese contraste ni evalúa su distribución. Un caso dentro de la misma banda no establece frecuencia de errores, peor caso ni comportamiento cerca de los cortes 0,6 y 1,4.
Arreglo:    Decir «en el capítulo comprobado, la diferencia fue 0,041». Mantener el muestreo como aproximación declarada y proponer una comparación pareada sobre varios libros y capítulos, con errores y cambios de banda, antes de afirmar que basta.

[SERIO] Se atribuye a cambiar el troceado una mejora que no está aislada ni terminada
Dónde:      entrega/notebook_proyecto.py:1930-1934
Qué dice:   «**Leer el documento entero importó más que cambiar de modelo.** [...] El troceado en ventanas fijas lo corrigió sin tocar los pesos».
Por qué:    La Figura 8 documenta la distribución heredada del v1; no compara los mismos libros y pesos bajo ambos protocolos. La solución descrita es remedir con v4 (`estrategia.md:337`), por lo que cambian modelo y lectura. Esa remedición sigue «En curso» (`estrategia.md:365`) y el propio cuadernillo recomienda ejecutarla (`:2013-2014`). No se presenta una ablación que permita atribuir el error al prólogo frente al modelo, a los cortes por cuantiles o a la selección del catálogo, ni una distribución final que demuestre que ya se corrigió.
Arreglo:    Reformular como diagnóstico e hipótesis de mejora: las etiquetas heredadas no son fiables y se están sustituyendo mediante otro protocolo y modelo. Retirar «importó más» y «lo corrigió sin tocar los pesos» hasta disponer de una comparación que mantenga los demás factores constantes.

[SERIO] Se confunden las clases por sextiles del experimento clásico con el anclaje del v4
Dónde:      entrega/notebook_proyecto.py:1106-1110
Qué dice:   «Un texto que este sistema llama B1 [...] es un texto que cae en el cuarto sextil de facilidad de un corpus de 4.724 extractos con juicios humanos».
Por qué:    Esta descripción corresponde a las clases artificiales de `qcut` del experimento con CLEAR, pero la frase la extiende al sistema y a la interfaz. El propio cuadernillo separa el v4, entrenado y medido con otro corpus (`:1391-1402`), y declara un ancla MCER de 654 documentos (`:1973-1975`). La letra del producto no significa pertenencia al cuarto sextil de CLEAR. El problema no se resuelve añadiendo que la letra no es un certificado: son dos procedimientos de etiquetado distintos.
Arreglo:    Reservar esta explicación a los clasificadores de referencia y usar etiquetas como Q1–Q6 o explicar que A1–C2 son nombres provisionales en esa figura. Describir aparte cómo la salida del v4 se transforma en una letra orientativa.

[SERIO] El cuadernillo propone calibrar sobre el conjunto que se presenta como evidencia externa
Dónde:      entrega/notebook_proyecto.py:2004-2008; entrega/estrategia.md:341
Qué dice:   «**Recalibrar la escala pública con una transformación afín** ajustada sobre el ancla externa»; en A7: «ajustada sobre entrenamiento» y «Las medias por nivel siguen estrictamente crecientes **y** se acercan a sus anclas».
Por qué:    Son instrucciones distintas. Usar el ancla externa de la Figura 13 para ajustar dos parámetros convertiría ese conjunto en datos de calibración; sus resultados posteriores no serían una validación externa intacta. Además, una transformación afín de pendiente positiva conserva el orden por construcción, mientras que «se acercan» no fija métrica, tolerancia ni conjunto de evaluación. El criterio permite declarar terminada una calibración por una mejora arbitrariamente pequeña sobre los mismos datos usados para ajustarla.
Arreglo:    Unificar A7 y §9.4: identificar datos de calibración separados de la evaluación final, fijar error de calibración y tolerancias por nivel y documentar dónde se evalúan. Con el modelo v4 cerrado, formularlo como posprocesamiento futuro, no como una mejora ya acreditada.

## Hallazgos MENORES

[MENOR] Las horas de CPU no se siguen del cálculo que acompaña a la figura
Dónde:      entrega/notebook_proyecto.py:1852-1855
Qué dice:   «unas 689 horas en la CPU de una computadora de escritorio —veintiocho días seguidos— y unas tres horas en una A100»; «247 veces».
Por qué:    Con los valores de la propia celda (`:1818-1828`), 61.642 × 350 = 21.574.700 ventanas. Divididas entre 8,19 ventanas/s y 3.600 dan **731,7426 horas**, es decir, **30,4893 días**. La A100 sí da 2,9639 horas y la razón de velocidades es 246,8864. El error es de 42,74 horas respecto de 689. La cifra depende además de un supuesto, no de una medición completa del catálogo.
Arreglo:    Cambiar el texto a 731,7 horas (30,5 días), mantener unas tres horas y el factor 247, y llamar al conjunto «estimación bajo el supuesto de 350 ventanas por libro». Advertir en una celda de texto que el feed es vivo; ese aviso aparece actualmente solo como comentario de código (`:352-354`).

[MENOR] El peor contraste publicado ya no corresponde a los pares que se prueban
Dónde:      entrega/estrategia.md:132; entrega/estrategia.md:362
Qué dice:   «Las cinco pasan; la peor mide **9,51**»; «las cinco paletas superan WCAG AA; la peor, 9,51».
Por qué:    Recalculé los cuatro pares por cada una de las cinco paletas definidos en `pruebas_extremas.py:802-807`, con sus colores actuales de `app/paletas.py`. Los veinte superan 4,5, pero el mínimo es **4,5273** en el botón alto de hielo (#f2fbff sobre #257c99). El 9,5148 corresponde al texto de interfaz de menta, y solo es el mínimo si se omiten los botones. La comprobación es de esos pares, no de toda la accesibilidad de color de la interfaz.
Arreglo:    Sustituir la cifra por 4,53:1 y decir «los veinte pares de contraste comprobados superan 4,5:1». Mantener la conformidad global como algo que necesita revisión del resto de componentes y estados.

[MENOR] La publicación del modelo figura a la vez cumplida y pendiente
Dónde:      entrega/estrategia.md:335; entrega/notebook_proyecto.py:1410-1414
Qué dice:   A1: «**Publicar el modelo (328 MB) y el diccionario (243 MB)**»; «hoy no corre en un Colab ajeno»; cuadernillo: «**los pesos todavía no están publicados**».
Por qué:    El comienzo del cuadernillo afirma lo contrario y enlaza el repositorio (`:45-48`); la celda de carga ya tiene ese identificador (`:1429`). Lo vuelve a dar por publicado en `:1970` y `:2002-2003`, pero §7.1 (`:1591-1592`) y los accionables (`:1872-1875`) conservan el estado anterior. El contraste puntual con `entrega/documento.md:976-977` también da los pesos por publicados. Además, publicar el diccionario no desbloquea el cuadernillo: este dice expresamente que no lo utiliza (`:57-59`). Hay contradicción documental independientemente de la disponibilidad efectiva del servidor.
Arreglo:    Revisar el estado de publicación una vez y sincronizar todas las menciones. Dividir A1 en publicación de recursos de la app y verificación del cuaderno en Colab; no atribuir al diccionario una dependencia inexistente. Si la publicación ya está terminada, retirarla del primer puesto de tareas pendientes.

[MENOR] Ausencia de clave externa no equivale a ausencia de red
Dónde:      entrega/estrategia.md:212-215
Qué dice:   «la aplicación sigue dando diccionario, fonética, audio de Wiktionary, buscador y puntuación, porque nada de eso usa red».
Por qué:    El audio de Wiktionary se reproduce mediante URL HTTP: `_reproductores` lo llama explícitamente remoto y construye un `<audio src="…">` (`app/ui.py:1615-1626`). Una URL guardada en SQLite no contiene el archivo sonoro. Que el audio no dependa de la clave del servicio de lenguaje es correcto; que no requiera red, no.
Arreglo:    Separar «funciona sin clave del servicio externo» de «funciona sin conexión». Especificar que las definiciones y la puntuación son locales, y que el audio remoto requiere conectividad salvo que esté descargado.

[MENOR] Se promete ausencia universal de relleno y exactitud numérica a partir del número de palabras
Dónde:      entrega/notebook_proyecto.py:482-485
Qué dice:   «250 palabras inglesas siempre superan los 256 subtokens BPE»; «No hay relleno, y por tanto agrupar las ventanas de una manera u otra no puede cambiar ni un decimal del resultado».
Por qué:    Palabras y subtokens no tienen esa relación universal: una palabra puede ocupar un único token, y los especiales tampoco fuerzan que 250 palabras rebasen 256 tokens. El propio texto admite ventanas de 150–250 palabras (`:217-219`) y la llamada contigua usa `padding=True` (`:1562-1563`). Además, ausencia de relleno no constituye una prueba general de identidad numérica bajo cualquier agrupación y dispositivo; las mediciones de lotes solo respaldan las configuraciones comprobadas.
Arreglo:    Sustituir la garantía por las longitudes tokenizadas y resultados observados en la prueba concreta. Aclarar que `max_length=256` es un límite, no una promesa de que todas las entradas tengan esa longitud.

[MENOR] Varias acciones no tienen el coste real o el criterio de terminado que se anuncia
Dónde:      entrega/estrategia.md:329-330; entrega/estrategia.md:339; entrega/estrategia.md:342; entrega/estrategia.md:344
Qué dice:   «Cada una lleva coste real y criterio de terminado»; A5: «Coste mínimo de hardware»; A8: «Cinco sesiones de 20 min» y «las tres primeras correcciones están hechas»; A10: «Trabajo de corpus, sin coste de cómputo».
Por qué:    «Mínimo» y «trabajo de corpus» no son presupuestos de dinero ni de tiempo. Las cinco sesiones suman 100 minutos, pero A8 exige también reclutamiento, análisis y tres correcciones de tamaño desconocido; ese esfuerzo no está incluido. A10 cuenta documentos, pero no define distribución por nivel, deduplicación, partición ni para qué se utilizarán con el modelo cerrado. Pasar de 654 a 1.001 documentos no demuestra por sí solo una mejora de la evidencia.
Arreglo:    Poner rangos de horas y dinero, distinguir observación de implementación, asignar un responsable y especificar criterios de aceptación. Para A10, fijar composición y uso del corpus: validación independiente, calibración separada o investigación futura.
