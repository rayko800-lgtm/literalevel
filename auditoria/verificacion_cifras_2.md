# Segunda verificación de cifras — sobre el estado del commit `8b579b6`

Encargo estrecho, el mismo de la primera vez: **ejecutar código y comprobar que
cada cifra publicada sale de donde dice**. Esta tanda se hace **después** de las
correcciones de hoy (46 → 47 textos, el archivo 59, el `.dat`, el TikZ, la
tarjeta pública y `_es_boilerplate`), y su foco son las cifras **derivadas**,
que es donde falló la ronda anterior, y lo **dibujado**, no solo lo escrito.

- Fecha: 9 de septiembre de 2026. Commit verificado: `8b579b6`.
- Máquina: Windows 11, CPU.
- **Nada del proyecto se modificó.** La única escritura es este archivo.
- Ejecutado de verdad: `validar_local.py`, `pruebas_extremas.py`,
  `pruebas_integracion.py`, `pruebas_ficha.py`, `tests_smoke.py`, más scripts
  propios en el scratchpad para WCAG, `_es_boilerplate`, los PDF y las rectas.
- La primera verificación está en `auditoria/verificacion_cifras.md`. Sus tres
  hallazgos (el archivo 59, los 332 MB, los 571 MB) **no se repiten aquí**; el
  del archivo 59 está corregido y se comprueba abajo de paso.

---

## 1. Las cifras vivas — `validar_local.py`, una sola ejecución (exit 0)

| cifra | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| **47** textos evaluados | Cuadros 10 y 11; doc `.md` 415, 707–712, 774; `.tex` 1146, 1643, 1766 | `VALIDACION CORRECTA: 47 textos` | **sí** |
| A1 · n=3 · 0,5040 · 0,111 | Cuadro 10 | `A1  3  0.5040  0.111` | **sí** |
| **A2 · n=8 · 0,5561 · 0,223** | Cuadro 10 | `A2  8  0.5561  0.223` | **sí** |
| B1 · n=12 · 0,9276 · 0,198 | Cuadro 10 | `B1 12  0.9276  0.198` | **sí** |
| B2 · n=12 · 1,2414 · 0,236 | Cuadro 10 | `B2 12  1.2414  0.236` | **sí** |
| C1 · n=12 · 1,4952 · 0,172 | Cuadro 10 | `C1 12  1.4952  0.172` | **sí** |
| Cuadro 12 · modelo v4 **0,860** | doc 776 | 0.860 | **sí** |
| Cuadro 12 · contar palabras **0,807** | doc 777 | 0.807 | **sí** |
| Cuadro 12 · parcial **0,668** | doc 778 | 0.668 | **sí** |
| Modelo contra longitud **0,732** | doc 791 | 0.732 | **sí** |
| Baseline parcial «no está definida» | doc 786–789 | imprime literalmente `indefinida` | **sí** |
| Filtro **estricto: 31** textos | doc 734 («31 en vez de 47») | `filtro COMPLETO (con saltos de linea): 31` | **sí** |
| Sin cuerpo localizable: **2** | Cuadro 11 | 2 | **sí** |
| Rechazados por `continuous_prose`: **10** | Cuadro 11 | 10 | **sí** |
| Los 10 son **nueve A1 y uno B1** | doc 755–757 | 9 ficheros `A1__…`, 1 `B1__…` | **sí** |
| Los 10 caen por **<150 palabras** | doc 757–758 | los diez, mismo `ValueError` | **sí** |
| Balance **59 − 2 − 10 = 47** | Cuadro 11 | 59−2−10 = **47** | **sí** |
| Medias estrictamente crecientes | doc 46–47, 1152 | el guion lo verifica y lo afirma | **sí** |

Salida literal (sin barras de carga):

```
nivel    n   media 0-2  desv (pobl.)   (Colab reportó)
A1       3      0.5040         0.111   —
A2       8      0.5561         0.223   0.6479
B1      12      0.9276         0.198   0.9513
B2      12      1.2414         0.236   1.2883
C1      12      1.4952         0.172   1.4950

textos sin cuerpo localizable: 2
textos que pasarian el filtro COMPLETO (con saltos de linea): 31
textos que fallaron al puntuar: 10

Cuadro 12 - el modelo frente a la senal trivial (47 textos)
  modelo v4                                  0.860
  contar palabras, sin modelo                0.807
  modelo descontando la longitud (parcial)   0.668
  (de paso: modelo contra longitud           0.732)
  contar palabras descontando la longitud:   indefinida

VALIDACION CORRECTA: 47 textos, 5 niveles, medias estrictamente crecientes.
```

