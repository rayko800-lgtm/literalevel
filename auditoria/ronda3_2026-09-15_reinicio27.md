# Reinicio 27 en el Space, verificado desde fuera

**Para la Central y f4.** Medido por entrega-4e el 15 sep 2026 contra `https://mikemaki1763-literalevel.hf.space` (sha `1708cb1`, desde `9e51c18`), sin cargar nada en local.

**Cómo se midió:**
- La línea base son las mismas peticiones al reinicio 26 (`5c6f8d9`), recogidas a las 07:26, antes de la subida.
- Peticiones con `n: 10`. «Sin perfil» es `ajustar: false`; «B1» es `nivel: 0.80` con `ajustar: true`.
- Antes de medir se hizo una búsqueda de calentamiento.
- Guiones en `D:\literalevel_tmp`:
  - `r27_space_vigia.mjs`, con su salida en `r27_space.json` y `r27_space.log`;
  - `r27_palabras_apellido.mjs`, con su salida en `r27_palabras_apellido.txt`.

## Resumen

- **Los arreglos del 27 se cumplen en el Space.** «cervantes», «dante», «moliere», «agatha christie» y «tolstoy» abren con obras suyas, sin perfil y con B1. «Jane Austen» con B1 abre con *The Watsons*, *Emma* y *Love and Freindship*.
- **Ninguna búsqueda pasa de 1 s.** La más lenta fue «river» con B1 (858 ms); las que hacían saltar la compuerta tardaron entre 485 y 758 ms.
- **`buscador_listo`** pasa a `true` entre los 23,1 y los 26,3 s tras RUNNING (f4 lo midió a los 29,2 s). `catalogo` ya decía `true` en el primer sondeo.
- **SERIO:** las palabras corrientes que también son apellido de un autor devuelven a ese autor en vez del tema. «london», «hope» y «king» cambian por completo respecto al 26, y pasa lo mismo con «school», «rose», «brown», «castle» y otras.

## Clásicos y Austen

«Autor» cuenta los resultados del top 10 cuyo primer autor contiene el apellido. En «moliere» el patrón no casa con «Molière», por la tilde, así que solo se da el top 3.

| Consulta | Perfil | 26, top 3 | 27, top 3 | Autor 26 → 27 | ms (27) |
|---|---|---|---|---|---|
| cervantes | — | History of Beasts · Heads and tales · Horse Stories | The Exemplary Novels · Numantia · The Wanderings of Persiles | 0 → 10 | 598 |
| cervantes | B1 | History of Beasts · Fox and Rooster · Horse Stories | Galatea · Don Quixote · Numantia | 0 → 10 | 618 |
| dante | — | Tin Foil… · Extraction of the Teeth · Monthly Review of Dental… | The New Life · The vision of hell · The Divine Comedy | 0 → 10 | 329 |
| dante | B1 | lo mismo que sin perfil | Divine Comedy (Longfellow) · The New Life · The Banquet | 0 → 10 | 672 |
| moliere | — | An Elementary Study of Insects · Bees · The Garden of Wishes | The Imaginary Invalid · The Flying Doctor · The Bores | top 3 de Molière | 758 |
| moliere | B1 | All insects - Kids song · The Insect Folk · An Elementary Study of Insects | The Impostures of Scapin · The Flying Doctor · The Middle-Class Gentleman | top 3 de Molière | 687 |
| agatha christie | — | Alvira · A Basket of Barley Loaves · The Dolorous Passion | The Plymouth Express Affair · The Missing Will · The Secret of Chimneys | 0 → 10 | 485 |
| agatha christie | B1 | lo mismo que sin perfil | The Mystery of the Blue Train · The Plymouth Express Affair · The Hunter's Lodge Case | 0 → 10 | 529 |
| tolstoy | — | "My Visit to Tolstoy" · The Life of Tolstoy · The Journal of Leo Tolstoi | The Journal of Leo Tolstoi · Tolstoi for the young · The Cossacks | 5 → 10 | 366 |
| tolstoy | B1 | Tolstoi for the young · The Power of Darkness · What Men Live By | lo mismo | 9 → 10 | 375 |
| Jane Austen | — | The Watsons · Love and Freindship · Lady Susan | lo mismo (10 de 10 comunes) | 8 → 8 | 400 |
| Jane Austen | B1 | Pride and Prejudice, a play (MacKaye) · The Watsons · Jane Austen, Her Life (Austen-Leigh) | The Watsons · Emma · Love and Freindship | 7 → 10 | 375 |

## SERIO: palabras corrientes que también son apellido

### Con línea base del 26

| Consulta | Perfil | Comunes con el 26 | Título con la palabra, 26 → 27 | Autor con ese apellido, 26 → 27 |
|---|---|---|---|---|
| london | — | 0/10 | 10 → 0 | 0 → 10 (Jack London salvo uno) |
| london | B1 | 1/10 | 9 → 0 | 1 → 10 |
| hope | — | 0/10 | 10 → 0 | 0 → 10 (Anthony Hope) |
| hope | B1 | 7/10 | 3 → 0 | 7 → 10 (Laura Lee Hope) |
| king | — | 0/10 | 10 → 0 | 0 → 10 (Charles, Basil y Richard King…) |
| king | B1 | 0/10 | 9 → 0 | 0 → 9 |

