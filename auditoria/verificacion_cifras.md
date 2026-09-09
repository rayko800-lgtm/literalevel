# Verificación de cifras de `entrega/documento.md`

Encargo estrecho: **ejecutar el código y comprobar que cada cifra publicada sale
de donde el documento dice que sale**. No se audita redacción, ni se buscan
contradicciones entre archivos, ni se leyó `auditoria/`. Única pregunta por
cifra: ¿se reproduce?

- Fecha: 9 de septiembre de 2026
- Máquina: la de Miguel (Windows 11, CPU)
- Nada del proyecto se modificó. La única escritura es este archivo.
- Comandos ejecutados: `python -X utf8 validar_local.py`,
  `python -X utf8 pruebas_extremas.py`, `python -X utf8 pruebas_integracion.py`,
  `python -X utf8 tests_smoke.py`, y varios cálculos propios en `python -c`.

---

## 1. `validar_local.py` — Cuadros 10, 11 y 12

Una sola ejecución. **Todo coincide, dígito a dígito.**

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| 46 textos evaluados | Cuadros 10 y 11, líneas 410, 707, 770, 777 | 46 | sí |
| A1 media 0,5040 (n=3) | Cuadro 10, línea 701 | 0.5040, n=3 | sí |
| A2 media 0,5480 (n=7) | Cuadro 10, línea 702 | 0.5480, n=7 | sí |
| B1 media 0,9276 (n=12) | Cuadro 10, línea 703 | 0.9276, n=12 | sí |
| B2 media 1,2414 (n=12) | Cuadro 10, línea 704 | 1.2414, n=12 | sí |
| C1 media 1,4952 (n=12) | Cuadro 10, línea 705 | 1.4952, n=12 | sí |
| Desviaciones 0,111 · 0,237 · 0,198 · 0,236 · 0,172 | Cuadro 10 | 0.111 · 0.237 · 0.198 · 0.236 · 0.172 | sí |
| Medias estrictamente crecientes | líneas 41–42, 1150 | el guion lo verifica y lo afirma | sí |
| Cuadro 12: modelo v4 = **0,855** | línea 772 | 0.855 | sí |
| Cuadro 12: contar palabras = **0,799** | líneas 412, 773, 1065 | 0.799 | sí |
| Cuadro 12: parcial descontando longitud = **0,665** | línea 774 | 0.665 | sí |
| Modelo contra longitud = **0,725** | línea 787 | 0.725 | sí |
| Baseline parcial «no está definida» | líneas 771–776 | el guion imprime literalmente `indefinida` | sí |
| Textos sin cuerpo localizable: **2** | Cuadro 11, línea 728 | 2 | sí |
| Rechazados por `continuous_prose`: **10** | Cuadro 11, línea 729 | 10 | sí |
| Los 10 son **nueve A1 y uno B1** | línea 754 | 9 ficheros `A1__…`, 1 fichero `B1__…` | sí |
| Los 10 caen **todos por <150 palabras** | líneas 756–760 | los 10 con «El texto es muy corto: se necesitan al menos 150 palabras» | sí |
| Pasarían el filtro completo: **30** | línea 741 | 30 | sí |

Salida literal de la ejecución (sin las barras de carga):

```
nivel    n   media 0-2  desv (pobl.)   (Colab reportó)
A1       3      0.5040         0.111   —
A2       7      0.5480         0.237   0.6479
B1      12      0.9276         0.198   0.9513
B2      12      1.2414         0.236   1.2883
C1      12      1.4952         0.172   1.4950

textos sin cuerpo localizable: 2
textos que pasarian el filtro COMPLETO (con saltos de linea): 30
textos que fallaron al puntuar: 10
    [9 ficheros A1__… y 1 fichero B1__…, los diez «muy corto: … al menos 150 palabras»]

Cuadro 12 - el modelo frente a la senal trivial (46 textos)
  modelo v4                                  0.855
  contar palabras, sin modelo                0.799
  modelo descontando la longitud (parcial)   0.665
  (de paso: modelo contra longitud           0.725)
  contar palabras descontando la longitud:   indefinida

VALIDACION CORRECTA: 46 textos, 5 niveles, medias estrictamente crecientes.
```

De propina, coincide también la frase de la línea 718 («A2 se desvía 0,10»):
0,6479 − 0,5480 = 0,0999.

