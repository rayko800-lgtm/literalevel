# Coherencia entre entregables

Auditoría de **desajustes entre archivos que deberían decir lo mismo**. No se
comprueba si las cifras son ciertas, sólo si concuerdan. No se ha modificado
ningún archivo del proyecto.

**Estado leído: 9 de septiembre de 2026, 12:20.** Los archivos se reescribieron
en bloque a las 12:17–12:19 (paso de corrección `46 → 47 textos`,
`0,855 → 0,860`, `0,799 → 0,807`, `0,665 → 0,668`, `A2 0,5480 n=7 → 0,5561
n=8`). Todo lo que sigue está verificado **contra esa versión**. Los PDF se
recompilaron a las 12:19, así que los restos que quedan ya están impresos.

---

## Recuento

| Grupo | Hallazgos |
|---|---|
| **A. Una cifra corregida en unos sitios y no en otros** | **15** |
| **B. Salvedad presente en un archivo y ausente en otro** | **7** |
| **C. Estructura y referencias cruzadas** | **4** |
| **D. Frases rotas** | **3** |
| **E. Divergencias menores entre pares** | **6** |
| **Total** | **35** |

Los tres primeros (**A1, A3, A4**) son de la misma familia y son los graves: el
paso de corrección de las 12:18 tocó la prosa y las tablas pero **no tocó el
`.dat` que dibuja la figura, ni las etiquetas escritas a mano dentro de esa
figura, ni la tarjeta del modelo**. El resultado es que en el PDF ya publicado
hay **tres totales distintos del mismo corpus en la misma página**.

Verificado y **sin hallazgo**: `\ref`/`\label` en `documento.tex` (40
referencias, todas con etiqueta); los doce «Cuadro N» citados en
`documento.md` resuelven al cuadro que dicen; `notebook_proyecto.py` y
`notebook_proyecto.ipynb` son **idénticos celda a celda** (92 celdas); sin
párrafos duplicados; consistentes 59 · 1.197 · 61.642 · 654 · 144 · 4.724 ·
148 · 1.049 · 38 · 328 MB · 243 MB · 205 · 27 · 40 · 4,53 · 3,11 · 31 s ·
7 USD/mes · 0,908 · 97,2 % · 0,829.

---

# A. Una cifra corregida en unos sitios y no en otros

## A1 — El `.dat` que dibuja la figura de validación quedó en la versión vieja · **GRAVE**

