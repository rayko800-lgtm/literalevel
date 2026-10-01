# Auditoría de la entrega — 30 sep 2026, 01:40 (literalevel-c6, skill `auditar-entrega-modulo-5`)

Segunda pasada, sobre lo corregido el 29 a las 19:15. Permiso de Miguel para ejecutar
cuadernos.

## Resumen
- **Commit / Space / Vercel:** `master` en `34c6be1` (= origin); `entrega/` sin cambios desde ese commit. Sin commit quedan solo archivos ajenos fuera de `entrega/` (PENDIENTES, README, HANDOFF, encargo, parquet, angular.json). Space `0547de1` RUNNING, salud ok, `buscador_listo` true. Vercel `HPL2JHFA`, 85 clips de Eos.
- **Nota simulada: 89 / 110** (aprueba con 80). Sube de 86 por el notebook ejecutado en limpio y las variantes cerradas.
- **Serios: 0** · **Menores: 3** (A1 Colab real, A2 copia del vídeo, A3 Eos) · **Proceso: 2** (A4, A5).
- Mecánica: `auditoria/mecanica_2026-09-30.json`, **38 OK · 4 avisos · 0 fallos** (avisos: plazo, Colab, archivos ajenos sin commit, Space estático citado como respaldo).

| Rubro | Pts | Hoy | Evidencia (medida hoy) | Falta |
|---|---|---|---|---|
| Documento | 15 | 13 | 65 pp.; 0 «??»; 45 referencias; páginas 9, 29, 39, 51 y 57 leídas hoy como imagen (limpias, cuadros enteros, cifras con fuente y fecha); ayer 1, 2, 23, 46, 60 | Lectura de las 55 páginas restantes; ortografía frase a frase |
| Estrategia | 15 | 13 | 20 pp.; páginas 1 y 8 leídas hoy (marco de la compañía ficticia; ciclo de usuarios con diagnóstico → corrección → verificación) | Cotejo cifra a cifra |
| Notebook | 15 | 11 | `.ipynb` = `.py` regenerado (103 celdas). **Ejecutado hoy otra vez en carpeta vacía fuera del repo**, sin `.env`, sin `LITERALEVEL_*` ni `HF_TOKEN`, modelo bajado de Hugging Face: 57 celdas de código, 1–57, **0 errores, 0 stderr**, ≈1 min. Segunda ejecución limpia consecutiva (la primera, ayer 19:15) | La rúbrica dice «desde cualquier Colab»: falta esa ejecución con la versión actual (A1) |
| Presentación | 10 | 9 | 17 diapositivas; diap. 4 ya con el catálogo final; QR a Vercel; sin cambios desde ayer 19:11 | Ensayo cronometrado |
| Interfaz | 10 | 9 | Recorrido real hoy a 390×844 en producción: inicio 2,9 s, búsqueda 1,3 s (24 libros), ficha y lector al instante, tabla AFI 1,3 s, Eos reproduce (readyState 4), boca 3D en 9,4 s; 0 errores de consola; sin desbordamiento | Cuenta, voz y micrófono |
| Demo en vivo | 25 | 17 | Guion al día; el recorrido completo del guion cabe en 90 s de esperas reales | Ensayo con voz, móvil, cuenta y red; `uso_openai.json` a cero |
| Vídeo | 20 | 17 | 720p H.264 2:12, SHA256 igual al registrado (`b18a8322…`), decodifica entero, QR final a Vercel; narración = `guion_revision.json` (13 escenas, 305 palabras, sin cifras) | A2 y A3 |

## Hallazgos

### A1 — Ejecución en Colab real pendiente (MENOR)
- **Rubro:** Notebook · **Afirmación:** «corre desde cualquier Colab sin errores ni warnings».
- **Evidencia:** dos ejecuciones limpias locales (29 sep 19:15 y 30 sep 01:36) con 0 errores y 0 stderr; la última de Colab (29 sep) fue anterior al silenciado del aviso `HF_TOKEN`. Intenté pilotar el Chrome de Miguel para lanzarla en Colab: la conexión (`chrome-devtools`) se quedó 30 minutos esperando el permiso, que nadie podía aceptar a esta hora; por la skill `conectar-google`, un solo intento y no se repite.
- **Acción:** abrir en Colab `entrega/notebook_proyecto.ipynb` (la copia de `entrega/`), «Entorno de ejecución → Ejecutar todo», comprobar 57 celdas sin avisos y adjuntar esa copia a Classroom. Diez minutos con Miguel delante.