---

## 2. `pruebas_extremas.py` y el contraste WCAG

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| **205** pruebas extremas | cierre de la suite | `Las 205 pruebas extremas pasan: ningun manejador lanzo excepcion.` (exit 0) | sí |
| **40 parejas** de contraste (8 por paleta) | prueba «todas las paletas son legibles» | la prueba imprime `5 paletas x 8 pares, todas AA` → 5 × 8 = 40 | sí |
| Peor pareja de **texto normal = 4,53** | umbral AA 4,5:1 | **4,5273** en `hielo/boton-alto` → 4,53 | sí |
| Peor pareja de **título = 3,11** | umbral AA texto grande 3,0:1 | **3,1081** en `menta/titulo-3` → 3,11 | sí |

El cálculo de contraste es **propio, no el del repositorio**: un script
independiente lee `app/paletas.py`, convierte `#rrggbb` y `rgba(...)` a sRGB,
aplica la luminancia relativa de WCAG 2.x (umbral 0,03928, gamma 2,4, pesos
0,2126 / 0,7152 / 0,0722) y la razón `(L1+0,05)/(L2+0,05)`. Cinco paletas
(`hielo`, `amanecer`, `menta`, `papel`, `medianoche`) × 8 parejas = 40. Ninguna
baja de su umbral.

Cinco peores de texto normal (umbral 4,5): 4,5273 `hielo/boton-alto` ·
4,6121 `papel/pestana-elegida` · 4,6200 `amanecer/pestana-elegida` ·
4,6470 `menta/pestana-elegida` · 4,6548 `papel/boton-alto`.

Cinco peores de título (umbral 3,0): 3,1081 `menta/titulo-3` ·
3,1084 `menta/titulo-2` · 3,1259 `amanecer/titulo-2` · 3,1316 `papel/titulo-3` ·
3,1328 `amanecer/titulo-3`.

El margen es estrecho —4,53 contra 4,5 pedido— pero se cumple.

---

## 3. Tamaños en disco

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| Modelo **328 MB** | doc líneas 644, 822, 1102 («los **pesos**», «los 328 MB del modelo») | `modelo_v4/model.safetensors` = 328 489 204 B = **328,49 MB** decimales | sí, tal como está escrito |
| `modelo_v4/` completo | — | 332 053 001 B = **332,05 MB** decimales (316,67 MiB) | **el directorio son 332, no 328** |
| Diccionario **243 MB** | doc líneas 224, 521 | `kaikki_diccionario.db` = 243 326 976 B = **243,33 MB** decimales | sí |
| Suma **571 MB** | `DESPLIEGUE.md` líneas 15 y 87 (no aparece en `documento.md`) | 328 + 243 = 571 con las cifras publicadas; en disco **575,38 MB** | aritmética sí; disco real no |

Desglose de `modelo_v4/`: `model.safetensors` 328,49 MB · `tokenizer.json`
3,56 MB · `config.json`, `tokenizer_config.json` y `README.md` por debajo de
0,01 MB cada uno.

Matiz importante, porque decide a quién afecta: **el 328 del documento es
correcto tal como está redactado** —dice «pesos», y el fichero de pesos son
328,49 MB—. Lo que no cuadra es el 571 de `DESPLIEGUE.md`: ahí la cifra
describe *lo que hay que subir al Volume*, y eso es la carpeta entera,
`tokenizer.json` incluido. El total a desplegar son **575 MB**, no 571.

---

## 4. Constantes de `app/scoring.py`

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| Ventana de **250 palabras** | doc líneas 247–252 | `BLOCK_WORDS = 250`; con 5.000 palabras los bloques tienen tamaño único `{250}` | sí |
| Mínimo **150 palabras** | doc línea 154 y mensaje de error | `MIN_WORDS = 150`; `fixed_blocks(149)` → `[]`, `fixed_blocks(150)` → 1 bloque | sí |
| Tope de **8 bloques** | doc línea 288 | `MAX_BLOCKS_PER_DOC = 8`; 5.000 palabras (20 ventanas posibles) → 8 bloques | sí |
| **MAX_LENGTH = 256** | `_puntuar_bloques` | `MAX_LENGTH = 256` | sí |
| Escala pública = interna × **0,4** | `AGENTS.md`, contrato de escalas | `public_score(y) = clip(y,0,5)*0.4`; comprobado en todo −1..6 a paso 0,001 | sí |
| Bandas cortan en **0,6 y 1,4** | doc líneas 799, 809 | barrido 0..2 a paso 0,0001: básico→intermedio exactamente en 0,6000; intermedio→avanzado exactamente en 1,4000 | sí |

