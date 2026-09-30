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