**El 59 ya no es una cifra heredada.** El patrón de `validar_local.py` es hoy
`*LearnEnglish?Reading*.pdf` (con `?`, línea 100) y encuentra **59 de 59** en
`C:\Users\laura\Downloads`. El manifiesto lista 59 nombres únicos, 12+10+13+12+12
= 59, y los 59 existen en disco. El hallazgo 3 de la verificación anterior está
cerrado.

---

## 2. Las derivadas — donde falló la ronda anterior

Todas calculadas a mano desde las cifras que imprime el guion, no copiadas.

| derivada | lo que dice el documento | valor obtenido | ¿coincide? |
|---|---|---|---|
| Escalón A1–A2 | **0,052** (doc `.md` 49, `.tex` 250, PDF pág. 1) | 0,5561 − 0,5040 = **0,0521** | **sí** |
| Desviación de A2 frente a Colab | **0,09** (doc 723 y 750) | 0,6479 − 0,5561 = **0,0918** | **sí** |
| Margen del modelo sobre contar palabras | **0,053** (no se publica como número; el texto dice «llega casi tan lejos») | 0,860 − 0,807 = **0,053** | **sí**, y coherente con la frase |
| Escalones después del primero | **tres** (doc `.md` 50, `.tex` 251) | escalones = 0,0521 · **0,3715 · 0,3138 · 0,2538** → cinco niveles, cuatro escalones, **tres** tras el primero | **sí en el documento**, **NO en la presentación** (§6) |
| «Una diferencia de 0,05 entre dos niveles adyacentes» | doc 1059 | 0,0521 | **sí** |
| Recta de Colab `0,7196x + 0,3760` | doc 795 | `numpy.polyfit` sobre A2–C1 de Colab: **0,719575x + 0,376050** | **sí** |
| Recta local `0,67x + 0,41` | doc 796 y pie de la figura de compresión | `polyfit` sobre las **cinco medias de hoy** (con A2 = 0,5561): **0,666925x + 0,411320** → 0,67x + 0,41 | **sí** |

La recta local es la que había que rehacer con el A2 nuevo, y sigue redondeando
a lo mismo: la corrección de 0,5480 → 0,5561 mueve la pendiente de 0,668950 a
0,666925 y la ordenada de 0,408080 a 0,411320. Los dos decimales publicados
aguantan.

---

## 3. Lo que está dibujado

### `entrega/datos_figuras/validacion.dat` contra el Cuadro 10

```
nivel n media desv
A1 3 0.5040 0.111
A2 8 0.5561 0.223
B1 12 0.9276 0.198
B2 12 1.2414 0.236
C1 12 1.4952 0.172
```

| comprobación | resultado | ¿coincide? |
|---|---|---|
| `.dat` contra Cuadro 10 del `.md` (líneas 705–709) | fila a fila, idénticos | **sí** |
| `.dat` contra el `tabular` del `.tex` (1636–1640) | fila a fila, idénticos | **sí** |
| `.dat` contra la salida de `validar_local.py` | fila a fila, idénticos | **sí** |
| n de A2 en el `.dat` | 8 | **sí** |

### Las etiquetas `n` escritas a mano dentro del `tikzpicture`

`entrega/documento.tex`, líneas 1677–1681, cinco `\node` sueltos:

| etiqueta | valor en el TikZ | valor en el `.dat` | ¿coincide? |
|---|---|---|---|
| A1 | `n\,=\,3` | 3 | **sí** |
| **A2** | `n\,=\,8` | **8** | **sí** |
| B1 | `n\,=\,12` | 12 | **sí** |
| B2 | `n\,=\,12` | 12 | **sí** |
| C1 | `n\,=\,12` | 12 | **sí** |

Es lo que el commit `425750f` dice haber arreglado, y está arreglado: la
etiqueta de A2 pone 8. Las barras salen del `.dat` por `table[...]`, así que no
pueden desincronizarse; las etiquetas sí podían, y no lo están.

### La flecha anotada de la figura de compresión

`entrega/documento.tex`, líneas 1813–1874.

| elemento | valor dibujado | valor de referencia | ¿coincide? |
|---|---|---|---|
| Punto A2 | `(0.4, 0.5561)` | 0,5561 | **sí** |
| **Flecha de sobreestimación en A2** | `(0.4,0.40) -- (0.4,0.556)` | ancla 0,40 → media 0,5561 | **sí** |
| Flecha de subestimación en C1 | `(1.6,1.60) -- (1.6,1.4952)` | ancla 1,60 → media 1,4952 | **sí** |
| Puntos A1, B1, B2, C1 | 0,5040 · 0,9276 · 1,2414 · 1,4952 | Cuadro 10 | **sí** |
| Recta roja dibujada | `0.72*x+0.38` | recta de Colab, 0,7196 / 0,3760 | **sí** |
| Pie: «sobre los cinco puntos locales sale 0,67x + 0,41» | 0,67 / 0,41 | recalculado 0,666925 / 0,411320 | **sí** |

