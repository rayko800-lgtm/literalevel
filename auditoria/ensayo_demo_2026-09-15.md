# Ensayo de la demo en vivo y del vídeo (15 sep 2026)

- **Quién:** entrega-e6 (811c22), por encargo de la Central.
- **Sobre qué:** el front `73a34dd` (`main-PV7YMA4W.js`) y la API del Space `af72fb0` (RUNNING). Los guiones son `entrega/guion_demo_en_vivo.md` y `entrega/guion_video.md` tal como están en HEAD (su último cambio es `13ad84a`).
- **Dos pasadas, siguiendo el guion paso a paso:**
  - **390 × 844**, `mobile` y `touch`;
  - **1280 × 800**, de escritorio.

  Cada una en Chrome, en un contexto aislado y sin datos previos. Al acabar, pestañas cerradas.
- **Sin cuenta.** Miguel dejó como norma no usar contraseñas de perfiles, y la Central lo confirmó. `literalevel_codigos.txt` no se abrió. Los pasos que dependen de la cuenta o del micrófono (la explicación del 4, y el 5 y el 6) quedan descritos tal como los ve alguien sin entrar. Al final va la lista de lo que tiene que probar Miguel en el teléfono.
- **Tiempos:** son de extremo a extremo, medidos en el navegador: desde que se pulsa hasta que lo esperado está en pantalla.

## Resumen para quien presenta

- **El recorrido se sostiene sin cuenta** en los pasos 1, 2, 3, 7, la parte local del 4 y la boca del 5. Ningún paso tarda más de 3 s si el motor está despierto, **salvo dos**: la primera consulta de palabra de la sesión (3,8 s) y la primera vez que se abre la boca 3D en el móvil (4,4 s). Los dos se evitan con la preparación que ya pide el guion.
- **Tropiezos que conviene arreglar en el guion antes del 19** (detalle en la tabla):
  - la palabra ensayada, *poverty*, está en «Antes del primer capítulo», que no se abre con «Empezar a leer»;
  - con el perfil 1,20 y una búsqueda de detectives no sale ninguna tarjeta de cuento libre;
  - el vídeo nombra dos botones de «Afinar» con un texto que no es el de la pantalla;
  - falta la receta para dejar el perfil exactamente en 1,20.
- **Tiempo:** el texto hablado de la demo son 425 palabras, unos 2:50 a 150 palabras por minuto. Con las esperas medidas y las que dependen de OpenAI, la estimación es de **3:40 a 4:10**, dentro de 3–5 min. El paso 4 es el único tramo que se pasa de su ventana: 30 s, contra 24 s de texto más la explicación de la IA.

## Paso a paso

