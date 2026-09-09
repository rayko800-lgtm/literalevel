# Encargo 2A: auditoría de coherencia entre entregables

Eres un **auditor externo**. No escribiste nada de esto y no tienes que ser
amable. Trabajas en `C:\Users\laura\literalevel`. **No modifiques ningún
archivo del proyecto.** Tu única salida es `auditoria/informe_codex_2a.md`.

> **No abras `auditoria/informe_codex.md`, `auditoria/encargo.md` ni
> `auditoria/encargo_2.md`.** Contienen otra revisión y leerlos te haría buscar
> lo que otro ya buscó.

## Alcance: SOLO una cosa, y hazla a fondo

Esta pasada tiene **un único objetivo**: encontrar **cifras y afirmaciones que
no coinciden entre sí** dentro del proyecto. Nada más. No audites la
metodología, no juzgues el enfoque, no busques fugas de datos: eso es otra
pasada. Si ves algo de eso, anótalo en una lista al final bajo «fuera de
alcance», en una línea cada uno, y sigue.

**Tienes un presupuesto limitado. Gástalo en comparar, no en leer entero.** Usa
`grep` para localizar cada cifra y compárala entre archivos; no leas los
documentos de principio a fin.

## El método

1. **Haz un inventario de las cifras clave** del proyecto: métricas del modelo,
   tamaños de corpus, particiones, velocidades, costes, umbrales, porcentajes.
2. Para cada una, **búscala en todos los archivos** y comprueba que no cambia.
3. Donde cambie, **decide cuál es la correcta** mirando el código o los datos, y
   dilo.

Los pares que más suelen discrepar:

| Contra | Contra |
|---|---|
| `entrega/documento.md` | `entrega/documento.tex` (deben decir **lo mismo**) |
| el documento | `entrega/notebook_proyecto.py` |
| el documento | `README.md` |
| cualquier texto | el código que lo implementa (`app/`, `colab_precalculo.py`) |
| el texto | `entrega/datos_figuras/*.dat` |

## Cosas concretas que quiero comprobadas

1. **Los cortes de banda y las anclas MCER.** Que el mismo número aparezca en
   `app/scoring.py`, `app/ui.py`, `entrega/documento.md`, `entrega/documento.tex`,
   `entrega/estrategia.md` y `entrega/datos_figuras/escala_cefr.dat`. Prueba los
   valores exactos de frontera y la regla de empates, no solo los del medio.
2. **La fórmula de puntuación** del documento y del `.tex` frente a lo que hace
   `app/scoring.py` paso a paso: troceado, recorte, media, factor de escala.
3. **Las métricas del modelo** (Spearman, exactitud, error ordinal, RMSE,
   Pearson, MAE): que cada una se atribuya al mismo corpus y al mismo tamaño de
   conjunto en todos los sitios donde aparece.
4. **Las velocidades y los costes**: que las divisiones salgan y que las
   extrapolaciones se sigan de las cifras dadas.
5. **Los tamaños**: número de libros del catálogo, extractos del corpus,
   particiones. Que sumen y que no cambien entre secciones.
6. **La agregación por libro**: que la app y `colab_precalculo.py` calculen el
   mismo número para el mismo libro.

## Formato

Cada hallazgo, cinco líneas y nada más:

```
[GRAVEDAD] Título de una línea
Dónde:      archivo:línea (todos los sitios implicados)
Qué dice:   las citas literales que se contradicen
Por qué:    cuál es la correcta y cómo lo sabes
Arreglo:    qué hay que cambiar
```

Gravedad: **CRÍTICO** si una cifra publicada es falsa; **SERIO** si dos
entregables se contradicen; **MENOR** si es formato o redacción; **DUDA** si no
pudiste verificarlo.

## Reglas

- **En español.** Ordena por gravedad.
- **Ni un hallazgo sin ubicación.**
- **Si una cifra la comprobaste y cuadra, dilo** en una lista corta al final.
  Sin eso no se distingue lo revisado de lo no revisado.
- **No arregles nada.** Señala; el autor decide.
- Termina con **media página** de veredicto: qué cifras son de fiar y cuáles no.
