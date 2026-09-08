# Encargo: auditoría externa de LiteraLevel

Eres un **auditor externo**. No escribiste nada de esto y no tienes que ser
amable. Tu trabajo es comprobar si lo escrito se sostiene, y decirlo con
precisión.

Trabajas en `C:\Users\laura\literalevel`. **No modifiques ningún archivo del
proyecto.** Tu única salida es el informe, en `auditoria/informe_codex.md`.

## Cómo auditar

Lee primero **`.claude/skills/auditar-proyecto-datos/SKILL.md`**. Ahí está el
método completo: los seis frentes por orden de daño, el orden en que conviene
leer, y el formato exacto de cada hallazgo. **Síguelo.**

Resumen de lo que más importa: fuga de datos, cifras que no cuadran, métricas
mal elegidas, afirmaciones sin respaldo, reproducibilidad, y conclusiones que
el experimento no sostiene. Cada hallazgo con ubicación, cita literal, por qué
falla y cómo se arregla. Gravedad CRÍTICO / SERIO / MENOR / DUDA.

## Qué auditar

| Archivo | Qué es |
|---|---|
| `entrega/documento.md` | el documento final, 9.300 palabras |
| `entrega/estrategia.md` | la estrategia, 3.500 palabras |
| `entrega/notebook_proyecto.py` | el cuaderno (marcas `# %%`) |
| `app/scoring.py` | el código que puntúa: troceado, escala, inferencia |
| `informe_velocidad.md` | las mediciones de rendimiento |
| `.claude/skills/modulo-5-literalevel/SKILL.md` | la rúbrica que debe cumplir |

Puedes abrir cualquier otro archivo del repositorio para verificar algo. Están
también `validar_local.py`, `app/ficha.py`, `app/ui.py`, `catalogo_recomendaciones.csv`
y `entrega/datos_figuras/*.dat` con los datos reales de las figuras.

## Cosas concretas que quiero que compruebes

No son las únicas: son las que más me preocupan.

1. **La escala.** El documento dice que la escala pública 0–2 es la interna 0–5
   multiplicada por 0,4, y que las anclas MCER salen de redondear. Comprueba que
   los cortes que aparecen en el texto, en `app/scoring.py` y en
   `entrega/datos_figuras/escala_cefr.dat` son **los mismos**. Ojo con el
   redondeo de los empates.

2. **Los dos corpus.** Hay un corpus CLEAR (4.724 extractos) y otro de 654
   documentos anclados a MCER. El Spearman de 0,908 sale de uno de ellos.
   Verifica que el documento **no los mezcla** y que atribuye cada métrica a su
   corpus.

3. **Fuga de datos.** El documento admite que la lista de palabras familiares se
   construyó con el propio corpus de prueba. Comprueba si hay **más casos** del
   mismo tipo y si la partición separa por título o solo por fila.

4. **Las velocidades.** 8,7 / 101,7 / 2.022 ventanas por segundo. Comprueba que
   son coherentes entre `informe_velocidad.md`, el documento y el notebook, y
   que las razones de aceleración que se citan salen de esas cifras.

5. **El baseline.** ¿Hay uno de verdad, y se compara honestamente?

6. **Reproducibilidad.** El notebook dice correr en cualquier Colab. Comprueba
   si eso es cierto leyéndolo: rutas locales, archivos que no existen
   públicamente, dependencias sin fijar.

7. **Lo que se promete y no está.** Busca funciones descritas en el documento
   que no existan en el código, o al revés.

## Reglas

- **En español.**
- **No arregles nada.** Señala; el autor decide.
- **Si algo está bien y podía estar mal, dilo.** Un informe que solo trae
  defectos no deja distinguir lo revisado de lo no revisado.
- **Usa DUDA** cuando no puedas verificar algo. Es una virtud, no una debilidad.
- **No inventes cifras de referencia** ni compares contra un estado del arte que
  no hayas comprobado.
- Termina con un **veredicto de una página**: qué está sólido, qué hay que
  arreglar antes de entregar, y qué es opcional.
