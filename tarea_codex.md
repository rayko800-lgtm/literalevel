# Tarea para Codex — afinar el cuestionario de nivel

Trabaja en `C:\Users\laura\literalevel`. Lee **`AGENTS.md`** primero.

**Tu archivo: `app/perfil.py`** (y `pruebas_perfil.py`). No toques `app/ui.py`: estoy dentro. El cableado de la interfaz lo hago yo con lo que dejes.

## El contexto

El cuestionario que hiciste **gustó mucho**. Miguel lo probó y dice: *«mejoró el cuestionario, me gustó muchísimo más»*. Ahora pide dos cosas concretas.

## 1. Los fragmentos: tres opciones son muy pocas

Hoy cada fragmento ofrece *«Lo entiendo todo» / «Capto la idea, pero se me escapan palabras» / «Me pierdo»*. Miguel: *«se me hace muy poquito, a lo mejor podríamos poner más opciones»*.

Sube a **cinco escalones** por fragmento, con el salto entre ellos bien pensado. Algo en la línea de: lo entiendo sin esfuerzo / lo entiendo pero releo alguna frase / capto la idea y se me escapan palabras sueltas / entiendo a medias, necesitaría diccionario / me pierdo. **Redáctalo tú**: lo importante es que cada escalón describa una experiencia distinta y reconocible, no que sean cinco sinónimos.

Reajusta los valores en la escala 0..2 para que la escalera siga teniendo sentido con el nivel CEFR de cada fragmento, y explica el criterio en un comentario.

## 2. Selección múltiple donde tenga sentido

Miguel: *«me gustaría también que pudiésemos seleccionar más de una opción, en algunos casos»*.

Decide **tú** en qué preguntas encaja y en cuáles no, y justifícalo. Mi lectura, discútela si no la compartes: «¿qué sueles leer en inglés?» admite varias respuestas de forma natural —alguien lee noticias **y** novelas—, y ahí el nivel razonable es **el más alto marcado**, no la media, porque quien lee literatura clásica también lee menús. En cambio «¿con qué frecuencia lees?» es excluyente por definición y debe seguir siendo de una sola opción.

Para las de selección múltiple, la estructura tiene que indicar que lo son, para que la interfaz pueda pintar un control distinto. Añade una marca clara al formato de `PREGUNTAS` (por ejemplo un cuarto elemento, o una clave `multiple`), **y dime en el commit exactamente qué forma tiene**, porque `ui.py` la recorre y tengo que adaptarme.

## Lo que no se puede romper

- `desde_cuestionario(respuestas: dict, nombre="") -> Perfil` mantiene su firma. Ahora algunos valores del dict pueden ser **listas** en vez de números: trátalo.
- Escala pública 0..2, y `PESO_FRAGMENTOS` sigue mandando sobre las opiniones.
- Responder solo algunas preguntas debe seguir funcionando.
- `python -X utf8 pruebas_extremas.py` → **124 OK**; `python -X utf8 tests_smoke.py` → **TODO OK**; `python -X utf8 pruebas_perfil.py` → verde. Amplía esta última con los casos nuevos: selección múltiple vacía, con una, con varias, y los extremos de los cinco escalones.
- **Haz commit, no hagas push.** Si tu sandbox no te deja escribir en `.git`, dilo y lo commiteo yo.

Si algo de esto te parece mala idea, dilo en vez de hacerlo a regañadientes.
