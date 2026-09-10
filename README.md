# LiteraLevel

App de lectura en inglés que estima la dificultad de un texto y acompaña al
lector mientras lee. Proyecto integrador del Módulo 5, Diplomado en Ciencia de
Datos (Generación 34).

**Está desplegada y funcionando:**

- Aplicación → <https://huggingface.co/spaces/MikeMaki1763/literalevel>
- Modelo v4 → <https://huggingface.co/MikeMaki1763/literalevel-v4>

Para correrla en local:

```bash
pip install -r requirements.txt
python -X utf8 main.py          # la app, en http://127.0.0.1:7860
```

## Qué hace

1. **Sitúa al lector.** Un cuestionario breve —seis preguntas y tres fragmentos
   en escalera—, o midiendo un texto que ya lee cómodo.
2. **Busca qué leer.** 1.197 libros indexados por significado: se describe la
   trama en español y el buscador la entiende. Se ajusta al nivel del lector.
   **Aviso sobre las etiquetas del catálogo:** la columna `nivel_cefr` de los
   1.197 libros **no es anotación humana ni metadato del editor**. Son
   predicciones automáticas de un modelo anterior (v1) sobre las primeras
   ~190 palabras de cada obra, con cortes CEFR obtenidos por cuantiles. Por
   eso hay cuentos infantiles etiquetados C1 y clásicos muy distintos entre sí
   todos en C2. Sirven para ordenar y filtrar de forma aproximada; **no son
   una medida de nivel fiable libro a libro**, y no deben presentarse como tal.
3. **Lee.** Lector integrado de epub, pdf y txt. Los libros de Project
   Gutenberg se descargan y se abren dentro de la app, sin salir a por ellos.
   Al abrir un libro sale su **ficha**: cuánto se tarda en leerlo al ritmo de
   quien lo abre, cuánto es diálogo, qué palabras se repiten. Todo eso está
   contado sobre el archivo. Aparte, y detrás de un botón, un resumen de qué
   trata escrito por un modelo de lenguaje a partir de pasajes del propio
   libro, marcado como tal. Y **la curva de dificultad capítulo a capítulo**,
   que sí lee el libro entero con el v4: ahí no se muestrea.
4. **Explica una palabra.** Doble clic sobre cualquier palabra del texto:
   lema, IPA británica y americana, definición de Wiktionary, el sentido que
   tiene *en esa frase*, la gramática y el audio de pronunciación. En español
   o en inglés, a elegir.
5. **Corrige la pronunciación.** Se lee una frase en voz alta y se marca
   palabra por palabra qué sonó bien y qué no, con el sonido concreto que
   falla y cómo colocar la boca.
6. **Recuerda.** *Mis libros* guarda todos los libros empezados, con la
   barra de avance y el capítulo por el que iba cada uno, y los reabre ahí
   mismo. *Mis palabras* guarda cada palabra consultada con su frase y su
   libro.

## El modelo

`distilroberta-base` en **regresión**, no clasificación. Bloques de 250
palabras, mínimo 150, hasta 8 por documento repartidos por todo el texto, media
sin ponderar. Escala interna 0..5 (A1..C2); escala pública 0..2 = interna × 0.4.

**El modelo no recibe la longitud del documento como variable**: puntúa
ventanas de tamaño fijo y promedia. Eso no es lo mismo que decir que su salida
sea independiente de la longitud — en British Council correlacionan 0.732,
porque ese corpus gradúa también por longitud de la tarea.

| Validación | n | Dentro de ±1 nivel | Spearman |
|---|---|---|---|
| Corpus de validación (no incluido) | 144 | 97.2 % | 0.908 |
| British Council (externo, no incluido) | 38 | 100 % | 0.829 |

### El baseline, dicho antes de que lo pregunten

Sobre los 47 textos de British Council que se pueden medir en local:

| Señal | Spearman con el nivel oficial |
|---|---|
| Modelo v4 | **0.860** |
| Contar las palabras del texto, sin modelo | 0.807 |
| Modelo, descontando la longitud (correlación parcial) | **0.668** |

Un contador de palabras llega casi tan lejos, y hay que decirlo: en British
Council el nivel y la longitud están confundidos. Lo que sostiene al modelo es
la tercera fila — **aporta señal por encima de la longitud**, que es lo que un
contador no puede hacer.

El argumento fuerte tampoco es el acierto exacto, sino que **en corpus externo
las medias por nivel quedan estrictamente ordenadas**: A1 0.504 < A2 0.556 <
B1 0.928 < B2 1.241 < C1 1.495 — la reproducción local sobre 47 textos. La
tanda histórica de Colab, con cuatro niveles y otras medias, está en la tabla
de más abajo; son conjuntos distintos y no se mezclan.

La escala pública es **ordinal y comprimida**: contra el ancla real, el ajuste
ronda `predicho ≈ 0.72 × real + 0.38`, así que un texto A2 suele puntuar cerca
de B1. Por eso la app muestra bandas (básico / intermedio / avanzado) y la
letra CEFR solo como orientación.

El modelo **es final y no se reentrena**.

## Reproducir la validación

```bash
python -X utf8 validar_local.py
```

Reproduce en local la validación externa hecha en Colab. **Lo que se reproduce
es el orden, no las cifras exactas.** Salida real en local, frente a lo que
reportó Colab:

| nivel | n | media local | Colab |
|---|---|---|---|
| A1 | 3 | 0.5040 | — |
| A2 | 8 | 0.5561 | 0.6479 |
| B1 | 12 | 0.9276 | 0.9513 |
| B2 | 12 | 1.2414 | 1.2883 |
| C1 | 12 | 1.4952 | 1.4950 |

