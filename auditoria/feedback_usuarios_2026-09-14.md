# Feedback de los primeros usuarios (desde el 14 sep 2026)

Cuentas repartidas por Miguel el 14 de septiembre por la tarde: invitado1 a
invitado8 con 20 usos cada una, profesor con 60. Front `45d9999`, motor
`7c09d90`. Este archivo recoge lo que dicen y lo que se mide a raíz de ello.

## Esmeralda (15 años, prepa), por partes

**Lo que dijo:** le gustó mucho. No encontró en su nivel muchos libros: salió
**B1** y buscó **amor**.

**Lo que se midió** (catalogo_medido.csv + catalogo_externo.csv, temas y gancho
con love/romance/courtship, letra por dificultad pública):

| Letra | Gutenberg | con amor | Libres | con amor |
|---|---|---|---|---|
| A1 | 1 | 0 | 749 | 0 |
| A2 | 40 | 0 | 5.580 | 0 |
| B1 | 558 | 2 | 5.543 | 0 |
| B2 | 3.127 | 33 | 2.578 | 0 |
| C1 | 23.454 | 884 | 794 | 0 |
| C2 | 25.999 | 1.107 | 113 | 0 |

En la franja de recomendación de B1 (0,55 a 1,05) salían **3** títulos con amor y
en la de B2 **60**, pero **esa primera medida era mía y estaba mal**: usaba el CSV
crudo, donde *A Midsummer Night's Dream* guarda 0,697, y buscaba las palabras
como subcadena. f4 lo midió sobre el catálogo que carga la app y dio **1 en B1** y **28 en B2**;
la auditoría de documentos (4e) no reprodujo el 28. **Cifra que queda**, con la
regla de la app escrita en el documento (libros literarios, sin excluidos, a
0,25 del nivel, love/romance/courtship en los temas): **1 en B1** (*The Princess
Nobody*) y **31 en B2** (29 títulos distintos). La tabla de arriba sirve solo
como forma del reparto.

**Lectura:** su experiencia coincide con los datos. La novela romántica de
Gutenberg (Austen, Brontë, Hardy) está casi toda en C1 y C2, y los cuentos
libres son infantiles y no tratan de amor. **Crecer el catálogo con más cuentos
no lo arregla**: el hueco es de composición, no de tamaño.

> **Corrección del 15 sep (madrugada), verificada sobre el CSV.** La cifra
> «1 en B1» contaba solo libros literarios de Gutenberg. La frase «los cuentos
> libres no tratan de amor» es falsa. Con love o romance en el título y
> dificultad entre 0,20 y 1,00 hay **74 cuentos libres** (36 en A2 y 38 en B1),
> y lo mismo pasa con fantasmas (47), monstruos (29) y amigos (338). La búsqueda
> no los devolvía: con nivel 0,40, «Historias de amor» traía 24 de 24 libros de
> Gutenberg (e6, `huecos_catalogo_2026-09-15.md`). **El hueco de Esmeralda era
> de búsqueda, no de composición.** Se arregla recuperando dentro de la franja
> del lector, en el reinicio 23.

**Qué se hace:** e6 reproduce la búsqueda con un perfil B1 en el Space y
propone cómo debería responder la pantalla cuando un tema tiene pocos libros en
la franja (por ejemplo, ofrecer los más cercanos por encima, marcados «un poco
por encima de tu nivel»). La decisión es de Miguel.


## Lo que se hizo (14 sep, noche)

- e6 lo reprodujo en el Space: `auditoria/diagnostico_encontrar_amor_b1_2026-09-14.md`. Además del hueco, dos fallos: con «Ordenar por mi nivel» el nivel pesaba más que el tema, y textos sin contenido («edws», «bumbumyj,jc», un cuento en coreano titulado «Love story») se colaban arriba.
- f4 los arregló en el reinicio 16 (Space `484b83b`): el nivel ordena solo dentro de lo relevante, un título acertado va siempre delante, y 163 textos libres que no son lectura en inglés quedan fuera del buscador y de recomendar (`no_lectura_externo.csv`).
- Miguel aprobó la pantalla nueva de Encontrar: dos bloques «En tu nivel» y «Un poco por encima de tu nivel», sin «A tu medida» para lo que no es lo pedido, y un botón «Ver también los de otros niveles». La hace e6.