| Paso del guion | 390 táctil | 1280 escritorio | ¿Coincide con lo que se ve? |
|---|---|---|---|
| **Antes: motor despierto** | `/api/estado` responde en 0,44 s y 0,26 s, con «68.546 libros». | igual | Sí. |
| **Antes: perfil 1,20 puesto** | «Tu nivel», primera pregunta «Varias veces por semana»: la estimación sale en el acto, «1,20 · B2», y «Me vale así (1,20 · B2), guardar». No hace falta contestar el resto. | igual; el botón dice solo «Me vale así, guardar» | **Falta en el guion** cómo se deja en 1,20. Probé 60 combinaciones al azar del cuestionario completo y ninguna dio 1,20 exacto; con la primera pregunta sola, sí. |
| **A y N** | Sin interacción. | — | Las cifras 53.179 y 15.367 son las publicadas. |
| **1. Entrar y el nivel** | Resultado inmediato: «Lees en inglés a nivel B2», «1,20 de 2 · Intermedio», franja 0,95–1,45. Botones «Afinar con un texto» y «Con un libro que ya leíste». | igual | La demo sí coincide: «1,20 sobre 2, banda intermedia», y «Afinar» está en los dos botones. **El vídeo no:** nombra «Mídeme con un texto» y «Mídeme con un libro que ya leí», y en pantalla no hay nada con ese texto. Además, el titular grande dice **B2**, y quien presenta dice «banda intermedia»: que no le sorprenda. |
| **2. Encontrar** | «una novela de detectives victoriana» en **1,6 s**. «En tu nivel» trae 1 tarjeta, *A Little Bit of Fluff: A Farce in Three Acts*, «A tu medida». «Un poco por encima» trae 13, y el botón «Ver también… (10)». **Ninguna tarjeta de cuento libre a la vista.** | 1,1 s en otra búsqueda | **No.** El guion pide «Desliza hasta ver una tarjeta de cuento libre entre los libros», y con 1,20 y detectives no hay. Con la regla del front, contra la API a 1,20, estas búsquedas **sí** ponen cuentos libres a la vista: «Cuentos cortos para empezar» (5 en «En tu nivel»), «cuentos de dragones» (14) y «Aventuras en el mar» (2). La farsa entra por el margen normal de relevancia, no por el de la franja. Ninguno de los dos guiones usa el chip «Detectives en Londres», que la ronda 3 del front de 4e (`7ecc2b1`) señala por dejar a B1 sin resultados de su nivel. |
| **3. «dostoyevski» y la ficha** | **0,7 s**. Aviso «De «dostoyevski» no hay libros en tu nivel ni un poco por encima…»; en «De otros niveles», *Best Russian Short Stories* y **Crime and Punishment segundo**. La ficha abre al momento: «C1 · 1,70 de 2», **203.415 palabras**, «Va por encima de tu nivel» y la curva «Medido entero» ya calculada. También dice «Empieza en el capítulo 2: los anteriores son portadilla». | búsqueda 1,1 s, ficha 1,2 s, curva calculada | Sí, las cifras son las que se dicen. |
| **4. Una palabra en su frase** | *poverty* está en **«Antes del primer capítulo»** (índice 0, prefacio del traductor). **Primera consulta de la sesión: 3,8 s** hasta ver el diccionario (0,45 s son la espera del lector tras seleccionar). En caliente, *debts* 0,83 s y *Mihail* 0,74 s, **0,3–0,4 s sin la espera**. Hoja de *poverty*: «noun · frecuente», US /ˈpɑːvɚti/, UK /ˈpɒvəti/, «Sin grabación para esta palabra: suena con la voz de tu navegador», la definición y la frase. **Sin cuenta:** «Esta parte necesita que entres con tu perfil…», y ni «En español» ni «Aquí significa». *debts* enseña «No estoy seguro de que sea esta acepción (afinidad 0,38)». *Mihail*: «Esta palabra no está en el diccionario» y **sin marca IA** (sin cuenta no se pide la definición). | *poverty* 0,75 s; la hoja sale a la derecha, 380 px | **A medias.** (a) «Empezar a leer» lleva al capítulo 2: *poverty* hay que buscarla abriendo el índice en «Antes del primer capítulo». El guion no lo dice. (b) La IPA coincide con el guion. (c) El vídeo dice «fonética con audio»; el audio es la voz del navegador, no una grabación. (d) «40 milisegundos» no es lo que ve quien mira: ve menos de medio segundo en caliente. (e) La marca IA y «Aquí significa» solo con cuenta. |
| **5. Pronunciar y corregir** | Banda arriba: «La corrección usa OpenAI, así que necesita que entres con tu perfil. Entrar». «Una frase de mi libro» rellena en 0,3 s («Dostoevsky was the son of a doctor.», del último capítulo leído). El micrófono, sin permiso, avisa «No tengo permiso para usar el micrófono…». La tabla del AFI abre en 0,3 s. En /ʌ/, «Escuchar y ver» suena, «Más lento» pasa a «Lento · 0,5×», y «Boca en 3D» pinta el lienzo en 1,6 s y **la cara de Blender en 4,4 s** la primera vez; lienzo de 136 a 556 y barra desde 628, sin taparse. | micrófono «Empezar a grabar» abajo (y = 759 de 800); boca 3D con cara en 1,7 s | Los botones coinciden. **Sin probar:** grabar, «Corrígeme» y el sonido que falla; se necesitan cuenta y micrófono. |
| **6. Que no suene robótico** | No se puede ensayar sin cuenta ni micrófono. | — | **Sin probar.** |
| **7. Mis palabras** | 0,6 s. «2 palabras distintas · 2 consultas · 1 libro», «Repasa cinco», *poverty* y *debts* con su frase. *Mihail* no se guarda: no trae sentido. | 1,0 s, *poverty* | Sí. **Pero** la tarjeta dice «Crime and Punishment, **cap. 1**» para una palabra del «Antes del primer capítulo»: quien presenta no debe leerlo en voz alta como «capítulo uno». Lo que se pronuncia mal (la otra mitad de lo que dice el paso) no se pudo probar. |

