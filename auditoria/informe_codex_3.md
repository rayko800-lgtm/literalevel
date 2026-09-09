# Auditoría de los apartados 7 a 11 de entrega/documento.md

Fecha: 9 de septiembre de 2026. Revisión limitada a los apartados 7, 8, 9, 10 y 11. Las fuentes auxiliares se consultan para contrastar sus afirmaciones, no para auditarlas. No se han leído archivos de `auditoria/`. No se han modificado archivos del proyecto salvo este informe. Se han recalculado las cuentas indicadas; no se ha vuelto a ejecutar la inferencia ni el entrenamiento.

## Hallazgos

[SERIO] Se atribuye causalidad a una comparación que cambia varias cosas a la vez
Dónde:      entrega/documento.md:984
Qué dice:   «El cuello de botella nunca fue el algoritmo, fue la representación del texto.»
Por qué:    El Cuadro 7 cambia representación, arquitectura, preentrenamiento y objetivo: logística de clases frente a roberta con regresión (líneas 530 y 567–569). Además, las líneas 534–536 admiten selección de época sobre los mismos 950 casos. Los errores 1,39 y 0,67 no aíslan el efecto de la representación ni de la regresión; que dos configuraciones de XGBoost pierdan no demuestra que aumentar la potencia «no sirve de nada». La fila «Regresión, no clasificación» de la línea 740 vuelve a atribuir el salto a otro factor tampoco aislado.
Arreglo:    Limitar la conclusión a las configuraciones observadas y retirar «nunca» y la explicación causal; para atribuir efectos, comparar objetivos o representaciones manteniendo constantes los otros factores y usando evaluación independiente.

[SERIO] La ventaja sobre un predictor constante no está medida en la validación real
Dónde:      entrega/documento.md:666
Qué dice:   «la ventaja sobre no hacer nada es real y grande»
Por qué:    El 44,4 % aleatorio y el 50 % de siempre B1 son correctos bajo las hipótesis uniformes explícitas, pero el 97,2 % procede de 144 documentos cuya distribución por nivel no se publica (líneas 918–922). El acierto real de siempre B1 sería (n_A2+n_B1+n_B2)/144: sin esos recuentos podría incluso superar 97,2 %. Comparar una distribución hipotética con otra desconocida no demuestra que la ventaja real sea «grande».
Arreglo:    Reportar los baselines sobre esos mismos 144 documentos, o mantener los porcentajes como ejemplos teóricos y retirar la inferencia de superioridad empírica.

[SERIO] La reproducción en cualquier máquina exige un corpus que no se entrega
Dónde:      entrega/documento.md:685
Qué dice:   «Esta tabla se reproduce en cualquier máquina con el guion `validar_local.py`.»
Por qué:    validar_local.py:40–55 exige un modelo local y PDF externos, buscados en el directorio recibido, LITERALEVEL_CORPUS o Downloads; no descarga ni identifica un manifiesto de los 45 casos. La propia limitación 10 reconoce que British Council no se redistribuye. entrega/datos_figuras/validacion.dat:2–6 conserva agregados, no entradas con las que reproducir la inferencia. El mismo exceso reaparece en la línea 928.
Arreglo:    Decir que la tabla puede recalcularse disponiendo de los mismos PDF y pesos; publicar identificadores, versiones y reglas de inclusión y distinguir datos de figura de una reproducción independiente.

[SERIO] La falta de textos redistribuibles no impide recalcular las métricas ya reportadas
Dónde:      entrega/documento.md:934
Qué dice:   «v4 —el 0,908 y el 97,2 %—, y eso no se arregla publicando nada: depende del»
Por qué:    Spearman, MAE, exactitud y tolerancia se recalculan con las parejas de etiqueta y predicción por documento, sin publicar el texto. El impedimento para volver a ejecutar la inferencia sobre el corpus original es distinto del impedimento para comprobar la aritmética de sus métricas. La afirmación «es lo único» de las líneas 955–957 repite esa falsa exclusividad. Un nuevo corpus mediría además un resultado nuevo, no necesariamente el 0,908 original.
Arreglo:    Separar reproducir entrenamiento, repetir inferencia y recalcular métricas; proponer publicar las 144 etiquetas/predicciones e identificadores anonimizados, reglas de redondeo y cálculo, y reservar el nuevo corpus redistribuible para una validación nueva.