La flecha de A2 llegaba antes a 0,548; hoy llega a 0,556. Está al día.

---

## 4. Las 205 pruebas y las 40 parejas de contraste

### Recuento propio de pruebas

| cifra | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| **205** pruebas extremas | `documento.tex` 679, 753, 839; `estrategia.md` 143, 223, 391; `README.md` 152 | 205 líneas `ok` en la salida, **0** fallos; el contador propio del guion imprime `Las 205 pruebas extremas pasan` (exit 0) | **sí** |
| **27** pasos de integración | `documento.tex` 839 | `Los 27 pasos del recorrido encadenan bien.` (exit 0) | **sí** |
| `pruebas_ficha.py` | — | `Todas las pruebas de la ficha pasan.` (exit 0) | — |
| `tests_smoke.py` | — | `TODO OK` (exit 0) | — |

Contadas por mi cuenta, línea a línea de la salida, sin fiarme del contador del
guion: 205 líneas `ok`, de las cuales 203 nombres distintos (dos nombres se
repiten en pruebas parametrizadas). Cero líneas de fallo.

### Contraste WCAG, calculado desde cero sobre `app/paletas.py`

Script propio e independiente del repositorio: parsea `app/paletas.py` con
`ast.literal_eval` (sin importar el módulo), convierte `#rrggbb` y `rgba(...)` a
sRGB, aplica la luminancia relativa de WCAG 2.x (umbral 0,03928, gamma 2,4,
pesos 0,2126 / 0,7152 / 0,0722) y la razón `(L1+0,05)/(L2+0,05)`.

| cifra | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| **40 parejas** («cuarenta parejas», ocho por paleta) | `documento.tex` 667, 838; `estrategia.md` 133, 390 | 5 paletas × 8 parejas = **40** | **sí** |
| Cinco paletas | `documento.tex` 667 | `hielo`, `amanecer`, `menta`, `papel`, `medianoche` | **sí** |
| Peor pareja de **texto normal 4,53** (umbral 4,5) | `documento.tex` 667, 838 | **4,5273** en `hielo/boton-alto` → 4,53 | **sí** |
| Peor pareja de **título 3,11** (umbral 3,0) | `documento.tex` 667, 838 | **3,1081** en `menta/titulo-3` → 3,11 | **sí** |
| «Las cinco pasan» | `documento.tex` 667 | **ninguna** de las 40 baja de su umbral | **sí** |

Cinco peores de texto normal: 4,5273 `hielo/boton-alto` · 4,6121
`papel/pestana-elegida` · 4,6200 `amanecer/pestana-elegida` · 4,6470
`menta/pestana-elegida` · 4,6548 `papel/boton-alto`.
Cinco peores de título: 3,1081 `menta/titulo-3` · 3,1084 `menta/titulo-2` ·
3,1259 `amanecer/titulo-2` · 3,1316 `papel/titulo-3` · 3,1328
`amanecer/titulo-3`.

Comprobado además que el resultado **no depende de cómo se traten los canales
alfa**: la prueba del repositorio descarta el alfa de los `rgba(...)`; repetido
componiendo cada color sobre el `--ll-fondo` de su paleta salen **exactamente
las mismas 40 razones**, con los mismos peores casos. La cifra publicada es
robusta a esa decisión.

Estas cifras no aparecen en `entrega/documento.md`, que es una versión más
corta; viven en `entrega/documento.tex` (que es de donde sale el PDF) y en
`entrega/estrategia.md`. Las dos fuentes dicen lo mismo.

---

## 5. `app/ficha.py::_es_boilerplate`, que cambió hoy

Casos fabricados a mano (licencia larga de Gutenberg, portadilla,
título delator, prosa limpia, prosa con la cabecera legal delante, prosa con
cabecera **y** licencia al final, y prosa que menciona Gutenberg de pasada):

