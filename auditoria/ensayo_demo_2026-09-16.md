# Ensayo del guion de la demo — 16 de septiembre de 2026

**Sobre qué se ensayó:** front en la **revisión del Space
`9b4a3b5a51299f4ce9715af640e40e1f3ea1d925`**, **del commit `a1c4268`**. Motor en
la revisión `0319290a83f9fce7d83087ec1e435df5acabf7c5`, fase `RUNNING`. Guion:
`entrega/guion_demo_en_vivo.md` en HEAD, con el punto 8 nuevo de 4e (`5fc8302`).

**Cómo:** navegador a **390 × 844 px**, móvil y táctil, contexto aislado y
limpio, **sin cuenta**. El perfil de 1,20 no se dio por supuesto: se obtuvo
contestando el cuestionario con la receta del propio guion.

**Lo que este ensayo no puede ver:** los pasos 5 y 6 con cuenta y micrófono, la
boca 3D y el cronómetro real. Siguen siendo de Miguel.

---

## Bien

**1. Punto 8, el arranque.** Se puede hacer tal cual y las cifras cuadran.
- `https://mikemaki1763-literalevel.hf.space/api/salud` responde
  `{"estado":"ok","api":"0.2.0","cargado":{"puntuador":false,"catalogo":true,"consultor":true},"buscador_listo":true}`.
  **Dice `"buscador_listo": true`**, que es lo que el guion manda comprobar.
- El `sleep_time` que cita —«172.800 s»— es exacto: la API de Hugging Face
  devuelve `gcTimeout: 172800`. Hardware `cpu-basic`, fase `RUNNING`.

**2. Las cifras que Miguel dice en la sección N.** «53.179 libros de Project
Gutenberg y, además, 15.367 textos de licencia libre» suman 68.546, y
`/api/estado` responde hoy **68.546 libros**. Cuadra.

**3. Punto 10, la bienvenida.** En contexto limpio sale la tarjeta con «**1 de
3**» y «**Libros en inglés a tu nivel**», y «Saltar» está **arriba a la
derecha** de la tarjeta (comprobado por geometría: dentro de los primeros 60 px
y pegado al borde derecho, no a ojo). Al pulsar «Saltar» desaparece.

**4. Punto 11, las ayudas de la primera vez.** Las dos salen literales:
- lector: «Mantén presionada una palabra para ver qué significa; desliza para
  cambiar de página.»
- *Pronunciar*: «Escribe o trae una frase, grábate leyéndola y te digo qué
  sonido corregir. Sin entrar puedes grabarte, escucharte y ver cómo se dice
  cada sonido.»
Las dos con su ✕ («Cerrar la ayuda», 178 – 218) y su «?» para recuperarlas.

**5. La receta del perfil de 1,20 — verificada entera, de punta a punta.** Es lo
más importante de este ensayo, porque de ella depende todo el recorrido. Las
seis respuestas del guion **existen con ese texto exacto y en ese orden**:

| Paso | Pregunta o fragmento | La respuesta del guion |
|---|---|---|
| 1 de 6 | ¿Con qué frecuencia lees algo en inglés? | «Varias veces por semana» ✔ |
| 2 de 6 | fragmento · *Alice's Adventures in Wonderland* | «Lo entiendo con naturalidad, sin necesidad de releer» ✔ |
| 3 de 6 | ¿Has terminado un libro entero en inglés? | «Sí, una novela actual» ✔ |
| 4 de 6 | fragmento · *The Adventures of Sherlock Holmes* | «Lo entiendo con naturalidad, sin necesidad de releer» ✔ |
| 5 de 6 | ¿Qué puedes contar de una página? | «Los hechos o argumentos principales» ✔ |
| 6 de 6 | fragmento · *Frankenstein* | «Entiendo algunas partes, pero necesitaría el diccionario para seguirlo» ✔ |

Al contestar la sexta **se guarda solo**, como dice el guion, y sale:
**«Lees en inglés a nivel B2»**, con «Ver el detalle» → «**1,20 de 2 ·
Intermedio**. Busco lecturas entre 0,95 y 1,45». Y el pie: «¿No te convence?
Afínalo con un libro que ya leíste · con un texto · volver a medirme».

