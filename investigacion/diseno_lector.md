# Diseño del lector de LiteraLevel

**Cómo hacer que se lea cómodo y que quien lo abre vuelva.**

Fecha: 8 de septiembre de 2026. Investigación sobre el código real de
`app/ui.py` (Gradio 6.26) y `app/paletas.py`, más evidencia externa citada.

Todo lo que aparece aquí como **[medido]** lo he calculado yo sobre el código
de este repositorio y se puede reproducir. Lo que aparece como **[documentado]**
tiene enlace a la fuente. Lo que aparece como **[opinión]** es criterio mío y
no lo respalda nada más que el argumento que lo acompaña. Lo que no pude
comprobar lo digo: **no verificado**.

Este documento no toca ningún archivo del repositorio. Es un plan para aplicar.

---

## 0. Resumen: las cinco cosas que más cambian por menos esfuerzo

| # | Cambio | Problema que resuelve | Esfuerzo |
|---|---|---|---|
| 1 | Quitar `max-height:62vh` del lector y limitar la **medida de línea** a ~66 caracteres | El scroll dentro del scroll en móvil (*"difícil de usar en celular"*) y la línea de 140 caracteres en escritorio | 6 líneas de CSS |
| 2 | Quitar `text-align:justify` | Ríos de espacio en blanco en móvil; lo desaconseja WCAG explícitamente | 1 línea |
| 3 | Control de **tamaño de letra** del lector (y que se recuerde) | Lo tiene todo lector que la gente usa; no lo tiene LiteraLevel | ~15 líneas de Python + CSS |
| 4 | Arreglar el **contraste del botón primario**: falla AA en las cinco paletas | Defecto real, medido, que la prueba actual no detecta | 5 valores hex |
| 5 | Paleta **`neon`** (azul neón, oscura) + **`cristal`** (azul claro) | Lo que pide Miguel, con los ratios ya calculados y pasando AA | ~40 líneas en `paletas.py` |

Ninguno de los cinco es un rediseño. Los cinco resuelven un problema concreto.

---

## 1. Lo que ya está bien y no hay que tocar

Lo digo primero porque la tentación al llegar a un archivo de 112 KB es
reescribirlo. Estas decisiones son buenas y aguantan el análisis:

- **La arquitectura de paletas.** Un `<style>` propio para la paleta, separado
  del estructural, cambiado con `paleta.change(_css_paleta, paleta, paleta_css)`.
  Cambiar de tema no vuelve a mandar la hoja entera ni descoloca nada. Todo lo
  que propongo abajo se cuelga de este mismo mecanismo.
- **Inyectar CSS con `gr.HTML("<style>…")` en vez de `launch(css=…)`.** No es
  un apaño: **[medido]** el frontend de Gradio 6.26 reescribe las reglas que
  se pasan por `css=` y las prefija con
  `.gradio-container.gradio-container-6.26.0 .contain `, así que un selector
  como `body` o `#ll-lector` desde `css=` no llegaría donde se quiere. El
  `<style>` crudo sí. Mantenlo.
- **La doble barra de navegación de capítulos** (arriba y abajo del texto) y el
  resultado del cuestionario pintado dos veces. Son correcciones de scroll
  móvil bien razonadas.
- **`JS_SELECCION` escuchando `selectionchange` y no `mouseup`.** El comentario
  del código tiene razón: en iOS no llega `mouseup` al seleccionar con el dedo.
- **La carga perezosa** de modelo, catálogo y diccionario.
- **El campo de estrellas en CSS puro con semilla fija.** Cero peticiones de
  red, cero parpadeo entre recargas.
- **La biblioteca** (`app/biblioteca.py`): ya guarda por qué capítulo va cada
  libro y ordena por lo último tocado. La mitad de la retención honesta ya
  está construida; falta enseñarla.

---

## 2. Defectos verificados en el código actual

Estos no son opiniones de diseño. Son medidas.

### 2.1 El botón primario falla WCAG AA en las **cinco** paletas

`_CSS_GLOBAL` pinta el botón primario así:

```css
button.primary,.primary button{
  background:linear-gradient(180deg,var(--ll-boton-alto),var(--ll-acento-hondo));
  color:var(--ll-boton-texto)}
```

El texto es `--ll-boton-texto` y la parte de arriba del degradado es
`--ll-boton-alto`. **[medido]** con el mismo algoritmo de luminancia relativa
que usa `pruebas_extremas.py`:

| paleta | `boton-texto` sobre `boton-alto` | sobre `acento-hondo` |
|---|---|---|
| hielo | **2.58 : 1** | 6.38 : 1 |
| amanecer | **2.56 : 1** | 5.30 : 1 |
| menta | **2.50 : 1** | 5.08 : 1 |
| papel | **3.58 : 1** | 7.10 : 1 |
| medianoche | **3.91 : 1** | 5.72 : 1 |

AA pide 4.5:1 para texto normal. La mitad superior del botón principal de la
app —el que dice "Estimar mi nivel", "Consultar", "Leer el libro entero"— está
por debajo en las cinco paletas. La prueba «todas las paletas son legibles» no
lo ve porque solo comprueba dos pares: `texto/fondo` y `lector-texto/lector-fondo`.

**Arreglo mínimo** (solo hay que oscurecer `--ll-boton-alto`, el degradado
sigue existiendo y el aspecto apenas cambia). **[medido]** estos valores dan
≥4.5:1 con el `boton-texto` que ya tiene cada paleta:

| paleta | `--ll-boton-alto` actual | propuesto | ratio resultante |
|---|---|---|---|
| hielo | `#3aa9cf` | `#257c99` | 4.53 : 1 |
| amanecer | `#e08a4c` | `#ae5a1e` | 4.73 : 1 |
| menta | `#63b394` | `#3e7f66` | 4.74 : 1 |
| papel | `#a1814f` | `#8a6f44` | 4.65 : 1 |
| medianoche | `#8a72b0` | `#7e63a8` | 4.71 : 1 |

### 2.2 El color de acento falla AA como texto en las paletas claras

`--ll-acento` se usa como **color de texto** en la pestaña seleccionada:

```css
.tab-nav button.selected{color:var(--ll-acento)}
```

**[medido]** `--ll-acento` contra `--ll-fondo`:

| paleta | acento / fondo | acento-hondo / fondo |
|---|---|---|
| hielo | 12.13 ✔ | 3.01 ✘ |
| amanecer | **3.54 ✘** | 5.13 ✔ |
| menta | **3.04 ✘** | 4.80 ✔ |
| papel | **4.28 ✘** | 6.41 ✔ |
| medianoche | 9.77 ✔ | 3.02 ✘ |

Hay un patrón limpio: en las paletas oscuras sirve `--ll-acento`; en las claras
sirve `--ll-acento-hondo`. **Arreglo:** una variable nueva `--ll-acento-texto`
que en cada paleta apunte al que pasa, y usarla en `.tab-nav button.selected` y
en cualquier enlace.

> **Trampa de la prueba, importante:** `pruebas_extremas.py` comprueba que
> *todas las paletas definen exactamente las mismas variables*
> (`len({tuple(sorted(d["vars"])) …}) == 1`). Si añades `--ll-acento-texto`
> tienes que añadirla a **las siete** paletas (cinco actuales + las dos nuevas)
> o la prueba se cae. Lo mismo para cualquier variable que se añada.

### 2.3 Otra trampa de la prueba de contraste

El parser de la prueba lee `rgba(8,16,28,.62)` y **descarta el alfa**: trata el
color como opaco. Es decir, la prueba mide el contraste de un fondo de lector
que en pantalla es semitransparente sobre el fondo de página. En la práctica
funciona porque los fondos de lector y de página son parecidos en cada paleta,
pero conviene saberlo: la prueba es una aproximación optimista, no una medición
de lo que se ve. Si algún día se pone un `--ll-lector-fondo` muy distinto del
`--ll-fondo`, la prueba pasará y la pantalla no.

### 2.4 El texto justificado

`_CSS_LECTOR` tiene `text-align:justify; hyphens:auto`. **[documentado]** El
criterio WCAG 2.2 **1.4.8 Visual Presentation** (nivel AAA) dice literalmente:
*"Text is not justified (aligned to both the left and the right margins)"*,
porque el texto justificado dificulta la lectura a personas con dificultades
cognitivas — los ríos de espacio en blanco despistan al ojo.
([W3C, Understanding SC 1.4.8](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html))

