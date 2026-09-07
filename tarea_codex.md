# Tarea para Codex — el audio de pronunciación sale cortado

Trabaja en `C:\Users\laura\literalevel`. Lee **`AGENTS.md`** primero.

**Tus archivos en esta tarea: `app/lexicon.py` y `app/voz.py`.** No toques `app/ui.py` ni `app/catalogo.py`: estoy dentro de ellos ahora mismo.

## El fallo, reproducido por el usuario en un móvil Android

Miguel consultó dos palabras y escuchó el audio generado:

- **«pick on»** → el audio dice solo **«pic»**
- **«fortress»** → el audio dice solo **«fortre»**

Es decir: el mp3 que genera `tts-1` **está truncado**, le falta el final. No es un problema de reproductor: pasa con palabras distintas y siempre corta por el final.

## Por dónde empezar

`_generar_audio_tts` en `app/lexicon.py` (alrededor de la línea 512) y `generar_audio_correcto` en `app/voz.py`. Sospechas que merecen comprobación, en este orden:

1. **Escritura sin cerrar.** Mira cómo se escribe el archivo (`respuesta.write_to_file(...)` o equivalente) y si el contenido está completamente volcado y cerrado antes de que la ruta se devuelva. Si Gradio sirve el archivo mientras todavía se está escribiendo, el navegador recibe un mp3 a medias.
2. **La caché por contenido que puse yo.** `generar_audio_correcto` ahora reutiliza el archivo si ya existe, comprobando solo `os.path.getsize(...) > 0`. **Un archivo a medio escribir tiene tamaño mayor que cero**, así que una vez que se guarda truncado, se sirve truncado para siempre. Ojo también a `_generar_audio_tts` en `lexicon.py`, que cachea la ruta en SQLite.
3. **El texto que se manda.** Comprueba que a la API se le envía la palabra o frase entera, no un fragmento.

Verifica midiendo, no mirando: genera el audio de «fortress» y de «pick on», mira el **tamaño en bytes y la duración real** del mp3, y compáralo con lo que debería durar. Un mp3 de `tts-1` de una palabra ronda los 8 KB; si sale mucho menor, está truncado.

## Qué entregar

1. **El diagnóstico**, dicho con el dato que lo demuestra.
2. **El arreglo**, con la escritura hecha de forma atómica: escribir a un archivo temporal y renombrar al final. Así un corte a media escritura nunca deja un archivo válido a medias en la caché.
3. **Limpiar los que ya estén truncados** en `~/.literalevel/audio/`, o hacer que la caché los detecte y los regenere. Si no, Miguel seguirá oyendo «fortre» aunque el código esté bien.
4. Una prueba que lo cubra, en el estilo de `pruebas_desambiguacion.py`.

## Reglas

- **No cambies ninguna firma pública** sin decirlo en la primera línea del commit.
- La degradación elegante sigue vigente: sin clave ni red, nada puede lanzar excepción.
- `python -X utf8 pruebas_extremas.py` y `python -X utf8 tests_smoke.py` tienen que seguir en verde.
- **Haz commit, no hagas push.** Si tu sandbox no te deja escribir en `.git`, dilo al final y lo commiteo yo.
