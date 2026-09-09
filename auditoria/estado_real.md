# Estado real de los hallazgos de auditoría — 9 de septiembre de 2026

Inventario propio, hecho contra el árbol de trabajo de hoy (HEAD `974308b`,
«tercera auditoria de Astra: los seis serios, corregidos»). Se comprobaron los
**cinco informes** de `auditoria/` hallazgo por hallazgo, yendo al archivo y a la
línea que cada uno cita. **No se leyó `verificacion_pendientes.md` como fuente de
verdad** y no se modificó ningún archivo del proyecto: este documento es la única
escritura.

Los números de línea de los informes ya no valen: `documento.md` ha pasado de
~900 a 1.233 líneas en dos días. Todas las referencias de abajo son a las líneas
de **hoy**.

Recuento: **29 ABIERTO · 9 CERRADO A MEDIAS · 44 CERRADO · 3 FALSO · 6 NO
VERIFICABLE.** Los duplicados se cuentan una sola vez, agrupados.

---

## 1. Críticos

### [Codex H01 | CRÍTICO] Los 950 extractos de «prueba» eligieron la época
Veredicto:  CERRADO
Comprobado: `documento.md:532-539` lo declara con todas las letras — «esos 950
extractos son también los que sirvieron para **elegir la época**, de modo que
funcionan como validación de selección y no como un test independiente; sus
números pueden ser algo optimistas». Idéntico en `documento.tex`.

### [Codex H02 | CRÍTICO] El vocabulario del test entra en modelos evaluados
Veredicto:  CERRADO
Comprobado: `notebook_proyecto.py:843-849`: el `GroupShuffleSplit` va primero
(`:843`) y la lista de 3.000 familiares se construye después, recorriendo
`clear["Excerpt"].iloc[idx_train]`. El comentario lo dice: «las 3.000 más
frecuentes DEL ENTRENAMIENTO». Fable lo verificó por separado en las tres rondas.

### [Codex H03 | CRÍTICO] Los sextiles de CLEAR no son niveles MCER
Veredicto:  CERRADO
Comprobado: `documento.md:535-540` — «las seis clases salen de partir
`BT_easiness` en **sextiles de este corpus**, no de anotaciones del Marco Común
Europeo. Se les dan nombres A1–C2 para poder ordenarlos, pero no son niveles MCER
certificados ni equivalen a los del modelo desplegado». Igual en `.tex:1300+`.

### [Codex H04 | CRÍTICO] El PCA no establece un techo predictivo del 38 %
Veredicto:  CERRADO
Comprobado: `notebook_proyecto.py:990-997` — «El PCA se ajusta *sin mirar la
variable objetivo* […] **no es un techo**», y aporta el contraejemplo (una
regresión lineal supervisada llega a 0,707 sobre las mismas variables). En
`documento.md:444`: «La conclusión honesta es empírica, no un techo».

### [Fable-1 | CRÍTICO] El Cuadro 8 evaluaba v2 sobre sus propios textos de afinado
Veredicto:  CERRADO
Comprobado: `documento.md:603` — la casilla de v2 en la fila de OneStopEnglish
dice ahora *no comparable*, y `:213` (Cuadro 2) declara OneStopEnglish como
«Corpus de **afinado** de la variante v2 (151 artículos)». `:609` explica por qué
está vacía. Fable-3 verificó que la casilla también está vacía en el `.tex` y que
la figura no dibuja la barra.

### [Fable-1 | CRÍTICO] «Corpus externo que nunca vio»
Veredicto:  CERRADO
Comprobado: `grep "nunca vio"` sobre `entrega/`, `README.md` y `modelo_v4/` no
devuelve nada. El Resumen (`documento.md:32-35`, `.tex:242-244`) dice ahora «un
corpus externo que **no se usó para ajustar los pesos** —aunque sí se exploró
durante el desarrollo, y eso se detalla en la limitación 6—».
Queda vivo lo que sostiene el hallazgo: la composición de los 654 sigue sin
publicarse (ver el ABIERTO más abajo).

### [Fable-2 | CRÍTICO] El Cuadro 7 usaba cifras que el propio cuaderno contradice
Veredicto:  CERRADO
Comprobado: `documento.md:545-552`. El Cuadro 7 tiene ahora una columna «Tanda» y
seis filas: las históricas (0,29/1,39 y 0,28/1,42) marcadas como tales, y las
recalculadas del cuadernillo (logística 3 variables **0,313/1,295**, logística 17
variables **0,352/1,061**, XGBoost 17 variables **0,340/1,081**). Las conclusiones
(`:1061-1077`) citan el escalón real. Igual en `.tex:1320-1332` y `.tex:2395-2405`.

---

## 2. Serios

### [Fable-3 S1 | SERIO] El Cuadro 12 afirmaba haber medido lo que §7.2 dice que no se midió
Veredicto:  CERRADO
Comprobado: `documento.md:754` y `.tex:1823` dicen ahora «frente a 1,5× más
parámetros (125 M contra 82 M). **La diferencia de calidad entre las dos no se
midió**». Desapareció el «3×» y desapareció la contradicción con `:578`.

### [Fable-3 S2 / Codex H13 / Fable-1 | SERIO] Las «6,3 h de A100» ★ dos familias
Veredicto:  **CERRADO A MEDIAS**
Comprobado: corregido en los entregables — `documento.md:849-856` («entre 3 y 5
horas», con los dos supuestos y la retractación explícita), `.tex:262`, `:2147`,
`estrategia.md:337` (A3: «Entre 3 y 5 h de A100») y `.tex:796`. Verificado a mano:
61.642×350/2.022/3.600 = 2,964 h; con 606,4 ventanas, 5,135 h — el documento dice
5,14, redondeo defendible.
Pero **`investigacion/competencia.md` sigue diciendo «6,3 horas» tres veces**
(`:119`, `:326`, `:481`, esta última citando `documento.md §8.3` como fuente, que
ya dice otra cosa) y `investigacion/transformer_v5.md:190` una más. El commit
`3830574` metió la competencia «dentro de los entregables».
Arreglo:    poner «3–5 h» en `investigacion/competencia.md:119,326,481` y en
`investigacion/transformer_v5.md:190`. La fila 481 además cita un §8.3 que la
contradice: hay que reescribirla entera.

### [Fable-3 S3 | SERIO] «Ese mismo modelo sobre esa misma partición»
Veredicto:  CERRADO
Comprobado: `documento.md:1069-1074` explica exactamente lo que Fable-3 dedujo —
«`palabras_raras` no contiene lo mismo: en el cuadernillo se calcula contra las
3.000 palabras más frecuentes **del entrenamiento de CLEAR**, y en la tanda
histórica contra las listas externas de NLTK y del SPGC». Igual en `.tex:2399+`.

### [Fable-3 S4 / Fable-2 / Fable-1 | SERIO] El filtro de prosa del documento no es el del código
Veredicto:  **CERRADO A MEDIAS**
Comprobado: `documento.md:268-284` es ahora ejemplar: distingue el filtro del
análisis (dos vías, ≥7 palabras/línea, densidad (0, 0,11]) del que corre en
producción (`scoring.continuous_prose`, con sus reglas reales enumeradas), y
cuenta la secuencia verdadera («primero se puntuaron los 59 textos, se vio que el
modelo daba resultados absurdos con el menú […] y **de ese diagnóstico salió la
idea del filtro**»). `:703-708` atribuye la diferencia 38/45 a sus dos causas.
Lo que quedó sin arrastrar:
1. **El pie del Cuadro 10 sigue diciendo la causa incompleta** —
   `documento.md:689-690` y `.tex:1624`: «sobre los 45 textos que sobreviven a la
   **extracción de los PDF**». Diez de los trece los tira el filtro, no la
   extracción. `README.md:105-107` repite la versión vieja entera.
