# La medición del catálogo, jueves 10 de septiembre de 2026

Tanda en Colab con **T4 gratuita**, cuenta `rayko800@gmail.com`. Todo lo de aquí
está impreso por el cuaderno, no estimado.

---

## Lo que salió

| | |
|---|---|
| Libros con perfil medido por el v4 | **29.875** |
| Líneas en los shards / libros distintos | 29.875 / 29.875 — **sin duplicados** |
| Pendientes al empezar la tanda | 2.099 |
| La tanda | 2.099 libros en **2,1 min, 0 errores** |
| Salida | `literalevel_bigdata/catalogo_medido.csv` (en Drive) |

Lo que se creía «catálogo sin medir» era en realidad **catálogo sin descargar**:
casi 30.000 de los 31.974 textos que hay en Drive ya tenían perfil de tandas
anteriores, y el cuaderno los descuenta solo.

## La velocidad, y una cifra que NO hay que publicar

La tanda dio **16,7 libros/s**, que son 1.002 libros/min. **Esa cifra es
engañosa y no debe salir en ningún entregable.** La T4 hace 492 ventanas/s
medidas, así que 16,7 libros/s implica **29 ventanas por libro** —unas 7.000
palabras—: los 2.099 que quedaban eran **los pequeños**, no una muestra del
catálogo.

La cifra honesta, para un libro típico de 350 ventanas:

| | libros/min | de dónde sale |
|---|---|---|
| **T4 gratis, con prefetch** | **84** | 492 v/s ÷ 350 ventanas |
| A100 de pago, sin prefetch | 61 | lo medido y publicado hasta hoy |

**La tarjeta gratis con el prefetch va más rápido que la de pago sin él.** El
cuello de botella nunca fue la GPU —en la A100 estaba parada el 80 % del tiempo
esperando a Drive— y el prefetch lo tapó. Con eso, el catálogo entero son unas
**12 h de T4 gratis**, reanudables, en vez de las 15 unidades de pago que
proyectaba el documento. **Esas 15 unidades ya no hacen falta para nada.**

---

## El hallazgo que hay que decidir, y NO antes del vídeo

`describe()` sobre la dificultad de los 29.875:

```
count    29875.000000
mean         1.745611
std          0.203034
min          0.270000
25%          1.664000
50%          1.795000
75%          1.888000
max          2.000000
```

En la escala pública 0..2, con los anclajes del MCER (A1 0 · A2 0,4 · B1 0,8 ·
B2 1,2 · C1 1,6 · C2 2,0), eso dice que **al menos tres cuartas partes del
corpus de Gutenberg puntúan C1 o por encima**, y la mediana (1,795) cae entre C1
y C2.

**Y el catálogo que usa la app dice lo contrario.** Sus 1.197 libros llevan
etiqueta del **modelo v1** aplicado a las primeras ~190 palabras con cortes por
cuantiles:

| | A1 | A2 | B1 | B2 | C1 | C2 |
|---|---|---|---|---|---|---|
| Etiquetas v1 (1.197 libros) | **60,4 %** | 15,5 % | 5,8 % | 4,3 % | 4,4 % | 9,6 % |
| v4 medido (29.875 libros) | — | — | — | — | ≥ 75 % en C1–C2 | |

No son el mismo conjunto —1.197 curados contra 29.875—, así que la comparación
es de dirección, no de celda a celda. Pero la dirección es inequívoca y
**confirma con 29.875 mediciones una limitación que el documento ya declaraba**:
que la correspondencia de las etiquetas v1 no se sostiene.

### Por qué el v4 no está necesariamente equivocado

Sus propias medias en los 47 textos graduados de la validación son 0,504 (A1) ·
0,556 (A2) · 0,928 (B1) · 1,241 (B2) · **1,495 (C1)**. O sea: un texto graduado
de nivel C1 puntúa 1,50, y la literatura de Gutenberg promedia **1,75**. Que la
literatura del XIX sea más dura que una lectura graduada de C1 no es un fallo
del modelo: es lo esperable.

Lo que sí habría que revisar es **qué le ofrece la app a un lector de B1** si el
catálogo medido resulta ser casi todo C1–C2.

### Qué NO hacer ahora

**No cambiar el catálogo de la app antes del vídeo.** La app usa
`catalogo_recomendaciones.csv` con las etiquetas v1 y no se ha tocado: cambiarlo
a dos días de grabar es meter una variable enorme en la demo sin tiempo de
probarla. Esto es material para el documento —una limitación medida, que es
mejor defensa que una limitación declarada— y una decisión para después.

---

## Lo que de verdad falta

| | |
|---|---|
| Libros en inglés del catálogo oficial | 61.642 |
| Descargados a Drive | ~31.974 |
| **Con perfil medido** | **29.875** |
| **Por descargar** | **~29.700** |

Y **descargar no necesita GPU ni unidades**: la celda 6c baja los textos de los
shards de `common-pile/project_gutenberg` en Hugging Face. Se puede dejar
corriendo en un entorno de CPU gratuito.
