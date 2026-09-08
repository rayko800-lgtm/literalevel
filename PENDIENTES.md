# Pendientes de LiteraLevel

Actualizado: 8 de septiembre de 2026, 15:50.

La rúbrica son 110 puntos y se aprueba con 80. El orden de esta lista es por
puntos que están en juego, no por comodidad.

---

## Bloqueado en Miguel — nadie más puede hacerlo

| Qué | Desbloquea | Por qué solo tú |
|---|---|---|
| **Token de Hugging Face** | **15 pts** (notebook reproducible) | Publicar el modelo v4 y el diccionario. Hoy el notebook no corre en un Colab limpio porque los pesos solo existen en tu disco. Media hora de trabajo, y es lo que más puntos por minuto da de toda la lista |
| **Micrófono** | parte de **25 pts** (demo en vivo) | Sin él no se puede enseñar la corrección de pronunciación, que es lo que el profe pidió ver. Unos audífonos con micro bastan |
| **Despliegue permanente** | protege **25 pts** | El enlace de hoy muere al apagar la computadora. Hugging Face Spaces son 9 USD/mes, y desde 2026 una cuenta gratuita no puede crear un Space de Gradio |
| **Conector de Drive** | ver el catálogo | claude.ai → Ajustes → Conectores → Google Drive. Está autenticado pero rechaza toda operación |
| **Aceptar la pestaña de Colab** | ver las descargas | Ojo: conectó con la cuenta de Miguel Reyes y el Colab Pro está en rayko800 |

---

## En marcha

- [x] **Bandas del lector** — arregladas y subidas. Ya no puede salir "C1" e
      "intermedio" en la misma línea
- [x] **Auditoría externa de Astra** — 24 hallazgos, informe en
      `auditoria/informe_codex.md`
- [x] **Investigación de competencia y diseño del v5** — en `investigacion/`
- [ ] **H02: fuga de datos del vocabulario** — el único hallazgo que exige
      recalcular. Rehacer la lista de palabras familiares solo con
      entrenamiento y volver a medir los modelos clásicos. CPU, sin GPU
- [ ] **H01, H03, H04: redacción** — llamar a los 950 extractos "validación de
      selección", a los sextiles "sextiles de facilidad de CLEAR", y retirar la
      palabra "techo" del PCA
- [ ] **Corregir la frase falsa del SPGC** — el documento dice que producción
      usa esa lista externa y no usa ninguna
- [ ] **Apartado de competencia** — en Estrategia completo y condensado en el
      documento, con tres figuras en TikZ. Barranco exige negocio antes de
      concluir
- [ ] **Segunda auditoría de Astra** — programada para las 18:52, cuando
      recupera créditos, ya sobre el texto corregido

---

## Sin empezar

- [ ] **Presentación (10 pts)** — se deriva del documento, es lo último
- [ ] **Grabar el vídeo (20 pts)** — el guion ya está escrito y en LaTeX

---

## Decisiones que quedan abiertas

- **Recalibrar la escala.** Un texto A1 se anuncia como A2. Corregirlo es
  recalibrar, y la recta se ajustó con textos de examen, no con novelas. No se
  toca sin validar contra el catálogo
- **Limpiar el Drive.** Pendiente de que vuelva el conector. Antes de borrar
  nada va una lista de qué hay y qué pesa: en esa carpeta viven los pesos del
  v4 y no hay otra copia
- **El modelo v2 de Codex.** Gana en material graduado y pierde en literatura,
  que es nuestro caso de uso. No entra en esta entrega
