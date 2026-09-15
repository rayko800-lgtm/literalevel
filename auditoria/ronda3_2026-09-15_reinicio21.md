# Ronda 3: el código y los datos del reinicio 21, antes de subir (15 sep 2026)

- **Auditor:** entrega-4e.
- **HEAD al empezar:** `7ecc2b1`.
- **Qué se audita:** `git diff 7c9c289~1..7c9c289`, de f4:
  - `tools/medir_corpus.py`: `MARGEN_RARO` y `asignar`;
  - `app/catalogo.py`: nombre entero del autor;
  - `tools/marcar_no_lectura.py`: APOCALYPTO;
  - `tools/catalogar_corpus.py`, `pruebas_corpus.py` y el banco C8.

  Además, los datos de `740eb84`, que la Central añadió a mitad de auditoría.
- **Método:**
  - Lectura del diff a ciegas.
  - `pruebas_corpus.py` con `LITERALEVEL_SIN_CLAVES=1` y TEMP en D:.
  - `medir()` de `7c9c289` con un **puntuador falso** (0,2 + 1,8 × fracción de palabras «RARO») y carpeta de medidas en D:.
  - Las similitudes de nombre, sin modelo.
  - Con el modelo, **solo después de que f4 avisara de que había terminado la regeneración**: el orden real de la búsqueda y la medida de dos bloques.
  - Todo en local y en solo lectura. Nada en el árbol limpio de f4 en D:.
- **[V]** es ejecutado; **[L]**, solo leído.

**Pruebas:** `pruebas_corpus.py` da **41 de 41** en `7c9c289` [V]. El banco C8 no lo corrí.

---

## Hallazgos

### [SERIO] El nombre entero apaga al autor cuando la consulta mezcla apellido y tema o título: «treasure island stevenson» ya no pone *Treasure Island* primero

*(Avisado a la Central antes de terminar el informe.)*

- **Dónde:** `app/catalogo.py:725-729` en `7c9c289`, con `_vocabulario_de_nombres` (`:312`).
- **Qué dice:**
  > `nombres_de_la_consulta = pistas & vocabulario`
  >
  > `if len(pistas) > 1 and nombres_de_la_consulta:`
  >
  > `    for i in np.flatnonzero(por_apellido >= _PARECIDO_NOMBRE):`
  >
  > `        if nombres_de_la_consulta - enteros[i]:`
  >
  > `            por_apellido[i] = 0.0`
- **Por qué:**
  - **El vocabulario de nombres no son solo nombres** [V]. Salen **24.296** palabras de todo el campo de autor, apellidos incluidos, de Gutenberg y de los textos libres.
    - De 70 palabras corrientes que probé, son «nombre» *love, hope, rose, grace, king, white, black, young, wood, moon, star, story, stories, adventure, school, little, green, brown, gold, summer, winter, spring, world, life, house, home, child, children, animal, bird, tree, flower, ghost, music, wild, call, island*, y también *amor* y *luna*.
    - Cualquiera de ellas en la consulta, junto a un apellido, deja en 0 el apellido de todos los autores cuyo nombre no la contiene: es decir, del autor buscado.
  - **Parecido de nombre del autor buscado** [V, sin modelo], con la regla del 19 y con la del 21:

    | Consulta | 19 | 21 |
    |---|---|---|
    | «treasure island stevenson» | 0,900 | **0** |
    | «love poems by browning» | 0,900 | **0** |
    | «ghost stories by dickens» | 0,900 | **0** |
    | «white fang jack london» | 0,887 | **0** |
    | «the call of the wild by jack london» | 0,887 | **0** |
    | «rose garden by frances hodgson burnett» | 0,880 | **0** |

  - **Orden real con el modelo** [V], en local con los datos de `740eb84`: `7c9c289` tal cual, frente al mismo código con el vocabulario vacío (esa regla apagada):

    | Consulta | 21 tal cual | 21 sin la regla |
    |---|---|---|
    | «treasure island stevenson» | *Treasure Island* **5.º y 6.º**; primero «Treasure Hunting» (un cuento) y «The Island Treasure» | *Treasure Island* 1.º y 2.º; Stevenson en 8 de 10 |
    | «love poems by browning» | **ningún Browning** en los 10 primeros | 7 Browning |
    | «the secret garden frances hodgson burnett» | **ningún Burnett** | 7 Burnett |
    | «white fang jack london» | **ningún Jack London** | 2 |
    | «the call of the wild by jack london» | el libro 2.º; Jack London en 4 de 10 | el libro 1.º; Jack London en 10 de 10 |
    | «a christmas carol dickens» | Dickens 1 de 10 | Dickens 5 de 10 |
    | «jane austen», «dostoyevski», «sherlock holmes stories conan doyle», «the time machine wells» | igual | igual |

  - **En el Space del 19** (`af72fb0`) [V]:
    - «treasure island stevenson» da Stevenson del 1 al 10;
    - «love poems by browning», Browning en 7 de 10;
    - «the secret garden frances hodgson burnett», Burnett en 8 de 10.

    Es una regresión del 21 frente a lo publicado.
  - El commit lo presenta como que las palabras de tema del vocabulario «solo quitan un apellido parcial». No es así: quitan el apellido **exacto** del autor buscado, porque la condición es que la consulta traiga una palabra del vocabulario que ese autor no tenga, y ningún autor tiene «island» en su nombre.
