# Ronda 4 · Enlaces y recursos públicos de la entrega (4e, 15 sep 2026)

Encargo de la Central (`5efbc9f`): comprobar que cada enlace y cada recurso
público que citan los entregables existe y responde **sin cuenta**. Solo
lectura; no se ha tocado `app/`, `front/`, el cuaderno ni los documentos.

**Qué se recorrió:** `entrega/documento.md` y `.tex`, `estrategia.md`,
`presentacion.tex`, `notebook_proyecto.py` y `.ipynb`, `guion_demo_en_vivo.md`,
`guion_video.md` y `.tex`, `mensaje_profesor.md`, `referencias.bib` (la
bibliografía de `documento.tex`, `\addbibresource` en la línea 65) y el README de
los dos Spaces (descargados sin token). Un guion extrae cada URL y DOI con su
archivo:línea: **229 apariciones y 97 enlaces distintos** tras normalizar los
artefactos de extracción (la URL de CLEAR partida en dos líneas, `**` de negrita
pegado, saltos de línea de celdas). `presentacion.tex`, `guion_video.md` y
`guion_video.tex` no contienen ningún enlace.

**Cómo:** `curl -I -L` con agente de navegador y, si el HEAD se rechaza, GET de
1 KB. Los DOI, además, contra la API de handles de doi.org (`responseCode 1` =
registrado; un DOI inventado da `100`). Los repos de Hugging Face, contra su API
pública y `resolve/main/<archivo>` sin token. Hora de las medidas: 10:10–10:50
del 15 de septiembre.

## Resumen

| Gravedad | Hallazgo |
|---|---|
| **SERIO** | El «repositorio» del que el cuaderno y los documentos dicen que se recalculan cifras **no es público**: `github.com/rayko800-lgtm/literalevel` da 404 sin sesión, y `validar_local.py`, `tools/bajar_corpus_bc.py` y `entrenamiento_v4/` no están en ninguno de los tres repos públicos de Hugging Face. El cuaderno **corre** sin ellos; lo que no se puede hacer sin cuenta es el paso 4 de su receta de British Council ni el recálculo de las métricas del v4. Detalle abajo. |
| — | Todo lo que el cuaderno descarga con código responde sin cuenta y con el tamaño que dice: CLEAR (3,35 MB), catálogo de Gutenberg (21,2 MB) y los pesos del v4 (328,5 MB). |
| — | Los 59 PDF de British Council del manifiesto: **59 de 59 idénticos byte a byte** (SHA-256) descargados desde un navegador sin sesión. Con código no responden, como el propio cuaderno avisa. |
| — | Los dos Spaces, públicos y en `RUNNING`; `/api/estado` 200. |
| — | 12 DOI registrados y 25 enlaces web más, todos 200. Ningún enlace roto. |

## Hallazgo

**[SERIO] Las cifras que se «recalculan desde el repositorio» dependen de un repositorio que no es público**

- **Dónde:**
  - `entrega/notebook_proyecto.py:1950` y `:2102-2103`: el paso 4 de la receta de
    British Council y la salida de la celda mandan a ejecutar
    `python -X utf8 validar_local.py corpus_bc` «desde la raíz del repositorio».
  - `:1945`: el manifiesto en CSV «en el repositorio».
  - `:1953`: `tools/bajar_corpus_bc.py`.
  - `:1540`, `:2579`, `:2585`, `:2602`: guion y métricas del v4 en
    `entrenamiento_v4/`.
  - `:2578`: la tabla de reproducibilidad dice «Sí, fuera del cuadernillo».
  - Documentos: `documento.md:1430` («también se recalculan desde el
    repositorio»), `documento.tex:532`, `:3041` y `:3234`, `estrategia.md:24` y `:27`.
  - `mensaje_profesor.md:49` ofrece compartir el repositorio, sin enlace.
- **Qué pasa:**
  - `https://github.com/rayko800-lgtm/literalevel` responde **404** sin sesión, o
    sea privado o inexistente para un lector sin cuenta. Ningún entregable enlaza
    esa URL: la saqué del remoto de este árbol.
  - En la API pública de HF (`/tree/main?recursive=true`):
    - el Space de la API (126 archivos) trae `catalogo_recomendaciones.csv` y
      `catalogo_medido.csv`, que citan `notebook_proyecto.py:809` y `:859`, pero
      **no** trae `validar_local.py`, `tools/`, `entrenamiento_v4/`,
      `corpus_bc_manifiesto.csv` ni los CSV de `validacion_graduados_puntuaciones_*`;
    - el repo del modelo solo tiene 6 archivos (pesos, tokenizador, config y
      README);
    - el Space del front no tiene ninguno de ellos.
- **Por qué es SERIO y no MENOR:** es un recurso que el cuaderno pide para una de
  sus afirmaciones (Cuadro 13 «al decimal», métricas del v4 «idénticas a cuatro
  decimales»), y quien lo abre sin cuenta no puede llegar a él. **No bloquea la
  ejecución:**
  - la celda de British Council verifica hashes con `corpus_bc/` vacío o lleno y
    no llama a `validar_local.py`;
  - la de los graduados cae a la tabla impresa si no están los CSV (`:2264-2272`);
  - el modelo sale de HF.
