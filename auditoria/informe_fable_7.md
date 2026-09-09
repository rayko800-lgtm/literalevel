# Informe Fable 7

Fecha: 9 de septiembre de 2026. Último commit observado: `dfd8cb2`. Alcance: los cuatro commits `bbbb04e..dfd8cb2`, los seis archivos de entrega y las cifras nuevas de hoy. No se repite el inventario. Única escritura: este archivo.

**Recuento: CRÍTICO 0 · SERIO 5 · MENOR 8.**

Todo lo que se ejecutó y lo que salió:

| Comprobación | Resultado |
|---|---|
| `python -X utf8 validar_local.py` | 46 textos, medias A1 0,5040 · A2 0,5480 · B1 0,9276 · B2 1,2414 · C1 1,4952, orden creciente; «pasarían el filtro COMPLETO: 30»; 10 rechazados por «muy corto» (9 A1 + 1 B1) |
| Recuento propio por nivel con `cuerpo` y `cuerpo_estricto` + `continuous_prose` | con espacio A1 3 · A2 7 · B1 12 · B2 12 · C1 12 = 46; con saltos A1 **1** · A2 3 · B1 6 · B2 10 · C1 10 = **30**. Los 16 que caen de más caen todos por `maquetado_de_lista` |
| Mínimos cuadrados sobre las 4 medias de Colab (x = 0,4…1,6) | pendiente 0,7196, ordenada 0,3760 → **0,72x + 0,38** correcto |
| Mínimos cuadrados sobre las 5 medias locales (x = 0…1,6) | 0,6690, 0,4081 → **0,67x + 0,41** correcto |
| `python -c "import gradio; gradio.__version__"` | **6.26.0**; el Space declara `sdk_version: 6.26.0` |
| `python -X utf8 pruebas_extremas.py` | «Las 205 pruebas extremas pasan» |
| API de Hugging Face, Space `MikeMaki1763/literalevel` | `hardware: cpu-basic`, `gcTimeout: 172800`, `stage: RUNNING`; coincide con documento.md:1092-1095 |
| API de Hugging Face, modelo `literalevel-v4` | `model.safetensors` 328.489.204 bytes = 328 MB; público |
| `notebook_proyecto.py:1701` y `.ipynb` | `n = [3, 7, 12, 12, 12]` suma 46 en los dos |
| `presentacion.pdf` (texto extraído) | contiene «Recorrido de ejemplo», «estimadas», «cuestionario», «En curso», «Esmeralda», «1,241»; no contiene «1,248» |
| `documento.pdf` (texto extraído) | contiene los párrafos nuevos (30/46, 0,67x, 60.000, «46 en local»); no contiene «45 en local» |
| Numeración de cuadros en `documento.md` | pies 1…16 en orden, cada referencia apunta a un cuadro existente; en el `.tex` todo `\ref{cuad:*}` tiene su `\label` |
| Párrafos duplicados (líneas >70 caracteres repetidas) en md de entrega | ninguno |

Ninguna cifra nueva de hoy falla al recalcularse. Por eso no hay CRÍTICO. Lo que hay son dos frases nuevas que **dicen más de lo que se midió**, una frase que el `.tex` dejó a medias y salió así al PDF, y una cara del 45 que sobrevivió en el cuaderno.

---

## SERIO

### S1 · `documento.tex:2452-2457` — la limitación 14 quedó a medio corregir y así está en el PDF

El `.md` (`documento.md:1109-1114`) se reescribió entero y queda bien. El `.tex` solo recibió la mitad del cambio, y el resultado, tal como se lee en `documento.pdf`:

> «en todo lo que no usa red —diccionario, fonética, buscador y puntuación. Los enlaces de audio de Wiktionary son aparte: los descarga el navegador del lector, así que necesitan conexión, aunque no clave— pero se apagan la explicación en contexto y la corrección de pronunciación.»

Una raya se abre en «—diccionario» y se cierra en «clave—», con un punto y una frase entera dentro, y el «pero se apagan» que sigue ya no tiene con qué contrastar. Además el `.tex` conserva «todo lo que no usa red», que era exactamente la objeción (Astra B13); el `.md` lo cambió a «todo lo que no sale a la red desde el servidor». Es la única de las seis correcciones del documento que se hizo en un archivo y no en el otro, y es la que va al PDF.

### S2 · `documento.md:757-759` / `documento.tex:1749-1750` — los tres A1 «pasaron el filtro de la aplicación», y el párrafo nuevo de tres párrafos antes dice lo contrario

La frase antigua: «los tres textos A1 que sostienen el escalón más débil del Cuadro 10 **pasaron el filtro de la aplicación**, no el del análisis». La salvedad nueva (`documento.md:733-740`): el validador «filtra **más flojo que la propia aplicación**» y con el filtro de la aplicación «A1 se queda con uno solo».

Medido: de los tres A1 que sobreviven con espacio, dos (*Dictionary definitions*, *Job adverts*) caen por `maquetado_de_lista` con saltos de línea. Los tres pasaron el filtro **del validador**, que la misma página acaba de definir como una versión desactivada del de la aplicación. Las dos frases no pueden ser ciertas a la vez y están a doce líneas.