[SERIO] La validación ordinal del v4 no demuestra su utilidad para ordenar novelas
Dónde:      entrega/documento.md:981
Qué dice:   «Para el problema planteado —elegir qué leer— acertar el orden es lo que importa; acertar la letra exacta es un lujo.»
Por qué:    El párrafo traslada al problema de elegir lectura el orden observado en materiales de examen. El Cuadro 10 solo tiene A1–C1, no C2; el Cuadro 8 muestra diferencias importantes entre dominios, pero evalúa v1 y v2, no v4. Puntuar novelas y dibujar sus curvas no verifica su dificultad contra etiquetas externas ni contra lectores. La limitación 9 enumera tamaño y composición del anclaje, pero falta explicitar esta ausencia de validación del v4 en el dominio de uso.
Arreglo:    Concluir que el v4 ordena las medias de los cinco niveles de la muestra British Council; añadir la falta de validación en novelas y en C2 y dejar pendiente el vínculo entre esa señal y una mejor elección del lector.

[SERIO] Agrupar por libro no garantiza separar autores
Dónde:      entrega/documento.md:741
Qué dice:   «Evitar fuga de datos entre extractos del mismo autor»
Por qué:    La decisión de esa misma fila es «Partición agrupada por libro». Separar identificadores de libro impide que fragmentos del mismo libro crucen particiones, pero permite que dos obras del mismo autor queden a ambos lados. La afirmación de la línea 526 solo especifica agrupación por libro; no aporta una comprobación de disyunción de autores.
Arreglo:    Sustituir «autor» por «libro» y reconocer que no se garantiza independencia por autor; si realmente se comprobó, aportar el recuento de autores compartidos.

[MENOR] El balance de exclusiones deja un texto sin explicar
Dónde:      entrega/documento.md:693
Qué dice:   «otros diez los rechaza `scoring.continuous_prose`»
Por qué:    Según las líneas 690–697, de 59 originales falta uno, dos no tienen cuerpo y diez son rechazados: 59−1−2−10=46, no los 45 del Cuadro 10. La suma de las n de ese cuadro sí es 45. Falta explicar una exclusión o corregir uno de los recuentos.
Arreglo:    Dar un balance exhaustivo y sin solapamientos que cierre en 45, preferiblemente acompañado de identificadores y motivo por cada PDF excluido.

[MENOR] Se confunde el tamaño de dos pruebas de rendimiento
Dónde:      entrega/documento.md:835
Qué dice:   «lote dan 286/286 valores idénticos con MAE 0,000000000.»
Por qué:    informe_velocidad.md:122–124 y app/scoring.py:248–249 documentan la prueba de igualdad con 300/300 ventanas. Las 286 corresponden a la prueba de número de hilos (informe_velocidad.md:83), no a la comparación de agrupaciones. No se ha localizado respaldo de la prueba 286/286 en las fuentes contrastadas.
Arreglo:    Citar 300/300 y el experimento correspondiente, o aportar el registro de una segunda prueba con 286.

[MENOR] «Sin mover un decimal» contradice la diferencia que se reporta
Dónde:      entrega/documento.md:1014
Qué dice:   «La velocidad se ganó sin mover un decimal, y se demostró.»
Por qué:    Las líneas 829–831 y el informe de velocidad, líneas 199–200, dicen que una de 840 ventanas cambió 0,001. Eso es una diferencia pequeña y explícita, pero no identidad decimal universal. La prueba finita de reagrupación tampoco permite afirmar «no puede» para cualquier entrada: fixed_blocks admite bloques de 150–249 palabras (app/scoring.py:82–85) y la tokenización usa padding=True (líneas 258–260).
Arreglo:    Decir «sin cambios relevantes en esta prueba», cuantificar la discrepancia y limitar la identidad por lotes al conjunto y configuración medidos.

