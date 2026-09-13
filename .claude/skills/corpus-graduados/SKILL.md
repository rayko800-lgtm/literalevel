---
name: corpus-graduados
description: Bajar, limpiar, validar y catalogar corpus externos de lectura (StoryWeaver, African Storybook, VOA Learning English, Let's Read) para LiteraLevel — la regla de licencias de Miguel, los endpoints que funcionan, las trampas de formato de cada fuente y cómo medir cuentos cortos con el v4. Úsala antes de tocar corpus_graduado/, validar_graduados.py, tools/bajar_*.py o tools/catalogar_corpus.py, o al añadir cualquier fuente nueva de textos al catálogo.
---

# Corpus graduados: de la descarga al catálogo

El pipeline completo, con sus puntos de control, está en `PIPELINE_CORPUS.md`.
Los hallazgos medidos, en `auditoria/validacion_graduados_2026-09-12.md`.
**El v4 no se reentrena nunca**: todo esto es medir, validar y catalogar.

## 1. La regla de Miguel (12 sep 2026)

| ¿Licencia libre? | ¿Nivel del editor? | Qué se hace |
|---|---|---|
| No (NC, ND, adaptado de AP/Reuters/AFP, desconocida) | da igual | Se mide y valida **internamente**. **Nunca** al catálogo |
| Sí (dominio público, CC BY) | Sí | Primero se **valida el orden** contra el nivel; después al catálogo |
| Sí | No | **Lo gradúa el v4** (nuestro veredicto) y al catálogo |

El nivel de un editor infantil **no es MCER**: se valida el orden (Spearman,
medias crecientes), nunca «el modelo acierta A1».

## 2. Las fuentes, y lo que costó averiguar de cada una

### StoryWeaver — CC BY 4.0 toda la plataforma (su FAQ), niveles 1–4
- Listado: `https://storyweaver.org.in/api/v1/books-search?languages%5B%5D=English&levels%5B%5D=N&page=P&per_page=50`
  (16.805 libros en inglés: 5.289 / 5.458 / 3.690 / 2.368).
- Ficha: `/api/v1/stories/<slug>` · Texto: `/api/v1/stories/<slug>/read` → `pages[].html`, solo `pageType == "StoryPage"`.
- **Trampa:** cada página trae un bloque de JavaScript del lector web
  (`$(document).ready(function() { var story_editor = ...`) y un contador `2/10`.
  Hay que quitar `<script>` antes de limpiar etiquetas y, en lo ya bajado, las
  líneas enteras de ese bloque (regex `_SIN_JS` de `validar_graduados.py`).
- **Trampa:** el listado va ordenado por valoración. Para validar sin sesgo de
  popularidad se baja en **orden aleatorio intercalando niveles** (semilla
  20260912) y se apartan las primeras 48 líneas, que se bajaron antes.
- Lento: ~1–1,4 s por petición. Tres hilos con pausa propia; aun así, horas.

### African Storybook — licencia por cuento, niveles 1–5 en su web
- Texto: repo `global-asp/asp-source`, carpeta `en/` (368 `.md`; `##` = salto de
  página; `* License: [CC-BY]` al final). Tarball por codeload de GitHub.
- Nivel: **no está en el repo**. Está en `https://www.africanstorybook.org/booklistjs.php`
  (`bookItems.push({id, title, lang, level, approved})`). Inglés = `lang:"1133"`.
  Se cruza por título normalizado: 300 de 368 cruzan.
- Licencias: 316 CC-BY · 48 CC-BY-NC · 3 CC BY-NC-SA · 1 desconocida.

### VOA Learning English — dominio público, **sin nivel por artículo**
- Las páginas «Beginning/Intermediate/Advanced» (p/5609–5611) enlazan las mismas
  secciones: el sitio no etiqueta cada artículo. Se guarda la sección.
- Cuerpo: párrafos `<p>` tras `id="article-content"`.
- **Trampa de licencia:** muchos de «As It Is» cierran con «X reported this story
  for the Associated Press. Y adapted it for VOA Learning English». La política de
  VOA (p/6021) dice que el material de AP tiene derechos → **interno**. Igual
  Reuters y AFP. Solo lo escrito por VOA va al catálogo.
- Quitar el aviso «No media source currently available» y el glosario final
  («Words in This Story», «steep – n. …»).

### Let's Read (The Asia Foundation) — licencia por libro, niveles 1–5
- La API está en el chunk `_app` de letsreadasia.org: base `https://letsreadasia.org/api`.
- Inglés `lId=4846240843956224`. Listado:
  `/book/elastic/search/?searchText=&lId=<ingles>&readingLevel=N&limit=20&cursor=<cursorWebSafeString>`
  (308 / 416 / 284 / 155 / 129).
- Texto: `/v5/book/preview/language/<ingles>/book/<masterBookId>` →
  `pages[].extractedLongContentValue`. **Con el `id` del libro da 404**: usar `masterBookId`.
- Muchos «ingleses» son traducciones: deduplicar por `masterBookId`.
- Licencias mezcladas; en la muestra, casi todo CC-BY-NC o NC-ND → interno.
- Sin robots.txt; los términos no hablan de acceso automatizado. 1 petición/s.

### Descartadas
- Global Digital Library: la API (`api.digitallibrary.io`) no responde.
- UniversalCEFR `elg_cefr_en` y `cambridge_exams_en`: **son el corpus de
  entrenamiento del v4**. Validar con ellos es fuga.

## 3. Cómo se mide con el v4

- **Páginas en párrafos antes de nada.** Un libro ilustrado trae una frase por
  renglón y el filtro de prosa lo toma por lista: 70 de 219 unidades rechazadas.
  Unir cada página en un párrafo las dejó en 9.
- **Cuentos cortos (decisión de Miguel):** ≥250 palabras, solos; los demás, en
  bloques de ≥250 **sin mezclar fuente ni nivel**. La cola corta se declara, no se estira.
  Al catalogar, un cuento corto toma la puntuación de su bloque y va marcado `medida = bloque`.
- **Fuga:** 8-gramas contra ELG CEFR English (en caché de HF), umbral 50 %.
- **Métricas siempre con la línea base de contar palabras** y la correlación
  parcial que descuenta la longitud. En African Storybook la longitud (0,706)
  ordenaba mejor que el modelo (0,416): sin esa línea base el resultado engaña.
- `validar_graduados.py --fuente X` escribe `auditoria/validacion_graduados_puntuaciones_X.csv`.
  **Sin `--fuente` sobrescribe el archivo común**: una vez borró lo de otra fuente.

## 4. Catalogar

`tools/catalogar_corpus.py` → `catalogo_externo.csv` (mismas columnas que
`catalogo_medido.csv` + fuente, licencia, atribución, url, nivel_editor, medida)
y `corpus_abierto.parquet` (texto + atribución al final). **Aborta** si llega un
texto con licencia no libre. Ids: `SWV<id>`, `ASB<nnnn>`, `VOA<num>`.

## 4 bis. Cómo se abren en la app (commit c3932ac)

- `app/catalogo.py` añade `catalogo_externo.csv` **al final** del medido (sin
  duplicar ids) y lleva **dos archivos de embeddings**: `catalogo_emb_<huella>.npy`
  (Gutenberg, 82 MB, ya publicado) y `catalogo_emb_ext_<huella>.npy` (externo).
  Cambiar el externo recodifica solo sus filas. **Trampa:** el glob de limpieza de
  Gutenberg (`catalogo_emb_*`) también casa con los del externo; hay una guarda.
- `es_abrible(id)`: `PG…` o presente en `corpus_abierto.parquet`. `texto_abierto(id)`.
- `app/ui.py`: `_abrible()` sustituye a los `startswith("PG")`; `_descargar_gutenberg`
  escribe el texto libre como `<id>.txt` local sin red; `_esta_cacheado` ya no busca
  los dígitos de `SWV369` entre los `pg369` de Gutenberg; `_abrir` reconoce
  `swv|asb|voa|lrd` como ids del catálogo y pone el título en la cabecera.
- Pruebas: `pruebas_corpus.py` (10). Mutantes: `C3-*` en `tools/banco_mutantes.py`,
  suite `pruebas_corpus.py`.
- Despliegue: `catalogo_externo.csv` y `corpus_abierto.parquet` están en la lista
  blanca; el `.npy` del externo se sube a mano con `upload_file`.

## 5. Trabajar con otras sesiones a la vez

Varias sesiones de Claude Code comparten **la misma carpeta**: `git pull --rebase`
no protege nada. Reglas que funcionaron:
- Repartir archivos por mensaje (`SendMessage`) antes de empezar.
- Nunca `git add -A` ni `commit -a`: solo rutas explícitas.
- Pruebas nuevas en un archivo propio (`pruebas_corpus.py`) si otra sesión está
  editando `pruebas_extremas.py`.
- Al matar un proceso por su línea de comandos desde bash, el patrón coincide con
  el propio shell y lo mata también (exit 255): filtra por `Name -like 'python*'`.
- **Commitear solo tu parte de un archivo compartido** (sin `git add -p`, que no
  hay modo interactivo): `git diff -U3 archivo`, filtrar los hunks por la función
  del encabezado `@@`, `git apply --cached --check` y `git apply --cached`, y
  **compilar `git show :archivo` antes del commit**. Con `-U0` y
  `--unidiff-zero` una inserción cayó en otra línea y el índice no compilaba.
- La herramienta Edit falla con «modified since read» si otra sesión tocó el
  archivo: relee la zona y edita en la misma respuesta.

## 6. Auditores externos esta noche

- **Codex**: antes del encargo, una llamada mínima
  (`codex exec --skip-git-repo-check --sandbox read-only "Responde solo: ok"`)
  para ver si hay cupo; ya gasta ~13 mil tokens por el contexto. Encargo estrecho,
  a ciegas, solo lectura, `-c model_reasoning_effort="medium"`, y el informe por
  la salida estándar (no darle escritura: hay otras sesiones en la carpeta).
- **Fable** (subagente `model: fable`): para lo que Codex no mira —método y
  estadística—, también a ciegas y de solo lectura.
