---
name: auditar-entrega-modulo-5
description: Auditar el paquete de entrega del Módulo 5 de Pléyade (LiteraLevel) rubro por rubro contra la rúbrica de Barranco — documento, estrategia, notebook, presentación, interfaz, vídeo y demo en vivo — y dar una nota simulada con evidencia. Úsala siempre que Miguel diga «audita mi proyecto», «revisa la entrega», «qué nota sacaría», «qué falta para entregar», «pasa la rúbrica», o pida verificar cualquier entregable antes del 4 de octubre o de la demo del 10, aunque no diga la palabra auditoría. No es para auditar el código ni el modelo por sí mismos: para eso están `auditoria-literalevel` y `auditar-proyecto-datos`.
---

# Auditar la entrega del Módulo 5

La rúbrica manda (skill global `modulo-5-literalevel`: 110 puntos, se aprueba con 80, la
demo en vivo pesa 25). Esta skill pone esa rúbrica delante de lo que hay de verdad en
`entrega/`, en `pleyade-app.vercel.app` y en el Space, y saca un informe que Miguel
puede pegar en ChatGPT. Auditar no es corregir: lo que salga se cierra con
`corregir-sin-inventar`.

> **La regla:** cada rubro se califica con lo que un evaluador vería, no con lo que el
> HANDOFF dice que existe. Un PDF que abre no es un documento correcto; un 200 no es una
> app que funciona; un guion no es un vídeo.

## 0. Antes de empezar (10 minutos, no más)

1. Fija el estado: `git rev-parse --short HEAD`, `git status --short`, revisión del Space
   y build de Vercel. Todo hallazgo se cita contra esas revisiones (skill
   `desplegar-en-spaces` §0: la revisión del Space no es un commit).
2. Corre las comprobaciones mecánicas y guarda su salida:
   ```
   python -X utf8 .claude/skills/auditar-entrega-modulo-5/scripts/comprobar_entrega.py --json auditoria/mecanica_<fecha>.json
   ```
   Da una tabla OK / AVISO / FALLO por rubro: secciones y orden del documento, referencias
   sin resolver, PDF más viejos que su fuente, celdas con error en el notebook, duración,
   códec y QR de cada mp4, palabras habladas del guion, cifras que viven en varios archivos
   con variantes viejas, y la salud de Vercel y el Space. **Léela como inventario, no como
   veredicto:** lo que está en OK todavía puede estar mal escrito.
3. Lee `docs/ai/HANDOFF.md` solo para saber qué cambió desde la última auditoría (la
   anterior está en `auditoria/preentrega_<fecha>.md`). No cargues el historial legado.

Política de recursos: una sola sesión, sin subagentes, sin navegador salvo para el
recorrido real de la interfaz (§5). Fable o Codex solo como auditor ciego de un commit
congelado (`auditar-con-modelo-externo`), nunca como coeditores.

## 1. Documento (15) — se lee como Barranco

Con `entrega/documento.pdf` abierto (Read por páginas), no con el `.tex`:

- **Secciones en el orden de la rúbrica** y una estrategia de negocio antes de concluir:
  Barranco considera incompleto un proyecto que acaba en métricas.
- **Cada cifra central rastreable** a su fuente: 53.179 libros y 585.111 capítulos medidos
  (12 sep), Spearman 0,908 en validación **interna, no ciega** (decir «ciega» fue un SERIO
  el 14 sep), 97,2 % de orden CEFR, modelo articulatorio 0,566 frente a 0,443. Si una
  cifra no está en el notebook, en `investigacion/` o en un commit, es un hallazgo aunque
  suene bien.
- **Lo honesto está dicho por el autor** (`modulo-5-literalevel` §8): escala 0–2 propia,
  etiquetas viejas no fiables, muestreo justificado, catálogo sin filtrar por contenido con
  aviso en la ficha. Que lo diga el evaluador antes que el documento cuesta puntos.
- **Kaggle no se usó y se dice**; **Angular y Vercel fueron petición del profesor y se
  dice**; Eos se presenta como lo que es hoy (en Pronunciar con 85 sonidos pregrabados y
  frases nuevas por cola; el fotorrealismo 4K no está demostrado).
- **APA:** `referencias.bib` compila sin «??», autores y años en el texto, sin URL
  sueltas como referencia.
