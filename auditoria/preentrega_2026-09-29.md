# Auditoría de la entrega — 29 sep 2026, 18:30 (literalevel-c6, skill `auditar-entrega-modulo-5`)

## Resumen
- **Commit / Space / Vercel:** `master` en `77f036b` con 21 archivos sin commit (entre ellos todo `entrega/`; lo auditado es el disco, no el commit). Space `MikeMaki1763/literalevel` revisión `0547de1`, RUNNING, `/api/salud` ok y `buscador_listo` true. Vercel build `HPL2JHFA`, 85 clips de Eos.
- **Nota simulada: 86 / 110** (aprueba con 80). Conservadora: dos rubros sin prueba en limpio (notebook y ensayo de la demo) no pasan de dos tercios.
- **Serios: 1** (A1, causado por esta auditoría) · **Menores: 4** · **Documentación / histórico correcto: 3**.
- Comprobación mecánica: `auditoria/mecanica_2026-09-29.json` (37 OK · 5 avisos · 1 fallo).

| Rubro | Puntos | Hoy | Evidencia | Falta |
|---|---|---|---|---|
| Documento | 15 | 13 | 65 pp., secciones en el orden de la rúbrica, 0 «??», 45 referencias; p. 23 «No se usó Kaggle»; Angular/Vercel como petición del profesor; §7.9 Eos al día (85 sonidos, 28 sep); validación «interna» (la única «ciega» es la de los auditores externos, p. 56); páginas 1, 2, 23, 46 y 60 leídas como imagen, limpias | Lectura completa página a página (se leyeron 5 de 65) |
| Estrategia | 15 | 13 | 20 pp.; accionables (Cuadro 6, con coste y criterio), usuarios (Esmeralda, Laura, Ismael), usabilidad; las cinco paletas se presentan como corrección de «la interfaz de entonces (Gradio)», no como producto actual | Cotejo cifra a cifra con el documento (el mecánico no encontró variantes) |
| Notebook | 15 | 8 | Fuentes del `.ipynb` idénticas a `notebook_proyecto.py` (103 celdas). La ejecución en Colab de hoy la documenta `auditoria/cierre_entrega_2026-09-29.md` (1–57, sin errores, 1 aviso `HF_TOKEN`) | **Ver A1:** la copia local con salidas se perdió en esta auditoría; hay que volver a bajarla de Colab. Sin ella el repositorio no lo demuestra |
| Presentación | 10 | 9 | 17 diapositivas; QR de la última decodifica a `pleyade-app.vercel.app` y la URL va en texto; diap. 10 de Eos al día; diap. 4 con 61.642 fechado «7 sep» (A6) | Ensayo cronometrado en la pantalla real |
| Interfaz | 10 | 9 | Recorrido real a 390×844 en producción: inicio 2,9 s, búsqueda 0,9 s (24 libros), ficha y lector inmediatos, tabla AFI 1,6 s, Eos reproduce, boca 3D en 9,6 s; 0 errores de consola; sin desbordamiento horizontal | Cuenta, corrección de voz y micrófono (no se prueban sin gasto) |
| Demo en vivo | 25 | 17 | `guion_demo_en_vivo.md` al día (29 sep): 10 oct turno 5, Vercel, Eos, plan B por paso; el recorrido del guion funciona en menos de 90 s incluidas las esperas | **Ensayo con voz, móvil, cuenta y red reales**; `uso_openai.json` a cero antes de dar la cuenta al profesor (nota en `mensaje_profesor.md`) |
| Vídeo | 20 | 17 | `pleyade_eos_comercial_v3_720p.mp4` 2:12, H.264+AAC, decodifica entero, SHA256 igual al registrado, QR final a Vercel; fotogramas a 0/25/50/75/100 %: marca desde el segundo 0, app real (Encontrar, lector, Pronunciar con la corrección) y cierre con QR; guion narrado `guion_revision.json` (13 escenas, 305 palabras, sin cifras) | Decidir la copia que se sube (A3) y la excepción de Eos (A4) |

## Hallazgos

### A1 — La copia local del notebook ejecutado se perdió en esta auditoría
- **Severidad:** SERIO (reproducibilidad; causado por mí) · **Rubro:** Notebook
- **Afirmación:** `entrega/notebook_proyecto.ipynb` conserva la ejecución en Colab del 29 sep (celdas 1–57, salidas guardadas).
- **Fuente:** `entrega/notebook_proyecto.ipynb` (mtime 18:08:52).
- **Evidencia:** a las 18:08 ejecuté `tools/a_notebook.py entrega/notebook_proyecto.py` para comparar fuentes y el guion regenera el `.ipynb` **en su sitio**: ahora tiene 0 salidas y 0 `execution_count` (antes: 57 celdas con salida, 1 stderr). Las fuentes siguen siendo idénticas al `.py`. `HEAD` guarda una versión anterior con salidas de otra ejecución, no la de hoy.
- **Resultado:** el repositorio ya no contiene la prueba de ejecución de hoy. La entrega no está afectada si el borrador de Classroom apunta a la copia de Drive ejecutada en Colab (así lo describe `cierre_entrega_2026-09-29.md`).
- **Acción:** en Colab, «Archivo → Descargar .ipynb» de la copia ejecutada y sobrescribir `entrega/notebook_proyecto.ipynb`; comprobar con el guion mecánico que vuelve a tener 57 salidas. Cinco minutos. La skill queda corregida para regenerar siempre a un temporal (§3).

