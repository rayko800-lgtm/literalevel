# Encargo: segunda auditoría externa de LiteraLevel

Eres un **auditor externo**. No escribiste nada de esto, no le debes nada a
nadie y no tienes que ser amable. Tu trabajo es comprobar si lo escrito se
sostiene, y decirlo con precisión.

Trabajas en `C:\Users\laura\literalevel`. **No modifiques ningún archivo del
proyecto.** Tu única salida es el informe, en `auditoria/informe_codex_2.md`.

> **No abras `auditoria/informe_codex.md` ni `auditoria/encargo.md`.** Contienen
> el resultado de otra revisión y leerlos te haría buscar lo que otro ya buscó,
> que es justo lo que no quiero. Ve al material y forma tu propio juicio.

## Cómo auditar

Lee primero **`.claude/skills/auditar-proyecto-datos/SKILL.md`**. Ahí está el
método: los seis frentes por orden de daño, el orden en que conviene leer, y el
formato exacto de cada hallazgo. **Síguelo.**

## El listón, que esta vez es más alto

Esta es una segunda pasada sobre un trabajo que ya se ha revisado. Da por hecho
que lo fácil ya se encontró. Por tanto:

1. **Verifica ejecutando, no leyendo.** Si una cifra se puede recalcular,
   recalcúlala. Si una función se puede llamar con un caso límite, llámala.
   `python -X utf8` está disponible; el corpus CLEAR se descarga solo desde
   GitHub. Un hallazgo comprobado con las manos vale por diez sospechas.
2. **Persigue las coherencias entre archivos.** La misma cifra en el documento,
   en el `.tex`, en el cuadernillo, en el README y en el código tiene que ser la
   misma cifra. Los desacuerdos entre entregables son la mina más productiva.
3. **Duda de lo que suena redondo.** Una frase que explica muy bien por qué algo
   está bien merece más escrutinio que una que reconoce un fallo.
4. **Comprueba los arreglos, no solo las afirmaciones.** Si el texto dice que
   algo se corrigió o se midió, ve al código y a los datos y confírmalo. Que una
   corrección esté anunciada no significa que esté hecha, ni que esté completa,
   ni que no haya roto otra cosa.
5. **Busca lo que falta.** El baseline ausente, la limitación no reconocida, el
   caso límite sin prueba, la métrica que convenía y no aparece.
6. **Sé estricto con la gravedad.** No infles: un CRÍTICO que resulta ser MENOR
   te quita autoridad sobre los demás. Pero tampoco rebajes por cortesía.

## Qué auditar

| Archivo | Qué es |
|---|---|
| `entrega/documento.md` | el documento final |
| `entrega/documento.tex` | el mismo documento en LaTeX; **tiene que decir lo mismo** |
| `entrega/estrategia.md` | la estrategia |
| `entrega/notebook_proyecto.py` | el cuaderno (marcas `# %%`) |
| `app/scoring.py` | el código que puntúa: troceado, escala, inferencia |
| `app/ficha.py` | agregación por libro y filtro de capítulos |
| `app/ui.py` | la interfaz: tabla MCER, bandas, modos de análisis |
| `colab_precalculo.py` | el precálculo masivo del catálogo |
| `validar_local.py` | el validador contra textos externos |
| `informe_velocidad.md` | las mediciones de rendimiento |
| `auditoria/medir_fuga_vocabulario.py` | un experimento de fuga de datos |
| `auditoria/medir_recorte_bloques.py` | una medición sobre el recorte de bloques |
| `.claude/skills/modulo-5-literalevel/SKILL.md` | la rúbrica que debe cumplir |

Puedes abrir cualquier otro archivo para verificar algo. Están también
`pruebas_extremas.py`, `README.md`, `AGENTS.md`, `catalogo_recomendaciones.csv`
y `entrega/datos_figuras/*.dat` con los datos de las figuras.

## Preguntas concretas, que no son las únicas

1. **La escala y sus fronteras.** Comprueba que los cortes de banda, las anclas
   MCER y la regla de empates son **los mismos** en `app/scoring.py`, en
   `app/ui.py`, en el documento, en el `.tex`, en la estrategia y en
   `entrega/datos_figuras/escala_cefr.dat`. Prueba los valores exactos de
   frontera, no solo los del medio.
2. **La agregación.** ¿Un mismo libro da el mismo número medido en la app y
   medido por el precálculo del catálogo? Sigue el camino entero.
3. **Fuga de datos.** ¿Alguna variable, lista, umbral o corte se construye
   mirando datos que después sirven para evaluar? Repasa cada paso de
   preprocesamiento, no solo los evidentes.
4. **Los dos corpus.** Hay un corpus CLEAR y otro de documentos anclados a MCER.
   Verifica que ninguna métrica se atribuye al corpus equivocado.
5. **Las cifras de velocidad y de coste.** ¿Salen las divisiones? ¿Las
   extrapolaciones se siguen del cálculo entregado?
6. **Reproducibilidad.** Lee el cuadernillo como si fueras a ejecutarlo en un
   Colab limpio. ¿Qué se rompe?
7. **Lo que se promete y no está**, o al revés: funciones descritas que no
   existen, comportamientos del código que nadie documenta.
8. **Las pruebas.** ¿Comprueban lo que dicen comprobar? ¿Alguna puede pasar sin
   ejercitar nada?

## Reglas

- **En español.**
- **No arregles nada.** Señala; el autor decide.
- **Si algo está bien y podía estar mal, dilo.** Un informe que solo trae
  defectos no deja distinguir lo revisado de lo no revisado.
- **Usa DUDA** cuando no puedas verificarlo. Es una virtud, no una debilidad.
- **No inventes cifras de referencia** ni compares contra un estado del arte que
  no hayas comprobado.
- Termina con un **veredicto de una página**: qué está sólido, qué hay que
  arreglar antes de entregar, y qué es opcional.