## Esmeralda, segunda prueba (nota de voz del 15 sep, madrugada)

Probó la última versión publicada (front con portadas, paletas y la pantalla
de Encontrar en dos bloques; motor del reinicio 22-24). La nota de voz dura
2 min 43 s. Se transcribió con whisper-1 para leerla; el audio no se guarda en
el repositorio.

**Lo que le gustó:**

- Las opciones de colores («wow, me encantó eso») y las portadas «tipo portadas
  de los libros, con un encuadre».
- Los ajustes de lectura.
- La organización: «en ciertos aspectos ya es fácil de entender».
- Poder subir su propio libro.
- El cambio frente a la primera vez: «ya es más fácil de usar y aparte ya lo
  disfrutas más… ya no siento que estoy trabajando… me hacía pensar que estaba
  haciendo un trabajo de informática… es totalmente otra cosa».

**Lo que no:**

1. **Variedad en su nivel:** «no haya tanta variedad… al elegir un libro de mi
   nivel». Es el fallo de búsqueda medido esta noche (los cuentos de su nivel
   están en el catálogo y la búsqueda no los sacaba). Lo arregla el reinicio 25.
2. **Las preguntas de Tu nivel:** «no me convencieron… eran como tres, cuatro
   preguntas al principio, después se decía definir, o con otras preguntas…
   esa opción no debería estar, porque debería definirlo de una».
3. **Pronunciar:** «me perdí en la corrección de la pronunciación… me gustó
   muchísimo, pero… a lo mejor yo soy muy tonta o no entendí cómo usarlo… en
   lo de que tienes que ir como que más lento, en eso me perdí un poquito».

«A lo mejor yo soy muy tonta» vuelve a aparecer, como en la primera prueba: se
trata como fallo de diseño, no de la usuaria.

**Qué se hace:** e6 recorre Tu nivel y Pronunciar a 390 px como alguien que
llega sin saber nada y propone una o dos versiones de cada pantalla con
esquema (`auditoria/esmeralda_ux_2026-09-15.md`). Miguel elige antes de
programar. La variedad va con el reinicio 25.

**Decisión de Miguel (15 sep, 05:10), sobre el recorrido de e6 (`auditoria/esmeralda_ux_2026-09-15.md`, de52e7d):**
- **Tu nivel, propuesta A:** seis preguntas sin «Me vale así» ni nivel provisional. Se guarda solo al terminar, con «Lees en inglés a nivel B1 · Ver libros de mi nivel». Afinar queda como enlace pequeño al final.
- **Pronunciar, propuesta A:** primero el resumen, luego la palabra a practicar con «Escuchar y ver» y el interruptor «🐢 Despacio». El ritmo y el habla natural van plegados. «Corrígeme» lleva texto, y tras corregir aparece «Grabar otra vez» (9624b0a), para no pagar dos veces la misma grabación.
- **Aparte:** 4e mide si el cuestionario infravalora. En el recorrido, unas respuestas sinceras de B1 dieron A2.

## Miguel prueba la versión lista (15 sep, 06:48-06:51, móvil)

Front dca18b4 con el motor del reinicio 26, perfil propio B1 (0,95).

- **Encontrar, «Cuentos de dragones»:** «En tu nivel» abre con cuentos de dragones de su franja: DRAGON WONDERS (B1 0,98), DRAGON BEFRIENDS YOUNG GIRL (B2 1,08), When I Met a cute, fluffy and tiny dragon, THE DRAGON MYSTERY, The mouse+dragon y My Father's Dragon, todos «A tu medida». Funciona como se diseñó.
- **Fallo en la ficha de un cuento de un solo capítulo** (el de Kian): «Dificultad capítulo a capítulo» dice «Se va soltando… Lo más llevadero, el capítulo 1; lo más exigente, el 1», y la gráfica sale sin ningún punto. «Lo que más se repite» solo muestra el nombre del personaje. Lo arregla e6.
- **Observación de producto, sin cambio todavía:** el resumen de ese cuento dice «Para peques que disfrutan cuentos rimados». Con la franja, a una lectora B1 de 15 años le salen cuentos infantiles de su nivel. Es lo que hay en las fuentes libres. Conviene vigilar si a Esmeralda le parecen demasiado infantiles.