La corrección de A2 llegó al cuadro pero no al fichero de datos del que se
dibuja la figura de al lado.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/datos_figuras/validacion.dat` | 3 | `A2 7 0.5480 0.237` |
| `entrega/documento.tex` | 1637 | `A2 & 8 & 0,5561 & 0,223 \\` |
| `entrega/documento.md` | 702 | `\| A2 \| 8 \| 0,5561 \| 0,223 \|` |

`documento.tex:1672` dibuja la figura **directamente de ese fichero**:

```
] table[x expr=\coordindex, y=media, y error=desv] {datos_figuras/validacion.dat};
```

y el pie del cuadro (`documento.tex:1645`) declara ese mismo fichero como
fuente: *«Fuente: `datos_figuras/validacion.dat`»*. Es decir: **la barra de A2
del PDF mide 0,5480 con desviación 0,237, justo debajo de una tabla que dice
0,5561 y 0,223**, y ambas se presentan como el mismo dato.

## A2 — El Resumen sigue describiendo el escalón A1–A2 con los números viejos · **GRAVE**

Primera página del entregable. La frase se apoya en la media y la desviación de
A2 anteriores a la corrección, y coincide con el `.dat` obsoleto de A1, no con
el Cuadro 10 que está veinte páginas después.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 44–45 | «el escalón A1–A2 es de **0,044** sobre desviaciones de 0,111 y **0,237**» |
| `entrega/documento.tex` | 250 | «el escalón A1--A2 es de **0,044** sobre desviaciones de 0,111 y **0,237**» |
| `entrega/documento.md` | 701–702 (Cuadro 10) | A1 media **0,5040** desv **0,111** · A2 media **0,5561** desv **0,223** |
| `entrega/datos_figuras/validacion.dat` | 3 | `A2 7 0.5480 **0.237**` (el valor viejo, ver A1) |

Con los valores del Cuadro 10, el escalón A1–A2 es **0,0521**, no 0,044, y la
desviación de A2 es **0,223**, no 0,237. Ambos números aparecen en la misma
frase que introduce el resultado principal del trabajo, y las dos versiones del
documento la traen igual.

## A3 — Las etiquetas `n` de esa misma figura suman 45, no 47 · **GRAVE**

Están escritas a mano dentro del TikZ y no se tocaron en ninguna de las dos
correcciones (`45 → 46` ni `46 → 47`).

`entrega/documento.tex:1678–1682`:

```
\node[...] at (axis cs:0,0.72) {n\,=\,3};
\node[...] at (axis cs:1,0.90) {n\,=\,7};     <- el cuadro dice 8
\node[...] at (axis cs:2,1.19) {n\,=\,12};
\node[...] at (axis cs:3,1.55) {n\,=\,11};    <- el cuadro dice 12
\node[...] at (axis cs:4,1.72) {n\,=\,12};
```

3 + 7 + 12 + 11 + 12 = **45**. En la misma doble página conviven **tres
totales**:

| Fuente | n por nivel | Total |
|---|---|---|
| Etiquetas de la figura (`documento.tex:1678–1682`) | 3 · 7 · 12 · **11** · 12 | **45** |
| `datos_figuras/validacion.dat` | 3 · **7** · 12 · 12 · 12 | **46** |
| Cuadro 10 (`documento.tex:1637`, `documento.md:702`) y todo el resto del texto | 3 · **8** · 12 · 12 · 12 | **47** |

## A4 — `modelo_v4/README.md` conserva dos medias viejas · **GRAVE**

En el mismo archivo, las líneas 91–92 **sí** recibieron la corrección
(`0,807` / `0,860`), pero la tabla de medias por nivel no.

| Archivo | Línea | Dice |
|---|---|---|
| `modelo_v4/README.md` | 78 | `\| **Media (0–2)** \| 0,504 \| **0,548** \| 0,928 \| **1,248** \| 1,495 \|` |
| `entrega/presentacion.tex` | 235–236 | `A1 0,504 · A2 **0,556** · B1 0,928 · B2 **1,241** · C1 1,495` |
| `PENDIENTES.md` | 76 | `0,5040 · **0,5561** · 0,9276 · **1,2414** · 1,4952` |

`1,248` es además el redondeo del valor **anterior al anterior** (`1,2478`, hoy
`1,2414`): esa celda lleva dos correcciones de retraso.

## A5 — «0,548» sobrevive en la prosa del cuadernillo

El array de código del cuadernillo sí se actualizó
(`notebook_proyecto.py:1702`: `[0.5040, 0.5561, ...]`), pero la prosa que lo
comenta, no. Está igual en el `.ipynb`.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 1751 | «**A1 y A2 casi no se distinguen** (0,504 frente a **0,548**)» |
| `entrega/notebook_proyecto.py` | 1982 | «A1 y A2 son prácticamente indistinguibles (0,504 frente a **0,548**, con n = 3 en A1)» |
| `entrega/notebook_proyecto.py` | 1702 | `"Media v4 (escala 0-2)": [0.5040, **0.5561**, 0.9276, 1.2414, 1.4952]` |

## A6 — El último «46» del documento

Único resto del valor anterior en los dos archivos del Grupo 1, y en la misma
frase de los dos.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 748 | «…y una parte de esos **46** son textos que la app rechazaría por parecer listas.» |
| `entrega/documento.tex` | 1741 | «…y una parte de esos **46** son textos que la app rechazaría por parecer listas.» |
| `entrega/documento.md` | 729 · 731 · 769 · 776 | `**Evaluados** \| **47**` · «De 59 a **47**» · «(**47** textos)» · «los mismos **47** textos» |

## A7 — La flecha de la figura de compresión apunta al valor viejo

Dentro de la misma figura, el punto se actualizó y la anotación no.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.tex` | 1840 | `coordinates {(0.0,0.5040) (0.4,**0.5561**) (0.8,0.9276) ...}` |
| `entrega/documento.tex` | 1851 | `(axis cs:0.4,0.40) -- (axis cs:0.4,**0.548**);` |
| `entrega/documento.tex` | 1844 | etiqueta «A2» colocada en `axis cs:0.42,**0.545**` |

