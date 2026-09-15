# Auditoría cruzada a ciegas: CATÁLOGO Y DESPLIEGUE

- Auditor: entrega-e6 (811c22). Área de entrega-f4.
- Código auditado: HEAD `5d35e85ffa2dc4bd2c48b0f908649140e13605ec`.
- Archivos: `app/catalogo.py`, `app/ficha.py`, `tools/catalogar_corpus.py`,
  `tools/medir_corpus.py`, `tools/cerrar_corpus.py`, `tools/marcar_no_lectura.py`,
  `tools/desplegar_app.py`, `tools/desplegar_front.py`, `pruebas_corpus.py`,
  `pruebas_despliegue.py`, `pruebas_despliegue_front.py`.
- Método: solo lectura. **[V]** significa que lo comprobé ejecutando algo
  (datos en disco, código cargado o el Space). **[L]** significa que solo lo leí.
- Pruebas, ejecutadas con `LITERALEVEL_SIN_CLAVES=1` [V]:
  `pruebas_despliegue.py` 13 OK, `pruebas_despliegue_front.py` 16 OK,
  `pruebas_corpus.py` 27 OK.

Resumen: 2 serios, 4 menores y 1 duda. Lo más importante es el primero: en los
15.357 textos libres, el buscador solo indexa el título y el autor.

---

## SERIO

### S1. Los 15.357 textos libres se buscan solo por título y autor [V]

**Dónde:** `app/catalogo.py:319-325` y `tools/marcar_no_lectura.py:16-18`

**Qué dice:**
```python
return (d["title"].astype(str) + ". " + d["author"].astype(str) + ". "
        + d["hook"].astype(str) + " " + d["huella_texto"].astype(str)).tolist()
```
Y en marcar_no_lectura: «Sin gancho ni texto real, el vector de búsqueda de esas
filas es casi solo el de sus temas».

**Por qué:** en `catalogo_externo.csv`, `hook` y `huella_texto` están vacíos en
las 15.357 filas (en Gutenberg `huella_texto` falta solo en 89 de 53.179). Cargué
`Catalogo()` y recalculé la huella del `.npy` externo sobre `_texto_indexable()`.
Da `c0de66f8d3dfff21`, que es el `catalogo_emb_ext_c0de66f8d3dfff21.npy` que hay
en disco. Así que los vectores de verdad salen de cadenas como
`'Dham Taka , Dham Taka. Deepanshu  Garg .  '`.

Consecuencias:
- Una búsqueda temática entre cuentos solo compara títulos. Buscar «amor» con
  un perfil B1 en el Space devuelve «MY FUTURE» (autor 휘영김), «SANGKURIANG»
  y «dak side» entre los primeros.
- Los temas tampoco se indexan, así que la explicación de marcar_no_lectura no
  es la causa real.
- Las pruebas no lo pueden ver: todos los fixtures de `pruebas_corpus.py`
  (líneas 66, 74, 188, 195, 246…) usan `hook` y `huella_texto` vacíos.

**Arreglo:** que `catalogar_corpus` rellene `huella_texto` de los libres con el
arranque de `ficha.para_medir(texto)` (sin la atribución), regenerar el `.npy`
externo y añadir una prueba que exija texto indexable más allá del título.

### S2. Los textos del final de cada grupo nunca se miden y salen del catálogo sin aviso [V]

**Dónde:** `tools/medir_corpus.py:146-161` y `tools/catalogar_corpus.py:14` y `:235-236`

**Qué dice:**
```python
for (_, _), g in resto.groupby(["fuente", resto["nivel_editor"].fillna("sin")]):
    idx, ids, trozos, cuenta = [], [], [], 0
    ...
        if cuenta >= bloque:
            r = obtener("bloque", ids, "\n\n".join(trozos))
```
El docstring dice que un texto se queda fuera solo si «el filtro de prosa lo
rechaza».

**Por qué:** cuando termina el bucle de un grupo, lo que queda por debajo de 250
palabras se descarta sin medirlo.