2. **El balance no cierra en 45.** `documento.md:703-707`: 59 originales − 1 no
   disponible − 2 sin cuerpo − 10 rechazados = **46**, no 45. Mismo error en
   `.tex:1687-1690`. (Codex-3 lo marcó como MENOR y sigue exacto.)
Arreglo:    pie del Cuadro 10 → «45 textos que pasan la extracción y el filtro de
prosa de la aplicación», en `.md:690`, `.tex:1624` y `README.md:106`; y cerrar el
balance de `:703-707` con la exclusión que falta.

### [Codex-3 | SERIO] «El cuello de botella nunca fue el algoritmo»
Veredicto:  CERRADO
Comprobado: `documento.md:1044` dice ahora «**En las configuraciones probadas**,
el cuello de botella no estuvo en el algoritmo». Y en el cuerpo, `:439-444`
acota el argumento: «Lo que no se demuestra es que exista un límite teórico […]
La conclusión honesta es empírica, no un techo». `.tex:2380` igual.

### [Codex-3 | SERIO] La ventaja sobre un predictor constante no está medida
Veredicto:  CERRADO
Comprobado: `documento.md:668-675` — «Esas dos referencias son teóricas y hay que
leerlas como tales […] Si ese conjunto estuviera concentrado en los niveles
centrales, "contestar siempre B1" acertaría bastante más del 50 % […] no que la
ventaja empírica sobre un predictor constante esté medida: **no lo está**».

### [Codex-3 | SERIO] «Se reproduce en cualquier máquina»
Veredicto:  CERRADO
Comprobado: `documento.md:692-696` — «Esta tabla se **recalcula** con el guion
`validar_local.py`, en cualquier máquina **que tenga los mismos PDF y los mismos
pesos**. No es una reproducción independiente». `:974` acota lo mismo.

### [Codex-3 | SERIO] «Eso no se arregla publicando nada»
Veredicto:  CERRADO
Comprobado: limitación 11, `documento.md:976-987`: «conviene separar tres cosas
que aquí se mezclaban en una: repetir el entrenamiento, volver a ejecutar la
inferencia y recalcular la aritmética de las métricas. Lo tercero **sí se podría
comprobar sin publicar un solo texto** […] decir que "no se arregla publicando
nada" era falso».

### [Codex-3 | SERIO] La validación ordinal no demuestra utilidad para novelas
Veredicto:  CERRADO
Comprobado: `documento.md:1034-1042` es un párrafo nuevo y directo: «Ese orden
está medido sobre **textos de examen**, de A1 a C1 y sin C2, no sobre novelas […]
**la dificultad de una novela no se ha contrastado contra ninguna etiqueta
externa ni contra ningún lector**».

### [Codex-3 | SERIO] Agrupar por libro no separa autores
Veredicto:  CERRADO
Comprobado: `documento.md:753` y `.tex:1821`: «Evitar fuga de datos entre
extractos **del mismo libro**. No separa autores: dos obras del mismo autor
pueden caer a ambos lados, y eso no se comprobó».

### [Codex H06 | SERIO] Escala, bandas y empates ★ dos familias
Veredicto:  CERRADO (con un fleco trivial)
Comprobado: `app/scoring.py:131-137`, `public_band` deriva la banda de la letra
del ancla (`ANCHORS[floor(clip(score,0,2)*2.5+0.5)]`) y `anchor_cefr:152` usa
`floor(y+0.5)`. Como `score = clip(interno,0,5)*0,4`, `score*2,5 = clip(interno)`:
las dos rutas dan por álgebra la misma letra. Verificado el caso que Fable-3
levantó (interno 1,4999 → público 0,59996 → A2/básico, coherente): en
`scoring.py:306` la banda se calcula sobre `pub` **sin redondear**, no sobre
`round(pub,3)`. Documento y `escala_cefr.dat` usan 0,6 y 1,4.
Fleco:      `entrega/datos_figuras/escala_cefr.dat` da los seis intervalos pero
sigue sin decir qué extremo incluye. Con la regla del código son semiabiertos
`[desde, hasta)`. Una línea de cabecera lo cerraría.

### [Codex H07 | SERIO] La dificultad global cambiaba entre app y precálculo
Veredicto:  CERRADO
Comprobado: `app/ficha.py:336-363` — un solo estimador, `sum(media_i·n_i)/sum(n_i)`,
con la explicación del fallo en el docstring; `colab_precalculo.py:544-552`
promedia todas las ventanas; y `pruebas_extremas.py:951-977` tiene un `assert`
sobre 500 libros sintéticos que suspendería si alguien volviera a la media de
medias.

### [Codex H08 | SERIO] La fórmula publicada recortaba después de promediar
Veredicto:  CERRADO
Comprobado: `documento.md:120`: `f(T) = 0,4 · (1/n) Σ clip(g(b_k), 0, 5)`. El
`clip` está dentro del sumatorio, que es lo que hace `_puntuar_bloques`.

### [Codex H09 | SERIO] «Todas las ventanas miden 250 palabras, sin excepción»
Veredicto:  CERRADO
Comprobado: `notebook_proyecto.py:1538-1544` añade las dos salvedades (documento
de 150–250 palabras → una ventana más corta; truncado a 256 sub-tokens) y remata:
«pero "sin excepción" era decir de más».

### [Codex H10 | SERIO] Publicar los pesos no vuelve reproducible la evaluación
Veredicto:  CERRADO
Comprobado: limitación 11 (`documento.md:975-987`) separa «el cuaderno corre» de
«el cuaderno recalcula» y nombra los pesos publicados
(`MikeMaki1763/literalevel-v4`). El «una sola cosa / no hace falta cambiar ninguna
otra línea» ya no aparece en el repositorio.

### [Codex H11 | SERIO] El validador podía aprobar sin evaluar nada
Veredicto:  CERRADO
Comprobado: `validar_local.py:87-124`. Exige los cinco niveles
(`NIVELES_ESPERADOS`), un mínimo de 2 textos por nivel, medias estrictamente
crecientes, imprime «VALIDACION FALLIDA» y `sys.exit(1)`. Además separa «sin
cuerpo localizable» de «fallaron al puntuar» e imprime el tipo de excepción
(`:70-78`, `:92-95`), que era el MENOR de Fable-1.

### [Codex H12 | SERIO] El documento no presentaba la comparación clásica completa
Veredicto:  CERRADO
Comprobado: el Cuadro 7 (`documento.md:545-552`) incluye ahora las filas de 17
variables (0,352/1,061 y 0,340/1,081) que Codex echaba en falta, y las
conclusiones (`:1073-1076`) dicen que «contra unas variables clásicas bien
surtidas, la ventaja del *embedding* es bastante menor».