[MENOR] Los cortes antiguos no dividían 0–2 en tres partes
Dónde:      entrega/documento.md:724
Qué dice:   «Al principio estaban en 0,8 y 1,6 —el 0–2 partido en tres—, pero»
Por qué:    Tres intervalos iguales sobre 0–2 tienen cortes 0,6667 y 1,3333. Los cortes 0,8 y 1,6 producen anchuras 0,8, 0,8 y 0,4. Es un error aritmético en la explicación histórica, aunque no invalida las fronteras actuales 0,6 y 1,4.
Arreglo:    Retirar «el 0–2 partido en tres» y describir los cortes antiguos sin esa justificación.

[MENOR] El audio de Wiktionary necesita red aunque no necesite clave de OpenAI
Dónde:      entrega/documento.md:945
Qué dice:   «la aplicación sigue funcionando en todo lo que no usa red»
Por qué:    La lista inmediata incluye «audio de Wiktionary». app/ui.py:1615–1626 genera reproductores HTML cuyo src es una URL HTTP remota, con preload="none"; el navegador debe solicitar el audio. El diccionario local guarda la referencia, no convierte ese archivo remoto en audio disponible sin conexión. La ausencia de clave y la ausencia de red son condiciones diferentes.
Arreglo:    Mantener que Wiktionary no requiere clave de OpenAI, pero excluir su audio remoto de la lista de funciones sin red.

[MENOR] La escasa ganancia del híbrido no demuestra redundancia informativa
Dónde:      entrega/documento.md:745
Qué dice:   «Ganancia nula (0,37 y 0,37; 0,91 vs 0,93). El embedding ya contiene esa información»
Por qué:    El error ordinal sí baja 0,02, aproximadamente un 2,15 %. Las exactitudes solo están publicadas con dos decimales y no hay incertidumbre de la diferencia. La falta de una mejora grande con esa combinación y clasificador no demuestra que el embedding contenga toda la información de las variables: es una explicación posible, no una propiedad observada.
Arreglo:    Reportar «ganancia pequeña en esta configuración» y presentar la redundancia como hipótesis, sin afirmar igualdad de rendimiento ni de contenido informativo.

[DUDA] Las métricas internas y el carácter «ciego» carecen de prueba verificable
Dónde:      entrega/documento.md:642
Qué dice:   «y 144 de validación. Esos 144 documentos son el conjunto de validación ciega»
Por qué:    Las líneas 645–651 reconocen expresamente que no hay archivo de respaldo para esa ejecución. Solo se pueden comprobar 510+144=654, 77/144=53,47 % y 140/144=97,22 %. No se dispone de predicciones para 0,908 o MAE 0,499, ni protocolo que acredite que esos 144 casos no participaron en selección de época, hiperparámetros o decisiones. Decir que el dato es interno no demuestra que sea ciego.
Arreglo:    Mantener las cifras como resultados declarados no verificados y usar «validación interna» hasta aportar manifiesto de partición, protocolo de selección y predicciones por caso.

[DUDA] El resultado externo individual no se puede reconstruir desde las medias publicadas
Dónde:      entrega/documento.md:703
Qué dice:   «| Modelo v4 | **0,854** |»
Por qué:    entrega/datos_figuras/validacion.dat solo contiene n, media y desviación por nivel. validar_local.py:55–85 conserva las puntuaciones agrupadas e imprime sus agregados; no calcula Spearman, longitud ni correlación parcial. Las búsquedas dirigidas encuentran 0,854, 0,807 y 0,657 repetidos como texto, sin una tabla de las 45 parejas de etiqueta/predicción y longitud que permita comprobarlos. Esos agregados no determinan los rangos individuales; que la fórmula parcial sea compatible no verifica sus entradas. Tampoco se puede reconstruir así el 0,829 de los 38 casos.
Arreglo:    Publicar identificador, nivel, longitud y predicción por caso, con la fórmula de correlación parcial y la ejecución que distingue las muestras de 38 y 45; hasta entonces, etiquetar estos coeficientes como resultados declarados.

## Afirmaciones comprobadas que se sostienen

