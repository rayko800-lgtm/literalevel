# LiteraLevel con una sola mano

**Cómo usar la app entera con el pulgar y cómo comprobarlo.**

Fecha: 13 de septiembre de 2026. Es un documento de investigación: no toca
código.

**Etiquetas.** **[verificado]**: fuente consultada, en las referencias.
**[secundaria]**: solo en terceros o en el extracto de un buscador.
**[código]**: leído en `front/src`, no medido en un navegador.
**[calculado]**: cuenta mía. **[opinión]**: criterio mío con su argumento.
**No verificado**: no se usa como argumento.

**Qué no se repite.** `diseno_lector.md` §7 ya da los tamaños mínimos de las
normas, los 16 px de los campos y la barra de pestañas. `retencion_movil.md`
§4.2 ya propone ocultar la barra inferior al bajar y `overscroll-behavior`.
Aquí se añade **dónde** va cada control, con qué gesto y cómo se mide. Hay un
cambio: `retencion_movil.md` descartaba pasar de capítulo deslizando, pero el
front **ya pasa página deslizando** en el modo por páginas [código]. Por eso
§2.4 no discute si hay gesto, sino cómo acotarlo.

---

## 0. Las diez reglas que más cambian

1. **Lector: barra de lectura abajo**, encima de la navegación, con
   «‹ Anterior · Índice · Aa · Siguiente ›». En el modo seguido, las flechas
   hoy solo están arriba y miden 40 px.
2. **Anterior y siguiente: 56 px y siempre en el mismo sitio.** Se tocan en
   serie.
3. **Deslizar para pasar página, solo si el gesto nace a más de 24 px del
   borde lateral.** Nunca en el modo seguido ni con texto seleccionado.
4. **Nada primario en el 25 % superior de la pantalla.** Lo que quede arriba es
   un duplicado.
5. **Toda hoja inferior se cierra desde abajo:** «Cerrar» en el pie fijo,
   arrastrar hacia abajo, velo o Escape.
6. **Índice y «Aa», en hojas inferiores.** Hoy son un cajón lateral y el panel
   global de ajustes.
7. **Pronunciar: barra de acción fija abajo** con «Escuchar · Grabar/Parar ·
   Otra frase». El micrófono mide 72 px, va en el centro y no se mueve.
8. **El teclado no tapa nada:** con un campo enfocado se esconden las barras
   fijas, y el campo y su botón quedan dentro del `visualViewport`.
9. **Todo lo fijo abajo suma `env(safe-area-inset-bottom)`**, y el borde
   inferior no lleva gestos propios.
10. **Sin interruptor de zurdos:** controles centrados o en pares simétricos.

---

## 1. Evidencia

### 1.1 Cómo se sujeta el teléfono

- **Hoober (2013a)** [verificado] observó 1.333 usos en la calle, 780 tocando
  la pantalla: **49 % con una mano, 36 % acunado y 15 % con las dos**. Con una
  mano, el 67 % usaba el pulgar derecho y el **33 % el izquierdo**; al acunar,
  el 79 % sujetaba con la izquierda. Además, el agarre cambia «muy a menudo, a
  veces cada pocos segundos».
- **Hoober (2017)** [verificado]: «el 75 % de los usuarios toca la pantalla
  solo con un pulgar».
- **Clark (2015)**: con *phablets* se usan las dos manos el 70 % del tiempo,
  aunque el pulgar sigue tocando el 60 % **[secundaria: no hallé la fuente
  primaria]**. Eardley et al. (2017) [verificado, resumen] muestran que el
  agarre y la inclinación cambian según la tarea.
- **Hueco:** no encontré una observación de campo reciente con teléfonos de
  6,1–6,7″. **El 49 % es de 2013.** Las pantallas grandes traen más cambios de
  agarre, y eso refuerza la regla; no invento una cifra nueva.

**[opinión]** «Con una mano» es el **peor caso frecuente**: una estudiante de
pie en el autobús. Si funciona así, funciona acunado y con dos manos.

### 1.2 Hasta dónde llega el pulgar

