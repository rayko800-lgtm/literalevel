# Confirmación de coherencia entre entregables

Segundo barrido de **desajustes entre archivos que deberían decir lo mismo**,
rehecho sobre el estado posterior a la reestructuración editorial (`afd000f` y
`f36cffe`). No se comprueba si las cifras son ciertas, sólo si concuerdan. **No
se ha modificado ningún archivo del proyecto**; lo único escrito es este
informe.

**Estado leído: 9 de septiembre de 2026, 14:20.** Árbol limpio (`git status`
sin cambios), `HEAD` en `f36cffe`. Los tres PDF son posteriores a sus fuentes
(`documento.pdf` 14:07 sobre `.tex` 14:06; `presentacion.pdf` 14:02 sobre
`.tex` 13:51; `guion_video.pdf` 14:02 sobre `.tex` 14:01), así que **todo lo
que sigue ya está impreso**.

Método: `grep` sobre los doce archivos del contrato, más comparación
normalizada frase a frase entre `documento.md` y `documento.tex` (562 frases
contra 602), regeneración de `notebook_proyecto.ipynb` desde el `.py` para
diferencia celda a celda, recuento del guion con `tools/contar_guion.py`,
recálculo de los `.dat` con `awk` contra los números escritos a mano en los
`tikzpicture`, y resolución **una por una** de las citas «Cuadro N» en prosa
contra la numeración real del `.md` (17 cuadros) y del PDF (22 cuadros,
contados sobre los `\caption` de entorno tabular de `documento.tex`).

---

## Recuento

| Grupo | Hallazgos |
|---|---|
| **A. Graves** | **4** |
| **B. Medios** | **7** |
| **C. Menores** | **10** |
| **Total** | **21** |

**Lo que la reestructuración sí arregló**, comprobado uno por uno: las etiquetas
`n` del TikZ de validación ya suman 47 (3+8+12+12+12); `validacion.dat` trae
`A2 8 0.5561 0.223`; el Resumen de los dos archivos dice 0,052 y 0,223 y **«los
tres escalones siguientes, no»** —igual que la diapositiva 7, que dice «los
otros tres»—; la flecha de la figura de compresión apunta a 0,556;
`modelo_v4/README.md` ya publica 0,556 y 1,241 y trae la salvedad de las 144
parejas; no queda ningún «46» ni ningún «45» sueltos; `documento.tex:1736` ya no
arrastra el «las» huérfano; «una versión anterior» son exactamente **dos** en
cada archivo y en los mismos dos sitios; los cuadros del `.md` van de 1 a 17 sin
huecos; `documento.md` y `documento.tex` tienen las mismas 14 limitaciones en el
mismo orden y la «limitación 6» que cita el Resumen es la que dice ser; el §7.7
es idéntico en los dos archivos; y `DESPLIEGUE.md` ya no está escrito como si el
despliegue no hubiera ocurrido.

**Verificado y sin hallazgo**: el caso de uso, dato por dato, en los cuatro
sitios (perfil 1,20 · «dostoyevski» mal escrito · *Notes from a Dead House* ·
130.104 palabras · 487 ventanas · 86 s · media 1,73 · 40 ms), incluida la
diapositiva 8, que es efectivamente la octava de las doce.
`notebook_proyecto.py` y `.ipynb` son **idénticos celda a celda** (92 celdas, 39
de texto y 53 de código; regenerado el `.ipynb` desde el `.py` con
`tools/a_notebook.py`, cero diferencias). Los `.dat` de curvas cuadran con lo
dibujado hasta el último decimal (*War and Peace*: media 1,7346 → 1,735
dibujado, mínimo 1,333 en el capítulo 34, máximo 1,990 en el 202, rango 0,657;
*Crime and Punishment* 1,6793 y 1,270–1,891; *Alice* 1,4967 y 1,296–1,878).
`velocidad.dat` cuadra con el Cuadro 16 y con las tres etiquetas escritas a mano
(8,19 · 112,7 · 2.022, y los factores 13,8× y 247×). El manifiesto cierra la
aritmética del corpus: 12+10+13+12+12 = 59, y 59 − 2 − 10 = 47 con reparto
3/8/12/12/12. Consistentes en todas sus formas y con los dos separadores
decimales: 47 · 0,5561 · 1,2414 · 0,860 · 0,807 · 0,668 · 0,732 · 31 · 205 · 27
· 40 parejas · 4,53 · 3,11 · 328 MB · 243 MB · 31 s · 7 USD/mes · 0,908 · 97,2 %
· 654 · 510 · 144 · 38 · 59 · 61.642 · 1.197 · 148 · 1.049 · 0,517 · 0,725 ·
0,89 · 48 h.

