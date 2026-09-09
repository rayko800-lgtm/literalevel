# Encargo: auditoría de la estrategia y del cuadernillo

Eres un **auditor externo**. No escribiste nada de esto y no tienes que ser
amable. Trabajas en `C:\Users\laura\literalevel`. **No modifiques ningún
archivo del proyecto.** Tu única salida es `auditoria/informe_codex_4.md`.

> **No abras nada dentro de `auditoria/`** salvo para escribir tu informe. Ahí
> hay revisiones ajenas; leerlas te haría buscar lo que otro ya buscó.

## Alcance: DOS archivos. Nada más.

- **`entrega/estrategia.md`** — entero.
- **`entrega/notebook_proyecto.py`** — solo sus **celdas de texto** (las que
  empiezan por `# %% [markdown]`), es decir, lo que el lector lee. El código
  puedes abrirlo para verificar una afirmación, pero no lo audites por sí mismo.

Esto es deliberado y va en serio: tres encargos anteriores con alcance amplio
**se quedaron sin presupuesto en la fase de lectura y no llegaron a escribir ni
una línea de informe**. El que sí entregó fue el más estrecho.

`entrega/documento.md` **ya se auditó y no toca ahora**. Si ves algo ahí,
anótalo al final en una línea bajo «fuera de alcance» y sigue.

## Por qué estos dos archivos

La estrategia vale 15 puntos de la rúbrica y **nadie la ha auditado todavía**.
Acaba de añadírsele un apartado nuevo, el 5, sobre la competencia, con cifras
tomadas de fuentes externas. El cuadernillo vale otros 15 y solo se ha revisado
su código, no lo que afirma en sus celdas de texto.

## Cómo gastar el presupuesto

1. **Empieza por el apartado 5 de la estrategia** («Contra quién compite esto»),
   que es lo más nuevo y lo menos revisado.
2. Sigue por los **accionables**, las **métricas de éxito** y los **riesgos**:
   ahí es donde una estrategia suele prometer lo que no puede cumplir.
3. Termina con las celdas de texto del cuadernillo.
4. **Usa `grep` para localizar**, no leas los archivos enteros de un tirón.
5. **Escribe el informe en cuanto tengas material sólido.**

## Qué buscar

1. **Cifras sin respaldo.** El apartado 5 cita precios de licencias, valores de
   correlación de la literatura y comparaciones con productos comerciales.
   ¿Están respaldadas por algo dentro del repositorio, o son afirmaciones al
   aire? Hay un informe de investigación en `investigacion/competencia.md`:
   comprueba si la estrategia dice lo mismo que él.
2. **Afirmaciones más fuertes que su evidencia**: «el único», «nadie hace»,
   «ganamos», «basta», «demuestra». Cada una merece que se compruebe qué la
   respalda.
3. **Accionables que no son accionables**: sin coste, sin criterio de terminado,
   o cuyo criterio no se puede comprobar.
4. **Métricas de éxito que no se pueden medir** con lo que el proyecto tiene.
5. **Riesgos que faltan.** Un apartado de riesgos que no menciona el riesgo
   evidente está incompleto.
6. **Contradicciones entre la estrategia y el documento** en cifras o
   afirmaciones. Los dos tienen que decir lo mismo.
7. En el cuadernillo: **celdas de texto que prometen lo que el código de al lado
   no hace**, o que interpretan un resultado más allá de lo que da.

## Formato

```
[GRAVEDAD] Título de una línea
Dónde:      archivo:línea
Qué dice:   la cita literal
Por qué:    en qué falla, con el número o la regla concreta
Arreglo:    qué hay que cambiar
```

Gravedad **CRÍTICO / SERIO / MENOR / DUDA**, y sé estricto.

## Reglas

- **En español.** Ordena por gravedad.
- **Ni un hallazgo sin ubicación ni sin cita.**
- **Verifica antes de afirmar.** Recalcula lo que se pueda recalcular.
- **Si algo lo comprobaste y se sostiene, dilo** en una lista corta al final.
- **Usa DUDA** cuando no puedas verificarlo desde el repositorio.
- **No arregles nada.** Señala; el autor decide.
- Termina con **media página** de veredicto sobre si la estrategia y el
  cuadernillo están listos para entregarse.
