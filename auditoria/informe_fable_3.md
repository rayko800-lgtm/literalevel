# Auditoría externa de LiteraLevel — informe 3

Auditor: Fable 5.1, 9 de septiembre de 2026. Trabajo sobre `C:\Users\laura\literalevel`
sin leer ninguna revisión previa. Ningún archivo del proyecto fue modificado.

**Método.** Leí primero conclusiones y limitaciones de `entrega/documento.md`, hice
inventario de sus cifras y las rastreé hacia atrás hasta el código, los datos en disco
y las otras piezas de la entrega. Lo que se podía recalcular, lo recalculé: en
particular **volví a ejecutar de cero la validación externa** sobre los PDF de British
Council que hay en esta máquina (58 ficheros), con el modelo de `modelo_v4/`, mediante
un guion propio en el scratchpad que replica `validar_local.py` y añade lo que ese guion
no calcula (Spearman, baseline de longitud, correlación parcial, ajuste afín).

**Resumen.** 0 CRÍTICO · 4 SERIO · 8 MENOR · 8 DUDA. No encontré fuga de datos ni
cifra falsa en el resultado central. Lo que encontré son **correcciones que se aplicaron
en un sitio y no en otro**, y dos razonamientos que sostienen una conclusión correcta
con una premisa que el propio código desmiente.

---

## SERIO

### [SERIO] El Cuadro 12 afirma haber medido lo que el §7.2 dice que no se midió
- **Dónde:** `entrega/documento.md:730` y `entrega/documento.tex:1803` (fila
  «`distilroberta` y no `roberta-base` completo»); contra `entrega/documento.md:568-571`.
- **Qué dice:** Cuadro 12: «328 MB y 0,9 s de carga; **la diferencia de calidad no
  justificaba 3× de tamaño**». §7.2: «La diferencia de calidad entre las dos
  arquitecturas sobre CLEAR **no se midió**, así que la decisión de usar la destilada se
  tomó por tamaño y velocidad, no porque se comprobara que costaba poco. Lo señaló una
  auditoría externa.»
- **Por qué:** son incompatibles: la corrección se hizo en el §7.2 y se dejó intacta la
  fila del cuadro que decía lo contrario. Además el «3×» no cuadra con las cifras del
  propio documento: 125 M frente a 82 M de parámetros (`documento.md:558,626`) es 1,5×,
  no 3×.
- **Arreglo:** reescribir la evidencia de esa fila como «tamaño y velocidad; la pérdida
  de calidad no se midió», y quitar el «3×» o justificarlo.

### [SERIO] Las «6,3 h» retractadas en el documento siguen vivas en la estrategia y en el `.tex`
- **Dónde:** `entrega/estrategia.md:257` y `entrega/documento.tex:796` (accionable A3);
  contra `entrega/documento.md:829-833` y `entrega/estrategia.md:183`.
- **Qué dice:** A3: «~6,3 h de A100, dentro del crédito disponible». Documento §8.3:
  «Una versión anterior de este documento decía 6,3 horas, **que no se sigue de ninguno
  de los dos supuestos**; lo detectó una auditoría externa.» Estrategia línea 183:
  «entre tres y cinco horas».
- **Por qué:** la corrección se aplicó al párrafo pero no a la tabla de accionables, y
  el `.tex` —que «tiene que decir lo mismo» que el `.md`— la hereda. `estrategia.md` se
  contradice a sí mismo a 74 líneas de distancia. Recalculado: 61.642 × 350 / 2.022 =
  2,96 h; 61.642 × 606,4 / 2.022 = 5,14 h. El documento tiene razón; la tabla no.
- **Arreglo:** «3–5 h de A100» en A3, en los dos archivos.

### [SERIO] «Ese mismo modelo sobre esa misma partición» no puede dar 1,39 y 1,295 a la vez
- **Dónde:** `entrega/documento.md:520-521` («Todos los modelos comparten la misma
  partición agrupada por libro … y la misma semilla»), `:539-541` (Cuadro 7),
  `:965-968` (conclusiones); `entrega/notebook_proyecto.py:843-848,1268-1276`.
- **Qué dice:** «el cuadernillo entregado recalcula **ese mismo modelo sobre esa misma
  partición** y obtiene 1,295» frente al 1,39 «histórico» de la misma regresión
  logística sobre «3 variables clásicas».