## Tiempos contra la ventana de cada tramo

Palabras entre comillas en los «Dice:» de la demo, a 150 y a 130 palabras por minuto, más las esperas medidas.

| Tramo | Ventana | Texto | Espera medida o esperable | Holgura |
|---|---|---|---|---|
| A | 20 s | 18–20 s | — | justa |
| N | 20 s | 20–23 s | — | **se pasa 0–3 s** |
| 1. Nivel | 20 s | 16–18 s | < 1 s | bien |
| 2. Encontrar | 25 s | 14–17 s | 1,6 s y deslizar | bien |
| 3. Ficha | 25 s | 17–19 s | 0,7 s de búsqueda y ficha al momento | bien |
| 4. Palabra | 30 s | 24–28 s | 0,8 s el diccionario y **unos 15 s la explicación** (docstring de `/api/palabra`; sin cuenta no se pudo medir) | **se pasa unos 10 s** |
| 5. Pronunciar | 30 s | 18–21 s | leer la frase, unos 5 s, y la corrección (sin medir) | **justa**; sin medir la corrección |
| 6. Natural | 30 s | 14–17 s | grabar, corregir y el audio natural (sin medir) | desconocida |
| 7. Mis palabras | 20 s | 8–9 s | 0,6 s | bien |
| V | 15 s | 16–18 s | — | **se pasa 1–3 s** |
| A final | 10 s | 6 s | — | bien |
| **Total** | **4:05** | **2:50–3:16** | unos 25–40 s | **3:40–4:10 estimado**, dentro de 3–5 min |

**El vídeo:** `tools/contar_guion.py` da 496 palabras (3:18 a 150 palabras por minuto), como dice el guion. Con las esperas de la demo (búsqueda, palabra en caliente, ficha y boca) se queda por debajo de 4:40 si la palabra y la boca se preparan antes.

## Qué cambiar en los guiones (para 4e, vía la Central)

1. **Receta del perfil 1,20** en «Antes de conectarse» y en «Preparación de la toma»: *Tu nivel* → primera pregunta «Varias veces por semana» → «Me vale así (1,20 · B2), guardar». Y avisar de que el titular dirá «nivel B2».
2. **Paso 2 de la demo:** cambiar la búsqueda de ejemplo por una que enseñe cuentos libres con 1,20, como «Cuentos cortos para empezar» o «cuentos de dragones». O quitar «Desliza hasta ver una tarjeta de cuento libre».
3. **Paso 4 (demo y vídeo):** decir que *poverty* está en «Antes del primer capítulo» y que se abre desde el índice, no con «Empezar a leer».
4. **Vídeo, «Afinar»:** «Afinar con un texto» y «Con un libro que ya leíste», no «Mídeme con un texto» ni «Mídeme con un libro que ya leí».
5. **Vídeo, «40 milisegundos»:** es lo que tarda el servidor, no lo que se ve (0,3–0,4 s en caliente y 3,8 s la primera). Mejor «al instante» o «en menos de medio segundo».
6. **Vídeo, captura de *poverty*:** la «fonética con audio» es la voz del navegador («Sin grabación para esta palabra»), no un audio grabado.
7. **Paso 7:** la tarjeta dirá «cap. 1» para una palabra del prefacio; que no se lea en voz alta.
8. **Vídeo, «La boca en 3D»:** cita el front `45d9999`; el publicado es `73a34dd`.
9. **Paso 4 de la demo:** la ventana de 30 s no cabe con la explicación de la IA (unos 15 s). O se habla mientras llega (el texto ya lo prevé), o se recorta la segunda palabra.
10. **Preparación:** abrir la boca 3D una vez antes de compartir; la primera carga en el móvil tardó 4,4 s.

## Lo que tiene que probar Miguel en el teléfono, con su cuenta y micrófono

1. **Paso 4:** cuánto tarda en llegar «En español» y «Aquí significa» con *poverty*.
2. **Paso 4, la marca IA:** con qué palabra sale; con *Mihail*, sin cuenta, solo sale «no está en el diccionario».
3. **Paso 5:** grabar «Una frase de mi libro» con una palabra mal dicha a propósito.
   - cuánto tarda «Corrígeme»;
   - si sale el sonido que falla y su «Escuchar y ver».