- **Ortografía y redacción se califican:** una pasada de lectura real por páginas, no un
  grep. Anota página y frase.
- Cuadros que se cortan, glifos AFI que faltan (`/uː/` falló el 26 sep), figuras sin pie.

## 2. Estrategia (15)

`entrega/estrategia.md` y su PDF. Tres cosas explícitas y no otras: **accionables** (qué se
hace, no «se podría»), **usuarios** (quiénes y qué necesitan; Esmeralda, 15 años, es el
ciclo real medido y corregido) y **usabilidad del modelo**. Cada accionable tiene que
apoyarse en un resultado vigente; si cita las cinco paletas de Gradio o el Space estático
como producto actual, es DOCUMENTACIÓN. Comprueba que no contradice al documento en
ninguna cifra (el guion mecánico marca variantes).

## 3. Notebook (15) — tiene que correr en Colab limpio

- `entrega/notebook_proyecto.ipynb` **se regenera desde el `.py`** con
  `tools/a_notebook.py`; audita el `.py`, regenera a un temporal y compara celdas.
- La exigencia es «desde cualquier Colab sin errores ni warnings». Las salidas guardadas
  no lo demuestran: **ejecútalo en una carpeta vacía fuera del repo**, sin `.env` ni
  variables `LITERALEVEL_*`, con el modelo bajado de `MikeMaki1763/literalevel-v4`. Si se
  puede, en Colab de verdad (skills `conectar-google` y `precalculo-en-colab`; sin GPU de
  pago, memoria `sin-gasto`). Registra tiempo, celdas, errores y stderr.
- Mismas cifras que el documento; conclusiones y recomendaciones al final; código
  comentado en español legible por el profesor.
- RAM: con el catálogo cargado no cabe otra suite a la vez (memoria
  `memoria-banco-y-arbol-limpio`).

## 4. Presentación (10)

`entrega/presentacion.pdf`, diapositiva a diapositiva con Read: legible en grande, una idea
por diapositiva, se deriva del documento sin cifras nuevas, la de Eos dice «en
desarrollo» solo si sigue siéndolo, la última lleva la acción («mide tu nivel») y un QR que
decodifica a `https://pleyade-app.vercel.app` (el guion lo comprueba). El orden que pide
la plantilla de Barranco está en `oratoria-ansva`.

## 5. Interfaz (10) y demo en vivo (25) — se prueban como una persona

Esto es lo que más pesa y lo que menos se puede auditar desde el código. Skill
`probar-la-app-de-verdad`, con Playwright headless (no toques la pantalla: otra sesión
puede estar usando Unreal) a **390×844 con emulación táctil** y en escritorio:

- Ruta con almohadilla: `https://pleyade-app.vercel.app/#/pronunciar`; la primera vez sale
  el tutorial («Saltar»). La API se sirve desde el Space: `/api/salud` con
  `buscador_listo` true; si el Space dormía, recarga una vez antes de dar fallo.
- **El recorrido del guion de la demo** (`entrega/guion_demo_en_vivo.md`), paso a paso y
  con cronómetro: inicio → cuenta → nivel → Encontrar con la curva → libro y lector →
  palabra → Pronunciar (grabación, corrección, boca 3D, «Ver a Eos») → Mi espacio.
  Cada «Hace:» del guion tiene que existir con ese nombre en pantalla. Apunta segundos
  reales de cada espera (despertar el motor, la explicación de la IA, el audio).
- Cuenta de la demo: `/api/entrar` devuelve `restantes`; que no llegue a la demo con el
  cupo gastado. Contraseñas: nunca en el informe.
- Consola sin errores, nada cortado a 390 px, botones alcanzables con la barra inferior,
  modo Noche si la demo va en Noche.
- Plan B escrito: Space estático de respaldo, vídeo si cae la red, qué se dice si un paso
  se atasca (el guion ya lo prevé: se dice lo que saldría y se sigue).
- Micrófono y cámara probados en la máquina de la demo, no supuestos.

Un test unitario verde no cuenta aquí. Una captura sí.

## 6. Vídeo (20)

Con el mp4 final de `entrega/`:

- **La cara.** La rúbrica escrita exige al alumno «con su cara visible todo el rato», y en
  el comercial habla Eos. El profesor aceptó esa excepción (confirmado por Miguel el 27 sep;
  el texto del profesor no está archivado). El informe lo dice **siempre**, con esas dos
  frases, en el rubro del vídeo: ni lo calla ni lo marca como fallo definitivo. Es un riesgo
  a gestionar (pedir la confirmación por escrito; `guion_video.md` es el plan B con Miguel a
  cámara), no un incumplimiento demostrado. Una revisión que no lo mencione está incompleta.
