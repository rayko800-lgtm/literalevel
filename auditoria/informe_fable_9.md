# Informe de auditoría 9 — LiteraLevel

Auditor externo (Fable). Fecha: 9 de septiembre de 2026. Estado auditado: `HEAD = 201287a`.
Regla del encargo: empezar por lo dibujado; archivo y línea en cada hallazgo; sin tocar nada del proyecto salvo este archivo.

## Recuento

| Gravedad | Nº |
|---|---|
| CRÍTICO | 0 |
| SERIO | 0 |
| MENOR | 9 |
| DUDA | 0 |

**Ninguna cifra publicada está mal.** Las 30 cifras vivas del encargo recalculan exactas ejecutando los guiones; las nueve retiradas no aparecen en ningún PDF; los tres PDF llevan lo de hoy. Los nueve hallazgos son de redacción, colocación o aritmética de apoyo, y **tres de ellos los introdujo una corrección de hoy** (H1, H7, H9). Ninguno cambia un resultado.

Respuesta a la parte D, con esas palabras: **sí, queda algo que avergonzaría al autor si lo lee un profesor universitario**, y son tres cosas, ninguna numérica: H1 (una frase nueva que explica mal su propia figura), H2 (un pie de figura que afirma lo contrario de lo que su curva enseña) y H3 (rótulos que se pisan en la figura 9 del PDF). Las otras seis no las vería un profesor.

---

## Hallazgos, por gravedad

### [MENOR] H1 — La frase añadida hoy para explicar «siete cajas, seis pasos» explica lo que no pasa
- **Dónde:** `entrega/documento.tex:2058-2059`; PDF `documento.pdf` p. 33 (texto extraído, línea 1988). Introducida en `201287a`.
- **Qué dice:** «La figura 9 resume el recorrido —donde la ficha y la curva van en cajas separadas— y los seis pasos que siguen lo detallan.»
- **Por qué:** en la lista que sigue (`documento.tex:2107-2148`) la ficha es el paso 3 y la curva el paso 4: **también van separadas en el texto**. La séptima caja de la figura es «1. Perfil» (`documento.tex:2067`), que en el texto no es un paso enumerado sino la frase previa «un lector cuyo perfil da 1,20». El paréntesis de hoy no explica la diferencia; la atribuye a algo que no ocurre. Es el patrón del encargo: una corrección (el mensaje de `201287a` dice «la ficha y la curva van separadas en la figura y juntas en el texto») que se escribió sin volver a contar la lista.
- **Arreglo:** «—donde situarse es la primera caja y los seis pasos que siguen, las otras seis—».

### [MENOR] H2 — El pie de la figura 10 dice que la novela «se endurece hacia el tramo central», y la media móvil dibujada dice otra cosa
- **Dónde:** `entrega/documento.tex:2214-2215` (pie de `fig:curva_wp`); PDF p. 34.
- **Qué dice:** «la novela se endurece de forma sostenida hacia el tramo central».
- **Por qué:** recalculado sobre `datos_figuras/curva_War_and_Peace_ma.dat` (la misma columna `media_movil` que pinta la línea gruesa): el máximo de la media móvil está en el **capítulo 289** (1,858) y los ocho valores más altos son los capítulos 286–292; el segundo pico es el 87. Por tercios, la media móvil vale 1,723 / 1,735 / 1,746: sube ligeramente hacia el **final**, y el tercio central promedia exactamente la media del libro (1,735). La figura enseña dos endurecimientos —hacia el capítulo 90 y hacia el 290— con el centro en la media. El pie afirma lo que la curva no muestra, y está en «la figura que mejor explica el producto».
- **Arreglo:** «se endurece en dos tramos, alrededor de los capítulos 90 y 290, con un valle hacia el 65».

### [MENOR] H3 — En la figura 9 del PDF los rótulos de tiempo se pisan
- **Dónde:** `entrega/documento.tex:2082-2083` y `2089-2090` (etiquetas `40 ms en local`, `una frase` y el `label=below:mientras lee` del recuadro); PDF p. 33, comprobado sobre la página renderizada.
- **Qué se ve:** «40 ms en local», «mientras lee» y «una frase» quedan en la misma línea y se superponen; y la flecha curva Abrir→Palabra cruza el rótulo «un clic».
- **Por qué:** el recuadro de fondo (`fit=(palabra)(voz)`) pone su etiqueta a la misma altura que las etiquetas `below=1.5mm` de las cajas. Es solo maquetación, pero es la primera figura del apartado de producto.
- **Arreglo:** `label=below:` → `label={[yshift=-3mm]below:mientras lee}` o mover las etiquetas de tiempo dentro de las cajas.

