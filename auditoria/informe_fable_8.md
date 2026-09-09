# Octava auditoría — Fable, 9 de septiembre de 2026, tarde

Estado auditado: HEAD `425750f` («lo que la correccion de 46->47 no toco»),
árbol de trabajo limpio. Se leyeron `git log`/`git diff ff80c21..HEAD` enteros
y los dos informes que provocaron esos cambios (`verificacion_cifras.md`,
`coherencia_entregables.md`). No se abrió ningún informe anterior de Fable ni
de Codex. No se modificó ningún archivo del proyecto; la única escritura es
este informe.

## Recuento

| Gravedad | Hallazgos |
|---|---|
| **CRÍTICO** | **1** |
| **SERIO** | **3** |
| **MENOR** | **11** |
| **DUDA** | **1** |
| **Total** | **16** |

**Respuesta a la pregunta D — ¿queda algo que avergonzaría al autor si lo lee
un profesor universitario?: sí.** Cuatro cosas, por orden: (1) la tarjeta del
modelo que está publicada en Hugging Face lleva tres cifras que el propio
documento ya declara equivocadas (0,548 · 1,248 · 0,854); (2) el pie del
Cuadro 16 del PDF habla de «tres restas» debajo de una tabla que tiene dos;
(3) el cuadernillo dice «0,504 frente a 0,548» treinta líneas después de
imprimir 0,5561; (4) la primera página del PDF cuenta «cuatro escalones
siguientes» cuando, quitado el A1–A2, quedan tres.

**Respuesta a la pregunta A — ¿alguna corrección de hoy inventó, exageró o
rompió algo?: no inventó ni exageró; sí dejó tres cifras derivadas sin
recalcular** (hallazgos 2, 4 y 5) y no subió al Hub la tarjeta que corrigió
(hallazgo 1). Las cifras nuevas se reproducen todas; la lista de lo verificado
va al final.

---

## CRÍTICO

### 1 · La tarjeta del modelo publicada en Hugging Face es la de hace dos correcciones

- **Dónde:** `https://huggingface.co/MikeMaki1763/literalevel-v4/raw/main/README.md`,
  líneas 78 y 91–92 de la copia descargada (guardada en el scratchpad de esta
  sesión). `lastModified` del repo según la API del Hub:
  `2026-09-09T01:15:47Z` (8 de septiembre, 19:15 hora local). La copia local
  `modelo_v4/README.md` se corrigió hoy a las 12:27 (`git log`: `f40af8e`) y
  **no se volvió a subir**.
- **Qué dice (publicado):**
  `| **Media (0–2)** | 0,504 | 0,548 | 0,928 | 1,248 | 1,495 |` y
  «Contar palabras sin modelo alguno alcanza 0,807 en el corpus de British
  Council, donde este modelo da **0,854**».
- **Qué dice (local, `modelo_v4/README.md:85` y `:99`):**
  `0,504 | 0,556 | 0,928 | 1,241 | 1,495` y «donde este modelo da 0,860».
  Además la versión publicada **no tiene** el aviso de las líneas 72–78
  locales («Las 144 parejas de etiqueta y predicción no están publicadas»).
- **Por qué:** es el único artefacto público del proyecto aparte del Space, y
  el documento lo cita como el modelo entregado. El profesor que abra el enlace
  lee `1,248` (dos correcciones de retraso: 1,2478 → 1,2414), `0,548`
  (n=7, hoy n=8 y 0,5561) y `0,854`, que no es siquiera el 0,855 anterior a
  hoy. Tres cifras distintas del PDF para los mismos tres datos.
  `diff` completo local↔Hub: sólo esas dos líneas y el bloque del aviso.
- **Arreglo:** subir `modelo_v4/README.md` al repo del modelo
  (`desplegar_datos.py:81` ya hace `upload_folder` de la carpeta; basta con
  ejecutarlo o con `api.upload_file` del README solo). Al subirlo, cerrar de
  paso el B5 de `coherencia_entregables.md`: en `:99` decir «da 0,860 sobre
  los 47 textos locales» para que no choque con el 0,829 (38 textos) de la
  tabla de `:70`.