C1 coincide hasta la tercera cifra decimal (1,4952 frente a 1,4950); A2 se
desvía 0.09. La causa es la
extracción de los PDF y el filtro de prosa continua: en local sobreviven 47 de los
59 originales —dos no tienen cuerpo localizable y otros diez los rechaza `scoring.continuous_prose` por quedarse bajo las 150 palabras— y el anclaje
«Reading text … Tasks» recorta distinto. **Lo que sí se reproduce exactamente es
que las medias quedan estrictamente crecientes**, que es el resultado que
sostiene el trabajo.

El guion imprime además las tres cifras del cuadro del *baseline* (el 13 de `documento.md`, el 18 del PDF; modelo 0,860, contar
palabras 0,807, parcial descontando la longitud 0,668) y la lista de los diez
rechazados con su motivo. Los nombres de los 59 archivos del corpus están en
[`entrega/manifiesto_corpus_externo.md`](entrega/manifiesto_corpus_externo.md).

No imprime ni un fragmento de los textos: el corpus tiene derechos.

## Módulos

| Archivo | Qué hace |
|---|---|
| `main.py` | Punto de entrada. **No renombrar a `app.py`**: chocaría con `app/` |
| `app/ui.py` | La interfaz: ocho pestañas en Gradio 6 |
| `app/scoring.py` | Puntuación de dificultad. Port fiel del v4 |
| `app/reader.py` | Lector de epub, pdf y txt → capítulos |
| `app/catalogo.py` | Buscador semántico sobre el catálogo |
| `app/lexicon.py` | Diccionario Kaikki, IPA, audio y explicación contextual |
| `app/voz.py` | Tutor de pronunciación (whisper-1 → difflib → tts-1) |
| `app/cuaderno.py` | Historial de palabras consultadas, con su frase y su libro |
| `app/biblioteca.py` | Los libros abiertos y por qué capítulo va cada uno |
| `app/ficha.py` | Ficha del libro: lo que se cuenta, y el resumen de qué trata |
| `app/perfil.py` | Nivel del lector y rango de lectura recomendado |
| `app/config.py` | Claves. Nunca las imprime |

`app/perfil.py` **no puede llamarse `profile.py`**: taparía el módulo
`profile` de la biblioteca estándar y rompería `import cProfile` dentro de
torch.

## Pruebas

```bash
python -X utf8 tests_smoke.py          # lógica de bloques y escala, sin modelo
python -X utf8 pruebas_extremas.py     # 216 pruebas que intentan romper la interfaz
python -X utf8 pruebas_integracion.py   # 27 pasos del recorrido completo
python -X utf8 pruebas_desambiguacion.py   # 7 pruebas de acepciones, sin red
python -X utf8 pruebas_perfil.py       # extremos del cuestionario de nivel
python -X utf8 pruebas_ficha.py        # que los números de la ficha signifiquen algo
python -X utf8 pruebas_lexicon.py      # diccionario y caché (usa OpenAI)
python -X utf8 pruebas_voz.py          # ciclo de voz completo (usa OpenAI)
```

La regla que verifican las pruebas extremas es una sola: **ningún manejador
puede lanzar una excepción hacia la interfaz**. Lo que falla vuelve como texto
legible.

## Datos que no van en el repositorio

| Qué | Tamaño | De dónde sale |
|---|---|---|
| `modelo_v4/` | 328 MB | Hugging Face, `MikeMaki1763/literalevel-v4` (público, sin credenciales) |
| `kaikki_diccionario.db` | 243 MB | volcado de Kaikki/Wiktionary, 1,48 M entradas (sin publicar; copia en Drive) |
| `CLAVES.txt`, `.env` | — | claves reales |

Están en `.gitignore`. La app los localiza con `LITERALEVEL_MODELO` y
`LITERALEVEL_DICCIONARIO`, y sin ellos lo dice en la pestaña **Estado** en vez
de fallar. `validar_local.py` también los acepta, y recibe la carpeta del
corpus como argumento.

**Qué se puede reproducir clonando este repositorio y qué no.** El modelo v4
**está publicado** en Hugging Face, en un repositorio público y sin
credenciales: [`MikeMaki1763/literalevel-v4`](https://huggingface.co/MikeMaki1763/literalevel-v4).
Basta apuntar `LITERALEVEL_MODELO` ahí. El corpus de British Council no se
distribuye (tiene derechos) y el corpus de validación de 144 textos tampoco
está aquí: las cifras de 0.908 y 97.2 % **no son verificables desde este
repositorio**, aunque su aritmética interna sí cuadra (510 + 144 = 654,
77/144 = 53,47 %, 140/144 = 97,22 %). Lo que sí se
comprueba en local es la tabla de arriba, con los PDF de British Council en
una carpeta. El código de entrenamiento del v4 no forma parte de este
repositorio: aquí vive la aplicación, no el experimento.

**Sin `OPENAI_API_KEY` la app sigue funcionando**: diccionario, IPA, buscador
y puntuación no salen a la red. El audio de Wiktionary sí: es un enlace a
`upload.wikimedia.org` que descarga el navegador. Lo que se apaga es la
explicación contextual y la voz.

## Más

- `AGENTS.md` — contrato entre módulos y reparto de archivos entre los agentes
  que trabajan en este repo.
- `DESPLIEGUE.md` — las opciones para publicarlo, con el consumo medido.