- **Arreglo (decisión de Miguel, no de esta auditoría):** hay tres salidas.
  1. Hacer público el repositorio (o una copia con `validar_local.py`, `tools/`,
     `entrenamiento_v4/` y el manifiesto) y enlazarlo.
  2. Subir esos tres a un repo público de HF que ya existe.
  3. Rebajar el texto a «el repositorio se comparte a petición» en los sitios
     citados, de acuerdo con lo que ya ofrece `mensaje_profesor.md:49`.

## Recursos que el cuaderno usa con código

| Enlace | Dónde se cita | HTTP | Observación |
|---|---|---|---|
| `https://raw.githubusercontent.com/scrosseye/CLEAR-Corpus/main/CLEAR_corpus_final.xlsx` | notebook_proyecto.py:287-288 (celda 6) | 200 | 3.349.179 bytes; el cuaderno pide `minimo_bytes=3_000_000` y dice 3,3 MB (:361). Con `urllib` sin cabeceras, igual que `descargar()` (:180), responde 206 al pedir 1 KB. |
| `https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv` | notebook_proyecto.py:367, :436, :2562, :2655 (celdas 12 y 102) | 200 | 21.215.185 bytes (`minimo_bytes=15_000_000`; el cuaderno dice 21,2 MB, :439). Last-Modified 13 sep 2026. `urllib` sin cabeceras: 206. |
| `https://huggingface.co/MikeMaki1763/literalevel-v4` | notebook_proyecto.py:56, :1471 (celdas 1 y 72); README Space API:38 | 200 | API: `private: false`, `gated: false`, sha `0a45209`. |
| `…/literalevel-v4/resolve/main/config.json` | lo pide `from_pretrained(URL_MODELO)`, notebook_proyecto.py:1588-1589 | 200 | sin token |
| `…/resolve/main/model.safetensors` | ídem | 200 | `X-Linked-Size` 328.489.204; el cuaderno dice 328 MB (:1549). |
| `…/resolve/main/tokenizer.json` | ídem | 200 | sin token |
| `…/resolve/main/tokenizer_config.json` | ídem | 200 | sin token |
| `…/resolve/main/special_tokens_map.json`, `vocab.txt` | (no los cita el cuaderno) | 404 | No existen en el repo y no hacen falta: con `tokenizer.json`, `AutoTokenizer` los trata como opcionales. Solo se anota para que un 404 en el registro de Colab no se lea como fallo. |

## British Council: 59 PDF del manifiesto

| Enlace | Dónde se cita | HTTP | Observación |
|---|---|---|---|
| `https://learnenglish.britishcouncil.org/sites/podcasts/files/LearnEnglish-Reading-*.pdf` (59 URL: 12 A1, 10 A2 + `LearnEnglish_Reading-A2-An-email-from-a-friend.pdf`, 13 B1, 12 B2, 12 C1) | notebook_proyecto.py:1873-1989, una URL cada dos líneas (`MANIFIESTO_BC`, celda 87) | **200 en navegador**; 000 con `curl` y con Python | Desde Chrome, en un contexto aislado sin sesión y con `fetch(..., {credentials: "omit"})` a la misma web: 59 de 59 con SHA-256 igual al del manifiesto, 5,3 MB, 7 s. Con `curl` (HEAD y GET) los 59 se quedan sin respuesta (`000`, tiempo agotado a 30–40 s); con `urllib` y agente de navegador, un GET entero se agota a 25 s. Un GET de 1 KB con `urllib` sí respondió una vez (206, `%PDF-`), sin que eso sirva para descargar. Coincide con lo que dice el cuaderno en :1934-1937 («se descargan con el navegador, no con código»): la afirmación sigue siendo cierta hoy. |

## Spaces

| Enlace | Dónde se cita | HTTP | Observación |
|---|---|---|---|
| `https://mikemaki1763-literalevel-front.static.hf.space/` | documento.md:1271, documento.tex:1013, estrategia.md:453, notebook_proyecto.py:12 (celda 0), guion_demo_en_vivo.md:25, mensaje_profesor.md:20 | 302 → 200 | Redirige a `/index.html` (200, 0,38 s) y sirve «LiteraLevel · Lee en inglés a tu medida». Space `literalevel-front`: `private: false`, sha `72e9525`, `RUNNING`. |
| `https://mikemaki1763-literalevel.hf.space/api/estado` | guion_demo_en_vivo.md:30 | 200 | 0,29–0,54 s. Space `literalevel`: `private: false`, sha `0319290`, `RUNNING`. |
| `https://huggingface.co/spaces/MikeMaki1763/literalevel` | README Space front:17 | 200 | |
| `https://huggingface.co/spaces/MikeMaki1763/literalevel-front` | (página del Space, pedida por la Central; no la cita ningún entregable) | 200 | |
| `https://kaikki.org/` | README Space API:59 | 200 | El cuaderno no usa Kaikki (notebook_proyecto.py:68). |
| `https://www.gutenberg.org/` | README Space API:58 | 200 | |