## A8 — 552 contra 553 palabras del guion

Dentro del mismo archivo, y contra los dos guiones.

| Archivo | Línea | Dice |
|---|---|---|
| `PENDIENTES.md` | 26 | «El guion está escrito, cronometrado (**552** palabras, 3:41)» |
| `PENDIENTES.md` | 87 | `\| Palabras habladas del guion \| **553** (las que van entre comillas) = 3:41 \|` |
| `entrega/guion_video.md` | 10 | «El texto hablado son **553** palabras» |
| `entrega/guion_video.tex` | 145 | «Texto hablado: **553 palabras**» |

## A9 — 562 MB contra 571 MB

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 1918 | «…pico realista de 1,2-1,5 GB, y **562 MB** en disco» |
| `DESPLIEGUE.md` | 15 | «Los **571 MB** de datos **no van en el repositorio**» |
| `DESPLIEGUE.md` | 87 | «los **571 MB** van en un Volume» |
| `PENDIENTES.md` | 89 | `\| Modelo + diccionario \| **571 MB** \|` |

328 + 243 = 571. El mismo cuadernillo cita 328 MB (`:1423`) y 243 MB (`:57`).

## A10 — 2,8 h contra «entre 3 y 5 h» de A100

| Archivo | Línea | Dice |
|---|---|---|
| `PENDIENTES.md` | 47 | `\| Coste real del catálogo \| **2,8 h** de cómputo A100; ~17 h de extremo a extremo \|` |
| `entrega/documento.md` | 58 | «son entre **tres y cinco** horas de cómputo» |
| `entrega/documento.tex` | 803 | «Entre **3 y 5 h** de A100, dentro del crédito disponible» |
| `entrega/estrategia.md` | 273 · 365 | «entre **tres y cinco** horas de una GPU A100» |
| `entrega/presentacion.tex` | 337 | «$\approx$**3--5 h** de cómputo A100, *estimadas*» |

## A11 — Ocho pestañas contra siete

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 53 | «una aplicación funcionando —**ocho pestañas** en Gradio 6.26» |
| `entrega/documento.tex` | 258 | «una aplicación funcionando —**ocho pestañas** en Gradio 6.26» |
| `README.md` | 131 | `\| app/ui.py \| La interfaz: **siete pestañas** en Gradio 6 \|` |

## A12 — Cientos de millones contra 1.500 millones

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 67 | «**Cientos de millones** de personas estudian inglés como segunda lengua.» |
| `entrega/documento.tex` | 290 | «**Cientos de millones** de personas estudian inglés como segunda lengua.» |
| `entrega/guion_video.md` | 77 | «**1.500 millones** de personas estudian inglés» |
| `entrega/guion_video.tex` | 243 | «**1.500 millones** de personas estudian inglés» |
| `entrega/notebook_proyecto.py` | 142 | «Alrededor de **mil quinientos millones** de personas estudian inglés» |

Un orden de magnitud de diferencia, y la cifra grande es la que se dice a
cámara en el segundo 35 del vídeo.

## A13 — Tres preguntas contra seis

`README.md` funde las seis preguntas y los tres fragmentos en un solo número.

