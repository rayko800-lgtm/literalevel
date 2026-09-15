# LiteraLevel

App de lectura en inglés que estima la dificultad de un texto y acompaña al
lector mientras lee. Proyecto integrador del Módulo 5, Diplomado en Ciencia de
Datos (Generación 34).

**Entrega web: Angular + API**, con Gradio como respaldo:

- Aplicación Angular → <https://mikemaki1763-literalevel-front.static.hf.space/>
- API y respaldo Gradio → <https://huggingface.co/spaces/MikeMaki1763/literalevel>
- Modelo v4 → <https://huggingface.co/MikeMaki1763/literalevel-v4>

Para correr Angular en local, en una terminal desde la raíz del proyecto:

```bash
pip install -r requirements.txt
python -X utf8 -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd front
npm.cmd ci
npm.cmd start -- --host 127.0.0.1 --port 4200
```

Abrir `http://127.0.0.1:4200/`. El proxy de desarrollo (`front/proxy.conf.json`)
envía `/api` al puerto 8000. No hace falta instalar Angular globalmente. Para el respaldo Gradio,
`python -X utf8 main.py` usa el puerto 7860; ese comando por sí solo no arranca
la API que espera el front. `python -X utf8 app/api.py` levanta la API y Gradio
en un solo proceso, solo en local. Los recursos del apartado Datos también hacen falta.

## Qué hace

1. **Sitúa al lector.** Un cuestionario breve —seis preguntas y tres fragmentos
   en escalera—, o midiendo un texto que ya lee cómodo.
2. **Busca qué leer.** 53.179 libros de Project Gutenberg indexados por
   significado: se describe la trama en español y el buscador la entiende. Se
   ajusta al nivel del lector. **Cada libro está medido entero por el modelo
   v4**, capítulo a capítulo (585.111 capítulos), y cuando un libro te queda
   grande la aplicación te propone los capítulos que sí están a tu alcance. La
   letra es orientativa: el modelo ordena bien los niveles, pero no certifica
   ninguno. Además, **15.357 textos de licencia libre** (StoryWeaver, Let's
   Read, African Storybook y VOA) medidos con el v4, que se abren sin descargar
   nada y salen intercalados al recomendar por nivel: 68.536 textos en total
   (commit `377a650`). Los títulos con aviso de contenido lo enseñan antes de
   abrir y nunca encabezan la recomendación. (Hasta el 12 de septiembre de 2026
   el catálogo eran 1.197 libros con etiquetas heredadas de un modelo v1.)
3. **Lee.** Lector integrado de epub, pdf y txt. Los libros de Project
   Gutenberg se descargan y se abren dentro de la app, sin salir a por ellos.
   Al abrir un libro sale su **ficha**: tiempo estimado a 180 o 110 palabras por
   minuto (no el ritmo medido del lector), cuánto es diálogo y qué palabras se repiten. Todo eso está
   contado sobre el archivo. Aparte, y detrás de un botón, un resumen de qué
   trata escrito por un modelo de lenguaje a partir de pasajes del propio
   libro, marcado como tal. Y **la curva de dificultad capítulo a capítulo**,
   que sí lee el libro entero con el v4: ahí no se muestrea.
4. **Explica una palabra.** Doble clic sobre cualquier palabra del texto:
   lema, IPA británica y americana de la forma escrita (Wiktionary, CMUdict o, si
   faltan, la IA, marcada), definición, el sentido que
   tiene *en esa frase*, la gramática y el audio de pronunciación. En español
   o en inglés, a elegir. Kaikki conserva la definición cuando existe una
   acepción utilizable; si no existe y se autoriza el servicio externo, el
   fallback aparece marcado como generado por IA. Si la acepción es dudosa y no
   hay explicación, dice «Puede ser» con las principales.