### [Codex H14 | SERIO] El lote de 64/128 no se alcanza en el recorrido interactivo
Veredicto:  **CERRADO A MEDIAS**
Comprobado: `app/ui.py:1193-1194` **sigue llamando `p.perfil_de_texto(...)`
capítulo a capítulo dentro del bucle**, y `_puntuar_bloques` no acumula ventanas
entre llamadas. Con los tamaños del propio informe (máximo 31 ventanas por
capítulo) no se forman lotes de 64 ni de 128 en la interfaz.
Lo que sí mejoró: el Cuadro 14 vive ahora dentro de §8.3 «Escalado: el catálogo
entero, precalculado» (`documento.md:823-836`), y el precálculo sí concatena
todas las ventanas antes de puntuar (`colab_precalculo.py:540-544`), de modo que
para ese camino la medición es legítima.
Arreglo:    una frase en el pie del Cuadro 14 (`documento.md:835`, `.tex:2090`):
«medido sobre el camino del precálculo, que reagrupa las ventanas de todo el
libro; la curva en vivo puntúa capítulo a capítulo y no alcanza esos lotes». O
acumular ventanas entre capítulos en `ui.py:1193`.

### [Codex H15 | SERIO] Ocho ventanas no validan un libro entero
Veredicto:  **CERRADO A MEDIAS**
Comprobado: el documento sí lo acotó — `documento.md:476` (fila T7): «8 bloques
dan 1,784 y el recorrido completo **de las 23 ventanas del mismo capítulo** da
1,743». Pero **el cuaderno entregado no**: `notebook_proyecto.py:1546-1549` sigue
diciendo «La pregunta de producto es si ocho ventanas bastan para representar un
libro entero. **Está medida y la respuesta es sí:** sobre un mismo texto, el
muestreo de 8 ventanas da 1,784 y el recorrido completo da 1,743». Es el mismo
capítulo, presentado como si fuera un libro.
Arreglo:    `notebook_proyecto.py:1546-1549` → «sobre un mismo capítulo de 23
ventanas», y bajar «la respuesta es sí» a «la desviación medida en ese caso es de
0,041».

### [Codex H16 / Fable-1 / Fable-2 | SERIO] Pruebas que no podían fallar ★ dos familias
Veredicto:  CERRADO
Comprobado: `pruebas_extremas.py:37-54` reescribe el docstring del envoltorio
explicando el fallo, y las cuatro sustantivas llevan `assert`:
`_bandas_coherentes:841` (`assert not malas`), `_contraste_suficiente:778+`,
`_una_sola_letra:862`, `_agregacion_por_ventanas:970` (`assert not malas`). Las
tres decorativas de Fable-2 también: `_caso_de_la_auditoria:979`
(`assert abs(v-1.8) < 1e-9`), `_apuntar_en_ruta_imposible:938` (`assert r is None`),
`_tres_bandas:849` (`assert b == [...]`). 25 `assert` en el archivo.

### [Codex H17 | SERIO] Las estadísticas de la ficha son de muestra, y «tu ritmo» es un supuesto
Veredicto:  **ABIERTO**
Comprobado: `app/ficha.py:159` — `_muestra(libro, tope_palabras=60000)`; `:183`
la usa para las estadísticas; `:203` recorta a `toks[:20000]` para la riqueza
léxica; `:31-32` fija `PPM_COMODO = 180` y `PPM_EXIGENTE = 110`. Nada de eso es
una velocidad observada del lector ni una estadística global de la obra. El
documento sigue diciendo, en `:800-802`, que «todo lo que dice está **contado
sobre el fichero**: palabras reales, **tiempo de lectura a su ritmo**, longitud
media de frase, proporción de diálogo, variedad de vocabulario…», y
`estrategia.md:71` repite «cuánto tarda en leerlo **a su ritmo**».
Arreglo:    `documento.md:800-802` y `.tex` equivalente: separar «palabras: total
contado sobre el fichero» de «frase, diálogo y vocabulario: sobre una muestra de
hasta 60.000 palabras (20.000 tokens para la riqueza léxica)» y de «tiempo:
estimado a 180 o 110 palabras/minuto según el ajuste al nivel, no medido al
lector». `estrategia.md:71`: cambiar «a su ritmo» por «a una velocidad supuesta».

### [Codex H18 | SERIO] El salto de «orden por nivel» a «utilidad personal»
Veredicto:  **CERRADO A MEDIAS**
Comprobado: la limitación se puso donde importa —`documento.md:1034-1042` dice
que el vínculo entre la señal y elegir mejor un libro «queda pendiente»— y la
limitación 13 (`:990`) declara el n = 1. Pero el Resumen sigue prometiendo, en
`:25`, que la aplicación «le busca **libros que pueda terminar**», y el peso
`PESO_FRAGMENTOS = 0.65` de `app/perfil.py:210` no aparece en ningún entregable
como decisión heurística sin validar.
Arreglo:    `documento.md:25` → «le busca libros a su nivel»; y una línea en §6 o
en el Cuadro 12 declarando el 0,65 como heurístico.

### [Fable-1 | SERIO] Tres cifras distintas para la misma velocidad ★ dos familias (Codex H20/H22)
Veredicto:  **CERRADO A MEDIAS**
Comprobado: unificado en 8,19 / 112,7 / **13,8×** en `documento.md:831-832`,
`:1085`, `estrategia.md:181` y `app/scoring.py:207-215` (que además explica por
qué el «dieciocho veces» anterior comparaba contra otra base).
Pero **`arrancar_gpu.py:13-17` conserva la tanda vieja entera**: «CPU […] 8,7
ventanas/s / GPU […] 101,7 ventanas/s 11,7x» y «MAE 0,0000012». Fable-1 pedía
expresamente que documento, `scoring.py` **y `arrancar_gpu.py`** citaran una sola
tanda; se arreglaron dos de tres.
Arreglo:    `arrancar_gpu.py:13-17` → 8,19 / 112,7 / 13,8× y MAE 0,000001.

### [Fable-1 / Fable-2 / Codex-3 | SERIO] El Cuadro 11 no lo calcula ningún guion ★ dos familias
Veredicto:  **ABIERTO**
Comprobado: `grep -rl spearman --include=*.py` devuelve solo
`auditoria/medir_fuga_vocabulario.py`, `entrega/notebook_proyecto.py` y
`notebook_v4_dump.py` — ninguno calcula el Cuadro 11. `validar_local.py` entero:
imprime medias, desviaciones y el veredicto de orden; **no** Spearman, **no**
recuento de palabras, **no** correlación parcial, **no** la recta.
`grep "0.854\|0.807\|0.657"` sobre todos los `.py`: cero resultados.
Atenuante fuerte: Fable-3 rehizo el cálculo con un guion propio y los cuatro
números **salen exactos** (0,854 / 0,807 / 0,730 / 0,657). El resultado es real;
lo que no existe es el guion que lo produce dentro del repositorio.
Arreglo:    añadir a `validar_local.py`, después de la línea 85, el cálculo de
`scipy.stats.spearmanr` del modelo y del recuento de palabras sobre los mismos 45
textos, la parcial `(r_my − r_mx·r_xy)/√((1−r_mx²)(1−r_xy²))` y el `polyfit`; e
imprimirlos junto al Cuadro 10. Son unas quince líneas.

