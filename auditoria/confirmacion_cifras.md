# Confirmación de cifras tras la reestructuración editorial

Tercera pasada de la misma clase que `verificacion_cifras.md` y
`verificacion_cifras_2.md`, sobre el estado de **hoy**: después de `afd000f`
(caso de uso unificado, `tools/contar_guion.py`) y `f36cffe` (7.4 reestructurado,
§7.7 nuevo, cuadro de conjuntos, renumeración 9→10…16→17).

- Fecha: 9 de septiembre de 2026. `HEAD` = `f36cffe`, árbol limpio.
- Windows 11, CPU. **Nada del proyecto se modificó**; la única escritura es este archivo.
- Ejecutado de verdad: `validar_local.py`, `pruebas_extremas.py`,
  `pruebas_integracion.py`, `pruebas_ficha.py`, `pruebas_perfil.py`,
  `tests_smoke.py`, `tools/contar_guion.py`, más scripts propios en el
  scratchpad para los pies de cuadro, las `\ref`, los tres PDF con `pypdf`,
  el filtro estricto del §7.7 y la descarga de la tarjeta de Hugging Face.
- Lo que las dos verificaciones anteriores ya cerraron no se repite salvo
  cuando la reestructuración pudo moverlo. Su único hallazgo abierto —la
  diapositiva 7 con «los otros **cuatro**»— se comprueba abajo, y está resuelto.

---

## 1. `validar_local.py` — las cifras vivas

Una sola ejecución, `exit 0`.

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| Textos evaluados | 47 | `VALIDACION CORRECTA: 47 textos` | **sí** |
| A1 · n · media · desv | 3 · 0,5040 · 0,111 | 3 · 0.5040 · 0.111 | **sí** |
| **A2 · n · media · desv** | **8 · 0,5561 · 0,223** | 8 · 0.5561 · 0.223 | **sí** |
| B1 · n · media · desv | 12 · 0,9276 · 0,198 | 12 · 0.9276 · 0.198 | **sí** |
| B2 · n · media · desv | 12 · 1,2414 · 0,236 | 12 · 1.2414 · 0.236 | **sí** |
| C1 · n · media · desv | 12 · 1,4952 · 0,172 | 12 · 1.4952 · 0.172 | **sí** |
| Baseline · modelo v4 | 0,860 | 0.860 | **sí** |
| Baseline · contar palabras | 0,807 | 0.807 | **sí** |
| Baseline · parcial | 0,668 | 0.668 | **sí** |
| Modelo contra longitud | 0,732 | 0.732 | **sí** |
| Baseline parcial de longitud | «no está definida» | imprime `indefinida` | **sí** |
| Filtro estricto | 31 | 31 | **sí** |
| Sin cuerpo localizable | 2 | 2 | **sí** |
| Rechazados por `continuous_prose` | 10 | 10 | **sí** |
| Los 10, quiénes | nueve A1 y uno B1 | 9 `A1__…`, 1 `B1__…` | **sí** |
| Los 10, por qué | <150 palabras | los diez, mismo `ValueError` | **sí** |
| Balance | 59 − 2 − 10 = 47 | 59 − 2 − 10 = 47 | **sí** |
| Medias | estrictamente crecientes | el guion lo verifica y lo afirma | **sí** |

## 2. Las cinco suites

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| `pruebas_extremas.py` | verde | `Las 205 pruebas extremas pasan` · exit 0 | **sí** |
| `pruebas_integracion.py` | verde | `Los 27 pasos del recorrido encadenan bien.` · exit 0 | **sí** |
| `pruebas_ficha.py` | verde | `Todas las pruebas de la ficha pasan.` · exit 0 | **sí** |
| `pruebas_perfil.py` | verde | `TODO OK: extremo fácil=0.000, extremo difícil=1.977` · exit 0 | **sí** |
| `tests_smoke.py` | verde | `TODO OK` · exit 0 | **sí** |

## 3. La renumeración del `.md`

Pies de cuadro extraídos por regex y ordenados; después, cada cita «Cuadro N»
del cuerpo confrontada con el pie que lleva ese número.

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| Pies de cuadro | 1…17 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17 | **sí** |
| Huecos | ninguno | ninguno | **sí** |
| Repetidos | ninguno | ninguno | **sí** |
| Citas en el texto | 22 citas, cada una a su cuadro | 21 correctas, **1 incorrecta** | **NO (1)** |

Las 21 correctas, una a una: L379→3 catálogo heredado · L427→11 reproducción
local · L433→9 conjuntos · L666→9 · L671→10 métricas · L672→10 · L673→12
balance, →11 orden, →13 *baseline* · L685→10 · L727→11 y →13 · L741→12 ·
L755→11 · L854→11 · L868→11 · L873→12 · L884→11 · L1113→3 · L1129→13 ·
L1146→11 · L1258→4. **Todas las que la renumeración tocó (9→17) apuntan bien.**

