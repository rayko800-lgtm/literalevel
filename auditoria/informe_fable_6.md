# Informe Fable 6 — ¿las correcciones son correctas, y rompieron algo?

Fecha: 9 de septiembre de 2026. Árbol de trabajo en HEAD `6494c08` («cerrar la
lista de auditoria: lo corregido, medido antes de escribirlo»), sin cambios sin
confirmar. Se leyó `cierre_2026-09-09.md` como declaración de parte, después
`informe_fable_5.md`, después el diff completo del commit, y **cada cifra del
cierre se volvió a medir en esta máquina**: se ejecutaron `pruebas_extremas.py`,
`pruebas_integracion.py` y `validar_local.py`, se recalculó el contraste WCAG
sobre `app/paletas.py`, se midieron los tamaños con `os.path.getsize`, se
consultó la API de Hugging Face, se comparó el manifiesto con la carpeta real y
se cronometró el vistazo sobre prosa real. No se modificó ningún archivo del
proyecto: este informe es la única escritura.

**Recuento: 1 CRÍTICO · 5 SERIOS · 6 MENORES · 3 DUDAS.**
**Del informe 5: los 2 críticos, los 5 serios y los 6 menores están cerrados.
Del inventario de 34 abiertos: 30 cerrados, 1 cambiado a peor (#10, que es el
crítico de aquí), 1 cerrado a medias (#6), 2 abiertos y declarados (#27, #38).**

---

## A. ¿Alguna corrección inventó algo?

Sí, una. Y dos afirmaciones nuevas se escribieron sin medir.

### CRÍTICO

**C1. La procedencia añadida a la recta `0,72 × real + 0,38` no reproduce la
recta.**
- Dónde: `entrega/documento.md:760-761` y `:994-995`.
- Qué dice: «el ajuste ronda `predicho ≈ 0,72 × real + 0,38` —**mínimos
  cuadrados sobre las cinco medias por nivel de la validación local**, no sobre
  los textos uno a uno—».
- Por qué: se hizo el cálculo. Las cinco medias locales son las del Cuadro 10
  (`datos_figuras/validacion.dat`: 0,5040 · 0,5480 · 0,9276 · 1,2478 · 1,4952) y
  el eje que usa la propia figura de compresión es A1 = 0,0 … C1 = 1,6
  (`documento.tex:1794-1798`). Mínimos cuadrados sobre esos cinco puntos dan
  **pendiente 0,671 y ordenada 0,408**, con cualquier codificación del eje la
  pendiente es 0,671. Lo que sí da **0,7196 x + 0,376** es el ajuste sobre las
  **cuatro medias de Colab** (A2–C1: 0,6479 · 0,9513 · 1,2883 · 1,4950, en
  0,4 … 1,6), es decir, sobre los 38 textos de la tanda original, no sobre los
  45 locales. El hallazgo #10 del inventario pedía decir de dónde sale la recta;
  la corrección le puso una procedencia que no es la suya. Es el mismo pecado del
  286: rellenar un hueco con una explicación plausible en vez de con la medida.
- Agravante: la nota **solo está en el `.md`**. `documento.tex:1759` y `:2334`
  siguen sin procedencia y el PDF no contiene «mínimos cuadrados» (comprobado
  con `pypdf`). Los dos archivos vuelven a decir cosas distintas.
- Arreglo: o se dice la verdad («ajuste sobre las cuatro medias A2–C1 de la
  tanda de Colab; sobre las cinco medias locales sale 0,67x + 0,41») o se
  recalcula y se publica la recta local en los cuatro sitios (`.md`, `.tex`,
  figura `documento.tex:1801` y `app/scoring.py:108`).

### SERIO

**S1. «Por debajo del segundo» es una cifra nueva, no medida, y aquí no sale.**
- Dónde: `entrega/documento.md:638-640`, `entrega/documento.tex:1564-1566`.
- Qué dice: «con un tope de **ocho ventanas por documento** […]: es lo que
  mantiene el análisis por debajo del segundo en una CPU».
- Por qué: medido en esta máquina (la misma Ryzen 5 2600 de `scoring.py:187`
  y del Cuadro 14), `Puntuador.puntuar()` sobre prosa real con sus 8 ventanas
  tarda **0,98–1,01 s** en un capítulo de 2.148 palabras y **1,08–1,21 s** en un
  libro de 26.547 palabras (cinco repeticiones cada uno, tras calentar). Cuadra
  con el propio Cuadro 14: 8 ventanas a 6,96–8,19 ventanas/s son 0,98–1,15 s, y
  eso sin contar el troceado. La aplicación lo etiqueta con más honestidad:
  «Vistazo rápido (unos segundos)» (`estrategia.md:131`). No está en la tabla
  «Lo que se midió antes de escribirlo» del cierre, y es justo el tipo de frase
  que la tanda decía haber desterrado.
- Arreglo: «en torno a un segundo en una CPU de escritorio» o dar la medida.

**S2. «Sin nivel en el nombre del archivo» es falso: el archivo se llama
`B2__…Reading-B2_Work-life-balance.pdf`.**
- Dónde: `README.md:99-100`, `entrega/documento.md:716` (Cuadro 10b),
  `entrega/documento.tex:1708`, `entrega/manifiesto_corpus_externo.md:15` y
  `:93-95` (encabezado «Sin nivel en el nombre (1)» seguido del nombre con dos
  «B2»), y `cierre_2026-09-09.md:26`.
- Por qué: el nivel está en el nombre dos veces. Lo que pasa es que
  `validar_local.py:24` usa `\b(A1|A2|B1|B2|C1|C2)\b` y en ese nombre las dos
  «B2» van seguidas de guion bajo, que es carácter de palabra: `\b` no casa. Es
  un defecto del guion, no del archivo. Y no es inocuo: extraído con la misma
  función `cuerpo()`, ese PDF tiene **556 palabras de cuerpo, pasa el filtro de
  prosa y el modelo lo puntúa 1,19** (B2 real, predicción en la banda
  intermedia-alta, coherente con la media B2 de 1,2478). Con él la validación
  local son **46 textos**, B2 tiene n = 12 y su media baja a ≈ 1,243; el orden
  estricto se conserva (0,9276 < 1,243 < 1,4952), así que la conclusión no
  cambia, pero el «45» del Cuadro 10, el «−1» del Cuadro 10b y los tres
  decimales de B2 y del Cuadro 11 son artefactos de un regex. El profesor que
  abra el manifiesto ve el «B2__» en la primera línea de la sección «sin nivel».
- Arreglo: corregir el regex (`[_\-]` alrededor, o `re.search(r"(A1|A2|B1|B2|C1|C2)", …)`),
  rehacer `validar_local.py` con 46 y actualizar Cuadros 10, 10b y 11 en los
  cuatro archivos; o, si se decide dejar fuera el texto, decir el motivo real:
  «el nombre no sigue el patrón `Reading-XX-` que busca el guion».

## B. ¿Se rompió algo al corregir?

### SERIO

**S3. El accionable A2 está «HECHO» y treinta líneas después el criterio de
éxito «Enlace permanente disponible» sigue «Pendiente (A2)».**
- Dónde: `entrega/estrategia.md:364` («**HECHO**: `huggingface.co/spaces/…`»)
  frente a `entrega/estrategia.md:392` («| Operación | Enlace permanente
  disponible | **Pendiente** (A2) |»). Lo mismo en `entrega/documento.tex:798`
  frente a `:837`, y el PDF lo imprime («Pendiente (A2)» aparece una vez en
  `documento.pdf`).
- Por qué: es la contradicción C1 del informe 5 reaparecida dentro del mismo
  archivo, en la tabla que resume si el proyecto cumplió lo que prometió.
- Arreglo: «**Cumplido** (A2): Space público; sin disco persistente (A4)».

**S4. La presentación cobra 9 USD/mes por un despliegue que el documento
declara gratuito.**
- Dónde: `entrega/presentacion.tex:326-327`: «Desplegar de forma permanente &
  9 USD/mes & **Hecho**: dirección fija que no muere al apagar». Frente a
  `documento.tex:798` y `estrategia.md:364`: «Gratuito: Hugging Face Spaces
  sobre `cpu-basic`». Y la API confirma `cpu-basic`, que es el plan sin coste.
- Por qué: la diapositiva es lo que se proyecta delante del profesor; el cierre
  (`:32-40`) dice haber unificado «en lo que es verdad» y no revisó la
  presentación.
- Arreglo: «gratis (CPU básica)» en la celda de coste.

**S5. `investigacion/competencia.md` quedó a medio corregir y se contradice en
el mismo párrafo.**
- Dónde: `investigacion/competencia.md:450-454`. Título: «**Ellos están
  desplegados y nosotros no.**» Cuerpo, ya cambiado por el commit: «Nosotros
  tenemos una web gratuita sin disco persistente y un consumo de 1,05–1,5 GB de
  RSS que descarta todos los planes gratuitos de 512 MB. **Un producto que no se
  puede abrir no compite con nadie.**»
- Por qué: el cierre (`:39-40`) da por corregidas «las dos menciones» de este
  archivo; cambió las palabras y dejó el título y la frase final, que dicen lo
  contrario del cuerpo. Además, «descarta todos los planes gratuitos» está
  escrito en un párrafo que acaba de decir que corre en uno.
- Arreglo: retitular («Ellos están en las tiendas; nosotros en una web
  gratuita») y quitar la última frase.

### MENOR

**M1. La suma de DESPLIEGUE.md ya no cuadra.** `DESPLIEGUE.md:11-12` pasó a
328 MB + 243 MB; `DESPLIEGUE.md:15` y `:87` siguen diciendo «Los 549 MB de
datos» (que era 317 + 232). Ahora son 571.

**M2. El `.md` y el `.tex` volvieron a separarse en tres puntos.**
- `documento.tex:1153-1155` añade «el catálogo gratuito de British Council no
  tiene C2, así que el corpus nunca tuvo seis»; `documento.md:416-417` solo
  cambia «seis» por «cinco» y no explica nada.
- `documento.md:697` y `:721` crean un «Cuadro 10b» y lo citan desde el pie del
  Cuadro 10; en el `.tex` la misma tabla va sin caption ni número
  (`documento.tex:1699-1715`), así que en el PDF no existe ningún «Cuadro 10b».
- La procedencia de la recta (C1) solo está en el `.md`.

**M3. Al quitar un absoluto se puso otro, y se borró la evidencia que lo
sostenía.** `app/scoring.py:246-247`: «250 palabras inglesas pasan **siempre**
de 256 BPE»; `documento.md:885` y `documento.tex:2187`: «que al tokenizar pasan
de 256 *tokens* BPE y se truncan». La versión anterior decía «Comprobado sobre
200 ventanas: el 100 % mide exactamente 256» y el commit la quitó. Comprobado
aquí con el tokenizador del v4: sobre las 107 ventanas de *Alice* el mínimo es
256 y el máximo 328, ninguna por debajo; pero 250 palabras monosílabas sin
puntuación dan **252** *tokens*, así que «siempre» es una propiedad de la prosa
real, no del tokenizador. La frase empírica era mejor que el «siempre»: conviene
restaurarla.

**M4. «Capítulo a capítulo» significa dos cosas distintas a diez páginas de
distancia.** En `documento.md:641` / `documento.tex:1567` el precálculo «lo lee
entero, capítulo a capítulo»; en el pie del Cuadro 14 (`documento.md:871-873`,
`documento.tex:2127-2130`) el precálculo «agrupa en lotes fijos de 64/128» y es
**la aplicación en vivo** la que «mide capítulo a capítulo». Un lector cuidadoso
ve una contradicción donde solo hay dos usos de la misma frase (unidad de salida
frente a unidad de lote). Además, «el catálogo precalculado sí lo lee entero» va
en presente cuando A3 está «en curso» y el Cuadro 3 dice que las etiquetas del
catálogo son de un v1 sobre ~190 palabras.

**M5. El guion del vídeo sigue diciendo «a mi ritmo».** `guion_video.md:107-108`,
`guion_video.tex:279` y `guion_video.pdf`: «Cuánto tardo en leerlo *a mi
ritmo*». El cierre (`:71-73`) retiró «a su ritmo» del documento y de la
estrategia; en el guion, que es lo que se dice en voz alta, quedó. Es el #6 del
inventario, cerrado a medias.

**M6. Tics de redacción de esta tanda** (detalle en C).

### DUDA

**D1. No se pudo reproducir la compilación del `.tex`.** En esta máquina no hay
`xelatex`, `lualatex`, `latexmk` ni `tectonic` (buscados en PATH, Program Files,
AppData y WSL, que no está instalado). Lo que sí se comprobó: los tres PDF están
fechados hoy a las 06:20–06:25, `documento.pdf` contiene los textos nuevos
(«HECHO a medias», «4,53», «205 pruebas», «ocho ventanas por», «300/300») y no
contiene ningún «??»; las **40 referencias `\ref` distintas tienen `\label`**
(script propio, coincide con el cierre). Así que compiló, en algún sitio que el
cierre no nombra. Las 13 etiquetas sin referenciar son las mismas que en el
informe 5 y son inofensivas.

**D2. El contraste se mide en cuatro parejas por paleta, y fuera de ellas hay
colores por debajo de AA.** Las veinte parejas pasan y la peor es 4,53 (hielo,
botón), exactamente como dice el cierre. Pero `--ll-acento` sobre `--ll-fondo`
da 3,54 (amanecer), 3,04 (menta) y 4,28 (papel), y `--ll-titulo-3` sobre
`--ll-fondo` da 2,13 / 1,87 / 2,54 en las tres paletas claras. La redacción nueva
(«en las veinte parejas de color que se comprueban») es honesta; el «Cumplido»
de la fila «Accesibilidad de color» (`estrategia.md:390`, `documento.tex:835`)
depende de que el acento y el tercer color de título no se usen como texto
sobre el fondo, y eso no se verificó en `ui.py`.

**D3. «Arranque en frío de decenas de segundos»** (limitación 12,
`documento.md:1046-1048`) no está medido. Es verosímil (torch + 328 MB en
`cpu-basic`) y la API da `gcTimeout = 172800` s, es decir, la suspensión llega a
las 48 h sin visitas, lo que cuadra con «tras un periodo sin visitas». Se anota
como no medido, no como error.

---

## C. ¿Se ha ido al otro extremo?

**En general, no.** La limitación 12 afirma lo que hay y lo que falta sin pedir
perdón; el balance 59→45 es la mejor versión de ese párrafo hasta ahora; el pie
del Cuadro 14 dice exactamente cuánto vale la cifra y para qué no vale; A1
«HECHO a medias» es la frase correcta. Cinco sitios sí tienen el tic, y son de
esta tanda:

1. **Dos filas seguidas del Cuadro 12 con la misma fórmula de descargo.**
   `documento.md:788` («…así que se da como orden de magnitud, no como cifra
   auditable») y `:793` («…así que vale como orden de magnitud y no como cifra
   auditable»); igual en `documento.tex:1862` y `:1872`. Una vez es honestidad;
   dos veces en veinte líneas es una muletilla. Basta con una nota al pie común.
2. **«No es exactitud bit a bit —eso sería falso—»**, `documento.md:1151`,
   `documento.tex:2489`. Nadie en ese párrafo ha dicho «bit a bit»; el
   documento discute con una versión anterior de sí mismo. Sobra el inciso.
3. **El pie del Cuadro 11 repite los tres números que están justo encima y los
   fecha:** «reproducidas hoy en local: 0,854, 0,807 y 0,657»
   (`documento.md:744-747`, `documento.tex:1744`). «Hoy» en un documento de
   entrega no significa nada dentro de un mes. Con «las tres cifras las calcula
   `validar_local.py` sobre los mismos 45 textos» está dicho todo.
4. **Un título con paréntesis de disculpa:** «## 7.2 Validación externa (no del
   todo ciega)» (`notebook_proyecto.py:1657`, y `:244` en la tabla). La salvedad
   es correcta y ya está explicada dos párrafos más abajo; en el título resta
   sin añadir.
