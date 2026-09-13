# Validación del v4 con lectura graduada por sus editores — 12 de septiembre de 2026

**Estado: en curso.** Hecho African Storybook. StoryWeaver y VOA se están
descargando; esta nota se completa cuando terminen. **No se ha reentrenado nada:**
todo es evaluación con los pesos finales del v4.

Reproducible con:

```
python -X utf8 tools/niveles_african_storybook.py <booklistjs.php guardado>
python -X utf8 tools/bajar_storyweaver.py
python -X utf8 tools/bajar_voa.py --tope 60
python -X utf8 validar_graduados.py
```

Las puntuaciones, sin texto, quedan en `auditoria/validacion_graduados_puntuaciones.csv`.

## Qué se valida y qué no

Los niveles de estas fuentes los pone **cada editor, con su propio criterio y para
lectores infantiles**. No son niveles del MCER. Lo único que se puede comprobar es
el **orden**: si el nivel 1 del editor puntúa por debajo del 2, el 2 del 3, etc.

| Fuente | Nivel del editor | Textos en inglés | Licencia | ¿Al catálogo? |
|---|---|---|---|---|
| African Storybook | 1–5 (300 cruzados; 67 sin cruzar) | 367 | 316 CC BY · 48 CC BY-NC · 3 CC BY-NC-SA · 1 desconocida | Solo los CC BY |
| StoryWeaver | 1–4 | ~16.800 (descargando) | CC BY 4.0, toda la plataforma | Sí |
| VOA Learning English | **Sin nivel por artículo** | muestra de 60 por sección (descargando) | Dominio público; lo adaptado de AP, Reuters o AFP tiene derechos | Solo lo escrito por VOA |
| Let's Read | Sí | — | CC | **No descargado**: su lector no expone una API localizable |

## Decisiones de método

- **Cuentos cortos (decisión de Miguel):** los de 250 palabras o más se miden solos;
  los más cortos se juntan en bloques de al menos 250 palabras, **siempre dentro de
  la misma fuente y el mismo nivel**. La cola que no llega se declara y se deja fuera.
  Las métricas se dan también por separado para «solos» y «bloques».
- **Páginas en párrafos.** Un libro ilustrado trae una o dos frases por página en
  renglones sueltos. Tal cual, el filtro de prosa del v4 rechazó **70 de 219**
  unidades de African Storybook por «parece una lista, un menú o una tabla». Unir
  cada página en un párrafo —que es lo fiel al libro— dejó los rechazos en **9**.
- **Fuga:** se descarta cualquier texto que comparta la mitad o más de sus 8-gramas
  con ELG CEFR English, el corpus de entrenamiento. En African Storybook: **0 textos,
  máximo compartido 0,000**.
- **VOA:** se quita el aviso del reproductor («No media source currently available»)
  y el glosario final («Words in This Story»); se marca como interno todo artículo
  cuyo crédito diga que se adaptó de Associated Press, Reuters o AFP.

## African Storybook

210 de 219 unidades puntuadas. Las 9 que no: 7 del nivel 1 rechazadas por el filtro
de prosa (6 «parece una lista», 1 «forma de frase»), 1 cola corta del nivel 1 y 1
cola corta de los cuentos sin nivel. **Detrás de esas 8 unidades del nivel 1 hay 42
de sus 65 cuentos.**

Intervalos al 95 % por remuestreo (2.000 réplicas, semilla 20260912). La
«longitud» de un bloque es la **natural** de sus cuentos (palabras / cuentos), no
la del bloque, que solo dice cuántos cupieron.

| Nivel del editor | Unidades | Media del v4 (0–2) | IC 95 % | Longitud natural | ρ v4–longitud dentro del nivel |
|---|---|---|---|---|---|
| 1 | 8 | 0,315 | [0,191; 0,453] | 179 | 0,83 (n = 8) |
| 2 | 37 | 0,323 | [0,265; 0,389] | 158 | −0,12 |
| 3 | 32 | 0,405 | [0,361; 0,450] | 297 | 0,19 |
| 4 | 61 | 0,493 | [0,431; 0,557] | 486 | 0,10 |
| 5 | 36 | 0,598 | [0,522; 0,671] | 739 | 0,14 |

| Métrica (174 unidades) | Valor | IC 95 % |
|---|---|---|
| Spearman v4 contra nivel | **0,416** | [0,279; 0,537] |
| Spearman longitud natural contra nivel | **0,810** | — |
| v4 descontando la longitud natural (parcial) | 0,133 | [−0,029; 0,289] |
| Medias crecientes en los remuestreos | **54 %** | — |

Por separado: los textos de 250 palabras o más (123) dan 0,307 [0,130; 0,464] con
medias crecientes solo en el 6,5 % de los remuestreos; los bloques de cuentos
cortos (51) dan 0,205 [−0,071; 0,442], **indistinguible de cero**.

**Sensibilidad sin el filtro de prosa** (la app lo mantiene; esto solo mide su
efecto sobre la validación): el nivel 1 pasa de 8 a 15 unidades y su media **baja**
de 0,315 a 0,291 [0,208; 0,381]; Spearman 0,445 [0,310; 0,561] y medias crecientes
en el **70 %** de los remuestreos. El resto de niveles no cambia.

