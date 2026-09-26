# Pendientes de Pléyade (proyecto LiteraLevel)

Actualizado: **26 de septiembre de 2026**. Entrega: **3 de octubre de 2026**.
El estado operativo del día está en [`docs/ai/HANDOFF.md`](docs/ai/HANDOFF.md).

La rúbrica son 110 puntos y se aprueba con 80. El orden de esta lista es por
puntos en juego, no por comodidad.

## Estado al 26 de septiembre

- **Entrega:** la app es **Pléyade**, Angular en Vercel
  (<https://pleyade-app.vercel.app>), con la misma app de respaldo en
  <https://mikemaki1763-literalevel-front.static.hf.space/>. API y motor en el
  Space `MikeMaki1763/literalevel` (revisión `103eef5`, commit `06a16db`),
  cuenta Pro de Hugging Face activa (7 USD/mes).
- **Entregables puestos al día el 26 sep** (rama `dev/entregables`): documento
  (con el modelo articulatorio en §7.8), estrategia, presentación, guiones del
  vídeo y de la demo, mensaje al profesor, cuaderno (solo texto) y 22 capturas
  nuevas desde Vercel (`entrega/capturas/registro.txt`).
- **Pendientes de Miguel, por puntos:**
  1. **Demo en vivo (25):** ensayarla con cuenta, micrófono y el perfil de 1,20
     puesto en la cuenta (tu nivel real, C2 1,88, se vuelve a poner después).
  2. **Vídeo (20):** grabarlo con Pléyade (el guion ya está al día: 514
     palabras, 3:26 a 150 ppm).
  3. Poner a cero `uso_openai.json` del bucket, para que la cuenta del profesor
     tenga cupo.
  4. Probar la lectura en vivo con tu voz (solo se probó con voz sintética).
- **Abierto, declarado en el documento:** contraste del tema de la marca sobre la
  galaxia sin medir; Eos en desarrollo, fuera de la entrega; prueba de usuario
  sobre el front nuevo (A8). El tiempo de carga de la boca 3D en Vercel ya está
  medido (26 sep, navegador sin caché: 3,0–3,1 s; 8,9 s con la CDN fría; 1,7 MB
  por la red).
- **Detalle visto al hacer las capturas:** la «L» de la tarjeta de bienvenida ya es
  el icono de Pléyade (commit `2b37573`, literalevel-f3, publicado el 26 sep).

## Estado al 14 de septiembre (histórico)

- **Entrega:** Angular es la interfaz principal; FastAPI adapta el motor Python
  y Gradio queda de respaldo. Enlace de entonces:
  <https://mikemaki1763-literalevel-front.static.hf.space/>.
- **Primero leer:** [relevo de Codex](auditoria/relevo_codex_2026-09-13_noche.md),
  [despliegue selectivo](auditoria/despliegue_codex_2026-09-13_noche.md) y
  [cierre documental](auditoria/cierre_documento_codex_2026-09-14.md).
- **Motor (cierre del 14 sep 2026):** Space `MikeMaki1763/literalevel` en
  `7c09d90` (reinicio 15), RUNNING. Front `MikeMaki1763/literalevel-front` en
  `45d9999`, RUNNING (lo publica e6). Cada reinicio, con lo que subió y lo que
  se comprobó, está en [`DESPLIEGUE.md`](DESPLIEGUE.md). Para comparar sin
  escribir: `python tools/desplegar_app.py --seco`.
- **Pruebas en árbol limpio de `8ee42f0` (último cambio de código del motor):**
  corpus 24, API 51/51, voz temporal, ficha, integración 27, smoke, voz, ritmo
  de voz, léxico y extremas 349; tras `04fced0`, corpus 25 en el árbol de
  trabajo. Banco de mutantes: los 10 nuevos del día cazados por su prueba (C3-libres-*,
  C3-atribucion-medida, C3-bloque-sin-marca-*, C3-servido-sin-limpiar,
  C3-estribillo-fuera, C3-medidas-sin-cache). Desde `9be2c42` el banco copia
  `pruebas_api.py`; antes ningún mutante de `api.py` con esa suite podía
  cazarse.
- **Catálogo:** 68.546 libros = 53.179 de Gutenberg + 15.367 textos libres
  (StoryWeaver 14.506, Let's Read 328, African Storybook 280, VOA 253; `740eb84`,
  publicado en el reinicio 21), medidos con el v4 en CPU local; en `377a650`
  quedaron 894 fuera y la nota de `DESPLIEGUE.md` explica por qué.
- **Cuentas listas para usuarios (14 sep):** invitado1 a invitado8 con 20 usos
  cada una, profesor con 60 y miguel sin tope. Comprobado entrando en el Space.
  Las contraseñas las da Miguel desde `literalevel_codigos.txt`.
- **Cerrado hoy y comprobado en el Space:**
  - reinicio 9: lectura natural en la voz y su historial de ritmo;
  - reinicio 10: catálogo con StoryWeaver;
  - reinicios 11 y 12: topes por hora de medidas y curvas, con aviso propio;
  - reinicio 12: libres intercalados;
  - reinicio 13: temas y portada por IA en la API;
  - reinicio 14: atribución fuera de la medida (Doggie 0,35 → 0,007), libres
    por cercanía al nivel, `medido_en_bloque` y plurales;
  - reinicio 15: texto servido sin U+FEFF ni páginas dobles.
  De los 6 puntos de la prueba como persona, 1 a 4 están cerrados y
  comprobados en el Space. El 5 (plurales y la letra del resultado) y el 6
  (nota bajo los resultados) los cerró e6 en el front y en `ui.py`; f4 no los
  ha vuelto a probar en el navegador.
- **Pendientes de Miguel:** ensayo de pronunciación con micrófono físico,
  recorrido Angular con usuarios y vídeo grabado con cámara visible.
- **Abierto de verdad:**
  - una prueba como persona del front publicado (`45d9999`) con los cambios de
    la tarde: plurales, `medido_en_bloque` pintado y portadas;
  - la ficha de un libro largo tarda 2,2–3,4 s en cada petición (PG1661), sin
    investigar;
  - calidad de acepciones (caso `house`);
  - muestras de portadas FLUX sin generar;
  - integración pública de la boca 3D sin verificar por f4;
  - 13 libros de Let's Read CC BY 3.0 siguen internos y podrían entrar;
  - la columna `palabras` del catálogo externo cuenta el texto medido, con las
    páginas repetidas.
  No conectar GPU ni publicar portadas sin aprobación visual y permiso de
  subida; desde el 14 sep no hay presupuesto (solo Colab gratis).

## Histórico de auditorías y coordinación, hasta el 12 de septiembre

**El registro previo recomendaba leer primero
[`auditoria/cierre_auditoria_17.md`](auditoria/cierre_auditoria_17.md)** —la
última en aquel corte, y la más barata de todas: una pasada ESTRECHA sobre el diff del día
encontró un **crítico** que la auditoría completa de unas horas antes no podía
ver, porque el diff no existía todavía—, luego
[`auditoria/cierre_auditoria_16.md`](auditoria/cierre_auditoria_16.md) —6
serios, con tres de ellos visibles en cámara— y
[`auditoria/cierre_auditoria_15.md`](auditoria/cierre_auditoria_15.md) —7
serios, 6 menores y sobre todo **veintidós mutantes vivos** que se
convirtieron en diecinueve pruebas—, después
[`auditoria/cierre_auditoria_13.md`](auditoria/cierre_auditoria_13.md) —8
serios, 14 menores y 3 notas, con banco de mutantes propio—, después
[`auditoria/cierre_auditoria_11.md`](auditoria/cierre_auditoria_11.md) —la más
productiva del proyecto, y la razón fue pedirle al auditor que **mutara el
código**—, luego
[`auditoria/cierre_2026-09-09_noche.md`](auditoria/cierre_2026-09-09_noche.md)
y [`auditoria/cierre_2026-09-09.md`](auditoria/cierre_2026-09-09.md), y luego
`git log` desde `aed7751`.

Cuatro avisos que valen para cualquiera que toque esto:

1. **Una prueba que pasa no demuestra que cazaría el fallo.** Hay CUATRO formas
   de que no pruebe nada. La tercera la encontró la auditoría 13: el manejador
   rechaza la entrada **antes** de llegar al código que quieres probar, y la
   aserción se cumple sobre el vacío. **La cuarta, la 15, y es la más
   traicionera: un doble puesto por prudencia que anula justo lo que se quiere
   medir.** En la cabecera de `pruebas_extremas.py` había un
   `ui.voz.registrar_fallos = lambda *a, **k: None` para no ensuciar el
   `voz.db` de quien ejecutara las pruebas; desde que `LITERALEVEL_DATOS`
   apunta a una carpeta temporal ya no hacía falta, y mientras estuvo ahí el
   mutante que daba a todos los visitantes la misma `voz.db` **no lo podía
   cazar nadie**. Está en la skill
   `probar-la-app-de-verdad`, y el banco de mutantes vive en
   [`tools/banco_mutantes.py`](tools/banco_mutantes.py) —en el repositorio y
   no en `scratchpad/`, porque un subagente de auditoría sobrescribió el
   archivo cuando estaba en el bloc compartido y se perdió entero—.
2. **La prueba de contraste mide variables de la paleta**, así que un color
   clavado en el CSS le es invisible.
3. **Arreglar algo puede quitar una red que otra cosa usaba.** Al limpiar los
   títulos de capítulo, la portadilla legal de tres libros pasó a contar como
   capítulo, porque el detector de licencia vivía de ese título sin que nadie lo
   hubiera escrito. Se vio midiendo lo mismo con el árbol de antes y el de
   después, no leyendo.

**Estado histórico: el Space estaba al día hasta la auditoría 17**, subida el 11 de septiembre de
2026 y cotejada por hash: los catorce archivos publicados son idénticos byte a
byte a los locales. **No te fíes de esta línea**, que es la que se queda vieja:
`python tools/desplegar_app.py --seco` lo compara sin publicar. Sin `--seco`
el script puede subir cambios. La auditoría 16
ya avisó una vez de que esta frase iba por detrás del repositorio.

Son muchos commits y tocan archivos compartidos: `app/ui.py`, `app/cuentas.py`
—con interfaz pública nueva: `problemas()`, `declaradas()` y `devolver()`—,
`app/paletas.py`, `app/perfil.py` —con `HOLGURA`, que es **la única** holgura de
recomendación y la lee `ui`—, `app/scoring.py`, `app/ficha.py` —con `miles()`,
que usan `ui` y `catalogo`—, `app/catalogo.py`, `validar_local.py`,
`pruebas_extremas.py`, `pruebas_lexicon.py` y `colab_precalculo.py`.

Y dos de Codex, avisados en su commit: `app/reader.py` (la cabecera corrida de
Gutenberg y los pies de ilustración) y `app/lexicon.py` (`llamadas_de_pago` en
`ResultadoLexico` y la clave del audio normalizada).

`auditoria/estado_real.md` **está superado**: úsalo como histórico. El estado
actual se resume al principio de este archivo y enlaza sus informes de cierre.

---

## Bloqueos registrados el 12 de septiembre (histórico)

| Qué | Desbloquea | Por qué solo tú |
|---|---|---|
| ~~Unidades de Colab~~ | **YA NO BLOQUEA** | La **T4 gratuita** hace el trabajo: medido el 10 de septiembre de 2026, 492 ventanas/s, que son **84 libros/min** contra los 61 de la A100 de pago. El cuello de botella era Drive, no la tarjeta, y el prefetch lo tapó. El catálogo entero son ~12 h de T4 gratis y reanudables. Las «15 unidades» ya no hacen falta |
| **Micrófono** | parte de **25 pts** (demo en vivo) | Sin él no se puede enseñar la corrección de pronunciación, que es lo que el profesor pidió ver. Unos audífonos con micro bastan |
| **Grabar el vídeo** | **20 pts** | El guion está escrito, cronometrado (569 palabras, 3:48) y compilado en PDF |
| **Cupo de Codex** | la auditoría de cifras | **La ventana es corta, no semanal**: el aviso del 11 anunciaba el martes 15 y el 12 por la mañana ya respondía. Pero se agotó otra vez a mitad del encargo —`auditoria/encargo_12.md`— **sin emitir un solo hallazgo**: murió recopilando con `grep`, que es el modo de fallo que esta casa ya tiene documentado dos veces. Vuelve a la 1:56 p. m. del 12. Si se relanza, hay que partirlo en trozos de un solo archivo |
| ~~Token de Hugging Face~~ | **HECHO** | Modelo en `MikeMaki1763/literalevel-v4`, público, descarga sin credenciales verificada. El token vive en `C:\Users\laura\.hf_token` y **hay que revocarlo** cuando se acabe de subir |
| ~~Despliegue permanente~~ | **HECHO** | `MikeMaki1763/literalevel`, público, `cpu-basic`, RUNNING. Cuesta 7 USD/mes (cuenta Pro, ya pagada). Arranque medido: 31 s hasta `RUNNING`, 32 s hasta que responde |
| ~~Aceptar la pestaña de Colab~~ | **HECHO** | Conectado a `rayko800@gmail.com`, que es la cuenta con Colab Pro y con `literalevel_bigdata` |

El **conector de Drive de claude.ai** sigue devolviendo `Operation is not
implemented, or supported, or enabled`. Ya no bloquea nada: el Drive se lee
entero a través de Colab con `drive.mount`.

---

## El catálogo — HECHO el 12 de septiembre de 2026

> **Terminado y en la app.** 53.179 libros y 585.111 capítulos medidos, 0
> errores y ningún libro medido dos veces (sonda 11b). La última tanda midió
> 9.795 libros en 54,8 minutos. Publicado en el Space junto con la curva por
> capítulo y los embeddings del buscador; probado en el navegador el mismo día.
> Lo que sigue es cómo se llegó, y se queda como histórico.
>
> **12 de septiembre de 2026: midiendo, y ya sin Drive.** El freno de estos días
> no era la descarga: era que los resultados iban a Google Drive, que pide un
> permiso interactivo en cada sesión nueva. Ahora van a un repositorio privado
> de Hugging Face (`MikeMaki1763/literalevel-catalogo`) con el token en los
> Secretos de Colab, y una sesión caída se reanuda sin que nadie dé un clic.
>
> - **Rescatados de Drive: 153 shards** (117 antiguos + 36 del lado A),
>   verificados en el repositorio de Hugging Face. Fue el último permiso de Drive.
> - **Descarga: 57.226 libros en 7,7 minutos** desde el volcado de Common Pile.
> - **Por medir: 9.795.** La tanda arrancó a las 16:07 en una T4 gratuita.
> - **Cómo va, sin abrir Colab:** `python -X utf8 tools/ver_progreso.py`.
> - Cómo reanudar si Colab corta: [`COLAB.md`](COLAB.md).
>
> **Decidido por Miguel: el catálogo medido entra en la app en cuanto esté.** La
> celda 11 ya exporta, además del CSV por libro, la curva por capítulo
> (`capitulos_medidos.parquet`) y los embeddings del buscador con el nombre que
> espera `app/catalogo.py`.
>
> Lo de abajo es el estado del 9 y el 10 de septiembre, y se queda como histórico.

Cifras vivas: **medidas el 9 de septiembre de 2026** y en movimiento mientras
la descarga y el precalculo sigan corriendo. Sin fecha son falsas mañana.

| | |
|---|---|
| Libros objetivo (inglés, Project Gutenberg) | 61.642 de 79.337 entradas (instantánea del catálogo oficial del 7 de septiembre de 2026) |
| Descargados a Drive | **31.974** (51,9 %) el 9 de septiembre de 2026 |
| **Con perfil medido por el v4** | **29.875** el 10 de septiembre de 2026, sin duplicados (29.875 líneas, 29.875 ids distintos). En `literalevel_bigdata/catalogo_medido.csv` |
| Velocidad | **84 libros/min en T4 gratis** (492 ventanas/s ÷ 350 ventanas por libro), medido el 10 de septiembre de 2026. En A100 sin prefetch eran 61 de extremo a extremo, con la tarjeta parada el 80 % esperando a Drive. **La gratis con prefetch gana a la de pago sin él** |
| Cuello de botella | **no es la GPU**: el 80 % del tiempo espera a Drive |
| Ventanas por libro | **332,3 de media**, mediana 266 (medido sobre 5.153 el 9 de septiembre de 2026) |
| Coste real del catálogo | **2,8 h** de cómputo A100; ~17 h de extremo a extremo. *Corregido el 15 de septiembre: las dos son estimaciones para los 61.642 (332,3 ventanas a 2.022 por segundo, y 61 libros por minuto), no horas gastadas; las unidades de A100 que se gastaron no quedaron registradas* |

**Lo que falta ya no es medir: es DESCARGAR.** 29.875 de los ~31.974 textos que
hay en Drive tienen perfil; quedan ~29.700 libros del catálogo oficial sin bajar.
Y descargar **no necesita GPU ni unidades**.

> **Y un hallazgo que hay que decidir, pero NO antes del vídeo.** La dificultad
> media de los 29.875 es **1,75 sobre 2**, con el cuartil 1 en 1,664: **al menos
> tres cuartas partes del corpus puntúan C1 o por encima**. El catálogo que usa
> la app dice lo contrario —sus etiquetas del v1 son 60,4 % A1—. No es un fallo
> del v4: sus propias medias en los textos graduados van de 0,50 (A1) a 1,50
> (C1), así que que la literatura del XIX promedie 1,75 es lo esperable. Lo que
> hay que decidir es qué le ofrece la app a un lector de B1. **La app no se ha
> tocado**: sigue con `catalogo_recomendaciones.csv`. Cambiarla a dos días de
> grabar sería meter una variable enorme en la demo. Todo el detalle en
> [`auditoria/medicion_catalogo_2026-09-10.md`](auditoria/medicion_catalogo_2026-09-10.md).

`colab_precalculo.ipynb` es reanudable: lee los shards que ya hay y se salta
los ids hechos. La descarga **no necesita GPU** — se puede dejar corriendo en
un entorno de CPU gratuito mientras no haya unidades.

---

## Estado de la entrega

- [x] **Documento** actualizado a Angular y corte de pruebas: `46819e7`, PDF de 52 páginas
- [x] **Estrategia** (`entrega/estrategia.md`, absorbida en el `.tex`)
- [x] **Cuadernillo** (`entrega/notebook_proyecto.py` → `.ipynb`, 103 celdas; narrativa revisada, sin afirmar ejecución nueva en Colab)
- [x] **Guion del vídeo** actualizado a Angular (`13281a9`), 480 palabras habladas; falta grabar
- [x] **Presentación** actualizada a Angular (`13281a9`), 14 diapositivas
- [x] **Apartado de competencia** — §8.6 de la copia Markdown, §8.5 del PDF y §5 de la estrategia
- [x] **Manifiesto del corpus externo** (`entrega/manifiesto_corpus_externo.md`)
- [ ] **Vídeo grabado** — bloqueado en el micrófono
- [x] **Catálogo remedido** — terminado el 12 de septiembre de 2026: 53.179 libros y
  585.111 capítulos medidos por el v4, sin Drive y sin un libro medido dos veces.
  Está en la app publicada y probado en el navegador: buscador, ficha, curva entera
  (836 ventanas en *Crime and Punishment*) y capítulos sugeridos
- [ ] **Capítulos a tu nivel, fase 2** — ofrecerlos ya en la lista del buscador y en
  «Sorpréndeme», antes de abrir el libro
- [x] **Tarjeta del modelo corregida en Hugging Face** — publicada el 12 de septiembre
  de 2026 (commit `daee09d`): cuatro épocas y no seis, validación que eligió el punto
  de control y no ciega, British Council de desarrollo y no externo, ELG CEFR English
  como corpus, OneStopEnglish y métricas recalculadas
- [x] **Licencia del modelo** — decidido por Miguel el 12 de septiembre de 2026:
  **CC BY-NC-SA 4.0**, la misma que el corpus de entrenamiento (antes ponía Apache 2.0)
- [x] **Corpus del British Council reconstruible** — manifiesto con URL y SHA-256
  (`entrega/corpus_bc_manifiesto.csv`) y `tools/bajar_corpus_bc.py`; comprobado
  desde una carpeta vacía: da las cifras publicadas
- [x] ~~Validación con UniversalCEFR~~ — **retirada: era el entrenamiento.** El v4
  se entrenó con ELG CEFR English (= `elg_cefr_en`), y los 325 textos de Cambridge
  están dentro de él. De paso se sabe ya de qué está hecho el corpus de anclaje:
  guion y métricas del entrenamiento en `entrenamiento_v4/`
  ([`auditoria/validacion_universalcefr_2026-09-12.md`](auditoria/validacion_universalcefr_2026-09-12.md))
- [x] **Métricas internas del v4 recalculadas**: guion + pesos + datos públicos
  dan 0,5347 / 0,9722 / MAE 0,4985 / Spearman 0,9084, idénticas a cuatro decimales
- [x] **Validación externa con OneStopEnglish** — 0 solapamiento con el
  entrenamiento; 560 unidades, Spearman 0,800 (palabras 0,692), parcial 0,688; en
  orden dentro del artículo 183/185, con la longitud sola en 179
  ([`auditoria/validacion_onestop_2026-09-12.md`](auditoria/validacion_onestop_2026-09-12.md))
- [x] **Capítulos a tu nivel, fase 1** (dentro del lector) — 302 pruebas extremas y
  8 mutantes nuevos, los 8 cazados por su prueba. Con el catálogo medido, 303
  pruebas y 7 mutantes más para la alineación con el catálogo

---

## Cifras de referencia y fecha de comprobación

Medidas el 9 de septiembre de 2026 salvo donde la fila diga otra fecha, y
con su guion de procedencia. No todas se han reejecutado en el cierre del 14.

| Qué | Valor | Con qué se comprueba |
|---|---|---|
| Validación externa | **47 textos** (los 59 menos 2 sin cuerpo y 10 cortos) | `validar_local.py` |
| Medias por nivel | 0,5040 · **0,5561** · 0,9276 · **1,2414** · 1,4952 | `validar_local.py` |
| Cuadro 13 del `.md`, 18 del PDF (baseline) | **0,860 / 0,807 / 0,668** | `validar_local.py` |
| Modelo contra longitud | 0,732 | `validar_local.py` |
| Pruebas de estrés históricas | **303** en el corte del 12 sep; no es el total actual validado | `pruebas_extremas.py`; revisar salida de la ejecución, no esta cifra |
| Catálogo medido (12 sep 2026) | **53.179** libros · **585.111** capítulos · A1 1 · A2 40 · B1 558 · B2 3.127 · C1 23.454 · C2 25.999 | `catalogo_medido.csv`, `capitulos_medidos.parquet` |
| Capítulos a nivel ≤ 0,95 | **3.644** en 1.499 libros | `capitulos_medidos.parquet` |
| *Crime and Punishment* en la app (txt) | 203.415 palabras · 40 capítulos · **836** ventanas · media 1,70 | app publicada, 12 sep 2026 |
| Pasos de integración | **27** | `pruebas_integracion.py` |
| Parejas de contraste | **85** (17 por paleta) | `pruebas_extremas.py` |
| Peor contraste | 4,53 (texto) · 3,11 (título) | `pruebas_extremas.py` |
| Carpeta `modelo_v4/` / diccionario | 332 MB / 243 MB (los pesos solos son 328) | `os.path.getsize`, remedido el 10 de septiembre de 2026 |
| Arranque en frío del Space | **31 s** hasta `RUNNING`, **32 s** hasta que responde | `medir_arranque.py` |
| Recta de compresión | 0,7196x + 0,3760 (4 medias de Colab); 0,67x + 0,41 con las 5 locales | recalculable |
| Textos que pasan el filtro COMPLETO | **36** (el de la app; aquí se puntúan 47) | `validar_local.py` |
| Palabras habladas del guion (14 sep) | **480** = 3:12 a 150 ppm, sin pausas ni acciones | `tools/contar_guion.py` |
| Coste del despliegue | **7 USD/mes** (cuenta Pro; tarifa 9, con descuento) | API `whoami-v2` |
| Carpeta + diccionario | 575 MB (332,1 + 243,3) | `os.path.getsize`, remedido el 10 de septiembre de 2026 |

---

## Decisiones que quedan abiertas

- **Recalibrar la escala.** Un texto A2 puntúa cerca de B1. Es el accionable
  A7. No se toca sin validar contra el catálogo, que ya está medido: el
  siguiente paso es comparar su reparto con el ancla externa.
- **Publicar el diccionario Kaikki** (243 MB). El guion de subida existe; es la
  mitad que falta del accionable A1.
- ~~**Disco persistente en el Space** (A4)~~ **HECHO** el 10 de septiembre de
  2026 por la noche. Bucket privado `MikeMaki1763/literalevel-datos` montado en
  `/data`, con `LITERALEVEL_DATOS=/data`. Verificado reiniciando el Space: el
  perfil sigue ahí. Detalle en `DESPLIEGUE.md`.
- **El modelo v2 de Codex.** Gana en material graduado y pierde en literatura,
  que es nuestro caso de uso. No entra en esta entrega.
