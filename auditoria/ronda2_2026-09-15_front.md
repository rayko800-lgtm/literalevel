# Ronda 2: el front de e6 (15 sep 2026)

**Auditor:** entrega-4e. **HEAD al empezar:** `5b68d64`.

**Diff auditado:** los seis commits de `front/src` desde la publicación `45d9999`:

| Commit | Qué toca |
|---|---|
| `c0ab601` | Encontrar en dos bloques |
| `869baea` | Barra del 3D |
| `cf002c4` | Sombras en `escena.ts` |
| `e663ceb` y `f712d73` | Tiempos |
| `17516a5` | Leyenda del ritmo |

`git log 4d4bb1b..HEAD -- front/src` no da ningún otro. `45d9999` es un commit del Space del front, no del repositorio, así que el diff se leyó commit a commit.

**Front publicado:** `MikeMaki1763/literalevel-front` en `6cfda19`, publicado con el árbol `37c8b92044c8`. Ese árbol es `f712d73:front` y también `5b68d64:front`, así que lo publicado lleva los seis commits [V].

**Método:**
- Chrome en contexto aislado, con viewport 390×844, `mobile` y `touch`, en tema claro.
- Perfil B1 creado con la API del Space y el `X-Lector` de esa pestaña: nivel 0,953, B1, intermedio.
- Búsquedas escritas en el formulario, como una persona.
- La pestaña quedó cerrada.
- **[V]** es ejecutado; **[L]**, solo leído.

---

## Cierre de lo pedido

| Pedido | Resultado | Evidencia |
|---|---|---|
| Los dos bloques con perfil B1 | **Sí**, con una salvedad en «amor» (hallazgo 1) | Ver detalle debajo de la tabla. [V] |
| Ningún resultado irrelevante con etiqueta de encaje | **Sí en «Menos parecidos»; no en «amor»** | Las 25 tarjetas de «Menos parecidos» (2 de «Jane Austen» y 23 de «amor») van sin etiqueta. Pero *Design and tradition* (autor «Fenn, Amor») sale en «De otros niveles» con «Exigente» y no es de amor: hallazgo 1. [V] |
| Botón «Ver también los de otros niveles» | **Sí** | Mide 48 × 358 px. El recuento (14) coincide con lo que abre. Al pulsarlo aparece «De otros niveles» y el botón pasa a «Ocultar los de otros niveles». Si no hay nada en las dos franjas no sale botón: se enseña directamente con el aviso. [V] |
| La boca 3D no queda tapada | **Sí** (ficha del sonido /θ/) | Lienzo de 79 a 499 px (420 px); barra pegada (`sticky`, `bottom: 96px`) de 626 a 746; cabecera de 0 a 65. **0 px tapados**, confirmado en captura a 390 px. Sin error de carga y sin respaldo 2D. La boca 3D del detalle de la corrección no la probé: pide grabar con micrófono. [V] |
| Consola limpia | **Sí** | **0 mensajes de consola** tras las tres búsquedas, la ficha y la boca 3D. Tampoco sale el aviso de three «PCFSoftShadowMap has been removed» (`cf002c4`). Solo hay una *issue* de Chrome, no de consola; ver la nota 4. [V] |
| Tiempos (`e663ceb`, `f712d73`) | **Sí** | En la ficha de SWV991 (71 palabras): chip «1 minuto» y «Tiempo 1 minuto (va por encima de tu nivel)». Ni «1 minutos» ni «entre 1 minuto y 1 minuto» en la página. La API ya devuelve «1 minuto» (`cb799bc`), así que el arreglo del front queda de reserva. [V] |
| Leyenda del ritmo (`17516a5`) | **No probada en el navegador** | Pide una corrección grabada. Cubierta por la especificación `la leyenda de énfasis y de enlaces solo sale si hay alguno que pintar`. [L] y [V prueba] |
| Sin desbordamiento a 390 px | **Sí** | `scrollWidth` = 390 en Encontrar con las tres búsquedas, en Pronunciar con el 3D abierto y en la ficha. [V] |
| Pruebas del front | **62 de 62** | `ng test --watch=false`, 14 archivos. [V] |

**Detalle de los dos bloques con perfil B1:**

| Búsqueda | Qué se ve |
|---|---|
| «detectives en Londres» | «En tu nivel»: 10 tarjetas, las 10 con «A tu medida». «Ver también los de otros niveles (14)» abre «De otros niveles» con 14 tarjetas, las 14 «Exigente». |
| «Jane Austen» | Sale el aviso «no hay libros en tu nivel ni un poco por encima». «De otros niveles»: 22 tarjetas, las 22 «Exigente». «Menos parecidos»: 2, sin etiqueta. |
| «amor» | Sale el aviso. «De otros niveles»: 1 tarjeta, «Exigente». «Menos parecidos»: 23, sin etiqueta. |