---

## SERIO

### 2 · El pie del Cuadro 16 del PDF describe tres restas; la tabla tiene dos

- **Dónde:** `entrega/documento.tex:1723–1724` → `documento.pdf`, pie del
  Cuadro 16 (texto extraído con `pypdf`: «Cuadro 16: De 59 a 47, paso a paso.
  Las dos primeras restas son de extracción; la tercera es el filtro de prosa
  continua»).
- **Qué dice:** «De 59 a 47, paso a paso. Las dos primeras restas son de
  extracción; la tercera es el filtro de prosa continua.»
- **Por qué:** el commit `f40af8e` quitó la fila «menos: no disponible −1»
  (`documento.tex:1717` en la versión anterior) y corrigió el párrafo de
  abajo (`:1742`: «La primera resta es de extracción. La segunda no»), pero
  **no tocó el pie**. Quedan dos filas de resta (−2 y −10) y un pie que
  cuenta tres. El `.md` no tiene este pie (`documento.md:726`: «*Cuadro 11. De
  59 a 47, paso a paso.*»), así que la contradicción está sólo en el
  entregable. Es exactamente el patrón que el encargo pide vigilar: la
  corrección de hoy introdujo la incoherencia.
- **Arreglo:** «La primera resta es de extracción; la segunda es el filtro de
  prosa continua.» Y recompilar.

### 3 · El cuadernillo dice «0,504 frente a 0,548» debajo de una celda que imprime 0,5561

- **Dónde:** `entrega/notebook_proyecto.py:1751` y `:1984`;
  `entrega/notebook_proyecto.ipynb:2188` y `:2459` (idénticos: comprobado que
  las 92 celdas del `.ipynb` coinciden con el `.py`).
- **Qué dice:** «**A1 y A2 casi no se distinguen** (0,504 frente a 0,548), y
  A1 tiene tres textos» · «A1 y A2 son prácticamente indistinguibles (0,504
  frente a 0,548, con n = 3 en A1)».
- **Por qué:** la celda de código de `:1702` ya dice
  `[0.5040, 0.5561, 0.9276, 1.2414, 1.4952]` y `:1704` imprime «47 textos
  legibles en local». La prosa que comenta esa salida sigue con la media
  vieja. Estaba señalado como **A5** en `coherencia_entregables.md:122–131` y
  el commit `425750f` no lo cerró. El cuadernillo es entregable de rúbrica y
  el profesor lo lee de arriba abajo.
- **Arreglo:** «0,504 frente a 0,556» en los dos sitios, y regenerar el
  `.ipynb`.

### 4 · «A2 se desvía 0,10» ya no sale de las medias publicadas

- **Dónde:** `entrega/documento.md:723` y `:750`; `entrega/documento.tex:1704`
  y `:1739` (las dos en el PDF); `README.md:112`; comentario de
  `validar_local.py:57`.
- **Qué dice:** «C1 coincide hasta la tercera cifra decimal —1,4952 frente a
  1,4950—, A2 se desvía 0,10» · «aquella tanda son 38 textos y A2 se desvía
  0,10».
- **Por qué:** con la media vieja, 0,6479 − 0,5480 = 0,0999 → 0,10
  (`verificacion_cifras.md:67–68` lo comprobó). Con la de hoy,
  **0,6479 − 0,5561 = 0,0918 → 0,09**. Es una cifra derivada de la que cambió
  y nadie la recalculó. No cambia ninguna conclusión, pero está dos veces en
  el PDF y una en el README, y es aritmética que un lector puede rehacer con
  el Cuadro 15 delante.
- **Arreglo:** «A2 se desvía 0,09» en los seis sitios.

---

## MENOR

### 5 · La flecha de la figura de compresión sigue apuntando a 0,548