### [MENOR] H4 — Los rótulos «básico / intermedio / avanzado» de la figura 2 siguen en el centro de las bandas derogadas
- **Dónde:** `entrega/documento.tex:448-450`.
- **Qué dice:** `at (0.4,-0.85) {básico}`, `at (1.2,-0.85) {intermedio}`, `at (1.8,-0.85) {avanzado}`.
- **Por qué:** 0,4 / 1,2 / 1,8 son exactamente los centros de 0–0,8 / 0,8–1,6 / 1,6–2, los cortes que `5c76c63` retiró de los rellenos y las llaves (`:427-429`, `:453-455`) pero no de los rótulos. Los centros vigentes son 0,3 / 1,0 / 1,7. En el PDF (p. 6) «intermedio» cae bajo B2, descentrado respecto a su llave 0,6–1,4. No dice nada falso —cada rótulo sigue dentro de su tramo— pero es el último resto del error de ayer.
- **Arreglo:** `0.3`, `1.0`, `1.7`.

### [MENOR] H5 — La figura 4 dibuja solo la tanda «histórica» del cuadro 12 y no lo dice
- **Dónde:** `entrega/documento.tex:1362-1364`, `1376`, `1389` (figura); `1336-1343` (cuadro 12).
- **Qué dice:** el cuadro tiene ocho filas con columna «Tanda» (tres «recalculada»); la figura pinta cinco barras, todas de filas «histórica», con la etiqueta a secas «XGBoost» = 0,28 / 1,42. En el mismo cuadro, la fila **en negrita** de XGBoost dice 0,340 / 1,081, y la regresión logística de 3 variables aparece dos veces (0,29/1,39 histórica y 0,313/1,295 recalculada). El pie cierra con «Datos del cuadro 12» sin decir cuáles.
- **Por qué:** un lector que compare figura y cuadro encuentra dos valores para «XGBoost» y ninguna nota que los distinga. No altera la tesis (la representación manda) porque los dos primeros modelos comparten representación en ambas tandas.
- **Arreglo:** en el pie, «Se dibuja la tanda histórica del cuadro 12, que es la que tiene las cinco representaciones».

### [MENOR] H6 — El «mismo caso contado una sola vez» cambia de sexo entre entregables
- **Dónde:** `entrega/documento.tex:2056` («un lector cuyo perfil da 1,20») y `:2118` («él está en 1,20»); `entrega/documento.md:914`, `:928`; frente a `entrega/presentacion.tex:249-250` («una lectora… la lectora ilustra») y `entrega/guion_video.tex:171` («una lectora con perfil 1,20»).
- **Por qué:** el guion afirma (`guion_video.tex:172-173`) «Los tres entregables cuentan el mismo recorrido, con el mismo lector y el mismo libro». Los datos coinciden (1,20 · 130.104 · 487 · 86 s · 1,73 · 40 ms, comprobados en los tres PDF); el personaje no.
- **Arreglo:** «lectora» en `documento.tex:2056` y `:2118` (y en el `.md`), o «lector» en los otros dos.

### [MENOR] H7 — AGENTS.md suma 332 + 243 + 0,9 y escribe 575
- **Dónde:** `AGENTS.md:92`, corregido hoy en `5c76c63` (antes «562 MB (modelo 328 + diccionario 233 + CSV 0,9)», que sí sumaba).
- **Qué dice:** «En disco, 575 MB (modelo 332 con su tokenizador + diccionario 243 + CSV 0,9)».
- **Por qué:** 332 + 243 + 0,9 = 575,9. Medido con `os.path.getsize`: `modelo_v4/` 332,1 MB, `kaikki_diccionario.db` 243,3 MB; con el CSV, 576,3. Los «575 MB» de `PENDIENTES.md:89` son correctos porque esa fila dice «Modelo + diccionario» (575,4) y no incluye el CSV. AGENTS metió el CSV en el paréntesis y no en la suma.
- **Arreglo:** «576 MB (…)» o quitar «+ CSV 0,9» del paréntesis.