- El Cuadro 10 coincide con entrega/datos_figuras/validacion.dat:2–6: 3+7+12+11+12=45 y sus cinco medias son estrictamente crecientes. Esto comprueba coherencia entre artefactos, no una nueva ejecución del modelo.
- La escala pública recorta a 0–5 y multiplica por 0,4 (app/scoring.py:96–98); el redondeo orientativo y las bandas actuales son compatibles con los cortes 0,6 y 1,4 y con entrega/datos_figuras/escala_cefr.dat.
- La aritmética de velocidad es consistente: 8,19/6,16−1=32,95 %; 112,7/8,19=13,76; 2.022/8,19=246,89; 35,48/7,45=4,76. Respaldan los redondeos +33 %, ×13,8, ×247 y ×4,8, sin convertirlos en una medida universal.
- Las extrapolaciones del catálogo están bien calculadas bajo sus supuestos explícitos: 61.642×350/2.022/3.600=2,9639 h; con 606,4 ventanas son 5,1351 h; a 0,3 libros/s, 57,0759 h de descarga. No verifican que la media real del catálogo sea una de esas dos.
- Bajo clases equiprobables y predicción uniforme independiente, la tolerancia aleatoria es 16/36=44,44 %; siempre B1 cubre 3/6=50 %. Son ejemplos teóricos correctos.
- La correlación parcial declarada es aritméticamente compatible con las tres correlaciones redondeadas: (0,854−0,730×0,807)/√[(1−0,730²)(1−0,807²)]=0,6563, próxima a 0,657. Sin datos individuales, esto no verifica las correlaciones de entrada.
- La recta aproximada 0,72×real+0,38 tiene respaldo aritmético: el ajuste lineal no ponderado sobre las cuatro medias Colab de validar_local.py:80, con anclas A2=0,4, B1=0,8, B2=1,2 y C1=1,6, da pendiente 0,719575 e intercepto 0,37605. Esto muestra una forma de obtenerla; no acredita que ese fuera el procedimiento original ni una calibración por documento.
- Multiplicar 18 libros hasta 45.345 equivale a ×2.519,17: «por 2.500» es un redondeo razonable.

## Fuera de alcance

- entrega/notebook_proyecto.py:1643–1644: «Es un 25 % mejor» repite una interpretación del salto entre modelos que requeriría su propia revisión; no se desarrolla aquí.

## Veredicto

Los apartados revisados contienen resultados plausibles y varias cuentas comprobables, pero todavía presentan como demostradas conclusiones que solo son compatibles con la evidencia disponible. No he encontrado un fallo que justifique la etiqueta CRÍTICO. Los problemas de mayor gravedad son de inferencia y trazabilidad: atribuir la mejora a una causa no aislada, proclamar superioridad frente a baselines calculados sobre otra distribución y trasladar una validación de examen a la elección de novelas. Corregirlos exige acotar las conclusiones, no cambiar las métricas para que parezcan mejores.

La evidencia más clara es el orden creciente de las cinco medias British Council y la coherencia de los cálculos de rendimiento. Su alcance es limitado: cinco medias no equivalen a acertar cada comparación individual; los resultados de v1 y v2 no validan automáticamente v4 en literatura; y unas cifras repetidas en un .dat no sustituyen las observaciones que permitirían recalcularlas. El texto ya reconoce tamaño muestral pequeño, reutilización del corpus y ausencia del entrenamiento del v4, pero las conclusiones vuelven a borrar parte de esas cautelas.

La defensa de la reproducibilidad necesita una distinción central: publicar pesos permite ejecutar inferencia; publicar datos por caso permite recalcular métricas; publicar el corpus y el protocolo permite repetir la evaluación. El documento mezcla esos tres niveles y promete más de lo que entrega, a la vez que declara imposible una verificación aritmética que sí podría facilitarse sin compartir los textos.

El trabajo puede defenderse como un prototipo funcional con una señal ordinal prometedora y optimizaciones medidas. Estos apartados aún no sostienen que se haya demostrado la causa del salto de calidad ni que el sistema ya resuelva empíricamente la elección de lectura. La revisión necesaria es concreta: cerrar el balance de exclusiones, documentar la procedencia de los números y sustituir absolutos por afirmaciones ajustadas a las pruebas realizadas.
