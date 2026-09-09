# Unificación del caso de uso recorrido de principio a fin

**Fecha:** 9 de septiembre de 2026
**Ámbito editado:** `entrega/presentacion.tex`, `entrega/guion_video.md`,
`entrega/guion_video.tex`. **No** se ha tocado `documento.md` ni `documento.tex`.
**Fuente de verdad:** `entrega/documento.md` §8.2. **Aviso: hay otro agente editando ese archivo en paralelo, así que los números de línea que cito aquí son los del 9 sep a las 13:58 y se mueven; el texto citado sí es literal.**

---

## 1. El problema, tal como estaba

El mismo recorrido se contaba tres veces con tres lectores distintos:

| Dónde | Lector | Libro | Palabra |
|---|---|---|---|
| `documento.md` §8.2 | perfil **1,20** sobre 2, banda intermedia, ancla B2 | *Notes from a Dead House* (y de paso *Alice*, *Pride and Prejudice*, *Crime and Punishment*) | ninguna |
| `presentacion.tex` diap. 8 | «una lectora de 15 años» en **0,93** | *Sherlock Holmes* | *peculiar* |
| `guion_video.md` / `.tex` | sin nivel declarado | «el libro», sin nombre | ninguna |

Ni el 0,93 ni *Sherlock Holmes* ni *peculiar* existen en el documento: eran
invención de la diapositiva. Está también recogido como hallazgo **E4** en
`auditoria/coherencia_entregables.md:452–461`.

---

## 2. El recorrido elegido, y de dónde sale cada dato

Se conserva **la lectora del documento** (1,20 sobre 2) y **el único libro del
§8.2 que trae cifras medidas de principio a fin** (*Notes from a Dead House*).

| Paso | Dato usado | Procedencia exacta |
|---|---|---|
| 1. Se sitúa | perfil **1,20 sobre 2**, banda **intermedia**, ancla **B2** | `documento.md:915–916`. La palabra «intermedia» la confirma `documento.md:815–816`: bandas *básico* < 0,6 ≤ *intermedio* < 1,4 ≤ *avanzado*; 1,20 cae en intermedio |
| 2. Busca | escribe **«dostoyevski»** mal escrito y el rescate por parecido ortográfico lo encuentra; la búsqueda es por significado, no por título | `documento.md:918–925` (paso 1 del §8.2), que cita literalmente «dostoyevski», «chejov», «Shakespear» |
| 3. Abre | ***Notes from a Dead House***; se descarga de Project Gutenberg y se abre en la app; ficha **contada sobre el texto y no sobre metadatos**: palabras, diálogo, repeticiones, tiempo de lectura al ritmo que le toca a su nivel | `documento.md:926–940` (pasos 2 y 3) y `:941–942` para las **130.104 palabras** |
| 4. Mide | **487 ventanas en 86 s** → media **1,73** sobre 2; **la segunda vez, 0,02 s** porque queda en caché | `documento.md:941–945` (paso 4) |
| 5. Lee | la palabra en **40 ms** en local (lema, gramática, diccionario, desambiguación, IPA); la explicación en contexto llega después. Y la lectura en voz alta, corregida palabra por palabra | `documento.md:946–951` (pasos 5 y 6) |

**El remate del recorrido** —«**1,73 frente a 1,20**: el libro le queda por
encima, y lo sabe antes de la primera página»— no es un dato nuevo: es la resta
de dos cifras que ya están en el §8.2, y encaja con la regla de ritmo de lectura
que el propio §8.2 enuncia (180 o 110 palabras por minuto «según el texto le
quede por debajo o por encima de su nivel», `documento.md:933–936`).

**Lo que NO se ha inventado.** El documento no dice qué palabra consulta la
lectora en el paso 5. Siguiendo la instrucción, **el paso se describe sin
ejemplo concreto**: se dice «la palabra en 40 ms», no se nombra ninguna. Por eso
también se corrigió la frase del guion que prometía «un libro concreto y **una
palabra concreta**» — ahora promete un lector concreto y un libro concreto, que
es lo que hay.

**La salvedad se mantiene, y reforzada.** La diapositiva 8 sigue diciendo que
la lectora ilustra y no es una sesión registrada, y que la única prueba de
usuario real del proyecto es la de Esmeralda, *n* = 1, remitiendo al documento.

---

## 3. Qué se cambió, archivo por archivo

### `entrega/presentacion.tex` — diapositiva 8 reescrita entera

- Entradilla: «El recorrido del apartado 8.2 del documento» + perfil 1,20 +
  la salvedad de siempre (ilustra / Esmeralda *n* = 1).
- Diagrama TikZ de cinco cajas: **Se sitúa → Busca → Abre → Mide → Lee**
  (antes: Se sitúa → Busca → Elige → Lee → Practica).