5. **Una frase de sesenta palabras en §7.4** (`documento.md:637-641`): «Puntúa
   bloques […] promedia sin ponderar, con un tope de ocho ventanas […]: es lo
   que mantiene […], y por eso un vistazo mide […] (el catálogo precalculado sí
   […]).» Son tres afirmaciones; que sean tres frases.

---

## D. ¿Queda algo que avergonzaría al autor si lo lee un profesor universitario?

**Sí.** Seis cosas, y las seis son nuevas de esta tanda o quedaron a medio
corregir en ella:

1. La recta `0,72x + 0,38` lleva ahora una procedencia que, recalculada, da
   `0,67x + 0,41` (C1). Es la segunda vez consecutiva que una corrección
   rellena un hueco con algo que no se midió.
2. «Por debajo del segundo» tarda 1,0–1,2 s en la máquina del autor (S1).
3. El manifiesto lista bajo «Sin nivel en el nombre» un archivo que empieza por
   `B2__` y que el modelo puntúa sin problema (S2).
4. «Enlace permanente disponible: **Pendiente**» treinta líneas después de
   «A2: **HECHO**», en el PDF y en la estrategia (S3).
5. La diapositiva de estrategia cobra 9 USD/mes por lo que el documento llama
   gratuito (S4).
6. «Los 549 MB de datos» debajo de una tabla que suma 571 (M1).