## DOI (bibliografía)

Primer salto de `doi.org`: 302 en los 12. Con `-L`, varias editoriales (Wiley,
ACM, APA, Springer) devuelven otro 302 o un reto antibots a `curl`; eso no dice
nada del DOI, así que se contrastó con la API de handles.

| DOI | Dónde se cita | doi.org | Destino registrado |
|---|---|---|---|
| 10.1002/tesq.157 | documento.md:1745, estrategia.md:710, referencias.bib:139 | 302 · handle 1 | onlinelibrary.wiley.com |
| 10.1007/978-3-031-17258-8_16 | documento.md:1673, estrategia.md:662, referencias.bib:294 | 302 · handle 1 | link.springer.com |
| 10.1037/0033-2909.125.6.627 | documento.md:1698, estrategia.md:670, referencias.bib:66 | 302 · handle 1 | doi.apa.org |
| 10.1145/2934664 | documento.md:1812, referencias.bib:250 | 302 · handle 1 | dl.acm.org |
| 10.1145/2939672.2939785 | documento.md:1681, referencias.bib:24 | 302 · handle 1 | dl.acm.org |
| 10.18653/v1/2020.emnlp-demos.6 | documento.md:1799, referencias.bib:219 | 302 · handle 1 | aclanthology.org |
| 10.18653/v1/2025.emnlp-main.491 | documento.md:1721, estrategia.md:683, referencias.bib:270 | 302 · handle 1 | aclanthology.org |
| 10.18653/v1/D19-1410 | documento.md:1769, referencias.bib:187 | 302 · handle 1 | aclweb.org/anthology |
| 10.18653/v1/W18-0535 | documento.md:1788, referencias.bib:208 | 302 · handle 1 | aclweb.org/anthology (http) |
| 10.3390/e22010126 | documento.md:1705, referencias.bib:87 | 302 · handle 1 | mdpi.com |
| 10.3758/s13428-022-01802-x | documento.md:1690, referencias.bib:45 | 302 · handle 1 | link.springer.com |
| 10.5281/zenodo.2422561 | documento.md:1701, referencias.bib:75 | 302 · handle 1 | zenodo.org |

## Otros enlaces web

| Enlace | Dónde se cita | HTTP | Observación |
|---|---|---|---|
| `https://arxiv.org/abs/1906.02569` | documento.md:1669, referencias.bib:13 | 200 | |
| `https://arxiv.org/abs/1907.11692` | documento.md:1736, referencias.bib:127 | 200 | |
| `https://arxiv.org/abs/1910.01108` | documento.md:1776, referencias.bib:197 | 200 | |
| `https://arxiv.org/abs/2506.05209` | documento.md:1728, estrategia.md:690, referencias.bib:304 | 200 | |
| `https://arxiv.org/abs/2506.14046` | estrategia.md:695 | 200 | Solo en la estrategia; no está en `referencias.bib`. No es un enlace roto, se anota por si debía estar en la bibliografía del documento. |
| `https://arxiv.org/abs/2604.24470` | documento.md:1709, estrategia.md:674, referencias.bib:280 | 200 | |
| `https://github.com/cmusphinx/cmudict` | documento.md:1676, estrategia.md:665, referencias.bib:312 | 200 | |
| `https://learningenglish.voanews.com` | documento.md:1791, estrategia.md:729, referencias.bib:365 | 200 | redirige a la barra final |
| `https://static.makehumancommunity.org/about/license.html` | documento.md:1739, estrategia.md:704, referencias.bib:334 | 200 | |
| `https://storyweaver.org.in` | documento.md:1761, estrategia.md:717, referencias.bib:342 | 200 | |
| `https://teakreader.com/english-reading-level-checker-for-books` | documento.md:1779, estrategia.md:723, referencias.bib:327 | 200 | |
| `https://www.africanstorybook.org` | documento.md:1772, estrategia.md:720, referencias.bib:358 | 200 | |
| `https://www.gutenberg.org` | documento.md:1764, referencias.bib:176 | 200 | |
| `https://www.letsreadasia.org` | documento.md:1782, estrategia.md:726, referencias.bib:350 | 200 | |
| `https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/` | documento.md:1752, estrategia.md:714, referencias.bib:158 | 200 | |
| `https://www.w3.org/TR/WCAG22/` | documento.md:1802, estrategia.md:732, referencias.bib:228 | 200 | |
| `https://www2.metametricsinc.com/content-creator-annual-pricing` | documento.md:1742, estrategia.md:707, referencias.bib:320 | 200 | |

## Lo que no se comprobó

- Que el cuaderno **corra entero** en Colab: no es de este encargo (lo ejecuta
  f4). Aquí solo consta que cada recurso que descarga responde sin cuenta desde
  esta máquina; desde las IP de Colab el CDN de British Council no se ha probado,
  y el cuaderno no lo descarga con código.
- El contenido de los artículos tras cada DOI (solo que el DOI está registrado y
  apunta a la editorial).
- Si el repositorio de GitHub existe con otra visibilidad o bajo otro nombre:
  solo que esa URL da 404 sin sesión.
