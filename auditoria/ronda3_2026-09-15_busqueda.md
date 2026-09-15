# Ronda 3: la búsqueda y el catálogo del reinicio 19 (15 sep 2026)

- **Auditor:** entrega-4e.
- **HEAD al empezar:** `13ad84a`.
- **Qué se audita:** `git diff 6945046..bffc69d -- app/catalogo.py app/api.py no_lectura_externo.csv`:
  - `7d94bd9`: nombre endurecido, palabra suelta en frases, filas sin título;
  - `a557288`: anuncios;
  - `c63ce44`, que entra por `app/api.py`: el 422 sin eco y el candado de subidas.

  Con ellos, la regla de anuncios de `tools/marcar_no_lectura.py` en `bffc69d`.
- **No auditado, por encargo:** «Jane Austen» y los bloques raros, que van en el 21.
- **Informe anterior:** `auditoria/ronda2_2026-09-15_catalogo.md`, mío. Solo para la tabla de cierre; lo nuevo, a ciegas en el diff.
- **Space publicado:** `MikeMaki1763/literalevel` en `af72fb0`. Sobre `053a486` solo cambia `app/voz.py` y `app/lexicon.py`, así que catálogo y API son los de `053a486` = `bffc69d` [V].
  - `/api/estado` da 68.546 [V].
  - Todas las posiciones que cito son del Space, con `/api/buscar` sin nivel (`ajustar: false`), salvo donde digo «en local».
- **Cuidado con HEAD:** después de `bffc69d` hay un commit de f4 sobre `app/catalogo.py` (`7c9c289`: nombre entero del autor y bloques raros), que va para el 21.
  - Por eso no uso HEAD para posiciones.
  - Solo lo uso para medir un paso que ese commit no toca (el margen semántico, hallazgo 1), y lo confirmo en el Space.
- **Pruebas:** `pruebas_corpus.py` **39 de 39** en `40cdcd4` y `pruebas_api.py` **55 de 55** en `42de4cb`, con `LITERALEVEL_SIN_CLAVES=1` y TEMP en D: [V]. El banco de mutantes C6 y C7 no lo corrí.
- **[V]** es ejecutado; **[L]**, solo leído.

---

## Cierre de la ronda 2

| Hallazgo de la ronda 2 | Estado | Evidencia |
|---|---|---|
| **SERIO.** El rescate por nombre se lleva por delante las búsquedas temáticas en español | **cerrado** | [V] Detalle debajo de la tabla. |
| **MENOR.** Anuncios con enlaces visibles en las tarjetas | **a medias** | [V] Detalle debajo de la tabla; siguen visibles otros anuncios sin llamada (hallazgo 3). |
| **MENOR.** Las cifras del catálogo externo cambian | **cerrado** | [V] `/api/estado` da 68.546, y los documentos lo dicen desde `13ad84a`. |
| **DUDA.** Ganchos cortos | sin cambios, como se esperaba | [V] 565 ganchos con menos de 12 palabras y 1.189 que acaban en «…», en `bffc69d`. |

**Las tres consultas de tema de la ronda 2** dan hoy exactamente la lista que en la ronda 2 daba la semántica sola:

| Consulta | Primeros resultados en el Space |
|---|---|
| «cuentos sobre la lluvia y los agricultores» | *Rain* 0,684, *The Water Seed* 0,664, *Girl and a farmer* 0,659, *The Duet of Rainmakers* 0,655 |
| «historias sobre la lluvia y los agricultores» | los mismos cuatro, en otro orden |
| «viaje al espacio y la luna» | *To Mars via the Moon* 0,737, *Journey To The Moon* 0,721, *Journey to Space* 0,705, *A Voyage to the Moon* 0,699 |

- Ni *Forest Sombre*, ni *Historians*, ni *Luna: The Lost Dog*.
- «sobre» sola ya no rescata *Sombre*.

**Los anuncios de la ronda 2:**
- Los seis visibles que di están ahora en `no_lectura_externo.csv`:
  - por regla: SWV59417, SWV551720, SWV600113, SWV642071 y SWV642072;
  - revisado a mano: SWV687758.
- SWV589104 cambia de motivo a «anuncio o enlace comercial».
- Las URL ya no están en ganchos ni huellas: en `bffc69d`, las 7 coincidencias de `www.` son onomatopeyas («Ewwwwwwwwwwwww…», «POWWWW…»), ninguna un enlace.