### A2 — Qué copia del vídeo va en Classroom (MENOR, decisión de Miguel)
- El borrador lleva el máster 4K HEVC (267,9 MB). El 720p H.264 (12,8 MB) es el mismo corte y se reproduce en cualquier sitio. **Acción:** sustituir, o comprobar que el 4K descargado se reproduce fuera del navegador.

### A3 — Eos narra el vídeo (MENOR, riesgo a gestionar)
- La rúbrica pide la cara del alumno; el profesor aceptó la excepción (27 y 29 sep, sin texto archivado). `mensaje_profesor.md` l. 66 lo deja por escrito. Plan B: `guion_video.md`. **Acción:** guardar la respuesta del profesor si llega.

### A4 — Classroom (proceso)
- Los adjuntos de Classroom son copias: la presentación (19:11) y el notebook (19:15) corregidos ayer, y el documento, la estrategia y los anexos cambiados ayer por la tarde, **hay que volver a subirlos** si se adjuntaron antes de esas horas. Pulsar «Entregar» antes del 4 oct 11:59 p.m. No se pudo comprobar desde aquí.

### A5 — `uso_openai.json` a cero (proceso)
- Antes de dar la cuenta al profesor. Escribir en el bucket necesita el permiso explícito de Miguel en la sesión.

### Cerrado desde ayer (verificado hoy)
- A1 del 29 (copia local sin salidas): `entrega/notebook_proyecto.ipynb` es la copia ejecutada en limpio.
- A2 del 29 (aviso `HF_TOKEN`): silenciado en la primera celda; 0 stderr en las dos ejecuciones.
- A6 del 29 (variantes viejas): 514 aclarado como histórico; diapositiva 4 con el catálogo final; las citas del Space estático son respaldo declarado en los cinco archivos.
- A5 del 29 (foto de la entrega): `entrega/` en `34c6be1` (sin el 4K).

## Lo que no se pudo verificar
- Colab real (A1); `LiteraLevel_V4_reproducible.ipynb` en modo `verify` necesita el paquete de datos de Drive (`literalevel_bigdata/entrega_profesor_v4`), que no está en esta máquina; los otros dos anexos no se ejecutan por diseño (lotes de horas y GPU).
- Las 55 páginas del documento no leídas hoy; audio del vídeo; cuenta, cupo, voz y micrófono; estado de Classroom.

## Siguiente paso (por puntos por hora)
1. Con Miguel delante: ejecutar el notebook en Colab y adjuntar esa copia (15 pts, 10 min).
2. Volver a subir a Classroom presentación, notebook, documento, estrategia y anexos; decidir el vídeo (720p H.264); «Entregar».
3. Ensayo real de la demo con voz, móvil, cuenta y cronómetro; `uso_openai.json` a cero (25 pts).
4. Si sobra tiempo: lectura de ortografía del documento entero.

