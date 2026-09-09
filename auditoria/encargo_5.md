# Encargo 5 para Astra — dos archivos, nada más

Auditoría externa de LiteraLevel, proyecto de titulación de un diplomado de
ciencia de datos. Se entrega a un profesor universitario.

**Este encargo es deliberadamente estrecho.** Los tres encargos amplios
anteriores se quedaron sin contexto antes de escribir una sola línea de
informe. Aquí hay **dos archivos** y dos preguntas. No amplíes el alcance.

---

## Reglas de trabajo, que importan tanto como el encargo

- **No abras el resto de `auditoria/`.** Ni los informes de Fable, ni los
  encargos anteriores, ni `cierre_2026-09-09.md`. Son cientos de páginas y te
  vas a quedar sin contexto. El único archivo de esa carpeta que entra en el
  encargo es `estado_real.md`.
- **Usa `grep` antes que leer entero.** `entrega/documento.md` son 1.200
  líneas: no lo leas de arriba abajo, busca en él la cifra que quieres
  comprobar. `rg -n "0,855" entrega/documento.md` te da la respuesta en una
  línea.
- **Escribe el informe en cuanto tengas material sólido**, no al final. Si te
  quedas sin contexto a mitad, más vale un informe de cinco hallazgos
  comprobados que ninguno.
- Cita **archivo y línea** en cada hallazgo. Nada de «parece que».
- **No modifiques ningún archivo del proyecto.** Tu única escritura es
  `auditoria/informe_codex_5.md`.

---

## Parte A — `entrega/presentacion.tex` contra `entrega/documento.md`

La presentación son 12 diapositivas y es lo que se proyecta el día de la
defensa. El documento es la fuente de verdad. Dos preguntas:

**A1. ¿Coincide cada cifra?** Saca todos los números de `presentacion.tex` y
comprueba uno por uno que el documento dice lo mismo. Los que más importan,
porque cambiaron hoy:

| En la presentación | Debería decir |
|---|---|
| Spearman del modelo | 0,855 |
| contar palabras | 0,799 |
| correlación parcial | 0,665 |
| textos de validación externa | 46 |
| coste del despliegue | 7 USD/mes |

Si encuentras 0,854, 0,807, 0,657 o 45, es un residuo y es un hallazgo.
Comprueba también las que no están en esa tabla: 0,908, 97,2 %, 61.642, 328 MB,
las horas de A100, el número de pruebas.

**A2. ¿Hay alguna afirmación más fuerte que la del documento?** Una
presentación tiende a redondear y a quitar salvedades por espacio, y ahí es
donde se cuela lo que un profesor pregunta. Busca:

- cifras que el documento presenta con una salvedad («no está medido», «no es
  comparación cara a cara», «orden de magnitud») y que la diapositiva da
  desnudas;
- comparaciones con la competencia que suenen a victoria medida cuando el
  documento dice explícitamente que no lo son;
- promesas al usuario que el documento no sostiene;
- el estado del despliegue y del catálogo: el documento dice que la remedición
  del catálogo **está en curso** y que las etiquetas de hoy son heredadas de un
  modelo v1.

---

## Parte B — `auditoria/estado_real.md`, qué sigue abierto

Ese archivo es un inventario de hallazgos de auditorías anteriores, con un
veredicto por hallazgo. **Se escribió hace dos días y desde entonces se han
cerrado muchos**, así que está desactualizado y no sabemos cuánto.

Coge **solo los que marca como `ABIERTO` o `CERRADO A MEDIAS`** —los que ya
dice `CERRADO`, `FALSO` o `NO VERIFICABLE` no entran— y para cada uno ve al
archivo y a la línea de hoy. Los números de línea que cita ya no valen: los
archivos han crecido. Busca por el texto.

Devuelve una tabla con una fila por hallazgo:

| # | Hallazgo | Veredicto HOY | Dónde y cita |
|---|---|---|---|

Veredictos posibles: **SIGUE ABIERTO** · **YA CERRADO** · **CERRADO A MEDIAS**
· **FALSO** (el hallazgo nunca fue cierto) · **NO VERIFICABLE**.

Si te quedas sin contexto antes de terminar la lista, **escribe lo que lleves
y dilo**: «verificados los N primeros, el resto sin revisar» es un resultado
útil. Un inventario a medias con veredictos ciertos vale más que uno completo
con veredictos inventados.

---

## Contexto mínimo que necesitas y no vas a deducir

- La escala pública es **0–2**; la interna del modelo, 0–5. `público = interno × 0,4`.
- Las bandas se derivan del ancla MCER, con fronteras equivalentes en **0,6 y
  1,4**. Los cortes viejos eran 0,8 y 1,6 y están retirados a propósito.
- La validación externa son **46 textos** de British Council. Era 45 hasta esta
  mañana: un archivo se caía por un fallo de expresión regular.
- El despliegue está **hecho**: `MikeMaki1763/literalevel` en Hugging Face
  Spaces, público y corriendo. Cuesta **7 USD/mes** (cuenta Pro con descuento;
  la tarifa es 9). No es gratuito, aunque el hardware sea `cpu-basic`.
- El catálogo **no está terminado**: 4.522 libros medidos de 61.642 a día de
  hoy. Cualquier afirmación en presente sobre «el catálogo medido» es un
  hallazgo.

---

## Salida

`auditoria/informe_codex_5.md`, con:

1. Recuento por gravedad al principio: CRÍTICO · SERIO · MENOR.
2. Parte A: los hallazgos de la presentación, con archivo y línea.
3. Parte B: la tabla del inventario.
4. Una sección de «lo que está bien y podía estar mal», para que se sepa qué
   comprobaste y salió limpio.

No inventes hallazgos para llenar el informe. Si la presentación está bien,
dilo: es un resultado.