- **Bergstrom-Lehtovirta y Oulasvirta (2014)** [verificado, texto leído]
  modelan el **área funcional del pulgar**. Depende del tamaño de la pantalla,
  del tamaño de la mano y de dónde apoya el índice detrás: *«cuanto mayor la
  pantalla y menor la mano, menor es esta área en proporción»*. Fuera de ella
  hay que cambiar de agarre. Recomiendan no poner elementos cerca de los
  extremos del alcance.
- **Kim y Ji (2019)** [verificado, resumen]: en teléfonos de 4,7–5,2″, la zona
  natural del pulgar es **más del 50 %** de la pantalla con pulgar grande y
  **en torno al 30 %** con pequeño o mediano. Todos evitaban la franja inferior
  y la zona superior izquierda.
- **Le et al. (2018)** [verificado, resumen]: a mayor teléfono, **el agarre sube
  hacia el borde superior**. **Park y Han (2010)** [verificado, resumen]: el
  **borde inferior** es menos preciso.
- **Clark (2015)** [verificado]: *«arriba frente a abajo importa más que
  izquierda frente a derecha»*. Lo esencial va en el centro, donde se solapan
  las zonas de los dos pulgares.

**Diestro y zurdo [opinión con esa base]:** el pulgar derecho barre la parte
baja e izquierda y el izquierdo la baja y derecha. La intersección es **la
franja central-baja**, y ahí van los primarios.

### 1.3 Dónde se acierta

- **Hoober (2013b, 2017)** [verificado]: se mira y se toca sobre todo **el
  centro**. Para acertar el 95 % bastan **7 mm en el centro**, pero hacen falta
  **~12 mm en las esquinas**. Pide **≥ 8 mm entre centros** y advierte que en
  los bordes se acierta peor: con el dedo, el borde no «regala» tamaño como con
  el ratón.
- **Samsung (s. f.)** [verificado, PDF leído]: One UI separa un **área de
  visión** arriba, sin nada que tocar, de un **área de interacción** abajo. El
  límite es *«la altura que un dedo alcanza con más facilidad»*, y los diálogos
  suben desde abajo «para que el dedo llegue».

### 1.4 Tamaño del objetivo

| Fuente | Cifra |
|---|---|
| WCAG 2.2, SC 2.5.8 (AA) [verificado] | 24 × 24 px CSS, o círculos de 24 px que no se toquen: es el suelo |
| Apple HIG, *Accessibility* [verificado] | **44 × 44 pt por defecto**, 28 pt de mínimo; **~12 pt de separación** con borde y ~24 pt sin él |
| Android Accessibility Help [verificado] | **48 × 48 dp (~9 mm)**, separados **≥ 8 dp** |
| Parhi, Karlson y Bederson (2006) [verificado, resumen] | **9,2 mm** para toques sueltos con el pulgar |

**[calculado]** En un iPhone de 390 × 844 (460 ppp, factor 3), 1 px CSS ≈
**0,166 mm**: **44 px ≈ 7,3 mm; 48 px ≈ 8 mm; 56 px ≈ 9,3 mm; 72 px ≈ 12 mm**.
En Android, a 360 px de ancho, algo más por px, según el modelo.

### 1.5 Fitts aplicado al pulgar

El tiempo de apuntar crece con log₂(D/W + 1) (Fitts, 1954) [verificado]. Con el
pulgar hay tres matices:

1. **D se mide desde el reposo del pulgar** (abajo y a un lado), no desde el
   control anterior. Fuera del área funcional, el coste es cambiar de agarre.
2. **W tiene suelo:** el dedo tiene una imprecisión absoluta que no se corrige
   yendo despacio (Bi et al., 2013) [verificado].
3. **Repetir cuesta D ≈ 0 solo si el objetivo no se mueve:** anterior y
   siguiente, grabar y parar.

---

## 2. Patrones