En una columna estrecha de móvil el problema es peor, no menor: con 35–40
caracteres por línea, justificar produce espacios enormes entre palabras.

Sobre `hyphens:auto`: **[medido]** la plantilla de Gradio 6.26 sirve
`<html lang="en">`, así que el guionado se aplica con reglas inglesas. Para el
texto del libro es correcto; para la interfaz en español, no. Si se quita
`justify`, `hyphens` deja de hacer falta.

### 2.5 El scroll dentro del scroll

`#ll-lector{max-height:62vh;overflow-y:auto}`. Esto crea una caja que se
desplaza dentro de una página que también se desplaza. En escritorio es
incómodo; en móvil es la cosa que más se parece a *"o yo soy muy tonta para
esto"*: el dedo a veces mueve el texto y a veces mueve la página, según dónde
caiga, y no hay forma de saberlo de antemano. **[opinión, pero con base]** es
el defecto de usabilidad más grave del lector.

### 2.6 La medida de línea

`#ll-lector` no tiene `max-width`. Ocupa todo el ancho del bloque de Gradio. En
un portátil de 1440 px con la tipografía Georgia a 19 px, eso son del orden de
120–140 caracteres por línea. Ver §3.1.

### 2.7 Las filas de Gradio no se parten en móvil

```python
with gr.Row():
    b_prev = gr.Button("‹ Anterior", scale=1)
    cap = gr.Dropdown(label="Capítulo", choices=[], scale=4)
    b_next = gr.Button("Siguiente ›", scale=1)
```

`gr.Row` es un flex row y no envuelve solo. A 390 px de ancho, con `scale`
1/4/1, cada botón se queda con del orden de 55–60 px de ancho. Ver §7.

### 2.8 El `h1` con degradado se vuelve invisible en alto contraste

```css
h1{-webkit-text-fill-color:transparent;color:transparent; …}
```

En modo de alto contraste forzado del sistema (Windows), el navegador
sustituye colores pero no puede restituir un `background-clip:text`, y el
título puede desaparecer. Hace falta una salvaguarda `@media (forced-colors: active)`.
**[opinión sobre el riesgo concreto en este caso; el mecanismo está documentado.]**

---

## 3. Tipografía y comodidad de lectura de prosa larga

### 3.1 Longitud de línea

Es el parámetro con mejor relación entre lo que cuesta y lo que mejora.

