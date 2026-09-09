# Trabajo sobre `entrega/documento.md` y `entrega/documento.tex`

**Encargo.** Observaciones de `auditoria/lectura_de_profesor.md` sobre el §7.4
ahogado en salvedades, la falta de un mapa de los conjuntos de evaluación y las
siete menciones a «una versión anterior de este documento». Ámbito: los dos
archivos del documento y ninguno más. No se tocó `presentacion.tex` ni
`guion_video.*`.

**Nota sobre la numeración del encargo.** El encargo dice «observaciones 3, 4 y
7». Las tareas descritas son en realidad las observaciones **3, 4 y 14** del
informe; la 7 es la frase «deja de abandonar libros» del `guion_video.md`, que
está fuera de este ámbito y no se ha tocado. Se trabajó sobre las tareas
descritas, no sobre los números.

---

## Cifras de control, antes y después

| | Antes | Después |
|---|---|---|
| `Overfull \hbox` distintos | **11** | **11** (mismas líneas, mismas magnitudes) |
| Avisos `Overfull` en la salida de tectonic (todas las pasadas) | 23 | 23 |
| Páginas del PDF | 43 | **45** |
| `\ref` distintas / `\label` | 41 / 54 | 43 / 56 |
| Referencias rotas | ninguna | **ninguna** |
| Errores de compilación / citas sin resolver | 0 | 0 |
| Cuadros numerados en el `.md` | 16 | 17 |
| «una versión anterior de este documento» | 7 en cada archivo | **2 en cada archivo** |

El conjunto de desbordes es **idéntico** al de partida: 50,65 pt en la línea
263; cuatro en la 903 (6,25 / 13,81 / 31,91 / 37,66 pt); 13,97; 2,68; 18,09;
2,36; 2,27 y 30,60 pt. Todos preexistentes, ninguno introducido aquí.

---

## Tarea 1 — El §7.4 afirmaba y luego se desdecía

### Qué se movió

**1. La afirmación va primero, entera y sin peros** (139 palabras). Antes decía
sólo «Sobre textos externos con nivel MCER oficial, las medias por nivel quedan
estrictamente crecientes» y saltaba a la tabla. Ahora dice **qué se midió** (los
47 textos de la reproducción local de British Council, cada uno con nivel MCER
oficial de la institución que lo publica, ninguno usado para ajustar los pesos),
**cómo** (`validar_local.py`, agrupados por nivel) y **qué salió** (las cinco
medias crecientes, de A1 a C1, y Spearman 0,860). Cierra diciendo que ése es el
resultado que el trabajo afirma haber conseguido.

Se mantiene la afirmación **sobre los cinco niveles**, que es lo que está
medido. El informe del profesor proponía rebajarla a A2–C1; el encargo pedía
«primero la afirmación, entera y sin peros» y no tocar ninguna cifra, así que se
conservó el alcance real de la medición y el recorte a cuatro niveles queda
descrito como salvedad, no como afirmación.

**2. Las salvedades van después, agrupadas y rotuladas.** Se abre un bloque
titulado **«La letra pequeña de ese resultado»** (`\subsubsection*` en el `.tex`,
`####` en el `.md`) con una entradilla que avisa de que empieza la letra
pequeña, y cuatro salvedades numeradas en palabras:

- *Una: el escalón A1–A2 está dentro del ruido.* Es nueva **en este apartado**,
  pero no en el documento: repite literalmente lo que ya decía el Resumen (0,052
  sobre desviaciones de 0,111 y 0,223, tres textos). Se trajo aquí porque era la
  salvedad que el §7.4 no ponía y el lector la necesitaba junto a la tabla.
- *Dos: es una reproducción local, no independiente.* Es el párrafo «Esta tabla
  se recalcula…» tal cual, con los derechos de los PDF y la desviación frente a
  Colab.
- *Tres: los 38 de Colab y los 47 de aquí son dos tandas distintas, y no se
  restan.* Es el párrafo del balance, con su Cuadro 12 (`cuad:balance`) detrás.
- *Cuatro: el validador local filtra más flojo que la aplicación.* Cinco líneas:
  sobreviven 31 de 47, A1 se queda con un texto, y remisión al §7.7.

**3. La forense del filtro sale a un apartado propio.** Los dos párrafos largos
—el de las cuatro reglas de `scoring.continuous_prose` y el de los diez textos
rechazados— se llevaron íntegros a un **§7.7, «Qué filtra el validador local y
qué filtra la aplicación»**, al final del §7 (después del cuadro de decisiones
metodológicas, antes del §8). Allí van repartidos en cuatro párrafos con
rótulo: qué regla se desactiva, por qué se conserva así, qué textos se caen y
por qué regla, y qué le hace eso al resultado principal. **No se borró ninguna
salvedad**: las 437 palabras están todas, sólo que ya no cortan la lectura de la
tabla.

Efecto medido: entre el pie de la tabla principal y el §7.5 había **588
palabras** de advertencias; ahora hay **405**, y están ordenadas y rotuladas.

### Qué se comprobó

- **Desbordes**: sin cambios respecto a la línea base (11 distintos, mismas
  magnitudes).