- **Dónde:** `entrega/documento.tex:1851` (flecha) y `:1844` (etiqueta «A2»).
- **Qué dice:** `(axis cs:0.4,0.40) -- (axis cs:0.4,0.548);` y
  `at (axis cs:0.42,0.545) {A2}`; el punto dibujado en `:1840` es
  `(0.4,0.5561)`.
- **Por qué:** señalado como **A7** en `coherencia_entregables.md:139–153`; el
  commit de hoy actualizó el punto y no la flecha. La diferencia (0,008) no se
  ve a simple vista, pero está dibujado en el PDF con el valor viejo.
- **Arreglo:** `0.5561` en la flecha, `0.553` en la etiqueta.

### 6 · «Los cuatro escalones siguientes, no» — son tres

- **Dónde:** `entrega/documento.md:50–51`; `entrega/documento.tex:251` (PDF,
  primera página); `entrega/presentacion.tex:241–242` («los otros cuatro,
  no»).
- **Qué dice:** «el escalón A1–A2 es de 0,052 … Está dentro del ruido. Los
  cuatro escalones siguientes, no.»
- **Por qué:** cinco niveles (A1…C1) tienen cuatro escalones; descontado el
  A1–A2 quedan A2–B1, B1–B2 y B2–C1: tres. Señalado como **D2** en
  `coherencia_entregables.md:400–410`, no cerrado. Es la frase que introduce
  el resultado principal en el Resumen.
- **Arreglo:** «Los tres escalones siguientes, no» / «los otros tres, no».

### 7 · Frase rota en el PDF: «reproduce las el cuadro 15»

- **Dónde:** `entrega/documento.tex:1736–1737` → PDF («…porque es la que
  reproduce las el cuadro 15 de este documento»).
- **Qué dice:** «Se conserva la unión con espacio porque es la que reproduce
  las el cuadro~\ref{cuad:validacion} de este documento».
- **Por qué:** **D1** de `coherencia_entregables.md`, no cerrado. El `.md`
  (`documento.md:748`) lee bien.
- **Arreglo:** quitar «las».

### 8 · README: «Tres preguntas» cuando la app hace seis y tres fragmentos

- **Dónde:** `README.md:21`.
- **Qué dice:** «**Sitúa al lector.** Tres preguntas, o midiendo un texto que
  ya lee cómodo.»
- **Por qué:** `app/perfil.py`: `len(PREGUNTAS) == 6`, `len(FRAGMENTOS) == 3`
  (ejecutado). El documento (`documento.md:846`) y el guion dicen «seis
  preguntas … tres fragmentos». **A13** de `coherencia_entregables.md`, no
  cerrado.
- **Arreglo:** «Seis preguntas y tres fragmentos, o midiendo un texto…».

### 9 · README titula con las medias de Colab, sin decirlo y sin A1

- **Dónde:** `README.md:83–84` frente a su propia tabla en `README.md:105–109`.
- **Qué dice:** «en corpus externo las medias por nivel quedan estrictamente
  ordenadas: A2 0.648 < B1 0.951 < B2 1.288 < C1 1.495».
- **Por qué:** son la columna «Colab» (0,6479 / 0,9513 / 1,2883 / 1,4950) de
  la tabla de veinte líneas más abajo, no las locales que titulan el PDF y la
  presentación (0,5040 · 0,5561 · …). **A14**, no cerrado.
- **Arreglo:** poner las cinco locales, o decir «en la tanda de Colab (38
  textos)».

### 10 · Dos citas al «documento principal» usan la numeración del `.md`, no la del PDF

- **Dónde:** `entrega/estrategia.md:182`; `README.md:119`.
- **Qué dice:** «Cuadro 15 del documento principal: 8,19 ventanas/s en CPU…»
  · «las tres cifras del Cuadro 12 (modelo 0,860…)».
