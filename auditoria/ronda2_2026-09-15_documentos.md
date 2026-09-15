# Ronda 2: auditoría de los documentos

- **Auditor:** entrega-e6 (811c22).
- **Qué se audita:** `git diff 804e649..HEAD -- entrega/ AGENTS.md README.md`, que son los commits **72c9ee6** (los 4 serios) y **b0dac54** (los 11 menores y la duda de amor).
- **Informe de la ronda 1:** `auditoria/cruzada_2026-09-14_documentos.md` (de 4e). Lo leí solo para comprobar el cierre. Lo nuevo, cada cifra cambiada contra su fuente y las promesas, lo busqué a ciegas en el diff.
- **Método:** **[V]** es comprobado ejecutando o consultando la fuente; **[L]** es solo leído.

## Qué se ejecutó

**Recuentos con `Catalogo()` (el catálogo tal como lo carga la app):**
- reparto por letra con `correcciones_catalogo.csv`;
- libros por debajo de B2;
- literarios con y sin los excluidos;
- libros de amor por franja, con la regla escrita en el texto.

**Contra el repositorio:**
- `catalogo_externo.csv` en 377a650 y en HEAD, por fuente y licencia;
- `app/pronunciacion_cmu.tsv` y su licencia;
- `PENDIENTES.md`, por la procedencia de 57.226 y del coste.

**Documentos:**
- cotejo de citas de `documento.tex` contra `referencias.bib`;
- texto extraído de los tres PDF (`documento`, `presentacion`, `guion_video`);
- `grep` de «ciega», «garantiza», «cabe en la cuota», «Sorpréndeme», «32 de 35» y «casilla».

**En el Space:** `/api/buscar` con «dostoyevski», con nivel 1,20 y sin nivel.

**Referencias nuevas, en su fuente:**
- arXiv 2604.24470 (Grossman y Chen), en texto completo;
- arXiv 2506.14046 (Kogan et al.), en texto completo;
- arXiv 2506.05209 (Common Pile);
- ACL Anthology 2025.emnlp-main.491 (UniversalCEFR);
- la página de tarifas de MetaMetrics;
- el DOI de Breuker, que resuelve a su capítulo de Springer, detrás de inicio de sesión.

**Pruebas:**
- Hoy, sin claves, ejecuté `pruebas_api.py` (52 de 52) y `pruebas_voz_ritmo.py` (34 de 34).
- `pruebas_corpus.py` lo conté sin ejecutarlo: 34 llamadas `prueba(` en d58b0be. No lo corrí porque f4 tiene cambios sin confirmar en ese archivo.
- Las 349 extremas no las ejecuté.

## Hallazgos nuevos

### [SERIO] El Cuadro 17 y la estrategia dicen ahora que medir el catálogo costó 0 USD de cómputo, y el registro del proyecto dice que parte se midió en una A100 de pago [L]

- **Dónde:**
  - `entrega/documento.md:1316` (Cuadro 17) y `1324-1327`;
  - `entrega/documento.tex:2893` y `2940-2943`;
  - `entrega/estrategia.md:475-478`.
- **Qué dice:**
  > `| Lexile, tarifa de creador de contenido (MetaMetrics, 2026) | **3.824–54.636 USD/año** | 0 USD de cómputo (T4 gratuita) |`
  >
  > «Medirlos aquí no costó cómputo de pago: los libros de Gutenberg se midieron en una T4 gratuita de Colab, en tandas reanudables —la última, 9.795 libros en 55 minutos—»
- **Por qué:**
  - `PENDIENTES.md` es el registro de ese trabajo y dice otra cosa:
    - «84 libros/min contra los 61 de la **A100 de pago**» (línea 139);
    - «Coste real del catálogo | **2,8 h de cómputo A100**; ~17 h de extremo a extremo» (línea 192), con 29.875 libros medidos a 10 de septiembre;
    - la cuenta de Colab es «la cuenta con Colab Pro» (línea 145).
  - El propio documento, en §8.3 (`documento.md:1193-1194`), dice «Después se ejecutó… El ritmo real medido en la A100 fue de 61 libros por minuto».
  - Solo la última tanda (9.795 libros, 12 de septiembre) consta en T4 gratuita. Con eso no se sostiene «0 USD» para los 53.179.
  - En la ronda 1 esta misma celda fue un SERIO por decir que «cabía en la cuota». El arreglo cambia una cifra sin respaldo por otra.
  - No puedo ver la facturación de Colab, así que no digo cuánto se pagó. Lo que digo es que el documento afirma un coste cero que su propio registro contradice.