| Archivo | Línea | Dice |
|---|---|---|
| `README.md` | 21 | «**Sitúa al lector.** **Tres preguntas**, o midiendo un texto que ya lee cómodo.» |
| `entrega/documento.md` | 846 | «**Seis preguntas** sobre hábitos observables y **tres fragmentos** reales en escalera» |
| `entrega/documento.tex` | 548 · 1939 · 1967 | «**Seis preguntas**…» · «**6 preguntas**\\+ 3 fragmentos» |
| `entrega/estrategia.md` | 49 | «**Seis preguntas** sobre hábitos observables» |
| `entrega/guion_video.md` | 100 | «Contesto **seis preguntas** sobre cómo leo y leo **tres fragmentos** reales.» |
| `entrega/guion_video.tex` | 271 | «Contesto **seis preguntas**… y leo **tres fragmentos**» |

## A14 — El README titula con las medias de Colab, no con las locales

| Archivo | Línea | Dice |
|---|---|---|
| `README.md` | 83–84 | «**en corpus externo las medias por nivel quedan estrictamente ordenadas**: A2 **0.648** < B1 **0.951** < B2 **1.288** < C1 **1.495**.» |
| `README.md` | 106–109 (su propia tabla) | media local A2 **0.5561**, B1 **0.9276**, B2 **1.2414** — la columna «Colab» es la de 0.6479 / 0.9513 / 1.2883 |
| `entrega/documento.md` | 1149 | «(0,5040 · **0,5561** · 0,9276 · 1,2414 · 1,4952)» |

El titular del README son cuatro medias de la tanda de Colab presentadas sin
decir de qué tanda salen, y sin A1. El resto de la entrega titula con las cinco
locales.

## A15 — 9 $ contra 7 USD/mes

| Archivo | Línea | Dice |
|---|---|---|
| `DESPLIEGUE.md` | 30 | «## Opción A — Hugging Face PRO, **9 $ un mes**» |
| `DESPLIEGUE.md` | 81 | «Viable si los **9 $** son un problema real.» |
| `entrega/documento.tex` | 801 | «**7 USD/mes**: … Pro (**9 USD de tarifa, 7 con descuento**)» |
| `entrega/estrategia.md` | 364 | «**7 USD/mes**: … (9 USD de tarifa, 7 con descuento)» |
| `PENDIENTES.md` | 88 | «**7 USD/mes** (cuenta Pro; tarifa 9, con descuento)» |

---

# B. Salvedad presente en un archivo y ausente en otro

## B1 — `DESPLIEGUE.md` sigue escrito como si el despliegue no hubiera ocurrido · **GRAVE**

| Archivo | Línea | Dice |
|---|---|---|
| `DESPLIEGUE.md` | 3–4 | «Todo lo que sigue está **preparado y verificado en local**. **Lo único que falta es elegir plataforma y ejecutar**.» |
| `DESPLIEGUE.md` | 114 | «Así que **si se despliega**, hay que montar almacenamiento.» |
| `README.md` | 7 | «**Está desplegada y funcionando**» |
| `entrega/documento.tex` | 801 · 840 | «**HECHO**: `MikeMaki1763/literalevel`, público y en marcha» |
| `entrega/estrategia.md` | 364 · 392 | «**HECHO**: … público y en marcha» |
| `PENDIENTES.md` | 28 | «~~Despliegue permanente~~ \| **HECHO**» |

El archivo entero presenta tres opciones A/B/C como decisión abierta; la
decisión está tomada y ejecutada (opción A).

## B2 — El cuadernillo dice que el enlace es temporal

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 1917 (ídem `.ipynb`) | «**Despliegue permanente de la interfaz.** El enlace actual **es temporal y muere al apagar la computadora**.» |
| `entrega/documento.tex` | 801 | «El enlace **anterior** era un túnel temporal… **HECHO**» |

## B3 — «Tres horas de nube», sin horquilla y sin «estimadas»

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 1912 | «**Ejecutar el precálculo del catálogo en A100.** **Tres horas de nube** convierten 61.642 libros sin medir en 61.642 libros medidos» |
| `entrega/presentacion.tex` | 337 | «$\approx$**3--5 h** de cómputo A100, ***estimadas***» |
| `entrega/documento.md` | 943–944 | «son entre **3 y 5 horas** de A100, y **conviene decir de qué depende esa horquilla en vez de dar una cifra sola**» |