**La que no**, `entrega/documento.md` línea 472:

> **Estructura por dominio.** … el modelo funciona mejor en texto informativo
> que en literario, y peor en la banda más fácil (Lexile 500)… Los números están
> en el **Cuadro 7**.

Esos números están en el **Cuadro 8** (*Matriz modelo × dominio*: Literatura
CLEAR, Informativo CLEAR, Lexile 500, Lexile 1300). El Cuadro 7 es la progresión
de modelos. **No es un daño de la renumeración**: `git log -S` la sitúa en
`fbb8e28`, el commit que creó el documento, y afecta a un número que la tanda
de hoy ni tocó. El `.tex` **acierta** en el mismo párrafo, porque no escribe el
número a mano: `cuadro~\ref{cuad:dominio}` (línea 1204). Es un error exclusivo
del `.md`.

**El PDF, aparte.** Como el `.tex` lleva cinco cuadros que el `.md` no trae
(necesidades de la usuaria, comentario→cambio, accionables, métricas por nivel,
riesgos), LaTeX numera **1…22**, no 1…17. Comprobado que esa numeración también
está sana —22 pies, sin huecos ni repetidos— y que las 43 `\ref` distintas
resuelven al cuadro correcto: en el PDF, «cuadro 14» es el de conjuntos,
«cuadro 16» la reproducción local, «cuadro 17» el balance 59→47 y «cuadro 18»
el *baseline*. **La divergencia 17 / 22 es de formato, no un fallo.**

## 4. El cuadro de conjuntos (144 · 38 · 47 · 31 · 59)

| conjunto | lo que dice el cuadro | lo que dice el resto del documento | ¿coincide? |
|---|---|---|---|
| Validación ciega · **144** | 654 aceptados = 510 + 144; Spearman 0,908; ±1 nivel 97,2 % (Cuadro 10) | Cuadro 10 fila 1: 144 · 53,5 % · 97,2 % · 0,908; L1146 y L685 lo repiten; 510+144 = 654 | **sí** |
| Colab · **38** | Spearman 0,829, 100 % dentro de ±1 (Cuadro 10); las cuatro medias que ajustan la recta (7.5) | Cuadro 10 fila 2: 38 · 50,0 % · 100 % · 0,829; la recta 0,72x+0,38 está en L807–812, dentro del 7.5 | **sí** |
| Reproducción local · **47** | 59 − 2 − 10 (Cuadro 12); orden creciente (Cuadro 11); 0,860 / 0,807 / 0,668 (Cuadro 13) | Cuadro 12 da 47; Cuadro 11 son 47; Cuadro 13 son esas tres | **sí** |
| Filtro completo · **31** | sobreviven 31, A1 se queda con un solo texto (7.7) | el guion imprime 31; §7.7 lo repite | **sí** |
| Publicados · **59** | los 59 nombres en el manifiesto; diagnóstico 4.3(a); 89,8 % entre las dos vías | manifiesto: Total 59; §4.3(a) existe en L266–291 y dice 53 de 59 = 89,8 % | **sí** |

Sus punteros internos también apuntan bien: «(7.5)» → la recta de compresión
(L807), «(7.7)» → el filtro (L851), y los cuatro «Cuadro N» que cita están entre
los 21 correctos del punto 3. Y la afirmación que da sentido al cuadro —«**los
38 y los 47 son tandas distintas y no se restan**»— es consistente con §7.7,
que atribuye la diferencia a dos causas (otra extracción y otro filtro).

**Las afirmaciones nuevas del §7.7, comprobadas ejecutando** (rehaciendo el
filtro estricto sobre los 59 PDF, sin cargar el modelo):

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| Con saltos de línea sobreviven… | 31 de 47 | 31 (A1 1 · A2 4 · B1 6 · B2 10 · C1 10) | **sí** |
| …y A1 se queda con | uno solo | **1** | **sí** |
| De los tres A1, caen | dos, por maquetado de lista | 2 de 3, ambos `maquetado_de_lista` | **sí** |
| El que se salva | — | `A1__…Holiday home adverts.pdf` | — |
| Motivos de rechazo en estricto | longitud + maquetado | `corto` 10 · `maquetado_de_lista` 16 | **sí** |

## 5. `tools/contar_guion.py`

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| Palabras habladas | la que publiquen `.md` y `.tex` | **561** (6 bloques: 64+77+213+79+90+44 = 567 brutas, 561 tras descontar acotaciones) | — |
| `entrega/guion_video.md` | = la del guion | línea 10: «**561 palabras y son 3:44**» | **sí** |
| `entrega/guion_video.tex` | = la del guion | línea 145: «**561 palabras** = 3:44» | **sí** |
| Duración a 150 ppm | 3:44 | `3:44` | **sí** |
| Los tres dicen lo mismo | sí | sí | **sí** |

