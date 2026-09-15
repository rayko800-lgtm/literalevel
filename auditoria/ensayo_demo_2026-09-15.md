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