---

# A. Graves

## A1 — La figura de la escala dibuja los cortes de banda **viejos**, y el texto dice que los dibuja bien · **GRAVE**

Es lo dibujado contra lo escrito, en el mismo documento y a dos páginas de
distancia. `app/scoring.py` agrupa las bandas por ancla MCER (básico = A1/A2,
intermedio = B1/B2, avanzado = C1/C2), lo que sitúa los cortes en **0,6 y 1,4**;
el propio `.md` cuenta que **antes estaban en 0,8 y 1,6** y que eso fue un
error corregido. La figura sigue dibujando 0,8 y 1,6.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.tex` | 427–429 | `\fill[llverde!12] (0,-0.32) rectangle (0.8,0.32);` · `\fill[llambar!14] (0.8,...) rectangle (1.6,...);` · `\fill[llrojo!12] (1.6,...) rectangle (2.0,...)` — y las llaves de `\draw[decorate...brace]`, en **453–455**, reparten igual: **0–0,8 / 0,8–1,6 / 1,6–2,0** |
| `entrega/documento.tex` | 730–732 | «La interfaz muestra **bandas** —básico $< 0{,}6 \leq$ intermedio $< 1{,}4 \leq$ avanzado, **tal como las dibuja la figura~\ref{fig:escala}**—» |
| `entrega/documento.md` | 814–815 | «la interfaz muestra **bandas** (básico < **0,6** ≤ intermedio < **1,4** ≤ avanzado)» |
| `entrega/documento.md` | 818–819 | «Al principio estaban en **0,8 y 1,6**, que además **ni siquiera partían el 0–2 en tres partes iguales**» |
| `entrega/estrategia.md` | 198 | «básico < **0,6** ≤ intermedio < **1,4** ≤ avanzado, que son los cortes…» |
| `app/scoring.py` | 105–137 | «Antes eran **0,8 y 1,6**… Ahora la banda se deriva del ancla MCER» |

El pie de la figura remite además a `datos_figuras/escala_cefr.dat` como fuente.
Ese `.dat` **sí** está bien y las marcas grises de letra MCER (0,20 · 0,60 ·
1,00 · 1,40 · 1,80) lo respetan; lo que no sale del `.dat` son las tres bandas
de producto, escritas a mano con los valores derogados.

**Y el mismo error aparece en la otra figura**, contradiciéndose a sí misma
dentro del bloque:

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.tex` | 2172 | `% banda "avanzado" (>= 1,6)` |
| `entrega/documento.tex` | 2174 | `\addplot[...] coordinates {(0,1.6) (366,1.6)};` ← la banda sombreada arranca en **1,6** |
| `entrega/documento.tex` | 2204 | `{banda «avanzado» ($\geq 1{,}4$)}` ← la etiqueta de esa misma banda dice **1,4** |

## A2 — La renumeración de cuadros dejó tres citas externas apuntando al cuadro equivocado · **GRAVE**

El Cuadro de conjuntos, nuevo, entra como **Cuadro 9** del `.md` y **Cuadro 14**
del PDF, y empuja a todos los siguientes. Comprobado contra `afd000f`: antes de
`f36cffe` el cuadro de velocidad era el **20** del PDF y el **15** del `.md`, y
el del *baseline* el **17** del PDF y el **12** del `.md`. Hoy son el 21/16 y el
18/13. Las tres citas escritas a mano fuera de `documento.md` no se movieron.