| caso | palabras | `_es_boilerplate` | esperado | ¿coincide? |
|---|---|---|---|---|
| Licencia larga del final (`THE FULL PROJECT GUTENBERG LICENSE` + `Section 1…`) | 696 | **True** | True | **sí** |
| Portadilla de Gutenberg (corta, con `Produced by`) | 74 | **True** | True | **sí** |
| Título delator con cuerpo de prosa | 1.908 | **True** | True | **sí** |
| Prosa limpia | 1.908 | **False** | False | **sí** |
| **Prosa con la cabecera legal delante** («Texto completo») | 2.027 | **False** | False | **sí** |
| Prosa con cabecera **y** licencia al final | 2.733 | **False** | False | **sí** |
| Prosa que menciona Gutenberg de pasada | 1.914 | **False** | False | **sí** |

Y el arreglo es real, no cosmético. Reimplementando la lógica **anterior**
(mirar las primeras 400 palabras del texto **crudo**, sin `sin_licencia`) sobre
los mismos casos:

| caso | lógica vieja | lógica de hoy |
|---|---|---|
| Prosa con cabecera, 2.027 palabras | **True** (se descartaba) | False |
| Prosa con cabecera, 5.843 palabras | **True** (se descartaba) | False |
| Licencia larga | True | **True** |
| Portadilla | True | **True** |

Es decir: sigue cazando lo que tenía que cazar y ha dejado de tirar prosa. De
propina, `_palabras_reales` sobre el capítulo único «Texto completo» de 2.733
palabras brutas devuelve **1.908**, que son las de la obra sin envoltura —lo que
sostiene la afirmación de que el tiempo de lectura ya no sale inflado por texto
legal—.

---

## 6. Los tres PDF

Texto extraído con `pypdf` (`documento.pdf` 43 páginas / 114.141 caracteres;
`presentacion.pdf` 12 páginas; `guion_video.pdf` 6 páginas). Los tres PDF son
**más nuevos que sus `.tex`**, así que están recompilados tras las correcciones.
La búsqueda se hizo dos veces: literal, y con los espacios y los guiones de
corte de línea normalizados, para que no se escape una cifra partida en dos
líneas.

### Cifras retiradas — ninguna debe aparecer

| cifra retirada | `documento.pdf` | `presentacion.pdf` | `guion_video.pdf` | ¿limpio? |
|---|---|---|---|---|
| `0,548` | 0 | 0 | 0 | **sí** |
| `1,248` | 0 | 0 | 0 | **sí** |
| `0,855` | 0 | 0 | 0 | **sí** |
| `0,799` | 0 | 0 | 0 | **sí** |
| `0,665` | 0 | 0 | 0 | **sí** |
| «45 textos» / «46 textos» | 0 | 0 | 0 | **sí** |
| «cuatro escalones» (literal) | 0 | 0 | 0 | **sí** |
| «se desvía 0,10» | 0 | 0 | 0 | **sí** |

Barrido más amplio, por si la cifra viajaba con otra cara: los únicos números
que preceden a la palabra «textos» en los tres PDF son 3, 12, 31, 38, 47, 59 y
567 —todos legítimos—. Las tres apariciones de «46» en `documento.pdf` son un
`0,46` de exactitud, otro `0,46` en una figura de barras y el volumen 59(11) de
una referencia bibliográfica. El `0,10` que queda en `documento.pdf` habla de
«los 0,10 de diferencia» entre dos definiciones de `palabras_raras`, no de A2.

### Cifras de hoy — deben aparecer

| cifra | `documento.pdf` | `presentacion.pdf` | `guion_video.pdf` |
|---|---|---|---|
| «47 textos» | 4 | 1 | — |
| 0,5561 | 4 | (0,556) 1 | — |
| 0,223 | 2 | — | — |
| 0,860 / 0,807 / 0,668 | 4 / 3 / 2 | 1 / 1 / 1 | — |
| 0,732 | 1 | — | — |
| 0,052 | 1 | — | — |
| «tres escalones» | 1 | — | — |
| 0,5040 · 0,9276 · 1,2414 · 1,4952 | 4 · 4 · 4 · 5 | (0,504 · 0,928 · 1,241 · 1,495) 1 | — |

El guion del vídeo **no publica ninguna cifra del corpus externo**: dice
«distilroberta-base · Spearman 0,908 interno · orden MCER creciente en textos
externos». No hay nada que corregir ahí, y por eso está vacía su columna. (El
`45` que aparece en él es el 45 % de la S del reparto ANSVA, no un recuento de
textos.)

### El `0,725`, como avisaba el encargo

Aparece 3 veces en `documento.pdf` y 1 en `presentacion.pdf`, y **siempre** es
el Pearson del mejor LLM zero-shot publicado en el corpus CLEAR, junto a 0,517
de las fórmulas clásicas y 0,89 de LiteraLevel. **No es un resto del 0,732.**