## Revisión de las 05:40 (copias bajadas de Drive/Classroom a `Descargas` entre la 01:41 y las 02:16)
- **Documento, estrategia, presentación corregida y los tres anexos: byte a byte iguales a `entrega/`** (SHA256): `Copia de Pleyade_TrabajoFinal_Documento_2026-09-29.pdf`, `…Estrategia…pdf`, `Pleyade_TrabajoFinal_Presentacion_CORREGIDA_2026-09-29.pdf`, `Copia de Pleyade_Anexo_{Verificacion_V4,Precalculo_Catalogo,Eos_V3}_2026-09-29.ipynb`.
- **A1 (Colab real) cerrado con evidencia:** `ENSAYO_NO_ENTREGAR_Pleyade_Notebook_2026-09-30.ipynb` trae `executionInfo` de Colab en las 57 celdas de código (30 sep, 01:45→01:47), orden 1–57, 0 errores, 0 stderr, fuentes idénticas a `entrega/` y el 0,908 en las salidas. El aviso de `HF_TOKEN` ya no aparece en Colab.
- **Nuevo A6 (MENOR, a confirmar):** el cuaderno de Classroom `Pleyade_TrabajoFinal_Notebook_CORREGIDO_2026-09-29.ipynb` se bajó por última vez a las 02:01 **a mitad de una segunda ejecución** (40 de 57 celdas con salida, 01:54→01:55). No se puede ver desde aquí cómo quedó al terminar. Acción: abrirlo en Colab y comprobar las 57 celdas ejecutadas, o volver a bajarlo para medirlo; si quedó a medias, «Ejecutar todo» otra vez o sustituirlo por la copia del ensayo.
- **Nota simulada revisada: 92 / 110** (notebook 14 de 15, a falta de confirmar A6).

## Revisión ampliada (30 sep, tarde): todo lo que se puede comprobar sin Miguel
**Nota simulada: 96 / 110** (documento 14, estrategia 14, notebook 14, presentación 9, interfaz 10, demo 17, vídeo 18).

### Hecho y medido
- **Documento, las 65 páginas** vistas en hojas de contacto y 12 leídas a tamaño real; corrector sobre las 4.425 formas distintas del PDF (sin erratas: lo que marca son flexiones que el diccionario no trae, identificadores de código y artefactos de extracción). **Dos defectos de maquetación corregidos y recompilados** (tectonic, 0 errores, 0 «??», ahora **66 páginas**): los apartados 3.7 y 3.8 quedaban como dos títulos vacíos (sus cuadros 7 y 8 flotaban tres páginas más allá) y los cuadros 3 y 6 tenían una columna de una palabra por línea. Copia anterior en `D:/Temp/claude/lectura/documento_antes.pdf`.
- **Estrategia:** las 20 páginas vistas; corrector sin erratas.
- **Presentación:** las 17 diapositivas vistas a tamaño legible; sin texto cortado.
- **Vídeo, audio incluido:** transcripción local (whisper) del 720p frente a `guion_revision.json`: 305 palabras dichas de 305, similitud 0,93; las diferencias son el reconocedor oyendo «Playjari/Egoz» por Pléyade/Eos y tres palabras sueltas. No se narra ninguna cifra.
- **Interfaz:** además del móvil, escritorio a 1366 px en cinco pantallas: sin desbordamiento ni errores de consola.
- **Demo con la cuenta real** (`miguel`, sin ninguna acción de pago): entrar 0,4 s; la cuenta no tiene tope de usos; búsqueda 0,8–1,0 s; ficha 1,2 s; curva 0,35 s; diccionario de *poverty* 0,8 s; Mis palabras (6 palabras, 16 consultas, «Repasa cinco» visible) y Mi espacio («Donde lo dejaste»: *Crime and Punishment*) en menos de 2,5 s; «Una frase de mi libro» existe en Pronunciar.
- **Notebook ↔ documento:** en las salidas ejecutadas aparecen 0,908, 97,2 %, 53.179, 4.724 y las medias por nivel 0,504…1,495. 0,860, 0,807, 0,668, 585.111 y los errores ordinales 1,39/0,93/0,67 están en el texto del cuaderno, no como salida calculada (el documento dice que salen de `validar_local.py` y del precálculo).

