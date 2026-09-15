# Huecos del catálogo para A2 y B1: cuentos libres que aún no tenemos

- **Autor:** entrega-e6 (811c22), por encargo de la Central.
- **Tipo de trabajo:** estimación en solo lectura. No se bajó ningún texto, no se tocó `corpus_graduado/` ni `catalogo_externo.csv`, y no hubo gasto.
- **Para qué:** que Miguel decida si se amplía el catálogo después de la demo.

## Resumen

1. **Hay pocos textos libres nuevos, y solo en StoryWeaver.** Contando los que llevan el tema en el título y no están en nuestra descarga:

   | Tema | Nuevos |
   |---|---|
   | amigos | 23 |
   | escuela | 12 |
   | familia | 9 |
   | misterios | 9 |
   | deportes | 8 |
   | planetas | 6 |
   | amor | 5 |
   | fantasmas | 5 |
   | monstruos | 5 |
   | piratas | 2 |
   | Navidad | 2 |
   | brujas | 0 |
   | robots | 0 |

   En Let's Read y African Storybook no hay ninguno: lo libre que falta ya está bajado y se descartó al catalogar, casi siempre por tener menos de 150 palabras. La única reserva grande son 2.335 cuentos de nivel 1 a 3 de la web de African Storybook, con la licencia sin comprobar.

2. **El catálogo ya tiene cuentos de estos temas en A2–B1.** Son libres de nivel del editor 1 a 3, con el tema en el título y dificultad del v4 entre 0,20 y 1,00:

   | Tema | En A2–B1 |
   |---|---|
   | amigos | 298 |
   | escuela | 150 |
   | familia | 88 |
   | misterios | 72 |
   | amor | 71 |
   | planetas | 66 |
   | fantasmas | 40 |
   | deportes | 35 |
   | Navidad | 32 |
   | monstruos | 28 |
   | robots | 9 |
   | brujas | 6 |
   | piratas | 1 |

3. **La búsqueda no los saca.** Contra la API del Space `384a206`, con nivel 0,40 y n=24:
   - «Fantasmas» devuelve 23 libros de Gutenberg y un cuento. Hay 40 en A2–B1 con «ghost» en el título.
   - «ghost stories», «Historias de amor» y «Monstruos» devuelven 24 de 24 de Gutenberg.
   - «Robots» sí trae los 9 cuentos, pero con parecido 0,78 frente a un techo de 0,855. Ese salto de 0,075 no lo cruza la regla del front (SALTO 0,05, `bloques-busqueda.ts`), y los 9 caen en «Menos parecidos».

   **Conclusión:** para amor, familia, amigos, escuela, fantasmas, monstruos, misterios, planetas y Navidad, el hueco en A2 y B1 no es de composición del catálogo sino de cómo busca y reparte la app. Ampliar el catálogo no lo arreglaría. Solo piratas, brujas y robots son escasos también en origen. Esto matiza el §3 de la skill buscador-encontrar («si el hueco es de composición, se arregla añadiendo textos»): antes hay que ver si la búsqueda devuelve lo que ya hay.

**Límites:**
- El tema se decide por palabras clave, no por lectura.
- La búsqueda de StoryWeaver reduce las palabras a su raíz y mira el texto entero; por eso se dan dos cotas.
- De African Storybook solo se conoce la licencia de los 368 cuentos del repositorio.
- La comprobación de la búsqueda son 6 consultas con A2 (0,40), no la batería completa.
- Las cifras de las fuentes son del 15 de septiembre.

## Qué se contó y cómo

- **Qué:**
  - cuentos en inglés de **nivel del editor 1 a 3**;
  - con **licencia que podría entrar** según la regla de Miguel (dominio público o CC BY; ni NC ni ND, ni licencia desconocida);
  - de los trece temas que no llegaban con A2 y B1 en Encontrar.
- **Cruce:** con los ids de `catalogo_externo.csv`: `SWV<id>`, `ASB<nnnn>` y `LRD<masterBookId>`, como en `tools/catalogar_corpus.py`.
- **Palabras clave de cada tema** (en inglés, las mismas en las tres fuentes):

| Tema | Palabras |
|---|---|
| amor | love, romance |
| familia | family |
| amigos | friend, friends, friendship |
| deportes | sport, sports, football, race |
| escuela | school |
| piratas | pirate, pirates |
| fantasmas | ghost, ghosts |
| monstruos | monster, monsters |
| brujas | witch, witches |
| robots | robot, robots |
| planetas | planet, planets, space |
| Navidad | christmas |
| misterios | mystery, mysteries, detective |