| Archivo | Línea | Dice | Debería decir |
|---|---|---|---|
| `entrega/estrategia.md` | 182 | «**Cuadro 20 del PDF —el 15 de la copia de lectura—**: 8,19 ventanas/s en CPU, 112,7 en la GPU local…» | Cuadro **21** del PDF, **16** de la copia de lectura |
| `README.md` | 120 | «El guion imprime además las tres cifras del **Cuadro 12** (modelo 0,860, contar palabras 0,807, parcial descontando la longitud 0,668)» | **Cuadro 13** del `.md` (18 del PDF) |
| `PENDIENTES.md` | 77 | `\| **Cuadro 12** (baseline) \| **0,860 / 0,807 / 0,668** \| validar_local.py \|` | **Cuadro 13** |

Y lo que imprime el guion que las tres citan, que es lo que va a ver el
profesor en pantalla:

| Archivo | Línea | Dice |
|---|---|---|
| `validar_local.py` | 201 | `print("Cuadro 12 - el modelo frente a la senal trivial "` ← salida visible |
| `validar_local.py` | 147 | `# --- Cuadro 12 del documento: el modelo frente a la senal trivial ---` |
| `validar_local.py` | 127 | `# Para el baseline del Cuadro 12 hace falta ademas la longitud.` |
| `validar_local.py` | 50 | `# Se conserva el espacio porque es lo que reproduce el Cuadro 10 del` ← hoy es el **Cuadro 11** |
| `AGENTS.md` | 14 | «`validar_local.py` (el regex del nivel, **el bloque del Cuadro 12**…)» ← hoy es el 13 |

*(Comprobado además que la nota de `.claude/skills/latex-en-esta-maquina/SKILL.md:127`
—«"Cuadro 11" del `.md` es "Cuadro 16" del PDF»— sigue siendo cierta por
casualidad: `.md` 11 = PDF 16. No hay hallazgo ahí.)*

## A3 — El recuento del guion bajó a `PENDIENTES.md` en la versión de antes de `afd000f` · **GRAVE**