### [Fable-2 / Fable-3 / Codex-3 | SERIO] La recta «0,72 × real + 0,38» no es el ajuste de los puntos que dibuja
Veredicto:  **ABIERTO**
Comprobado: `documento.tex:1764-1770` traza `{0.72*x+0.38}` sobre los **cinco
puntos locales** `(0.0,0.5040) (0.4,0.5480) (0.8,0.9276) (1.2,1.2478)
(1.6,1.4952)`. El ajuste por mínimos cuadrados de esos cinco puntos es
**0,671·x + 0,408** (Fable-2 y Fable-3 coinciden; Codex-3 verificó que 0,72/0,38
sale de las **cuatro** medias de Colab de `validar_local.py:80`, y da
0,719575·x + 0,37605). En `documento.md:729` y `:940` la fórmula sigue sin nota
de procedencia, y el pie de la figura (`.tex:1790-1795`) razona sobre «la
pendiente es 0,72» como si fuera el ajuste de lo dibujado.
Arreglo:    o bien añadir en `documento.md:729` y en el pie de `.tex:1793` «recta
ajustada sobre las cuatro medias de la tanda de Colab (A2–C1)», o bien sustituir
`{0.72*x+0.38}` por `{0.671*x+0.408}` en `.tex:1764` y actualizar las tres
menciones. Lo primero es media línea; lo segundo toca cinco sitios.

### [Fable-2 / Fable-3 / Codex H11 | SERIO] `validar_local.py` une las líneas: el detector de listas no puede actuar ★ dos familias
Veredicto:  **ABIERTO**
Comprobado: `validar_local.py:34-35`, `cuerpo()` termina en
`return " ".join(utiles) or None` — devuelve **una sola línea**. `puntuar()`
(`app/scoring.py:297`) llama a `continuous_prose` sobre ese texto, y el propio
docstring de `puntuar` (`:288-295`) explica que con una sola línea «sus dos
comprobaciones de maquetado —dos o más viñetas, seis o más líneas— no podían
dispararse jamás. El detector de listas, menús y tablas era código muerto». El
guion de validación reproduce exactamente ese fallo que el código de producción
declara haber corregido. Además `continuous_prose` se importa en `:18` y no se
usa en ninguna otra parte del guion.
Nota:       el filtro no queda inerte del todo —los umbrales de nº de frases y de
palabras por frase sí actúan, y son los que tiran los diez textos—, pero las dos
vías de maquetado, que son las que atrapan menús y tableros, no.
Arreglo:    `validar_local.py:35` → `return "\n".join(utiles) or None`, y
normalizar dentro de `puntuar`. Si eso cambia el recuento de 45, hay que rehacer
el Cuadro 10; conviene medirlo antes de tocarlo.

### [Fable-2 | SERIO] El MAE de 0,499 no dice en qué escala está
Veredicto:  **ABIERTO**
Comprobado: `documento.md:659-660` y `.tex:1587-1588`: «MAE de 0,499 niveles en el
conjunto de validación». No se dice si son niveles de la escala interna 0–5 o de
la pública 0–2. En una tabla donde todo lo demás son porcentajes y un Spearman,
el lector no puede deducirlo.
Arreglo:    «MAE de 0,499 niveles de la escala interna 0–5» (o 0–2, según cuál
sea) en el pie del Cuadro 9, en `.md:659` y `.tex:1587`.

### [Fable-1 | SERIO] La «validación externa ciega» del cuaderno es una tabla tecleada
Veredicto:  **CERRADO A MEDIAS**
Comprobado: las dos `axhline` **sí** están corregidas —`notebook_proyecto.py:1692-1693`
trazan 0,6 y 1,4, no 0,8 y 1,6—, y el markdown de arriba (`:1656-1662`) declara
ahora que el corpus «no se usó para ajustar los pesos, aunque sí se miró durante
el desarrollo […] tampoco es un conjunto virgen». Pero la celda de `:1669-1682`
sigue construyendo el `DataFrame` con constantes tecleadas y sigue imprimiendo
`all(a < b for a, b in zip(medias, medias[1:]))` sobre ellas, bajo un encabezado
que sigue diciendo «## 7.2 **Validación externa ciega**» (`:1653`). Un lector de
cuaderno espera que una celda que imprime un resultado lo haya calculado.
Arreglo:    `notebook_proyecto.py:1653` → «7.2 Validación externa (cifras citadas
de `validar_local.py`, no recalculadas aquí)», y un comentario de dos líneas
encima del `DataFrame` en `:1669`.

### [Fable-1 | SERIO] El orden A1 < A2 descansa en tres textos
Veredicto:  CERRADO
Comprobado: el Resumen (`documento.md:36-42`) da ahora la n por nivel y añade «con
una salvedad que conviene leer junto a las cifras: el escalón A1–A2 es de 0,044
sobre desviaciones de 0,111 y 0,237, y descansa en tres textos. **Está dentro del
ruido**». El Cuadro 10 (`:682-688`) tiene columna de desviación. `README.md:104`
dice «tercera cifra». Idéntico en `.tex:245-250`.

### [Fable-1 / Fable-2 | SERIO] La tarjeta `metricas_literalevel_v4.json` no existe
Veredicto:  CERRADO
Comprobado: `documento.md:646-651` retira la cita y dice «una versión anterior de
este documento citaba una tarjeta `metricas_literalevel_v4.json` que **no
existe**. Lo único comprobable desde el repositorio es la aritmética interna».
`grep` confirma que la tarjeta no se cita en ningún entregable.
Pero ojo al defecto que introdujo esa corrección: ver el ABIERTO «frase rota».

### [Fable-2 | SERIO] Las conclusiones colgaban el 0,908 de los «textos externos»
Veredicto:  CERRADO
Comprobado: `documento.md:1024-1031` separa las dos cosas en dos frases: Spearman
0,829 (38) y 0,854 (45) sobre British Council; «El **0,908 y el 97,2 %** son otra
cosa: salen del conjunto de validación de **144 documentos del propio corpus de
anclaje**, que es interno. Atribuirlos a los externos era un error».

### [Fable-2 | SERIO] Colab no tuvo A1, y los tres A1 locales pasaron otro filtro
Veredicto:  CERRADO
Comprobado: `documento.md:706-708`: «Importa decirlo porque los tres textos A1 que
sostienen el escalón más débil del Cuadro 10 pasaron el filtro de la aplicación,
no el del análisis». `.tex:1690-1692` igual.

### [Fable-2 | SERIO] El Cuadro 7 no decía que el transformer era `roberta-base`
Veredicto:  CERRADO
Comprobado: la fila del Cuadro 7 dice «**`roberta-base` afinado**»
(`documento.md:552`) y `:573-579` avisa: «Ese `roberta-base` **no es el modelo que
se despliega**».

### [Fable-2 | SERIO] El 97,2 % no tenía línea base
Veredicto:  CERRADO — ver el SERIO de Codex-3 sobre el predictor constante.

---

## 3. Menores