**2.1 Navegación inferior.** Material pide **de tres a cinco destinos, abajo**
(Material Components, s. f.-b) [verificado]. Los cuatro de LiteraLevel se
quedan. **[código]** Ya mide 54 px, suma la zona segura y se esconde al bajar.
**Regla:** lo que se esconde vuelve con un gesto, y los botones de capítulo no
dependen de que la barra se vea.

**2.2 Hojas inferiores.** Son *«una alternativa a los menús en línea y a los
diálogos simples en el móvil»* y se cierran tocando fuera o arrastrando hacia
abajo (Material Components, s. f.-a) [verificado]. Lo que falla aunque sea
hoja es la X de arriba: con la hoja de palabra al 74 % de alto, la X cae en el
26 % superior [código]. **Regla:** el cierre y la acción van en un **pie fijo**,
y la hoja abre a ≤ 60 % de alto y se expande arrastrando.

**2.3 Botón flotante.** **[opinión]** En un lector tapa texto, y solo
Pronunciar tiene una acción única. **Regla:** sin FAB sobre el contenido; la
acción principal va en una barra fija inferior.

**2.4 Deslizar.**
- **Android** [verificado]: *volver* es deslizar hacia dentro desde cualquier
  borde lateral. *Inicio* va en el borde inferior y **las apps no pueden
  excluirlo**. Las nativas pueden reservar solo 200 dp por borde lateral
  **[secundaria]**; una web, nada.
- **Safari en iOS**: deslizar desde el borde izquierdo va atrás en el historial
  **[secundaria]**, y en el lector eso saca del capítulo.
- **Selección:** consultar es mantener pulsado y arrastrar los tiradores; un
  deslizamiento que pase página a mitad rompe la función estrella.
- **[código]** `alSoltarToque` pasa página con |dx| > 50 px o con un toque en
  el 30 % lateral, ignora el gesto si hay selección y usa `touch-action:
  pan-y`. Está bien, pero **no descarta los gestos nacidos en el borde**.

**Reglas:** se ignora el gesto si el `pointerdown` cae a ≤ 24 px de un borde
lateral o a ≤ 32 px del inferior; no hay gesto en el modo seguido; todo gesto
tiene su botón; y nada se borra solo deslizando.

**2.5 Reachability.** En iPhone con Face ID se activa **deslizando hacia abajo
en el borde inferior** **[secundaria: extracto de Apple Support]**. Android 12
trae un modo equivalente **[secundaria]**. **[opinión]** Es red de seguridad,
no diseño: no se cuenta con ella y **el borde inferior no lleva gestos
propios**.

**2.6 Esquinas superiores.** Son lo más lejano (§1.2) y lo menos preciso
(§1.3). **[código]** Hoy arriba a la derecha están Ajustes, el perfil, las
herramientas del lector y la X de hojas y paneles; arriba a la izquierda,
«volver al libro» y «Pregunta anterior». **Regla:** en el 25 % superior solo
van títulos, estado y duplicados.

**2.7 Zona segura.** Con `viewport-fit=cover`, el contenido llega bajo la barra
de inicio. Se protege con `env(safe-area-inset-bottom)` y `max()` para un
mínimo (Horton, 2017; MDN, s. f.-a) [verificado]. **[código]** Ya se hace en la
navegación, la hoja de palabra, el índice y los ajustes. **Regla:**
`padding-bottom: max(8px, env(safe-area-inset-bottom))` en todo lo fijo abajo,
también en las barras nuevas.

**2.8 Teclado.** Desde Chrome 108 en Android, abrir el teclado solo reduce el
viewport visual, y lo `position: fixed` **se queda y puede quedar tapado**,
como en iOS (Chrome for Developers, 2022) [verificado].
`interactive-widget=resizes-content` no existe en Safari, y la VirtualKeyboard
API es experimental y solo de Chromium (MDN, s. f.-b) [verificado]. **[código]**
Casos: «Consultar otra palabra» en el pie de la hoja, la frase de Pronunciar, el
buscador, entrar en Ajustes y la muestra de Tu nivel. **Regla:** con el campo
enfocado se esconden las barras fijas, un oyente de `visualViewport` mantiene
visibles el campo y su botón, y se puede enviar con la tecla del teclado.