- **Páginas y colocación**: se extrajo el texto del PDF página a página con
  `pypdf` y se comprobó dónde cae cada bloque. La afirmación, el cuadro de
  validación, la figura de validación y el rótulo «La letra pequeña» quedan
  **los cuatro en la misma página** (p. 29). El cuadro del balance y el §7.5
  caen en la 30. El §7.7 empieza y termina en la 33, completo, con el §8 detrás.
  Ninguna figura ni cuadro quedó suelto en una página donde no pinta nada, así
  que no hizo falta tocar ningún `[htbp]`.
- **Referencias**: `sec:filtro` es nueva y tiene su `\label`; las `\ref` a
  `cuad:validacion`, `cuad:balance` y `cuad:baseline` sobreviven al traslado.
  Cero rotas.

### Un arreglo de paso

En el texto que se movió había una errata de sintaxis: *«porque es la que
reproduce **las el** cuadro~\ref{cuad:validacion}»*. Al reescribir el párrafo
quedó como «porque la unión con espacio es la que reproduce el
cuadro~\ref{cuad:validacion}». Es prosa, no cifra.

---

## Tarea 2 — Las reglas del juego

Se añadió un cuadro con **una fila por conjunto**, al principio del §7.4, antes
de cualquier cifra de evaluación —es decir, antes también del cuadro de métricas
del modelo desplegado, porque es ahí donde el lector se encuentra por primera
vez el 144 y el 38 juntos—. Columnas: **conjunto · n · de dónde sale · qué se
mide con él · qué *no* se puede hacer con él**.

Las cinco filas: **144** (validación ciega interna), **38** (British Council,
tanda de Colab), **47** (British Council, reproducción local), **31** (los que
pasan el filtro completo de la aplicación) y **59** (todos los publicados). La
columna de prohibiciones dice explícitamente que **los 38 y los 47 son tandas
distintas y no se restan** («47 − 38 no son nueve textos concretos que se puedan
nombrar»), que el 144 no es externo y su 0,908 no se compara con las cifras de
British Council, que los 47 no son «los textos que la aplicación aceptaría», que
el 31 no sostiene el orden sobre cinco niveles y no da ninguna cifra publicada,
y que el 59 no es un conjunto evaluable.

Va precedido de un párrafo —«Antes de las cifras, las reglas del juego»— que
avisa de que son cinco conjuntos, de que cuatro salen del mismo material y de
que **sus tamaños no se restan entre sí**.

Además se citó el cuadro **desde el §5.2**, que es donde el informe del profesor
localiza el punto en que el lector pierde el hilo (el párrafo de «Dificultad
frente a dominio», con el 0,879 y el 0,765): una frase al final remite al cuadro
nuevo.

**Ninguna cifra del cuadro es nueva.** Todas salen de párrafos que ya estaban en
el documento. Deliberadamente **no** se puso un Spearman para los conjuntos de
31 y 59, porque el documento no lo reporta y no se iba a inventar; y no se citó
el 0,879 en la fila del 59 porque el documento no dice con precisión sobre qué
conjunto filtrado se midió el 0,765 con el que se compara.

### Renumeración

En el `.tex` los cuadros se numeran solos: el nuevo es `cuad:conjuntos` y el
resto se corrió solo. En el `.md`, que numera a mano, se renumeró **Cuadro 9 →
10 … Cuadro 16 → 17** con una expresión regular en orden descendente, aplicada a
captions **y** a referencias en el texto, y se comprobó el recuento de cada
número antes y después:

```
 9 : 2 -> 0      13 : 1 -> 2
10 : 5 -> 2      14 : 1 -> 1
11 : 3 -> 5      15 : 1 -> 1
12 : 2 -> 3      16 : 1 -> 1
                 17 : 0 -> 1
```

Los pies de cuadro del `.md` quedan en secuencia 1–17 sin huecos ni repetidos
(verificado con `grep` sobre `^\*Cuadro [0-9]`). Los Cuadros 1–8 no se tocaron.
Sigue en pie lo declarado en la cabecera del `.md`: **la numeración del `.md` y
la del PDF no coinciden** (en el PDF el cuadro nuevo es el 14, porque allí se
numeran también tablas que en el `.md` van como listas).

### Qué se comprobó

- Al compilar aparecieron **dos desbordes nuevos**, los dos en el cuadro nuevo:
  **40,64 pt** en la fila del 31 y **103,64 pt** en la fila del 59. La causa era
  la misma: nombres de código largos (`scoring.continuous_prose` y
  `entrega/manifiesto_corpus_externo.md`) en una columna de 3 cm, que además
  `\cod` compone con `\small` absoluto y por tanto **más grande** que el
  `\footnotesize` de la tabla. Se resolvió sacando los dos nombres de esa
  columna: en la fila del 31 se dice «las cuatro reglas del filtro de prosa
  continua» y en la del 59 «el manifiesto del corpus externo». Los dos nombres
  completos siguen estando en el §7.7 y en el cuadro del balance. Tras el
  arreglo, **cero desbordes nuevos**.
