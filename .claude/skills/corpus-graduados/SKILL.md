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

### Lo que se aprendió al medirlas (13 sep 2026)

- **StoryWeaver valida** (0,426 [0,348; 0,502]; parcial sin longitud 0,206
  [0,111; 0,295]). **African Storybook** gradúa sobre todo por longitud (0,81) y
  la parcial no es distinguible de cero. **Let's Read no valida** (0,178): más de
  la mitad son traducciones que **heredan el nivel del original** en otro idioma
  (ρ = 0,023 en traducciones, 0,207 en originales). No promediar las tres.
- **La misma obra está en varias bibliotecas** con niveles distintos: «The Red
  Raincoat» es nivel 1 en StoryWeaver y 2 en Let's Read, con el mismo texto. En el
  catálogo salía dos veces: `catalogar_corpus.py` deduplica por título y autor
  (StoryWeaver > African Storybook > Let's Read > VOA).
- **StoryWeaver:** hay slugs con letras no ASCII; sin `urllib.parse.quote` la
  descarga reventó en el libro 2.584 con `UnicodeEncodeError`.
- **Let's Read:** 13 libros CC BY 3.0 quedaron internos porque el descargador solo
  aceptaba 4.0; son libres y podrían entrar.
- **Documento LaTeX:** al añadir la tabla `cuad:graduados`, `TeX capacity exceeded
  [input stack size]` en el pie. No se identificó la macro exacta: se resolvió
  volviendo al texto de cabecera y pie que ya compilaba y cambiando **solo** el
  ancho con `\resizebox`. Ante un error así, diff mínimo contra la última versión buena.

### Descartadas
- Global Digital Library: la API (`api.digitallibrary.io`) no responde.
- UniversalCEFR `elg_cefr_en` y `cambridge_exams_en`: **son el corpus de
  entrenamiento del v4**. Validar con ellos es fuga.

## 3. Cómo se mide con el v4

- **Páginas en párrafos antes de nada.** Un libro ilustrado trae una frase por
  renglón y el filtro de prosa lo toma por lista: 70 de 219 unidades rechazadas.
  Unir cada página en un párrafo las dejó en 9.
- **Cuentos cortos (decisión de Miguel):** al VALIDAR, ≥250 palabras solos; los
  demás, en bloques de ≥250 **sin mezclar fuente ni nivel**. La cola corta se
  declara, no se estira. Al CATALOGAR el corte para medir solo es 150
  (`scoring.MIN_WORDS`); ver §4 ter.
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

## 4 ter. StoryWeaver entero en el catálogo (14 sep 2026)

Resultado: `catalogo_externo.csv` pasó de 3.919 a **15.357** filas (StoryWeaver
14.500, Let's Read 326, African Storybook 278, VOA 253) y la app, a 68.536
libros. Todo gratis, en CPU local. Lo que hay que saber para repetirlo:

**Medir en local por shards, no de un tirón.** `tools/medir_corpus.py` guarda
cada unidad medida en `corpus_graduado/medidas/medidas_NNNN.jsonl`, de 250 en
250, con una **clave del contenido** (sha256 de tipo + ids + texto). Reanudar
lee lo hecho del disco, no un contador. `--tope N` mide N y da la ETA.
- Velocidad real en esta CPU (torch solo CPU; la GTX 1650 no se usa sin torch
  con CUDA): 3,8–5,3 ventanas/s y unas 70–120 unidades/min. 12.800 unidades
  tardaron unas 2 h. Las pruebas en paralelo la frenan, pero no rompen nada.
- **El reparto importa y va en orden:** 1) cada texto con ≥150 palabras
  (`scoring.MIN_WORDS`) se mide solo; 2) los cortos **y los que el filtro de
  prosa rechazó solos** se agrupan en bloques de ≥250 palabras de su fuente y
  nivel, en orden de id. Por eso los bloques no se forman hasta que la primera
  pasada está completa.
- Cierre en un comando: `tools/cerrar_corpus.py`. Para si falta algo por medir,
  cataloga, compara con el catálogo anterior (filas, fuente, letra), pasa
  `pruebas_corpus` y hace `--seco`. Su último paso deja de ser útil si los CSV
  aún no tienen commit, porque el desplegador compara bytes del commit.
- **Los 894 que quedan fuera, y por qué** (recontado por 4e): 776 tienen <150
  palabras; 878 cayeron en uno de los 260 bloques que el filtro de prosa del v4
  rechazó (215 «lista, menú o tabla», 32 por frases, 13 con <4 frases); de los
  16 restantes, 15 no llegaron a formar bloque y 1 se midió solo, lo rechazó el
  filtro y no llegó a bloque. Cita la línea de salida literal y el desglose,
  no una explicación de memoria: la primera que di aquí estaba mal.
- Los 48 de StoryWeaver bajados por popularidad **entran** al catálogo. Solo se
  apartan al VALIDAR.

**Lo que se mide y lo que se enseña no son lo mismo.**
- `corpus_abierto.parquet` lleva la **atribución en español al final** (CC BY
  la exige). Medida con el cuento, esa línea con URL lo subía: «Doggie is Happy»
  (SWV229485) daba 0,349 en «¿Cómo de difícil es?» y 0,007 en el catálogo. Todo
  lo que puntúa usa `ficha.para_medir(texto)` (sin licencia de Gutenberg y sin
  el último párrafo de atribución); lo que se enseña sigue con ella. Si se
  arregla después de que se guardaran curvas, **borra las curvas de ids no PG**
  del bucket (`analisis/*.json` cuyo `titulo` es swv|asb|lrd|voa…txt), no las
  sinopsis.
- **Limpieza del texto servido, nunca del medido.** `catalogar_corpus.limpiar_para_servir`
  quita U+FEFF, un párrafo idéntico al anterior y un párrafo que es la misma
  página dos veces (cada mitad con ≥12 palabras y ≥2 frases). Los estribillos de
  una frase y la repetición no consecutiva **se quedan**: en cuentos infantiles
  es a propósito. Limpiar antes de medir cambiaría la clave y obligaría a volver
  a medir. Comprobación: regenerar sin medir y que `catalogo_externo.csv` salga
  **idéntico byte a byte**. Cambiaron 1.442 textos servidos (1.257 solo U+FEFF).
  La columna `palabras` sigue contando el texto medido.

**En la app.**
- **Medido en bloque:** un cuento corto toma la dificultad de su bloque. La
  tarjeta y la ficha llevan `medido_en_bloque` (contrato con e6) para no
  presentarla como suya.
- **Intercalado en «Sorpréndeme»** (decisión de Miguel): los libres no tienen
  descargas y por popularidad salían del puesto 20 en A2 y nunca en B1. Si hay
  libres en la franja, ocupan los puestos 2, 5, 8… (un tercio); el resto va por
  descargas; un título con aviso de contenido sigue fuera de los 5 primeros.
  **Ordénalos por cercanía al nivel del lector** y, a igual distancia, primero
  los medidos solos. Por id empataban y A2 y B1 veían los mismos tres cuentos.
- **Rendimiento:** `isin` contra un índice de texto de arrow recorre en Python
  sus 15.357 ids en cada llamada (0,22 s por recomendación). Con un frozenset
  cacheado son 3 ms.
- Pruebas: `pruebas_corpus.py` (25 al cierre del 14 sep, con una prueba sobre el
  catálogo real y otra con el modelo para Doggie). Mutantes `C3-*`.

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