4. **Paso 6:** «Don't you want to come with us?».
   - *doncha* y *wanna*, «aquí sin pausa» y «Escúchalo natural»;
   - cuánto tarda.
5. **Paso 7:** que la palabra mal pronunciada aparezca en «Mis palabras».
6. **El cronómetro:** la demo entera, contra los 3–5 minutos. Las ventanas de los pasos 4, 5 y 6 son las que no se han podido medir.

## Anexo: los guiones corregidos por 4e en a978155

- **Sobre qué:** el front publicado `ec957d0` (repositorio `4e6276e`) y la API del Space `384a206` (reinicio 21).
- **Cómo:** a 390 px táctil, sin cuenta, en contextos aislados limpios.
- **Qué se probó:** solo lo que cambió; al acabar, pestañas cerradas.

| Lo que cambió | ¿Coincide? | Lo visto |
|---|---|---|
| **Receta del perfil 1,20** | Sí | «Varias veces por semana» → «Me vale así (1,20 · B2), guardar» → «Lees en inglés a nivel B2», «1,20 de 2», franja «0,95 y 1,45». |
| **Botones de «Afinar»** | Sí | «Afinar con un texto» y «Con un libro que ya leíste». |
| **Paso 2, «cuentos de dragones»** | Sí | 1,5 s. «En tu nivel» trae 14 tarjetas: 13 cuentos libres y *My Father's Dragon* (Gutenberg, B1 · 0,95). La primera, *The Dragon Hunter*, es libre y se ve sin deslizar (empieza a 573 px de 844). «Un poco por encima» trae 1. |
| **Los guiones y los chips** | Sí | Ningún guion nombra un chip; «cuentos de dragones» se escribe a mano. |
| ***poverty* por el Índice** | Sí, con un matiz | En la ficha, «Índice · 40 capítulos» queda a 2.135 px, unas 2,5 pantallas por debajo de «Empezar a leer», detrás de la curva y de «Cómo es de leer». La entrada se llama «1 · Antes del primer capítulo · 5 min». Abre en 0,5 s, y *poverty* está en «In 1864 he lost his first wife… He was in terrible poverty». El lector también tiene «Índice» arriba (lo vi, no lo probé). |
| **«cap. 1» en Mis palabras** | Sí | El Índice y el lector («CAPÍTULO 1 DE 40») también numeran el prefacio como 1. La etiqueta es coherente con la app, y el aviso de no leerla en voz alta sigue valiendo. |
| **Boca 3D abierta una vez** | El consejo vale; la cifra ya no | El guion dice 4,4 s. Desde `88b3a83`, a 390 y con la caché vacía: lienzo en 0,7 s y cara en 2,1 s la primera vez, 0,5–0,6 s después, y 2 bajadas de .glb. |

**«Antes de grabar, con cuenta y micrófono»** se entiende: seis puntos, y cada uno dice el paso, qué mirar y qué medir. Tres cosas ayudarían a Miguel:

1. **El título.** Está en el guion de la demo en vivo. «Antes de la demo…» evita confundirlo con la grabación del plan B.
2. **Entrar y los fallos.** No dice dónde se entra (*Ajustes → Tu perfil*, como pone el guion del vídeo) ni qué hacer si un punto falla (remitir al plan B).
3. **El punto 1.** Conviene recordar el camino de *poverty*: «Índice → Antes del primer capítulo».

**Restos en el guion del vídeo:**

- **`guion_video.md:150-158`** dice aún «Los 40 milisegundos que dices a cámara», pero el texto ya dice «al instante» (línea 275). En la misma nota, «la primera consulta léxica de la sesión tarda unos 55 segundos» (11 sep) no cuadra con los 3,8 s medidos hoy.
- **`guion_video.md:73`** cita `b76ca59`, que es el commit del Space del front, no del repositorio (`88b3a83`). Lo publicado ahora es `ec957d0` / `4e6276e`, con la misma boca.

**Fuera de los guiones** (no se pidió): `documento.md:1305`, `estrategia.md:445` y `documento.tex:1009` siguen con «front `45d9999`».

