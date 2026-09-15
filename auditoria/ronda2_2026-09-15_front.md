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
