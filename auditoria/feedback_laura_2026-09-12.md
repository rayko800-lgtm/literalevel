# Feedback de Laura — 12 de septiembre de 2026

Segunda persona ajena al desarrollo que usa LiteraLevel, después de Esmeralda.
Laura es hermana del autor y trabaja en desarrollo web: habla de *grids*,
*divs*, *sections*, *margin* y *navbar* con propiedad, así que su crítica es de
usuaria y de diseñadora a la vez. Probó la aplicación **desplegada** en Hugging
Face Spaces, primero en la laptop y después en su teléfono Android, y mandó
tres capturas y dos notas de voz por WhatsApp.

## Cómo se obtuvo

- **Notas de voz:** dos archivos `.opus` de WhatsApp, de **5:43** y **2:14**.
  Transcritos con `gpt-4o-transcribe` de OpenAI (idioma `es`). Primero se
  intentó en local con `whisper-large-v3-turbo` en CPU, pero iba demasiado
  lento y se canceló.
- **Un incidente con el archivo:** la primera copia del audio de 5:43 que llegó
  al equipo estaba **dañada sin arreglo posible**. Empezaba con un salto de
  línea `\r\n` y contenía **323.682 caracteres de reemplazo UTF-8**
  (`EF BF BD`): alguien la había pasado por un canal de texto y cada byte no
  válido se había sustituido. `ffmpeg` la rechazó con 183 errores de CRC en
  las páginas Ogg. Hubo que volver a bajarla de WhatsApp.
- **Capturas:** tres, del teléfono, sobre el Space desplegado.

## Transcripción literal

Se reproduce tal cual salió del transcriptor, sin corregir muletillas. Las
palabras entre corchetes son aclaraciones de este documento.

### Nota 1 (5:43)

