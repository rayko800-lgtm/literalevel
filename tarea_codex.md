# Tarea para Codex — rehacer el cuestionario de nivel

Trabaja en `C:\Users\laura\literalevel`. Lee **`AGENTS.md`** primero: reparto de archivos, contrato entre módulos y trampas del repo.

**Tu archivo en esta tarea es `app/perfil.py`.** No toques `app/ui.py` — la interfaz la cableo yo con lo que dejes. Avisa en la primera línea del commit si cambias alguna firma.

## El problema, en palabras del usuario

Miguel probó la app y dijo del cuestionario: *«se me hizo muy básico»*, *«para niveles avanzados sí es rápido… pero alguien que no sabe gramática no entiende eso»*. Quiere algo **más completo y más amigable**, y sugiere **poner fragmentos: "lee esto y dime cuánto entiendes, sé sincero"**.

Mira `PREGUNTAS` en `app/perfil.py`. Son tres. La tercera dice literalmente *«¿Y las frases largas con varias subordinadas?»* — y ese es el fallo: **un lector normal no sabe qué es una subordinada**. Es un usuario final, no un lingüista.

## Lo que no se puede romper

- El resultado es un número en la **escala pública 0..2**: básico <0.8, intermedio <1.6, avanzado. Anclajes CEFR: A1=0.0, A2=0.4, B1=0.8, B2=1.2, C1=1.6, C2=2.0.
- `desde_cuestionario(respuestas: dict, nombre="") -> Perfil` **tiene que seguir existiendo y aceptando el mismo tipo de entrada** (clave de pregunta → valor). `ui.py` la llama así, y también `pruebas_extremas.py`.
- Todo lo que ve el usuario, en **español**. Los fragmentos de lectura, en inglés.
- `perfil.py` **no puede llamarse `profile.py`** ni importar nada nuevo pesado: se carga al arrancar la app.

## Qué hay que dejar hecho, en `app/perfil.py`

**1. De 5 a 7 preguntas de opinión**, sin jerga gramatical. Nada de «subordinadas», «cláusulas» ni «tiempos verbales». Pregunta por hechos observables: qué lee y con qué frecuencia, si necesita diccionario, si ve series en inglés sin subtítulos, si ha terminado un libro entero en inglés. Cada una con 4-5 opciones y su valor en la escala 0..2, razonado en un comentario.

**2. Tres o cuatro fragmentos reales de lectura**, en una estructura nueva y exportada (por ejemplo `FRAGMENTOS`), con dificultad escalonada: uno fácil de verdad (A2/B1), uno medio (B2), uno difícil (C1/C2). Cada uno con:
- el texto exacto, **40-70 palabras**, entendible sin contexto previo
- obra y autor, **de dominio público** (Project Gutenberg). No inventes citas ni las atribuyas mal
- su nivel CEFR
- la pregunta de autoevaluación y sus opciones con valor: *«lo entiendo todo» / «capto la idea, se me escapan palabras» / «me pierdo»*

**3. Cómo se combinan** opinión y fragmentos. Mi opinión, discútela si no la compartes: **los fragmentos deberían pesar más**, porque delante de un texto real la gente se autoevalúa mejor que describiéndose. Deja el peso en una constante con nombre.

**4. Que `desde_cuestionario` siga funcionando** aunque solo se respondan algunas preguntas, como ahora.

## Cómo entregarlo

- Comenta el porqué de las decisiones, en el estilo del resto del repo: qué problema resuelve cada cosa, no qué hace cada línea.
- `python -X utf8 pruebas_extremas.py` tiene que seguir dando **118 OK** y `python -X utf8 tests_smoke.py` **TODO OK**. Si algo se rompe ahí, tu cambio rompió el contrato.
- Añade una prueba tuya que compruebe que las combinaciones extremas dan lo esperado: todo lo más fácil → cerca de 0, todo lo más difícil → cerca de 2.
- **Haz commit, no hagas push.** Lo reviso antes de subirlo.

Si algo de esto te parece mala idea, dilo en el commit en vez de hacerlo a regañadientes.