Todo lo demás es redacción. Ninguno de los seis invalida un resultado: el
orden estricto por nivel, la correlación parcial y la identidad de lotes se
sostienen con lo medido aquí.

---

## Lo que está bien y podía estar mal — cifra por cifra del cierre

| Cifra del cierre | Comprobación en esta máquina | Veredicto |
|---|---|---|
| Peor contraste **4,53**, hielo, botón sobre `--ll-boton-alto` | Fórmula WCAG sobre `paletas.PALETAS`: hielo/botón **4,53**; las otras cuatro 4,65–4,74; el 9,51 antiguo es menta texto/fondo | **Sale** |
| Modelo **328,5 MB** `.safetensors`, 332,1 MB carpeta | `os.path.getsize`: 328 489 204 B (328,5 MB = 313,3 MiB); carpeta 332 053 001 B (316,7 MiB, el «317» viejo) | **Sale** |
| Diccionario **243,3 MB** = 232,1 MiB | 243 326 976 B | **Sale** |
| **205** pruebas | `pruebas_extremas.py`: «Las 205 pruebas extremas pasan»; 206 líneas con `prueba(` = 205 llamadas + el `def` | **Sale** |
| **27** pasos | `pruebas_integracion.py`: «Los 27 pasos del recorrido encadenan bien»; 28 `paso(` = 27 + el `def` | **Sale** |
| Space **RUNNING**, `cpu-basic`, sin almacenamiento persistente | API: `stage RUNNING`, `hardware cpu-basic`, `storage None`, público, `gcTimeout 172800` | **Sale** |
| Modelo público; diccionario **no publicado** | `literalevel-v4` público, 6 archivos; no existe ningún dataset de diccionario (el único dataset del autor es `literalevel-precalculo`) | **Sale** |
| Cuadro 11: **0,854 / 0,807 / 0,657**, y 0,730 | `validar_local.py`: 0.854 / 0.807 / 0.657 / 0.730 sobre 45 textos | **Sale** |
| Los 10 rechazos, todos por **«menos de 150 palabras»**; nueve A1 y un B1 | Los diez imprimen `ValueError: … al menos 150 palabras`; 9 `A1__` y `B1__…email-request-for-help` | **Sale** |
| 58 casan con el patrón, **57 con nivel** (12/9/13/11/12) | `glob` en `~/Downloads`: 58; regex: 57 con esa distribución; manifiesto = disco, 58/58 | **Sale como recuento**; la descripción del 58.º es falsa (S2) |
| Medias estrictamente crecientes, 5 niveles | 0,5040 < 0,5480 < 0,9276 < 1,2478 < 1,4952 | **Sale** |
| `.ipynb` regenerado, 92 celdas, 53 de código | JSON: 92 / 53; contiene «no del todo ciega» (2) y ya no «Está medida y la respuesta es sí» (0) | **Sale** |
| 40 referencias cruzadas, ninguna rota | 53 `\label`, 40 `\ref` distintas, 0 sin etiqueta; PDF sin «??» | **Sale** |