### [MENOR] H8 — «Cuadro 13» y «Cuadro 11» sin decir de qué documento, cuando el PDF numera distinto
- **Dónde:** `validar_local.py:50` («Cuadro 11 del…»), `:147` («Cuadro 13 del documento»), `:201` (lo imprime); `README.md:122` («las tres cifras del Cuadro 13»).
- **Por qué:** esos números son los de `documento.md` (11 = validación, 13 = baseline). En `documento.pdf` la validación es el **cuadro 16** y el baseline el **cuadro 18**; el cuadro 13 del PDF es la matriz modelo × dominio. `PENDIENTES.md:77` («Cuadro 13 del `.md`, 18 del PDF») y `entrega/estrategia.md` («Cuadro 21 del PDF —el 16 de la copia de lectura—») ya lo hacen bien; el validador y el README, no. Quien ejecute el guion con el PDF delante busca el cuadro equivocado.
- **Arreglo:** «Cuadro 13 del .md (18 del PDF)» en las tres líneas.

### [MENOR] H9 — La barra ANSVA del guion redondea 53,6 % a 53 % para que sume 100
- **Dónde:** `entrega/guion_video.tex:186-194`, retocada hoy en `f36cffe`; PDF `guion_video.pdf` p. 1.
- **Qué dice:** 11 / 13 / 53 / 14 / 9 %, con anchos 1,32 / 1,56 / 6,36 / 1,68 / 1,08 (suman 12,0).
- **Por qué:** los relojes del guion (`:218, :241, :263, :322, :347`) dan 30 / 35 / 150 / 40 / 25 s = 280 s → 10,7 / 12,5 / 53,6 / 14,3 / 8,9 %. Redondeando bien, 11 / 13 / 54 / 14 / 9 (suma 101). Se eligió 53 para cuadrar el 100. Trivial, y la frase «la S se lleva la mitad» sigue siendo cierta.
- **Arreglo:** «54 %», o una nota «redondeado a 100».

---

## Parte A — lo dibujado, figura por figura

Se abrieron los **16 `tikzpicture`** de `documento.tex` y los **3** de `presentacion.tex` (más el de `guion_video.tex`), se cotejó cada coordenada contra el texto y los `.dat`, y se **renderizaron las páginas** de los tres PDF con las figuras (PyMuPDF) para mirar lo impreso, no solo el fuente.

| Figura | Qué se comprobó | Resultado |
|---|---|---|
| Portada (`:206-216`) | 0,908 · A1<…<C1 · 97,2 % contra cuadro 15 (`:1666-1667`) | ✓ |
| Fig. 1 pipeline (`:378-409`) | «8,2 a 2.022 ventanas/s» contra cuadro 21; «100 % llega a 256» contra T4 (`:1242`) y §8.3 | ✓ |
| **Fig. 2 escala** (`:424-459`) | rellenos `0.6`/`1.4`, llaves `0.6`/`1.4`, cortes 0,20…1,80 = `escala_cefr.dat`, anclas n×0,4, contra `:1849-1850` («básico < 0,6 ≤ intermedio < 1,4 ≤ avanzado») y `scoring.public_band` | ✓ rellenos y llaves; **H4** rótulos |
| Fig. 3 catálogo (`:1001-1024`) | 723+185+69+52+53+115 = 1.197; 199,5 = 1.197/6; «seis de cada diez» = 60,4 %; «121» = 69+52 | ✓ |
| Fig. 4 progresión (`:1355-1392`) | barras contra cuadro 12; azar 1/6 = 0,167 | ✓ valores; **H5** tanda |
| Fig. 5 épocas (`:1434-1461`) | 0,560 / 0,578 / 0,637 / 0,660 contra `:1423-1425` | ✓ |
| Fig. 6 dominio (`:1500-1529`) | 11 barras y 6 `n` contra cuadro 13; hueco de v2 en prensa a propósito | ✓ |
| **Fig. 7 validación** (`:1723-1759`) | barras y errores desde `validacion.dat` = cuadro 16 = salida de `validar_local.py`; `n = 3/8/12/12/12` en su columna y por encima de media+desv; anclas 0/0,4/0,8/1,2/1,6 | ✓ |
| **Fig. 8 compresión** (`:1873-1920`) | cinco puntos = `validacion.dat`; recta 0,72x+0,38: **recalculada por mínimos cuadrados sobre las cuatro medias de Colab** que imprime el validador (0,6479 / 0,9513 / 1,2883 / 1,4950) → 0,7196x + 0,3760 ✓; sobre las cinco locales → 0,667x + 0,411 ✓; flecha A2 en 0,556 (corregida hoy de 0,548) | ✓ |
| Fig. 9 recorrido (`:2065-2099`) | «< 2 min», «12,7 s a minutos», «40 ms» contra cuadro 20 (`:2039-2047`) | ✓ cifras; **H1** frase, **H3** solape |
| **Fig. 10 War and Peace** (`:2158-2208`) | sombreado desde **1,4** y rótulo «≥ 1,4» (corregido hoy); media 1,7346→1,735; mín. 1,333 en cap. 34; máx. 1,990 en cap. 202; 1,990−1,333 = 0,657; `media_movil` = ventana centrada de 15 (recalculada, diferencia máxima 0,0000) | ✓ dibujo; **H2** pie |
| Fig. 11 curvas (`:2223-2250`) | C&P media 1,6793, rango 1,270–1,891; Alice 1,4967→1,497, 1,296–1,878; «casi dos décimas» = 0,182 | ✓ |
| Fig. 12 velocidad (`:2294-2323`) | 8,19 / 112,7 / 2.022 = `velocidad.dat`; 13,76→13,8×; 246,9→247× | ✓ |
| Fig. 13 competencia (`:2422-2443`) | 0,517 / 0,725 / 0,89 contra cuadro 22 | ✓ |
| Pres. diap. 5 (`presentacion.tex:164-182`) | 1,061 / 0,93 / 0,67 contra cuadro 12; «XGBoost de 300 árboles» = `notebook_proyecto.py:1297` `n_estimators=300` | ✓ |
| Pres. diap. 8 (`:256-267`) | 1,20 · 487 · 86 s · 1,73 · 130.104 · 0,02 s · 40 ms contra `documento.tex:2136-2145`; «apartado 8.2» ✓; es la diapositiva 8 ✓ | ✓ |
| Pres. diap. 9 (`:294-311`) | idem fig. 13 | ✓ |
| Guion barra ANSVA (`guion_video.tex:186-194`) | anchos contra relojes | **H9** |