### B1 — La cuenta de la demo no tiene el perfil que dice el guion (SERIO para la demo)
- **Afirmación:** `guion_demo_en_vivo.md` paso 1: «Lees en inglés a nivel B2» y 1,20 en «Ver el detalle»; pasos 2 y 3 descritos «con el perfil de 1,20».
- **Evidencia:** `/api/perfil` de la cuenta `miguel`: **0,72, B1**, origen cuestionario, creado el 27 sep 19:02 (la tarde en que se grabó el comercial). En pantalla: «Lees en inglés a nivel B1». Con ese perfil, «Crimen y castigo de Dostoyevski» abre «En tu nivel» con *The Punishment* y el libro no está en la primera pantalla; el guion espera el aviso «no hay libros en tu nivel» y el libro el primero en «De otros niveles».
- **Acción (dos caminos):** (a) dejar la cuenta en 1,20 antes de ensayar: en *Tu nivel* → repetir el cuestionario marcando la **quinta opción en las seis preguntas** y, en los fragmentos, fácil «Lo entiendo con naturalidad», medio «Capto bien la idea…», difícil «Me pierdo…» (da 1,197, que la app enseña como 1,20; calculado con `perfil.desde_cuestionario`); o (b) reescribir los pasos 1–3 del guion para 0,72/B1, que es además el perfil que se ve en el vídeo.

### Para Miguel
1. **Volver a subir `documento.pdf`** a Classroom (cambió hoy: 66 páginas).
2. Resolver B1 y ensayar la demo.
3. Confirmar el cuaderno adjunto (A6) y la copia del vídeo.

## Auditoría completa (30 sep, noche): lectura íntegra y cierre de lo que salió
**Nota simulada: 96 / 110** (sin cambio respecto a la tarde: lo nuevo confirma, no resta).

### Leído entero
- **Documento:** las 66 páginas, texto completo (unas 35.000 palabras), tras la recompilación de la tarde. Coherente en cifras y fechas con estrategia, presentación, guion de la demo y cuaderno; las salvedades (validación interna no ciega, 38 frente a 47 textos, escala comprimida, Eos sin validar con lectores) están en los tres sitios. Sin erratas detectadas. Referencias en APA con DOI o URL.
- **Estrategia:** las 20 páginas. **Una referencia cruzada caducada corregida:** citaba «Cuadro 21 del PDF —el 16 de la copia de lectura—» para las velocidades y hoy son el **Cuadro 28** del PDF y el **17** del `.md`. Corregido en `estrategia.md` y **`estrategia.pdf` regenerado con la misma receta de la otra sesión** (`tmp/pdfs/make_strategy.mjs` + impresión con Chrome): 20 páginas, maquetación idéntica.
- **Cuaderno:** las 46 celdas de texto (12.000 palabras). **Una cifra desalineada corregida:** decía «solo 599 libros en A1–B1» y el Cuadro 11 del documento suma 1 + 40 + 557 = **598** (tras la corrección de PG2242). Corregido en el `.py`, `.ipynb` regenerado y **ejecutado otra vez en carpeta limpia: 57 celdas, 1–57, 0 errores, 0 stderr**. Las cifras centrales (0,908, 97,2 %, 53.179, 4.724, medias por nivel) salen de las celdas ejecutadas; 0,860, 0,807, 0,668 y 585.111 van en el texto, calculadas fuera (`validar_local.py`, precálculo), y el propio cuaderno lo declara.
- **Presentación:** texto completo de las 17 diapositivas; la 13 declara el 1,20 como «caso ilustrativo, no una sesión registrada», coherente con B1 (la cuenta está en 0,72).
- **Mensaje al profesor:** completo; sin contraseñas, enlace de Vercel, topes iguales a los del documento, Eos presentada como está.
- **Interfaz, de nuevo en el build de hoy** (`main-G2GOFZ7O.js`, con los tres commits del reproductor de lectura de la otra sesión): el recorrido de la demo a 390×844 sigue entero, sin errores de consola, Eos y boca 3D funcionando.

### Para volver a subir a Classroom
1. `documento.pdf` (tarde: 66 páginas).
2. `estrategia.pdf` (noche: referencia al Cuadro 28).
3. `notebook_proyecto.ipynb` (noche: 598; ejecutado en limpio aquí; lo ideal, ejecutarlo en Colab y adjuntar esa copia).

### Sigue en pie
- **B1:** perfil de la cuenta `miguel` en 0,72/B1 frente al 1,20 del guion de la demo (receta arriba).
- Ensayo de la demo con voz; copia del vídeo (720p H.264); `uso_openai.json` a cero; «Entregar».
