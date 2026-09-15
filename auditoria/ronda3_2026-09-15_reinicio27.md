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