### S3 · `documento.md:741-742` / `documento.tex:1736-1737` / `validar_local.py:48-49` — «reproduce las cifras publicadas, incluidas las de la sesión de Colab»

La unión con espacio no reproduce las cifras de Colab; nada local las reproduce. Lo dice el propio documento veinte líneas más arriba (`documento.md:716-718`: «las medias difieren ligeramente de las obtenidas en Colab […] A2 se desvía 0,10»), y en `documento.md:756`: «Los dos entornos filtraron con reglas distintas». Colab tuvo 38 textos y A2 = 0,6479; aquí 46 y 0,5480. Lo que la unión con espacio reproduce es el Cuadro 10 local, y solo eso. La frase se escribió hoy para justificar por qué se conserva el espacio, e inventa una concordancia que el documento ya había negado.

### S4 · `entrega/notebook_proyecto.py:244` y `notebook_proyecto.ipynb` — «59 textos (45 legibles en local)»

Tercera cara del 45. Hoy se corrigió «45 en local» en documento.md/.tex y el `n` de la celda de validación (`:1701`, que ahora suma 46 e imprime «46 textos legibles en local» en `:1704`). Esta tabla de fuentes del mismo cuaderno sigue en 45, y está en la celda de texto que el profesor lee antes que la de código. El cuaderno se contradice a sí mismo: 45 en la línea 244, 46 en la 1704.

### S5 · `documento.md:735-736` / `documento.tex:1730-1731` / `validar_local.py:40-41` — «desactiva dos de las cuatro reglas»

`app/scoring.py:52-73` tiene cuatro salidas: `corto`, `pocas_frases`, `forma_de_frase`, `maquetado_de_lista`. Las dos comprobaciones que miran `splitlines()` (viñetas y líneas cortas) son las **dos condiciones de la cuarta regla** (`:71`), no dos reglas. El propio documento las llama en singular «el detector de maquetado de lista» (`documento.md:755`), y `app/scoring.py:306-307` dice «sus dos comprobaciones de maquetado». Con cualquier forma de contar que dé cuatro, lo desactivado es una regla de cuatro; «dos de las cuatro» hace sonar al validador medio apagado cuando `corto`, `pocas_frases` y `forma_de_frase` siguen activas, y es el tipo de exageración que un lector del código detecta en un minuto.

---

## MENOR

### M1 · `documento.md:917` / `documento.tex:2225` — MAE 0,0000012 frente a 0,000001

Hoy se cambió `arrancar_gpu.py:17` de 0,0000012 a 0,000001 «para que case» con `app/scoring.py:210` e `informe_velocidad.md:186,189,201`. El documento y el PDF siguen diciendo 0,0000012. Misma cifra con dos caras, y la corrección de hoy dejó al documento en el lado minoritario.

### M2 · `documento.md:733-748` / `documento.tex:1729-1741` — «La cuarta no» perdió su antecedente

La salvedad se insertó entre el Cuadro 11 y el párrafo «Las dos primeras restas son de extracción. La cuarta no: son diez textos…». Ese párrafo enumera las filas del cuadro, que ahora están dos párrafos más arriba, separadas por un asunto distinto. Basta con mover la salvedad detrás de ese párrafo.

### M3 · `documento.md:866-867` / `documento.tex:591,2014-2015` — «muestra de 60.000 palabras» es un tope, no un tamaño

`app/ficha.py:159,173-177`: por capítulo se toman `max(300, 60000 // n_capítulos)` palabras. Un libro de 20.000 palabras se mide entero; uno de 250 capítulos supera los 60.000. «Hasta 60.000» sería exacto. Y «la variedad léxica, sobre las primeras 20.000» son los primeros 20.000 *tokens de esa muestra repartida* (`ficha.py:203`), no las primeras 20.000 palabras del libro. La corrección de hoy está bien encaminada (Astra B05) y solo le sobra precisión que no tiene.

### M4 · `validar_local.py:118,138,192` — el guion sigue imprimiendo «Cuadro 11» para lo que el documento llama Cuadro 12

`documento.md:732` = Cuadro 11 es el balance 59→46; `:771` = Cuadro 12 es el baseline. El guion imprime «Cuadro 11 - el modelo frente a la senal trivial». Astra lo anotó en B08; sigue igual. El profesor que ejecute el guion verá dos cuadros 11 distintos.

### M5 · `entrega/manifiesto_corpus_externo.md:20-28` frente a `documento.md:720-732`

El manifiesto dice hoy que el texto 59 «no se puede identificar por nombre» y que «es una cifra heredada, no un archivo localizado». El documento presenta el Cuadro 11 como «contado sobre los archivos reales» con una fila «menos: no disponible −1», que sugiere un archivo conocido que falta. Además, `manifiesto:20`: «los 58 de arriba mas uno mas» es una frase que hay que releer.

### M6 · `documento.md:480` / `documento.tex:1236` — T1 describe la regla de líneas cortas distinto que el código y que el propio validador