- **Por qué:** si fueran el mismo modelo, las mismas variables y la misma partición, las
  dos filas serían idénticas; difieren en 0,10 de error ordinal y 0,02 de exactitud. La
  causa más probable está en el cuaderno: su `palabras_raras` usa como lista de
  familiares **las 3.000 palabras más frecuentes del entrenamiento de CLEAR**
  (`notebook_proyecto.py:845-848`), mientras que la tanda histórica usaba las listas de
  NLTK/SPGC (Cuadro 4). Son tres variables con el mismo nombre y distinto contenido. El
  texto vende la comparación como recálculo exacto y no lo es; y de esa comparación
  cuelga un párrafo entero de las conclusiones.
- **Arreglo:** decir qué cambió entre tandas (lista léxica, versión de las tres
  variables, o partición) o retirar «ese mismo modelo sobre esa misma partición».

### [SERIO] El filtro de prosa del `.md` no es el que aplica el código; y eso explica parte del 38 frente a 45
- **Dónde:** `entrega/documento.md:261-267` (§4.3 a) y `:680-686`;
  `app/scoring.py:52-73` (`continuous_prose`); `validar_local.py:18,73`.
- **Qué dice:** el filtro estructural es «≥7 palabras por línea y densidad de
  puntuación final de frase en el intervalo (0, 0,11]». Y sobre la discrepancia 38/45:
  «porque la extracción de texto de los PDF conserva 45 de los 59 textos originales y
  el anclaje de la sección de lectura recorta distinto».
- **Por qué:** `continuous_prose` no aplica ninguno de esos dos umbrales: usa media de
  palabras por frase en [5, 55], ≥4 frases, ≥2 viñetas o >35 % de líneas cortas. En mi
  ejecución local, de 58 PDF, 2 no tienen cuerpo localizable y **10 los rechaza
  `continuous_prose`** (9 de A1 y 1 de B1); quedan 45. En Colab quedaron 38. Es decir,
  la mitad de la diferencia es que **los dos entornos filtran con reglas distintas**, no
  la extracción. Además `validar_local.py:18` importa `continuous_prose` y nunca lo usa
  (el filtro actúa dentro de `puntuar()`), lo que sugiere que el guion se escribió
  pensando en aplicar el filtro documentado y no llegó a hacerlo.
- **Arreglo:** documentar en §4.3(a) y §7.4 que la reproducción local usa el filtro de
  la aplicación (y cuál es), y atribuir la diferencia 38/45 a las dos causas.

---

## MENOR

### [MENOR] «No hay relleno» es falso en general; el código lo dice y el documento lo niega
- **Dónde:** `entrega/documento.md:817-820`; `informe_velocidad.md:122-126`;
  `app/scoring.py:243-249`; contra `colab_precalculo.py:507-515`.
- **Qué dice:** documento: «como todas las ventanas ocupan exactamente 256 tokens tras
  truncar, no hay relleno, y 286 ventanas … dan 286/286 valores idénticos». Precálculo:
  «NO es identico bit a bit. Medido sobre Alicia, 112 ventanas: 103 coinciden
  exactamente y las otras difieren como mucho en 4,8e-07. El motivo es el relleno».
- **Por qué:** `fixed_blocks` devuelve ventanas de menos de 250 palabras cuando el texto
  tiene entre 150 y 250 (`scoring.py:83-84`) y la última ventana de un capítulo corto
  puede ser breve; el tokenizador se llama con `padding=True` en la app y en el
  precálculo. La conclusión («no mueve ninguna cifra redondeada a tres decimales») se
  sostiene; la premisa con la que se presenta como «no es una suposición» no.
- **Arreglo:** «las diferencias por relleno son < 5e-07 y no alcanzan el tercer
  decimal», que es lo que de verdad se midió.

### [MENOR] La banda y la letra sí pueden contradecirse, y la prueba no lo ejercita
- **Dónde:** `app/scoring.py:304-307` (`puntuar`), `:131` (`public_band`), `:152`
  (`anchor_cefr`); `pruebas_extremas.py:833-869`; `entrega/documento.md:715-716`.
- **Qué dice:** «Así la palabra y la letra no pueden contradecirse por construcción.»
- **Por qué:** `puntuar()` redondea la puntuación pública a tres decimales **antes** de
  calcular la banda, pero la letra sale del valor interno sin redondear. Ejecutado:
  interno 1,4999 → público 0,600 → banda «intermedio», letra «A2». Lo mismo en 3,4996
  («avanzado» / «B2»). Las pruebas `_bandas_coherentes` y `_una_sola_letra` comparan
  funciones sueltas sobre valores sin redondear; ninguna pasa por el camino real de
  `Resultado`. El hueco es de 0,0005 interno por frontera: irrelevante en la práctica,
  pero «por construcción» es una afirmación de imposibilidad y es falsa.