El comentario interno `name path=corte16` (`documento.tex:2178`) conserva el nombre del corte viejo aunque ya dibuja 1,4; es invisible y no cuenta como hallazgo.

**`.dat` contra su tabla:** `validacion.dat` = cuadro 16 = salida del validador (n suma 47); `velocidad.dat` = cuadro 21; `escala_cefr.dat` = cortes de `public_band` y de la figura 2; las tres curvas = pies de las figuras 10 y 11. Ninguna discrepancia.

## Parte B — ¿alguna corrección de hoy inventó, exageró o rompió algo?

Leídos los seis commits (`8b579b6..201287a`) y el diff completo de `documento.tex`, `presentacion.tex`, `guion_video.tex`, `validar_local.py`, `app/scoring.py`, `notebook_proyecto.py`, README, AGENTS, PENDIENTES, DESPLIEGUE y estrategia.

**Rompió / inventó (los tres son menores):** H1 (`201287a`, frase que explica mal la figura 9), H7 (`5c76c63`, suma de AGENTS), H9 (`f36cffe`, redondeo forzado). Ninguno toca una cifra de resultado.

**Correcciones de hoy comprobadas y correctas:**
- «cuatro escalones» → «tres escalones siguientes» (`documento.tex`, `presentacion.tex:241`): cinco niveles dan cuatro escalones; menos el A1–A2, tres ✓.
- «A2 se desvía 0,10» → «0,09»: |0,5561 − 0,6479| = 0,092 ✓ (Colab reportó 0,6479 según la salida del validador).
- Flecha de la figura 8 0,548 → 0,556 ✓; `.py` y `.ipynb` del cuaderno sincronizados (0 apariciones de 0,548; 2 de 0,556 en el `.ipynb`).
- Bandas y llaves de la figura 2 a 0,6 / 1,4 ✓; sombreado de la figura 10 a 1,4 ✓ (visto en el PDF).
- README: «margen 0,053» = 0,860 − 0,807 ✓; titular con las cinco medias locales ✓.
- Guion: 561 palabras = 3:44 (561/150·60 = 224,4 s) ✓, reproducido por `tools/contar_guion.py`.
- PENDIENTES 553→561, 571→575 ✓ (575,4 medido).
- `app/scoring.py` (4 líneas de comentario) no cambia comportamiento: `tests_smoke.py` imprime el mapa 0→A1 básico … 5→C2 avanzado y las 205 pruebas pasan.