Comprobado además que los cortes son **emergentes, no constantes escritas a
mano**: `public_band` no contiene ni 0,6 ni 1,4. Calcula
`ANCHORS[floor(clip(score,0,2)·2,5 + 0,5)]` y agrupa A1–A2 / B1–B2 / C1–C2. De
ahí salen los cortes: la letra pasa a B1 cuando `s·2,5+0,5 ≥ 2`, o sea
`s ≥ 0,6`; y a C1 cuando `s·2,5+0,5 ≥ 4`, o sea `s ≥ 1,4`. Los dos números del
documento son consecuencia del agrupamiento MCER, tal como afirma la línea 809.

### El desempate `floor(x + 0,5)`

| afirmación | valor obtenido | ¿coincide? |
|---|---|---|
| `anchor_cefr` usa `floor(y+0,5)`, no `round` | idéntica a `ANCHORS[floor(y+0,5)]` en todo −1..6 a paso 0,0005 | sí |
| «los empates suben, no se van al par» | empates internos 0,5 · 1,5 · 2,5 · 3,5 · 4,5 → **A2, B1, B2, C1, C2** | sí |
| `round` de Python daría otra cosa | los mismos empates con `round` → **A1, B1, B1, C1, C1**: tres letras distintas | sí, el problema descrito era real |
| «la palabra y la letra no pueden contradecirse» (doc línea 810) | recorriendo la escala interna 0..5 a paso 0,00025 por el camino real de la app —`anchor_cefr(interno)` contra `public_band(public_score(interno))`— **0 discordancias** | sí |

`pruebas_extremas.py` llega a lo mismo por su cuenta: «la banda nunca
contradice a la letra — las 201 puntuaciones concuerdan» y «la interfaz y el
contrato dan la misma letra — las 50.001 coinciden».

Un aviso para quien repita esta comprobación: si se recorre la escala
**pública** y se recupera la interna dividiendo por 0,4, aparece una
discordancia falsa en `p = 0,6`, porque `0.6/0.4 = 1.4999999999999998` en coma
flotante. No es un fallo del código —la app nunca hace esa división—, es un
artefacto de la comprobación. Midiendo desde la escala interna, que es como
funciona de verdad, no hay ninguna.

---

## 5. Las dos rectas de compresión

Ajuste propio por mínimos cuadrados (`numpy.polyfit`, grado 1).

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| Colab, 4 medias A2–C1: **0,7196x + 0,3760** | doc línea 795 | **0,719575x + 0,376050** → 0,7196x + 0,3760 | sí |
| Locales, 5 medias A1–C1: **0,67x + 0,41** | doc líneas 796, 1046 | **0,668950x + 0,408080** → 0,67x + 0,41 | sí |
| «el ajuste ronda 0,72 × real + 0,38» | doc línea 791 y docstring de `public_band` | 0,7196 → 0,72 y 0,3760 → 0,38 | sí |
| «la pendiente está muy por debajo de 1» | doc línea 797 | 0,7196 y 0,6690, las dos | sí |

Anclas usadas, las del encargo y las del documento: A1 0,0 · A2 0,4 · B1 0,8 ·
B2 1,2 · C1 1,6. Medias de Colab: A2 0,6479 · B1 0,9513 · B2 1,2883 · C1 1,4950
—las imprime el propio `validar_local.py` en su columna «Colab reportó», así que
no hay que ir a buscarlas fuera—. R² = 0,9912 para la recta de Colab y
R² = 0,9637 para la local. Las dos rectas se reproducen a todos los decimales
que el documento publica.

---

## 6. Aritmética interna

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| 510 + 144 = **654** | doc líneas 658, 666 | 654 | sí |
| 77/144 = **53,47 %** | doc línea 666 | 0,534722… = 53,47 % | sí |
| 140/144 = **97,22 %** | doc líneas 666, 673 | 0,972222… = 97,22 % | sí |
| 59 − 1 − 2 − 10 = **46** | Cuadro 11 | 46 | sí |