- **Arreglo:** derivar la banda de `interno` (o de `letra`) y añadir a las pruebas los
  dos valores de arriba.

### [MENOR] Las conclusiones mezclan la lista de 18 libros con la correlación de la de 397
- **Dónde:** `entrega/documento.md:977-981` y `:734` (Cuadro 12); contra `:378-384`
  (Cuadro 4) y `notebook_proyecto.py:928-932`.
- **Qué dice:** «Multiplicar por 2.500 el corpus … —de 18 libros a los 45.345 del SPGC—
  dejó la correlación en −0,326 frente a −0,330.»
- **Por qué:** −0,330 es la de **397** libros; la de 18 es −0,379. Frente a 18 libros el
  SPGC no «deja igual» la correlación: la baja 0,053. El resultado negativo es más
  fuerte de lo que se cuenta.
- **Arreglo:** «de −0,379 (18 libros) a −0,326» o «de 397 libros a 45.345».

### [MENOR] «De seis niveles a cuatro» cuando el corpus tiene cinco y el local conserva cinco
- **Dónde:** `entrega/documento.md:408-410`; contra `:216` («59 textos A1–C1») y el
  Cuadro 10.
- **Qué dice:** «el rango evaluable se encoge de seis niveles a cuatro (A2–C1)».
- **Por qué:** British Council no tiene C2 (cinco niveles), y en local sobreviven 3
  textos A1 (cinco niveles). En el mismo párrafo el baseline de longitud toma tres
  valores —0,879 (sin filtrar), 0,765 (filtrado en Colab), 0,807 (local)— y solo se
  explica la primera diferencia.
- **Arreglo:** «de cinco a cuatro en Colab; en local quedan tres A1» y una línea sobre
  0,765 frente a 0,807.

### [MENOR] Tres recuentos distintos de las mismas pruebas
- **Dónde:** `README.md:138` («147 pruebas»), `entrega/estrategia.md:142,219,283` y
  `entrega/documento.tex:674,746,832` («183 pruebas»); `pruebas_extremas.py` contiene
  198 llamadas literales a `prueba(`.
- **Por qué:** al menos dos de las tres cifras están desactualizadas. No ejecuté el
  archivo (carga la interfaz y hay claves de OpenAI en el repo), así que el número real
  de `HECHAS` queda como DUDA; que los recuentos no coincidan entre sí, no.
- **Arreglo:** una sola cifra, tomada de la salida del guion.

### [MENOR] 328 MB y 317 MB son el mismo archivo en dos unidades
- **Dónde:** `entrega/documento.md:628` («328 MB»); `README.md:155` («317 MB»).
- **Por qué:** medido: `model.safetensors` = 328.489.204 bytes (328 MB); la carpeta
  `modelo_v4/` = 332.053.001 bytes = 317 MiB. Ambas son ciertas; parecen dos modelos.
- **Arreglo:** una unidad.

### [MENOR] El ajuste afín «0,72 × real + 0,38» viene del corpus de Colab, no del cuadro junto al que se presenta
- **Dónde:** `entrega/documento.md:704-706`, `:868-870`; `entrega/documento.tex:1744-1749`
  (la recta se dibuja sobre los cinco puntos locales).
- **Por qué:** recalculado: sobre las cuatro medias de Colab (`validar_local.py:74`)
  sale 0,720x + 0,376 —de ahí la cifra—; sobre los 45 textos locales, 0,714x + 0,359;
  sobre las cinco medias locales, 0,671x + 0,408. «Ronda» lo cubre, pero conviene decir
  de qué corpus sale, porque en la figura la recta acompaña a otros datos.
- **Arreglo:** una nota de procedencia junto a la fórmula.

### [MENOR] «Sobreviven a la extracción de los PDF» atribuye a la extracción lo que hace el filtro
- **Dónde:** `entrega/documento.md:675-677` (pie del Cuadro 10), `README.md:106`.
- **Por qué:** en mi ejecución la extracción solo pierde 2 textos; los otros 10 los
  rechaza el filtro de prosa (véase el SERIO correspondiente). El pie del cuadro da una
  causa incompleta.
- **Arreglo:** «45 textos que pasan la extracción y el filtro de prosa de la aplicación».

---

## DUDA (no pude verificarlo)