- Tabla «Paso / Lo que produce» rehecha con las cinco filas nuevas.
- Línea de cierre nueva: «1,73 frente a 1,20…».
- **Ajustes geométricos** para que el diagrama no se saliera (ver §4):
  `text width` 2,4 cm → **2,25 cm**, `inner sep` 4 pt → **3,5 pt**,
  `node distance` 3 mm → **2 mm**, y tres `\vspace` recortados
  (2→1 mm, 3→2 mm, 4→2 mm) para absorber la línea de cierre añadida.

### `entrega/guion_video.md` y `entrega/guion_video.tex` — los dos igual

- **Fase S, parlamentos Uno a Cuatro** reescritos con los datos de arriba.
  «Uno» ahora dice el nivel (1,20 sobre 2, banda intermedia); «Dos» sustituye
  «una novela de detectives victoriana» por *dostoyevski* mal escrito; «Tres»
  nombra el libro y da 130.104 palabras, 487 ventanas, 86 segundos y media 1,73
  contra el 1,20 de la lectora; «Cuatro» añade los 40 milisegundos.
- Se **retiró** «Aquí se ve que arranca duro y se suelta», que afirmaba una
  tendencia concreta de la curva que el documento no mide para este libro.
- Nota de puesta en escena nueva en la caja «En pantalla» de la fase S: usar en
  la demo el mismo caso que el §8.2 y la diapositiva 8, y aviso de que las
  cifras habladas son las medidas **sobre ese libro**.
- Sección «Por qué está construido así»: la promesa «un libro concreto y una
  palabra concreta» pasa a nombrar el caso compartido por los tres entregables.
- Cifra de duración actualizada (ver §5) y **definición del recuento explicitada**
  («sin contar las acotaciones entre paréntesis»), para que sea reproducible.
- Relojes de fase reajustados (ver §5).
- Corregida una divergencia **preexistente** entre `.md` y `.tex`: la fase N
  decía «puestas por **nadie** que haya leído el libro» en el `.md` y «por
  **alguien**» en el `.tex`. Ahora los dos dicen «nadie».

---

## 4. Comprobaciones tras compilar

Compilado con `tectonic -X compile` (PATH `/d/tex/bin`, caché `D:/tex/cache`).

### Desbordes en `presentacion.tex`

Tectonic imprime las advertencias **una vez por pasada** y hace dos pasadas, así
que la cuenta bruta duplica los avisos únicos.

| | Antes | Después |
|---|---|---|
| Avisos brutos (2 pasadas) | **8** | **6** |
| Avisos únicos | 4 | 3 |
| `Overfull \hbox` línea 137 (diapositiva «Los datos, en cifras») | 9,12 pt | 9,12 pt · sin cambio, **preexistente** |
| `Overfull \vbox` línea 243 (diapositiva «El modelo desplegado») | 9,49 pt | 9,49 pt · sin cambio, **preexistente** |
| `Overfull \hbox` de la **diapositiva 8** (el diagrama de cinco cajas) | **19,24 pt** | **desaparecido** |
| `Overfull \vbox` de la **diapositiva 8** | **12,54 pt** | **desaparecido** |
| `Underfull \hbox` línea 353 (badness 2027) | sí | sí · sin cambio, preexistente |

**Los desbordes bajaron, no subieron: de 8 a 6.** Los dos que quedan no son de
la diapositiva 8 y ya estaban antes de tocar nada; no se han arreglado para no
meter cambios ajenos al encargo.

Aritmética del diagrama, por si hay que volver a tocarlo: cinco cajas de
`text width` + 2 × `inner sep`, más cuatro huecos de `node distance`. Con los
valores viejos salían ≈ 415 pt contra un ancho de texto de ≈ 396 pt (de ahí los
19,24 pt de desborde); con los nuevos salen ≈ 378 pt, con ~18 pt de margen.

### Páginas

- `presentacion.pdf`: **12 páginas**, las mismas que antes. La diapositiva 8
  sigue siendo **una sola página** (página 8), no se partió en dos.
- `guion_video.pdf`: 6 páginas, **0 avisos** de `Overfull`/`Underfull` (igual
  que antes del cambio).

### Texto extraído del PDF con `pypdf` 6.17.0

Página 8 de `presentacion.pdf`, verbatim:

> Ejemplo de uso y aplicación
> El recorrido del apartado 8.2 del documento, paso a paso: una lectora cuyo
> perfil da 1,20 sobre 2, banda intermedia. Los pasos y las cifras son los de la
> aplicación; la lectora ilustra, no es una sesión registrada. La única prueba
> de usuario real es la de Esmeralda, n = 1, y está en el documento.
> 1. Se sitúa / cuestionario / → 1,20 · 2. Busca / escribe mal / «dostoyevski» ·
> 3. Abre / Notes from / a Dead House · 4. Mide / 487 ventanas / en 86 s ·
> 5. Lee / palabra: 40 ms / y en voz alta
> Se sitúa — 1,20 sobre 2, banda intermedia, ancla B2
> Busca — búsqueda por significado; el nombre mal escrito llega igual
> Abre — ficha sobre el texto: 130.104 palabras, diálogo, repeticiones
> Mide — 487 ventanas en 86 s → media 1,73; la segunda vez, 0,02 s
> Lee — la palabra en 40 ms; la voz alta, corregida palabra por palabra
> 1,73 frente a 1,20: el libro le queda por encima, y lo sabe antes de la primera página.

**Restos del recorrido viejo, buscados en las 12 páginas:**

| Término | Resultado |
|---|---|
| `Sherlock` | **no aparece** |
| `Holmes` | **no aparece** |
| `peculiar` | **no aparece** |
| `misterio` | **no aparece** |
| `Ana` | solo como subcadena de «vent**ana**s» (pág. 8) y «cerc**ana**» (pág. 11); **no hay ninguna «Ana» como palabra suelta** (comprobado con `\bAna\b`) |
| `0,93` | aparece en la **página 5**, y **es correcto**: es el error ordinal del *embedding* de 384 d en la gráfica del Hallazgo 1, nada que ver con el perfil de la lectora |
| `1,20` · `1,73` · `dostoyevski` · `Dead House` · `487` · `130.104` · `40 ms` · `Esmeralda` | todos en la página 8, donde deben estar |

En `guion_video.pdf`: aparecen `551 palabras`, `3:40`, `dostoyevski`,
`Notes from a Dead House`, `130.104`, `487 ventanas`, `86 segundos`, `1,73`,
`1,20 sobre 2`, `1:05 – 3:35`; **no** aparecen `553`, `3:41` ni
`detectives victoriana`.

### Paridad `.md` ↔ `.tex`

Script que extrae los seis bloques «…» del `.md` y los seis entornos `dice` del
`.tex`, normaliza el marcado y los compara palabra a palabra:
**PARIDAD: IDÉNTICOS**, los seis bloques.

---

## 5. Recuento del guion

Regla de recuento: solo lo que va entre comillas angulares dentro de la sección
«EL GUION», **excluyendo las acotaciones escénicas entre paréntesis**
(*(mostrar el resultado)*, *(doble clic en una palabra)*, *(leer una frase en
voz alta al micrófono)*), que no se dicen en voz alta.

| | Palabras habladas | A 150 ppm |
|---|---|---|
| **Cifra que publicaban los dos archivos** | 553 | 3:41 |
| **Recuento real del texto que había** | **510** | 3:24 |
| **Recuento real del texto nuevo** | **551** | **3:40** |

**La cifra de 553 ya estaba mal antes de tocar nada**: el texto que había eran
510 palabras. Publicaba 43 palabras de más. Ahora la cifra publicada (551) es un
recuento real y reproducible, y por eso se ha añadido a los dos archivos la
aclaración de que las acotaciones no cuentan.

Con 4:40 de objetivo, 3:40 hablados dejan **exactamente 1:00** para lo que la
demo tarda de verdad — que es lo que el propio guion promete.

### Relojes de fase reajustados

La fase S creció 41 palabras habladas (≈ 16 s). Con los relojes viejos, la S se
quedaba con 15 s de holgura para toda la demo en vivo, que es precisamente la
fase que más espera acumula. Se redistribuyó sin tocar el total de 4:40:

| Fase | Antes | Ahora | Habladas | Holgura |
|---|---|---|---|---|
| A · Atención | 0:00 – 0:35 | **0:00 – 0:30** | 64 p = 26 s | 4 s |
| N · Necesidad | 0:35 – 1:15 | **0:30 – 1:05** | 77 p = 31 s | 4 s |
| S · Satisfacción | 1:15 – 3:20 | **1:05 – 3:35** | 276 p = 110 s | **40 s** |
| V · Visualización | 3:20 – 4:10 | **3:35 – 4:15** | 90 p = 36 s | 4 s |
| A · Acción | 4:10 – 4:40 | **4:15 – 4:40** | 44 p = 18 s | 7 s |
| | | **280 s** | **220 s** | **60 s** |

La gráfica de barras de `guion_video.tex` («Cómo se reparte el tiempo») se
recalculó en consecuencia: **11 / 13 / 53 / 14 / 9 %**, suma 100. Las dos frases
que la comentan siguen siendo ciertas: «la S se lleva la mitad» (53 %) y «A y N
juntas no pasan de un cuarto» (24 %).

---

## 6. Lo que habría que arreglar en `documento.md` §8.2 — NO lo he tocado