La aritmética cierra. Lo que no se puede comprobar desde el repositorio es de
dónde salen el 77 y el 140 —el conjunto de validación de 144 documentos no
acompaña al proyecto—, y **el documento lo dice él mismo** en la línea 666 («lo
único comprobable desde el repositorio es la aritmética interna») y en las
líneas 688, 1079 y 1092. No es una cifra publicada sin aviso: es una cifra
publicada con su aviso. Aquí solo se confirma que la aritmética que el documento
se ofrece a que comprueben, cuadra.

Nota lateral, no publicada: 654 aceptados + 57 descartados = 711 documentos
brutos, consistente con la línea 658.

---

## 7. `entrega/manifiesto_corpus_externo.md`

| cifra publicada | dónde | valor obtenido | ¿coincide? |
|---|---|---|---|
| A1 **12** | tabla del manifiesto | 12 nombres listados | sí |
| A2 **9** | tabla del manifiesto | 9 nombres listados | sí |
| B1 **13** | tabla del manifiesto | 13 nombres listados | sí |
| B2 **12** | tabla del manifiesto | 12 nombres listados | sí |
| C1 **12** | tabla del manifiesto | 12 nombres listados | sí |
| Total **58** archivos | tabla del manifiesto | 58, sin duplicados, y 12+9+13+12+12 = 58 | sí |
| «Sin nivel en el nombre: 0» | tabla del manifiesto | los 58 llevan prefijo de nivel | sí |
| Los 58 existen en `C:\Users\laura\Downloads` | — | **58 de 58 encontrados** | sí |
| «El archivo número 59 no llegó a bajarse a este disco» | párrafo tras la tabla | **está en el disco** | **NO** |

Los recuentos por nivel cuadran y los 58 ficheros existen. Lo que no se sostiene
es la explicación del archivo 59.

**En `Downloads` hay 59 PDF con prefijo de nivel, no 58.** El que sobra es:

```
C:\Users\laura\Downloads\A2__LearnEnglish_Reading-A2-An-email-from-a-friend.pdf
```

Se le escapa a todo el mundo por un guion bajo. `validar_local.py` recorre
`glob("*LearnEnglish-Reading*.pdf")`, con **guion**; este fichero se llama
`LearnEnglish_Reading`, con **guion bajo**. Por eso el guion nunca lo ve, por
eso no está en el manifiesto y por eso pareció «no disponible». (Existe además
un `B2__LearnEnglish-Reading-B2-An-email-from-a-friend.pdf`, que sí está
listado: son dos textos distintos con título parecido, no un duplicado.)

Puesto a prueba, en lectura sola y sin tocar nada:

- tiene cuerpo localizable entre «Reading text» y «Tasks»: 187 palabras;
- pasa `continuous_prose` **con las dos variantes**, la floja (`ok`) y la
  estricta con saltos de línea (`ok`);
- se puntúa sin error: **0,613**, banda «intermedio», ancla B1, 1 bloque.

Consecuencias sobre cifras publicadas, si se corrigiera el `glob`:

| cifra | publicada | con el archivo 59 dentro |
|---|---|---|
| Cuadro 11, «menos: no disponible» | −1 | **0** |
| Cuadro 11, evaluados | 46 | **47** |
| Cuadro 10, n de A2 | 7 | **8** |
| Cuadro 10, media de A2 | 0,5480 | **0,5561** |
| Textos que pasan el filtro completo | 30 | **31** |

El resultado que sostiene el trabajo **no se rompe**: con el archivo dentro,
A1 0,5040 < A2 0,5561 y las medias siguen estrictamente crecientes. El daño es
de exactitud, no de conclusión. Pero el manifiesto afirma algo verificablemente
falso —«no llegó a bajarse a este disco»— cuando el fichero lleva ahí desde el 2
de septiembre, y presenta el 59 como «una cifra heredada, no un archivo
localizado» cuando sí es localizable. Esa frase es la que hay que corregir.

---

## 8. `requirements.txt` contra lo instalado

Comprobado con `importlib.metadata.version`.

