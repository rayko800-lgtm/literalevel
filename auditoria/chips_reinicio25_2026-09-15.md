# Chips de Encontrar sobre el reinicio 25

**Para la Central y e6.** Medido por entrega-4e el 15 sep 2026 contra el Space `4ba66f9` (reinicio 25, con la franja), solo lectura. No se cambió ningún chip.

**Resumen:**
- **Los 8 chips actuales cumplen el criterio de e6 con margen,** y casi todo lo que traen es del tema.
- **De reserva cumplen los 8,** pero «Cuentos de hadas» lo hace sin cuentos de hadas: 0 del tema con A2 y 1 con B1.
- **De los 13 que antes no llegaban:**
  - cumplen 12, y 11 traen al menos 3 del tema con A2 y con B1;
  - «Monstruos» cumple en número con 1 solo del tema;
  - «Piratas» no llega con A2 (2).
- **El criterio de e6 cuenta tarjetas, no tema.** Con la franja del 25, un chip puede llenar sus bloques con cuentos del nivel que no son de lo que pide.
- **En la página publicada, a 390 px con un B1 guardado desde el cuestionario:**
  - lo marcado por la franja cae en «En tu nivel» o en «Un poco por encima» en las tres búsquedas;
  - la página no se desborda;
  - la consola no tiene errores ni avisos.

## Cómo se midió

- **Bloques:** `bloquesBusqueda` del front publicado. El front `657ea8f` sirve `b9773bd`, y `bloques-busqueda.ts` y `encontrar.ts` son idénticos entre `b9773bd` y HEAD.
  - Se compiló con el esbuild de `front/` y se aplicó en Node a las respuestas reales de `/api/buscar`, con la `franja` que devuelve la API.
- **Petición:** `{consulta, nivel, ajustar: true, n: 24}`, con A2 = 0,40 y B1 = 0,80.
- **Criterio (e6, `4e6276e`):** al menos 3 entre «A tu medida» y «Un poco por encima», con A2 y con B1.
- **Tiempos:** hice una búsqueda de calentamiento antes de medir. Tardó 0,7 s, así que el Space ya estaba despierto. Todas las búsquedas medidas tardaron entre 0,4 y 0,9 s.
- **«Del tema»:** un patrón por chip sobre título y gancho (en inglés, porque el catálogo lo es), escrito en el guion **antes** de ver ninguna respuesta.
  - En «Cuentos cortos para empezar», del tema es un texto libre corto, es decir, con id que no empieza por PG.
  - **Es una aproximación,** revisada a mano solo en los chips que se dicen abajo.
- **Guion y salida:** `D:\literalevel_tmp\chips_r25.mjs`, `chips_r25_tabla.txt` y `chips_r25_salida.json` (con cada tarjeta de los dos bloques, marcada + o − según el patrón).

## Tabla

Formato: **medida / encima (del tema)**. «Marc.» son los que la API marca `por_franja`.

### Los 8 actuales

| Chip | A2 | Marc. A2 | B1 | Marc. B1 | Cumple |
|---|---|---|---|---|---|
| Detectives | 1 / 9 (9) | 8 | 12 / 2 (13) | 9 | sí |
| El océano | 7 / 9 (15) | 9 | 17 / 1 (16) | 9 | sí |
| Una historia de amistad | 11 / 11 (22) | 20 | 19 / 2 (21) | 19 | sí |
| Cuentos cortos para empezar | 4 / 6 (10) | 7 | 8 / 4 (12) | 9 | sí |
| Viajes al espacio | 3 / 4 (7) | 5 | 5 / 5 (10) | 8 | sí |
| Dinosaurios | 7 / 6 (13) | 9 | 11 / 3 (14) | 12 | sí |
| Cuentos de miedo para niños | 9 / 2 (9) | 10 | 8 / 2 (8) | 10 | sí |
| Animales de la selva | 9 / 8 (16) | 12 | 17 / 2 (18) | 13 | sí |

«Viajes al espacio», que en el 21 estaba justo en el mínimo (A2 1/2, B1 2/3), ya tiene 7 y 10 tarjetas.

### De reserva (los que e6 dio por buenos en `4e6276e`)

| Chip | A2 | Marc. A2 | B1 | Marc. B1 | Cumple |
|---|---|---|---|---|---|
| **Cuentos de hadas** | 3 / 12 (**0**) | 12 | 8 / 9 (**1**) | 13 | sí, **sin tema** |
| Cuentos de dragones | 8 / 6 (14) | 13 | 15 / 8 (22) | 16 | sí |
| Historias de la luna | 4 / 11 (15) | 15 | 14 / 2 (16) | 16 | sí |
| Magia | 6 / 9 (14) | 15 | 13 / 2 (14) | 15 | sí |
| Música y baile | 6 / 6 (12) | 12 | 7 / 6 (12) | 12 | sí |
| Aventuras en la selva | 10 / 4 (14) | 9 | 14 / 1 (15) | 9 | sí |
| Un viaje en tren | 6 / 8 (14) | 12 | 12 / 0 (12) | 10 | sí |
| Superhéroes | 5 / 7 (12) | 10 | 12 / 1 (12) | 11 | sí |

### Los que no llegaban en el 21