- **Por qué:** en el PDF (numeración contada sobre el texto extraído) el
  Cuadro 15 es la validación externa y el de velocidad es el **Cuadro 20**;
  el del *baseline* es el **Cuadro 17**, no el 12. **C3**, no cerrado.
- **Arreglo:** «Cuadro 20 del PDF (Cuadro 15 del `.md`)» y «Cuadro 17 del
  PDF (Cuadro 12 del `.md`)».

### 11 · Docstring de `app/scoring.py` con medias de hace dos correcciones

- **Dónde:** `app/scoring.py:113–114`.
- **Qué dice:** «medido con las medias reales de `validar_local.py`: A1 0,504
  → basico · A2 **0,548** → basico · B1 0,928 → intermedio · B2 **1,248** →
  intermedio».
- **Por qué:** dice «medias reales de `validar_local.py`» y son las de antes
  de ayer (1,248 = 1,2478). El argumento del docstring (qué banda le tocaba a
  cada nivel con los cortes viejos) no cambia con 0,556 / 1,241, pero la
  atribución es falsa.
- **Arreglo:** `0,556` y `1,241`.

### 12 · `investigacion/competencia.md`: margen «0,047» y medias viejas

- **Dónde:** `investigacion/competencia.md:216`, `:439` y `:220`.
- **Qué dice:** «el margen sobre la señal trivial es de 0,047» · «compran
  0,047 de Spearman» · «(0,504 · 0,548 · 0,928 · 1,248 · 1,495)».
- **Por qué:** el mismo archivo se corrigió hoy a 0,807 / 0,860 (`:215`,
  `:437`), y 0,860 − 0,807 = **0,053**. Las medias de `:220` son las de dos
  correcciones atrás. No es entregable, pero está en el repositorio que se
  entrega.
- **Arreglo:** «0,053» y «0,504 · 0,556 · 0,928 · 1,241 · 1,495».

### 13 · Tres cifras distintas para «modelo + diccionario» en disco

- **Dónde:** `AGENTS.md:92` («562 MB (modelo 328 + diccionario **233** + CSV
  0,9)»); `PENDIENTES.md:89` («Modelo + diccionario | **571 MB** |
  `os.path.getsize`»); `DESPLIEGUE.md:20` y `:92`, `desplegar_datos.py:3`,
  `entrega/notebook_proyecto.py:1922` («**575 MB**»).
- **Por qué:** medido: `model.safetensors` 328,49 MB + `kaikki_diccionario.db`
  243,33 MB = **571,8 MB**; la carpeta `modelo_v4/` entera + db = 575,4 MB. El
  «233» de `AGENTS.md` es un error (el diccionario son 243). El 571 de
  `PENDIENTES.md` dice «`os.path.getsize`» y la suma real de los dos ficheros
  redondea a 572. Hoy se pasó a 575 en cuatro archivos y no en éste.
- **Arreglo:** una sola cifra (575 MB, lo que se sube) en `PENDIENTES.md:89` y
  `AGENTS.md:92`, y «243» en `AGENTS.md`.

### 14 · `DESPLIEGUE.md` termina en un encabezado vacío y sigue condicional

- **Dónde:** `DESPLIEGUE.md:127` (última línea del archivo: «## Lo que ya no
  hace falta resolver (continuación)», sin cuerpo); `DESPLIEGUE.md:119`
  («Así que **si se despliega**, hay que montar almacenamiento»).
- **Por qué:** la cabecera (`:3–9`) ya dice que está desplegado (**B1**
  cerrado), pero el cuerpo conserva el condicional y el encabezado huérfano
  (**D3**, cerrado a medias).
- **Arreglo:** borrar `:127`; «Está desplegado, así que hay que montar
  almacenamiento».

### 15 · Instrucción de chat dentro del guion `.md`

- **Dónde:** `entrega/guion_video.md:30–31`.
- **Qué dice:** «Si tienes el libro y quieres que el guion se reescriba sobre
  esa estructura, dímelo y lo rehago.»