«king» con B1 era, en el 26, una lista de cuentos de reyes del nivel («The King's Feast», «The Worthy King»…). En el 27 trae «Color mixing guide For artists» (King, John L.), «Texas Gemstones», «Elements of woodwork» y «The Oldest Code of Laws» (Hammurabi, King of).

### Solo en el 27 (sin línea base)

Cifras: autor con la palabra / título con la palabra, en el top 10, sin perfil · con B1.

- **Cambian a autor:**
  - school 10/0 · 10/0, con autores como «Springvalley School» o «The Polymath School»;
  - rose 10/0 · 10/0, que casa también por nombre de pila: «Rose Larsen», «Maia Rose»;
  - brown 10/3 · 10/1, grey 10/0 · 10/1, castle 10/0 · 10/0, white 10/1 · 10/1;
  - green 10/1 · 10/0, bird 10/0 · 10/0, hunt 10/3 · 10/0;
  - wood 10/0 · 10/1, hill 10/1 · 10/0, young 10/3 · 9/2, lamb 10/8 · 10/2.
- **Siguen en el tema:** river, war, dream y sea (0 de autor); moon 2/8; wolf 5/5; love 4/7 · 7/4.

### Causa probable (leída en el código, no aislada en el Space)

- Sin perfil no entra la clave `primero`, y la compuerta de tema no salta porque el parecido de los títulos es alto. Así que el cambio sin perfil viene de `_EXTRA_AUTOR_SOBRE_TITULO`.
- En el 26, el rescate por apellido exacto y el de título exacto empataban, y desempataba el tema, que prefería «The History of London». Con +0,005 gana siempre el autor.
- La prueba de f4 («london, hope y king dan el mismo top 10») comparaba con y sin la exención de la compuerta, no con y sin ese extra.

**Propuesta sin medir:** aplicar el extra solo cuando la palabra es más de autor que de título. Por ejemplo, cuando los títulos que la contienen son menos que las obras de los autores con ese apellido:
- tolstoy tiene pocos títulos con la palabra y muchas obras, así que conserva el extra;
- king, london, school y rose tienen cientos de títulos, así que no.

Hay que medirla con estas mismas palabras antes de subir.

## `buscador_listo` tras RUNNING

Sondeo de `/api/salud` cada ~3 s durante 90 s desde que la API de Hugging Face dio RUNNING con `1708cb1`:

| Segundos tras RUNNING | `buscador_listo` | `catalogo` |
|---|---|---|
| 0,0 · 3,3 · 6,4 · 9,5 · 12,6 · 15,7 · 18,8 · 23,1 | false | true |
| 26,3 y todos los siguientes hasta 88,7 | true | true |

- `puntuador` y `consultor` siguen en `false` los 90 s, porque cargan cuando se usan.
- Con esto, el punto 8 del guion de la demo deja la búsqueda de prueba como lo principal y avisa de «unos 30 s» tras un reinicio.

## Reinicio 28 (`74f1484`, desde `b896b1f`): el SERIO, cerrado en el Space

**Cómo se midió:**
- Las mismas peticiones, desde fuera, tras RUNNING con el sha nuevo.
- Guion `r28_space_vigia.mjs`, con salida en `r28_space.json` y `.log`.
- Referencias:
  - para las 9 búsquedas del 27, mi línea base del 26;
  - para school, brown y castle (y otra vez london, hope y king), el top 10 del 26 que sacó f4 en local con el catalogo.py de 49a8e4d (igual al de 9132a59), en `auditoria/top10_palabras_de_tema_26.json`.

**Resultados:**
- **Palabras corrientes:** london, hope, king, school, brown y castle, sin perfil y con B1, dan **exactamente el mismo top 10 del 26, en el mismo orden** (12 de 12 listas).
- **«rose»:** f4 la añadió a la línea base del 26 en `5a2fc04` (200 listas). En el Space del 28, sin perfil y con B1, da **el mismo top 10 que el 26 y en el mismo orden**. Sin perfil, 10 de 10 llevan «rose» en el título; con B1, 6 son de título y 4 de autoras con ese nombre, igual que en el 26.
- **Clásicos:** siguen bien. cervantes, dante, moliere y agatha christie abren con sus obras, sin perfil y con B1, igual que en el 27.
- **Austen:** «Jane Austen» con B1 abre con *The Watsons*, *Emma* y *Love and Freindship*, como en el 27. Sin perfil queda igual que en el 26.
- **tolstoy:** vuelve al top 10 del 26 (10 de 10, con y sin perfil). Sin perfil abre otra vez con «My Visit to Tolstoy», como aceptó la Central.
- **Tiempos:** la más lenta fue «cervantes» con B1, 1.050 ms; todas las demás, entre 375 y 840 ms. Ninguna pasa de 2 s.
- **`buscador_listo`:** `true` entre los 13,6 y los 16,7 s tras RUNNING; `catalogo`, `true` desde el primer sondeo. Arrancó antes que en el 27 (23,1-26,3 s), así que el «medio minuto» del punto 8 del guion sigue siendo holgado.

## Reinicio 29 (`5ab6832`, desde `7e2b861`): las consultas de autor ya no añaden cuentos por franja

**Cómo se midió:**
- Desde fuera, contra mi línea base del Space del 28 (`74f1484`, recogida antes de la subida, `i4_base28.json`).
- 11 consultas × sin perfil, B1 (0,80) y 1,20, con `n: 24`, los bloques del front publicado y una búsqueda de calentamiento.
- Se compara el top 10, el número de marcas `por_franja` y el bloque de *Crime and Punishment* (PG2554). El orden de la cola, puestos 11-24, no se compara, porque f4 avisó de que varía entre máquinas.
- Guion `r29_space_vigia.mjs`, con salida en `r29_space.json` y `.log`.

**Resultados:**
- **Top 10:** igual al del 28, y en el mismo orden, en las **33 de 33** listas.
- **Sin perfil:** 0 marcas antes y después en todas las consultas.
- **Consultas de autor, marcas del 28 → 29:**

| Consulta | B1 | 1,20 |
|---|---|---|
| Crimen y castigo de Dostoyevski | 4 → **0** | 0 → 0 |
| dostoyevski | 13 → 1 | 15 → 3 |
| cervantes | 12 → **0** | 12 → **0** |
| dickens | 12 → **0** | 17 → 5 |

  - Las marcas que quedan en «dostoyevski» con 1,20 son rusos que ya estaban entre los 24 (*Verotchka's Tales*, *The Precipice*, *Makar's Dream*). Ya no quedan «Books» ni «Story Chikkappa».
  - Aun así, «dostoyevski» con 1,20 deja una tarjeta en «En tu nivel», así que no da el aviso de «no hay libros en tu nivel». El paso 3 sigue con «Crimen y castigo de Dostoyevski».
- **Paso 3 de la demo:** «Crimen y castigo de Dostoyevski» con 1,20 deja «En tu nivel» y «Un poco por encima» vacíos, con *Crime and Punishment* **el primero de «De otros niveles»**, igual que en el 28. Con B1 queda igual y ya sin las 4 marcas.
- **«school» y las de control** (books, library, grade, public, team, children), con B1 y con 1,20: mismas marcas que en el 28 (de 7 a 18 cada una) y los mismos bloques. La regla no toca las consultas que no abren con un libro de Gutenberg rescatado por su autor, y «school» sigue abriendo con «The Polymath School».
- **Tiempos:** entre 378 y 1.039 ms; solo «public» pasa de 1 s (1.005 y 1.039 ms), y ninguna llega a 2 s.
- **`buscador_listo`:** `true` entre los 15,8 y los 19,0 s tras RUNNING.

**Regresión del 29, vista después (f4 y e6):** con 1,20, «león», «brown», «hope» y «animales de la granja» perdían marcas. La regla tomaba por consulta de autor un nombre parecido a la palabra: Cieza de León, Brown, Laura Lee Hope, «Bureau of Animal Industry». Miguel autorizó volver al 28.

## Vuelta atrás al 28 (`62e5a06`, catalogo.py de `b896b1f`)

**Cómo se midió:** las mismas 33 listas que en el 29, desde fuera y contra mi línea base del Space del 28 (`i4_base28.json`), más las cuatro palabras de la regresión frente a las cifras del 28 que dio f4. Guion `r28b_space_vigia.mjs`, con salida en `r28b_space.json` y `.log`.

**Resultados:**
- **Las 33 listas vuelven exactamente al 28:** mismo top 10 en el mismo orden, mismas marcas y *Crime and Punishment* en el mismo bloque.
- **Paso 3 de la demo:** «Crimen y castigo de Dostoyevski» con 1,20 da 0 marcas, «En tu nivel» y «Un poco por encima» vacíos y el libro el primero de «De otros niveles». Con B1 vuelven sus 4 marcas, como en el 28.
- **«dostoyevski» con 1,20:** vuelven a colarse 15 marcas y 9 tarjetas en «En tu nivel», lo esperado en el 28. El guion ya no usa esa consulta.
- **Las cuatro palabras recuperan sus marcas, igual que las cifras del 28 de f4:**
  - «león», 12 con 1,20;
  - «brown», 12 con 1,20;
  - «hope», 9 con 1,20;
  - «animales de la granja», 15 con 1,20, 16 con A2 y 13 con B1.
- **Tiempos:** entre 521 y 1.533 ms, más lentos que en el 29 (hasta 1.039 ms) pero ninguno llega a 2 s. Se midió nada más quedar listo el buscador.
- **`buscador_listo`:** `true` entre los 43,1 y los 46,2 s tras RUNNING. Es más tarde que en los arranques anteriores (14-26 s), y el «medio minuto» del punto 8 del guion se queda corto para este arranque. No sé si fue un arranque lento puntual o si pasa siempre: hay que volver a medirlo en el próximo reinicio.