- **Arreglo:**
  - que la regla solo mire nombres de pila (lo que va detrás de la coma), no el campo entero;
  - y que no cuente una palabra que sea más corriente en títulos o temas que en nombres.

  Por ejemplo: quitar el apellido suelto solo si la palabra de más es nombre de pila de algún autor que comparta ese apellido («Jane» frente a «Sidney Austen»).

  Y añadir a la prueba «treasure island stevenson» y «love poems by browning».

### [MENOR] En un bloque de 3 con dos textos raros, se marca como raro el texto normal y se queda arrastrado

- **Dónde:** `tools/medir_corpus.py:195-212` en `7c9c289`.
- **Qué dice:**
  > `if rr["dificultad"] is not None and abs(rr["dificultad"] - completo) > mayor:`
  >
  > `    mayor, raro, sin_raro = abs(rr["dificultad"] - completo), k, rr["dificultad"]`
- **Por qué:**
  - La regla busca el único texto cuya ausencia más mueve la medida.
  - Con dos textos difíciles y uno fácil, quitar el fácil es lo que más mueve. Así que el marcado es el fácil, que conserva la medida del bloque entero (arrastrada por los dos difíciles), y los dos difíciles pasan a la de sin él.
  - **Con el puntuador falso** [V], el bloque normal + RARO + RARO:
    - el normal queda en **1,4** con `raro_en_bloque = True`;
    - los dos RARO quedan en 2,0.
  - Es el mismo resultado que «un texto fácil entre dos difíciles» (caso 3, idéntico): la regla no distingue los dos casos.
  - Con un APOCALYPTO por bloque funciona; con dos en el mismo bloque, el poema de nivel 1 sigue en B2 y además queda marcado como el raro.
- **Arreglo:** en bloques de 3, no marcar nada si los dos que quedan tras quitar el «raro» no se parecen entre sí. O repetir la búsqueda sobre el resto una vez quitado el primero. Como mínimo, una prueba con dos raros.

### [MENOR] Si la cola se une a un bloque que ya tenía un raro, la marca queda obsoleta

- **Dónde:** `tools/medir_corpus.py:251` y `:212` en `7c9c289`.
- **Qué dice:**
  > `idx, ids, trozos = previo[0] + idx, previo[1] + ids, previo[2] + trozos`
  >
  > `df.at[idx[raro], "raro_en_bloque"] = True`
- **Por qué:**
  - El último bloque del grupo ya pasó por `asignar`, que pudo marcar un raro y apuntarlo en `bloques_con_raro`. Después, la cola corta se une a él y `asignar` se llama otra vez sobre el bloque unido.
  - Nada vuelve a poner `raro_en_bloque` a `False` ni quita la entrada vieja de `bloques_con_raro`.
  - **Con el puntuador falso** [V], tres de 90 palabras con el tercero RARO y una cola de 60:
    - el primer paso marca el raro (0,8 frente a 0,2);
    - el bloque unido ya no tiene raro (quitar el RARO lo mueve 0,49): los cuatro textos quedan en **0,6909**;
    - pero el RARO **sigue marcado** `raro_en_bloque = True`, y `bloques_con_raro` sigue diciendo `completo 0,8 / sin_raro 0,2`, que ya no es verdad.
  - `raro_en_bloque` no lo lee todavía ni `app/` ni el front [V], así que hoy solo afecta al recuento («92 bloques con un raro») y al CSV.
  - En los datos de `740eb84` hay 27 raros cuya dificultad coincide exactamente con la de otro texto de su grupo. Es compatible con este fallo, pero también con una coincidencia entre bloques distintos: no lo he separado [V el recuento; DUDA la causa].