El propio documento dice explícitamente que no se dé una cifra sola; el
cuadernillo da una cifra sola.

## B4 — La tarjeta del modelo publica 0,908 y 97,2 % sin la salvedad

`modelo_v4/README.md:69` da `144 | 53,5 % | 97,2 % | 0,908` y **en ningún punto
del archivo** dice que esas 144 parejas no están publicadas. Es el único
artefacto público del proyecto que omite esa nota.

| Archivo | Línea | Salvedad |
|---|---|---|
| `entrega/documento.md` | 1079 · 1086 | «no son verificables clonando el proyecto» |
| `entrega/presentacion.tex` | 230 | «las **144 parejas** de etiqueta y predicción **no están publicadas**» |
| `README.md` | 182–185 | «**no son verificables desde este repositorio**» |
| `entrega/notebook_proyecto.py` | 1989 | «**no son verificables desde el repositorio**» |
| `modelo_v4/README.md` | 69 | *(nada)* |

## B5 — La tarjeta del modelo mezcla el 0,860 y el 0,829 sin distinguir conjuntos

| Archivo | Línea | Dice |
|---|---|---|
| `modelo_v4/README.md` | 70 | `\| British Council, externo \| **38** \| 50,0 % \| 100 % \| **0,829** \|` |
| `modelo_v4/README.md` | 92 | «en el corpus de British Council, donde **este modelo da 0,860**» |
| `entrega/documento.md` | 1150 | «alcanza Spearman **0,829 con 38 textos**, **0,860 con los 47**» |

En la tarjeta, dos cifras del «corpus de British Council» a 22 líneas de
distancia, sin decir que son dos conjuntos distintos.

## B6 — La presentación da por «Hecho» un accionable que está hecho a medias

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/presentacion.tex` | 333–334 | «**Publicar el modelo** \| 30 min, gratis \| **Hecho**: el cuaderno corre en un Colab limpio» |
| `entrega/documento.tex` | 799 | «**Publicar el modelo y el diccionario**… **HECHO a medias**: … **el diccionario (243 MB) sigue sin publicar**» |
| `entrega/estrategia.md` | 363 | «**HECHO a medias**: … El diccionario (243 MB) sigue sin publicar» |
| `PENDIENTES.md` | 97 | «**Publicar el diccionario Kaikki** (243 MB). … la mitad que falta del accionable A1.» |

La diapositiva resuelve el desajuste recortando el enunciado del accionable
(«Publicar el modelo» en vez de «el modelo y el diccionario»).

## B7 — La presentación da el despliegue sin sus dos salvedades

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/presentacion.tex` | 335–336 | «Desplegar de forma permanente \| 7 USD/mes \| **Hecho**: dirección fija que no muere al apagar» |
| `entrega/documento.md` | 1099 · 1106–1108 | «ese hardware **suspende el servicio tras 48 h sin visitas**» · «**no da almacenamiento persistente**» |
| `entrega/documento.tex` | 840 | «**Sin disco persistente todavía (A4)**» |
| `entrega/documento.tex` | 2570 | «sobre el hardware más barato: **se suspende por inactividad y no guarda nada** entre reinicios» |

---

# C. Estructura y referencias cruzadas

## C1 — `documento.md` y `documento.tex` discrepan sobre dónde vive la Estrategia · **GRAVE**

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 9–11 | «La sección **Estrategia** de este trabajo **se entrega en un documento aparte**, `estrategia.md`, por su extensión. En este documento **se resume** en el apartado 3 y **se remite allí** para el desarrollo completo.» |
| `entrega/documento.tex` | 270–273 | «La *Estrategia* … **se desarrolla completa en el apartado 3** y **no en un anexo**: ocupa el lugar que le corresponde en el orden de secciones» |
| `PENDIENTES.md` | 58 | «**Estrategia** (`entrega/estrategia.md`, **absorbida en el `.tex`**)» |