> Me gustó la aplicación. Es interesante la aplicación como tal, el objetivo
> con el que está hecha la aplicación. Pero siento que hay algunas cosas que no
> me gustan. Por ejemplo, la primera es que tuvimos muchos intentos para entrar
> con el usuario y la contraseña que me diste. No me dejó entrar. Y después
> cuando me diste otro usuario, ya me dejó probar todo y ya pude sacar mi
> grado. Y estuvo padre porque ya estuve jugando con la aplicación. Lo que no me
> gusta es que hay un pequeño delay con el tacto, ¿cómo decirlo? Cuando yo bajo
> las páginas se traba y hay un cierto delay. Yo hago el movimiento de deslizar
> con el dedo y dos, tres segundos y la página se empieza a mover. Hay ese delay
> que a lo mejor es normal, pero con otras páginas, por ejemplo, para la
> experiencia del usuario, es normal que tú con el más mínimo toque de la
> pantalla, la pantalla o la página se mueve. Es como la sensibilidad, siento
> yo. Y cuando voy hasta la parte de abajo, llego hasta la parte de abajo y le
> doy o le sigo bajando con el dedo deslizando la pantalla para ir más abajo y
> llego hasta el tope, se traba. Hace unos movimientos la página como si se
> fuera para arriba o para abajo y como que ahí se traba. Eso es uno. Dos, los
> grips o los dips [*grids* o *divs*] en los que tienes contenidos, los textos,
> por así decirlo, las secciones, los sections, no sé si utilizaste HTML o
> bueno, sí, las etiquetas del HTML, no les das un margin path [*padding*] o no
> les das como el suficiente espacio entre el contenido que está en esa
> sección, en esa section o en ese dip y en algunas partes las palabras se ven
> cortadas por las curvas de los dips. Eso me gustó, eso está padre, no está
> todo puntiagudo, me gusta que estén los recuadros, como por ejemplo, donde das
> información de los libros, donde dice War and Peace by Tostoy Leo, está
> curveado y esa parte me gusta, pero si te das cuenta no dejas un espacio entre
> el cuadro y lo que escribes y si te das cuenta todo lo que escribes está
> alineado, justificado a la derecha, no está centrado, no tiene un margin
> center o una etiqueta del CS[S] que te ayude a centrar todo y por ejemplo si
> te das cuenta esos cuadros hacen que se coman los cachos de las letras, por
> ejemplo ahí donde dice empieza en el capítulo 2, los anteriores son
> portadilla, se come el palito de la P, entonces hace ruido visual, no es como
> que muy agradable para la experiencia del usuario, en cuanto a funcionalidad,
> pues solamente eso del delay. Y también cuando estoy leyendo los libros y doy
> a la página de siguiente capítulo, me deja ahí mismo abajo, entonces tengo que
> hacer todo el scroll para irme hasta la parte de arriba y empezar a leer el
> siguiente capítulo, en vez de que cuando le doy en el botón de siguiente
> capítulo, me redirija hasta la parte de arriba y empiece otra vez yo a leer el
> capítulo, eso también está un poco, pues no me gusta porque tienes que hacer
> todo ese movimiento, en vez de que la página lo haga por ti. Y después en la
> parte de la pronunciación, no pronuncié dos palabras, que fue cool y defeat,
> y está bien porque la aplicación me dijo, no los detecteo, no los pronuncie, y
> está bien porque no los pronuncié, pero también no entiendo las partes de que
> te explica cómo pronunciar, me gustaría que estuvieran los símbolos del
> alfabeto, no me acuerdo del nombre, pero es la de los símbolos, la que te dice
> cuáles son los símbolos y como la pronunciación, siento yo que eso estaría más
> padre, y pues no entiendo el sonido, por ejemplo, de la primera palabra que
> era warm [*warn*], el sonido W que es diferente a la letra B, en español no
> entiendo eso, ¿sabes? Eso y también una vez que ya le di en la parte de la
> pronunciación y que ya escribí lo que quería yo pronunciar, algo que me
> molesta es que tenga que volver a meterme en esa entrada de texto, en ese
> input, y tenga que borrar todo para que, pues volver a poner otra palabra, a
> lo mejor podrías poner un botón abajo de todo eso, abajo de donde te dice
> corréjeme y donde te muestra los estos de revisar otra palabra, o continuar, o
> siguiente palabra, o siguiente vocalización, porque todo lo tengo que hacer
> manual, tengo que irme otra vez a la entrada, al input donde voy a meter la
> frase que voy a leer para grabar, y tengo que borrarla toda, y si meto frases
> grandes, pues es un poco complicado, no he tardado, voy a tener que estar
> picándole el botón en el teclado de borrar y borrar y borrar, ¿no? Eso es
> como que lo que no me gusta.

### Nota 2 (2:14)

> Y ya de ahí en fuera, todo se ve chido, nada más que sí te digo, todo se ve,
> el responsive está bien, porque lo probé en la computadora la vez pasada y lo
> probé ahorita en el teléfono y se ve bien, me gusta, o sea, esa parte del
> responsive, de la forma en que se acomodan las cosas, los grips, los dips, las
> sections, están padres, porque no me genera ruido visual, no son como esas
> páginas de que todo se hace en un cuadrito chiquitito chiquitito y te ocupa
> como una tercera parte de la pantalla vertical, y me gusta porque se acomoda
> bien, pero no me gusta el estilo que le diste porque en la laptop se ve que
> todo está justificado a la derecha, no se ve que esté centrado o que esté
> justificado a los dos lados, por así decirlo, los colores igual de entrada no
> me gustan mucho, que me parece ser que es como un negro y un azul muy fuerte,
> a mí me gusta el modo oscuro de los teléfonos y se ve bien, se ve padre, pero
> por lo mismo de que usas muchos colores oscuros, no encuentro ese contraste y
> no encuentro esa división entre las secciones, sí, o sea, porque está muy
> oscuro, tienes todos los colores oscuros, la paleta de colores no me hace yo
> encontrar un contraste en el que pueda entender la división y tengo que irme
> a un modo claro para entender ahora las secciones, porque la diferencia de
> colores en el modo oscuro no es mucha, entonces las secciones no las entiendo,
> y a mí ya es como más personal, pero me hubiese gustado un navbar arriba, y
> ahí en ese navbar me hubieras puesto la parte de mi nivel, buscar una lectura
> y después la pronunciación, porque esas son como las funciones de tu
> aplicación, y lo que pones en los tres circulitos son configuraciones, que si
> le pones la parte del color, no son funcionalidades, son configuraciones,
> entonces generalmente las configuraciones van justamente en esos tres
> puntitos, qué más, qué más, pues nada más eso, te digo.