**2.9 Zurdos.** El 33 % de quien usa una mano usa la izquierda (Hoober, 2013a).
Adaptar la barra de acciones ayudó sobre todo a la mano no dominante (Mehrotra
et al., 2022) [verificado; preprint]. **[opinión]** Un interruptor que nadie
encuentra no lo resuelve; lo resuelve una maqueta **centrada o simétrica**. Si
aparece un control asimétrico, entonces se añade el espejo en Ajustes.

---

## 3. Reglas pantalla por pantalla

**Zonas [opinión basada en §1]**, en fracción del alto medida desde arriba:
**A** 0–25 %, lectura y títulos; **B** 25–40 %, secundarios; **C** 40–90 %,
primarios; **D**, navegación y zona segura, sin gestos. *Primario* significa
que la tarea no se completa sin tocarlo.

**Tamaños:** primarios ≥ 48 px; tocados en serie ≥ 56 px; cualquier otro
objetivo ≥ 44 px; hueco ≥ 8 px.

### 3.1 Lector

Hoy [código]: las herramientas y el volver están arriba. En el modo seguido,
Anterior y Siguiente (40 px) solo aparecen al empezar y al terminar el
capítulo. En el modo páginas, las flechas del paginador (48 px) ya caen en la
zona C.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Anterior / siguiente | Barra de lectura fija sobre la navegación, en los extremos, a ≥ 16 px del borde | **56** | Modo páginas: deslizar desde > 24 px del borde; toque en el 30 % lateral | En serie; simétrico |
| Índice | Centro de la barra; **hoja inferior** al 60 %, desplazada al capítulo actual | 48 | Arrastrar el asa | Hoy es un cajón a pantalla completa con la X arriba |
| Tamaño de letra (Aa) | Centro de la barra; **hoja propia**: 4 tamaños, modo y tema | 48 | — | Hoy abre los ajustes globales, que empiezan por los colores |
| Consultar palabra | Sobre el texto; la ficha sube como hoja | La línea (excepción *inline* de 2.5.8) | Mantener pulsado | Lo que se agranda es la ficha |
| Volver al libro | En la hoja del índice y en la barra si cabe; el enlace de arriba queda como duplicado | 48 | *Volver* del sistema, sin depender de él | Esquina superior |
| Mostrar/ocultar la barra | Toque corto en el 40 % central del texto | La franja | Subir un poco | Retardo de 350 ms para no chocar con el doble toque |

### 3.2 Ficha de palabra

Hoy [código]: X arriba, US/UK de 40 px y el campo de otra palabra al pie.
Guardar es implícito: consultar ya anota en el cuaderno.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Escuchar US / UK | Primera fila; con la hoja a ≤ 60 % cae en C | 48 | — | La acción más repetida |
| Cerrar | **Pie fijo**, a la izquierda; X arriba como duplicado | 48 | Arrastrar hacia abajo; velo; Escape | §2.2 |
| Guardar / quitar (si se hace explícito) | Pie fijo, a la derecha, con estado «Guardada ✓» | 48 | Nunca solo deslizar | Junto al pulgar |
| Consultar otra palabra | Pie; al enfocar, la hoja sube con el `visualViewport` | 48 | Tecla «Buscar» | §2.8 |

### 3.3 Encontrar

Hoy [código]: buscador de 58 px arriba, pestañas de 42 px, interruptor de nivel
de 44 px e ideas de 40 px.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Búsqueda | Arriba en la maqueta; con resultados, píldora «Nueva búsqueda» abajo en el centro que sube y enfoca el campo | 56 / 48 | Tecla «Buscar» (`enterkeyhint` ya existe) | Lo caro es alcanzar el campo, no escribir |
| Pestañas y filtros | Bajo el buscador; si hay filtros reales, «Filtros» abajo, en hoja con «Ver N libros» en el pie | 48 | — | Hoy 42 px |
| Ordenar por mi nivel | Fila entera tocable | 48 | — | La casilla mide 20 px |
| Ideas | Chips con hueco de 8 px | 44 | — | Hoy 40 px |
| Quitar de mis libros | Botón con deshacer | 48 | Nunca solo deslizar | Destructivo |