- **Arreglo:** decir lo que consta, «2,8 h de A100 en Colab Pro para la primera parte y la última tanda en T4 gratuita», o no poner coste de cómputo en el cuadro. Y quitar «no costó cómputo de pago».

### [MENOR] Las 17 horas se calcularon para los 61.642 libros en inglés y ahora se atribuyen a los 53.179 [V]

- **Dónde:** `entrega/documento.md:1326-1327`, `entrega/documento.tex:2942-2943` y `entrega/estrategia.md:477-478`.
- **Qué dice:** «Los 53.179 libros del catálogo medido… Al ritmo medido en una A100, 61 libros por minuto, habrían sido unas 17 horas de reloj (§8.3).»
- **Por qué:**
  - §8.3 (`documento.md:1194-1195`) da las 17 horas «para los 61.642»: 61.642 / 61 = 1.010 min, **16,8 h**.
  - Para los 53.179 de esta frase salen 871,8 min, **14,5 h**.
- **Arreglo:** «unas 14,5 horas para los 53.179», o citar las 17 h con los 61.642.

### [MENOR] «Validación ciega» sigue en el Cuadro 10 del documento entregado [V]

- **Dónde:** `entrega/documento.tex:1921`, y el PDF `entrega/documento.pdf` (la fila del cuadro).
- **Qué dice:**
  > `\textbf{Validación ciega} (interno) & 144 & Partición de validación del corpus de anclaje …`
- **Por qué:**
  - Los cuatro sitios que señaló la ronda 1 ya dicen «validación interna» (en el PDF sale 4 veces). Pero la etiqueta de esta fila no se cambió y **sale en el PDF**: «Validación ciega (interno) 144 Partición de validación d…».
  - La misma fila explica que no es externa y que sobre esos 144 se eligió el punto de control. El `.md` no tiene esa etiqueta (su único «a ciegas» es el de las auditorías), así que además las dos copias difieren.
- **Arreglo:** «Validación interna» en la fila y recompilar el PDF.

### [MENOR] El Cuadro 2 da los recuentos de los textos libres sin fecha, y en HEAD el catálogo ya tiene 15.367 [V]