**Cotejo con la API:** llamé a `/api/buscar` con n = 24 y el mismo `X-Lector`, y apliqué la regla de `bloquesBusqueda` (margen 0,05 del mejor parecido; «En tu nivel» si −0,45 < d ≤ 0,15; «Un poco por encima» si 0,15 < d ≤ 0,45). Da los mismos recuentos que pinta el front en las tres: 10 y 14; 0 y 22 + 2; 0 y 1 + 23.

---

## Hallazgos

### [MENOR] En «amor», un acierto de nombre falso se lleva el techo y manda todo lo demás a «Menos parecidos»

- **Dónde:** `front/src/app/compartido/bloques-busqueda.ts:95-97`, con el rescate por nombre de `app/catalogo.py:617-622`.
- **Qué dice:**
  > `const techo = Math.max(...libros.map(l => l.similitud));`
  >
  > `if (l.similitud < techo - MARGEN_RELEVANCIA - HOLGURA) { b.menosParecidos.push(l); continue; }`
- **Por qué:**
  - En el Space, el primer resultado de «amor» es *Design and tradition*, del autor «Fenn, Amor», con similitud 0,852. Llega ahí por el rescate por nombre, no por el tema.
  - Con ese techo, todo lo que queda por debajo de 0,801 pasa a «Menos parecidos». Ahí caen *Amour, Amour, Dear Planet!* (0,759), *Historia Amoris* (0,684) y *Amores* (0,684), además de *Air Service Boys* (autor Charles Amory) y *Arms and Armor*.
  - El único libro con etiqueta de encaje es el que no trata de amor, y el aviso dice que lo de otros niveles es «de amor».
  - En «Jane Austen» pasa lo mismo, pero más suave: *Outpost*, *Betty Alden* y *Standish of Standish* son de Jane G. **Austin** y salen en «De otros niveles» con «Exigente».
  - La causa es del catálogo y ya está en `auditoria/ronda2_2026-09-15_catalogo.md` (SERIO, para el reinicio 19 de f4). Lo que añade el front es que un solo falso positivo arriba basta para vaciar los dos bloques.
- **Arreglo:** que el reinicio 19 corrija el rescate. En el front, además, el techo podría calcularse sin los resultados que solo suben por nombre, si la API marcara cuáles son. Hay que repetir «amor» y «Jane Austen» con el 19.

### [MENOR] Accesibilidad de los botones de mostrar y ocultar

- **Dónde:** `front/src/app/pantallas/encontrar.ts`, en el diff de `c0ab601` (líneas 182 y 185 de la plantilla).
- **Qué dice:**
  > `<button type="button" class="boton secundario ver-otros" (click)="verOtros.set(false)" aria-controls="b-otros b-menos">Ocultar los de otros niveles</button>`
  >
  > `<button type="button" class="boton secundario ver-otros" (click)="verOtros.set(true)" [attr.aria-expanded]="false">`
- **Por qué:**
  - «Ver también» dice `aria-expanded="false"` pero no qué controla. «Ocultar» dice qué controla pero no `aria-expanded="true"`.
  - Son dos botones distintos que se sustituyen, así que el lector de pantalla no oye un mismo control que se abre y se cierra.
  - `aria-controls` apunta a `b-menos` aunque esa sección no exista (en «detectives» no la hay).
- **Arreglo:** un solo botón con `[attr.aria-expanded]="verOtros()"`, y `aria-controls` solo con los ids que se pintan.

### [DUDA] «detectives en Londres» no mira Londres, y un cuento de nivel 1 sale como B2

- **Dónde:** el catálogo, no el front (`catalogo.buscar` y la medida en bloque de `tools/medir_corpus.py`).
- **Por qué:**
  - Las 10 tarjetas de «En tu nivel» son cuentos de detectives de StoryWeaver, y ninguno pasa en Londres. Todos los resultados están entre 0,747 y 0,792 de similitud: «Londres» no pesa. [V]
  - SWV991, un poema de nivel 1 del editor («Eyes are red. Why, oh why?», 54 palabras), se ve como **B2 · 1,29**, «va por encima de tu nivel», para una lectora B1. Es la cola del grupo StoryWeaver nivel 1 unida al último bloque (`6945046`), que mide 1,291 [V].
  - Ninguno de los dos es un fallo del front.