## Anexo 2: segundo ensayo completo sobre lo publicado el 15 sep por la tarde

- **Quién:** entrega-e6 (811c22), por encargo de la Central.
- **Sobre qué:** el front `bdfa418` (`main-4E3B2GGO.js`; en código es `3662e57`, con el mismo bundle) y la API del Space `74f1484` (RUNNING, reinicio 28). El guion es `entrega/guion_demo_en_vivo.md` en `800060e`, igual en HEAD.
- **Lo que no existía en el primer ensayo** (front `73a34dd`, Space `af72fb0`): las pantallas A de *Tu nivel* y *Pronunciar*, la franja de nivel en *Encontrar*, la precarga del buscador, el aviso de silencio y los reinicios 26, 27 y 28.
- **Cómo:** tres contextos aislados de Chrome, sin datos previos y **sin cuenta** (la norma de Miguel sigue: ni contraseñas ni `literalevel_codigos.txt`):
  - 390 × 844 `mobile` y `touch`;
  - 1280 × 800 de escritorio;
  - otro a 390 para probar búsquedas alternativas al paso 3.

  Antes de medir hubo una búsqueda de calentamiento («animales de la granja»: 0,92 s a 390 y 0,77 s a 1280). Los tiempos son de extremo a extremo en el navegador. Al acabar, las tres pestañas cerradas.
- **Qué no se pudo probar:** el micrófono, porque sin permiso la app dice «No tengo permiso para usar el micrófono…». Tampoco lo que necesita cuenta: la explicación de la IA, «Corrígeme», «Para sonar más natural» y el aviso de silencio.

### Resumen para quien presenta

- **SERIO, paso 3.** «dostoyevski» con el perfil de 1,20 ya no enseña lo que dice el guion. No hay aviso de «no hay libros en tu nivel ni un poco por encima». «En tu nivel» abre con 9 tarjetas, 7 de ellas cuentos libres que no tienen que ver con el autor (*Tanaji Malusare*, *Story Chikkappa*, *Books*…). *Crime and Punishment* solo aparece tras «Ver también los de otros niveles (21)», segundo en «De otros niveles», a 3.789 px en el móvil (unas 4,5 pantallas) y a 1.681 px a 1280. f4 ya está midiendo la causa.
- **Todo lo demás que se ve sin cuenta cuadra con el guion,** en las dos anchuras:
  - la receta del 1,20;
  - «cuentos de dragones» (19 libres de 20);
  - los detectives (3 de Gutenberg);
  - la ficha de *Crime and Punishment*;
  - *poverty* por el Índice;
  - los botones de *Pronunciar*;
  - «Mis palabras» con «cap. 1».
- **Tiempo.** Con el buscador caliente, cada búsqueda tarda entre 0,49 y 0,77 s, y la ficha, el lector y la boca, menos de 3 s. La estimación del primer ensayo (3:40–4:10) se mantiene: no ha cambiado ningún «Dice:» que alargue un tramo.

### Paso a paso