- **Arreglo:** al unir la cola, deshacer lo que `asignar` escribió para `previo` (marca y entrada) antes de volver a asignar. Una prueba con cola y raro.

### [MENOR] 42 textos que no están en inglés siguen visibles, y un anuncio de venta de GHB

- **Dónde:** `tools/marcar_no_lectura.py:50` y `:108` en `7c9c289` (`MIN_INGLES = 0.6`), sobre `no_lectura_externo.csv` de `740eb84` (200 filas).
- **Por qué:**
  - La Central preguntaba si quedan más textos en francés o italiano fuera de los raros.
  - **Recorrido** [V] de los textos servidos que no están excluidos, contando palabras vacías de francés, italiano, español e inglés: 87 candidatos. Miré a mano unos 70 de ellos (hay muchos falsos positivos en inglés), y **al menos 42 no están en inglés** y siguen visibles con letra:
    - **español** (15): SWV60482, SWV60496, SWV60972, SWV60975, SWV617282, SWV619471, SWV619509, SWV620202, SWV692166, SWV290341, SWV48807, SWV48827, SWV105585, SWV127963, SWV194319;
    - **francés** (8): SWV122353, SWV137079, SWV192664, SWV238014, SWV442634, SWV465783, SWV49314, SWV618269;
    - **italiano** (5): SWV261406, SWV444271, SWV46924, SWV61199, SWV676267;
    - **turco** (5): SWV388065, SWV65732, SWV67360, SWV67576, SWV69810;
    - **catalán** (2): SWV129059, SWV132405;
    - **hindi o gujarati transliterados** (3): SWV296299, SWV5466, SWV59172;
    - **uno cada uno:** rumano (SWV350933), portugués (SWV84557), ewe (SWV107681) e hindi en devanagari (SWV461300).
  - Pasan la regla de `MIN_INGLES`: el 60 % de sus palabras está en el diccionario inglés de Kaikki. No comprobé qué palabras cuentan; lo probable es que cuenten las cortas y los nombres propios, que ese diccionario recoge de muchas lenguas [DUDA].
  - **En la misma lista hay un anuncio de venta de droga:** SWV644124, «Buying GHB Online» («Buying GHB online, buy GHB online, where to buy GHB online…»), visible con B1. No lo marcan ni la regla de anuncios ni la lista revisada.
- **Arreglo:**
  - una regla de idioma que no dependa del diccionario (por ejemplo, proporción de palabras vacías del inglés frente a las de otras lenguas, como la de este recorrido) y repasar a mano lo que marque;
  - SWV644124 a `ANUNCIOS_REVISADOS` ya.

### [DUDA] Los que suben de A2 a B2 por quitar el raro: ¿de verdad eran A2?

- **Dónde:** `asignar` (`tools/medir_corpus.py:185-214` en `7c9c289`), sobre `catalogo_externo.csv` de `740eb84`.
- **Por qué:**
  - Mirados a mano [V] cuatro de los 16 que pasan de A2 a B2, en dos bloques. Para reconstruirlos, tomé los textos de la misma fuente que en `a557288` compartían dificultad exacta.
  - **Raro SWV21894**, un poema repetitivo («Tree tree beautiful tree / Beautiful green tree…»):
    - conserva 0,597;
    - SWV217407 («My name is Biju. And I have four freinds…») y SWV217506 («THERE ARE COLOURS EVERYWHERE…») suben a **1,344 (B2)**.
    - El raro sí parece el fácil de su bloque. Pero «My name is Biju» no es un texto B2.
  - **Raro SWV187405** («One day Mohan told his friends that next week was Deepavali…»):
    - conserva 0,518;
    - SWV187384 («Once there lived a lion who wanted to eat all the animals…») y SWV187420 («ONE DAY IN THE MORNING NOBODY WANTED TO GET UP…») suben a **1,15 (B2)**.
    - Aquí el raro no es visiblemente más fácil que los otros.
  - **Medido con el v4** [V] sobre los bloques reconstruidos:

    | Raro | Textos | Completo | Sin el raro | Sin el raro, en minúsculas | En `740eb84` |
    |---|---|---|---|---|---|
    | SWV21894 | 13 | 0,591 | **0,648** | 1,027 | 1,344 |
    | SWV187405 | 16 | 0,563 | **0,680** | 0,867 | 1,15 |

  - Los bloques reconstruidos miden lo que medían en el 19 (0,59 frente a 0,597; 0,56 frente a 0,518). **Quitar el raro los deja en A2**, no en B2.
  - Así que la subida a B2 no sale de quitar ese texto a ese bloque. En `740eb84`, textos que en el 19 compartían bloque tienen ahora medidas distintas (0,597 y 1,344 en el mismo grupo). Con los 15 textos que pasaron a `no_lectura`, los bloques del 21 se formaron distinto, y no puedo rehacerlos desde el CSV.
  - **Las mayúsculas no lo explican:** en minúsculas la medida **sube** (0,648 → 1,027), no baja.