`afd000f` introdujo `tools/contar_guion.py`, que trae la regla ejecutable y da
**561 palabras, 3:44**. Ejecutado ahora: 6 bloques de parlamento, 64 + 77 + 213
+ 79 + 90 + 44 = **561**. Los dos guiones lo recogen; el archivo que lo
inventaria, no.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/guion_video.md` | 10 | «El texto hablado son **561 palabras** y son **3:44** a 150 palabras por minuto.» |
| `entrega/guion_video.tex` | 145–146 | «Texto hablado: **561 palabras** = **3:44** a ritmo normal.» |
| `PENDIENTES.md` | 26 | «El guion está escrito, cronometrado (**553 palabras, 3:41**) y compilado en PDF» |
| `PENDIENTES.md` | 87 | `\| Palabras habladas del guion \| **553** (las que van entre comillas) = **3:41** \| entrega/guion_video.md \|` |

La segunda fila es peor que la primera: la tabla se titula «Cifras vigentes,
para no volver a publicar las viejas» y su columna «Con qué se comprueba» remite
a `entrega/guion_video.md`, que dice otra cosa.

## A4 — `documento.md:472` cita el Cuadro 7 para los números que están en el Cuadro 8 · **GRAVE**

No lo causó la renumeración —los cuadros 7 y 8 no se movieron— pero es una cita
en prosa que no resuelve, y el `.tex` demuestra cuál es la correcta porque usa
`\ref`.

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 468–472 | «La comparación por subconjuntos de CLEAR (literario frente a informativo, y por banda Lexile)… Los números están en el **Cuadro 7**.» |
| `entrega/documento.tex` | 1200–1204 | Mismo párrafo, palabra por palabra, y termina en «Los números están en el cuadro~**\ref{cuad:dominio}**» |
| `entrega/documento.md` | 571 | *Cuadro 7.* **Progresión de modelos** sobre los mismos 950 extractos reservados |
| `entrega/documento.md` | 621 | *Cuadro 8.* **Matriz modelo × dominio** — Literatura 0,848 · Informativo 0,905 · Lexile 500 0,651 · Lexile 1300 0,877 |

`cuad:dominio` es el Cuadro 8 del `.md`. Los cuatro valores que el párrafo
describe están en el 8; el 7 no tiene ni filas por dominio ni bandas Lexile.

---

# B. Medios

## B1 — 571 MB contra 575 MB, y una suma que no cierra

`DESPLIEGUE.md` y el cuadernillo ya recibieron la corrección a 575; `PENDIENTES.md`
no. Y dentro del propio `DESPLIEGUE.md` la tabla no suma lo que el texto dice.

| Archivo | Línea | Dice |
|---|---|---|
| `PENDIENTES.md` | 89 | `\| Modelo + diccionario \| **571 MB** \| os.path.getsize \|` |
| `DESPLIEGUE.md` | 20 · 92 | «Los **575 MB** de datos no van en el repositorio» · «los **575 MB** van en un Volume» |
| `AGENTS.md` | 92 · 113 | «En disco, **575 MB** (modelo **332** con su tokenizador + diccionario 243 + CSV 0,9)» |
| `entrega/notebook_proyecto.py` | 1922 | «**575 MB** en disco» |
| `DESPLIEGUE.md` | 15–18 (su propia tabla) | código ~120 KB + CSV **1 MB** + `modelo_v4/` **328 MB** + `kaikki` **243 MB** = **572**, no 575 |

Medido ahora en disco: `model.safetensors` 328,5 MB, carpeta `modelo_v4/`
completa 332,1 MB, `kaikki_diccionario.db` 243,4 MB, CSV 0,87 MB. `AGENTS.md`
es el único que distingue las dos cifras del modelo; los demás usan 328 para la
carpeta entera y luego la suman como si fuera 332.

## B2 — La tarjeta pública sigue llamando «British Council» a dos conjuntos distintos, que es justo lo que el Cuadro 9 nuevo prohíbe

El Cuadro 9 se añadió en `f36cffe` para decir explícitamente que los 38 y los 47
son tandas distintas. `modelo_v4/README.md` es el único artefacto público del
proyecto y no recogió el criterio.

| Archivo | Línea | Dice |
|---|---|---|
| `modelo_v4/README.md` | 70 | `\| British Council, externo \| **38** \| 50,0 % \| 100 % \| **0,829** \|` |
| `modelo_v4/README.md` | 98–100 | «Contar palabras sin modelo alguno alcanza 0,807 **en el corpus de British Council, donde este modelo da 0,860**» |
| `entrega/documento.md` | 672 (Cuadro 9) | «**Qué no se puede hacer con él**: Restarlo de los 47. Es otra tanda, con otra extracción y otro filtro» |
| `entrega/documento.md` | 1214–1215 | «alcanza Spearman **0,829 con 38 textos**, **0,860 con los 47**» |

Y una consecuencia concreta en el mismo archivo:

| Archivo | Línea | Dice |
|---|---|---|
| `modelo_v4/README.md` | 72–77 | «Lo que sí es reproducible es **la fila de British Council**: los nombres de los 59 archivos están en el repositorio del proyecto y `validar_local.py` los vuelve a medir.» |

La fila de British Council de esa tabla es la de **38 textos y 0,829**.
`validar_local.py` no reproduce esa fila: reproduce la de **47 textos y 0,860**,
que en esa tarjeta no aparece en ninguna tabla.

## B3 — El titular del `README.md` son las cuatro medias de Colab, sin decir de qué tanda salen

| Archivo | Línea | Dice |
|---|---|---|
| `README.md` | 83–85 | «**en corpus externo las medias por nivel quedan estrictamente ordenadas**: A2 **0.648** < B1 **0.951** < B2 **1.288** < C1 **1.495**.» |
| `README.md` | 104–110 (su propia tabla, veinte líneas más abajo) | media **local** A2 0.5561 · B1 0.9276 · B2 1.2414; la columna «Colab» es la de 0.6479 / 0.9513 / 1.2883 |
| `entrega/documento.md` | 725 | «de A1 a C1 —**0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952**—» |
| `entrega/documento.tex` | 834 · `entrega/estrategia.md` 387 | «**Cumplido**: 0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952» |

Son cuatro medias de otra tanda, sin A1 y sin etiqueta, presentadas como el
resultado principal. El resto de la entrega titula con las cinco locales.

## B4 — El cuadernillo pide como accionable pendiente algo que él mismo declara hecho veinte pantallas antes

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 45–46 (ídem `.ipynb`) | «**El modelo v4 está publicado** en Hugging Face, en un repositorio público: `MikeMaki1763/literalevel-v4`.» |
| `entrega/notebook_proyecto.py` | 1907–1911 | «**1. Publicar el modelo v4 y el diccionario en Hugging Face.** Es media hora de trabajo y desbloquea la reproducibilidad completa de este cuadernillo, **que hoy es su única carencia**.» |
| `entrega/documento.tex` | 798 · `entrega/estrategia.md` 363 | «**HECHO a medias**: el modelo está en `MikeMaki1763/literalevel-v4`…; **el diccionario (243 MB) sigue sin publicar**» |

## B5 — «Tres horas de nube», cifra sola, cuando el documento dice explícitamente que no se dé una cifra sola

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/notebook_proyecto.py` | 1912–1913 | «**Ejecutar el precálculo del catálogo en A100.** **Tres horas de nube** convierten 61.642 libros sin medir en 61.642 libros medidos» |
| `entrega/presentacion.tex` | 341 | «$\approx$**3--5 h** de cómputo A100, ***estimadas***» |
| `entrega/documento.md` | 58 · `entrega/documento.tex` 803 | «son entre **tres y cinco** horas de cómputo» · «Entre **3 y 5 h** de A100» |
| `entrega/estrategia.md` | 183–185 | «son **entre tres y cinco horas** de cómputo, **según el número medio de ventanas por libro, que todavía no está medido**» |
| `PENDIENTES.md` | 47 | «**2,8 h** de cómputo A100; ~17 h de extremo a extremo» |