### [Codex H19 / Codex-3 | MENOR] «Sin clave» no es «sin red»: el audio de Wiktionary
Veredicto:  **ABIERTO** — y es el hallazgo abierto que más veces se repite
Comprobado: `app/ui.py:1615-1627`, `_reproductores` emite
`<audio controls preload="none" src="{url}">` con URLs `http` de
`upload.wikimedia.org`. El navegador tiene que pedirlas. No necesitan clave de
OpenAI; sí necesitan red. El texto sigue igual en **cinco sitios**:
`documento.md:998-1000` (limitación 14: «sigue funcionando en todo lo que no usa
red —diccionario, fonética, audio de Wiktionary, buscador y puntuación—»),
`documento.tex:2330-2331`, `documento.tex:740-741`, `estrategia.md:213-214`
(«porque nada de eso usa red») y `README.md:177-179`.
Arreglo:    en los cinco: «sin clave siguen funcionando el diccionario, la
fonética, el buscador y la puntuación, que son locales; el audio de Wiktionary no
necesita clave pero sí conexión».

### [Codex H20 / Fable-1 / Fable-2 / Codex-3 | MENOR] «286 ventanas» donde la fuente dice 300 ★ dos familias, cuatro veces
Veredicto:  **ABIERTO**
Comprobado: `documento.md:846-847` y `.tex:2143-2144` siguen diciendo «286
ventanas puntuadas de una en una y en un solo lote dan 286/286 valores idénticos
con MAE 0,000000000». La fuente (`informe_velocidad.md:121-124`) y
`app/scoring.py:248-249` documentan la prueba de reagrupado con **300/300**; las
286 son del barrido de hilos (`informe_velocidad.md:83`). Cuatro auditores en dos
familias lo señalaron por separado y sigue exactamente igual.
Arreglo:    300/300 en `.md:846-847` y `.tex:2143-2144`.

### [Fable-3 | MENOR] «No hay relleno» es falso en general
Veredicto:  **ABIERTO**
Comprobado: `documento.md:844-846` («como todas las ventanas ocupan exactamente
256 tokens tras truncar, **no hay relleno**») contra `app/scoring.py:82-85`
(`fixed_blocks` devuelve ventanas de 150–249 palabras para textos cortos) y
`colab_precalculo.py:507-515` («NO es identico bit a bit […] El motivo es el
relleno»). La conclusión —que no mueve el tercer decimal— se sostiene; la premisa
no. Igual en `.tex:2142-2143`.
Arreglo:    «las diferencias por relleno son menores de 5e-07 y no alcanzan el
tercer decimal», que es lo medido.

### [Codex-3 | MENOR] «Sin mover un decimal»
Veredicto:  **CERRADO A MEDIAS**
Comprobado: `documento.md:1084-1086` mantiene el titular «La velocidad se ganó
sin mover un decimal» pero ahora cuantifica en la misma frase: «con 839 de 840
ventanas idénticas a tres decimales». La discrepancia está declarada dos líneas
antes (`:841-843`). Queda el absoluto de `:844` («**no puede** mover un decimal»),
que es el que Codex-3 objetaba como afirmación de imposibilidad.
Arreglo:    `:844` → «no movió ningún decimal en la prueba realizada».

### [Codex H20 / Fable-3 | MENOR] −0,330 emparejado con 18 libros ★ dos familias
Veredicto:  **ABIERTO**
Comprobado: `documento.md:1079-1081`: «Multiplicar por 2.500 el corpus de
referencia léxica —**de 18 libros** a los 45.345 del SPGC— dejó la correlación en
−0,326 **frente a −0,330**». El propio Cuadro 4 (`:387-389`) dice que −0,379 es la
de 18 libros y −0,330 la de 397. El Cuadro 12 (`:758`) sí está bien («pasa de
−0,330 a −0,326»); la conclusión no. Mismo texto en `.tex`.
Arreglo:    `:1080-1081` → «de 397 libros a los 45.345 del SPGC, la correlación
pasa de −0,330 a −0,326; frente a los 18 del corpus de NLTK, de −0,379».

### [Codex H20 / Fable-3 | MENOR] «De seis niveles a cuatro» ★ dos familias
Veredicto:  **ABIERTO**
Comprobado: `documento.md:414` y `.tex:1149`: «el rango evaluable se encoge de
seis niveles a cuatro (A2–C1)». British Council va de A1 a C1 —cinco niveles,
como dice el propio `:216`— y en local sobreviven tres textos A1, o sea cinco
niveles en el Cuadro 10.
Arreglo:    «de cinco niveles a cuatro en la tanda de Colab; en local sobreviven
tres textos A1 y quedan cinco».

### [Fable-3 | MENOR] Tres recuentos distintos de las mismas pruebas
Veredicto:  **ABIERTO**
Comprobado: `README.md:138` dice «147 pruebas»; `estrategia.md:142`, `:220`,
`:388` y `documento.tex:674`, `:746`, `:832` dicen «183 pruebas»;
`pruebas_extremas.py` tiene **198** llamadas literales a `prueba(` (más las que
caigan dentro de sus 12 bucles, así que `HECHAS` será ≥ 198). De paso:
`estrategia.md:388` dice «27 pasos de integración» y `pruebas_integracion.py`
tiene 28.
Arreglo:    ejecutar `python -X utf8 pruebas_extremas.py`, tomar el número que
imprime `:993` y ponerlo en los siete sitios. Igual con los pasos de integración.

### [Fable-2 | MENOR] «La peor paleta, 9,51» no es la peor pareja
Veredicto:  **ABIERTO**
Comprobado: recalculado con la misma fórmula de luminancia de
`pruebas_extremas.py:786-793` sobre los cuatro pares que la prueba mide hoy:
**4,53** (hielo / botón-alto), 4,65 (papel), 4,71 (medianoche), 4,73 (amanecer),
4,74 (menta). El 9,51 es la peor del par *interfaz* (menta), nada más. Todas
pasan AA, pero el margen real es 0,03, no 5,01.
`estrategia.md:132` y `:387` siguen diciendo «la peor, 9,51».
Arreglo:    «las cinco pasan AA en los cuatro pares medidos; la peor pareja es el
texto del botón, 4,53; la peor de interfaz, 9,51».

### [Fable-3 | MENOR] 328 MB y 317 MB
Veredicto:  **ABIERTO**
Comprobado: `documento.md:634` dice «328 MB» (que es `model.safetensors` =
328.489.204 bytes, decimal) y `README.md:155` dice «317 MB» (que es la carpeta
entera en MiB). Ambas ciertas, parecen dos modelos.
Arreglo:    `README.md:155` → «328 MB (el archivo de pesos; 317 MiB la carpeta)».

### [Fable-1 | MENOR] El código manda a Drive y el documento dice que está en Hugging Face
Veredicto:  **ABIERTO, y más ancho de lo que Fable-1 vio**
Comprobado: `app/scoring.py:184-187` sigue diciendo «Descarga la carpeta
'modelo_literalevel_v4_transformer' de Drive (literalevel_bigdata)». Y **el
`README.md` entero se quedó en la versión anterior a la publicación del modelo**:
`:155` lo lista como «Drive, `literalevel_bigdata` (privado)» y `:165-168` afirma
que `desplegar_datos.py` lo sube a Hugging Face «pero **todavía no se ha
publicado**, así que hoy hay que pedirlo». La limitación 11 del documento
(`:976-979`) dice lo contrario: repositorio público
`MikeMaki1763/literalevel-v4`, descarga sin credenciales. El commit `26d6784`
publicó el modelo y el README no se enteró.
Arreglo:    `app/scoring.py:186` y `README.md:155`, `:165-168` → el repo de HF.
Es lo primero que mira quien clone.