### 3.4 Pronunciar

Hoy [código]: frase arriba y micrófono de 88 px en medio. «Otra frase» queda
**al final del resultado**, a veces muy abajo, y los fonemas miden 44 px.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Frase | Arriba (zona A); «Una frase de mi libro» y «Borrar» bajo el campo | 48 | — | Leer arriba y actuar abajo |
| Grabar / Parar | **Centro de la barra de acción fija**; el mismo botón cambia de icono | **72** | — | Primario y en serie: no se mueve |
| Corrígeme | Ocupa el sitio de Grabar cuando hay audio | 56 | — | El paso siguiente, en el mismo sitio |
| Escuchar la frase bien leída | Barra, a la izquierda | 48 | — | Simetría |
| Otra frase / Grabar otra vez | Barra, a la derecha | 48 | — | Hoy queda al final |
| Escuchar fonema | En su tarjeta, a la izquierda | 48 | — | Hoy 44 px |

Con el teclado abierto sobre la frase, la barra se oculta.

### 3.5 Tabla AFI

Hoy [código]: celdas de 76 × ~96 px, ficha del sonido en línea con la X arriba y
selector US/UK de 42 px.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Celda | Rejilla con hueco ≥ 8 px | 56 (ya cumple) | — | Se tocan muchas seguidas |
| Ficha del sonido | **Hoja inferior** a media altura; tocar otra celda la cambia sin mover la rejilla | — | Arrastrar para cerrar | Hoy desplaza el contenido |
| Escuchar otra vez | Pie de la hoja, en el centro | 56 | — | Acción repetida |
| US / UK | Cabecera de la hoja o encima de la rejilla | 48 | — | Hoy 42 px |

### 3.6 Mis palabras

Hoy [código]: tarjetas de 150 px que se voltean y una lista sin acciones. Ya
cumple.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Voltear | Toda la tarjeta | Tarjeta | — | Objetivo enorme |
| Escuchar (si se añade) | Parte baja de la tarjeta | 48 | — | Cerca del pulgar |
| Borrar (si se añade) | Menú de la fila, con deshacer | 48 | Deslizar solo como atajo, nunca desde el borde | Destructivo |

### 3.7 Tu nivel

Hoy [código]: opciones a todo el ancho, lo cual está bien. «Pregunta anterior»
va arriba a la izquierda.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Opciones | Como están | 52 de alto | — | Ya cumple |
| Atrás / Siguiente | **Pie fijo**: Atrás a la izquierda, Siguiente a la derecha | 56 | — | En serie; hoy Atrás en esquina |
| Me vale así, guardar | Pie fijo, sobre los dos | 48 | — | Salir sin estirarse |
| Ajustes y perfil | Fila nueva junto a «Mis palabras» | 56 de alto | — | §3.8 |

### 3.8 Ajustes y cuenta

Hoy [código]: icono de 48 px y chip de perfil de 36 px arriba a la derecha.
Abren un panel lateral con la X arriba.

| Control | Dónde va | Mínimo | Gesto opcional | Por qué |
|---|---|---|---|---|
| Abrir ajustes | Fila en **Tu nivel** y «Aa» en el lector; el icono de arriba queda como duplicado | 48 | — | Conserva las cuatro secciones sin un quinto destino |
| Panel | Hoja inferior hasta 760 px de ancho; cajón lateral en escritorio | — | Arrastrar para cerrar | §2.2 |
| Cerrar | Pie fijo | 48 | Velo; Escape | §2.6 |
| Entrar | Campos arriba de la hoja; botón visible sobre el teclado | 48 | Tecla «Ir» | §2.8 |
| Chip de perfil | Fuera de la cabecera en móvil, o 44 px | 44 | — | Hoy 36 px |

---

## 4. Lo que NO hacer

1. **Gestos que nacen en el borde lateral:** en Android es volver; en Safari,
   salir del capítulo.