## Ismael (hermano de Miguel), nota de voz del 15 sep

Probó la app el 14 y el 15 de septiembre. Nota de 14 s, transcrita con whisper-1 para leerla; el audio no se guarda en el repositorio.

> «Hoy y ayer estuve probando la aplicación, pero cuesta un poquito entenderle. Yo creo que le falta eso, ¿no?, hacerla más intuitiva, o a lo mejor unos cuadros de diálogo que te digan qué hace cada cosa.»

**Lectura:** es la misma señal que dio Esmeralda («a lo mejor yo soy muy tonta»), ahora de un adulto: sin explicación, no se entiende para qué sirve cada pantalla. No dice en cuál se perdió.

**Qué se hace:**
- e6 recorre el front publicado como alguien que llega por primera vez y propone dos formas de ayuda con esquema: una bienvenida de 3 o 4 pasos que se puede saltar, o una ayuda de una frase por pantalla. Informe en `auditoria/ismael_ayuda_2026-09-15.md`.
- Miguel elige antes de programar.
- Conviene preguntarle a Ismael en qué pantalla se perdió y qué quería hacer.

**Segunda nota (15 sep), de uno de los lectores, sin confirmar de quién:** el 16 de septiembre Miguel la mandó otra vez diciendo «según yo este es de Laura». Transcrita, es la misma grabación que estaba archivada aquí como segunda de Ismael, así que la atribución queda abierta y con ella **las dos** quejas que lleva dentro, el micrófono y la saturación.

> «Entré y ya inicié sesión, pero le pisas al micrófono y no te dice que hables, no se activa la grabación… lo que quieres es que sea más intuitiva, a lo mejor no tan saturada la página. Por ejemplo, los textos están largos y tienes que hacerle scroll, y te pierdes, no sabes qué hacer en la aplicación.»

- **Micrófono:** con sesión iniciada, pulsa y no pasa nada visible ni empieza la grabación. Puede ser un fallo, no solo de diseño. Si abrió el enlace desde WhatsApp, su navegador interno no suele permitir el micrófono. e6 revisa qué ve el usuario en cada caso: permiso negado, navegador sin micrófono o grabación sin audio.
- **Saturación:** textos largos, mucho scroll antes de saber qué hacer. Entra en las propuestas de ayuda de e6.
- **Falta saber:** qué teléfono y qué navegador usó, y si abrió el enlace desde WhatsApp.

**Dato de Miguel (15 sep), que era sobre Ismael y no necesariamente sobre esta nota:** usó un teléfono **Android** y abrió el enlace que le llegó **por WhatsApp**. En Android, WhatsApp puede abrir los enlaces en su navegador interno (un WebView), donde el micrófono no suele estar disponible. Era la hipótesis principal del fallo del micrófono, y sigue siendo **solo una hipótesis**: la nota dice «entré y ya inicié sesión», así que el caso a explicar es con sesión. El 16 de septiembre Miguel dijo además que Ismael no había iniciado sesión; eso queda como dicho por él y pendiente de confirmar, y no entra en los entregables. e6 comprueba qué muestra Pronunciar cuando no hay `mediaDevices` o `getUserMedia` falla, y si no sale nada visible lo arregla ya con un aviso para abrir la app en Chrome.

**Decisión de Miguel sobre la ayuda (15 sep, sobre `auditoria/ismael_ayuda_2026-09-15.md`):**
- **Ayuda: las dos.** Una bienvenida de 3 pasos, sin el de pronunciar, y además la línea de ayuda con «?» en Pronunciar y en el lector.
- **Los tres arreglos, ya:** «Entrar» lleva a «Tu perfil», el icono de Ajustes lleva texto y la tarjeta «Mídeme» se corrige.
- **Recortes:** primero el lector la primera vez, con un solo aviso.

e6 lo hace en tres tandas con visto bueno de 4e. 4e ajusta el guion de la demo cuando salga la bienvenida.