- **Qué haría:** que f4 imprima `bloques_con_raro` (ids, completo y sin_raro) de estos dos grupos y mida a mano el bloque sin el raro. Es posible que el bloque del 21 sea pequeño y que «sin el raro» quede en dos o tres textos cortos, donde el v4 mide mal. No lo doy por fallo sin eso.

### [NOTA] El margen quedó fijado antes de medir, pero la muestra que lo justifica no se puede rehacer

- **Dónde:** `tools/medir_corpus.py:50-57` en `7c9c289`.
- **Qué dice:**
  > «Fijado ANTES de medir la tanda (Central, 15 sep 2026): … en una muestra al azar de 30 bloques, quitar un solo texto movía la medida más de 0,5 en 3.»
- **Por qué:**
  - **El orden sí consta** [V]: `7c9c289`, con `MARGEN_RARO = 0.5`, es de las 02:39, y los datos regenerados (`740eb84`), de las 02:58. La constante no cambió entre los dos commits.
  - Pero la muestra de 30 bloques solo está en el comentario: ni guion ni registro en `tools/` ni en `auditoria/` [V búsqueda].
- **Arreglo:** dejar el guion o la salida de esa muestra, o decir en el comentario que no se conserva.

---

## Comprobado y correcto

- **El raro no baja de nivel respecto a su bloque** [L y V]: conserva `completo`, y en la prueba del repositorio y en el puntuador falso la conserva también cuando el raro es el fácil (caso 3).
- **Bloque de 2 textos:** no se mira (`len(ids) >= 3`, `:195`). Con el puntuador falso, normal + RARO de 130 palabras quedan los dos en 1,1 y sin marca [V]. Es lo que dice el código; lo apunto como límite, no como fallo.
- **Un bloque que se queda con un solo texto:**
  - una cola sola solo se mide si llega a 150 palabras (`MIN_WORDS`), y entonces no se busca raro;
  - si no llega y no hay bloque anterior, va a `cola_sin_medir`;
  - al buscar el raro, un resto de menos de 150 palabras sin uno de los textos se salta y no se mide (`if sum(...) < scoring.MIN_WORDS: continue`) [L].
- **«Fenn, Amor» no vuelve** [V, sin modelo]: con «amor», el parecido de nombre de Fenn es 0, porque el nombre entero solo cuenta con el apellido (`con_apellido`, `:721` y `:732`). Con «historias de amor», tampoco.
- **Nombre entero:**
  - «jane austen» pone a Austen, Jane en 8 de los 10 primeros, incluidos los tres primeros [V, modelo]; qué son los otros dos no lo miré;
  - «agatha christie» tiene ya parecido 1,02 y ningún otro Christie igual o por encima [V, sin modelo].
  - Si la búsqueda la saca delante no lo miré: la Central dice que va al 22 con cervantes, y no lo cuento como nuevo.
- **APOCALYPTO** (SWV98807) está en `no_lectura_externo.csv` con su motivo [V].
- **El reparto de los libres en `740eb84`:** A1 **766**, A2 **5.696**, B1 **5.491**, B2 **2.524**, C1 **777** y C2 **113**, recontado sobre el CSV. Coincide con lo que da la Central [V].
- **Cambios de letra frente a `a557288`:** 225, de los que **42 suben** (16 A2→B2, 16 B1→B2, 8 B1→C1 y 2 A2→B1) y 183 bajan. La Central daba 44 que suben; conté 42 [V].
- **`raro_en_bloque`:** 92 textos marcados, 10 de ellos también en `no_lectura` [V].