**6. Paso 2, *Encontrar*.** Las dos cifras del guion son correctas, contando
por tarjeta real y por procedencia (`PG…` = Gutenberg; el resto, licencia
libre):
- «cuentos de dragones» → «En tu nivel», **20 tarjetas, 19 de licencia libre**
  y una de Gutenberg. El guion dice «19 de sus 20 tarjetas».
- «una novela de detectives victoriana» → «En tu nivel», **3 libros, los tres
  de Gutenberg** (PG52851, PG49931, PG14095), ningún cuento libre. Igual que el
  guion.

**7. Paso 3** (no hacía falta repetirlo; salió de camino y coincide). Con el
perfil de 1,20, «Crimen y castigo de Dostoyevski» da el aviso literal «De
"Crimen y castigo de Dostoyevski" no hay libros en tu nivel ni un poco por
encima entre los resultados. Estos son los de otros niveles.», y *Crime and
Punishment* queda a **679 px** sin pulsar nada: la misma cifra del guion. La
ficha dice **C1 · 1,70 de 2**, que es el número que Miguel dice en voz alta.

**8. Paso 4, la palabra en su frase.**
- El Índice está a **2,04 pantallas** por debajo de «Empezar a leer» (368 px y
  2.091 px, con ventana de 844). El guion dice «unas 2 pantallas»: exacto.
- «Antes del primer capítulo» existe en el Índice y abre `#/leer/PG2554/0`.
- *poverty* responde al gesto: **diccionario e IPA al instante** —«noun ·
  frecuente», US /ˈpɑːvɚti/, UK /ˈpɒvəti/, «The quality or state of being poor;
  lack of money», con su ejemplo—, y el aviso de que la explicación en su frase
  pide perfil. Es justo lo que el guion anticipa y lo que dice el punto 2 de
  «Antes de la demo».

**9. Paso 7, *Mis palabras*.** Sale *poverty* con su frase, «Repasa cinco» y
«Las más raras de las últimas que miraste». Y dice «Crime and Punishment,
**cap. 1**» aunque la palabra es del prefacio: el guion ya avisa de no leerlo en
voz alta.

---

## No coincide

**A. Paso 5: «Una frase de mi libro» no siempre está.**
Dice el guion: «Pulsa "Una frase de mi libro" o escribe una corta».
Medido: entrando a *Pronunciar* **sin libro empezado**, ese botón **no existe**.
Después de abrir *Crime and Punishment*, el mismo `Pronunciar` lo muestra en
412 – 452. Depende del libro en curso, no de la pantalla.
Consecuencia: si Miguel ensaya *Pronunciar* en frío, o llega ahí por la
navegación inferior sin haber abierto libro, buscará un botón que no está.
Sugerencia para 4e: «Pulsa "Una frase de mi libro" —aparece si vienes de un
libro— o escribe una corta».

**B. Dos rutas distintas para comprobar lo mismo.**
«Antes de conectarse» manda abrir `/api/estado`; el punto 8 manda `/api/salud`.
Las dos responden 200, pero **solo `/api/salud` trae `buscador_listo`**, que es
lo que de verdad hay que mirar. `/api/estado` devuelve un informe largo donde
esa palabra no aparece. Sugerencia: dejar `/api/salud` en los dos sitios, o
decir en el primero qué se va a mirar exactamente.

**C. Menor, y es de la aplicación, no del guion.** En *Mis palabras* se lee «**1
palabras distintas**». Con una sola palabra el plural chirría. En la demo real
Miguel tendrá varias, así que no bloquea nada; queda apuntado.

**D. Menor, de redacción.** El paso 1 del recorrido dice «Unas preguntas y tres
fragmentos», y la pantalla ya dice «**Tres preguntas y tres fragmentos**». No se
contradicen, pero el guion puede decir lo mismo que se ve.

---

## Lo que no cambia y conviene no volver a medir

El paso 3 está medido sobre el reinicio 30b y hoy vuelve a dar 679 px. Las
cifras de arranque del punto 8 son de arranques por despliegue, no de un
despertar desde la suspensión, y eso sigue sin medirse: el guion ya lo dice así.
