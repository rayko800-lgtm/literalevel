# Ronda 2 — auditoría de los arreglos de f4 en el catálogo (15 sep 2026)

- **Auditor:** entrega-4e.
- **Diff auditado:** `git diff 5d35e85..6945046` sobre `app/catalogo.py`, `app/ficha.py`, `tools/catalogar_corpus.py`, `tools/medir_corpus.py`, `tools/cerrar_corpus.py` (no cambia), `tools/marcar_no_lectura.py` y `pruebas_corpus.py`. Cambian también los datos `catalogo_externo.csv`, `corpus_abierto.parquet` y `no_lectura_externo.csv`.
- **Árbol:** HEAD `b0dac54`, que contiene `6945046`. Los datos de disco coinciden con el commit (`git status` limpio en los CSV, el parquet y el `.npy`).
- **Método:**
  - De `auditoria/cruzada_2026-09-14_catalogo_despliegue.md` solo leí S1, S2, M1-M4 y D1, para la tabla de cierre. Lo nuevo del diff lo audité a ciegas.
  - Todo lo marcado **[V]** lo ejecuté con `LITERALEVEL_SIN_CLAVES=1` y sin medir nada nuevo. **[L]** es solo leído.
- **Fuera de alcance:** el arreglo de «amor» que f4 mete encima (frases españolas y nombre endurecido) se audita en otra pasada.

## Cierre de la ronda 1

| Hallazgo de e6 | Estado | Cómo lo comprobé |
|---|---|---|
| **S1.** Los libres se buscaban solo por título y autor | **Cerrado** | Ver detalle debajo de la tabla. [V] |
| **S2.** Las colas de grupo nunca se medían | **Cerrado** | Ver detalle debajo de la tabla. [V] |
| **M1.** `buscar` solo miraba los 3n primeros | **Cerrado** | Recorre `orden` entero (`catalogo.py:726`). Prueba `buscar llena n aunque los primeros esten excluidos`. [L] y [V prueba] |
| **M2.** La clave de medida no llevaba el modelo | **Cerrado** | `clave(..., modelo)` con `huella_modelo()`. Lo anterior vale solo con `HUELLA_V4` y se reescribe. En disco hay 25.608 unidades, de las que 12.808 ya llevan `modelo` (las del v4 reescritas). Prueba `la clave de medida cambia con el modelo`. [V] |
| **M3.** A StoryWeaver se le presumía la licencia | **Cerrado** | Sin `al_catalogo` entra solo si `licencia_libre(f.get("licencia"))`. La licencia ya no se inventa. Prueba `un libro de StoryWeaver sin licencia no entra al catalogo`. [L] y [V prueba] |
| **M4.** «1 minutos» | **Cerrado donde se ve** | `ficha.reloj(1)` sigue diciendo «1 minutos» [V]. Pero toda salida pasa por `ui._reloj_llano` o `_rango_de_tiempo`: la API en `api.py:690-691` y Gradio en `ui.py:2536`, `:2549` y `:2557`. Ningún `ficha.reloj` se enseña directo [V grep]. La raíz sigue sin tocar, por decisión (el archivo es de f4). |
| **D1.** El parquet se escaneaba como bytes | **Cerrado** | Prueba `una credencial dentro de un parquet comprimido tambien salta`: gzip y snappy, desde disco y desde los bytes del commit. [V prueba] |

**S1, en detalle:**
- **Gancho:** 15.366 de 15.367 filas lo tienen. La vacía es SWV137935, sin cuerpo y excluida.
- **Huella:** ninguna fila la tiene vacía. En las 15.367, la huella empieza por los temas sin «reading level».
- **`.npy`:** `_externo_indexable()` da la huella `5e8a5dab191c1917`, y `catalogo_emb_ext_5e8a5dab191c1917.npy` existe en la raíz y en la caché con forma 15.367 × 384.
- **Los vectores son de ese texto:** recodifiqué 40 filas al azar y el coseno con el `.npy` da **1,000000**. Como control, con las filas desplazadas da 0,284.
- **Búsqueda:** «a girl who makes an umbrella» saca SWV211552 primero.

**S2, en detalle:**
- **Entran 10 textos, todos en bloque:** ASB0238, ASB0311, LRDD1C2B…, LRDFDDDE…, SWV95006, SWV96311, SWV97259, SWV9756, SWV991 y SWV9922.
- **Reparto reproducido desde las medidas en disco, sin medir nada:**
  - con medida, 15.367 (11.039 solos y 4.328 en bloque);
  - fuera por el filtro, 882;
  - fuera por grupo corto, 2 (ASB0307 y LRDEA3672…).