- ≤ 5:00, MP4 que decodifica entero (el guion lo mide), imagen y audio sin cortes: míralo,
  no solo mídelo. Extrae fotogramas a 0, 25, 50, 75 y 100 % y léelos. Si hay varias copias
  (máster 4K en HEVC y 720p en H.264, mismo corte), el informe dice **cuál se sube**: para
  Classroom, la H.264 se reproduce en cualquier sitio; la HEVC no siempre.
- Lo que se dice coincide con el guion **que de verdad se narra**: desde el corte del 28 sep
  es `tools/video_eos_revision/guion_revision.json` (13 escenas); `guion_video_eos.md`
  es el borrador del 27 y lo dice en su primera línea. Coteja los subtítulos de los
  fotogramas con las escenas del JSON; el guion mecánico cuenta sus palabras. Ninguna cifra
  nueva (en el corte v3 no se narra ninguna: decisión documentada).
- Enseña la app real y las funciones principales (nivel, Encontrar con la curva, palabra,
  pronunciación de una frase), con la marca desde el segundo 0 y el QR al final.
- El informe identifica la copia entregada con bytes y SHA256 (los registrados en
  `docs/ai/video_eos_revision_2026-09-28.md`), y la copia de Drive si la hay.

## 7. Coherencia entre piezas y Classroom

Las mismas cifras viven en documento, estrategia, presentación, guiones, notebook,
README y mensaje al profesor (`corregir-sin-inventar`: la corrección se propaga a los
cuatro archivos). El guion mecánico marca las variantes viejas (Space estático, 61.642,
514 frente a 516 palabras); tú confirmas cada una leyendo el párrafo: citada como respaldo
o como historia fechada es HISTÓRICO CORRECTO, presentada como actual es DOCUMENTACIÓN. En
la primera pasada (29 sep) las cinco citas del Space estático eran respaldo declarado y el
514 era una nota de un corte anterior.

Entrega en Classroom: nombre «Pléyade (proyecto LiteraLevel)», archivos antes del **4
oct 2026, 11:59 p.m.**, demo el **10 oct, turno 5** (leído el 26 sep; la tarea viva no se
pudo abrir por navegador: si Miguel puede, que confirme con una captura). El mensaje al
profesor lleva el enlace de Vercel, la cuenta de prueba **sin** contraseña y no promete
nada que no esté publicado.

## 8. Nota simulada y severidades

Por rubro: puntos posibles, puntos que un evaluador daría hoy, qué evidencia lo sostiene
y qué le falta. Sé conservador: un rubro «PARCIAL» sin prueba en limpio no se lleva más de
dos tercios. Severidades de `auditoria-literalevel`: SERIO (amenaza demo, vídeo,
reproducibilidad o una afirmación central), MENOR, DOCUMENTACIÓN, HISTÓRICO CORRECTO,
POST-ENTREGA. Los SERIOS se avisan a quien vaya a subir archivos, con la Central en copia
(memoria `serio-antes-de-subir`).

## 9. Informe

Un solo bloque ```markdown``` para pegar en ChatGPT (memoria
`formato-reportes-para-chatgpt`), guardado además en `auditoria/preentrega_<fecha>.md`:

```
# Auditoría de la entrega — <fecha>

## Resumen
- Commit / Space / Vercel:
- Nota simulada: NN / 110 (tabla por rubro: puntos, estado, evidencia, falta)
- Serios: · Menores: · Documentación:

## Hallazgos
### A1 — título
- **Severidad:** · **Rubro:** · **Afirmación:** · **Fuente:** (archivo:línea o página)
- **Evidencia:** (lo medido, con comando o captura) · **Resultado:** · **Acción:**

## Lo que no se pudo verificar
## Siguiente paso (por puntos por hora, como modulo-5-literalevel §9)
```

Cierra actualizando `docs/ai/AUDIT_STATUS.md` (estado y evidencia mínima) y una línea en
el HANDOFF con la ruta del informe. No corrijas nada en la misma pasada: lo que salga se
arregla después, medido, con `corregir-sin-inventar`.