Las cifras mal publicadas antes (552 · 553 · 551 · 597) no aparecen en ninguno
de los dos archivos.

## 6. Los tres PDF (`pypdf`, con búsqueda literal y normalizada)

`documento.pdf` **45 páginas** (eran 43), `presentacion.pdf` 12,
`guion_video.pdf` 6. Los tres son **más nuevos que su `.tex`**: están
recompilados tras `f36cffe`.

### Lo nuevo — debe aparecer

| qué | esperado | doc | pres | guion | ¿coincide? |
|---|---|---|---|---|---|
| Rótulo «La letra pequeña» | en el documento | 2 | — | — | **sí** |
| §7.7 | en el documento | 5 menciones + el `\subsection` | — | — | **sí** |
| Cuadro de conjuntos («cinco conjuntos») | en el documento | 2 | — | — | **sí** |
| Caso de uso · perfil **1,20** | en los tres | 2 | 4 | 4 | **sí** |
| Caso de uso · *Notes from a Dead House* | en los tres | 1 | 1 | 3 | **sí** |
| Caso de uso · «dostoyevski» mal escrito | en los tres | 1 | 1 | 1 | **sí** |
| Caso de uso · 130.104 palabras | en los tres | 1 | 1 | 2 | **sí** |
| Caso de uso · 487 ventanas / 86 s / 1,73 | en los tres | 1/–/5 | 2/2/2 | 2/2/2 | **sí** |
| Caso de uso · 40 ms | doc y guion | 2 | (en la tabla) | 2 | **sí** |
| Cierre que aterriza en decisiones | en el documento | «…dicho como **decisión** y no como métrica» + «lo que este proyecto **recomienda hacer a continuación**» | — | — | **sí** |
| 0,860 · 0,807 · 0,668 | doc y presentación | 6/4/3 | 1/1/1 | — | **sí** |
| 0,5561 · 0,223 · 0,732 · «47 textos» | documento | 5/3/1/5 | –/–/–/1 | — | **sí** |

El **caso de uso está unificado y es coherente con el contrato del código**:
`public_band(1.20)` = `intermedio` y `anchor_cefr(1.20/0.4)` = **B2**, que es
justo lo que dicen la diapositiva 8 («1,20 sobre 2, banda *intermedia*, ancla
B2») y el §8.2. El remate «1,73 frente a 1,20» sale de restar dos cifras del
propio documento.

### Cifras retiradas — ninguna debe aparecer

| cifra retirada | doc | pres | guion | ¿limpio? |
|---|---|---|---|---|
| 0,548 | 0 | 0 | 0 | **sí** |
| 1,248 | 0 | 0 | 0 | **sí** |
| 0,855 | 0 | 0 | 0 | **sí** |
| 0,799 | 0 | 0 | 0 | **sí** |
| 0,665 | 0 | 0 | 0 | **sí** |
| «45 textos» / «46 textos» / «45/46» | 0 | 0 | 0 | **sí** |
| «cuatro escalones» | 0 | 0 | 0 | **sí** |
| «se desvía 0,10» | 0 | 0 | 0 | **sí** |
| 0,93 **como perfil del lector** | 0 | 0 | 0 | **sí** |
| Sherlock / Holmes | 1 pasaje | 0 | 0 | **sí, ver abajo** |

Comprobado también sobre las **fuentes** (`documento.md`, `documento.tex`,
`presentacion.tex`, `guion_video.md`, `guion_video.tex`): cero apariciones de
las ocho cifras retiradas. Y el hallazgo abierto de la verificación anterior
está **cerrado**: la diapositiva 7 dice hoy «el escalón A1–A2 descansa en 3
textos y está dentro del ruido; **los otros tres, no**».

**Los dos avisos del encargo se confirman, y ninguno es fallo.** Los tres
`0,725` de `documento.pdf` y el de `presentacion.pdf` están siempre en la
comparativa de CLEAR, junto a 0,517 de las fórmulas clásicas y 0,89 de
LiteraLevel: es el Pearson del mejor LLM *zero-shot* publicado. Los cinco `0,93`
de `documento.pdf` y el de `presentacion.pdf` son todos el **error ordinal
medio** del embedding MiniLM en la progresión de modelos (1,39 → 0,93 → 0,67),
nunca un perfil de lector.