- **Por qué:** es una frase dirigida al autor por quien escribió el archivo,
  no forma parte del guion. **E3**, no cerrado. El `.tex`/PDF no la lleva.
- **Arreglo:** quitarla.

---

## DUDA

### 16 · La descripción del Space no se comprobó

- **Dónde:** `https://huggingface.co/spaces/MikeMaki1763/literalevel`
  (README del Space, si lo tiene).
- **Por qué:** el hallazgo 1 demuestra que lo publicado en el Hub puede ir por
  detrás del repositorio. No se descargó el README del Space, así que no se
  sabe si repite alguna cifra. Se deja como duda, no como hallazgo.

---

## Lo verificado y correcto

Todo lo que sigue se ejecutó o se recalculó en esta sesión; se lista para que
se sepa qué se revisó y no sólo qué falló.

**Suites, tal cual las pide el encargo** (todas con `python -X utf8`):

| Guion | Resultado |
|---|---|
| `validar_local.py` | `VALIDACION CORRECTA: 47 textos, 5 niveles, medias estrictamente crecientes.` A1 3 / 0,5040 / 0,111 · A2 8 / 0,5561 / 0,223 · B1 12 / 0,9276 / 0,198 · B2 12 / 1,2414 / 0,236 · C1 12 / 1,4952 / 0,172. Sin cuerpo: 2. Filtro completo: **31**. Fallidos: 10 (9 `A1__`, 1 `B1__`, los diez «al menos 150 palabras»). Cuadro 12: **0,860 / 0,807 / 0,668**, modelo contra longitud **0,732**, contador parcial «indefinida». Exit 0 |
| `pruebas_extremas.py` | «Las 205 pruebas extremas pasan». Exit 0 |
| `pruebas_integracion.py` | «Los 27 pasos del recorrido encadenan bien». Exit 0 |
| `tests_smoke.py` | «TODO OK». Exit 0 |
| `pruebas_ficha.py` | «Todas las pruebas de la ficha pasan». Exit 0 |

**Recuento propio del corpus, sin el modelo** (copiando `cuerpo`,
`cuerpo_estricto` y `RE_NIVEL` de `validar_local.py` y llamando a
`scoring.continuous_prose`): 59 PDF casan con `*LearnEnglish?Reading*.pdf`
(A1 12 · A2 10 · B1 13 · B2 12 · C1 12); el manifiesto lista 59 nombres y
los 59 existen en disco; pasan el filtro flojo 3 · 8 · 12 · 12 · 12 = 47;
pasan el estricto 1 · 4 · 6 · 10 · 10 = **31**, con **A1 en 1**; los dos A1
que pasan el flojo y no el estricto caen por `maquetado_de_lista`
(`Dictionary-definitions`, `Job-adverts`). Coincide con `documento.tex:1737`
(«A1 se queda con uno solo») y `:1754` («dos de los tres caen por maquetado de
lista»).

**Figura de validación:** `datos_figuras/validacion.dat` = `A1 3 0.5040 0.111 ·
A2 8 0.5561 0.223 · B1 12 0.9276 0.198 · B2 12 1.2414 0.236 · C1 12 1.4952
0.172`; idéntico al Cuadro 10 de `documento.md:701–705`, al `documento.tex:1636–1640`
y a las etiquetas del TikZ `documento.tex:1678–1682` (n = 3, 8, 12, 12, 12 =
**47**); el texto extraído del PDF trae «n = 3 n = 8 n = 12 n = 12 n = 12» en
la figura y ningún «n = 7» ni «n = 11». El `.dat` se modificó a las 12:27 y el
PDF se compiló a las 12:28.

**Escalón A1–A2:** 0,5561 − 0,5040 = **0,0521** → «0,052» (`documento.md:49`,
`.tex:250`); desviaciones «0,111 y 0,223» = las del Cuadro 10.