### [Fable-1 | MENOR] Gradio afirmado pero no fijado
Veredicto:  **ABIERTO**
Comprobado: `documento.md:48` dice «ocho pestañas en Gradio 6.26»;
`requirements.txt:5` dice `gradio>=6.0`. Quien clone instalará la que haya ese
día, y Gradio rompe API entre menores.
Arreglo:    `requirements.txt:5` → `gradio==6.26.*`.

### [Fable-1 / Fable-2 | MENOR] `informe_velocidad.md` sin terminar
Veredicto:  **CERRADO A MEDIAS**
Comprobado: la nota del corte viejo **sí** está fechada —`informe_velocidad.md:165`
dice ahora «Era cierto con los cortes de banda viejos»—, y el informe ya no lo
cita ningún entregable (`grep "informe_velocidad\|informe de velocidad"` sobre
`entrega/` y `README.md` no devuelve nada), lo cual desactiva la parte grave del
hallazgo. Pero `:212-218` sigue con «## 4. Recomendación / _(pendiente)_ / ## 5.
Extrapolación / _(pendiente)_».
Arreglo:    una línea al principio: «mediciones brutas; la recomendación y la
extrapolación se trasladaron al §8.3 del documento».

### [Fable-1 / Fable-2 | MENOR] El tope de 8 ventanas no se declara en §7.4
Veredicto:  **ABIERTO** (leve)
Comprobado: `app/scoring.py:21` `MAX_BLOCKS_PER_DOC = 8`; `documento.md:635-636`
describe el estimador del modelo desplegado como «Puntúa bloques de 250 palabras
truncados a 256 tokens y promedia sin ponderar», sin la salvedad. El tope sí está
declarado en la fila T7 (`:476`), en otro apartado y con otro propósito.
Arreglo:    media línea en `:636`: «hasta ocho bloques repartidos por documento en
la puntuación rápida —que es la que usa `validar_local.py`—; todos en el catálogo
(véase T7)».

### [Codex-3 | MENOR] «El 0–2 partido en tres»
Veredicto:  CERRADO
Comprobado: `documento.md:734-736` dice ahora que los cortes 0,8 y 1,6 «**ni
siquiera partían el 0–2 en tres partes iguales**: dejaban dos tramos de 0,8 y uno
de 0,4». El error aritmético se convirtió en argumento.

### [Codex-3 | MENOR] «Ganancia nula» del híbrido
Veredicto:  CERRADO
Comprobado: `documento.md:450-452` dice «da 0,37 y 0,91: prácticamente lo mismo.
Esto **indica** que el embedding ya contiene la información…», y `:439-444`
acota el alcance del argumento entero. Ya no se afirma ausencia de ganancia como
propiedad observada.

### [Fable-1 / Fable-2 | MENOR] XGBoost con el error de la logística
Veredicto:  CERRADO
Comprobado: `grep "tanto con regresión logística como con XGBoost"` no devuelve
nada. Las conclusiones (`:1061-1066`) citan el escalón por tandas.

### [Fable-2 | MENOR] «Cuarta cifra» en el README
Veredicto:  CERRADO — `README.md:104` dice «tercera cifra decimal».

### [Fable-1 / Fable-2 | MENOR] 61.642 frente a 61.552
Veredicto:  CERRADO — `grep "61.552\|61552"` fuera de `auditoria/` no devuelve
nada. Unificado en 61.642.

### [Fable-1 | MENOR] fp16 «4,8×» en el documento, «cuatro veces y media» en el código
Veredicto:  CERRADO — `app/scoring.py:212-213` ya no dice «CUATRO VECES Y MEDIA»;
el bloque de comentarios de `:206-218` usa 13,8× y las cifras del informe.

### [Fable-1 | MENOR] `validar_local.py` silenciaba las excepciones bajo un solo rótulo
Veredicto:  CERRADO — `validar_local.py:70-78` y `:92-95` separan «sin cuerpo
localizable» de «fallaron al puntuar» e imprimen el tipo de excepción.

### [Fable-2 | MENOR] «5,14 h» no salía de 606 ventanas
Veredicto:  CERRADO — `documento.md:853-855` da ahora el promedio con un decimal
(«las **606,4** que promedian las cinco novelas largas medidas en local»).
Recalculado: 61.642×606,4/2.022/3.600 = **5,135 h**. 5,14 es el redondeo correcto.

### [Fable-2 | MENOR] MAE «0,0000012» con un decimal que la fuente no tiene
Veredicto:  FALSO (pero con un fleco)
Comprobado: la cifra es derivable, no inventada: una sola ventana desviada 0,001
sobre 840 da 0,001/840 = 1,190×10⁻⁶, que redondea a 0,0000012. Codex-3 llegó a lo
mismo. `informe_velocidad.md` reporta 0,000001 porque redondea a seis decimales.
Fleco:      `arrancar_gpu.py:17` lo cita junto a la tanda vieja (ver el CERRADO A
MEDIAS de velocidades).

---

## 4. Dudas

### [Codex H21 / Fable-1 / Fable-2 / Codex-3 | DUDA] La composición y la partición del corpus de anclaje ★ dos familias, cuatro veces
Veredicto:  **ABIERTO** (reconocido, no resuelto) · parcialmente NO VERIFICABLE
Comprobado: la limitación 9 (`documento.md:963-970`) lo declara con precisión —
«**su composición no está publicada**: no se dice cuántos documentos vienen de
cada fuente ni cuántos por nivel […] Publicar los recuentos no exige redistribuir
ni una línea de texto con derechos»— y `notebook_proyecto.py:1979-1987` repite el
hueco («quien audite este trabajo tiene derecho a exigir esa lista, y hoy no
está»). Es honesto. Pero el hueco sigue siendo el hueco: desde el repositorio no
se puede saber si los textos de British Council están entre los 654, ni si la
partición 510/144 es por documento o por grupo, ni si los 144 participaron en la
selección de época. Y de esos 144 salen las dos cifras más repetidas del trabajo.
Arreglo:    publicar en `modelo_v4/` un CSV o JSON con `id_anónimo, fuente,
nivel, partición, etiqueta, predicción` para los 654. No redistribuye texto y
cierra de golpe cuatro hallazgos de dos familias de auditores.

### [Fable-2 | DUDA] La desviación fp16 de 0,00037 en A100
Veredicto:  **ABIERTO** (afirmación sin respaldo localizable)
Comprobado: `grep -rn "00037"` fuera de `auditoria/` devuelve exactamente dos
líneas: `documento.md:760` y `.tex:1835`. No hay archivo con esa medición. La
cifra vecina de `informe_velocidad.md:182` es 0,00035, y es **local**, no A100.
Arreglo:    o adjuntar la salida de la celda de `colab_precalculo.py` que la
mide, o cambiarla por «la desviación medida en local es 0,00035».

### [Fable-2 | DUDA] «0,004 de diferencia máxima medida en cinco libros reales»
Veredicto:  **ABIERTO** (afirmación sin respaldo localizable)
Comprobado: `documento.md:755` y `.tex:1825`. `grep "0,004\|0.004"` sobre el resto
del repositorio no encuentra la medición. La prueba `_agregacion_por_ventanas`
demuestra la identidad algebraica sobre 500 libros sintéticos, no la magnitud
sobre cinco libros reales.
Arreglo:    o adjuntar la medición, o cambiar por «la diferencia es nula por
construcción desde que las dos rutas usan el mismo estimador».