**El Sherlock que queda es legítimo y conviene no borrarlo.** Es un solo pasaje
de `documento.pdf` (pág. 9, §3.1.1), que describe el cuestionario de perfil:
«Tres fragmentos literarios en escalera (*Alice*, Sherlock Holmes,
*Frankenstein*)». Es una descripción verdadera de lo que hace la app —
`app/perfil.py:181` trae literalmente `"obra": "The Adventures of Sherlock
Holmes"`—, no un resto del caso de uso retirado. Aparece igual en
`entrega/estrategia.md` línea 50. El Sherlock que había que quitar era el
**lector con 0,93 leyendo Sherlock** de la diapositiva, y ese no está en ninguno
de los tres PDF.

## 7. Referencias del `.tex`

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| `\ref` sin `\label` | ninguna | **ninguna** | **sí** |
| `\label` duplicados | ninguno | **ninguno** | **sí** |
| Recuento | — | 56 `\label` únicos · 103 `\ref` (43 distintas) | — |
| `presentacion.tex` / `guion_video.tex` | — | 0 `\label` y 0 `\ref`; nada que romper | **sí** |

Los 13 `\label` no citados (`sec:eda`, `cuad:riesgos`, `fig:dominio`…) son
anclas de navegación sin cita en el cuerpo: no producen ningún `??`.

## 8. La tarjeta publicada en Hugging Face

| qué | valor esperado | valor obtenido | ¿coincide? |
|---|---|---|---|
| Descarga de `…/literalevel-v4/raw/main/README.md` | HTTP 200 | HTTP 200 | **sí** |
| `diff` contra `modelo_v4/README.md` | vacío | **vacío** | **sí** |
| MD5 de las dos | iguales | `d0f2a2e673dcadf72c574206b4a40d4e` en ambas | **sí** |

Idénticas byte a byte, y con el mismo MD5 que en la verificación anterior: la
tanda de hoy no tocó el modelo ni su tarjeta, y la publicada sigue al día.

---

## Lo que no coincide

De las **78 comprobaciones de esta tanda, 77 se reproducen exactamente.** Una no,
y es anterior a los dos commits auditados:

1. **`entrega/documento.md`, línea 472: «Los números están en el Cuadro 7».**
   Debe decir **Cuadro 8**. Los números de los subconjuntos de CLEAR
   (literario/informativo, Lexile 500/1300) están en el Cuadro 8, *Matriz
   modelo × dominio*; el Cuadro 7 es la progresión de modelos. Viene de
   `fbb8e28`, el commit que creó el documento, y **la renumeración de hoy no la
   causó** —toca un número que no se movió—. El `.tex` acierta en el mismo
   párrafo porque usa `\ref{cuad:dominio}` en vez de escribir el número, así que
   **el PDF que se entrega está bien**: el fallo solo se ve leyendo el `.md`.

Y una anotación que no es una cifra publicada, por si alguien la persigue: los
rótulos internos de `validar_local.py` se quedaron un número por detrás de la
renumeración. El guion imprime «**Cuadro 12** - el modelo frente a la señal
trivial», que en el `.md` de hoy es el **Cuadro 13** (y el 18 en el PDF); sus
comentarios de las líneas 50 y 127 dicen «Cuadro 10» y «Cuadro 12» por lo que
hoy son el 11 y el 13, y el de la línea 51 sigue diciendo «A2 se desvía 0,10»
donde el documento ya dice 0,09. Ninguna de esas cadenas es una cifra del
trabajo —son el rótulo de una salida y tres comentarios—, pero quien ejecute el
guion con el documento al lado verá dos números distintos para la misma tabla.

**Todo lo demás coincide.** Las cinco medias con sus *n* y sus desviaciones, el
47 y su balance 59 − 2 − 10, el 31 del filtro estricto con su A1 en uno y sus
dos textos caídos por maquetado, el *baseline* entero (0,860 / 0,807 / 0,668) y
el 0,732 de paso; las cinco suites en verde; los diecisiete pies de cuadro del
`.md` sin huecos ni repetidos y veintiuna de sus veintidós citas —las
diecisiete que la renumeración tocó, todas—; los veintidós del PDF y sus
cuarenta y tres referencias resueltas; las cinco cifras del cuadro de conjuntos
contra el resto del documento; las 561 palabras del guion en sus dos archivos;
los tres PDF recompilados, con la letra pequeña, el §7.7, el cuadro de
conjuntos, el caso de uso idéntico en los tres y el cierre en decisiones, y sin
rastro de ninguna de las cifras retiradas —incluida la diapositiva 7, que ya
dice «tres»—; y la tarjeta de Hugging Face, idéntica byte a byte a la local.

---

**Veredicto: luz verde a la reestructuración —no introdujo ni una discrepancia—; queda un solo arreglo, heredado y solo en el `.md`: la línea 472 debe citar el Cuadro 8, no el 7.**