1. **0,908 · 97,2 % · 53,5 % · MAE 0,499 · 654/510/144** (`documento.md:634-655`). El
   documento admite que no hay artefacto en el repositorio. No hay forma de comprobarlo
   desde fuera; la aritmética interna sí cuadra.
2. **Fila British Council de Colab** (n = 38, exacto 50 %, ±1 100 %, Spearman 0,829,
   `documento.md:651`). En local, sobre 45, obtengo exacto 51,1 %, ±1 97,8 %, Spearman
   0,854: compatible, no idéntico. Señalo una coincidencia que conviene descartar
   explícitamente: OneStopEnglish también reserva **38** artículos (`documento.md:214`).
3. **Cuadro 8 completo** (v1/v2 por dominio, `documento.md:588-596`): ningún guion del
   repositorio lo reproduce.
4. **«La exactitud del clasificador de tres clases se mantuvo en 0,51 con las tres
   listas»** (`documento.md:389-390`): no aparece en el cuaderno ni en ningún otro
   archivo entregado.
5. **Filas «históricas» del Cuadro 7** (0,29/1,39, 0,28/1,42, 0,37/0,93, 0,37/0,91,
   0,46/0,67, RMSE por época): sin artefacto.
6. **3.774 / 950 extractos** (`documento.md:520-521`): no tengo el CLEAR en local para
   ejecutar el `GroupShuffleSplit`; el cuaderno lo descarga por red.
7. **Que el cuaderno corra entero en un Colab limpio** (limitación 11): no lo ejecuté.
   Depende de dos descargas por red (GitHub para CLEAR, Hugging Face para los pesos).
8. **2.022 ventanas/s y desviación fp16 0,00037 en A100**: no reproducible aquí.

---

## Verificado y correcto (podía estar mal y no lo está)

- **Cuadro 10 reproduce exacto.** Cinco medias y desviaciones a cuatro decimales
  (0,5040/0,111 · 0,5480/0,237 · 0,9276/0,198 · 1,2478/0,246 · 1,4952/0,172), con
  n = 3/7/12/11/12. Ejecutado de cero con `modelo_v4/` y los PDF de `~/Downloads`.
- **Cuadro 11 reproduce exacto**: Spearman modelo 0,854, longitud 0,807, modelo~longitud
  0,730, correlación parcial 0,657. El resultado que sostiene el trabajo (orden por
  nivel y señal por encima de la longitud) **es real y se puede rehacer**.
- **Sin fuga de datos en el cuaderno**: partición `GroupShuffleSplit` por `Title`
  (`notebook_proyecto.py:840-843`), lista de palabras familiares construida solo con
  entrenamiento (`:845-848`), `StandardScaler` ajustado sobre entrenamiento (`:1136`).
  El único escalador sobre el conjunto completo es el del PCA exploratorio (`:947`), que
  no alimenta ningún modelo evaluado.
- **Aritmética del documento**: Cuadro 3 (723+185+115+69+53+52 = 1.197; porcentajes
  suman 100,0; B1–B2 = 121); 148 + 1.049 = 1.197; 1.049/1.197 = 87,6 %; 53/59 = 89,8 %;
  151/189 = 79,9 %; 461 + 489 = 950; 3.774 + 950 = 4.724; 510 + 144 = 654; 77/144 =
  53,5 %; 140/144 = 97,2 %; azar ±1 con seis clases = 16/36 = 44,4 %, «siempre B1» =
  50 %; int8: 0,21/0,4 = 52 % y 2·0,21/2 = 21 %; 112,7/8,19 = 13,8×; 2.022/8,19 = 247×;
  2,96 h, 5,14 h y 57 h de descarga; +33 % = 1,13 × 1,18 (`informe_velocidad.md:95,120`);
  `inference_mode` 8,50 vs 8,53 = 0,4 %; 1,990 − 1,333 = 0,657.
- **Figura de *War and Peace*** (`entrega/datos_figuras/curva_War_and_Peace.dat`): 362
  capítulos, mínimo 1,333, máximo 1,990, media 1,735. Coincide con el pie del `.tex`.
- **`model.safetensors` = 328 MB**, como dice el §7.4.
- **Cortes de banda 0,6 y 1,4** derivados del ancla MCER (`scoring.py:131-137`) y
  coherentes con `escala_cefr.dat`.
- **Un solo estimador de dificultad global**: `ficha.dificultad_global` pondera por
  ventanas (`app/ficha.py:336-363`), `colab_precalculo.py:543-549` promedia todas las
  ventanas, y `pruebas_extremas.py:970-977` tiene un `assert` que suspendería si alguien
  volviera a la media de medias. El precálculo usa `ficha.capitulos_de_cuerpo`, el mismo
  filtro de capítulos que la app (`colab_precalculo.py:494-518`).