### [Codex H22 | DUDA] El registro experimental de las 2.022 ventanas/s
Veredicto:  NO VERIFICABLE desde el repositorio
Comprobado: `colab_precalculo.py:322-363` tiene la celda que la mide, sin salida
guardada. El `.ipynb` de precálculo no conserva ejecuciones. El documento la usa
como base de las 3–5 horas.

### [Codex H23 | DUDA] Los datos individuales del baseline de longitud
Veredicto:  CERRADO en lo comprobable, ABIERTO en lo demás
Comprobado: la parte que Codex podía comprobar sí se corrigió — la comparación
con «la correlación parcial nula del contador» ya no aparece. Fable-3 rehizo el
cálculo y los cuatro coeficientes salen exactos. Lo que sigue faltando son las 45
parejas por documento, y eso es el ABIERTO del Cuadro 11.

### [Fable-1 | DUDA] «Lectora ajena al proyecto» y «prima del autor»
Veredicto:  ABIERTO (leve, y probablemente aceptable)
Comprobado: `estrategia.md:103` lo declara («**Esmeralda, 15 años** […] prima del
autor»); `documento.md:49`, `:161` y `:190` dicen solo «ajena al proyecto», que
es cierto. La limitación 13 (`:990`) declara el n = 1. No es un error; un
evaluador que lea solo el documento puede leerlo como más independencia de la que
hay.
Arreglo:    dos palabras en `documento.md:190`, si se quiere cerrar del todo.

### [Fable-2 | DUDA] Las desviaciones del Cuadro 10 son poblacionales
Veredicto:  ABIERTO (trivial)
Comprobado: `validar_local.py:85` usa `np.std` (ddof=0). Con n = 3 la diferencia
frente a ddof=1 es un factor 1,22. El Cuadro 10 dice solo «Desviación».
Arreglo:    «Desviación (poblacional)» en el encabezado.

### [Fable-2 / Codex-3 | DUDA] Los 59 PDF no están enumerados
Veredicto:  ABIERTO (leve)
Comprobado: `validar_local.py:57` busca `*LearnEnglish-Reading*.pdf`. No hay
manifiesto. En esta máquina hay 58 archivos que casan; el documento habla de 59
originales, «uno no está disponible». Ese detalle sí está declarado ahora.
Arreglo:    un `.txt` con los 59 nombres y sus URL públicas junto a
`validar_local.py`.

### [Fable-3 DUDAS 1, 3, 4, 5, 6, 7, 8 | DUDA] Artefactos ausentes
Veredicto:  NO VERIFICABLE — sin cambios, y así lo declaran las limitaciones 9,
10 y 11. El Cuadro 8 completo, las filas históricas del Cuadro 7, el «0,51 con
las tres listas» y el 3.774/950 no tienen artefacto en el repositorio.

### [Codex H24 | DUDA] El estado de la rúbrica está desactualizado
Veredicto:  FALSO como hallazgo del proyecto — es un problema de la skill
`modulo-5-literalevel`, no de la entrega. Documento, estrategia, cuaderno, guion
de vídeo y PDF existen en `entrega/`.

---

## 5. Un defecto nuevo, introducido por una corrección

### [nuevo] Frase rota en §7.4 de `documento.md`
Veredicto:  **ABIERTO — CERRADO A MEDIAS en su origen**
Comprobado: `documento.md:651-652` dice literalmente:

> «Quien quiera verificar el resto tiene que confiar en esa ejecución o
> rehacerla. **Lo detectó una**
> se corrige diciéndolo, no citando un archivo inexistente.»

Falta el sujeto. La limpieza de las menciones a «una auditoría externa» que
recomendó Fable-3 (§«Sobre el exceso de cautela») se aplicó bien al `.tex` —el
párrafo equivalente termina limpio en «…o rehacerla.»— y dejó el `.md` roto. Hoy
quedan 2 menciones a «auditoría» en cada archivo, de las 12–13 que había: la
limpieza se hizo, pero no se releyó el resultado.
Arreglo:    `documento.md:651-652` → borrar «Lo detectó una» y empezar la frase
siguiente, o dejar el párrafo como en el `.tex`. **Es lo primero que hay que
tocar: está en el apartado que sostiene el modelo desplegado.**

---

## Lista 1 — Lo que sigue ABIERTO, por gravedad

**Bloqueantes de lectura (un profesor lo ve al primer repaso):**

| # | Qué | Dónde |
|---|---|---|
| 1 | Frase rota, sin sujeto, en §7.4 | `documento.md:651-652` |
| 2 | El balance de exclusiones da 46 y el cuadro dice 45 | `documento.md:703-707`, `.tex:1687-1690` |
| 3 | «286/286» donde la fuente dice 300/300 — cuatro auditores | `documento.md:846-847`, `.tex:2143-2144` |
| 4 | «De seis niveles a cuatro» siendo cinco | `documento.md:414`, `.tex:1149` |
| 5 | −0,330 emparejado con 18 libros (es de 397; la de 18 es −0,379) | `documento.md:1080-1081` y `.tex` |
| 6 | El pie del Cuadro 10 atribuye a la extracción lo que hace el filtro | `documento.md:690`, `.tex:1624`, `README.md:106` |

**Sustantivos (afectan a lo que el trabajo puede afirmar):**

| # | Qué | Dónde |
|---|---|---|
| 7 | El Cuadro 11 (0,854 / 0,807 / 0,657) no lo calcula ningún guion del repo | `validar_local.py` |
| 8 | La recta 0,72x+0,38 se traza sobre puntos cuyo ajuste es 0,671x+0,408, sin nota de procedencia | `.tex:1764`, `documento.md:729`, `:940` |
| 9 | `validar_local.py` une las líneas: el detector de listas no puede actuar | `validar_local.py:34-35` |
| 10 | La composición y la partición del corpus de anclaje siguen sin publicarse | `modelo_v4/` |
| 11 | Las estadísticas de la ficha son de muestra y «tu ritmo» es un supuesto de 180/110 ppm | `documento.md:800-802`, `estrategia.md:71` |
| 12 | El MAE 0,499 no dice en qué escala está | `documento.md:659`, `.tex:1587` |
| 13 | «No hay relleno» es falso; lo medido es <5e-07 | `documento.md:844-846`, `.tex:2142` |
| 14 | 0,00037 (fp16 A100) y 0,004 (cinco libros) sin respaldo en el repo | `documento.md:760`, `:755` |
| 15 | «Audio de Wiktionary […] porque nada de eso usa red» — en cinco sitios | `documento.md:998`, `.tex:2331`, `.tex:740`, `estrategia.md:214`, `README.md:177` |
| 16 | El tope de 8 ventanas no se declara en §7.4 | `documento.md:636` |
| 17 | «Libros que pueda terminar» en el Resumen; el 0,65 sin declarar | `documento.md:25`, `app/perfil.py:210` |

**De coherencia del repositorio (baratos, y los ve quien clone):**