### A2 — La ejecución en Colab lleva un aviso en stderr y la rúbrica pide «sin warnings»
- **Severidad:** MENOR · **Rubro:** Notebook
- **Fuente:** celda 72 de la copia ejecutada (`UserWarning: Error while fetching HF_TOKEN secret value from your vault…`), según la copia leída antes de A1 y `cierre_entrega_2026-09-29.md`.
- **Evidencia:** el aviso lo emite `huggingface_hub` cuando la cuenta de Colab tiene guardado el secreto `HF_TOKEN` y el cuaderno no corre desde la interfaz; no es un error y el modelo público carga igual.
- **Acción:** volver a ejecutar en una cuenta de Colab sin ese secreto, o silenciar el aviso en la primera celda (`warnings.filterwarnings` sobre `huggingface_hub`), y descargar esa copia (cierra A1 de paso).

### A3 — Qué copia del vídeo se sube
- **Severidad:** MENOR · **Rubro:** Vídeo
- **Fuente:** `entrega/pleyade_eos_comercial_v3_4k.mp4` (267,9 MB, HEVC Main10) y `_720p.mp4` (12,8 MB, H.264); `PENDIENTES.md` dice que el borrador de Classroom lleva el 4K.
- **Evidencia:** mismo corte y duración; el 720p decodifica en cualquier reproductor, el HEVC no siempre fuera del visor de Drive.
- **Acción:** adjuntar el 720p H.264 (o comprobar que el 4K se reproduce descargado, fuera del navegador) y decirlo en el mensaje al profesor.

### A4 — Eos habla en lugar de Miguel
- **Severidad:** MENOR (riesgo a gestionar) · **Rubro:** Vídeo
- **Afirmación de la rúbrica:** el alumno «con su cara visible todo el rato».
- **Evidencia:** el profesor aceptó que Eos narre todo el vídeo (confirmado por Miguel el 27 y el 29 sep; el texto del profesor no está archivado). `mensaje_profesor.md` l. 66 ya lo deja por escrito: «En el vídeo presenta Eos, como usted me autorizó; yo haré la demostración en vivo». Plan B: `guion_video.md` con Miguel a cámara.
- **Acción:** ninguna nueva; si el profesor contesta, guardar la respuesta.

### A5 — Nada de `entrega/` está en un commit
- **Severidad:** MENOR (proceso) · **Rubro:** coherencia
- **Evidencia:** `git status`: documento, estrategia, presentación, notebook, guiones, mensaje y los tres mp4 sin commit; parte son de otras sesiones.
- **Acción:** cuando se suban los archivos, commit **solo de las rutas de `entrega/`** que se entregan (nunca `git add -A`), para fijar la versión exacta.

### A6 — Variantes viejas leídas una a una
- **Severidad:** HISTÓRICO CORRECTO · **Rubro:** coherencia
- `guion_video.md` l. 30: «514 palabras habladas» describe un corte anterior de Codex; el vigente es 516 (l. 24) y el narrado 305 (JSON). Las cinco citas del Space estático (`documento.md` 1455, `estrategia.md` 536, `guion_demo_en_vivo.md` 40, `mensaje_profesor.md` 74, `notebook_proyecto.py` 14) lo llaman respaldo. Diapositiva 4: 61.642 «Gutenberg, 7 sep. 2026», fechado; la cifra final (53.179) va en las diapositivas 12 y 15.
- **Acción:** opcional, aclarar la l. 30 y añadir «(catálogo final: 53.179)» en la diapositiva 4.

### A7 — Pendientes que esta auditoría no puede cerrar
- **Severidad:** POST-ENTREGA / proceso · `uso_openai.json` del bucket a cero antes de mandar la cuenta; pulsar «Entregar» en Classroom antes del 4 oct 11:59 p.m. (el borrador con nueve elementos está «Asignado», según el cierre de hoy).

## Lo que no se pudo verificar
- Ejecución del notebook en Colab limpio (no hay `nbconvert` en esta máquina y la copia local quedó sin salidas, A1).
- Lectura completa del documento y la estrategia (muestra de cinco páginas del documento; ortografía no revisada frase a frase).
- Audio del vídeo (se leyeron fotogramas y subtítulos, no se escuchó).
- Cuenta de la demo, cupo restante, corrección de voz y micrófono (gasto o hardware).
- Estado vivo de Classroom.

## Siguiente paso (por puntos por hora)
1. Bajar de Colab la copia ejecutada del notebook y sobrescribir `entrega/notebook_proyecto.ipynb`; si se reejecuta, en una cuenta sin `HF_TOKEN` (15 pts, 5–20 min).
2. Ensayo real de la demo con voz, móvil, cuenta y cronómetro; `uso_openai.json` a cero (25 pts).
3. Decidir y adjuntar la copia del vídeo (720p H.264) y confirmarlo en el mensaje (20 pts).
4. Commit de las rutas de `entrega/` que se suben; «Entregar» en Classroom antes del 4 oct.
5. Si sobra tiempo: lectura de ortografía del documento y nota en la diapositiva 4.