- **Qué significan las columnas:**
  - **Hay:** los que cumplen tema, nivel y licencia en la fuente.
  - **Ya:** los que están en el CSV.
  - **Faltan:** Hay − Ya.
  - **Faltan, ya bajados:** están en `corpus_graduado/` (leí solo sus metadatos) y se quedaron fuera al catalogar; casi siempre son cortos o el filtro de prosa del v4 los rechazó (skill corpus-graduados, §4 ter).
  - **Faltan, sin bajar:** los únicos que suman textos nuevos.

## StoryWeaver

- **Licencia:** CC BY 4.0 en toda la plataforma, así que todo lo que devuelve podría entrar.
- **Inglés en la API** (15 sep): 5.292 libros de nivel 1, 5.461 de nivel 2 y 3.690 de nivel 3.
- **Cómo se contó:** `books-search` con `levels[]=N` y `query=<palabra>`, paginado entero, y la unión de ids por tema.
- **Tres cosas de la API que cambian cómo leer las cifras:**
  - **La búsqueda reduce a la raíz y mira el texto, no solo el título.** «friend» y «friends» dan los mismos 749 en nivel 2, y en una muestra de «love», nivel 1, salen «My Teacher» o «ROCKS ARENT FOOD!». Por eso hay dos tablas: una con todo lo que menciona la palabra (cota alta) y otra solo con la palabra en el título (cota baja).
  - **Hay filtro por categoría** (`categories[]=`, 38 categorías), pero son amplias: «Family & Friends», «School Stories», «Scary», «Adventure & Mystery», «STEM»… Solo «Scary» (miedo: fantasmas, monstruos, brujas) se contó por categoría; las demás mezclan temas o superan el millar por nivel.
  - **«Faltan, sin bajar»** son libros que hoy están en la API de nivel 1 a 3 y no están en nuestra descarga del 12–14 de septiembre: libros nuevos, o que cambiaron de nivel.

**Con la palabra en el título** (cota baja):

| Tema | Hay (1–3) | Ya | Faltan | Faltan, ya bajados (<150 palabras) | Faltan, sin bajar |
|---|---|---|---|---|---|
| amor | 104 | 92 | 12 | 7 (5) | 5 |
| familia | 124 | 105 | 19 | 10 (10) | 9 |
| amigos | 409 | 359 | 50 | 27 (23) | 23 |
| deportes | 58 | 44 | 14 | 6 (6) | 8 |
| escuela | 205 | 176 | 29 | 17 (13) | 12 |
| piratas | 9 | 6 | 3 | 1 (1) | 2 |
| fantasmas | 59 | 49 | 10 | 5 (3) | 5 |
| monstruos | 46 | 37 | 9 | 4 (1) | 5 |
| brujas | 11 | 10 | 1 | 1 (1) | 0 |
| robots | 14 | 11 | 3 | 3 (2) | 0 |
| planetas | 99 | 86 | 13 | 7 (4) | 6 |
| Navidad | 42 | 37 | 5 | 3 (2) | 2 |
| misterios | 118 | 100 | 18 | 9 (2) | 9 |

**Con la palabra en cualquier parte** (cota alta; lo que devuelve `query=`):

| Tema | Hay (1–3) | Ya | Faltan | Faltan, ya bajados (<150 palabras) | Faltan, sin bajar |
|---|---|---|---|---|---|
| amor | 1.123 | 1.007 | 116 | 67 (46) | 49 |
| familia | 1.035 | 930 | 105 | 59 (39) | 46 |
| amigos | 2.449 | 2.197 | 252 | 144 (102) | 108 |
| deportes | 200 | 171 | 29 | 14 (10) | 15 |
| escuela | 814 | 731 | 83 | 45 (31) | 38 |
| piratas | 28 | 22 | 6 | 2 (2) | 4 |
| fantasmas | 350 | 271 | 79 | 50 (40) | 29 |
| monstruos | 101 | 85 | 16 | 7 (4) | 9 |
| brujas | 43 | 38 | 5 | 4 (3) | 1 |
| robots | 58 | 46 | 12 | 9 (6) | 3 |
| planetas | 261 | 236 | 25 | 14 (9) | 11 |
| Navidad | 63 | 56 | 7 | 4 (2) | 3 |
| misterios | 592 | 512 | 80 | 32 (7) | 48 |
| *categoría «Scary»* | 251 | 223 | 28 | 10 (7) | 18 |

Un mismo libro puede contar en varios temas, así que las filas no se suman.

## Let's Read

- **Cómo se contó:** el listado de la API por nivel (`/book/elastic/search/…&readingLevel=N`) de 1, 2 y 3. Son 1.008 filas y 1.003 libros distintos por `masterBookId`: 305, 415 y 283.
- **Licencias de esos 1.003:**