---

## Hallazgos nuevos

### [SERIO] El margen semántico apaga el rescate de autores clásicos: «cervantes», «dante» y «moliere» no encuentran a su autor

- **Dónde:** `app/catalogo.py:693-696` en `bffc69d`, con `MARGEN_SEMANTICO_NOMBRE = 0.20` (`:215`).
- **Qué dice:**
  > `if con_nombre.any() and validos.any() and \`
  >
  > `        float(sem[con_nombre].max()) < float(sem[validos].max()) - MARGEN_SEMANTICO_NOMBRE:`
  >
  > `    lex = np.zeros_like(lex)          # se escribe parecido y no tiene que ver con lo pedido`
- **Por qué:**
  - **En el Space** [V], los cinco primeros:

    | Consulta | Primeros resultados | Libros visibles cuyo autor contiene «Cervantes», «Dante» o «Moli» (en local) |
    |---|---|---|
    | «cervantes» | *History of Beasts*, *Heads and tales*, *Horse Stories…*, *Stories of the Universe: Animal Life*, *Fox and Rooster* | 53 |
    | «dante» | *Tin Foil and Its Combinations for Filling Teeth*, *Extraction of the Teeth*, *The Monthly Review of Dental Surgery*… | 43 (puede incluir a Dante Gabriel Rossetti) |
    | «moliere» | *An Elementary Study of Insects*, *Bees*, *The Garden of Wishes*, *The Insect Folk*… | 25 |

    Ninguno de esos libros sale entre los 10 primeros. *The History of Don Quixote* sí sale, quinto, con «don quijote».
  - **Por qué se apaga, medido en local** [V]: repetí los pasos de `buscar`. HEAD cambia cómo se calcula el nombre (`7c9c289`), pero no el conjunto `con_nombre` de una palabra ni este margen.

    | Consulta | Mejor parecido semántico del catálogo | Mejor semántico entre los libros con nombre | ¿Se apaga? |
    |---|---|---|---|
    | cervantes | 0,727 | 0,441 | sí |
    | dante | 0,716 | 0,460 | sí |
    | moliere | 0,747 | 0,523 | sí |
    | balzac, dumas, hugo, platon, homero, virgilio, tolstoy, dickens | — | — | no, y el autor llena los 10 primeros |

  - Sin el margen, el apellido acertado vale `lex = 1,0` y `1,0 × _PESO_NOMBRE = 0,85`, por encima de 0,727: el autor iría delante. Es lo que hacía el código de `6945046` [L].
  - **La causa:** una palabra suelta se incrusta además en «historias de dante» y «libros sobre dante», y el modelo lo acerca a «dent-» y a otros temas. Los libros de Dante, que no hablan de sí mismos, quedan lejos.
  - El margen se calibró con nombres cuyas obras sí se parecen a la consulta (el comentario de `:207-214`: chejov, Austen, *Midsummer*, dostoyevski, dickens, *Frankenstein*, *Sambo*). Los autores clásicos que se escriben en español fallan. Justo es lo que el documento anuncia que funciona («dostoyevski», «chejov»).
  - `7c9c289`, que va para el 21, no toca este paso.
- **Arreglo:**
  - que un apellido acertado casi exacto (`lex` ≥ 0,95, o el apellido entero tal cual) rescate siempre, y dejar el margen para los parecidos parciales («amor» ≈ «Amory», 0,8);
  - o no aplicar el margen cuando la consulta es una sola palabra que es apellido de algún autor del catálogo;
  - y añadir «cervantes», «dante» y «moliere» a `_busquedas_reales_en_espanol`.

### [MENOR] Con nombre y apellido, las obras del autor quedan detrás de las de otros con el mismo apellido (lo anuncia el 21)

- **Dónde:** `app/catalogo.py:286-293` en `bffc69d` (`_apellidos`) y `:691`.
- **Qué dice:**
  > `"""… «Fenn, Amor» da «Fenn»: un nombre de pila no rescata."""`
  >
  > `return " ".join(a.split(",")[0] for a in str(autor).split(";"))`