Los dos archivos del Grupo 1 declaran cosas opuestas en su primera página. Y el
`.tex` se contradice consigo mismo: `documento.tex:2291` dice «**La versión
larga está en el documento de estrategia**».

Consecuencia medible: el `.md` §3 son **28 líneas de resumen** (líneas 176–203)
y el `.tex` §3 son **361 líneas** (510–870). Cifras que existen sólo en el
`.tex` y no tienen ningún equivalente en el `.md`: **205 pruebas** (679, 753,
839), **27 pasos** (839), **cuarenta parejas de color** (667, 838), **4,53 y
3,11** (667, 838), **11,3 GB** (803), **1,27 sobre 2** (2291 y estrategia.md).

## C2 — El criterio C3 apunta a sitios distintos

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 172–173 | «Las tres se cumplen y se documentan, respectivamente, en 7.4, 7.5 y **en el documento de estrategia**.» |
| `entrega/documento.tex` | 504–505 | «Se cumplen y se documentan, respectivamente, en los apartados \ref{sec:validacion}, \ref{sec:baseline} y **\ref{sec:esmeralda}**» (§3.3 del propio `.tex`) |

## C3 — Dos archivos citan cuadros del «documento principal» por la numeración del `.md`

La cabecera del `.md` (líneas 13–16) declara que su numeración y la del PDF no
coinciden y que **«las referencias internas de cada archivo apuntan a su propia
numeración»**. Pero estas dos citas son *externas*, van al «documento
principal», que es el PDF:

| Archivo | Línea | Cita | En el `.md` es | En el PDF es |
|---|---|---|---|---|
| `entrega/estrategia.md` | 182 | «**Cuadro 15 del documento principal**: 8,19 ventanas/s en CPU…» | Cuadro 15 ✓ | **Cuadro 20** |
| `README.md` | 119 | «las tres cifras del **Cuadro 12**(modelo 0,860…)» | Cuadro 12 ✓ | **Cuadro 17** |

(Numeración del PDF contada sobre los 21 `\caption` de entorno `table` de
`documento.tex`.)

## C4 — El resumen de accionables del `.md` describe una tabla que no existe

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 201–203 | «**Accionables.** Diez, con **responsable**, coste y criterio de terminado; **los tres primeros** son publicar modelo y diccionario, desplegar en enlace permanente y **terminar la remedición del catálogo**.» |
| `entrega/documento.tex` | 786–790 | Columnas de la tabla: `#` · `Acción` · `Por qué` · `Coste` · `Terminado cuando` — **no hay columna de responsable** |
| `entrega/estrategia.md` | 361 | Mismas cinco columnas, sin responsable |
| `entrega/documento.tex` | 822–823 | «Orden de ejecución si el tiempo aprieta: A1 → A2 → **A5** → A3 → A4. **Los tres primeros** son … despliegue, publicación y **un micrófono**.» |
| `entrega/estrategia.md` | 376–379 | Idéntico: los tres primeros son A1, A2 y **A5** |

«Los tres primeros» nombra A1/A2/A3 en el `.md` y A1/A2/A5 en los otros dos.

---

# D. Frases rotas

## D1 — Edición a medias en `documento.tex`

`entrega/documento.tex:1736–1737`:

> «Se conserva la unión con espacio porque es la que reproduce **las**
> el cuadro~\ref{cuad:validacion} de este documento…»

Sobra «las», resto de la sustitución de «las cifras de» / «el Cuadro 10». El
`.md` (línea 743) lee bien: «porque es la que reproduce **el Cuadro 10** de este
documento».

## D2 — «Los cuatro escalones siguientes» cuando sólo quedan tres