| Licencia | Libros |
|---|---|
| CC-BY-4.0 | 465 |
| CC-BY-3.0 | 13 |
| CC-BY-NC-4.0 | 388 |
| CC-BY-NC-ND-4.0 | 54 |
| Copyright | 52 |
| CC-BY-NC-SA-4.0 | 27 |
| CC-BY-NC-3.0 | 1 |
| vacía | 3 |

  Podrían entrar **478**: los 465 de CC-BY-4.0 y los 13 de CC-BY-3.0. Ya tenemos 311. Los otros **167 están bajados** y se quedaron fuera al catalogar; 59 de ellos tienen menos de 150 palabras.
- **Por etiqueta no se puede contar casi nada.** La API trae `tags`, pero solo 15 distintos, y de los trece temas solo encaja «Family & Friendship»: 157 libres, 108 ya en el catálogo y **49 que faltan**. No hay etiquetas de deportes, escuela, espacio, fiestas ni misterio. Por eso, abajo, cuentan las palabras clave en título y descripción.

| Tema | Hay (libres, 1–3) | Ya | Faltan | Faltan, ya bajados (<150 palabras) | Faltan, sin bajar | NC u otra no libre |
|---|---|---|---|---|---|---|
| amor | 7 | 3 | 4 | 4 (2) | 0 | 7 |
| familia | 22 | 18 | 4 | 4 (1) | 0 | 23 |
| amigos | 76 | 53 | 23 | 23 (7) | 0 | 87 |
| deportes | 6 | 6 | 0 | 0 | 0 | 6 |
| escuela | 38 | 31 | 7 | 7 (1) | 0 | 34 |
| piratas | 0 | 0 | 0 | 0 | 0 | 0 |
| fantasmas | 1 | 1 | 0 | 0 | 0 | 0 |
| monstruos | 0 | 0 | 0 | 0 | 0 | 7 |
| brujas | 1 | 0 | 1 | 1 (0) | 0 | 1 |
| robots | 0 | 0 | 0 | 0 | 0 | 1 |
| planetas | 1 | 1 | 0 | 0 | 0 | 6 |
| Navidad | 1 | 1 | 0 | 0 | 0 | 0 |
| misterios | 3 | 2 | 1 | 1 (0) | 0 | 2 |

**Lectura:** Let's Read no tiene textos libres nuevos para estos temas; todo lo libre ya está bajado. Lo que falta son descartes del catalogado, y en los temas vacíos (piratas, monstruos, robots) no hay nada libre ni siquiera en la fuente.

## African Storybook

- **Por tema no se puede contar desde sus datos.** `booklistjs.php` no trae categorías, solo `id`, `title`, `summary`, `level`, `approved` y un campo `other` que repite el nivel («first words», «first sentences», «first paragraphs»…). Conté las palabras clave en título y resumen.
- **La licencia solo se conoce de los 368 cuentos en inglés de `global-asp/asp-source`.** De ellos, 316 son CC-BY; son los que ya bajamos, y leí solo sus metadatos en `corpus_graduado/african_storybook/textos/cuentos.jsonl`.
- **Lo que hay en la web y no en el repositorio.** La web lista 3.183 libros en inglés, 2.565 de nivel 1 a 3 (1.017 aprobados en total). 2.335 de nivel 1 a 3 no están en el repositorio y **no tienen licencia comprobada**. Por la regla de Miguel no cuentan como «podría entrar»; van en la última columna, solo como orientación.
- **Libres de nivel 1 a 3 en el repositorio:** 162. Tenemos 134. Los **28 que faltan están bajados**; 25 tienen menos de 150 palabras (mediana 67). Otros 68 del repositorio no cruzan con la web y se quedan sin nivel.

| Tema | Hay (libres, 1–3, repo) | Ya | Faltan (todos ya bajados) | NC en el repo | En la web, licencia sin comprobar |
|---|---|---|---|---|---|
| amor | 2 | 0 | 2 | 1 | 96 |
| familia | 9 | 5 | 4 | 1 | 110 |
| amigos | 18 | 17 | 1 | 1 | 257 |
| deportes | 2 | 2 | 0 | 0 | 30 |
| escuela | 6 | 4 | 2 | 3 | 164 |
| piratas | 0 | 0 | 0 | 0 | 2 |
| fantasmas | 0 | 0 | 0 | 0 | 0 |
| monstruos | 0 | 0 | 0 | 0 | 1 |
| brujas | 0 | 0 | 0 | 0 | 3 |
| robots | 0 | 0 | 0 | 0 | 2 |
| planetas | 0 | 0 | 0 | 0 | 13 |
| Navidad | 0 | 0 | 0 | 0 | 11 |
| misterios | 0 | 0 | 0 | 0 | 5 |

**Lectura:** en lo que tiene licencia comprobada tampoco hay nada nuevo. La reserva real de African Storybook son los 2.335 de la web sin licencia comprobada. Amigos (257), escuela (164), familia (110) y amor (96) son los temas con más; los temas de miedo y fantasía no llegan a 15. Antes de contar con ellos habría que ver la licencia de cada cuento en su ficha, y eso no se hizo aquí.
