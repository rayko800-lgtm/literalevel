# Encargo 6 para Astra — el corpus externo y lo que se deriva de él

Auditoría externa de LiteraLevel, trabajo de titulación de un diplomado de
ciencia de datos que se entrega a un profesor universitario. Rigor máximo.

**Alcance estrecho a propósito.** Los encargos amplios se quedaron sin contexto
tres veces sin escribir una línea. Aquí hay **un tema** y tres preguntas.

---

## Reglas

- **`grep` antes que leer.** `entrega/documento.md` son 1.300 líneas.
- **No abras los informes anteriores de `auditoria/`.** Solo este encargo.
- **No modifiques ningún archivo del proyecto.** Tu única escritura es
  `auditoria/informe_codex_6.md`.
- **Ejecuta.** Tienes permiso para correr `python -X utf8 validar_local.py` y
  cualquier `python -c` que necesites. Una cifra comprobada vale por diez
  leídas.
- Escribe el informe en cuanto tengas material sólido, no al final.
- Archivo y línea en cada hallazgo. Nada de «parece que».

---

## El tema: el corpus externo de British Council

Hoy ha cambiado dos veces y las dos por el mismo motivo — un patrón que solo
contemplaba una forma de escribir un nombre:

1. Por la mañana: el regex del nivel usaba `\b`, que no corta contra un guion
   bajo, y perdía `B2__LearnEnglish-Reading-B2_Work-life-balance.pdf`. De 45
   textos se pasó a 46.
2. Por la tarde: el `glob` decía `*LearnEnglish-Reading*.pdf` y no veía
   `A2__LearnEnglish_Reading-A2-An-email-from-a-friend.pdf`, con guion bajo. De
   46 se pasó a **47**, y con él cambiaron A2 (n=8, media 0,5561), el Cuadro 12
   (0,860 / 0,807 / 0,668), el modelo-contra-longitud (0,732) y el recuento del
   filtro estricto (31).

---

## A. ¿Falta algún archivo más, o sobra alguno?

Ve a `C:\Users\laura\Downloads` y **cuenta tú mismo**, sin fiarte del patrón
que usa el proyecto. Los PDF del corpus siguen la forma
`NIVEL__LearnEnglish?Reading-...pdf`, pero ya se ha visto que las variantes
existen. Preguntas concretas:

- ¿Cuántos PDF hay que sean de este corpus, por cualquier criterio razonable
  (nombre, contenido, fecha de descarga)?
- ¿Los ve todos el patrón actual de `validar_local.py`? ¿Y el de
  `entrega/manifiesto_corpus_externo.md`?
- ¿Coincide el manifiesto, archivo por archivo, con lo que hay en el disco?
  ¿Y los recuentos por nivel?
- ¿Hay algún PDF con el nivel escrito de otra forma —minúsculas, sin guion,
  con espacio— que ambos patrones estén perdiendo?

## B. ¿Cuadra la aritmética de las exclusiones?

El documento publica: **59 − 2 sin cuerpo − 10 rechazados = 47**. Ejecuta
`validar_local.py` y comprueba que esos tres números salen, y que los 10
rechazados son los que el documento dice (nueve A1 y un B1, todos por quedarse
bajo las 150 palabras). Si alguno cae por otra regla, es un hallazgo.

Comprueba además el otro recuento que el guion imprime: **31 textos** pasarían
el filtro completo, el que aplica la aplicación. ¿Sale?

## C. ¿Está el 47 en todas partes, y en todas sus formas?

La cifra vive en muchos sitios y hoy se ha escapado cuatro veces por estar
escrita distinto. Busca **47, 46 y 45** —y sus derivadas: las medias por nivel,
el `n` de A2, el Cuadro 12— en:

`entrega/documento.md`, `entrega/documento.tex`,
`entrega/datos_figuras/validacion.dat`, las etiquetas escritas **a mano dentro
del TikZ** de la figura de validación, `entrega/estrategia.md`,
`entrega/presentacion.tex`, `entrega/notebook_proyecto.py`, `README.md`,
`PENDIENTES.md`, `modelo_v4/README.md` y `arrancar_gpu.py`.

Y **extrae el texto de `entrega/documento.pdf` y `entrega/presentacion.pdf`**
con `pypdf`: si el `.tex` está bien pero el PDF no se recompiló, el fallo es
real, porque el PDF es el entregable.

---

## Contexto mínimo que no vas a deducir

- Escala pública 0–2, interna 0–5, pública = interna × 0,4.
- Las medias vigentes: A1 0,5040 (n=3) · A2 0,5561 (n=8) · B1 0,9276 (n=12) ·
  B2 1,2414 (n=12) · C1 1,4952 (n=12).
- Los 38 textos que aparecen en algunos sitios son **otra tanda**, la de Colab.
  No se convierten en 47.
- `validar_local.py` une las líneas del PDF con espacio a propósito, y eso hace
  su filtro más flojo que el de la aplicación. Está declarado en el documento.

---

## Salida

`auditoria/informe_codex_6.md`, con recuento por gravedad al principio
(CRÍTICO · SERIO · MENOR), un apartado por cada pregunta y una sección final de
«lo que comprobé y salió limpio». Si el corpus está bien, dilo: es un
resultado, y es el que esperamos.