Los 67 cuentos sin nivel (36 unidades) dan media 0,475, cuartiles 0,27 / 0,44 /
0,60: la misma franja que los niveles 2–4.

### Hallazgos

1. **La longitud predice el nivel de este editor mucho mejor que el v4**, y eso
   dice más del corpus que del modelo: los niveles de African Storybook son casi una
   escala de longitud (0,81). El v4 no ve la longitud —puntúa ventanas fijas de 250
   palabras y promedia— y dentro de cada nivel su correlación con ella es ≈ 0 (de
   −0,12 a 0,19 con *n* suficiente). Ordena los niveles con 0,42 [0,28; 0,54] por
   contenido. Lo que **no** se puede afirmar es que aporte orden *además* de la
   longitud: la parcial (0,133) no es distinguible de cero.
2. **El orden entre los niveles 1 y 2 no está establecido.** Las medias suben en la
   muestra, pero solo en el 54 % de los remuestreos; los niveles 2 → 3 → 4 → 5 sí se
   separan.
3. **El filtro de prosa sesgaba el nivel 1 hacia arriba.** Un cuento de nivel 1 es
   una frase de pocas palabras por página, y unir la página en un párrafo no lo
   convierte en prosa: el filtro rechazó 42 de sus 65 cuentos y dejó pasar los de
   frases más largas. Sin el filtro, el nivel 1 baja por debajo del 2 y el orden
   gana consistencia (70 % de remuestreos).
4. **Todo cae en 0,29–0,60, la franja A2 de la escala del v4** (A1 exige menos de
   0,2). Para cuentos ilustrados infantiles es coherente con la compresión de escala
   ya documentada: un texto A1 tiende a anunciarse A2.

*Revisión metodológica de Fable (12 sep 2026): una versión anterior de esta sección
decía «lo explica sobre todo la longitud», «medias estrictamente crecientes», «el
nivel 1 no se mide por tener pocas palabras» y «franja A1–A2». Las cuatro cosas eran
lecturas equivocadas de cifras correctas; se corrigieron midiendo, y el validador
calcula ahora intervalos, la correlación dentro de cada nivel y la sensibilidad sin
filtro.*

## VOA Learning English (sin nivel por artículo)

Muestra de hasta 60 artículos por sección (477 bajados, 472 con texto). **468 de
470 unidades puntuadas.** Fuga contra ELG: 0.

| Sección | Bajados | Media del v4 (0–2) | Palabras medias |
|---|---|---|---|
| Ask a Teacher | 60 | 0,864 | 428 |
| Education Tips | 58 | 0,905 | 771 |
| Arts & Culture | 60 | 0,961 | 547 |
| Words & Their Stories | 60 | 0,969 | 528 |
| As It Is | 60 | 0,970 | 528 |
| Health & Lifestyle | 59 | 0,986 | 643 |
| American Stories | 60 | 0,987 | 1.395 |
| Science & Technology | 60 | 1,143 | 541 |

| Grupo | Artículos | Media del v4 | ¿Al catálogo? |
|---|---|---|---|
| Escritos por VOA (dominio público) | 261 | 0,930 | Sí |
| Adaptados de AP, Reuters o AFP | 216 | 1,024 | No, internos |

Media global **0,973**, cuartiles 0,82 / 0,97 / 1,11. Letras del v4 sobre los 466
artículos cruzados con su puntuación: B1 250 · B2 184 · A2 18 · C1 14.

### Lo que se observa (descripción, no validación: VOA no trae nivel)

1. **El v4 no confunde el material.** Pone VOA casi todo en B1–B2, por encima de los
   cuentos infantiles de African Storybook y muy por debajo de la literatura de
   Gutenberg (media del catálogo 1,74). Eso descarta un fallo grosero del modelo y
   nada más: son géneros y longitudes distintos, y comparar medias entre fuentes
   no valida el orden.
2. **Diferencias entre secciones** (Ask a Teacher 0,864; Ciencia y Tecnología
   1,143), dadas sin desviación ni intervalo. Con ocho secciones no se puede
   atribuir la causa ni al vocabulario ni a la longitud.
3. **Lo adaptado de agencias puntúa algo más alto** (1,024 contra 0,930), sin
   intervalo y sin controlar la sección: si las agencias se concentran en Ciencia y
   Tecnología, la diferencia puede ser de sección y no de origen.

*Revisión metodológica de Fable (12 sep 2026): una versión anterior de esta
sección decía «tiene sentido empíricamente» y «la longitud no lo explica» con un solo
contraejemplo; se rebajó a descripción.*

## Pendiente

- StoryWeaver: validar sobre la muestra aleatoria e intercalada por niveles que va
  bajando, y sobre el total al terminar.
- VOA: describir por sección y comparar lo escrito por VOA con lo adaptado de agencias.
- Let's Read: localizar un modo de descarga que respete sus condiciones.