Cuatro versiones de la misma horquilla, y la del cuadernillo es la única que da
un número sin margen.

## B6 — El resumen de accionables del `.md` describe una tabla que no existe y ordena distinto que los otros dos

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 201–203 | «**Accionables.** Diez, con **responsable**, coste y criterio de terminado; **los tres primeros** son publicar modelo y diccionario, desplegar en enlace permanente y **terminar la remedición del catálogo**.» |
| `entrega/documento.tex` | 785 | Columnas reales: `#` · `Acción` · `Por qué` · `Coste` · `Terminado cuando` — **no hay columna de responsable** |
| `entrega/estrategia.md` | 361 | `\| # \| Acción \| Por qué \| Coste \| Terminado cuando \|` — mismas cinco columnas, sin responsable |
| `entrega/documento.tex` | 822–825 · `entrega/estrategia.md` 376–379 | «Orden de ejecución si el tiempo aprieta: A1 → A2 → **A5** → A3 → A4. **Los tres primeros** son … despliegue, publicación y **un micrófono**.» |

«Los tres primeros» nombra A1/A2/**A3** en el `.md` y A1/A2/**A5** en los otros
dos.

## B7 — `DESPLIEGUE.md` se contradice consigo mismo dos veces

| Archivo | Línea | Dice |
|---|---|---|
| `DESPLIEGUE.md` | 3–5 | «**Ya está desplegado**: `MikeMaki1763/literalevel`… público y en marcha» |
| `DESPLIEGUE.md` | 119 | «Así que **si se despliega**, hay que montar almacenamiento.» |
| `DESPLIEGUE.md` | 4 | «una cuenta Pro de **7 USD/mes**» |
| `DESPLIEGUE.md` | 35 · 86 | «## Opción A — Hugging Face PRO, **9 $ un mes**» · «Viable si los **9 $** son un problema real.» |
| `entrega/documento.tex` | 801 · `PENDIENTES.md` 88 | «**7 USD/mes**… (**9 USD de tarifa, 7 con descuento**)» |

La segunda es sólo falta de la aclaración «tarifa 9, con descuento 7» que sí
llevan los otros archivos; la primera es una frase que quedó de antes del
despliegue en un archivo cuya primera línea ya dice que está hecho.

---

# C. Menores

## C1 — Frase rota en `README.md`

`README.md:190–191`:

> «**Sin `OPENAI_API_KEY` la app sigue funcionando**: diccionario, IPA, **audio
> de buscador** y puntuación no salen a la red.»

Falta «Wiktionary,» entre «audio de» y «buscador». La lista correcta está en
`AGENTS.md:56–57`: «diccionario, IPA, **audio de Wiktionary**, buscador y
puntuación no usan red». Es anterior a estos dos commits (viene ya de
`8b579b6~1`), pero sigue viva y la frase no se sostiene.

## C2 — La figura del recorrido numera siete pasos y el texto de al lado numera seis

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.tex` | 2058–2059 | «La figura~\ref{fig:recorrido} resume el recorrido y **los seis pasos** que siguen lo detallan.» |
| `entrega/documento.tex` | 2066–2073 | Cajas de la figura: **1. Perfil · 2. Buscar · 3. Abrir · 4. Ficha · 5. Curva · 6. Palabra · 7. Voz** |
| `entrega/documento.tex` | 2110–2149 | Lista numerada: **1. Busca · 2. Abre · 3. Ficha · 4. Curva · 5. Palabra · 6. Voz** |

Los dos numeran, y no coinciden: la «5» de la figura es la «4» del texto. El
`.md` sólo tiene la lista de seis, así que el desajuste es exclusivo del PDF.

## C3 — El guion pierde «estrictamente» al pasar a `.tex`

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/guion_video.md` | 129–130 | «orden MCER **estrictamente creciente** en textos externos» |
| `entrega/guion_video.tex` | 307 | «orden MCER **creciente** en textos externos» |

Es la diapositiva de métricas desnudas. El texto hablado sí dice «estrictamente
creciente» en los dos (`md:134`, `tex:313`). Hallazgo idéntico al del barrido
anterior; no se tocó.

## C4 — Qué nivel se anuncia como cuál: dos versiones del mismo efecto

| Archivo | Línea | Dice |
|---|---|---|
| `README.md` | 88 | «un texto **A2** suele puntuar cerca de **B1**» |
| `entrega/documento.tex` | 810 · `entrega/estrategia.md` 369 | «un **A2** puntúa cerca de **B1**» |
| `modelo_v4/README.md` | 92–93 | «un texto **A1** tiende a anunciarse como **A2**» |
| `PENDIENTES.md` | 95 | «Un texto **A1** se anuncia como **A2**.» |

## C5 — «Prima del autor» se cae en el Resumen del `.tex`

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 58–59 | «probada por una lectora de quince años, **prima del autor** y ajena al proyecto» |
| `entrega/documento.tex` | 258–259 | «probada por una lectora de quince años **ajena al proyecto**» |

Sí se declara más adelante (`documento.tex:621`), así que el efecto es sólo de
resumen. Sin cambios desde el barrido anterior.

## C6 — La nota sobre las fuentes de ANSVA difiere entre los dos guiones

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/guion_video.md` | 20 | «el método **ANSVA** de Fernando Miralles, **que es la secuencia clásica de persuasión**» |
| `entrega/guion_video.tex` | 158–159 | «el método **ANSVA** de Fernando Miralles, **campeón de España de oratoria**» |
| `entrega/guion_video.md` | 29–31 | «una *«estructura de la sardina»* de la que encontré el nombre pero **no su anatomía exacta**» |
| `entrega/guion_video.tex` | 174–178 | «una *«estructura de la sardina»*, **y PAS, y ADP**, de las que encontré el nombre pero **no su anatomía**» |

*(La instrucción de chat que el barrido anterior encontró en `guion_video.md`
—«dímelo y lo rehago»— ya no está.)*

## C7 — El `.md` trae una frase de la salvedad «Dos» que el `.tex` no tiene

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.md` | 759 | «…tiene que reunirlos por su cuenta. **El `.dat` de la figura guarda los agregados, no las entradas.** Lo que se reproduce exactamente es el orden…» |
| `entrega/documento.tex` | 1782–1786 | Mismo párrafo, sin esa frase |

La frase habla de una figura que sólo existe en el `.tex`, así que está en el
archivo que no la necesita y falta en el que sí.

## C8 — La diapositiva de estrategia recorta el enunciado de A1 y omite la salvedad de A2

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/presentacion.tex` | 337–338 | «**Publicar el modelo** \| 30 min, gratis \| **Hecho**: el cuaderno corre en un Colab limpio» |
| `entrega/documento.tex` | 798 | «**Publicar el modelo y el diccionario**… **HECHO a medias**: … **el diccionario (243 MB) sigue sin publicar**» |
| `entrega/presentacion.tex` | 339–340 | «Desplegar de forma permanente \| 7 USD/mes \| **Hecho**: dirección fija que no muere al apagar» |
| `entrega/documento.tex` | 800 | «**HECHO**: … público y en marcha; **queda el disco persistente, que es A4**» |

Hallazgo idéntico al del barrido anterior; no se tocó.

## C9 — Una frase repetida literalmente en dos apartados del PDF

| Archivo | Línea | Dice |
|---|---|---|
| `entrega/documento.tex` | 770–772 (§3.4.5) | «Por eso la ficha se pinta en dos etapas: **lo local aparece al instante y la explicación se añade cuando llega**.» |
| `entrega/documento.tex` | 2146–2147 (§8.2, paso 5) | «por eso la ficha se pinta en dos etapas: **lo local aparece al instante y la explicación se añade cuando llega**.» |

Sólo ocurre en el PDF, porque el `.md` resume el §3 y no trae la primera. No lo
causaron estos dos commits, pero es una repetición verbatim a cuarenta páginas
de distancia.

## C10 — `DESPLIEGUE.md`: encabezado pegado a la lista anterior

`DESPLIEGUE.md:104–105`: la línea 104 es el último elemento de la lista de «Lo
que ya no hace falta resolver» y la 105 es `## Persistencia: ahora importa más
que antes`, **sin línea en blanco de por medio**. El encabezado duplicado y
vacío del final del archivo, que señalaba el barrido anterior, ya no está.

---

# Veredicto

**No es luz verde.** Antes de entregar hay que arreglar, por este orden: **(1)**
las bandas 0,8/1,6 de `fig:escala` y la etiqueta contradictoria de la figura de
*War and Peace* en `documento.tex`; **(2)** las tres citas de cuadro desfasadas
por la renumeración (`estrategia.md:182`, `README.md:120`, `PENDIENTES.md:77`)
más las cuatro de `validar_local.py` y la de `AGENTS.md:14`; **(3)** el «553
palabras, 3:41» de `PENDIENTES.md:26` y `:87`, que hoy son 561 y 3:44; **(4)**
el «Cuadro 7» de `documento.md:472`, que es el 8. Los siete medios y los diez
menores del listado quedan a criterio, pero **B1** (571 contra 575) y **B2** (la
tarjeta pública mezclando los 38 y los 47) son los dos que un lector externo
puede comprobar solo.