2. **Gestos propios en el borde inferior:** inicio, Reachability y el modo a
   una mano son del sistema, y Android no deja excluirlos.
3. **El gesto de volver del sistema como única salida:** cada pantalla tiene su
   vuelta al alcance del pulgar. Que las PWA instaladas en iOS carezcan de ese
   gesto es no verificado; la regla vale igual.
4. **FAB sobre el texto:** tapa líneas y compite con la selección.
5. **Mover un botón entre estados** (grabar → parar, página N → N+1): el
   segundo toque deja de ser gratis.
6. **La X como único cierre de una hoja:** una hoja alta la sube a la zona A.
7. **Hojas que abren al 90 %:** mejor a media altura y expandibles.
8. **Borrar solo deslizando:** invisible y fácil de disparar sin querer.
9. **Un interruptor de zurdos para tapar una maqueta asimétrica:** se arregla
   la maqueta.
10. **`interactive-widget` o VirtualKeyboard como única defensa contra el
    teclado:** no existen en Safari.
11. **Los 24 px de 2.5.8 como objetivo:** es el suelo del AA, no el tamaño de un
    pulgar.

---

## 5. Cómo comprobarlo

### 5.1 Automatizable con Chrome

**Montaje:** emulación en Chrome (MCP `chrome-devtools` o Puppeteer) con **390
× 844** y **360 × 800**, DPR 3, `hasTouch` e `isMobile`. **Estados:** portada;
lector seguido (arriba y tras bajar 2.000 px) y por páginas; ficha de palabra;
índice; Encontrar con resultados; Pronunciar lista, grabada y con resultado;
AFI con ficha; Mis palabras; Tu nivel en cuestionario y resultado; ajustes
abiertos. **[opinión]** Marcar los primarios con `data-primario`, los tocados
en serie con `data-serie` y los duplicados de arriba con `data-duplicado`, para
no depender de clases.

| # | Comprobación | Criterio |
|---|---|---|
| 1 | Primarios en zona del pulgar | centro Y de cada `[data-primario]` visible entre **0,40·H** y H − 8 |
| 2 | Tamaño de primarios | ≥ **48 × 48**; `data-serie` ≥ **56**; micrófono ≥ 72 |
| 3 | Todo lo tocable (`button, a[href], input, select, textarea, summary, [role=button\|tab\|radio], label:has(input)`) | **error** si < 24 sin el espaciado de 2.5.8; **aviso** si < 44 |
| 4 | Separación | hueco entre cajas vecinas ≥ 8 px |
| 5 | Esquinas superiores | ningún objetivo sin `data-duplicado` con centro Y < 0,25·H y X < 0,25·W o > 0,75·W |
| 6 | Hojas | al abrir, borde superior ≥ 0,40·H; hay un cierre con centro Y ≥ 0,60·H; el velo cierra |
| 7 | Barra oculta | tras bajar 2.000 px, un scroll de −60 px deja Anterior/Siguiente cumpliendo 1 y 2 |
| 8 | Gesto desde el borde | modo páginas, `Input.dispatchTouchEvent` de x = 10 a 200: **no** pasa; de W/2 a W/2 − 150: **sí** |
| 9 | Gesto con selección | con una palabra seleccionada (`Selection.addRange`), deslizar **no** pasa |
| 10 | Zona segura | análisis estático: toda regla `position: fixed` con `bottom: 0` usa `safe-area-inset-bottom` en `padding-bottom` |
| 11 | Teclado (aproximación) | enfocar cada campo y reducir el alto a 0,58·H: campo y botón de enviar dentro; barras fijas ocultas |
| 12 | Desbordamiento | `scrollWidth ≤ innerWidth` en todos los estados |

**Límites:** la emulación no abre un teclado real ni reproduce el gesto de
volver. Tampoco verifiqué que emule la zona segura (de ahí que la 10 sea
estática). El 42 % de alto del teclado es una estimación.

### 5.2 Prueba con personas

- **Participantes:** cinco o seis, con al menos una **zurda** y una de **mano
  pequeña**, cada una con su teléfono (uno de ≥ 6,5″ y otro de ≤ 6,1″).