## Capturas

1. **Entrar con `invitado3`** → «No he podido entrar».
2. **Corrección de pronunciación, 78/100**, con detalles para `warn`, `don`, `t`,
   `defend`, `perpetrated` y `call`, y un «..» doble al final de cada sonido.
3. **Lector en el teléfono**: la caja de subida ocupa media pantalla y la
   cabecera del libro se aprieta a su lado en una columna de tres palabras por
   línea: «War and Peace — Tolstoy, Leo, graf · 375 capítulos…».

## Diagnóstico, corrección y verificación

Cada fila se verificó en la aplicación en local con Chrome controlado por el
protocolo de depuración, a **1440 × 900** (laptop) y a **390 × 844** con
emulación táctil (teléfono), además de la batería `pruebas_extremas.py`.
**La emulación táctil no es un teléfono real**: lo que depende del rendimiento
del dispositivo (fila 4) queda pendiente de que Laura lo pruebe otra vez.

| # | Lo que dijo o se vio | Diagnóstico | Corrección | Verificación |
|---|---|---|---|---|
| 1 | «Tuvimos muchos intentos para entrar… no me dejó entrar» (`invitado3`) | La cuenta existe en el secreto del Space y su contraseña tiene 14 caracteres, los mismos 14 puntos de la captura: casi seguro un error al teclear una contraseña **aleatoria de 14 caracteres en un teléfono**. Con `invitado7` entró a la primera | **Sin cambiar todavía.** Cambiar contraseñas de un Space desplegado es decisión del autor. Propuesta: contraseñas legibles (tres palabras) o enlace de invitación | — |
| 2 | Captura: «don» y «t» como palabras falladas | Los libros usan el apóstrofo tipográfico `’`. `voz.normalizar_palabras` lo trataba como puntuación y partía «don’t» en dos palabras que el alumno no había dicho mal | Se unifican `’ ‘ ʼ ´ \`` en `'` antes de limpiar | 2 pruebas nuevas: la contracción sigue siendo una palabra y dicha igual no cuenta como fallo |
| 3 | Captura: «español.. Coloca» | El modelo cierra la frase con punto y la interfaz añadía otro | Se quita el punto final antes de añadir el separador | Revisado en el código; sin prueba propia (necesita una llamada de pago) |
| 4 | «Deslizo con el dedo y dos, tres segundos y la página se empieza a mover… llego hasta el tope, se traba» | Dos causas de repintado en cada fotograma: `backdrop-filter: blur(7px)` en **cada** bloque (más de cien) y el fondo de estrellas con `background-attachment: fixed` | Las dos, **solo con ratón** (`@media (hover:hover) and (pointer:fine)`). En el teléfono los paneles son opacos al 86–90 % y el desenfoque apenas se veía | Con emulación táctil: `backdrop-filter: none` y `background-attachment: scroll`. **Falta confirmarlo en un teléfono real** |
| 5 | «No les das un margin… se come el palito de la P» | Un Markdown de Gradio es un bloque **sin relleno**, pero aquí todo bloque lleva fondo de panel: el texto quedaba pegado al canto redondeado | Relleno de 0,6 × 0,95 rem a los bloques de Markdown **con contenido** (uno vacío no se pinta como franja) | Medido: 9,6 px × 15,2 px; captura en laptop y teléfono |
| 6 | Captura: cabecera del libro en tres palabras por línea | Fila de Gradio con dos componentes. **El primer arreglo lo empeoró**: dar `min_width` a los componentes no parte la fila, y la cabecera salió letra a letra. Una fila de Gradio solo se parte entre **columnas** | Dos `gr.Column(min_width=300)`; caja de subida de 150 px de alto | Captura a 390 px: se apilan. A 1440 px siguen lado a lado |
| 7 | «Tolstoy, Leo, graf» | Gutenberg escribe «Apellido, Nombre, título, fechas» | `_autor_corto` se queda con las dos primeras partes | Prueba nueva: Tolstói, Conan Doyle («Sir»), Dostoievski con traductor y Homero |
| 8 | «En la laptop todo está justificado a la derecha, no está centrado» | El contenedor sí estaba centrado (72 px por lado a 1440), pero título, texto y pestañas iban pegados a un lado y el texto sin margen interior (fila 5) | Barra de pestañas **centrada en escritorio** y relleno interior. El texto corrido sigue alineado a la izquierda **a propósito**: el criterio 1.4.8 de las WCAG desaconseja justificarlo | Captura a 1440 px |
| 9 | «No encuentro esa división entre las secciones, tengo que irme a un modo claro» | En *hielo* (la paleta por defecto) el panel era `rgba(12,22,38,.72)` sobre `#05070d` y el borde tenía un 16 % de opacidad: casi invisibles. *Medianoche* tenía el mismo problema | Panel y borde más claros en las dos paletas oscuras: *hielo* `rgba(26,44,70,.86)` / borde 34 %; *medianoche* `rgba(54,50,64,.90)` / borde 32 % | Las 85 parejas de contraste WCAG siguen pasando; captura en laptop |
| 10 | «Me hubiese gustado un navbar arriba… lo que pones en los tres circulitos son configuraciones, no son funcionalidades» | *Colores* y *Estado* eran pestañas al mismo nivel que leer o pronunciar, y en el móvil empujaban las funciones al menú «…». El profesor había dicho lo mismo: «Colores toma demasiada presencia» | Botón **⚙ Ajustes** en la esquina de la cabecera con la paleta y el estado del servicio. Pestañas con rótulos cortos (*Buscar*, *Pronunciar*). La barra **se queda fija arriba** al bajar | Ajustes abre y cierra; barra a `top: 0` tras bajar 1.400 px; sin desplazamiento horizontal. En laptop se ven las seis funciones. **A 390 px solo caben tres (*Mi nivel*, *Buscar*, *Leer*) y *Pronunciar* sigue en «…»**: se probó bajar el relleno de las pestañas, el margen lateral de la página, quitar el hueco entre pestañas y forzar a Gradio a volver a medir, y ninguno cambió su reparto. Queda para la versión Angular, donde la navegación inferior es propia |
| 11 | «Doy a siguiente capítulo y me deja ahí mismo abajo» | Los botones no movían la página. Y el primer intento de arreglo **tampoco funcionó**, medido: el texto nuevo llega después del cambio de capítulo y el navegador deshacía el salto al sustituirlo; además había dos `#ll-lector` en la página y se tomaba el invisible. Y los botones que Laura pulsó eran los de **debajo** del texto, que no estaban cableados | Al pulsar anterior/siguiente —arriba o abajo— o elegir en el índice, sube al principio del texto visible, espera a que cambie y vuelve a subir, descontando la barra fija | Teléfono, botón de abajo: la página pasa de 33.962 a 2.675 px, el texto del capítulo III al IV, y el lector queda a 44 px, justo bajo la barra de 32 |
| 12 | «No entiendo… el sonido W que es diferente a la letra B» | La explicación compara con una letra, no con un sonido que el lector conozca. **Y además no sabía qué se había oído**: con «fix» por «fox» culpaba a la /f/, que estaba bien | Prompt reescrito: anclar el sonido a una palabra del español, decir en qué se diferencia si no existe y prohibir «más fuerte» sin decir qué mover. La evaluación guarda qué se entendió en lugar de cada palabra (`Evaluacion.entendidas`) y el prompt lo recibe | Prueba de punta a punta con un audio que dice «fix» y «dock»: antes culpaba a /f/ y /d/; ahora culpa a **/ɪ/** en *fox*, que es lo correcto. En *dog* elige /ɔ/ en vez de la /ɡ/ final, y a veces ancla con una palabra inglesa («la i de sit»): **límite del modelo, no resuelto** |
| 13 | «Me gustaría que estuvieran los símbolos del alfabeto… la de los símbolos» | La corrección no muestra el AFI | Símbolo AFI del fonema, transcripción de la palabra **sacada solo del diccionario local** (Kaikki; si no la trae, se dice) y un **mp3 pregrabado por fonema**: 41 sonidos de General American generados una vez con `gpt-4o-mini-tts`, con un coste aproximado de 0,19 USD y 1,04 MB en total, que se reproducen sin gastar créditos y sin clave | En la app local: «fox /fɑks/ (US) · Sonido /ɪ/» con su reproductor, y el mp3 responde `200 audio/mpeg`. **Nadie ha escuchado aún los audios**: un reconocedor de fonemas automático marca 15 de 41 como dudosos. Los primeros que hay que escuchar son /ð/, /ŋ/, /ə/ y /ʒ/ |
| 14 | «Tengo que borrar todo… podrías poner un botón abajo de corrígeme… siguiente palabra» | No había forma de empezar otra frase sin borrar a mano | Botón **«Otra frase ↺»** debajo de la corrección: vacía la frase, la grabación y el resultado, y sube a la caja | Probado: la caja pasa de «It is a truth universally acknowledged…» a vacía |
| 15 | *(Encontrado al probar el Space el 13 de septiembre, no lo dijo Laura)* El botón ⚙ Ajustes de la fila 10 **no se podía pulsar en el Space** | La cabecera fija de Hugging Face (`#huggingface-space-header`, la insignia con el nombre del Space) queda encima de la esquina superior derecha de la página, justo donde estaba el botón. En local no existe, y la prueba en el Space lo daba por bueno porque pulsaba con `element.click()` desde JavaScript, que atraviesa lo que haya encima | El botón pasa a la esquina **inferior** derecha de la cabecera, con relleno reservado para que no pise el texto | `document.elementFromPoint` en el centro del botón devuelve la cabecera de HF antes del arreglo y el propio botón después, a 390 y a 1440 px en local; *pendiente de repetir en el Space tras el despliegue* |

## Lo que se confirmó que sí funciona

- **El diseño adaptable**: «no son como esas páginas de que todo se hace en un
  cuadrito chiquitito».
- **Las esquinas redondeadas**, que eran la corrección del ciclo de Esmeralda:
  «me gusta que estén los recuadros… está curveado».
- **La detección de palabras no dichas**: omitió *cool* y *defeat* a propósito
  y la aplicación las marcó.

## Lo que se aprende de este ciclo

1. **Dos de los arreglos fallaron la primera vez y solo se supo al medirlos en
   el navegador.** Las 306 pruebas pasaban con la cabecera del libro saliendo
   letra a letra y con el botón de siguiente capítulo sin mover nada.
2. **Laura y el profesor dijeron lo mismo sin saberlo**: los ajustes no son
   una función.
3. **Con Esmeralda son dos lectoras, *n* = 2.** Sigue siendo diagnóstico y no
   estadística, pero ya hay una coincidencia: a las dos les costó el móvil y a
   ninguna le gustó la paleta por defecto.
4. **Una prueba en el navegador también puede mentir.** La primera pasada sobre
   el Space dio por buenos el botón de Ajustes y descartó que el menú «…»
   abriera Pronunciación, y se equivocó en las dos: pulsaba con
   `element.click()`, que atraviesa lo que tape el botón, y buscaba las
   pestañas por su texto, que encontraba la copia invisible que Gradio usa para
   medirlas. Con toques reales (`Input.dispatchTouchEvent`) y
   `document.elementFromPoint`, Ajustes resultó tapado y el menú funcionaba.