| Paso del guion | 390 táctil | 1280 escritorio | ¿Coincide? |
|---|---|---|---|
| **Antes: motor despierto** | `/api/estado` en 0,28 y 0,30 s, «68.546 libros», `funciones_openai.disponibles: true`. `/api/salud`, `buscador_listo: true`. | igual | Sí. |
| **Antes: perfil 1,20 (receta de seis)** | Cada opción avanza sola, con «1 de 6»… «6 de 6». Al contestar la sexta se guarda en 0,21 s: «Lees en inglés a nivel B2». En «Ver el detalle»: «1,20 de 2 · Intermedio. Busco lecturas entre 0,95 y 1,45». Pie: «¿No te convence? Afínalo con un libro que ya leíste · con un texto · volver a medirme». | se guarda en 0,49 s; textos iguales | **Sí**, palabra por palabra. No he vuelto a comprobar las cifras de los despistes (1,07–1,27, y 1,46 con «Capto bien la idea»). |
| **Antes: boca 3D abierta una vez** | Primera vez: lienzo en 1,6 s y `cara.glb` servida a los 2,95 s. Segunda vez: 0,63 s. | lienzo en 0,5 s, cara a los 1,76 s | El consejo vale. **La cifra no:** el guion dice 2,1 s y 0,5 s «en el front `ec957d0`»; hoy, 2,9 s en el móvil. |
| **Antes: frase de voz ensayada** | Sin cuenta ni micrófono, no se puede. | — | **Sin probar.** El guion la da por «verificada en el Space publicado a fecha de `7c09d90`» (14 sep), anterior a la pantalla A de *Pronunciar*: hoy «Para sonar más natural» va plegado y, detrás de la reducción, añade «de corrido aquí». |
| **1. Entrar y el nivel** | Resultado preparado: «Lees en inglés a nivel B2», escala A1–C2, «Ver libros de mi nivel», «Ver el detalle» con el 1,20 y el pie de afinar. | igual | Sí. |
| **2. Encontrar, «cuentos de dragones»** | 0,61 s. «En tu nivel»: 20 tarjetas, **19 libres**. La primera es *The Dragon Hunter* (B2 · 1,20, «A tu medida»). «Un poco por encima»: 1. «Ver también los de otros niveles (9)». | 0,68 s; 20 (19 libres) y 1 | **Sí.** La cifra «19 de sus 20» sigue exacta, pero el guion la atribuye al «reinicio 25»; hoy es el 28. |
| **2. «una novela de detectives victoriana»** | 0,56 s. «En tu nivel»: 3, todos de Gutenberg (*A Little Bit of Fluff*, *A Bullet for Cinderella*, *The Thirteenth Chair*). «Un poco por encima»: 23, ninguno libre. | 0,56 s; igual | Sí. |
| **3. «dostoyevski»** | 0,49 s. **Sin aviso.** «En tu nivel»: 9. Son *Verotchka's Tales* y *More Russian Picture Tales*, y 7 cuentos libres ajenos: *Tanaji Malusare*, *Story Chikkappa*, *Books* dos veces, *TARA - PRINCESS OF BARRACKPORE*, *The Story of M.S.Dhoni* y *Adhuri Betiyaan*. «Un poco por encima»: 6. *Crime and Punishment* sale tras «Ver también los de otros niveles (21)», **2.º de «De otros niveles», a 3.789 px**. | 0,62 s; igual, a 1.681 px | **No.** El guion dice que primero sale el aviso y que el libro aparece segundo en «De otros niveles» sin pulsar nada más. Alternativas en la tabla de abajo. |
| **3. La ficha** | Primera apertura en frío: 2,3 s hasta el título y 2,6 s con la curva. «C1 · 1,70 de 2», «40 capítulos», «203.415 palabras», «30 h 49 min», «Va por encima de tu nivel», curva «Medido entero» ya calculada, «Empieza en el capítulo 2: los anteriores son portadilla». | 1,5 s con la curva | Sí: «de media, 1,70». |
| **4. *poverty* por el Índice** | «Índice · 40 capítulos» a 2.075 px (unas 2,5 pantallas). Entrada «1 · Antes del primer capítulo · 5 min», que abre en 0,4 s («CAPÍTULO 1 DE 40»). El lector tiene «Índice» arriba. *poverty*: **primera consulta de la sesión, 4,5 s**; en caliente, 0,64–0,67 s. Hoja: «noun · frecuente», US /ˈpɑːvɚti/, UK /ˈpɒvəti/, «Sin grabación para esta palabra: suena con la voz de tu navegador», la definición y la frase. Sin cuenta: «Esta parte necesita que entres con tu perfil…». *religious* y *acclamations* dicen «No estoy seguro de que sea esta acepción». *Mihail*: «Esta palabra no está en el diccionario», sin marca IA. | 0,69 s en caliente; la hoja sale a la derecha (380 × 693) | Sí. La primera consulta en frío tarda más que en el primer ensayo (4,5 s frente a 3,8 s): la preparación que ya pide el guion lo evita. |
| **5. Pronunciar (sin cuenta)** | Banda: «La corrección usa OpenAI, así que necesita que entres con tu perfil. Entrar». «Una frase de mi libro», 0,21 s («Dostoevsky was the son of a doctor.»). Micrófono abajo, a y = 696. Al pulsarlo: «No tengo permiso para usar el micrófono…». AFI en 0,41 s. En /ʌ/: «Escuchar y ver», «🐢 Despacio» (que pasa a «🐢 Despacio · activado») y «Boca en 3D» (que pasa a «Cerrar 3D»). | frase en 0,18 s; micrófono a y = 759 | Los botones que nombra el guion existen con ese texto. **Sin probar:** grabar, «Corrígeme» y «Practica esta palabra» con la boca abierta. |
| **6. Que no suene robótico** | Sin cuenta ni micrófono, no se puede. | — | **Sin probar.** |
| **7. Mis palabras** | 0,35 s. «3 palabras distintas · 5 consultas · 1 libro», «Repasa cinco» y «Últimas consultas» con «Crime and Punishment, cap. 1». | igual, con *poverty* | Sí. |
| **Plan B: motor dormido** | No se provocó. El texto existe: «Despertando el motor de LiteraLevel. Si llevaba rato sin usarse tarda unos 30 segundos…». | — | Coherente con el guion. |
| **Extra: libro de un solo capítulo** (*The Indigo Fairy and the Lizard*, SWV4008) | 0,5 s. «B1 · 0,96 de 2 · 1 capítulo · 252 palabras». Tarjeta: «Es un texto de un solo capítulo, así que no hay curva que dibujar: su dificultad es 0,96 (B1).». Sin gráfica y sin «Lo que más se repite». | igual | Sí. El guion no lo usa. |