- **`validar_local.py` puede suspender**: exige los cinco niveles, dos textos por nivel
  y medias estrictamente crecientes, y sale con código 1 (`validar_local.py:87-124`).
- **La corrección de OneStopEnglish** (`documento.md:600-607`): la casilla está vacía en
  el `.md`, en el `.tex` (línea 1473) y en la figura (`documento.tex:1509-1510` no dibuja
  la barra v2 de prensa).
- **El sistema desplegado no consulta lista léxica alguna**, como declara `documento.md:484`:
  ninguna referencia a SPGC ni a palabras raras en `app/`.
- **Cuadro 7, 9, 10, 11, 12 y limitaciones** dicen lo mismo en `.md` y `.tex` en todas
  las cifras que comprobé, salvo lo señalado en SERIO 1 y 2.

---

## Sobre el exceso de cautela

El documento cita «una auditoría externa» **12 veces** en el `.md` (13 en el `.tex`,
3 en el cuaderno, 1 en `scoring.py`, 1 en `ficha.py`, 3 en las pruebas). Mi juicio:

- **Los resultados que se afirman son los que se sostienen.** El orden por nivel, la
  correlación parcial y la reproducibilidad del Cuadro 10/11 son reales —lo he
  rehecho— y el documento no los ha rebajado a advertencias. Bien.
- **Lo que sobra es la atribución, no la corrección.** Frases como «Lo detectó una
  auditoría externa y se corrige diciéndolo» (`documento.md:646-647`) o «Ambas cosas las
  señaló una auditoría externa y ambas son ciertas» (`:534-535`) no aportan información
  al lector; convierten un documento técnico en un registro de contrición. Un profesor
  lee eso como inseguridad, no como honestidad. Todo eso cabe en **una nota al pie o
  un apéndice «Historial de correcciones»**, y el cuerpo debería decir simplemente lo
  que es cierto.
- **Las limitaciones se solapan.** La 9, la 10 y la 11 (`documento.md:889-914`) dicen
  tres veces que las métricas del v4 no son recalculables; el Trabajo futuro 2 y 3
  (`:929-934`) son el mismo punto dos veces. Fusionarlas dejaría una sección de
  limitaciones más corta y más dura, que es lo que se quiere.
- **Un caso de cautela que perjudica**: el párrafo de §7.4 sobre la tarjeta
  `metricas_literalevel_v4.json` inexistente (`:640-647`) dedica siete líneas a un archivo
  que ya no se cita. Basta con «las cifras provienen de la ejecución de entrenamiento en
  Drive; no hay artefacto en el repositorio».

En resumen: **el fondo no se pasa de cauto; la forma sí.**

---

## Veredicto

**Casi listo para entregar a un profesor universitario.** El resultado central es
verificable y lo verifiqué; no hay fuga de datos; los baselines están; las
limitaciones son específicas. Lo que impide entregarlo tal cual son contradicciones
internas que un lector atento encontrará en diez minutos:

**Obligatorio antes de entregar (media hora de trabajo):**
1. Cuadro 12, fila `distilroberta`: quitar «la diferencia de calidad no justificaba 3×»
   (SERIO 1). Es una contradicción en la misma página que la corrección.
2. A3 en `estrategia.md` y `documento.tex`: «3–5 h», no «6,3 h» (SERIO 2).
3. Cuadro 7 / conclusiones: retirar o matizar «ese mismo modelo sobre esa misma
   partición» (SERIO 3).
4. §4.3(a) y pie del Cuadro 10: decir que el filtro local es el de la app y que
   explica 10 de los 13 textos que faltan (SERIO 4 y el MENOR asociado).

**Recomendable (una hora):**
5. Reducir las doce menciones a la auditoría a una nota o apéndice; fusionar las
   limitaciones 9–11 y los futuros 2–3.
6. Corregir «no hay relleno», «por construcción», «−0,330 frente a −0,326», «de seis
   niveles a cuatro», el recuento de pruebas y la unidad del tamaño del modelo.

**Opcional:**
7. Un guion `validar_local.py --spearman` (o una celda del cuaderno) que imprima el
   Cuadro 11 además del 10: hoy 0,854/0,807/0,657 no los calcula nada del repositorio,
   aunque —lo comprobé— salen exactos.
8. Publicar los recuentos por fuente y nivel del corpus de anclaje, como la limitación 9
   ya promete.
