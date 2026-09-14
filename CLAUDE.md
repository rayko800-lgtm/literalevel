# LiteraLevel

**Lee `AGENTS.md` antes de tocar código.** Contiene el reparto de archivos entre
Claude Code y Codex (aquí trabajan los dos a la vez), el contrato entre módulos
y lo que no se toca. Esto es solo el resumen.

**Relevo del 13 sep por la noche:** antes de retomar portadas, Blender o las
auditorias de `[Central]`, lee `auditoria/relevo_codex_2026-09-13_noche.md`.
Contiene el reparto, commits locales, pruebas y pendientes; no supone permiso
para gastar en Colab ni publicar.

- El modelo v4 es **final**, no se reentrena. La fase actual es la interfaz.
- `app/ui.py` es de Claude Code. `reader.py`, `lexicon.py` y `voz.py` los está
  auditando Codex: no los edites sin avisarlo en el commit.
- Escala pública 0..2 en todas las fronteras entre módulos; la interna 0..5 no
  sale de `scoring.py`.
- Nada de Oxford Dictionaries: el diccionario es Kaikki/Wiktionary en SQLite
  local. OpenAI explica el contexto y traduce, y nunca redefine una palabra que
  el diccionario trae. Si no la trae, la define y la interfaz la marca como
  «generada por IA» (decisión de Miguel, 13 sep 2026).
- Sin `OPENAI_API_KEY` la app tiene que seguir funcionando en todo lo que no
  usa red. Si un cambio rompe eso, está mal.
- `python -X utf8 app/ui.py` para arrancar. Los `.py` de la raíz que empiezan
  por `pruebas_` o `tests_` son las pruebas.