T1: «se rechaza si hay ≥2 viñetas o ≥6 líneas cortas». `app/scoring.py:71`: ≥2 viñetas, o bien **≥6 líneas y más del 35 % de ellas con ≤4 palabras**. `validar_local.py:41-42` lo describe bien («mas de un tercio de lineas de cuatro palabras o menos»). No es de hoy, pero la salvedad nueva manda al lector a esa regla, y las dos descripciones de la entrega no coinciden.

### M7 · `entrega/guion_video.md:10` — «552 palabras: 3:41»

Contando el texto entre comillas «…» después de «EL GUION» y quitando las acotaciones `*(…)*`: 6 bloques, **508 palabras**. Con las acotaciones dentro no llega a 530. No es de hoy y no cambia la conclusión (cabe de sobra en cinco minutos), pero es una cifra publicada que no sale.

### M8 · Deriva entre el repositorio y la copia desplegada (no es un archivo de entrega)

El `requirements.txt` que vive en el Space (`huggingface.co/spaces/MikeMaki1763/literalevel/raw/main/requirements.txt:5`) sigue en `gradio>=6.0`; el del repositorio quedó hoy en `==6.26.0`. No tiene efecto —el Space toma la versión de `sdk_version: 6.26.0` en su README—, pero si alguien compara los dos archivos parecerá que el pin no se desplegó. Y `DESPLIEGUE.md:52-57` muestra `app_file: main.py` y emoji 🧊 donde el Space real tiene `app_file: app.py` y 📖.

---

## Lo que se pidió comprobar y está bien

- **Salvedad del validador**: 30 con saltos, 46 con espacio, A1 con uno solo. Sale exacto en el guion y en un recuento independiente. Los diez rechazados caen por «corto» (9 A1 + 1 B1), como dice `documento.md:750-756`. Los 16 que caen de más con saltos de línea son *job adverts*, *conference programme*, *flyer for a gym*, *study skills tips*, *instant messages*… lo de «por parecer listas» es defendible.
- **Ficha 60.000 / 20.000**: los dos números existen en `app/ficha.py:159,203`; la reserva es de redacción (M3), no de cifra. Palabras y tiempo salen del fichero completo (`ficha.py:186-193` y constantes 180/110 en `:31-32`), como dice el documento.
- **Pie de la figura de compresión**: 0,7196x + 0,3760 sobre las cuatro medias de Colab y 0,669x + 0,408 sobre las cinco locales. Redondeos correctos, procedencia correcta, y la recta dibujada (`documento.tex:1830`) es la que dice el pie.
- **`gradio==6.26.0`**: es la instalada, la de la cabecera de `requirements.txt:7` y la del Space. El comentario al final de la línea es sintaxis válida de `pip`.
- **Presentación**: los siete puntos de Astra (A02–A07) están cerrados con la redacción propuesta o una equivalente; «Recorrido de ejemplo» declara que el perfil ilustra y remite a Esmeralda; «≈3–5 h de cómputo A100, estimadas; la descarga va aparte» concuerda con `documento.md:914-927`; las dos notas al pie (`presentacion.tex:159-161,229-230`) dicen lo que dice el documento en `:541-549` y `:660-667`; «cuestionario breve» concuerda con las seis preguntas y tres fragmentos de `documento.md:824` y `guion_video.md:100`. El PDF está recompilado con todo ello.
- **«45 en local» y «1,248»**: desaparecidos de documento.md, documento.tex, presentacion.tex y de los dos PDF. La única cara que sobrevive es la del cuaderno (S4).
- **Conclusión**: «su enlace es temporal» corregido en md y tex; el «hardware más barato / se suspende por inactividad / no guarda nada» concuerda con la limitación 12-13 y con la API.
- **Coherencia general**: cuadros numerados en orden, referencias cruzadas del `.tex` completas, ningún párrafo duplicado, `guion_video.md` y `.tex` cuentan lo mismo, `estrategia.md:196` cita 0,72x + 0,38 sin contradecir la procedencia que da el documento.

---

## C · ¿Queda algo que avergonzaría al autor si lo lee un profesor universitario?

**Sí.** En este orden:

1. La frase rota de la limitación 14 en el PDF (S1): una raya que encierra dos oraciones y un «pero» colgando. Se ve sin buscarlo.
2. Dos afirmaciones en la misma página de la validación que se contradicen: que los tres A1 pasaron el filtro de la aplicación (S2) y que la unión con espacio reproduce las cifras de Colab (S3). Un profesor que lea ese apartado con atención, y es el apartado que sostiene el trabajo, las encuentra.
3. El cuaderno diciendo 45 en la tabla de fuentes y 46 en la celda de validación (S4).
4. «Dos de las cuatro reglas» contra un código de cuatro `return` donde solo uno mira las líneas (S5).
5. El guion que imprime «Cuadro 11» para el Cuadro 12 (M4), porque es lo primero que ve quien ejecuta la reproducción.

Lo demás son decimales y redacción. Con S1–S5 y M1–M4 corregidos —una tarde, ningún experimento nuevo—, el proyecto cierra en cero por lo que a esta auditoría respecta.