| # | Qué | Dónde |
|---|---|---|
| 18 | El README dice que el modelo **no está publicado**; el documento dice que sí, en HF público | `README.md:155`, `:165-168`, `app/scoring.py:186` |
| 19 | Tres recuentos de pruebas: 147 / 183 / 198 (y 27 / 28 pasos) | `README.md:138`, `estrategia.md:142,220,388`, `.tex:674,746,832` |
| 20 | «La peor paleta, 9,51» — la peor pareja real es **4,53** | `estrategia.md:132`, `:387` |
| 21 | 317 MB frente a 328 MB, el mismo archivo | `README.md:155` |
| 22 | `gradio>=6.0` sin fijar, con «Gradio 6.26» en el documento | `requirements.txt:5` |
| 23 | `escala_cefr.dat` no dice qué extremo del intervalo incluye | `entrega/datos_figuras/escala_cefr.dat` |
| 24 | Desviaciones poblacionales sin declarar (ddof=0, con n=3) | `validar_local.py:85`, Cuadro 10 |
| 25 | Los 59 PDF no están enumerados | `validar_local.py:57` |
| 26 | «Ajena al proyecto» sin decir que es prima del autor | `documento.md:190` |
| 27 | «No puede mover un decimal» sigue siendo un absoluto | `documento.md:844` |
| 28 | El cuaderno dice que 8 ventanas representan un libro entero (es un capítulo) | `notebook_proyecto.py:1546-1549` |
| 29 | El cuaderno titula «Validación externa ciega» una tabla tecleada a mano | `notebook_proyecto.py:1653`, `:1669-1682` |

---

## Lista 2 — Lo CERRADO A MEDIAS (donde se cuela el error)

1. **La corrección de la tarjeta inexistente rompió el `.md` y dejó limpio el
   `.tex`.** `documento.md:651-652` frente al párrafo equivalente del `.tex`. El
   caso de manual: se editaron los dos archivos y solo se releyó uno.
2. **Las velocidades se unificaron en tres archivos de cuatro.**
   `documento.md`, `estrategia.md` y `app/scoring.py` dicen 8,19 / 112,7 / 13,8×;
   **`arrancar_gpu.py:13-17` sigue en 8,7 / 101,7 / 11,7×**. Fable-1 nombró los
   tres archivos y se arreglaron dos.
3. **Las 6,3 h se retractaron en `entrega/` y siguen vivas en `investigacion/`.**
   `competencia.md:119,326,481` y `transformer_v5.md:190`. La fila 481 de
   `competencia.md` cita como fuente el `§8.3` que la desmiente.
4. **El filtro de prosa se explicó en §4.3(a) y §7.4, pero no en el pie del
   Cuadro 10 ni en el balance de exclusiones ni en el README.** Se corrigió el
   párrafo largo y no las tres frases cortas que lo resumen.
5. **El muestreo de 8 ventanas se acotó en el documento (T7) y no en el
   cuaderno.** `notebook_proyecto.py:1546-1549` sigue diciendo «la respuesta es
   sí» sobre un libro entero.
6. **La celda 7.2 del cuaderno arregló las `axhline` (0,6 y 1,4) y no el título ni
   la tabla tecleada.** Media corrección visible, media invisible.
7. **El Cuadro 14 se movió al apartado del precálculo, pero nadie dijo que el
   recorrido en vivo no forma esos lotes.** `app/ui.py:1193-1194`.
8. **La utilidad personal se acotó en las conclusiones y no en el Resumen.**
   `documento.md:1034-1042` frente a `:25`.
9. **`informe_velocidad.md` fechó su nota obsoleta pero sigue con dos apartados
   «(pendiente)».** Ya no lo cita nadie, lo cual lo salva.

**El README es, en conjunto, el archivo más desfasado del repositorio**: dice que
el modelo no está publicado, da 317 MB, 147 pruebas, atribuye el 45/59 solo a la
extracción y repite el «no usan red». Cinco hallazgos vivos en 182 líneas.

---

## Lista 3 — Coincidencias entre auditores

Un hallazgo que Codex/Astra y Fable encontraron por separado vale más que uno
suelto. Estos son, con su estado:

**Encontrados por las dos familias y todavía ABIERTOS:**

| Hallazgo | Quién | Estado |
|---|---|---|
| «286» donde la fuente dice 300 | Codex H20 · Fable-1 · Fable-2 · Codex-3 (**4 veces**) | ABIERTO |
| −0,330 emparejado con 18 libros | Codex H20 · Fable-3 | ABIERTO |
| «De seis niveles a cuatro» | Codex H20 · Fable-3 | ABIERTO |
| El Cuadro 11 sin guion que lo calcule | Fable-1 · Fable-2 · Codex-3 | ABIERTO |
| `validar_local.py` une líneas y anula el detector de listas | Codex H11 · Fable-2 · Fable-3 | ABIERTO |
| La recta 0,72x+0,38 sin procedencia | Fable-1 · Fable-2 · Fable-3 · Codex-3 | ABIERTO |
| La composición del corpus de anclaje | Codex H21 · Fable-1 (CRÍTICO) · Fable-2 · Codex-3 | ABIERTO, reconocido |
| «Sin clave» confundido con «sin red» | Codex H19 · Codex-3 (misma familia, dos rondas) | ABIERTO |

**Encontrados por las dos familias y ya CERRADOS** (útiles como prueba de que el
proceso funciona):

| Hallazgo | Quién |
|---|---|
| Las 6,3 h de A100 | Codex H13 · Fable-1 · Fable-3 |
| Pruebas que informaban éxito devolviendo la lista de violaciones | Codex H16 · Fable-1 · Fable-2 |
| El validador aprobaba con la lista vacía | Codex H11 · Fable-1 |
| Bandas y empates incoherentes (0,8/1,6 contra 0,6/1,4; `round` contra `floor`) | Codex H06 · Fable-1 · Fable-2 |
| El Cuadro 7 y la promesa de «misma partición» | Codex H12 · Fable-2 (CRÍTICO) · Fable-3 |
| Tres cifras para la misma velocidad | Codex H20/H22 · Fable-1 |
| La tarjeta `metricas_literalevel_v4.json` inexistente | Codex H21 · Fable-1 · Fable-2 |
| British Council presentado como «nunca visto» | Codex H05 · Fable-1 (CRÍTICO) |
| Media de capítulos contra media de ventanas | Codex H07 · Fable-1 (lo verificó ya arreglado) |
| Los 950 extractos eligieron la época | Codex H01 · Fable-1 (lo listó en «lo que está bien») |

**Lo que vio una sola familia y sigue importando:** el muestreo de la ficha y
«tu ritmo» (solo Codex H17); los lotes de 64/128 en el recorrido interactivo
(solo Codex H14); el recuento de pruebas y la unidad del modelo (solo Fable-3);
la peor pareja de contraste, 4,53 (solo Fable-2, y lo he reproducido).

---

## ¿Se puede entregar hoy a un profesor universitario?

**No todavía, pero falta poco y es todo redacción:** hay que arreglar la frase
rota de `documento.md:651`, cerrar el balance de exclusiones en 45, cambiar 286
por 300, «seis niveles» por «cinco» y el −0,330 de 18 libros por el de 397
—media hora—, y decidir entre añadir a `validar_local.py` el cálculo del Cuadro
11 y declarar la procedencia de la recta 0,72x+0,38, o rebajar ambas cosas a
«resultado declarado, no recalculable desde el repositorio»; lo demás de la
lista 1 —README desfasado, recuento de pruebas, 9,51, Gradio sin fijar— no
invalida nada pero es lo que un evaluador atento abre primero.