**`app/ficha.py::_es_boilerplate`** (cambio `cd26805`), once casos fabricados
con `SimpleNamespace(titulo, texto, palabras)`:

| Caso | Resultado | Correcto |
|---|---|---|
| `.txt` entero: cabecera de Gutenberg + ~1.000 palabras de prosa + licencia («Texto completo») | False | sí (era el fallo: antes se descartaba) |
| Sólo la licencia final, con título «License» / sin título | True / True | sí |
| Prosa limpia, 1.440 palabras | False | sí |
| Prosa larga (7.200) que menciona «Project Gutenberg» una vez | False | sí |
| Portadilla sola (108 palabras) | True | sí |
| Prosa de 100 palabras | True | aceptable (< 150 reales) |
| Cabecera + 120 palabras de prosa | True | sí (< 150 reales) |
| Cabecera + 400 palabras de prosa, sin marca de fin | False | sí |
| Licencia sin asteriscos («End of Project Gutenberg's …») | True | sí |
| Capítulo XII de Alicia: 2.000 de prosa + licencia entera pegada | False | sí (se corta dentro, no se tira el capítulo) |

Sigue descartando la licencia y ya no descarta la prosa.

**PDF contra `.tex`** (`pypdf`): `documento.pdf` (43 pp.) compilado 12:28:34,
`.tex` guardado 12:27:13; `presentacion.pdf` 12:28:40 sobre `.tex` de 12:18;
`guion_video.pdf` 12:28:45 sobre `.tex` de 10:50. `documento.pdf` contiene
0,860 (×4), 0,807 (×3), 0,668 (×2), 0,732, 0,5561 (×4), 0,052, 0,223, «31
textos», «47» (×13), «1.500 millones»; **no contiene** 0,855, 0,799, 0,665,
0,5480, 0,548, 1,248, 0,044, 0,237, «30 textos», «no disponible», «n=7»,
«n=11», «Cientos de millones». Los tres «0,725» del PDF son el Pearson del LLM
*zero-shot* en CLEAR (`documento.tex:2301`, `:2332`, `:2338`), no el
modelo-contra-longitud; los dos «46» son la exactitud 0,46 de roberta-base.
`presentacion.pdf` contiene 0,860 / 0,807 / 0,668 / «47 textos» / «A2 0,556 …
B2 1,241». `guion_video.pdf` no lleva ninguna cifra afectada por el cambio
(sólo «1.500 millones», ahora coherente con el documento).

**Cuadernillo:** `notebook_proyecto.ipynb` ≡ `notebook_proyecto.py` (92
celdas, primera línea de cada celda localizada en el `.py`); `:244` «47
legibles», `:1701–1704` n = 8 y 0,5561, `:1918–1922` accionable 3 reescrito
con el despliegue hecho y 575 MB.

**Cierres de `coherencia_entregables.md` confirmados:** A1, A2, A3, A4 (en
local), A6 (último «46»), A8 (552 → 553: contadas 553 palabras entre «»
en `guion_video.md`), A9 (562 → 575 en el cuadernillo), A11 (ocho pestañas:
`app/ui.py` tiene 8 `gr.Tab`), A12 (1.500 millones en documento, guion y
cuadernillo), B1 y B2 (despliegue hecho en `DESPLIEGUE.md:3` y cuadernillo),
C1 (cabecera del `.md` explica dónde vive la Estrategia). Sin cerrar: A5, A7,
A13, A14, B4-en-el-Hub, B5, C3, D1, D2, D3 (a medias), E3 — todos recogidos
arriba.

**Otras cifras contrastadas y coherentes en todos los archivos donde
aparecen:** 59 · 2 · 10 · 47 · 31 · 38 · 0,829 · 0,908 · 97,2 % · 144 · 654 ·
0,7196x + 0,3760 · 0,67x + 0,41 · 205 · 27 · 40 · 4,53 · 3,11 · 328 MB · 243 MB
· 31 s · 7 USD/mes · 553 palabras · 3:41.