| paquete | `requirements.txt` | probado según la cabecera | instalado | ¿coincide? |
|---|---|---|---|---|
| torch | `>=2.4,<3` | 2.14.0+cpu | 2.14.0+cpu | sí |
| transformers | `>=5.16,<6` | 5.16.1 | 5.16.1 | sí |
| gradio | `==6.26.0` | 6.26.0 | 6.26.0 | sí |
| pypdf | `>=5.0,<7` | 6.17.0 | 6.17.0 | sí |
| numpy | `>=1.26,<3` | 2.4.2 | 2.4.2 | sí |
| pandas | `>=2.2,<4` | 3.0.0 | 3.0.0 | sí |
| sentence-transformers | `>=3.0,<7` | 6.0.1 | 6.0.1 | sí |
| spacy | `>=3.7,<3.9` | 3.8.16 | 3.8.16 | sí |
| wordfreq | `>=3.1,<4` | — | 3.1.1 | sí, en rango |
| openai | `>=1.40,<4` | 3.8.0 | 3.8.0 | sí |
| pydantic | `>=2.7,<3` | — | 2.13.5 | sí, en rango |
| plotly | `>=6.0,<8` | 7.0.0 | 7.0.0 | sí |
| en_core_web_sm | URL fijada a 3.8.0 | 3.8.0 | 3.8.0 | sí |

Las nueve versiones que la cabecera dice «probado de punta a punta con» son
**exactamente** las instaladas. Ninguna instalada se sale de su rango. El
`en_core_web_sm` instalado (3.8.0) casa con `spacy>=3.7,<3.9`, como pide el
comentario del propio fichero.

---

## 9. Las otras suites, ejecutadas por completitud

| guion | resultado |
|---|---|
| `tests_smoke.py` | `TODO OK` |
| `pruebas_integracion.py` | `Los 27 pasos del recorrido encadenan bien.` |
| `pruebas_extremas.py` | `Las 205 pruebas extremas pasan` (exit 0) |
| `validar_local.py` | `VALIDACION CORRECTA` (exit 0) |

---

## Resumen: lo que NO coincide

De las **48 cifras comprobadas ejecutando código, 45 se reproducen exactamente.**
Las tres que no:

1. **`modelo_v4/` son 332 MB decimales, no 328.** *(matiz, no error del
   documento)* El documento dice «los **pesos** ocupan 328 MB» y eso es
   correcto: `model.safetensors` son 328,49 MB. Pero la carpeta entera son
   332,05 MB, porque incluye `tokenizer.json` (3,56 MB). Quien lea «los 328 MB
   del modelo» (línea 1102) y dimensione una carpeta, se queda corto.

2. **La suma de 571 MB de `DESPLIEGUE.md` debería ser 575 MB.** 328 + 243 = 571
   es aritmética correcta sobre las cifras publicadas, pero ahí la cifra
   describe *lo que hay que subir al Volume*, y eso en disco son
   332,05 + 243,33 = **575,38 MB**. Cuatro megas; importan solo si el Volume se
   dimensiona justo. (Esta cifra no aparece en `entrega/documento.md`.)

3. **El manifiesto se equivoca sobre el archivo número 59.** Dice que «no llegó
   a bajarse a este disco» y que el 59 es «una cifra heredada, no un archivo
   localizado». El archivo está en `Downloads` desde el 2 de septiembre:
   `A2__LearnEnglish_Reading-A2-An-email-from-a-friend.pdf`. No lo ve nadie
   porque lleva guion bajo en `LearnEnglish_Reading` y el `glob` de
   `validar_local.py` busca guion. Puntúa 0,613, es A2 y pasa los dos filtros.
   Incluirlo movería A2 de 0,5480 (n=7) a 0,5561 (n=8), los evaluados de 46 a
   47, el recuento estricto de 30 a 31 y la resta «−1 no disponible» a 0. **El
   orden estrictamente creciente aguanta igual.**

Nada de lo anterior toca las cifras que sostienen el argumento del trabajo. Las
medias por nivel, sus desviaciones, el Cuadro 12 entero (0,855 / 0,799 / 0,665 /
0,725), el balance de 59 a 46, las constantes de `scoring.py`, los cortes de
banda en 0,6 y 1,4, el desempate `floor(x+0,5)`, las dos rectas de compresión,
la aritmética 510+144 / 77÷144 / 140÷144, las 205 pruebas, las 40 parejas de
contraste con sus peores casos en 4,53 y 3,11, y las trece versiones fijadas:
**todo se reproduce, y buena parte al cuarto decimal.**