- **Qué haría:** que f4 mire si el último bloque de StoryWeaver nivel 1 mide razonable antes del 19.

### [NOTA] La única *issue* de Chrome

- **Qué:** «Lazy-loaded images should have explicit dimensions», sobre `…/api/articulacion/ga/%CE%B8.svg`.
- **Por qué es solo nota:** la `img.corte` de la ficha (`pronunciar.html:302`) sí declara `width="240" height="248"`. Chrome la marca igual, probablemente porque el CSS cambia el tamaño. No es un mensaje de consola ni un error.

### [NOTA] El Space ya publica el catálogo nuevo

`/api/estado` da **68.546** textos (A1 750, A2 5.629, B1 6.100, B2 5.710, C1 24.245 y C2 26.112), y la API devuelve SWV991. Las cifras de los documentos (68.536 y 15.357) ya no coinciden con lo publicado. Según lo acordado, los sincronizo cuando f4 publique el 19. [V]

---

## Comprobado y correcto

- **Build:** lo publicado (`6cfda19`) es el front de `f712d73` y lleva los seis commits. [V]
- **`bloquesBusqueda`** (leído y con prueba):
  - reparte por la misma franja que las etiquetas (0,15 y 0,45);
  - la holgura de 0,001 absorbe el redondeo a tres decimales de la similitud;
  - «Un poco por encima» va del más cercano al más lejano;
  - sin perfil (`nivelBusqueda` a null) se vuelve a la lista de siempre;
  - los recuentos del front cuadran con la regla aplicada a la API en las tres búsquedas.
  
  [L], [V prueba] y [V]
- **Etiqueta y franja cuadran:** todas las tarjetas de «En tu nivel» dicen «A tu medida», todas las de «De otros niveles» dicen «Exigente», y ninguna de «Menos parecidos» lleva etiqueta. [V]
- **La barra del 3D** (`869baea`):
  - `--boca3d-alto` resuelve a 420 px a 390×844;
  - `colocarALaVista` mide la barra donde queda pegada;
  - al abrir el 3D la boca queda entera entre la cabecera y la barra.
  
  [V] y [L]
- **`tiempoLlano`:** «1 minuto» y el rango con los dos extremos iguales dicho una vez; los extremos son tiempos enteros («entre 1 h y 1 h 30 min» no se recorta). Especificación en `formato.spec.ts` y ficha real. [V]
- **`PCFShadowMap`** en lugar de `PCFSoftShadowMap`: sin aviso de three en consola con el 3D abierto. [V]
- **La leyenda** solo explica lo que se pinta (`hayEnfasis`, `hayEnlaces`). [L] y [V prueba]
- **Pruebas:** `ng test` da 62 de 62. [V]

---

## Anexo: el reinicio 19 como persona (e6, 15 sep 2026)

**Qué hay publicado:**
- API en el Space `053a486`, en estado RUNNING.
- Front `548ff40` (`main-D7PFOIU7.js`, con la meta apuntando a la API).

**Método:**
- Chrome en contexto aislado, 390×844, `mobile` y `touch`.
- Perfil B1 **desde el cuestionario del front** (0,80 · B1).
- Búsquedas escritas en el formulario, como una persona.
- Cotejo con `/api/buscar` (n = 24, nivel 0,8) aplicando la regla de `bloquesBusqueda`: los recuentos cuadran con lo que se pinta en las cuatro búsquedas.
- `scrollWidth` = 390 en todas.
- Pestañas cerradas.

| Búsqueda | «En tu nivel» | «Un poco por encima» | «De otros niveles» | «Menos parecidos» | Falsos positivos por nombre |
|---|---|---|---|---|---|
| «amor» | 0 | 0 | 13, todos de amor (C1–C2) | 11, todos de amor | **Ninguno** en los 24: ni «Fenn, Amor» ni «MY FUTURE» [V] |
| «Jane Austen» | 0 | 0 | 8: adaptaciones y libros **sobre** ella | 16, entre ellos **sus novelas** (Emma, Persuasion, Pride and Prejudice, Mansfield Park…) | **Ni rastro de Jane G. Austin.** Se cuelan en «Menos parecidos» *The Frightened Planet* (Sidney Austen) y *Life and Adventures of Calamity Jane* [V] |
| «historias de la luna» | 0 | 0 | 5 tratados y relatos C1–C2 | 19, con **cinco cuentos libres de su nivel** | Ninguno [V] |
| «libros sobre detectives» | 0 | 0 | 9, con dos manuales en cabeza | 15 novelas de detectives | Ninguno: los manuales entran por tema, no por nombre [V] |