El apartado se titula «Un recorrido completo, **con números reales**» y es un
montaje: los pasos mezclan cuatro libros. Por orden de gravedad:

### 6.1 · La búsqueda no encuentra el libro que se abre — **el fallo principal**

`documento.md:918–925` hace que la lectora pida «*una novela de detectives
victoriana*» y `:941` mide **Notes from a Dead House**, que es Dostoyevski,
1862, memorias de un penal siberiano: ni victoriana, ni detectives, ni novela.
El paso 1 promete algo que el paso 4 no entrega, y el §8.2 no dice en ningún
momento que se haya cambiado de libro.

**Arreglo sugerido (el que he usado en mis tres archivos):** que el paso 1 use
el ejemplo de rescate ortográfico que el propio párrafo ya cita —«dostoyevski»
mal escrito— en lugar de la consulta de detectives. Es la única forma de que la
búsqueda y el libro medido sean el mismo caso sin inventar mediciones nuevas.
La consulta de detectives puede quedarse, pero entonces como ejemplo aparte de
la búsqueda semántica, fuera de la numeración del recorrido.

### 6.2 · Un libro de 1,73 no debería salir en la búsqueda de un lector de 1,20

El paso 1 dice que el buscador «le devuelve obras **dentro de su rango**». El
paso 4 mide 1,73 de media para el libro que abre. Con las bandas del propio
documento (`:815–816`: intermedio < 1,4 ≤ avanzado), 1,20 es *intermedio* y
1,73 es *avanzado*: son bandas distintas. O el §8.2 explica que el libro le
queda por encima —que es lo que he hecho yo en la diapositiva y en el guion, y
resulta más vendible, porque enseña la herramienta avisando— o hay que
reconciliar el ejemplo. Tal como está, se contradice.

### 6.3 · El paso 3 ilustra la ficha con tres libros que no son el del recorrido

`:937–940` da las proporciones de diálogo de *Alice* (73 %), *Pride and
Prejudice* (28 %) y *Crime and Punishment* (31 %) dentro del paso 3 del
recorrido, sin dar la de *Notes from a Dead House*. Es una comparación
legítima y vale la pena conservarla, pero **no dentro de la numeración del
recorrido**: debería salir a una nota o a un párrafo aparte, para que los seis
pasos hablen de un solo libro.

### 6.4 · El §8.1 mete un cuarto libro en el cuadro

`:907` estima el coste del vistazo rápido «medido sobre *Crime and
Punishment*». Es correcto como medición, pero deja al lector con cuatro libros
en dos apartados consecutivos. Si el recorrido pasa a ser de un solo libro,
convendría decir explícitamente que esa cifra es de otro.

### 6.5 · El paso 5 no nombra ninguna palabra

`:946–950` describe la consulta de una palabra sin decir cuál. No es un error,
pero es lo que impide que los tres entregables enseñen «una palabra concreta»,
que es justo lo que el guion prometía. **Si se mide y se publica una consulta
real** —qué palabra, en qué frase de *Notes from a Dead House*, qué devolvió—
la diapositiva 8 y el guion pueden incorporarla en un minuto; hasta entonces
los tres archivos describen el paso sin ejemplo, a propósito.

### 6.6 · Nota menor de vocabulario

`:915–916` llama «banda intermedia» a la del 1,20, y está bien según `:815–816`
(*básico* / *intermedio* / *avanzado*). Pero `:824–826` presenta el mismo
agrupamiento con las etiquetas del MCER —*usuario básico* / *independiente* /
*competente*—. Conviven dos juegos de nombres para las mismas tres bandas. Yo he
usado «intermedia», que es el que aparece en el §8.2 y en la interfaz.

---

## 7. Fuera de ámbito, anotado y no tocado

- **`guion_video.md` línea 68 / `guion_video.tex`**, fase A: el gancho sigue
  diciendo «Nadie le dijo que *Moby Dick* le quedaba grande y que *El sabueso
  de los Baskerville* le quedaba justo». Es retórica de apertura, no el
  recorrido, y por eso lo he dejado; pero conviene saber que el vídeo menciona
  un libro de detectives al principio y demuestra Dostoyevski después. Si
  molesta, se cambia por dos títulos cualesquiera sin tocar cifras.
- **`presentacion.tex:137`** (`Overfull \hbox` 9,12 pt): las tres columnas de
  «Los datos, en cifras» a `0.33\textwidth` suman más que el ancho disponible.
  Se arregla bajando a `0.31`. No lo he hecho por no meter cambios fuera del
  encargo.
- **`presentacion.tex:243`** (`Overfull \vbox` 9,49 pt): la diapositiva «El
  modelo desplegado» va llena. Se arregla recortando uno de sus `\vspace`.