### Búsquedas para el paso 3, con el perfil de 1,20 a 390

| Consulta | ¿Aviso? | «En tu nivel» | Dónde sale *Crime and Punishment* |
|---|---|---|---|
| «dostoyevski» | no | 9 (7 libres ajenos) | tras «Ver también (21)», 2.º de «De otros niveles», 3.789 px |
| «dostoievski» | no | 11 | tras «Ver también (20)», 3.º de «De otros niveles», 4.411 px |
| «dostoyevsky» | no | 4 (*Verotchka's Tales*, *More Russian Picture Tales*, *TARA…*, *Savva…*) | tras «Ver también (23)», 2.º de «De otros niveles», 3.316 px |
| «crime and punishment» | no | 1 (*justice and injustice*, libre) | tras «Ver también (24)», **1.º de «De otros niveles», 949 px** |
| «crimen y castigo» | no | 3 libres (*justice and injustice*, *VIOLENCE*, *Legal and Law*) | tras «Ver también (24)», 6.º de «Menos parecidos a lo que buscas», 3.842 px |

Ninguna consulta reproduce el guion tal como está. Con «crime and punishment» el libro queda a una pantalla, pero sigue haciendo falta pulsar «Ver también».

### Qué cambiar en el guion (para 4e, vía la Central)

1. **Paso 3 (SERIO).** Depende de lo que decida f4 con el buscador. Si no cambia antes de grabar, hay tres opciones:
   - buscar «crime and punishment» y pulsar «Ver también los de otros niveles». Sale el primero, a una pantalla. Hay que quitar la frase del aviso;
   - abrir el libro desde la estantería o desde «Leer», que ya es lo que propone el Plan B;
   - mantener «dostoyevski», pero decir que hay que pulsar «Ver también…» y bajar cuatro pantallas.

   En cualquier caso, **quitar** «sale primero el aviso de que no hay libros en tu nivel ni un poco por encima».
2. **«Boca 3D abierta una vez»:** la cifra ya no vale. Hoy, a 390 con la caché vacía, la cara tarda 2,9 s la primera vez y 0,6 s después; a 1280, 1,8 s. Mejor quitar el hash `ec957d0` o poner el de hoy.
3. **«Frase de voz ensayada»:** la verificación citada (`7c09d90`, 14 sep) es anterior a la pantalla A de *Pronunciar*. Que Miguel la repita con cuenta (ya está en «Antes de la demo», punto 4), y que el guion no la dé por verificada.
4. **Paso 2:** «en la página publicada con el reinicio 25» puede pasar a «con el reinicio 28 (15 de septiembre)». La cifra, 19 de 20, sigue exacta.
5. **«Antes de la demo», punto 7 (voz baja):** cuando el aviso sale con cuenta, termina en «Este intento no cuenta.». Conviene que Miguel no se sorprenda: no gasta cupo.

### Lo que sigue pendiente para Miguel, con cuenta y micrófono

Sin cambios respecto a «Antes de la demo, con cuenta y micrófono» (puntos 1–8 del guion). Además, **repetir el paso 3** con la búsqueda que se decida, después de lo que suba f4.