| Chip | A2 | Marc. A2 | B1 | Marc. B1 | Cumple |
|---|---|---|---|---|---|
| Historias de amor | 5 / 7 (6) | 12 | 7 / 5 (8) | 12 | sí |
| Familia | 6 / 6 (12) | 12 | 12 / 1 (13) | 13 | sí |
| Fantasmas | 9 / 4 (13) | 13 | 10 / 3 (13) | 13 | sí |
| **Monstruos** | 6 / 6 (**1**) | 12 | 10 / 2 (**1**) | 12 | sí, **sin tema** |
| Amigos inseparables | 12 / 10 (22) | 21 | 20 / 0 (20) | 19 | sí |
| Deportes | 1 / 4 (4) | 5 | 5 / 2 (6) | 7 | sí |
| Historias de la escuela | 5 / 8 (13) | 13 | 12 / 2 (13) | 13 | sí |
| **Piratas** | **0 / 2** (2) | 2 | 1 / 3 (4) | 4 | **no** (A2) |
| Brujas y magia | 6 / 7 (13) | 13 | 11 / 2 (13) | 13 | sí |
| Robots | 6 / 4 (10) | 9 | 7 / 1 (8) | 7 | sí |
| Planetas y estrellas | 7 / 8 (15) | 15 | 11 / 9 (19) | 20 | sí |
| Navidad | 10 / 2 (12) | 12 | 11 / 2 (13) | 12 | sí |
| Misterios para resolver | 7 / 6 (12) | 13 | 8 / 5 (13) | 13 | sí |

## Revisado a mano

- **Cuentos de hadas:**
  - Con A2 las 15 tarjetas son cuentos del nivel sin hadas ni princesas: «HOLE», «Suma», «ALIEN BOT», «Biryani», «Kuppu»… La más cercana es «SANGKURIANG», una leyenda.
  - Con B1, el único + del patrón es «BOLDNESS», por «Once upon a time», y tampoco es un cuento de hadas.
  - **A mano: 0 y 0.**
- **Monstruos:**
  - El único del tema es «The book monster».
  - Rozan el tema «THE LEGEND» (zombis) y, con B1, «THE DIARY OF A CREEPY THING».
  - El resto son «An A-maize-ing Story», «sambar story», «The mysterious book»… **A mano: 1-3 de 12.**
  - Es el límite que f4 declaró en el 25: «Monstruos» 1/12 con todas las variantes.
- **Historias de amor:**
  - El patrón da 6 y 8, pero «Love friends» (un desayuno) y «ADA LOVELACE» (por «loved machines») no son del tema.
  - Varios son de amor entre hermanos o de familia: «The bond of love», «THE TREE OF LOVE».
  - Siguen colándose tres «My story».
  - **A mano: unos 5 con A2 y 7 con B1,** del tema en sentido amplio.
- **Deportes:** 4 de 5 con A2 y 6 de 7 con B1, bien contados. Sobra «THE STORY OF A GAMER».
- **Piratas:**
  - Con A2 solo hay 2: «Captain Hook» e «I Want To Be A Pirate».
  - Con B1 son 4, y los 4 son de piratas.
- **También miré, y el patrón acierta:** Cuentos de miedo para niños con B1 (8 de 10, sobran «Child safety» y «The Hardships of a Kid»), Superhéroes con B1 (12 de 13) y Robots con A2 (10 de 10).

## En la página publicada

**Montaje:**
- front `https://mikemaki1763-literalevel-front.static.hf.space` (657ea8f) con la API `4ba66f9`, en un contexto aislado sin cuenta;
- 390×844 táctil (DPR 3).

**Perfil:**
- El B1 se guardó desde el cuestionario de la página, con las 6 respuestas del perfil B1 fijado en `88c28d5`.
- Resultado: «Lees en inglés a nivel B1 · 0,95 de 2», franja de la API [0,503, 1,403].
- Es la cabecera anónima de ese contexto, no la cuenta de nadie.

**Búsquedas** (el front pide `n: 24`, `ajustar: true`; capturé la respuesta que recibió la página y leí los bloques pintados, con «Ver también» abierto):

| Búsqueda | Resultados | Marcados | En «En tu nivel» | En «Un poco por encima» | En otro bloque |
|---|---|---|---|---|---|
| Fantasmas | 36 | 12 | 10 | 2 | **0** |
| historias de la luna | 36 | 17 | 15 | 2 | **0** |
| Robots | 24 | 6 | 4 | 2 | **0** |

- **Títulos muy cortos:** «The Ghost», «Ghost» y «moon» aparecen como texto en varios bloques porque otros títulos los contienen. Sí están en uno de los dos bloques buenos, pero con esta lectura no puedo descartar que haya además una copia en otro bloque.
- **Desborde:** con «Ver también» abierto, en las tres búsquedas, `scrollWidth` = `clientWidth` = 390 y no hay elementos de `main` que pasen del ancho.
- **Consola:** sin errores ni avisos, contando los mensajes conservados de toda la sesión de la página.
- **Captura:** «Robots» con B1, en el scratchpad de 4e (`chips_r25_robots_b1_390.png`). No hay capturas de fallos porque no hubo ninguno.

## Para e6 (sin aplicar)

1. **Los 8 actuales se pueden quedar.** El más justo, «Deportes» aparte, es «Viajes al espacio», con 7 y 10 tarjetas y 7 y 10 del tema.
2. **«Cuentos de hadas» no debería entrar como reserva.** Cumple el mínimo de tarjetas, pero no trae cuentos de hadas.
3. **Ya pueden ser chips,** con al menos 6 del tema en A2 y en B1: Historias de amor, Familia, Fantasmas, Amigos inseparables, Historias de la escuela, Brujas y magia, Robots, Planetas y estrellas, Navidad y Misterios para resolver.
   - Deportes también cumple, pero va justo con A2 (5 tarjetas, 4 del tema).
   - Monstruos no: cumple en número, pero no en tema.
   - Piratas no: con A2 se queda en 2.
4. **Propuesta de criterio para la próxima medida:** contar **del tema**, no solo tarjetas, porque con la franja un chip puede cumplir con cuentos que no son de lo que pide. Algo como «al menos 3 del tema entre los dos bloques, con A2 y con B1», revisado a mano.