- **Por qué:**
  - **En el Space** [V]:
    - «agatha christie» saca primero *Christmas on the briny* (W. Bede Christie), *A List of Philippine Baptismal Names*, *A Love Story* (William Harvey Christie) y *Embroidery and Tapestry Weaving* (Grace Christie). Agatha Christie ocupa 11 de las posiciones entre la 5 y la 16;
    - «emily bronte» saca *Emily Brontë* (una biografía), *Agnes Grey* (Anne), *Cottage Poems* (Patrick) y *Villette* (Charlotte); ninguna novela de Emily en los 6 primeros.
  - **Medido** [V] el parecido de nombre de las obras del autor, con las fichas de antes (título y autor) y las de ahora (apellidos):

    | Consulta | Antes | Ahora |
    |---|---|---|
    | «agatha christie» | 1,000, y 0 libros de otros con igual o más | 0,925, y 5 de otros con igual o más |
    | «emily bronte» | 1,000, y 2 de otros | 0,925, y 12 de otros |

  - Al quitar el nombre de pila, la consulta cubre una palabra de dos, y el castigo por palabras sin cubrir de `_similitud_nombres` iguala al autor con cualquiera que comparta apellido.
  - La Central dice que el reinicio 21 lo cierra (nombre de pila y apellido juntos cuentan como coincidencia completa). Lo apunto para comprobarlo entonces; no lo he medido sobre `7c9c289`.
- **Arreglo:** el del 21. Que la prueba incluya un autor con homónimos de apellido («agatha christie») además de «Jane Austen».

### [MENOR] Siguen visibles anuncios largos sin «llamada», y la búsqueda los pone primeros

- **Dónde:** `tools/marcar_no_lectura.py:94` en `bffc69d`, con `_LLAMADA` (`:58`) y `MAX_PALABRAS_ENLACE = 30` (`:60`).
- **Qué dice:**
  > `if fuente == "storyweaver" and _enlace_comercial(cuerpo) and (_LLAMADA.search(cuerpo) or len(_URL.sub(" ", cuerpo).split()) <= MAX_PALABRAS_ENLACE):`
- **Por qué:**
  - La regla pide una llamada de las de la lista, o un texto de 30 palabras o menos. Un artículo publicitario largo con «Website -», «Visit To Buy Now:-», «Visit website :», «Follow these links» o «Trang web:» pasa.
  - **Recorrido** [V] de los textos servidos (`corpus_abierto.parquet`) que no están excluidos: 74 llevan un enlace ajeno a las cuatro bibliotecas y a Bilum Books. Casi todos son citas legítimas (UNESCO, un proyecto de Oxford, referencias de un trabajo escolar). Pero estos nueve son anuncios o promoción, y todos están visibles:

    | Texto | Letra | Qué es |
    |---|---|---|
    | SWV573562 | B2 | «Apartments in Dabolim Provident Housing» (precios y dirección) |
    | SWV602973 | B2 | «Painting contractors in Coimbatore» |
    | SWV616784 | C1 | «Secrets of Pure Oil for Cooking», con «Visit To Buy Now:-» |
    | SWV641941 | B2 | «AK prefab- Security guard room construction in UAE» |
    | SWV642960 | B1 | «baby clothing», con «Follow these links» |
    | SWV651227 | A2 | «day curoa gates», en vietnamita, con teléfono y web |
    | SWV670926 | C1 | «Liquid Detergent: A B2B Guide for Manufacturers» |
    | SWV307241 | A2 | «sudha yoga», con «if you want to join please visit» |
    | SWV639007 | B1 | cuento con el enlace de una web comercial al final (dudoso) |

  - **En el Space** [V], la búsqueda los da **primeros**:
    - «painting contractors» → SWV602973 (0,856);
    - «apartments in goa» → SWV573562;
    - «liquid detergent supplier» → SWV670926;
    - «prefab security guard room» → SWV641941.

    Y con nivel pueden salir al recomendar, porque tienen letra de A2 a C1.
- **Arreglo:** ampliar `_LLAMADA` («visit to buy», «visit website», «website -», «follow these links», teléfono con prefijo o «Address -») y pasar los nueve por `ANUNCIOS_REVISADOS`. Después, volver a generar `no_lectura_externo.csv`.

### [MENOR] Los 89 libros de Gutenberg sin título salen de buscar y de recomendar, y son libros de verdad