Con cinco niveles hay **cuatro** escalones (A1–A2, A2–B1, B1–B2, B2–C1).
Descontado el A1–A2, quedan **tres**.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 44–46 | «el escalón A1–A2 … descansa en tres textos. Está dentro del ruido. **Los cuatro escalones siguientes, no.**» |
| `entrega/documento.tex` | 250–251 | «…Está dentro del ruido. **Los cuatro escalones siguientes, no.**» |
| `entrega/presentacion.tex` | 241–242 | «El escalón A1--A2 descansa en 3 textos y está dentro del ruido; **los otros cuatro**, no.» |

Los tres archivos concuerdan entre sí, pero los tres cuentan mal.

## D3 — `DESPLIEGUE.md` termina en un encabezado duplicado y vacío

| Línea | Contenido |
|---|---|
| 92 | `## Lo que ya no hace falta resolver` |
| 99 | último elemento de la lista de esa sección |
| 100 | `## Persistencia: ahora importa más que antes` ← **sin línea en blanco antes; no se renderiza como encabezado** |
| 122 | `## Lo que ya no hace falta resolver (continuación)` ← **última línea del archivo, sin cuerpo** |

---

# E. Divergencias menores entre pares

## E1 — El guion pierde «estrictamente» al pasar a `.tex`

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/guion_video.md` | 120–121 | «orden MCER **estrictamente creciente** en textos externos» |
| `entrega/guion_video.tex` | 296 | «orden MCER **creciente** en textos externos» |

Es la diapositiva de métricas desnudas. El texto hablado sí dice
«estrictamente creciente» en los dos (`md:125`, `tex:302`).

## E2 — Atribución de ANSVA sólo en el `.tex`

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/guion_video.md` | 20 | «el método **ANSVA** de Fernando Miralles, que es la secuencia clásica de persuasión» |
| `entrega/guion_video.tex` | 158 | «el método **ANSVA** de Fernando Miralles, **campeón de España de oratoria**» |

## E3 — Instrucción de chat dentro del guion `.md`

`entrega/guion_video.md:30–31`, dentro de la «Nota honesta sobre las fuentes»:

> «**Si tienes el libro y quieres que el guion se reescriba sobre esa
> estructura, dímelo y lo rehago.**»

No tiene equivalente en `guion_video.tex:174–177`, que además amplía la nota
(«la *estructura de la sardina*, **y PAS, y ADP**») y elimina la frase. El
`.md` menciona sólo la sardina.

## E4 — El recorrido de ejemplo usa un lector distinto en cada sitio

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 856 | «un lector cuyo perfil da **1,20 sobre 2** (banda intermedia, ancla B2)» — 6 pasos, *Notes from a Dead House* |
| `entrega/presentacion.tex` | 249 · 260 · 276 | «una lectora de 15 años que el sistema sitúa en **0,93**» — 5 pasos, *Sherlock Holmes*, palabra *peculiar* |

Misma sección («Un recorrido completo» / «Ejemplo de uso y aplicación»), dos
recorridos con números distintos. La diapositiva no es trazable al documento.

## E5 — Qué nivel se anuncia como cuál

| Archivo | Línea | Dice |
|---|---|---|
| `README.md` | 87–88 | «así que un texto **A2** suele puntuar cerca de **B1**» |
| `entrega/documento.tex` | 811 | «un **A2** puntúa cerca de **B1**» |
| `entrega/estrategia.md` | 369 | «un **A2** puntúa cerca de **B1**» |
| `modelo_v4/README.md` | 85–86 | «un texto **A1** tiende a anunciarse como **A2**» |
| `PENDIENTES.md` | 95 | «Un texto **A1** se anuncia como **A2**.» |

## E6 — La divulgación de parentesco se cae en el `.tex`

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 53–54 | «probada por una lectora de quince años, **prima del autor** y ajena al proyecto» |
| `entrega/documento.tex` | 258–259 | «probada por una lectora de quince años **ajena al proyecto**» |

En el Resumen del `.tex` desaparece «prima del autor». Sí se declara más
adelante (`documento.tex:621`), así que el efecto es sólo de resumen.