- **Dificultades que cambian: 4.** SWV98782, SWV98807, SWV98842 y SWV9895 pasan de 1,575 a 1,291 (de C1 a B2). Son del último bloque de StoryWeaver nivel 1.

Lo que f4 declara en `6945046` sobre todo esto cuadra con lo medido.

**Pruebas:**
- `pruebas_corpus.py`: **34 de 34** [V].
- Banco C5 (`tools/banco_mutantes.py C5`, los 9 mutantes que declara f4): **9 de 9 cazados por su prueba**, con el control sin mutar en verde (349 pruebas extremas) [V].

---

## Hallazgos nuevos

### [SERIO] El rescate por nombre se lleva por delante las búsquedas temáticas en español

- **Dónde:** `app/catalogo.py:617` y `:621-622`, con `_PARECIDO_NOMBRE = 0.75` (`:197`) y `_PESO_NOMBRE = 0.85` (`:199`).
- **Qué dice:**
  > `lex = _similitud_nombres(consulta, self._fichas)`
  >
  > `sim = np.maximum(sim, np.where(lex >= _PARECIDO_NOMBRE, lex * _PESO_NOMBRE + 0.01 * sim, 0.0))`
- **Por qué:**
  - Una sola palabra española de la consulta que se parece a una palabra de un título o de un autor sube ese libro a 0,69-0,77. Eso gana a los libros que sí tratan del tema.
  - Ahora que los libres se buscan por su texto, la parte semántica acierta; lo que falla es el rescate.
  - Tres consultas de tema, sin nivel, en local [V]:

  | Consulta | Primeros resultados | Por qué suben | Lo que daría la semántica sola |
  |---|---|---|---|
  | «cuentos sobre la lluvia y los agricultores» | 37 libros rescatados. *Hymns … Centos*, *Forest Sombre*, *His Sombre Rivals* (semántica 0,20-0,37; nombre 0,81-0,82) | «sobre» ≈ «Sombre», «cuentos» ≈ «Centos» | Rain 0,684, The Water Seed 0,664, Girl and a farmer 0,659, The Duet of Rainmakers 0,655 |
  | «historias sobre la lluvia y los agricultores» | 99 rescatados; los 6 primeros, *The Great Events by Famous Historians* y parecidos (semántica 0,31-0,34; nombre 0,841) | «historias» ≈ «Historians» | Los mismos cuatro de arriba |
  | «viaje al espacio y la luna» | 20 rescatados: *Fantasy of Luna*, *Luna: The Lost Dog* (un perro), *Our Little Boer Cousin* (nombre 0,900) | «luna» | To Mars via the Moon 0,737, Journey To The Moon 0,721, Journey to Space 0,705, A Voyage to the Moon 0,699 |

  - Las mismas consultas en inglés salen bien: «stories about rain and farmers» y «a trip to space and the moon» sacan títulos del tema.
  - En español también salen bien cuando ninguna palabra se parece a un título: «historias de piratas en el mar», «viaje al espacio», «cuentos de animales del bosque».
  - La interfaz invita a describir en español lo que se quiere leer.
- **Arreglo:** que el rescate exija que la consulta entera se parezca al título o al autor, no una palabra suelta, o que no cuenten palabras funcionales ni comunes del español. Es lo que anuncia el «nombre endurecido» de f4, y la próxima pasada debería repetir estas tres consultas.

### [MENOR] Anuncios con enlaces de StoryWeaver visibles en las tarjetas

- **Dónde:** `tools/marcar_no_lectura.py:54` (`motivo_no_lectura`, que solo mira vocabulario y alfabeto) y los ganchos nuevos de `catalogar_corpus.gancho`.
- **Qué dice (ganchos visibles, no excluidos):**
  > SWV59417 «ABS 200 Complete Course( Introduction to Applied Behavioral Science) To Buy This Tutorial Click Below http://www.homeworkbag.com/…»
  >
  > SWV600113 «Why is My Blender Not Spinning what are the Reasons and Solutions: https://blenderproguide…»
  >
  > SWV642071 «To know more about Hoarding Signage- https://screenworks.graphics/…»
- **Por qué:**
  - No es la atribución que añade el catalogador: esa no aparece en ningún gancho ni en ninguna huella [V]. Son textos subidos a StoryWeaver como publicidad.
  - Antes el gancho iba vacío y no se veían; ahora salen en la tarjeta.
  - **Medido:** 6 anuncios o enlaces visibles en el gancho (SWV59417, SWV551720, SWV600113, SWV642071, SWV642072 y SWV687758), más 25 textos visibles con URL en la huella. SWV589104 sí está excluido.