Otras comprobaciones que podían fallar y no fallaron:

- **La tanda inventada de 286 desapareció** de `documento.md`, `documento.tex`
  y `app/scoring.py`; `286` solo queda en `informe_velocidad.md:83` (barrido de
  hilos), donde es verdad. `notebook_proyecto.py:1762` («300/300 valores
  idénticos bit a bit») concuerda con la única comprobación que existe.
- **El argumento sustituto se sostiene desde el código:** `fixed_blocks`
  (`scoring.py:76-93`) emite ventanas de `size=250` exactas y cubre la cola con
  la última ventana completa; la única ventana más corta es la de un texto de
  150–250 palabras (`n <= size`), que efectivamente va sola.
- **Tope de ocho ventanas:** `MAX_BLOCKS_PER_DOC = 8` (`scoring.py:21`), usado
  por `puntuar()`; `perfil_de_texto` lo desactiva (`scoring.py:284`). §7.4 lo
  describe bien salvo el «por debajo del segundo».
- **180 / 110 palabras por minuto:** `ficha.py:31-32`. **«Unas veinte ventanas
  por capítulo»:** 286/14 = 20,4. **6,96 y 8,19:** `informe_velocidad.md:94,115`.
- **MAE 0,499 → 0,200:** 0,499 × 0,4 = 0,1996. **−0,379 → −0,326 con −0,330 a
  397 libros:** idéntico al Cuadro 4. **45.345/18 = 2.519 ≈ ×2.500.**