- **Dónde:** `app/catalogo.py:554-556` en `bffc69d`.
- **Qué dice:**
  > `sin_titulo = (titulo.isna() | titulo.astype(str).str.strip().isin(["", "nan"])).to_numpy()`
  >
  > `self._excl = self._excl | sin_titulo`
- **Por qué:**
  - En `catalogo_medido.csv` hay 89 filas con `title` vacío, y también `author` vacío [V].
  - El arreglo evita que su vector («nan. nan.») encabece búsquedas, que era el fallo. Pero los libros existen y están medidos. Cuatro de ellos, con su título en gutenberg.org [V]:
    - PG8177, *The Esperanto Teacher* (Helen Fryer);
    - PG9090, *Germania and Agricola* (Tacitus);
    - PG20775, *The Annals of the Cakchiquels*;
    - PG70998, *The complete works of John Gower*, vol. 1.
  - En el Space, «the esperanto teacher» no devuelve PG8177, y «germania and agricola tacitus» no devuelve PG9090 [V]. Quedan invisibles también al recomendar.
- **Arreglo:** rellenar título y autor desde la instantánea del catálogo oficial (la de 79.337 entradas del 7 de septiembre) antes de calcular el vector, y excluir solo las filas que sigan sin título.

### [DUDA] «luna» sola sigue sacando títulos con «Luna» y no la luna

- **Dónde:** `app/catalogo.py:296` en `bffc69d` (`_titulo_completo`), junto con `FRASES_PALABRA_SUELTA` (`:223`).
- **Por qué:**
  - En el Space [V], «luna» da *Fantasy of Luna*, *LUNA'S ADVENTURE TO MOON*, *Luna and the Stars*, *Luna Escapade*, *The Song of Luna* y *Luna: The Lost Dog*, todos a 0,854-0,856.
  - Una sola palabra que es entera una palabra del título cuenta como título completo, y el margen no la apaga porque alguno de esos libros sí trata de la luna.
  - «cuentos de la luna» da libros sobre la luna, así que es solo la palabra sola. Es ambiguo («Luna» es también un nombre); no lo doy por fallo.
- **Qué haría:** si se quiere que una palabra suelta en español busque su tema, que `_titulo_completo` no puntúe cuando la consulta es una sola palabra común del español.

---

## Comprobado y correcto

- **Nombres que siguen funcionando** [V]:
  - «dostoyevski» (Dostoyevsky en 7 de los 8 primeros);
  - «chejov» (Chekhov del 1 al 8, salvo un ensayo sobre él);
  - «Shakespear», «Frankenstein» (las tres ediciones primero), «A Midsummer Night's Dream», «sherlock holmes», «hound of the baskervilles»;
  - «mark twain», «jack london», «verne», «kafka», «bronte», «tolstoi», «goethe» y «wilde».
- **Palabra suelta en frases** [V]:
  - «amor» da 8 de 8 libros de amor (*A Dozen Ways Of Love*, *Love's Usuries*, *Hints for Lovers*…), sin *Amory* ni *Armour*;
  - «miedo» da libros sobre el miedo y «dragones», libros de dragones.
- **Anuncios excluidos, fuera de la búsqueda** [V]: «click below to buy this tutorial» ya no saca ninguno de los excluidos (el primero es *Discover the Excitement of Hairpin Lace*, 0,378).
- **422 sin eco**, en el Space con `X-Lector` [V]:
  - con `{"usuario": 12345, "clave": {"secreta": "CLAVE-DE-PRUEBA-XYZ"}}` responde `loc`, `msg` y `type`, sin el valor;
  - con `consulta: ""` y `n: 99`, igual.
  - `para_gradio` registra el manejador (`pruebas_api.py:1067`) [L].
- **Candado de subidas** (`app/api.py:287-307`, `:1073` y `:2113`) [L]:
  - no se toma dos veces: `_guardar_nombre_subido` y `_titulo_subido` no lo piden;
  - el `raise _no(429…)` dentro del `with` lo suelta;
  - `nombres.json` se escribe a un temporal y `os.replace`.
  - Cargar el libro dentro del candado hace esperar a otra subida o borrado del mismo lector, que es lo buscado.
- **Reproducción local:** en la primera tanda, las 29 consultas principales dieron en local las mismas posiciones que el Space [V]. No afirmo con qué commit exacto de `app/catalogo.py` corrió: `7c9c289` entró durante la auditoría. Por eso las posiciones citadas son las del Space.