- **Arreglo:** una regla más en `motivo_no_lectura`: URL comercial o «click below», «to know more», «buy this». Después, volver a generar `no_lectura_externo.csv`.

### [MENOR] Las cifras del catálogo externo cambian y los documentos y el Space todavía dicen las de antes

- **Dónde:** `catalogo_externo.csv`, frente a `entrega/documento.tex` §4.3 y §8.5, `estrategia.md` y la presentación, y frente a `/api/estado` del Space (68.536).
- **Qué dice:** los documentos: «15.357 textos de licencia libre … 749 A1, 5.580 A2, 5.543 B1, 2.578 B2, 794 C1 y 113 C2 … 894 textos libres se quedaron fuera … 11.872 textos entre A1 y B1».
- **Por qué:** recontado [V] en `6945046`:

  | | Antes (`5d35e85`) | Ahora (`6945046`) |
  |---|---|---|
  | Textos libres | 15.357 | **15.367** |
  | StoryWeaver / Let's Read / African Storybook / VOA | 14.500 / 326 / 278 / 253 | 14.506 / 328 / 280 / 253 |
  | Solos / en bloque | 11.039 / 4.318 | 11.039 / **4.328** |
  | A1 / A2 / B1 | 749 / 5.580 / 5.543 | 749 / **5.589** / 5.543 |
  | B2 / C1 / C2 | 2.578 / 794 / 113 | **2.583** / **790** / 113 |
  | Entre A1 y B1 | 11.872 | **11.881** |
  | Fuera | 894 | **884** (882 por el filtro y 2 por grupo corto) |
  | Catálogo total | 68.536 | 68.546 |

  No es un error de f4: son sus números corregidos. Pero el Space los dará cuando se publique el reinicio 18, y hasta que no se sincronicen los documentos, lo que se enseña y lo que se cuenta no coincidirán. Los documentos los llevo yo desde la ronda 1.
- **Arreglo:** tras el reinicio 18, comprobar `/api/estado` y propagar la tabla a los documentos con el barrido de `corregir-sin-inventar`. El recuento de «894» del §4.3 se rehace entero.

### [DUDA] Muchos ganchos quedan cortos

- **Dónde:** `tools/catalogar_corpus.py`, `GANCHO_MIN, GANCHO_MAX = 12, 30`.
- **Por qué:**
  - 567 ganchos tienen menos de 12 palabras y 1.189 acaban en «…» porque la primera frase pasa de 30 [V].
  - Lo corto es casi siempre un cuento corto de verdad, así que parece correcto. Pero en la tarjeta se ve a veces solo la primera frase de un título largo: en SWV478031 el gancho es igual al título.
  - Para la búsqueda no importa: la huella lleva 40 palabras más.
- **Arreglo:** nada obligatorio. Si molesta en la tarjeta, saltar las frases que repiten el título.

---

## Comprobado y correcto

- **La atribución no está en ningún gancho ni en ninguna huella.** Busqué «licencia», «publicado en», «CC BY», «Pratham Books» y las URL de las cuatro bibliotecas: lo que aparece es texto de los autores, no la línea que añade el catalogador. [V]
- **`para_medir` quita la atribución también sin cuerpo** (SWV137935). `no_lectura_externo.csv` pasa de 163 a 164 filas [V] y SWV137935 está excluido [V].
- **Los temas van delante en la huella** y sin «reading level»; el modelo corta a 128 tokens. [V] y [L]
- **`embeddings_por_partes`:** reanudable por partes con escritura atómica, y el nombre del `.npy` sale de `_externo_indexable`, el mismo que busca `embeddings`. Prueba de reanudación [V prueba]; el `.npy` publicado cuadra con el texto (coseno 1,000000).
- **La cola de grupo:** se mide sola si llega a `MIN_WORDS`; si no, se une al último bloque, y solo la de un grupo entero corto se cuenta aparte. Prueba `la cola de cada grupo se mide o se cuenta aparte` [V] y reparto real reproducido [V].
- **Búsquedas de tema que salen bien** (sin nivel, local) [V]:
  - «a girl who makes an umbrella»: SWV211552 primero y 7 de 10 sobre paraguas;
  - «cuentos de animales del bosque»;
  - «a boy who wants to fly like a bird»: *Fly Like A Bird* primero;
  - «historias de piratas en el mar»: 8 de 8 de piratas;
  - «viaje al espacio», «stories about rain and farmers» y «a trip to space and the moon».
- **`tools/cerrar_corpus.py`** no cambia en el rango. [V]