- **Cuadros del `.md`:** 1…15 sin saltos (más el 10b). **Cabecera «Cifra
  publicada / La nuestra»** en los dos archivos. **A1 «HECHO a medias»** en los
  dos. **Audio de Wiktionary** corregido en los cinco sitios. **6,3 h** fuera de
  `investigacion/` salvo `acelerar_precalculo.md:62-67`, que la discute como
  estimación errónea, y `documento.md:899`, que la retira. **317 / 232 MB,
  9,51, 183 y 147 pruebas, «pueda terminar», «Su número», «Cuadro 17», «túnel
  temporal» como presente:** cero apariciones en los entregables.
- **`requirements.txt`** con techo de versión mayor en todas las líneas y las
  versiones probadas anotadas. **`escala_cefr.dat`** con sus comentarios `#` no
  lo lee el `.tex` (los cortes están escritos a mano, `documento.tex:433`), así
  que no hay riesgo de compilación. **`validar_local.py`** no importa `scipy`;
  `_rangos` promedia empates como `rankdata`; la parcial es la fórmula estándar
  sobre rangos.
- **Las menciones asimétricas a «auditoría externa»** (M1 del informe 5) han
  desaparecido de los dos archivos. **La repetición «que no existe»** (M2) está
  resuelta (`documento.md:655` «inexistente»).

---

## Estado de la lista del informe 5

| Informe 5 | Hoy |
|---|---|
| C1 despliegue contradictorio | **Cerrado** en documento, estrategia y PENDIENTES; residuos en S3, S4 y S5 |
| C2 tanda de 286 inventada | **Cerrado** |
| S1 Cuadro 17 | **Cerrado** (15) |
| S2 cabecera del cuadro de competencia | **Cerrado** |
| S3 A1 hecho/pendiente | **Cerrado** (HECHO a medias en los dos) |
| S4 README Drive/HF y `scoring.py` | **Cerrado** |
| S5 balance 59→45 | **Cerrado como aritmética**; la resta nueva está mal descrita (S2 de aquí) |
| M1–M5 | **Cerrados** |
| #6 «a su ritmo» | **A medias**: queda en el guion (M5) |
| #10 recta sin procedencia | **Cambiado a peor**: procedencia falsa (C1) |
| #27 composición del corpus de anclaje, #38 artefactos ausentes | **Abiertos y declarados** como limitación; no se pueden cerrar desde el repositorio |
| Resto (#1-5, 7-9, 11-26, 28-37) | **Cerrados** y verificados en el archivo y la línea |