### Lo único que no coincide

`entrega/presentacion.pdf`, diapositiva 7 («El modelo desplegado»), al pie:

> El escalón A1–A2 descansa en 3 textos y está dentro del ruido; **los otros
> cuatro**, no.

Con cinco niveles hay **cuatro** escalones en total, así que tras el primero
quedan **tres**, no cuatro. Medidos: 0,0521 · 0,3715 · 0,3138 · 0,2538. El
documento lo dice bien —«Los tres escalones siguientes, no»,
`documento.tex` 251 y `documento.md` 50, y así sale impreso en la página 1 del
PDF—; la presentación no.

Está en `entrega/presentacion.tex` línea 241, y `git log -S` lo sitúa en
`aed7751`, el commit que creó la presentación: **no es una regresión de hoy, es
la única frase que las tandas de corrección no tocaron**, y se escapó a la
búsqueda porque no contiene la cadena literal «cuatro escalones».

---

## 7. La tarjeta publicada en Hugging Face

Descargada de
`https://huggingface.co/MikeMaki1763/literalevel-v4/raw/main/README.md`
(HTTP 200, 4.421 bytes).

| comprobación | resultado | ¿coincide? |
|---|---|---|
| Tarjeta publicada vs. `modelo_v4/README.md` local | `diff` **vacío**; mismo MD5 `d0f2a2e673dcadf72c574206b4a40d4e` | **sí, idénticas byte a byte** |
| Medias por nivel: 0,504 · 0,556 · 0,928 · 1,241 · 1,495 | son 0,5040 · **0,5561** · 0,9276 · 1,2414 · 1,4952 a tres decimales | **sí** |
| A2 = **0,556** (era 0,548) | corregida | **sí** |
| Contar palabras 0,807 vs. modelo 0,860 | idénticas al Cuadro 12 | **sí** |
| Validación ciega: 144 · 97,2 % · 0,908 | doc `.md` 1154–1155, presentación diapositiva 7 | **sí** |
| 53,5 % exacto | doc: 77/144 = 53,47 % | **sí**, redondeado |
| British Council externo: 38 · 100 % · 0,829 | doc `.md` 1153–1154 («0,829 con 38 textos, 0,860 con los 47») | **sí** |
| Escala pública ×0,4 y `floor(x + 0,5)` | contrato de `AGENTS.md` y doc | **sí** |
| Compresión `0,72 · real + 0,38` | recta de Colab, 0,7196 / 0,3760 | **sí** |
| 654 documentos de anclaje | doc `.md` 658, 666 | **sí** |
| «los nombres de los 59 archivos están en el repositorio» | 59 listados en el manifiesto, 59 en disco | **sí** |

La tarjeta pública, la local y el documento dicen lo mismo. El desfase de dos
correcciones que arregló `8b579b6` está efectivamente cerrado.

---

## Resumen: lo que NO coincide

De las **68 comprobaciones de esta tanda, 67 se reproducen exactamente**. La
única que no:

1. **`entrega/presentacion.pdf`, diapositiva 7: «los otros cuatro, no».**
   Debería decir **tres**. Cinco niveles dan cuatro escalones; quitando el
   primero (A1–A2, el que se declara dentro del ruido) quedan tres:
   0,3715 · 0,3138 · 0,2538. El documento ya lo dice bien; la presentación
   arrastra el recuento desde `aed7751` y ninguna de las tandas de hoy lo tocó,
   porque no contiene la cadena literal «cuatro escalones» que se estuvo
   buscando. Fuente: `entrega/presentacion.tex` línea 241.

**Todo lo demás coincide.** Las cinco medias con sus desviaciones y sus *n*, el
47 y su balance 59 − 2 − 10, el 31 del filtro estricto, el Cuadro 12 entero
(0,860 / 0,807 / 0,668) y el 0,732 de paso; las cuatro derivadas que fallaron la
vez anterior —el escalón 0,052, la desviación 0,09, el margen 0,053 y los tres
escalones del documento—; las dos rectas de compresión rehechas con el A2 nuevo;
el `.dat`, las cinco etiquetas `n` del TikZ y las dos flechas anotadas de la
figura de compresión; las 205 pruebas contadas a mano y las 40 parejas de
contraste recalculadas desde cero, con sus peores casos en 4,5273 y 3,1081; los
siete casos fabricados de `_es_boilerplate`, incluida la prosa con cabecera
legal que antes se descartaba; los tres PDF, sin rastro de ninguna de las ocho
cifras retiradas; y la tarjeta de Hugging Face, idéntica byte a byte a la local.
