# Tarea para Codex — desambiguación de acepciones en `lexicon.py`

Trabaja en `C:\Users\laura\literalevel`. **Lee `AGENTS.md` primero**: lleva el reparto de archivos entre tú y Claude Code, el contrato entre módulos y las trampas del repo.

## El fallo, con su caso reproducible

`ConsultorLexico.consultar` elige mal el sentido de **"peeped"** en la oración de *Alice's Adventures in Wonderland*:

> *"once or twice she had peeped into the book her sister was reading"*

Se queda con la glosa **"To speak briefly with a quiet voice"** (afinidad **0.23** entre 6 acepciones) en lugar del sentido de *mirar de reojo*. La explicación de OpenAI lo desmiente sola: *"la definición dada es otro sentido de peep y no aplica aquí"*.

Reprodúcelo antes de tocar nada:

```bash
python -X utf8 -c "import sys; sys.path.insert(0,'app'); from lexicon import ConsultorLexico; r = ConsultorLexico().consultar('peeped', 'Once or twice she had peeped into the book her sister was reading.', 1.0); print(r.sentido, r.similitud, r.n_sentidos_candidatos)"
```

## Diagnóstico de partida

`_elegir_sentido` compara por coseno la oración contra cada glosa con `all-MiniLM-L6-v2`. Las glosas de Wiktionary son de pocas palabras, así que la señal es escasa y con 6 candidatos la elección se acerca al azar. Dos vías, evalúalas tú:

1. Enriquecer el texto que se compara: `glosa + etiquetas + ejemplos` en vez de solo la glosa.
2. Exigir un margen mínimo entre el primer y el segundo candidato; si no lo hay, dejarlo explícito en lugar de dar uno por bueno.

## Restricciones, no negociables

- **No toques `app/ui.py`.** Es de Claude Code.
- **`consultar()` ya recibe `idioma` ('es'/'en')**, que entra en la clave de caché. No lo rompas.
- **Si cambias una firma pública, dilo en la primera línea del commit.** `ui.py` depende de siete módulos y se rompe en silencio.
- La regla de degradación elegante sigue vigente: sin `OPENAI_API_KEY` ni red, `consultar()` **nunca** lanza excepción; lo que falte va en `.avisos`.
- `ui.py` avisa cuando la afinidad baja de 0.35 (`AFINIDAD_DUDOSA`). Si tu arreglo cambia la escala de `similitud`, **dilo en el commit** para que se ajuste ese umbral.

## Qué entregar

1. El arreglo en `app/lexicon.py`.
2. Prueba de que "peeped" ahora elige un sentido de *mirar*, y de que no has empeorado los casos que ya funcionaban: **"brook"** (sustantivo vs verbo según la oración), **"set off"** (phrasal verb) y **"notwithstanding"** (spaCy la etiqueta ADP, cae fuera del mapa POS y debe usar todos los sentidos). `pruebas_lexicon.py` los cubre: ejecútalo.
3. `python -X utf8 pruebas_extremas.py` tiene que seguir dando **75 pruebas OK**. Es de Claude Code y prueba la interfaz; si algo ahí se rompe, tu cambio rompió el contrato.
4. **Haz commit, pero no hagas push.** Lo revisamos antes de subirlo.

Si concluyes que no se puede arreglar bien sin rehacer algo mayor, dilo claramente en vez de forzar un apaño: es información útil.