- **Condición:** de pie, con una mano y la otra ocupada con una bolsa. Cada
  tarea se hace con la mano dominante y con la otra.
- **Tareas:** (1) seguir el libro y avanzar dos capítulos; (2) cambiar la letra;
  (3) ir al capítulo 5 desde el índice; (4) consultar una palabra, oírla en
  británico y cerrar la ficha; (5) buscar «detectives en Londres» y abrir un
  libro; (6) grabar una frase, pedir la corrección y pasar a otra; (7) abrir
  /θ/ en la tabla AFI; (8) entrar con el perfil; (9) responder tres preguntas
  de Tu nivel y volver atrás una.
- **Qué se anota** (con vídeo cenital u observador): la tarea hecha **sin la
  otra mano**, los cambios de agarre, los toques fallidos, los **gestos de
  volver sin querer** y el tiempo.
- **Aprobado [opinión]:** ≥ 8 de 9 tareas sin segunda mano con la mano
  dominante y ≥ 7 con la otra; cero salidas accidentales del capítulo; nadie
  dice «no llego».

---

## 6. Qué no pude verificar

- El **límite de 200 dp** por borde en Android: solo el extracto del buscador
  del artículo de Banes (Medium dio 403).
- La página de **Reachability** de Apple y el **modo a una mano** de Android:
  extracto del buscador y prensa.
- El gesto de volver en **Safari** y su ausencia en las **PWA de iOS**: foros,
  sin documentación de Apple.
- Las cifras de **phablets** de Clark (2015), sin fuente primaria.
- Una **observación reciente** de uso con una mano: el dato es de 2013.
- Parhi et al. (2006), Park y Han (2010), Kim y Ji (2019), Le et al. (2018) y
  Eardley et al. (2017): **solo el resumen**. Mehrotra et al. (2022) es un
  **preprint**.
- **Material Design 3** (m3.material.io no se deja leer): cito Material
  Components en GitHub.
- **Hoober y Berkman (2011)**, origen de los diagramas de la zona del pulgar:
  no lo consulté.
- Si **Chrome DevTools emula `safe-area-inset-*`**, y los mm por px en Android.

---

## Referencias

Apple. (s. f.). *Accessibility*. Human Interface Guidelines.
https://developer.apple.com/design/human-interface-guidelines/accessibility

Apple. (s. f.). *Reach the top of the iPhone screen with one hand*. Manual de
uso del iPhone. https://support.apple.com/guide/iphone/use-reachability-iph145eba8e9/ios
**[secundaria: extracto del buscador]**

Android Developers. (s. f.). *Ensure compatibility with gesture navigation*.
https://developer.android.com/develop/ui/views/touch-and-input/gestures/gesturenav

Banes, C. (s. f.). *Gesture navigation: Handling gesture conflicts (III)*.
Android Developers en Medium.
https://medium.com/androiddevelopers/gesture-navigation-handling-gesture-conflicts-8ee9c2665c69
**[secundaria: página no accesible; fecha sin verificar]**

Bergstrom-Lehtovirta, J., y Oulasvirta, A. (2014). Modeling the functional area
of the thumb on mobile touchscreen surfaces. En *Proceedings of the SIGCHI
Conference on Human Factors in Computing Systems* (pp. 1991–2000). ACM.
https://doi.org/10.1145/2556288.2557354

Bi, X., Li, Y., y Zhai, S. (2013). FFitts law: Modeling finger touch with Fitts'
law. En *Proceedings of the SIGCHI Conference on Human Factors in Computing
Systems* (pp. 1363–1372). ACM. https://doi.org/10.1145/2470654.2466180

Chrome for Developers. (2022). *Prepare for viewport resize behavior changes
coming to Chrome on Android*. Google.
https://developer.chrome.com/blog/viewport-resize-behavior

Clark, J. (2015, 3 de noviembre). How we hold our gadgets [Extracto de
*Designing for touch*]. *A List Apart*.
https://alistapart.com/article/how-we-hold-our-gadgets/