En las cuatro sale el aviso «De «…» no hay libros en tu nivel ni un poco por encima entre los resultados. Estos son los de otros niveles.» y no sale botón.

### [SERIO] Lo que sí es del nivel de la lectora queda escondido en «Menos parecidos», y lo arriba es C1 [V]

- **Dónde:** `front/src/app/compartido/bloques-busqueda.ts` (mío), en el margen fijo de 0,05 bajo el mejor parecido.
- **Qué dice:** `if (l.similitud < techo - MARGEN_RELEVANCIA - HOLGURA) { b.menosParecidos.push(l); continue; }`
- **Por qué:**
  - **«historias de la luna».** El techo es *The Moon: A Popular Treatise* (0,802), así que todo lo que queda por debajo de 0,751 es «menos parecido». Ahí caen, sin etiqueta de encaje y detrás de 14 libros C1–C2:
    - *Aditi's Trip To Moon* (A2 · 0,46, similitud 0,738);
    - *Journey To The Moon* (B1 · 0,78, 0,731);
    - *CHANDU AND THE MOON* (0,62, 0,723);
    - *moon and hockey* (0,70, 0,704);
    - *THE MOON AND THE SUN* (0,96, 0,715).

    Son justo lo que una lectora B1 busca con esa frase.
  - **«Jane Austen».** Sus novelas (0,793) quedan bajo los libros cuyo título lleva su nombre (0,857), porque el nombre en el título sube la similitud. La primera tarjeta es la adaptación teatral de MacKaye.
  - El arreglo del 19 funciona: ya no hay falsos positivos por nombre. Pero la pantalla sigue prometiendo «Primero lo de tu nivel y un poco por encima», y en estas cuatro búsquedas no lo cumple.
  - El margen de 0,05 lo copié de `catalogo.MARGEN_RELEVANCIA`. El motor lo usa para ordenar, no para esconder.
- **Arreglo, a decidir con la Central:** no mandar a «Menos parecidos» lo que cae en la franja del lector. Por ejemplo, un margen más ancho solo para los de su nivel, o un tercer bloque «De tu nivel, algo menos parecidos» encima de «De otros niveles». O que la API marque la relevancia en vez de deducirla en el front.

### [NOTA] «amor» ya es honesto, pero para B1 no hay nada

Los 24 resultados son de amor, y ninguno está entre 0,35 y 1,25. Es el hueco de composición del catálogo que ya cuenta la limitación 13 del documento, no un fallo de la búsqueda.

### La boca 3D tras la auditoría de 4e (`5fb4d3a`), publicada en `548ff40`

| Punto | Commit | Estado | Evidencia |
|---|---|---|---|
| Fuga al cerrar (SERIO) | `d911cc2` y `b3ed0d7` | **cerrado** | Build de producción en local, 20 aperturas y cierres de /θ/: montón tras recoger **18,1 MB** (4e midió 48,7 MB con 10); **2 contextos creados, 1 vivo y 0 perdidos**, y los 20 en 3D con la cara de Blender. En el Space, 6 ciclos: 2 contextos creados, 1 vivo, 0 perdidos, todos en 3D. Causa extra: un renderer por apertura quedaba retenido por una textura de módulo de three, así que ahora se reutiliza uno. [V] |
| Audio tras cerrar | `bffc69d` | **cerrado** | En el Space, a 0,5×, «Escuchar y ver» y «Cerrar 3D» en el mismo turno: **ningún `play` ni `start`** en los 3 s siguientes y el visor desmontado. [V] |
| Teclado, icono de giro y `aria-pressed` | `2bbf9ec` | **cerrado** | Lienzo con `tabindex="0"`, `aria-keyshortcuts="ArrowLeft ArrowRight"` y la instrucción en su etiqueta; cuatro flechas pasan de perfil a frente (capturas). «Giro libre» con icono de giro; «reposo» con `aria-pressed`. [V] |
| Pérdida de contexto | `6fa33c0` | **cerrado** | Con `WEBGL_lose_context` cae al SVG de la API, sin canvas ni botones 3D; al cerrar y reabrir crea otro renderer y vuelve a pintar en 3D. [V] |
| README al día | `5cec3ae` | **cerrado** | Comisuras, `PCFShadowMap` con `shadow.radius`, pesos reales (three 736.521 bytes, `cara.glb` 1.902.952, `lengua.glb` 769.224) y cómo se libera el visor. [V] |
| `.glb` sin compresión y comprobación por geometría | — | **abierto** | No lo toqué. |
| Pruebas | — | **65 de 65** | `destruir.spec.ts` y `sonador.spec.ts` nuevas. [V] |