- El cuadro parte a dos páginas (27–28) y **repite la cabecera** en la segunda:
  se usó `longtable` con `\endfirsthead`/`\endhead` precisamente para eso, y
  además así el cuadro no flota lejos del párrafo que lo anuncia.

---

## Tarea 3 — De siete «una versión anterior de este documento» a dos

`grep -c` sobre la frase completa da 0 porque en el `.md` está partida por saltos
de línea. Contadas de verdad eran **siete** en cada archivo. Se conservan **dos**:

1. **La del §7.4** — la tarjeta `metricas_literalevel_v4.json` que no existe. Se
   conserva porque nombra un archivo concreto que un evaluador podría buscar en
   el repositorio, y porque la limitación 9 remite al §7.4 para justificar que
   las cifras no tienen respaldo en el repositorio.
2. **La nota global del §9**, al abrir las limitaciones. Es la que el informe del
   profesor pide conservar, y es la que hace innecesarias las demás.

Las cinco retiradas, con lo que dicen ahora:

| Dónde | Antes | Ahora |
|---|---|---|
| §2.1, el recorte | «Una versión anterior publicaba el recorte fuera del sumatorio; el código siempre hizo lo que se describe aquí» | «El recorte va dentro del sumatorio, que es lo que hace el código» |
| §4.3(a), el filtro | «…porque una versión anterior decía que el filtro se fijó “antes de mirar ningún resultado” y no es exacto» | «…porque el filtro no se fijó antes de mirar ningún resultado» |
| §7.4, el balance | «…tiene dos causas, y una versión anterior solo mencionaba una» | «…son dos tandas distintas, y no se restan» (dentro de la salvedad tres) |
| §8.3, las horas | «Una versión anterior decía 6,3 horas, que no se sigue de ninguno de los dos supuestos» | «Cualquier cifra fuera de esa horquilla no se sigue de ninguno de los dos supuestos» |
| §11, primera línea | «Y conviene separar dos cosas que esta frase mezclaba en una versión anterior» | «Hay dos resultados y vienen de corpus distintos, así que conviene no mezclarlos» |

Dos retoques de la misma familia, en la misma frase de las conclusiones y del
§7.4:

- «Atribuirlos a los externos **era** un error» → «**sería** un error». Deja de
  ser una confesión y sigue siendo el aviso al lector.
- Se quitó del `.md` la frase «Se corrige diciéndolo, no citando un archivo que
  no existe», que el `.tex` **no tenía**: era una divergencia entre los dos
  archivos y además la séptima voz de autocorrección.

### Qué se comprobó

Recuento final por programa: **2 en `documento.md` y 2 en `documento.tex`**, y
son **las mismas dos** en los dos archivos (se imprimió el contexto de cada una
para compararlas).

---

## Paridad entre los dos archivos

Se comprobó por programa que 19 frases distintivas de los cambios están en los
dos archivos. Todas salieron en los dos salvo una, y esa sólo porque en el `.md`
el salto de línea la parte por la mitad; verificada a ojo.

---

## Lo que vi y no toqué

1. **La observación 7 del informe** (el vídeo promete «deja de abandonar
   libros», que el documento declara no medido) está en `guion_video.md`. Fuera
   de ámbito, no se tocó.
2. **La observación 10 ya estaba arreglada** antes de que yo llegara. La
   limitación 9 no dice «tal como constan en la tarjeta del modelo» sino «tal
   como salieron de aquella ejecución, sin ningún archivo en el repositorio que
   las respalde —el apartado 7.4 lo explica—». No hay contradicción con el
   párrafo del §7.4 que conservé; al contrario, se apoyan. Lo digo porque
   refuerza la decisión de conservar esa mención y no otra.
3. **Queda una frase de la misma familia sin tocar**, en el §11: «Y aquí hay que
   poner un límite **que el documento no ponía**». No contiene «una versión
   anterior», así que quedaba fuera de la tarea 3, pero es la misma voz. Si se
   quiere rematar: «Y aquí hay que poner un límite».
4. **Ninguna cifra se tocó.** Se reutilizaron las que ya estaban (47, 144, 38,
   31, 59, 0,908, 0,829, 0,860, 0,807, 0,668, 0,052, 0,111, 0,223, 89,8 %, las
   cinco medias). No encontré ninguna que me pareciera mal al reestructurar.
5. **Las páginas suben de 43 a 45.** Es el coste del cuadro nuevo (página y
   cuarto, porque son cinco filas con cinco columnas de texto) más el rótulo del
   §7.7. No hay forma de meterlo sin pagarlo; comprobé que las dos páginas de
   más no dejan ninguna figura ni cuadro huérfano.

## Cómo se hizo

Nada por heredoc. Todas las ediciones fueron guiones de Python escritos con la
herramienta `Write` y ejecutados; cada sustitución verifica primero que el texto
a reemplazar **aparece exactamente una vez** y aborta si no. Están en el
directorio de trabajo temporal de la sesión (`edita_tex_1..5.py`,
`edita_md_1..5.py`, `edita_pointer.py`) por si hace falta releer qué hizo cada
uno.