Eardley, R., Roudaut, A., Gill, S., y Thompson, S. J. (2017). Understanding grip
shifts: How form factors impact hand movements on mobile phones. En
*Proceedings of the 2017 CHI Conference on Human Factors in Computing Systems*
(pp. 4680–4691). ACM. https://doi.org/10.1145/3025453.3025835

Fitts, P. M. (1954). The information capacity of the human motor system in
controlling the amplitude of movement. *Journal of Experimental Psychology,
47*(6), 381–391. https://doi.org/10.1037/h0055392

Google. (s. f.). *Touch target size*. Ayuda de Accesibilidad de Android.
https://support.google.com/accessibility/android/answer/7101858

Hoober, S. (2013a, 18 de febrero). How do users really hold mobile devices?
*UXmatters*.
https://www.uxmatters.com/mt/archives/2013/02/how-do-users-really-hold-mobile-devices.php

Hoober, S. (2013b, 18 de marzo). Common misconceptions about touch. *UXmatters*.
https://www.uxmatters.com/mt/archives/2013/03/common-misconceptions-about-touch.php

Hoober, S. (2017, 6 de marzo). Design for fingers, touch, and people, part 1.
*UXmatters*.
https://www.uxmatters.com/mt/archives/2017/03/design-for-fingers-touch-and-people-part-1.php

Horton, T. (2017, 22 de septiembre). *Designing websites for iPhone X*. WebKit.
https://webkit.org/blog/7929/designing-websites-for-iphone-x/

Kim, H. C., y Ji, Y. G. (2019). Natural thumb zone on smartphone with one-handed
interaction: Effects of thumb length and screen size. En *Proceedings of the
20th Congress of the International Ergonomics Association (IEA 2018), Volume
VII* (Advances in Intelligent Systems and Computing, Vol. 824). Springer.
https://doi.org/10.1007/978-3-319-96071-5_50

Le, H. V., Mayer, S., Bader, P., y Henze, N. (2018). Fingers' range and
comfortable area for one-handed smartphone interaction beyond the touchscreen.
En *Proceedings of the 2018 CHI Conference on Human Factors in Computing
Systems*. ACM. https://doi.org/10.1145/3173574.3173605

Material Components. (s. f.-a). *Bottom sheets* [Documentación]. GitHub.
https://github.com/material-components/material-components-android/blob/master/docs/components/BottomSheet.md

Material Components. (s. f.-b). *Bottom navigation* [Documentación]. GitHub.
https://github.com/material-components/material-components-android/blob/master/docs/components/BottomNavigation.md

MDN Web Docs. (s. f.-a). *env()*. Mozilla.
https://developer.mozilla.org/en-US/docs/Web/CSS/env

MDN Web Docs. (s. f.-b). *VirtualKeyboard API*. Mozilla.
https://developer.mozilla.org/en-US/docs/Web/API/VirtualKeyboard_API

Mehrotra, S., Das, S., y Zanwar, S. (2022). *Action bar adaptations for
one-handed use of smartphones* [Preprint]. arXiv.
https://arxiv.org/abs/2208.08734

Parhi, P., Karlson, A. K., y Bederson, B. B. (2006). Target size study for
one-handed thumb use on small touchscreen devices. En *Proceedings of the 8th
Conference on Human-Computer Interaction with Mobile Devices and Services
(MobileHCI '06)*. ACM. https://doi.org/10.1145/1152215.1152260

Park, Y. S., y Han, S. H. (2010). One-handed thumb interaction of mobile
devices from the input accuracy perspective. *International Journal of
Industrial Ergonomics, 40*(6), 746–756.
https://www.sciencedirect.com/science/article/abs/pii/S0169814110000806

Samsung Electronics. (s. f.). *One UI design guidelines* [PDF]. Mobile UX
Center. https://design.samsung.com/global/contents/one-ui/download/oneui_design_guide_eng.pdf

World Wide Web Consortium. (s. f.). *Understanding Success Criterion 2.5.8:
Target size (minimum)*. WCAG 2.2.
https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