Sobre los 16.251 textos cargados:
- 11.039 se miden solos.
- 5.212 van a bloques en 13 grupos.
- **16 quedan en colas de grupo que nunca se miden.** Por ejemplo, 2 textos de
  african_storybook nivel 3 (201 palabras) y 2 de letsread nivel 2 (247 palabras).
- 878 van en bloques que rechaza el filtro de prosa.

878 + 16 = 894, justo la diferencia entre 16.251 y las 15.357 filas del CSV.
Los 16 salen por `dificultad.isna()` sin que nada lo cuente aparte, y el recuento
«sin medida, fuera» los mezcla con los rechazos de prosa.

**Arreglo:** al acabar cada grupo, unir la cola al último bloque (o medirla sola
si llega a `MIN_WORDS`), e imprimir cuántos textos quedan en cola.

---

## MENOR

### M1. `buscar` solo mira los 3n primeros y puede devolver menos de n sin decirlo [L]

**Dónde:** `app/catalogo.py:633`

**Qué dice:** `for i in orden[:n * 3]:`

**Por qué:** si en esos 3n puestos hay más de 2n excluidos (índices, los 163 que
no son lectura) o por debajo de `minimo_similitud`, la lista se queda corta
aunque haya candidatos válidos más abajo. El aviso solo cuenta los «flojos», no
los excluidos. En el Space no lo vi pasar: «amor» devolvió 12.

**Arreglo:** recorrer `orden` entero hasta llenar n.

### M2. La clave de medida no incluye la versión del modelo [L]

**Dónde:** `tools/medir_corpus.py:41-48`

**Qué dice:** `for parte in (tipo, "|".join(map(str, ids)), texto):`

**Por qué:** si cambia `modelo_v4`, las medidas en disco se reutilizan como si
fueran del modelo nuevo. Hoy no pasa, porque CLAUDE.md declara el v4 final. Pero
nada lo impide.

**Arreglo:** meter en la clave una huella de `modelo_v4/config.json` y de los pesos.

### M3. A StoryWeaver se le presume licencia y paso al catálogo si falta el campo [V datos]

**Dónde:** `tools/catalogar_corpus.py:172`, `:182` y `:188`

**Qué dice:** `if not f.get("al_catalogo", fuente == "storyweaver"):` y
`f.get("licencia") or ("CC BY 4.0" if fuente == "storyweaver" else "")`

**Por qué:** hoy no hace daño. Los 16.022 registros de StoryWeaver llevan
`CC BY 4.0` escrito. Pero un registro futuro sin licencia entraría como libre, y
la barrera de `licencia_libre` no lo pararía porque recibe la licencia ya
presumida.

Resto de fuentes, verificado:
- african_storybook: 316 CC-BY dentro; 52 fuera (NC, NC-SA y 1 desconocida).
- VOA: 261 de dominio público dentro; 216 adaptados de agencia fuera.
- letsread: 517 dentro (CC-BY-4.0 y 3.0); 770 fuera.

**Arreglo:** exigir el campo `licencia` también en StoryWeaver y no catalogar si falta.

### M4. «1 minutos» [V en el front publicado]

**Dónde:** `app/ficha.py:113-114`

**Qué dice:** `if minutos < 90: return f"{minutos} minutos"`

**Por qué:** un cuento de un minuto sale como «1 minutos» en la píldora de la
ficha y en «Tiempo: 1 minutos a tu ritmo». Es uno de los cuatro fallos de la
prueba de persona sobre 45d9999.

**Arreglo:** `"1 minuto" if minutos == 1 else f"{minutos} minutos"`.

---

## DUDA

### D1. El escaneo de credenciales lee el parquet comprimido como texto [V parcial]

**Dónde:** `tools/desplegar_app.py:293-303`

**Qué dice:** «El parquet del corpus abierto SI se escanea: lleva texto plano dentro.»

**Por qué:** `corpus_abierto.parquet` va comprimido con SNAPPY.
- Comprobé que el texto sigue legible en los bytes: `Dham Taka` aparece y
  « the » sale 1.054 veces.