5. **Corrige la pronunciación.** Se lee una frase en voz alta y se marca
   palabra por palabra qué sonó bien y qué no, con el sonido concreto que
   falla y cómo colocar la boca, con su audio y el corte de la boca (2D o 3D)
   moviéndose al compás, también más lento. Y **lectura natural**: dónde se paró
   el lector y qué tramos van lentos para su nivel, énfasis, enlaces y
   reducciones del habla rápida (*don't you* → *doncha*), y la frase dicha de
   corrido.
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
| Validación interna ELG (predicciones en `entrenamiento_v4/`) | 144 | 97.2 % | 0.908 |
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
| `main.py` | Punto de entrada en local. En el Space el mismo papel lo hace un `app.py` |
| `front/` | Interfaz Angular, entregada como sitio estático |
| `app/api.py` | API FastAPI: adapta el motor Python para Angular |
| `app/ui.py` | Motor compartido, ayudantes de acceso e interfaz Gradio de respaldo |
| `app/scoring.py` | Puntuación de dificultad. Port fiel del v4 |
| `app/reader.py` | Lector de epub, pdf y txt → capítulos |
| `app/catalogo.py` | Buscador semántico sobre el catálogo |
| `app/lexicon.py` | Diccionario Kaikki, IPA, audio y explicación contextual |
| `app/voz.py` | Tutor de pronunciación y lectura natural (whisper-1 con marcas por palabra → difflib → tts-1) |
| `app/fonemas.py` | Fonemas del inglés, IPA de diccionario (Kaikki y CMUdict) |
| `app/articulacion.py` | Fichas de articulación por sonido, americano y británico |
| `app/animacion_articulatoria.py` | Corte de la boca en SVG animado, al compás del audio |
| `app/cuentas.py` | Cuentas, cupo de uso y devoluciones |
| `app/cuaderno.py` | Historial de palabras consultadas, con su frase y su libro |
| `app/biblioteca.py` | Los libros abiertos y por qué capítulo va cada uno |
| `app/ficha.py` | Ficha del libro: lo que se cuenta, y el resumen de qué trata |
| `app/perfil.py` | Nivel del lector y rango de lectura recomendado |
| `app/config.py` | Claves. Nunca las imprime |

`app/perfil.py` **no puede llamarse `profile.py`**: taparía el módulo
`profile` de la biblioteca estándar y rompería `import cProfile` dentro de
torch.

## Pruebas

Recuento del 14 de septiembre de 2026 en `74ffffc`, con `LITERALEVEL_SIN_CLAVES=1`
(no lee claves ni gasta):

| Suite | Qué cubre | Hoy |
|---|---|---|
| `tests_smoke.py` | bloques y escala, sin modelo | todo ok (no imprime recuento) |
| `pruebas_extremas.py` | robustez del motor y de Gradio | 349 de 349 |
| `pruebas_integracion.py` | recorrido completo encadenado | 27 pasos de 27 |
| `pruebas_desambiguacion.py` | acepciones, sin red | 8 de 8 |
| `pruebas_perfil.py` | cuestionario de nivel | todo ok (no imprime recuento) |
| `pruebas_ficha.py` | ficha, pasajes y capítulos de cuerpo | 49 comprobaciones, 0 fallos |
| `pruebas_corpus.py` | textos libres en catálogo y lector | 34 de 34 (15 sep) |
| `pruebas_animacion.py` | corte 2D: SVG, duración y repetición | 2.109 comprobaciones, todo ok |
| `pruebas_voz_ritmo.py` | lectura natural con whisper y OpenAI simulados | 34 de 34 (15 sep) |
| `pruebas_voz_concurrencia.py` | voz: candados, migración e historial | 10 de 10 |
| `pruebas_audio_atomico.py` | caché y escritura atómica del TTS | 4 de 4 |
| `pruebas_api.py` | frontera HTTP para Angular | 52 de 52 (15 sep) |
| `pruebas_api_voz_temporal.py` | subida de audio a la API, por AST | pasa |
| `pruebas_portadas.py` | pipeline de portadas, sin GPU ni red | 11 de 11 |
| `pruebas_despliegue.py` | guardas del despliegue del Space | 13 de 13 |
| `pruebas_despliegue_front.py` | publicador del front, sin red | 16 de 16 |
| `pruebas_voz.py` | ciclo de voz; con clave llama a OpenAI | 16 comprobaciones sin red, todo ok (sin clave se omite el ciclo real) |
| `pruebas_lexicon.py --sin-openai` | diccionario real; sin la opción llama a OpenAI | todo ok con --sin-openai |

```bash
python -X utf8 pruebas_extremas.py        # cualquiera de la tabla, igual
cd front && npm.cmd test                  # pruebas del front Angular
```

`pruebas_voz.py` y `pruebas_lexicon.py` (sin `--sin-openai`) llaman a OpenAI de
verdad si hay clave: no ejecutarlas en una revisión sin autorización de gasto.
La degradación legible es el objetivo, no una garantía que una suite pueda
demostrar para todas las entradas.

## Datos que no van en el repositorio

| Qué | Tamaño | De dónde sale |
|---|---|---|
| `modelo_v4/` | 332 MB | Hugging Face, `MikeMaki1763/literalevel-v4` (público, sin credenciales) |
| `kaikki_diccionario.db` | 243 MB | volcado Kaikki/Wiktionary; desplegado dentro del Space, no como dataset independiente |
| `CLAVES.txt`, `.env` | — | claves reales |

Están en `.gitignore`. La app los localiza con `LITERALEVEL_MODELO` y
`LITERALEVEL_DICCIONARIO`, y sin ellos lo dice en la pestaña **Estado** en vez
de fallar. `validar_local.py` también los acepta, y recibe la carpeta del
corpus como argumento.

**Qué se puede reproducir clonando este repositorio y qué no.** El modelo v4
**está publicado** en Hugging Face, en un repositorio público y sin
credenciales: [`MikeMaki1763/literalevel-v4`](https://huggingface.co/MikeMaki1763/literalevel-v4).
Basta apuntar `LITERALEVEL_MODELO` ahí. **El entrenamiento del v4 también está
aquí**, en [`entrenamiento_v4/`](entrenamiento_v4/): el guion, su tarjeta de
métricas y las 144 predicciones de validación. Sus datos (ELG CEFR English) son
públicos, y las cifras de 0,908 y 97,2 % se recalcularon el 12 de septiembre de
2026, idénticas a cuatro decimales. El corpus de British Council no se
distribuye (tiene derechos), pero se reconstruye con
`tools/bajar_corpus_bc.py` y su manifiesto de hashes, y con él se comprueba la
tabla de arriba.

**Sin `OPENAI_API_KEY` la app sigue funcionando**: diccionario, IPA, buscador
y puntuación no salen a la red. El audio de Wiktionary sí: es un enlace a
`upload.wikimedia.org` que descarga el navegador. Lo que se apaga es la
explicación contextual, la generación de definiciones/IPA, la corrección de voz
y el resumen del libro. La primera descarga de recursos y de libros requiere
conexión; disponer del diccionario local no significa que toda la app sea offline.

## Lo que sigue pendiente

Portadas: en la app hay portadas tipográficas por familia de tema; las generadas
por IA siguen sin hacerse (sin presupuesto). La boca 3D, con la cabeza de
MakeHuman, está publicada en la app, con el corte 2D de respaldo.

## Más

- `AGENTS.md` — contrato entre módulos y reparto de archivos entre los agentes
  que trabajan en este repo.
- `DESPLIEGUE.md` — las opciones para publicarlo, con el consumo medido.