**Cifras vivas recalculadas ejecutando** (`python -X utf8 …`): `validar_local.py` → 47 textos, A2 n=8 media 0,5561 desv 0,223, medias estrictamente crecientes, Cuadro 13 0,860 / 0,807 / 0,668, longitud 0,732, filtro estricto 31, diez rechazados (9 A1 + 1 B1) ✓. `pruebas_extremas.py` → 205 pasan ✓; contraste recalculado con la fórmula del test: 40 parejas, mín. texto 4,53, mín. título 3,11 ✓. `pruebas_integracion.py` 27 pasos ✓. `pruebas_ficha.py` ✓. `tests_smoke.py` ✓. `tools/contar_guion.py` → 561 = 3:44 ✓. 575 MB ✓ (H7 es la descomposición, no el total). 7 USD/mes (2 en documento, 1 en presentación) y 31 s (`documento.tex:2556`) presentes; no se remidieron (no hay guion que los produzca).

## Parte C — los tres PDF

Texto extraído con `pypdf` (`documento.pdf` 44 págs., `presentacion.pdf` 12, `guion_video.pdf` 6). Marcas de tiempo: cada PDF es posterior a su `.tex` (`documento.pdf` 14:41:49 > `.tex` 14:41:00; `presentacion.pdf` 14:02 > `.tex` 13:51; `guion_video.pdf` 14:41:55 > `.tex` 14:41:00), y el último commit (14:42) los incluye.

- **Llevan lo de hoy:** «tres escalones» (doc. líneas 43 y 1714 del texto extraído), «se desvía 0,09» (1725, 1965), cuadro 14 de los cinco conjuntos (1526), §7.7 (1953), «para qué sirve esto», «prima del autor»; presentación «los otros tres», «Nuestro codificador», caso 1,20 / 487 / 86 s; guion 561 = 3:44, «estrictamente creciente», «diapositiva 8».
- **Cifras retiradas:** 0,548 · 1,248 · 0,855 · 0,799 · 0,665 · 45/46 · «cuatro escalones» · «desvía 0,10» · 553 · 571 · 3:41 — **cero apariciones** en los tres PDF. «0,8 y 1,6» aparece una vez (doc. 1773) y es el párrafo que explica que fueron un error corregido: legítimo.
- **Falsos positivos confirmados como tales:** los 0,725 (doc. 2236, 2250, 2254; pres. 128) son el Pearson del LLM en CLEAR; «Sherlock Holmes» (doc. 319) es «Tres fragmentos literarios en escalera (Alice, Sherlock Holmes, …)», el cuestionario de perfil.
- **Figuras impresas:** vistas en las páginas renderizadas 6, 23, 28, 30, 33, 34, 35 del documento, 5, 7, 8, 9 de la presentación y 1 del guion. Lo dibujado coincide con el `.tex` corregido.

## Parte D — ¿queda algo que avergonzaría al autor si lo lee un profesor universitario?

**Sí.** Tres cosas, y ninguna es una cifra:

1. H1 — una frase de hoy que dice que la figura 9 separa «la ficha y la curva» cuando el texto también las separa, y calla que la caja de más es «Perfil».
2. H2 — el pie de «la figura que mejor explica el producto» afirma que la novela se endurece «hacia el tramo central», y la media móvil que tiene encima hace su máximo en el capítulo 289.
3. H3 — en esa misma figura 9, tres rótulos de tiempo se pisan en el PDF.

Las seis restantes (H4–H9) son de las que se arreglan en un minuto y un profesor no vería.

## Lo que se revisó y está bien (para distinguirlo de lo no revisado)

Además de la tabla de la parte A: numeración cruzada figura↔cuadro en el PDF (cuadro 20 cita «figura 10» = War and Peace ✓; el texto cita cuadros 16/18 donde el PDF los numera 16/18 ✓); presentación «Los datos en cifras» 4.724 / 654 / 61.642 contra cuadro 7 y cuadro 14 ✓; cuadro 15 y su lectura del 97,2 % (44,4 % azar, 50 % constante bajo uniforme) ✓; balance 59 − 2 − 10 = 47 ✓ y coincide con la salida del validador; «31 de esos 47» ✓; «0,052» del escalón A1–A2 = 0,5561 − 0,5040 ✓; «Alice 73 %, Pride 28 %, C&P 31 %» no se remidieron (fuera del alcance de los guiones dados).

No se ha modificado ningún archivo del proyecto salvo este informe.