- Pero Snappy sustituye repeticiones por referencias hacia atrás. Una clave que
  apareciera dos veces podría quedar partida en la segunda.
- Una clave aleatoria que aparece una sola vez casi seguro queda literal y se
  detectaría.

No lo probé con una clave plantada.

**Arreglo:** escanear la columna `texto` descomprimida (`pd.read_parquet`) en vez
de los bytes.

---

## Comprobado y correcto

**Medida**
- **La atribución no entra en la medida.** `catalogar_corpus` mide el texto
  crudo y añade la atribución solo al texto servido; `ficha.para_medir` quita la
  licencia de Gutenberg y `_ATRIBUCION_LIBRE`, y `marcar_no_lectura` la aplica
  antes de contar palabras. [L]
- **Los bloques son de su fuente y su nivel, en orden de id**, y los textos
  medidos en bloque llevan `medida = bloque`. [L] Recuentos en S2 [V].
- **La medida se puede reanudar.**
  - `leer_hechas` ignora una línea cortada.
  - `_Escritor.volcar` escribe a `.tmp` y hace `replace` atómico, sin pisar un
    shard que otra ejecución escribió entre medias.
  - El `finally` vuelca el búfer si se interrumpe con Ctrl+C.
  - Si el proceso muere de golpe se pierden hasta 249 unidades, y el docstring
    lo dice («de 250 en 250»).
  - Sin la primera pasada completa no se forman bloques.

  Todo esto [L].

**Catálogo y licencias**
- **Licencias.** `cargar` aborta con «NO CATALOGO NADA» si llega un texto no
  libre. Lo adaptado de AP/Reuters se queda fuera aunque venga con `al_catalogo`.
  Las prueba `pruebas_corpus` [V pruebas]. Recuentos por fuente en M3 [V].
- **Obras repetidas.** Se quita la misma obra en dos bibliotecas, dando
  prioridad a StoryWeaver: se fueron 364. [V]

**Búsqueda y recomendación**
- **Orden de búsqueda con nivel:**
  - El nivel ordena solo dentro de lo relevante, a 0,05 del mejor parecido.
  - Un título acertado va siempre delante.

  En el Space con perfil B1 [V]:
  - «A Midsummer Night's Dream» → PG1514 primero.
  - «dostoyevski» → obras de Dostoyevsky.
  - «hrrr» ya no devuelve el texto «hrrr»: devuelve cuentos de terror.
- **Exclusiones.** Los 163 textos de `no_lectura_externo.csv` y los índices
  están fuera de buscar y recomendar. En el Space no apareció ningún id excluido
  en las búsquedas probadas. [V]
- **Intercalado de libres** en los puestos 2, 5, 8…, y ningún texto con aviso de
  contenido en los 5 primeros de la recomendación por nivel. [L]
- **Correcciones** aplicadas sin tocar el `.npy`, y cache de embeddings por
  huella de las filas que de verdad quedan. [L] La huella del externo la
  recalculé y cuadra [V].

**Despliegue**
- **`desplegar_app`:**
  - Sube solo la lista blanca exacta. Todos los módulos locales que importan
    `api.py` y `ui.py` están en la lista [V].
  - Exige que cada archivo esté confirmado en git y sube el contenido del
    commit, no el del disco, con LF.
  - Escanea credenciales antes de subir; salta los `.mp3`.
  - Añade la regla LFS de `*.mp3` antes de subir audios.
  - No toca `README.md`, `app.py` ni los `.npy` o `.db` colocados a mano.

  [L] y [V pruebas].
- **`desplegar_front`:**
  - Exige `front/` limpio.
  - Aborta si la meta `literalevel-api` no apunta a la API, también con el HTML
    minificado. Esta regla la puse yo en f6a7942 y la reviso igual.
  - Compara los binarios publicados con los locales.

  [V pruebas] (16 OK). Tampoco hay archivos ignorados dentro de `front/public` ni
  de `front/src` que se pudieran quedar fuera [V].
