# LiteraLevel

App de lectura en inglés que estima la dificultad de un texto y acompaña al
lector mientras lee. Proyecto integrador del Módulo 5, Diplomado en Ciencia de
Datos (Generación 34).

```bash
pip install -r requirements.txt
python -X utf8 main.py          # la app, en http://127.0.0.1:7860
```

## Qué hace

1. **Sitúa al lector.** Tres preguntas, o midiendo un texto que ya lee cómodo.
2. **Busca qué leer.** 1.197 libros indexados por significado: se describe la
   trama en español y el buscador la entiende. Se ajusta al nivel del lector.
3. **Lee.** Lector integrado de epub, pdf y txt. Los libros de Project
   Gutenberg se descargan y se abren dentro de la app, sin salir a por ellos.
4. **Explica una palabra.** Doble clic sobre cualquier palabra del texto:
   lema, IPA británica y americana, definición de Wiktionary, el sentido que
   tiene *en esa frase*, la gramática y el audio de pronunciación. En español
   o en inglés, a elegir.
5. **Corrige la pronunciación.** Se lee una frase en voz alta y se marca
   palabra por palabra qué sonó bien y qué no, con el sonido concreto que
   falla y cómo colocar la boca.
6. **Recuerda.** Vuelve al capítulo donde se dejó la lectura y guarda cada
   palabra consultada con su frase y su libro.

## El modelo

`distilroberta-base` en **regresión**, no clasificación. Bloques de 250
palabras, mínimo 150, hasta 8 por documento, media sin ponderar. **La longitud
total nunca es una señal.** Escala interna 0..5 (A1..C2); escala pública
0..2 = interna × 0.4.

| Validación | n | Dentro de ±1 nivel | Spearman |
|---|---|---|---|
| Corpus de validación | 144 | 97.2 % | 0.908 |
| British Council (externo) | 38 | 100 % | 0.829 |

El argumento fuerte no es el acierto exacto, sino que **en corpus externo las
medias por nivel quedan estrictamente ordenadas**: A2 0.648 < B1 0.951 <
B2 1.288 < C1 1.495.

El modelo **es final y no se reentrena**.

## Reproducir la validación

```bash
python -X utf8 validar_local.py
```

Reproduce en local la validación externa hecha en Colab. Coincide hasta la
cuarta cifra (C1: 1.4952 local frente a 1.4950 en Colab) y el orden por nivel
es estrictamente creciente. No imprime ni un fragmento de los textos: el
corpus tiene derechos.

## Módulos

| Archivo | Qué hace |
|---|---|
| `main.py` | Punto de entrada. **No renombrar a `app.py`**: chocaría con `app/` |
| `app/ui.py` | La interfaz: seis pestañas en Gradio 6 |
| `app/scoring.py` | Puntuación de dificultad. Port fiel del v4 |
| `app/reader.py` | Lector de epub, pdf y txt → capítulos |
| `app/catalogo.py` | Buscador semántico sobre el catálogo |
| `app/lexicon.py` | Diccionario Kaikki, IPA, audio y explicación contextual |
| `app/voz.py` | Tutor de pronunciación (whisper-1 → difflib → tts-1) |
| `app/cuaderno.py` | Historial de palabras consultadas, con su frase y su libro |
| `app/perfil.py` | Nivel del lector y rango de lectura recomendado |
| `app/config.py` | Claves. Nunca las imprime |

`app/perfil.py` **no puede llamarse `profile.py`**: taparía el módulo
`profile` de la biblioteca estándar y rompería `import cProfile` dentro de
torch.

## Pruebas

```bash
python -X utf8 tests_smoke.py          # lógica de bloques y escala, sin modelo
python -X utf8 pruebas_extremas.py     # 91 pruebas que intentan romper la interfaz
python -X utf8 pruebas_desambiguacion.py   # 7 pruebas de acepciones, sin red
python -X utf8 pruebas_lexicon.py      # diccionario y caché (usa OpenAI)
python -X utf8 pruebas_voz.py          # ciclo de voz completo (usa OpenAI)
```

La regla que verifican las pruebas extremas es una sola: **ningún manejador
puede lanzar una excepción hacia la interfaz**. Lo que falla vuelve como texto
legible.

## Datos que no van en el repositorio

| Qué | Tamaño | De dónde sale |
|---|---|---|
| `modelo_v4/` | 317 MB | Drive, `literalevel_bigdata` |
| `kaikki_diccionario.db` | 232 MB | volcado de Kaikki/Wiktionary, 1,48 M entradas |
| `CLAVES.txt`, `.env` | — | claves reales |

Están en `.gitignore`. La app los localiza con `LITERALEVEL_MODELO` y
`LITERALEVEL_DICCIONARIO`, y sin ellos lo dice en la pestaña **Estado** en vez
de fallar.

**Sin `OPENAI_API_KEY` la app sigue funcionando**: diccionario, IPA, audio de
Wiktionary, buscador y puntuación no usan red. Lo que se apaga es la
explicación contextual y la voz.

## Más

- `AGENTS.md` — contrato entre módulos y reparto de archivos entre los agentes
  que trabajan en este repo.
- `DESPLIEGUE.md` — las opciones para publicarlo, con el consumo medido.