- **[documentado]** Butterick, *Practical Typography*: *"Aim for an average line
  length of 45–90 characters, including spaces"*, y advierte de que medir en
  pulgadas o centímetros es inútil porque el cuerpo de la letra cambia cuántos
  caracteres caben. ([practicaltypography.com/line-length.html](https://practicaltypography.com/line-length.html))
- **[documentado]** Baymard Institute: *"The optimal line length for body text
  is 50–75 characters"*, con un máximo de 80.
  ([baymard.com/blog/line-length-readability](https://baymard.com/blog/line-length-readability))
  *(La cifra que circula por ahí de "41% más saltos por encima de 80 caracteres"
  aparece en resúmenes de terceros; **no la he verificado en el artículo
  original** y no la uso como argumento.)*
- **[documentado]** WCAG 2.2 SC 1.4.8 (AAA) pide *"no more than 80 characters
  or glyphs"*. ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html))

**Objetivo: 60–70 caracteres.** Con `ch` de CSS hay que tener cuidado: `1ch`
es el ancho del carácter `0`, y en una serif de texto los dígitos son más
anchos que la media de las minúsculas, así que `66ch` da bastante **más** de 66
caracteres reales. **[opinión]** poner `max-width: 62ch` y comprobar a ojo con
un párrafo real es más honesto que fingir precisión.

Truco clave para Gradio: no estrechar el panel, estrechar **los párrafos**.
Así el bloque de Gradio sigue ocupando su ancho (y no rompe la maquetación) y
el texto queda centrado en una columna legible:

```css
#ll-lector p{max-width:62ch;margin-left:auto;margin-right:auto}
```

### 3.2 Interlineado y separación de párrafos

- **[documentado]** WCAG 2.2 SC **1.4.12 Text Spacing** (nivel **AA**, no AAA)
  exige que el contenido no se rompa cuando el usuario fuerza: interlineado
  ≥ **1.5** veces el cuerpo, espacio tras párrafo ≥ **2** veces el cuerpo,
  espaciado entre letras ≥ 0.12 em, entre palabras ≥ 0.16 em.
  ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html))
- **[documentado]** SC 1.4.8 pide interlineado de al menos "espacio y medio"
  dentro del párrafo y separación entre párrafos de al menos 1.5 veces el
  interlineado.

El lector actual usa `line-height:1.75` y `margin:0 0 1.05em`. El interlineado
está bien. La separación entre párrafos se queda corta frente a 1.4.8
(1.05 em < 1.5 × 1.75 em). **[opinión]** para prosa continua de libro, el
margen de párrafo grande rompe el ritmo; la alternativa clásica de libro
—sangría de primera línea y margen cero— es mejor y también resuelve el
criterio de "distinguir párrafos". Doy las dos opciones en el CSS del §8.

### 3.3 Cuerpo de letra en móvil frente a escritorio

- **[documentado]** Apple recomienda un mínimo de 11 pt en iOS/iPadOS y sitúa
  el cuerpo (`Body`) en 17 pt por defecto, y subraya que la densidad de píxeles,
  el brillo, la distancia, la vista del lector y la luz ambiente afectan al
  tamaño mínimo apropiado.
  ([Apple HIG, Typography](https://developer.apple.com/design/human-interface-guidelines/typography))
  *(La página de Apple se sirve por JavaScript y no pude extraer el texto
  literal con la herramienta de fetch; las cifras 11 pt / 17 pt las confirmé
  en varias fuentes secundarias que citan la HIG. **Cifra secundaria, no
  verificada en la fuente primaria.**)*
- **[documentado]** Legge & Bigelow (2011), *"Does print size matter for
  reading? A review of findings from vision science and typography"*, *Journal
  of Vision* 11(5). El rango en el que se lee a **velocidad máxima** ("fluent
  range") abarca un factor de 10 en tamaño angular de la altura de x, de unos
  0.2° a 2°; a 40 cm de distancia eso son alturas de x de 1.4 mm (≈4 pt) a
  14 mm (≈40 pt). ([ARVO Journals](https://jov.arvojournals.org/article.aspx?articleid=2191906) ·
  [PDF](https://graphicdesign-research.com/images/LeggeBiglow-2011.pdf))

Lo importante de Legge & Bigelow es lo que **no** dice: no dice que haya un
tamaño óptimo estrecho. El rango cómodo es amplísimo, y por eso la respuesta
correcta no es "elige tú el número perfecto" sino **"deja que lo elija quien
lee"**. Es exactamente lo que pide Miguel con "más libertad para el usuario".

**[opinión]** valores de partida razonables, con el usuario pudiendo moverlos:
19 px en móvil, 20–21 px en escritorio. El lector actual usa 19 px fijos, que
para escritorio se queda algo corto y para móvil está bien.

**Detalle no negociable de móvil:** **[documentado]** Safari en iOS hace zoom
automático al enfocar un campo de formulario cuyo `font-size` sea menor de
**16 px**. Poner 16 px o más en `input`/`textarea` lo evita. La solución del
`maximum-scale=1` en el viewport **no** vale: impide hacer zoom con los dedos y
viola WCAG. ([CSS-Tricks](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/))
Esto afecta directamente a la caja `#ll-palabra`, que es el corazón de la
función de consultar palabras. **[medido]** la plantilla de Gradio sirve
`<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">`,
sin `maximum-scale`, así que el zoom con los dedos funciona: bien, y no lo
toques.

### 3.4 ¿Negro puro sobre blanco puro es peor?

Aquí hay que separar dos afirmaciones que se confunden mucho.

**Lo que sí está documentado — sobre polaridad (claro sobre oscuro vs oscuro
sobre claro):**

Nielsen Norman Group resume la evidencia así: *"light mode leads to better
performance most of the time"* para personas con visión normal, y aun así
recomiendan **ofrecer** el modo oscuro.
([nngroup.com/articles/dark-mode](https://www.nngroup.com/articles/dark-mode/))
Los estudios que citan:

- **Piepenbrock et al. (2013)**, *Ergonomics*: agudeza visual y corrección de
  pruebas, en jóvenes (18–33) y mayores (60–85). El modo claro ganó en todas
  las dimensiones; y *"the smaller the font, the better it is for users to see
  the text in light mode"*.
- **Dobres et al. (2017)**, *Applied Ergonomics*: de día no hubo efecto
  significativo de la polaridad; de noche el modo claro rindió mejor.
- **Legge et al. (1985)**, *Vision Research*: personas con medios oculares
  turbios (cataratas) leen **mejor** en modo oscuro.

*(No he leído los tres artículos originales: los tomo de la síntesis de NN/g,
que sí los cita con autor, revista y año. Como resumen de terceros, es
sólido; como cita primaria, no verificado.)*

**Consecuencia incómoda para este proyecto:** el tema por defecto de
LiteraLevel es oscuro, y el que Miguel quiere también. La evidencia dice que
para lectura prolongada de la mayoría de la gente lo mejor es lo contrario.
La salida no es discutir con Miguel: es que la app **traiga las dos** y que
elegir sea trivial. Por eso propongo dos paletas nuevas en §6, una oscura de
neón y **una clara con la misma identidad azul**, para que "quiero el estilo
futurista" y "quiero leer dos horas sin que me duelan los ojos" no sean
decisiones que se peleen.

**Lo que NO está bien documentado:** la idea popular de que "#000 sobre #fff
cansa por halación" se repite mucho y rara vez con una cita. **No la doy por
verificada.** Lo que sí hay es guía de diseño, no de investigación:

- **[documentado, fuente secundaria]** Material Design recomienda como
  superficie base del tema oscuro un gris muy oscuro **`#121212`** en lugar de
  negro puro, entre otras cosas para que se distingan los niveles de elevación
  (`#1E1E1E`, `#242424`…). También recomienda **desaturar** los colores en tema
  oscuro, porque los colores saturados "vibran" visualmente contra fondos
  oscuros. *(Las páginas de material.io se sirven por JavaScript y no pude
  extraer el texto literal; estas dos recomendaciones aparecen consistentemente
  en múltiples fuentes que citan la guía, incluido el propio codelab de Google
  [Design a dark theme with Material and Figma](https://codelabs.developers.google.com/codelabs/design-material-darktheme).
  La cifra de "15.8:1 mínimo de contraste" que también circula: **no
  verificada**, no la uso.)*

**[medido]** La paleta `hielo` actual tiene `--ll-fondo: #05070d`, que es negro
a efectos prácticos, y da un contraste de **16.50 : 1** en la interfaz y
**16.68 : 1** en el lector. Es más de tres veces el mínimo AA. Bajarlo a
~13–15:1 sigue siendo enormemente accesible y sigue la recomendación de
Material de no usar negro puro. Es lo que hace la paleta `neon` propuesta
(fondo `#070c18`, contraste **14.84 : 1**).

### 3.5 ¿Qué familias tipográficas?

La respuesta honesta: **casi da igual, y quien te diga lo contrario está
vendiendo algo.**

**[documentado]** Las comparaciones entre serif y sans serif en pantalla
típicamente **no encuentran diferencias** de velocidad de lectura ni de
comprensión. El estudio de eye-tracking del Software Usability Research
Laboratory (Wichita State) no halló diferencia estadísticamente significativa
en velocidad ni comprensión entre serif y sans bien diseñadas, aunque los
lectores *puntuaron* las sans como más legibles y menos cansadas en cuerpos de
10–12 pt. Otros estudios dan resultados contradictorios entre sí.
([Overview of research: Type — legible-typography.com](https://legible-typography.com/en/5-overview-of-research-type) ·
[How Serif and Sans Serif Typefaces Influence Reading on Screen, Springer](https://link.springer.com/chapter/10.1007/978-3-319-40355-7_55) ·
[Serif vs sans serif y usabilidad en e-commerce, PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9680897/))

Lo que sí importa, por este orden: **cuerpo de letra**, **longitud de línea**,
**interlineado** y **contraste**. La familia es la última variable, y a partir
de ahí es identidad, no legibilidad.

**[opinión]** Para LiteraLevel:

- El lector se queda con **serif**. No porque lea mejor, sino porque señala
  "esto es un libro" y separa visualmente el texto de la obra de la interfaz.
  La pila actual (`Georgia, "Iowan Old Style", "Times New Roman", serif`) está
  bien; pondría `Iowan Old Style` y `Charter` **antes** de Georgia, porque en
  pantallas de alta densidad rinden mejor, y Georgia como red de seguridad.
- La **interfaz** debe ser sans y del sistema: `system-ui`. Es lo que hace que
  una app "no se sienta antigua" en un móvil — se parece al resto del teléfono.
  Aquí sí hay una ganancia perceptible y gratis.
- **Nada de fuentes web de Google Fonts.** Añaden una petición de red bloqueante
  a un arranque que ya carga 328 MB de modelo, y si el despliegue va sin red
  aparece el texto en Times. La app tiene como regla la degradación elegante;
  una fuente remota la incumple.
- Ofrecer al usuario **tres opciones** (serif / sans / "grande y espaciada") es
  más útil que acertar con una sola. Ver §4 y §8.

---

## 4. Modo lectura: qué hacen bien los lectores que la gente sí usa

Esto es observación de producto, no investigación. **[opinión informada]**, y
lo marco como tal. Lo valioso es qué de eso cabe en Gradio.

| Lo que hacen Kindle / Apple Books / Instapaper / Pocket / Readwise Reader | ¿Cabe en Gradio 6.26? |
|---|---|
| **Columna de ancho limitado**, con márgenes generosos y el texto centrado | **Sí, trivial.** `max-width` en el `<p>` + `margin:auto`. §8 |
| **Tamaño de letra ajustable** por el lector, en pasos, no continuo | **Sí.** `gr.Radio`/`gr.Slider` → `.change` → `gr.HTML` con `<style>` que reescribe una variable. Es el mismo patrón que ya usa la paleta |
| **Un solo scroll**: la página *es* el texto | **Sí.** Quitar `max-height:62vh` |
| **Progreso del capítulo** (barra fina, o "quedan 6 min") | **Sí,** con JS. Barra fija de 3 px arriba movida por `window.scrollY`. El "quedan X min" se calcula en Python: palabras del capítulo ÷ 200 ppm |
| **Dónde se quedó**, incluso a mitad de capítulo | **Parcial y ya casi hecho.** Entre capítulos ya lo guarda `biblioteca.py` y `sesion.json`. Dentro del capítulo hace falta guardar la fracción de scroll: ~15 líneas de JS con `localStorage`, cero Python |
| **Preferencias que sobreviven al cierre** | **Sí. [medido]** `gr.BrowserState` existe en Gradio 6.26 y guarda en `localStorage` cifrado. **Aviso importante:** si no le pasas `secret=` fija, genera una aleatoria **por proceso**, y al reiniciar el servidor las preferencias guardadas ya no se pueden descifrar. Hay que fijar **`storage_key=` y `secret=`** |
| **Modo sin distracciones** (esconder todo menos el texto) | **Sí, solo CSS.** Un `gr.Checkbox` que inyecta un `<style>` que oculta los acordeones y botones de análisis mientras se lee |
| **Tocar una palabra para su definición** | **Ya está**, y bien resuelto con `selectionchange` |
| Tipografía elegible entre 2–5 opciones | **Sí**, mismo patrón que el tamaño |
| Paso de página por gesto / a pantallas | **No merece la pena.** Reimplementar paginación sobre HTML fluido es caro y frágil. El scroll continuo con progreso visible es lo que hacen Instapaper y Pocket, y es suficiente |

**Lo que copiaría, por orden:** ancho de columna → un solo scroll → tamaño de
letra ajustable → progreso del capítulo → posición dentro del capítulo →
preferencias persistentes → modo sin distracciones.

**Lo que no copiaría:** la paginación, la sincronización entre dispositivos
(no hay cuentas), y el "tiempo de lectura restante del libro entero" (con
libros de 366 capítulos la cifra es tan grande que desanima en vez de motivar
— **[opinión]**).

---

## 5. Retención sin trucos sucios

### 5.1 Lo que hace volver a alguien, y respeta a quien vuelve

La distinción que uso es sencilla y se puede aplicar a cada idea: **¿la
mecánica sirve al objetivo del usuario, o sirve a la métrica de la app a costa
del usuario?**

Mecánicas que sirven al usuario (recomendadas, por orden de valor/esfuerzo):

1. **"Continuar donde lo dejaste", visible al entrar.** Es la que más rinde y
   la más honesta: no inventa un motivo para volver, elimina la fricción de
   volver. **Ya existe la mitad**: `biblioteca.listar()` devuelve los libros
   ordenados por lo último tocado y con `avance`. Hoy hay que ir a la pestaña
   "Mis libros" y pulsar "Ver mis libros". Debería salir solo, arriba,
   nada más abrir.
2. **Progreso visible y honesto.** Barra del capítulo y "capítulo 7 de 24".
   El *goal-gradient effect* (Kivetz, Urminsky & Zheng, 2006, *Journal of
   Marketing Research*) describe que el esfuerzo aumenta al acercarse a una
   meta visible — *no he verificado el artículo original, lo cito como
   referencia a comprobar*. Pero aunque el efecto no existiera, saber por dónde
   vas es información que el lector necesita, no un truco.
3. **El cuaderno de palabras como logro acumulado.** "Llevas 143 palabras
   consultadas en este libro" es un contador de algo que el usuario hizo de
   verdad y que le importa. Ya se guarda en `cuaderno.py`.
4. **Cerrar el bucle de nivel.** Cuando alguien lleva tres libros leídos,
   volver a estimar su nivel y enseñarle que subió. Es la promesa central del
   producto, y es lo único que LiteraLevel puede ofrecer y Kindle no.
5. **Metas que pone el usuario**, no la app. "Quiero leer 10 minutos al día",
   elegido por él, editable y desactivable sin fricción.
6. **Un buen momento de recompensa al terminar un capítulo**: una frase, la
   palabra más difícil que superó, y el botón de siguiente capítulo. Barato y
   sincero.

### 5.2 Lo que NO hay que hacer: lista explícita de patrones oscuros

**[documentado]** Tomo los nombres del catálogo de Harry Brignull en
[deceptive.design/types](https://www.deceptive.design/types), que es la
taxonomía de referencia. Los que una app de lectura tiene a mano y debe
rechazar:

| Patrón | Definición (deceptive.design) | Cómo aparecería en LiteraLevel |
|---|---|---|
| **Nagging** | *"El usuario intenta hacer algo, pero se le interrumpe insistentemente con peticiones de hacer otra cosa que puede no convenirle"* | Un modal "¿seguro que quieres salir?" o recordatorios que no se pueden apagar |
| **Confirmshaming** | *"Se manipula emocionalmente al usuario para que haga algo que no habría hecho"* | El botón de cancelar que dice "No, prefiero seguir sin aprender inglés" |
| **Fake urgency** | *"Se presiona al usuario con una limitación de tiempo falsa"* | "¡Tu racha expira en 2 horas!" cuando no expira nada real |
| **Fake scarcity / fake social proof** | *"Falsa indicación de escasez o popularidad"*, *"reseñas o actividad falsas"* | "37 personas están leyendo este libro ahora mismo" inventado |
| **Obstruction** | *"Barreras que dificultan completar la tarea"* | Esconder el ajuste de tamaño de letra a tres clics de profundidad |
| **Addictive Design** | *"Diseño que explota vulnerabilidades psicológicas para fomentar la interacción excesiva"* | La categoría que engloba las rachas mal hechas |
| **Preselection** | *"Opción por defecto ya marcada para influir en la decisión"* | Notificaciones diarias activadas de fábrica |
| **Trick wording / Visual interference** | Lenguaje confuso; información oculta o disfrazada | Un contador de "días activos" que en realidad cuenta aperturas de la app |

**El caso de las rachas, que merece párrafo propio.** Es la mecánica que más se
copia y la más fácil de convertir en patrón oscuro. La racha funciona por
**aversión a la pérdida**: duele más perder lo construido que ilusiona ganar
algo equivalente (Kahneman y Tversky). Eso significa que una racha no motiva a
leer: motiva a **no perder la racha**, que no es lo mismo. La crítica
documentada más clara es que el usuario acaba haciendo lo mínimo para
salvar el contador —abrir, tocar, cerrar— activando la métrica de retención sin
que haya ocurrido aprendizaje. Y un estudio longitudinal sobre gamificación en
Untappd concluye que las rachas, las insignias y los logros basados en cantidad
*"pueden fomentar el exceso, la formación de hábito y la dependencia"*
([arXiv](https://arxiv.org/pdf/2601.04841)).

*(Las cifras que circulan sobre Duolingo —"retención del 12% al 55%", "+14% en
retención a día 14 con la apuesta de racha", "3× más probabilidad de alcanzar
nivel intermedio"— vienen de blogs de marketing de agencias, no de artículos
revisados ni de publicaciones de Duolingo que yo haya podido verificar.
**No verificadas. No las uses en la presentación.**)*

**[opinión]** Si Miguel quiere una racha, la versión honesta es:

- Cuenta **minutos leídos**, no aperturas de la app.
- **Se puede pausar** ("me voy de vacaciones") sin perderla.
- **Perderla no se castiga**: no hay animación de vidrio roto, ni "has perdido
  47 días". Se dice "empiezas una nueva" y ya.
- **Se puede apagar entera** desde ajustes, y ese interruptor es visible.
- No hay notificaciones. Ninguna. No hay a quién notificar en una app local.

### 5.3 La métrica que no hay que perseguir

**[documentado]** La crítica más útil que encontré: las métricas de
"engagement" —clics, tiempo en la app— se recogen en entornos diseñados para
ser adictivos y cargados de patrones oscuros, así que medirlas y optimizarlas
realimenta el problema ([The Problem with Metrics…, arXiv](https://arxiv.org/pdf/2002.08512)).
Para LiteraLevel la métrica correcta es **capítulos terminados** y **palabras
consultadas que luego se reconocen**, no minutos de sesión.

---

## 6. Neón azul sin romper la legibilidad

### 6.1 Las reglas

Miguel tiene razón en su advertencia, y la evidencia la respalda: los pasteles
sobre claro no se leen. Pero el neón tiene el problema simétrico y menos obvio.

**Regla 1 — El neón no lleva texto largo.** Un color muy saturado y luminoso
sirve para bordes, iconos, un número de capítulo, la pestaña activa, un
subrayado. Nunca para un párrafo. Aunque el ratio de contraste dé bien, la
saturación alta contra fondo oscuro produce vibración visual — es la razón por
la que Material recomienda desaturar en tema oscuro (§3.4).

**Regla 2 — El resplandor va en el contenedor, nunca en el texto.** Un
`text-shadow` de neón sobre el texto **baja** el contraste efectivo: difumina
el borde de la letra, que es justo lo que el ojo usa para reconocerla. El
`box-shadow` sobre un panel o un borde no toca ninguna letra.

**Regla 3 — El neón necesita oscuridad.** Un resplandor sobre fondo claro no
brilla: se ve sucio. En la paleta clara (`cristal`) el "toque futurista" no se
hace con resplandor sino con **azul saturado, esquinas muy redondeadas y
mucho aire**. Es la misma identidad por otros medios.

**Regla 4 — El resplandor es decoración, nunca información.** Si el borde que
brilla es lo único que indica cuál es la pestaña activa, quien no distinga ese
matiz no puede usar la app. Siempre hay que doblarlo con algo no cromático:
grosor, subrayado, negrita, un icono.

**Regla 5 — El resplandor no se mueve.** Un `box-shadow` pulsante en bucle es
caro en GPU de móvil y molesta a quien tiene sensibilidad al movimiento.
Si hay animación, envuélvela en `@media (prefers-reduced-motion: reduce)`.

**Regla 6 — Un solo neón.** Un acento y ya. Dos colores de neón compitiendo es
lo que hace que una interfaz parezca una máquina recreativa en vez de
minimalista.

### 6.2 Lo que NO hay que hacer

- ✘ `text-shadow: 0 0 8px cyan` sobre el texto del lector, o sobre cualquier
  texto de más de tres palabras.
- ✘ Texto neón sobre fondo neón, aunque el ratio calculado pase: el cálculo de
  WCAG es sobre luminancia y no modela la vibración cromática.
- ✘ Bordes de 1 px de un color neón como **único** indicador de foco de
  teclado. El foco necesita un `outline` con `outline-offset`, visible en
  todas las paletas.
- ✘ Fondo animado con degradados en movimiento. En el móvil de Esmeralda eso es
  batería y calor.
- ✘ Glassmorphism apilado: `backdrop-filter:blur()` dentro de otro
  `backdrop-filter:blur()`. Ya hay uno en `.block`; añadir más capas de
  desenfoque es el camino más rápido a que el texto pierda contraste real
  contra un fondo que ya no controlas. **[opinión]**
- ✘ Negro puro (`#000`) como fondo con blanco puro (`#fff`) encima: 21:1, el
  máximo posible, y contra la recomendación de Material.

---

## 7. Móvil

### 7.1 Zonas táctiles

**[documentado]** Los tres números que importan:

| Norma | Mínimo | Nivel |
|---|---|---|
| WCAG 2.2 SC **2.5.8** Target Size (Minimum) | **24 × 24** px CSS | **AA** ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)) |
| WCAG 2.2 SC **2.5.5** Target Size (Enhanced) | **44 × 44** px CSS | AAA ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)) |
| Material Design / Android | **48 × 48 dp** (≈9 mm físicos) | Recomendación ([Android Accessibility Help](https://support.google.com/accessibility/android/answer/7101858?hl=en)) |
| Apple iOS | 44 × 44 pt | Recomendación |

**[opinión]** Para una app que va a usar una adolescente con el pulgar en el
autobús: **48 px de alto mínimo en todo lo pulsable**, no 24. El comentario del
código de `_CSS_GLOBAL` ya razona esto para las fichas de radio ("un circulito
de radio es un blanco de 12 px; la ficha entera es de 44") y es correcto:
falta aplicarlo a botones y pestañas.

### 7.2 Qué falla típicamente en Gradio en pantallas pequeñas

**[medido]** sobre Gradio 6.26 instalado:

1. **`gr.Row` no envuelve.** Es un flex row sin `flex-wrap`. Con tres
   controles y `scale` desiguales, en 390 px los botones se quedan en 55 px.
   Se arregla dando `elem_classes="ll-fila"` a las `Row` que lo necesiten y
   añadiendo `flex-wrap:wrap` en móvil. **No apuntes a las clases internas de
   Gradio**: no pude confirmar el nombre estable de la clase de `Row` en 6.26
   (está en un *chunk* cargado bajo demanda) y cambia entre versiones.
2. **`.gradio-container-6-26-0` lleva `overflow:hidden`.** Es la razón por la
   que conviene desconfiar de `position:sticky` dentro de la app. Para la barra
   de progreso, `position:fixed` sobre el viewport es más seguro que `sticky`.
   *(Que sticky falle aquí concretamente: **no verificado**, solo es la razón
   por la que elijo `fixed`.)*
3. **La barra de pestañas se desborda.** Hay siete pestañas ("Mi nivel",
   "Buscar lectura", "Leer", "Pronunciación", "Mis libros", "Mis palabras",
   "Colores", "Estado"). En 390 px no caben. Se arregla con
   `overflow-x:auto` + `scroll-snap` y ocultando la barra de scroll.
4. **Campos de formulario por debajo de 16 px** → zoom automático en iOS (§3.3).
5. **`gr.Dropdown` con 366 opciones** en móvil es una lista imposible. El
   acordeón "Índice del libro" con `gr.Radio` ya es mejor camino; en móvil
   debería ser el principal y el desplegable el secundario. **[opinión]**
6. **El nombre de la clase raíz lleva la versión** (`gradio-container-6-26-0`)
   pero **[medido]** el elemento también tiene la clase pelada
   `gradio-container`, así que los selectores actuales de `paletas.py` son
   correctos y seguirán funcionando al actualizar. Bien.

### 7.3 Qué se arregla solo con CSS

Todo lo de arriba menos el punto 1 (necesita un `elem_classes` en Python, que
es una línea) y el 5 (decisión de maquetación). El resto es CSS puro. Ver §8.4.

---

## 8. CSS concreto para pegar

> **Aviso de sintaxis, importante.** En `app/ui.py`, `_CSS_GLOBAL` es un
> **f-string**: dentro de él todas las llaves van **duplicadas** (`{{` `}}`).
> `_CSS_LECTOR`, `_CSS_VOZ`, `_CSS_CUADERNO` y `_CSS_BIBLIO` son cadenas
> normales: llaves simples. El CSS de abajo va con llaves **simples**; si lo
> pegas dentro de `_CSS_GLOBAL` hay que duplicarlas.

### 8.1 El lector — sustituto de `_CSS_LECTOR`

Resuelve §2.4 (justificado), §2.5 (doble scroll), §2.6 (medida de línea),
§3.2 (separación de párrafos) y §3.3 (cuerpo en móvil).

```css
<style>
/* Los tres números que el usuario puede mover. Se cambian desde otro
   <style>, igual que hace la paleta: nunca se reescribe esta hoja. */
:root{
  --ll-cuerpo:20px;        /* tamaño de letra del lector */
  --ll-medida:62ch;        /* ancho de la columna de texto */
  --ll-interlineado:1.75;
}

#ll-lector{
  /* SIN max-height: la página entera es el lector. Adiós al scroll dentro
     del scroll, que es lo que hace que en el móvil el dedo no sepa qué
     está moviendo. */
  padding:1.6rem clamp(1rem,4vw,2.2rem);
  border:1px solid var(--ll-borde);
  border-radius:18px;
  background:var(--ll-lector-fondo);
  color:var(--ll-lector-texto);
  font-family:"Iowan Old Style","Charter","Bitstream Charter",
              "Source Serif 4",Georgia,"Times New Roman",serif;
  font-size:var(--ll-cuerpo);
  line-height:var(--ll-interlineado);
  /* NO justify: WCAG 1.4.8 lo desaconseja y en una columna estrecha de
     móvil produce ríos de espacio en blanco. */
  text-align:left;
  hyphens:none;
  text-wrap:pretty;              /* evita líneas huérfanas de una palabra */
  font-kerning:normal;
  -webkit-font-smoothing:antialiased;
}

/* La medida la impone el PÁRRAFO, no el panel: así el bloque de Gradio
   sigue ocupando su ancho y no se descoloca nada, pero el texto se lee
   en una columna de libro. */
#ll-lector p{
  max-width:var(--ll-medida);
  margin:0 auto 1.5em;           /* 1.5em ≈ separación que pide WCAG 1.4.8 */
}
#ll-lector p:first-child{margin-top:0}

/* Alternativa de libro, si se prefiere el ritmo de novela impresa:
   sin margen entre párrafos y con sangría de primera línea. Elegir una
   de las dos, no las dos a la vez.
#ll-lector p{max-width:var(--ll-medida);margin:0 auto;text-indent:1.4em}
#ll-lector p:first-child{text-indent:0}
*/

#ll-lector::selection,#ll-lector p::selection{
  background:var(--ll-seleccion)}
#ll-lector .ll-vacio{font-style:italic;opacity:.7}

/* Móvil: la columna ya es estrecha por el ancho de pantalla, así que la
   medida sobra; lo que hace falta es menos padding y algo menos de cuerpo. */
@media (max-width:640px){
  :root{--ll-cuerpo:19px;--ll-interlineado:1.7}
  #ll-lector{padding:1.1rem 1rem;border-radius:14px}
  #ll-lector p{margin-bottom:1.35em}
}

/* Quien tiene el sistema en alto contraste no quiere nuestros colores. */
@media (forced-colors: active){
  #ll-lector{background:Canvas;color:CanvasText;border-color:CanvasText}
}
</style>
```

### 8.2 Tamaño de letra ajustable — el patrón de la paleta, aplicado

En Python, exactamente el mismo mecanismo que ya funciona para los colores.
**No lo aplico yo; esto es el boceto.**

```python
# En app/ui.py, junto a _css_paleta:

_CUERPOS = {"pequeña": ("18px", "62ch"), "normal": ("20px", "62ch"),
            "grande": ("23px", "54ch"), "enorme": ("27px", "46ch")}

def _css_cuerpo(clave: str) -> str:
    """Solo reescribe tres variables. Nunca lanza."""
    cuerpo, medida = _CUERPOS.get(str(clave), _CUERPOS["normal"])
    return (f"<style>:root{{--ll-cuerpo:{cuerpo};--ll-medida:{medida}}}</style>")

# En construir(), junto a paleta_css:
cuerpo_css = gr.HTML(_css_cuerpo("normal"), elem_id="ll-cuerpo-css")
# ... y en la pestaña de ajustes:
cuerpo = gr.Radio(choices=list(_CUERPOS), value="normal",
                  label="Tamaño de la letra")
cuerpo.change(_css_cuerpo, cuerpo, cuerpo_css)
```

Nótese que al subir el cuerpo **baja la medida en `ch`**: con letra grande hay
que estrechar la columna o se vuelve a pasar de 75 caracteres. Es el ajuste que
casi nadie hace y que separa un lector cómodo de uno "con letra grande".

Y hay que añadir `#ll-cuerpo-css{display:none}` a la regla que ya existe:

```css
#ll-css,#ll-paleta-css,#ll-cuerpo-css{display:none}
```

### 8.3 Que las preferencias sobrevivan al cierre

**[medido]** `gr.BrowserState` existe en 6.26 y guarda en `localStorage`
cifrado. **Hay que fijar `storage_key` y `secret`**, o al reiniciar el servidor
se genera un secreto nuevo y lo guardado deja de poder descifrarse:

```python
prefs = gr.BrowserState(
    {"paleta": paletas_mod.POR_DEFECTO, "cuerpo": "normal"},
    storage_key="literalevel_prefs",
    secret="literalevel-v4-prefs")   # fija, o se pierde en cada reinicio
```

y luego, en `demo.load`, aplicar `paleta` y `cuerpo` desde `prefs`. Si el valor
guardado es una clave que ya no existe, `_css_paleta` ya vuelve a la de siempre:
esa defensa está bien puesta y sigue valiendo.

### 8.4 Móvil: zonas táctiles, pestañas y filas

Va en `_CSS_GLOBAL` (recuerda **duplicar las llaves** allí):

```css
/* Zonas táctiles: 48 px, no 24. Lo pulsa un pulgar en un autobús. */
button,.gr-button,.tab-nav button,
label:has(input[type="radio"]),label:has(input[type="checkbox"]){
  min-height:48px}

/* Campos de formulario a 16 px o iOS hace zoom solo al enfocarlos. */
input,textarea,select,.gr-input,.gr-text-input{font-size:16px}

/* La barra de pestañas se desborda a 390 px. Que se deslice, y que se note
   que se puede deslizar. */
.tab-nav{
  overflow-x:auto;flex-wrap:nowrap;
  scroll-snap-type:x proximity;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none}
.tab-nav::-webkit-scrollbar{display:none}
.tab-nav button{scroll-snap-align:start;white-space:nowrap}

/* Foco de teclado visible en TODAS las paletas. Sin esto, quien navega con
   tabulador no sabe dónde está. */
:focus-visible{
  outline:2px solid var(--ll-acento-texto);
  outline-offset:3px;border-radius:4px}

/* Las filas que deben partirse en móvil. Requiere elem_classes="ll-fila"
   en la Row correspondiente de ui.py: NO apuntes a las clases internas de
   Gradio, cambian entre versiones. */
@media (max-width:640px){
  .ll-fila{flex-wrap:wrap !important}
  .ll-fila>*{min-width:100% !important}
}

/* El h1 con degradado desaparece en alto contraste forzado. Red de
   seguridad. */
@media (forced-colors: active){
  h1{-webkit-text-fill-color:CanvasText;color:CanvasText;
     background:none;filter:none}
}

/* Nada se mueve si el sistema pide que nada se mueva. */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{
    animation-duration:.01ms !important;
    transition-duration:.01ms !important}
}
```

### 8.5 Neón, hecho bien

```css
/* El resplandor va SIEMPRE en el contenedor, nunca en el texto. */
.block,.form,.panel,.gr-box{
  box-shadow:0 0 0 1px var(--ll-borde),
             0 8px 34px -18px var(--ll-halo)}

button.primary,.primary button{
  box-shadow:0 0 0 1px var(--ll-borde),
             0 0 22px -6px var(--ll-sombra-titulo)}
button.primary:hover,.primary button:hover{
  box-shadow:0 0 0 1px var(--ll-acento),
             0 0 30px -4px var(--ll-sombra-titulo)}

/* La pestaña activa: el color es ADORNO, el subrayado grueso es la
   información. Quien no distinga el matiz sigue sabiendo dónde está. */
.tab-nav button.selected{
  color:var(--ll-acento-texto) !important;
  font-weight:650;
  border-bottom:3px solid var(--ll-acento) !important;
  text-shadow:none}          /* nunca resplandor sobre texto */

/* Barra de progreso del capítulo: fija sobre el viewport (no sticky:
   el contenedor de Gradio tiene overflow:hidden). La mueve el JS de §8.6. */
#ll-progreso{
  position:fixed;top:0;left:0;height:3px;width:0;z-index:9999;
  background:linear-gradient(90deg,var(--ll-acento-hondo),var(--ll-acento));
  box-shadow:0 0 12px -2px var(--ll-acento);
  transition:width .08s linear;pointer-events:none}
```

### 8.6 Progreso del capítulo y posición dentro del capítulo

JavaScript puro, se engancha igual que `JS_SELECCION` (`demo.load(None, None,
None, js=…)`), cero cambios en Python. Boceto:

```javascript
() => {
  if (window.__llProg) return;
  window.__llProg = true;

  var barra = document.createElement('div');
  barra.id = 'll-progreso';
  document.body.appendChild(barra);

  function pintar() {
    var h = document.documentElement;
    var total = h.scrollHeight - h.clientHeight;
    var f = total > 0 ? h.scrollTop / total : 0;
    barra.style.width = (f * 100).toFixed(1) + '%';
    guardar(f);
  }

  // Dónde se quedó DENTRO del capítulo. La clave incluye el título del
  // capítulo para no restaurar la posición de un capítulo en otro.
  var clave = null, espera = null;
  function claveActual() {
    var l = document.querySelector('#ll-lector');
    if (!l) return null;
    return 'll:' + (l.textContent || '').slice(0, 80);
  }
  function guardar(f) {
    clearTimeout(espera);
    espera = setTimeout(function () {
      try { if (clave) localStorage.setItem(clave, String(f)); } catch (e) {}
    }, 400);
  }
  // Al cambiar de capítulo, Gradio redibuja #ll-lector: se detecta con
  // MutationObserver y se restaura la fracción guardada.
  new MutationObserver(function () {
    var k = claveActual();
    if (!k || k === clave) return;
    clave = k;
    try {
      var f = parseFloat(localStorage.getItem(k) || '0');
      if (f > 0.02 && f < 0.98) {
        var h = document.documentElement;
        h.scrollTop = f * (h.scrollHeight - h.clientHeight);
      }
    } catch (e) {}
  }).observe(document.body, { childList: true, subtree: true });

  addEventListener('scroll', pintar, { passive: true });
  pintar();
}
```

**[opinión]** Restaurar la posición solo si está entre el 2% y el 98% evita el
caso irritante de "abro un capítulo nuevo y me manda al final".

---

## 9. Las dos paletas nuevas

Ambas están calculadas con **el mismo algoritmo exacto** que
`pruebas_extremas.py::_contraste_suficiente` (luminancia relativa WCAG, alfa
descartado en `rgba`, igual que hace la prueba). **[medido]**

### 9.1 `neon` — azul neón sobre azul-negro (la que pide Miguel)

Minimalista, futurista, azul, con un solo acento de neón. Fondo azul-negro y
**no** negro puro, siguiendo la recomendación de Material (§3.4).

```python
    "neon": {
        "nombre": "Neón",
        "pista": "azul de neón sobre azul-negro, minimalista",
        "estrellas": True,
        "vars": {
            "--ll-fondo": "#070c18",
            "--ll-fondo-alto": "#0a1120",
            "--ll-fondo-bajo": "#0d182c",
            "--ll-panel": "rgba(14,24,44,.66)",
            "--ll-borde": "rgba(86,200,255,.22)",
            "--ll-acento": "#56c8ff",
            "--ll-acento-hondo": "#0f5c9e",
            "--ll-acento-claro": "#8fdcff",
            "--ll-acento-texto": "#56c8ff",
            "--ll-texto": "#d3e2f4",
            "--ll-lector-fondo": "rgba(11,18,34,.72)",
            "--ll-lector-texto": "#d8e5f4",
            "--ll-seleccion": "rgba(86,200,255,.34)",
            "--ll-halo": "rgba(30,120,220,.26)",
            "--ll-titulo-1": "#eaf6ff",
            "--ll-titulo-2": "#7fd4ff",
            "--ll-titulo-3": "#3f8fe0",
            "--ll-sombra-titulo": "rgba(80,190,255,.38)",
            "--ll-boton-alto": "#1a72b0",
            "--ll-boton-texto": "#f2fbff",
        },
    },
```

**Ratios medidos:**

| par | ratio | AA (4.5:1) |
|---|---|---|
| **interfaz** `texto` / `fondo` *(el que mide la prueba)* | **14.84 : 1** | ✔ |
| **lector** `lector-texto` / `lector-fondo` *(el que mide la prueba)* | **14.62 : 1** | ✔ |
| `texto` / `panel` | 13.46 : 1 | ✔ |
| `boton-texto` / `boton-alto` (arriba del degradado) | **4.91 : 1** | ✔ |
| `boton-texto` / `acento-hondo` (abajo del degradado) | 6.57 : 1 | ✔ |
| `acento-texto` / `fondo` (pestaña activa, enlaces) | 10.33 : 1 | ✔ |
| `acento-texto` / `panel` | 9.36 : 1 | ✔ |
| `acento-texto` / `lector-fondo` | 9.88 : 1 | ✔ |
| `titulo-3` / `fondo` (extremo del degradado del h1) | 5.78 : 1 | ✔ |
| `titulo-1` / `fondo` | 17.79 : 1 | ✔ |

Ninguno baja de 4.5:1. Pasa la prueba «todas las paletas son legibles».

**Nota de ajuste:** la primera versión que probé tenía `--ll-boton-alto:#1f7fc0`
y daba **4.12 : 1** — por debajo de AA. Lo oscurecí a `#1a72b0` hasta llegar a
4.91. Lo cuento porque es exactamente lo que pediste que hiciera si no llegaba.

### 9.2 `cristal` — el mismo azul, en claro

Misma identidad (azul, esquinas muy redondeadas, mucho aire) pero en polaridad
clara, que es la que la evidencia favorece para lectura prolongada (§3.4).
Sin resplandor: en claro el neón no brilla, ensucia (§6.1, regla 3).

```python
    "cristal": {
        "nombre": "Cristal",
        "pista": "el mismo azul, en claro: para leer horas de día",
        "estrellas": False,
        "vars": {
            "--ll-fondo": "#eef3fa",
            "--ll-fondo-alto": "#f5f9fd",
            "--ll-fondo-bajo": "#e4edf7",
            "--ll-panel": "rgba(255,255,255,.82)",
            "--ll-borde": "rgba(18,86,140,.18)",
            "--ll-acento": "#0e6ea6",
            "--ll-acento-hondo": "#07507c",
            "--ll-acento-claro": "#3fa6dd",
            "--ll-acento-texto": "#0a5c8c",
            "--ll-texto": "#1e2c3a",
            "--ll-lector-fondo": "rgba(253,254,255,.95)",
            "--ll-lector-texto": "#232f3c",
            "--ll-seleccion": "rgba(63,166,221,.34)",
            "--ll-halo": "rgba(90,165,225,.16)",
            "--ll-titulo-1": "#07507c",
            "--ll-titulo-2": "#0e6ea6",
            "--ll-titulo-3": "#2b8fc9",
            "--ll-sombra-titulo": "rgba(63,166,221,.28)",
            "--ll-boton-alto": "#0e6ea6",
            "--ll-boton-texto": "#ffffff",
        },
    },
```

**Ratios medidos:**

| par | ratio | AA (4.5:1) |
|---|---|---|
| **interfaz** `texto` / `fondo` *(prueba)* | **12.76 : 1** | ✔ |
| **lector** `lector-texto` / `lector-fondo` *(prueba)* | **13.48 : 1** | ✔ |
| `texto` / `panel` | 14.22 : 1 | ✔ |
| `boton-texto` / `boton-alto` | **5.53 : 1** | ✔ |
| `boton-texto` / `acento-hondo` | 8.58 : 1 | ✔ |
| `acento-texto` / `fondo` | 6.45 : 1 | ✔ |
| `acento-texto` / `panel` | 7.19 : 1 | ✔ |
| `acento-texto` / `lector-fondo` | 7.12 : 1 | ✔ |
| `titulo-1` / `fondo` | 7.70 : 1 | ✔ |
| `titulo-3` / `fondo` | 3.21 : 1 | ⚠ **solo texto grande** |

`titulo-3` a 3.21:1 cumple el mínimo de **3:1 para texto grande** (WCAG 1.4.3),
y solo se usa como extremo del degradado del `h1`, que es texto grande. Para
referencia, las paletas claras actuales tienen ese mismo valor mucho peor:
`amanecer` 2.13:1 y `menta` 1.87:1. **[medido]**

Ni `lector-texto` ni `texto` son negro puro: `#232f3c` y `#1e2c3a`, azul muy
oscuro. Mantiene la identidad azul y evita el 21:1 del negro sobre blanco.

### 9.3 Lo que hay que hacer para que la prueba siga pasando

1. Añadir **`--ll-acento-texto`** a **las cinco paletas existentes** con estos
   valores **[medidos]**, o la prueba «todas definen las mismas variables» falla:
   - `hielo`: `#8fd3e8` (= su `--ll-acento`, 12.13:1 sobre el fondo) ✔
   - `medianoche`: `#c9b6e4` (= su `--ll-acento`, 9.77:1) ✔
   - `amanecer`: `#a4522a` (= su `--ll-acento-hondo`, 5.13:1) ✔
   - `menta`: `#3a7a61` (= su `--ll-acento-hondo`, 4.80:1) ✔
   - `papel`: `#6b5333` (= su `--ll-acento-hondo`, 6.41:1) ✔
2. Corregir `--ll-boton-alto` en las cinco (tabla de §2.1).
3. **Ampliar la prueba** para que cubra los pares que hoy no mira. Sugerencia
   de qué añadir al diccionario de `_contraste_suficiente`:
   ```python
   "panel":        ("--ll-texto",        "--ll-panel"),
   "boton":        ("--ll-boton-texto",  "--ll-boton-alto"),
   "boton-hondo":  ("--ll-boton-texto",  "--ll-acento-hondo"),
   "acento-texto": ("--ll-acento-texto", "--ll-fondo"),
   ```
   Si se añaden **antes** de corregir los valores, la prueba se pondrá roja en
   las cinco paletas. Eso no es un fallo de la prueba: es el defecto de §2.1
   saliendo a la luz. Corrige primero los colores, o hazlo en el mismo commit.

---

## 10. Lista priorizada de cambios de interfaz

Ordenada por **mejora percibida ÷ esfuerzo**. Los cinco primeros son los que
haría aunque no quedara tiempo para nada más.

| # | Cambio | Problema (§) | Esfuerzo | Mejora |
|---|---|---|---|---|
| 1 | Quitar `max-height:62vh` del lector | 2.5 doble scroll en móvil | 1 línea | **Muy alta** |
| 2 | `max-width:62ch` + `margin:auto` en `#ll-lector p` | 2.6 líneas de 130 caracteres | 2 líneas | **Muy alta** |
| 3 | `text-align:left`, fuera `justify` y `hyphens` | 2.4 WCAG 1.4.8 | 2 líneas | Alta |
| 4 | Corregir `--ll-boton-alto` en las 5 paletas | 2.1 fallo AA real medido | 5 valores | Alta (accesibilidad) |
| 5 | `min-height:48px` en botones, pestañas y fichas + `font-size:16px` en inputs | 7.1, 7.2 pulgar y zoom de iOS | 6 líneas | **Muy alta en móvil** |
| 6 | Paletas `neon` y `cristal` + `--ll-acento-texto` en todas | Lo que pide Miguel; 2.2 | ~50 líneas | Alta |
| 7 | Barra de pestañas deslizable en móvil | 7.2 se desborda a 390 px | 6 líneas CSS | Alta en móvil |
| 8 | Selector de tamaño de letra (con la medida ajustándose) | 3.3, §4 libertad del usuario | ~15 líneas | Alta |
| 9 | `:focus-visible` visible en todas las paletas | 6.1 regla 4; accesibilidad de teclado | 3 líneas | Media-alta |
| 10 | Barra de progreso del capítulo | §4, §5.1 progreso honesto | ~20 líneas JS + CSS | Media-alta |
| 11 | "Continuar donde lo dejaste" arriba, al abrir, sin pulsar nada | 5.1 punto 1; ya hay datos | ~10 líneas Python | **Alta** |
| 12 | Posición dentro del capítulo con `localStorage` | §4 | ~25 líneas JS | Media |
| 13 | `gr.BrowserState` con `storage_key` y `secret` fijos | §8.3 preferencias que se pierden | ~10 líneas | Media |
| 14 | `elem_classes="ll-fila"` + `flex-wrap` en las Row del lector | 7.2 punto 1 | 3 líneas | Media |
| 15 | `prefers-reduced-motion` y `forced-colors` | 2.8, 6.1 regla 5 | 8 líneas | Media (baja frecuencia, alto impacto en quien la necesita) |
| 16 | Interfaz en `system-ui`, lector en serif | 3.5 "se siente antigua" | 2 líneas | Media |
| 17 | Ampliar `_contraste_suficiente` a los pares nuevos | 9.3 | 4 líneas | Media (evita recaídas) |
| 18 | Modo sin distracciones | §4 | ~15 líneas | Baja-media |

El 1, 2, 3 y 5 son **once líneas de CSS en total** y resuelven las tres cosas
que dijo Esmeralda. Si mañana solo hay media hora, es eso.

---

## 11. Lo que NO hay que hacer, y por qué

1. **No reescribas `ui.py`.** Es de Claude Code según `AGENTS.md` y sus
   comentarios registran decisiones que costaron descubrir (el `selectionchange`
   de iOS, la carga perezosa, el `.select` en vez de `.change` para evitar el
   bucle del índice). Un rediseño desde cero las pierde todas.
2. **No metas fuentes de Google Fonts ni CSS remoto.** Añaden una petición
   bloqueante y rompen la regla de degradación elegante del proyecto. Con
   `system-ui` y una pila de serifs del sistema se llega igual.
3. **No pongas `maximum-scale=1` ni `user-scalable=no`** para evitar el zoom
   de iOS. Impide ampliar con los dedos y viola WCAG 1.4.4. El arreglo correcto
   es `font-size:16px` en los campos.
4. **No uses `text-shadow` de neón sobre el texto que hay que leer.** Difumina
   el borde de la letra y baja el contraste efectivo, aunque el ratio calculado
   siga saliendo bien.
5. **No confíes solo en el ratio de contraste con colores muy saturados.** El
   cálculo de WCAG es de luminancia y no modela la vibración cromática. Por eso
   Material recomienda desaturar en tema oscuro.
6. **No añadas una variable CSS a una paleta sola.** La prueba exige que las
   siete definan exactamente el mismo conjunto (§9.3).
7. **No apuntes a las clases internas de Gradio** (`svelte-xxxx`,
   `gradio-container-6-26-0`). Cambian entre versiones. Usa `elem_id` y
   `elem_classes`, que es lo que ya hace bien la app con `#ll-lector`,
   `#ll-palabra`, `#ll-indice`.
8. **No pases este CSS por `launch(css=…)`.** **[medido]** Gradio 6.26 reescribe
   esas reglas prefijándolas con `.gradio-container.gradio-container-6.26.0 .contain `,
   y los selectores globales dejan de funcionar. El `gr.HTML("<style>…")` que ya
   usa la app es lo correcto.
9. **No pongas racha con castigo.** Ni animación de pérdida, ni "has perdido 47
   días", ni notificaciones. Es *Addictive Design* y *Fake urgency* en el
   catálogo de patrones oscuros (§5.2). Y en una app que se ejecuta en local no
   hay siquiera a quién notificar.
10. **No uses las cifras de retención de Duolingo en la presentación.** Vienen
    de blogs de agencias de marketing; no las he podido verificar en fuente
    primaria (§5.2). Si Miguel las dice en la defensa y alguien pregunta de
    dónde salen, no hay respuesta.
11. **No quites el modo oscuro** aunque la evidencia favorezca el claro. NN/g
    recomienda explícitamente **ofrecer** el oscuro; hay lectores (medios
    oculares turbios, luz baja) para los que es mejor. La respuesta es elegir,
    no imponer.
12. **No apiles `backdrop-filter:blur()`.** Ya hay uno en `.block`; encadenar
    capas de desenfoque destruye el contraste real contra un fondo que deja de
    ser predecible, y en móvil cuesta batería.
13. **No implementes paginación** al estilo Kindle. Sobre HTML fluido con
    tamaño de letra variable es caro y frágil; Instapaper y Pocket usan scroll
    continuo con progreso visible y les basta.
14. **No hagas del `gr.Dropdown` de 366 capítulos el control principal en
    móvil.** El acordeón con `gr.Radio` que ya existe es mejor; solo hay que
    darle la vuelta a las prioridades.

---

## 12. Fuentes

**Tipografía y legibilidad**
- Matthew Butterick, *Practical Typography* — [Line length](https://practicaltypography.com/line-length.html)
- Baymard Institute — [Readability: The Optimal Line Length](https://baymard.com/blog/line-length-readability)
- Legge, G. E. & Bigelow, C. A. (2011). *Does print size matter for reading? A review of findings from vision science and typography*. Journal of Vision, 11(5). — [ARVO](https://jov.arvojournals.org/article.aspx?articleid=2191906) · [PDF](https://graphicdesign-research.com/images/LeggeBiglow-2011.pdf)
- *Overview of research: Type* — [legible-typography.com](https://legible-typography.com/en/5-overview-of-research-type)
- *How Serif and Sans Serif Typefaces Influence Reading on Screen: An Eye Tracking Study* — [Springer](https://link.springer.com/chapter/10.1007/978-3-319-40355-7_55)
- *How does serif vs sans serif typeface impact the usability of e-commerce websites?* — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9680897/)

**Accesibilidad y normas**
- W3C, WCAG 2.2 — [SC 1.4.8 Visual Presentation (AAA)](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html)
- W3C, WCAG 2.2 — [SC 1.4.12 Text Spacing (AA)](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)
- W3C, WCAG 2.2 — [SC 2.5.8 Target Size Minimum (AA)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- W3C, WCAG 2.2 — [SC 2.5.5 Target Size Enhanced (AAA)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)
- Google — [Touch target size, Android Accessibility Help](https://support.google.com/accessibility/android/answer/7101858?hl=en)
- Apple — [Human Interface Guidelines: Typography](https://developer.apple.com/design/human-interface-guidelines/typography) *(cifras 11 pt / 17 pt vía fuentes secundarias; la página no se pudo extraer)*

**Modo oscuro y color**
- Nielsen Norman Group — [Dark Mode vs. Light Mode: Which Is Better?](https://www.nngroup.com/articles/dark-mode/) (resume Piepenbrock et al. 2013, Dobres et al. 2017, Legge et al. 1985)
- Google Codelabs — [Design a dark theme with Material and Figma](https://codelabs.developers.google.com/codelabs/design-material-darktheme)

**Móvil y web**
- CSS-Tricks — [16px or Larger Text Prevents iOS Form Zoom](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/)

**Retención y patrones oscuros**
- Harry Brignull — [Types of deceptive pattern](https://www.deceptive.design/types)
- Nielsen Norman Group — [Don't Trick Users: 2 Ways to Avoid Deceptive Design Patterns](https://www.nngroup.com/videos/avoid-deceptive-patterns/)
- *A Longitudinal Analysis of Gamification in Untappd: Ethical Reflections on a Social Drinking Application* — [arXiv](https://arxiv.org/pdf/2601.04841)
- *The Problem with Metrics is a Fundamental Problem for AI* — [arXiv](https://arxiv.org/pdf/2002.08512)

**Del propio repositorio (medido, no citado de fuera)**
- `app/paletas.py` — las cinco paletas y sus 19 variables
- `app/ui.py` — `_CSS_GLOBAL` (líneas ~254-310), `_CSS_LECTOR` y `_html_lectura` (~631-655), `JS_SELECCION` (~657+), montaje de la interfaz (~1971-2300)
- `app/biblioteca.py` — `Entrada.avance`, `listar()`, `anotar()`
- `pruebas_extremas.py` — `_contraste_suficiente` (~762-794) y la prueba «todas definen las mismas variables»
- Gradio 6.26 instalado: `Blocks.__init__` (deprecación de `css`/`js`/`head`/`theme` hacia `launch()`), `components/browser_state.py`, `templates/frontend/index.html`, `templates/frontend/assets/core-*.css`