- **Dónde:** `entrega/documento.md:235-238` y su equivalente en `documento.tex` (Cuadro 2).
- **Qué dice:** «14.500 textos» (StoryWeaver), «326 textos» con «CC BY 4.0 (316) y CC BY 3.0 (10)» (Let's Read), «278 textos» (African Storybook) y «253 textos» (VOA).
- **Por qué:**
  - **En 377a650 cuadra todo exactamente:** 14.500, 316 + 10, 278 y 253, en total 15.357.
  - **Pero en HEAD** (`catalogo_externo.csv` de 6945046, el arreglo de f4 a mi auditoría de catálogo) hay **15.367**: StoryWeaver 14.506, Let's Read 318 + 10, African Storybook 280 y VOA 253.
  - El párrafo «Y fuera de Gutenberg» sí lleva «A fecha de `377a650`»; el cuadro no.
  - Cuando el reinicio 19 publique ese catálogo, el cuadro describirá uno que ya no es el de la app.
- **Arreglo:** «a fecha de 377a650» en el pie del Cuadro 2, o actualizar los cuatro recuentos y el total tras el reinicio 19.

### [MENOR] Los documentos describen una casilla de Encontrar que el front ya no tiene, y el guion del vídeo no prevé el aviso nuevo [V]

- **Dónde:**
  - `entrega/documento.md:1055`, `1073` y `1079`, y `documento.tex:2451`, `2524` y `2530`;
  - `entrega/guion_video.md:160-166` (y `guion_video.tex`).
- **Qué dice:**
  > «con la casilla puesta, el nivel del perfil ordena lo más parecido, sin filtrar»
  >
  > «la casilla **acerca y no filtra**»
  >
  > «el 15 de septiembre, con perfil 1,20, seguía segundo»
- **Por qué:**
  - El front publicado el 15 de septiembre (98b4cb8, y ahora 6cfda19) quitó la casilla «Ordenar por mi nivel». Lo cambié yo (c0ab601), después del commit de estos documentos, así que no es un error de quien los escribió: es un desfase que hay que recoger.
  - Encontrar ahora siempre ordena por nivel y reparte en «En tu nivel», «Un poco por encima de tu nivel» y «Ver también los de otros niveles».
  - En el Space, «dostoyevski» con nivel 1,20 devuelve primero ocho libros C1, entre 1,700 y 1,750, todos a más de 0,45 del nivel. Con la regla de `bloques-busqueda.ts` la pantalla enseña primero «De «dostoyevski» no hay libros en tu nivel ni un poco por encima entre los resultados. Estos son los de otros niveles.» y debajo «De otros niveles», con *Crime and Punishment* **segundo**.
  - El «segundo» del guion sigue siendo verdad, pero ese aviso saldrá en cámara y el guion no lo menciona.
- **Arreglo:**
  - Cuadro 15 y §7: «ordena por nivel lo más parecido y enseña aparte lo de otros niveles, sin filtrar».
  - Guion: una línea que diga que sale el aviso de «otros niveles» y que *Crime and Punishment* es el segundo de ese bloque.

### [MENOR] La tabla de pruebas del README mezcla la fecha de su cabecera con filas del día siguiente [V]

- **Dónde:** `README.md:184`, con las filas cambiadas (líneas 195-200).
- **Qué dice:** «Recuento del 14 de septiembre de 2026 en `74ffffc`, con `LITERALEVEL_SIN_CLAVES=1`», y debajo «34 de 34 (15 sep)» y «52 de 52 (15 sep)».
- **Por qué:** la cabecera atribuye toda la tabla a 74ffffc, y tres filas son de otro día y de otro árbol.
- **Arreglo:** cambiar la cabecera por «Recuento de 74ffffc (14 sep); las filas marcadas (15 sep), sobre d58b0be».

## Tabla de la ronda 1

| Hallazgo de la ronda 1 | Estado | Cómo lo sé |
|---|---|---|
| **S.** «Validación ciega» en portada, resumen y demo | **a medias** | [V] Portada, resumen (`.md` y `.tex`) y demo dicen «validación interna», y el PDF la da 4 veces. Queda la fila del Cuadro 10 (hallazgo nuevo). |
| **S.** Cuadro 17: «~3 h de A100» y «cabe en la cuota» | **a medias** | [V] «~3 h» y «cabe en la cuota» ya no están en ningún archivo ni PDF. Pero la cifra nueva, «0 USD», choca con el registro (SERIO nuevo), y las 17 h no son de los 53.179 (MENOR nuevo). |
| **S.** Faltan fuentes en el inventario | **cerrado** | [V] Filas para ELG, las cuatro bibliotecas, Common Pile y CMUdict. Recuentos exactos en 377a650: 14.500, 316 + 10, 278 y 253. CMUdict da 126.052 filas en `pronunciacion_cmu.tsv`, con licencia BSD. Los 57.226 constan en `PENDIENTES.md:169`. ELG como CC BY-NC-SA 4.0 consta en `notebook_proyecto.ipynb`; su ficha en UniversalCEFR no la miré [L]. Queda la fecha del cuadro (MENOR nuevo). |
| **S.** Fuentes citadas que no están en las referencias | **cerrado** | [V] 37 claves citadas y 37 entradas en `.bib`, sin huérfanas. Contra la fuente: Grossman y Chen (2026) dan **0,725** en CLEAR con **1.890** textos y **10** modelos abiertos; Kogan et al. (2025), BERT de **45,7 M** con MSE 0,44 frente a 0,48 de PaLM 2-L; Common Pile, UniversalCEFR (pp. 9703–9755) y MetaMetrics (3.824 y 54.636 USD) cuadran. El capítulo de Breuker existe en Springer (DOI), pero sus páginas no las vi [L]. |
| **M.** §7.4 «en curso» y «heredadas» | cerrado | [V] Diff: «terminó el 12 de septiembre de 2026… ya las medidas por el v4». |
| **M.** §8.6 «las métricas del v4 no» se pueden rehacer | cerrado | [V] Diff: «**y** las métricas internas del v4 se pueden rehacer». |
| **M.** Cuadro 15 «acotada al rango» | cerrado | [V] «sin filtrar». Queda el desfase de la casilla (MENOR nuevo). |
| **M.** Datos «por sesión» y «solo la caché de definiciones» | cerrado | [V] «por navegador» y la lista de cachés compartidas, en `.md` y `.tex`. |
| **M.** «Las tres se cumplen» | cerrado | [V] «C1 y C2 se cumplen; C3… sobre el front… pendiente (A8)», en el cuadro de éxito y en la tabla de métricas. |
| **M.** Cifras de pruebas con fechas distintas y tabla en 32 de 35 | cerrado | [V] La tabla de métricas pasa a 52, 349, 34, 10 y 34 del 15 de septiembre. API 52 y lectura natural 34 los ejecuté; corpus 34, contado; extremas 349, sin ejecutar [L]. «32 de 35» solo queda como corte histórico fechado del 13 al 14. Queda la cabecera del README (MENOR nuevo). |
| **M.** «El validador garantiza la precisión» | cerrado | [V] «En esa batería todo lo que llegó al lector era correcto, y eso no es una garantía». Los «garantiza» que quedan son negaciones o sobre `qcut`. |
| **M.** «El acento a 4,5:1» frente a los chips | cerrado | [V] «a 4,5:1 sobre el fondo (… baja a 4,17:1 en algunos libros en tema claro, como SWV369)». |
| **M.** Cuadro 3b sin la corrección de PG2242 | cerrado | [V] Con `Catalogo()`: A1 1, A2 40, **B1 557**, B2 3.127, **C1 23.455** y C2 25.999, en total 53.179; **598** por debajo de B2; literarios A1-B1 sin excluidos **288** (292 contando los excluidos); literarios B2 sin excluidos **1.676**. |
| **M.** «Sorpréndeme» como botón actual en la estrategia | cerrado | [V] «La pestaña «A mi nivel» de *Encontrar*». «Sorpréndeme con algo de mi nivel» solo queda en el cuadro histórico de correcciones. |
| **M.** Cambios después de 2fbf0d9 y el «sin perfil sale tercero» del guion | cerrado | [V] Los 163 excluidos con 3524357 están en `.md`, `.tex` y estrategia. En el Space, sin nivel, *Crime and Punishment* no está entre los 8 primeros; con 1,20 sale segundo. Queda el aviso nuevo (MENOR nuevo). |
| **D.** Amor en B1 «1 y 28» | cerrado | [V] Con la regla escrita (literarios, sin excluidos, a 0,25 del centro, «love|romance|courtship» al principio de palabra en los temas): **B1 1**, **B2 31 en 29 títulos**, **0 libres**. Coincide con el texto. |
| **D.** Empates de nivel por coma flotante | abierto | [V] No hay ninguna prueba con `_cefr(1.4)` ni `_cefr(1.0)` en `pruebas_*.py`. |

## Comprobado y correcto

**Promesas y restos**
- **No queda ninguna promesa de coste ni de garantía de las señaladas:** 0 veces «cabe en la cuota», «~3 h de A100» y «validación ciega» en minúsculas, en los archivos y en los PDF. «Grossman» sale en `documento.pdf` y en `presentacion.pdf`, con el identificador de arXiv. [V]
- **Los PDF están recompilados con los cambios del `.tex`:** «557», «23.455» y «0 USD de cómputo» salen en `documento.pdf`, y «558» no. [V]

**Referencias y cifras citadas**
- **Las referencias nuevas del `.md` y de la estrategia van en APA y en orden alfabético,** y las del `.tex` tienen su entrada en `.bib`. [L y V]
- **La tarifa de Lexile citada es la publicada:** 3.824 USD/año en el nivel 1 y 54.636 USD/año en Enterprise. [V]
- **La frase sobre Kogan et al. está respaldada por el artículo:** «un BERT afinado de 45,7 millones de parámetros, con menos error que PaLM 2-L». [V]
