---
name: modulo-5-literalevel
description: La rúbrica del trabajo final del Módulo 5 y el estado real de LiteraLevel frente a cada entregable. Úsala al trabajar en cualquier cosa que se vaya a entregar o calificar — documento, notebook, presentación, interfaz, vídeo, demo en vivo — o al decidir en qué invertir el tiempo que queda. Manda sobre cualquier criterio de otros módulos.
---

# Módulo 5 — el trabajo final, y dónde estamos

**Profesor:** Mtro. Fernando Barranco Rodríguez. **110 puntos, individual.**
Se aprueba con **80**. Máximo 2 faltas. Prohibido grabar las clases.

> **Esta skill manda.** La skill `ciencia-de-datos-g34` reúne cinco módulos con
> cinco profesores, y sus criterios **se contradicen entre sí**: el módulo 2
> recomienda Kaggle y este lo prohíbe; hubo tareas que vetaban el uso de IA
> generativa y aquí es **objetivo declarado del módulo**. Para LiteraLevel, si
> algo choca, gana lo que dice aquí.

---

## 1. La rúbrica, por peso

Estado al **10 de septiembre de 2026**, tarde. Si lees esto más adelante,
comprueba `PENDIENTES.md`, que es el que se actualiza a diario.

| Entregable | Puntos | Estado |
|---|---|---|
| **Demo en vivo** | **25** | ⚠️ enlace permanente ✅ (`MikeMaki1763/literalevel`); falta el **micrófono**, sin el que no se puede enseñar la corrección de pronunciación |
| Vídeo | 20 | guion escrito, cronometrado (561 palabras = 3:44) y en PDF; **falta grabar** |
| Documento | 15 | ✅ `entrega/documento.md` y `.tex` → PDF de 47 páginas |
| Estrategia | 15 | ✅ `entrega/estrategia.md`, absorbida en el `.tex` |
| Notebook | 15 | ✅ 92 celdas, corre entero en un Colab limpio y sin avisos; el modelo está publicado |
| Presentación | 10 | ✅ `entrega/presentacion.tex` → PDF, 13 diapositivas |
| Interfaz | 10 | ✅ hecha, desplegada y probada en producción |

**Lo que queda no es de escribir, es de grabar y de medir**: el vídeo, el
micrófono, y el catálogo entero (bloqueado en las unidades de Colab).

**Lo que más pesa no es el modelo, es la demo en vivo.** El módulo declara que
lo que evalúa es *«hacer que esos modelos sean accesibles y valiosos para un
usuario final»*. Todo se ordena alrededor de esa frase.

---

## 2. Lo que hunde puntos sin remedio

1. **Faltar a la demo en vivo sin avisar = se pierden los 25 automáticamente.**
   Es en la última semana de clases, hay dos días, no hay prórroga.
2. **Kaggle está prohibido como fuente de datos.** Se esperan APIs, web
   scraping o datos corporativos. *(LiteraLevel usa Project Gutenberg y el
   corpus CLEAR: estamos bien, pero hay que decirlo en el documento.)*
3. **El notebook debe correr desde cualquier Colab sin errores ni warnings.**
   Ya corre: el modelo está en `MikeMaki1763/literalevel-v4`, público, y se
   baja sin credenciales. **Y ojo con la palabra «warnings», que es literal:**
   el Hub avisa por stderr de que la descarga va sin token («You are sending
   unauthenticated requests to the HF Hub»), y ese aviso contaba. Se silencia
   ese canal justo antes de cargar el modelo, con
   `huggingface_hub.utils.logging.set_verbosity_error()` y la razón escrita al
   lado. Probado: ni `HF_HUB_DISABLE_XET` ni `HF_HUB_DISABLE_IMPLICIT_TOKEN`
   lo callan; lo que funciona es eso o `HF_HUB_VERBOSITY=error`.
   El diccionario Kaikki sigue sin publicar (243 MB), y el cuadernillo no lo
   necesita.
4. **El vídeo es MP4, máximo 5 minutos, con su cara visible todo el rato.**
5. **Ortografía y redacción se califican.**

---

## 3. Documento (15 pts)

Secciones exigidas, en este orden:

Introducción/abstract accesible para público general · Planteamiento del
problema · **Estrategia** · Descripción de los datos (fuente, calidad,
relevancia) · Análisis exploratorio · Procesamiento de datos **con
justificación de cada transformación** · Modelación supervisada y/o no
supervisada · Resolución del problema · Conclusiones · **Referencias en APA** ·
Calidad de escritura y presentación visual.

**Se recomienda LaTeX.** Miguel ya entregó un documento en LaTeX en el módulo 4
y es su mejor modelo disponible: lleva cuadro de decisiones metodológicas *con
las hipótesis rechazadas*, traducción de las métricas a horas de trabajo
ahorradas, limitaciones numeradas y declaración de alcance ética.

**El patrón de Barranco:** el EDA se organiza en univariado / bivariado /
multivariado, y **siempre hay una sección de estrategia de negocio antes de
concluir**. Un proyecto que acaba en métricas y no en negocio está incompleto
para él.

---

## 4. Estrategia (15 pts)

Tres cosas, y las tres explícitas:

- **Accionables concretos y fundamentados** — no «se podría», sino qué se hace.
- **Descripción de usuarios**: quiénes son y qué necesitan.
- **Usabilidad del modelo**.

Para LiteraLevel hay material de primera mano que vale oro aquí: **Esmeralda,
15 años, prepa**, primera lectora ajena al proyecto. Dijo *«está bien difícil de
usar en celular»*, *«casi todo»*, *«la página se siente antigua»* y —lo que más
importa— *«o yo soy muy tonta para esto»*. Eso último es un fallo de diseño
documentado, con su corrección: seis etiquetas reescritas y cinco paletas de
color. Un ciclo de usuario real, medido y corregido, es exactamente lo que
pide este apartado.

---

## 5. Notebook (15 pts)

Organización y secuencia lógica · código limpio y comentado · descripción de
datos y EDA · preparación y limpieza · modelado y evaluación · conclusiones y
recomendaciones · **reproducibilidad: debe correr desde cualquier Colab sin
errores ni warnings**.

**Lo que existe hoy:** `notebook_v4_dump.py` es el volcado crudo del
entrenamiento (290 KB, desordenado) y `colab_precalculo.ipynb` es el precálculo
masivo del catálogo. **Falta el notebook limpio del proyecto**, que es el que se
califica.

---

## 6. Interfaz (10 pts) y demo en vivo (25 pts)

Gradio o Streamlit (o Tableau / Power BI / Looker). Explicación paso a paso,
demostraciones convincentes.

La demo son 3–5 minutos por alumno, cámara abierta, compartir pantalla,
**enfocarse en la usabilidad**, y Q&A.

**Los dos riesgos reales, que no son de código:**

- **El enlace.** Hoy es temporal y muere si se apaga la computadora. Para una
  demo calificada eso no se arriesga: hace falta despliegue permanente
  (Hugging Face Spaces, PRO 9 $/mes — y ojo, desde mediados de 2026 una cuenta
  gratuita **no puede** crear un Space de Gradio).
- **El micrófono.** Esta computadora no tiene. Sin él no se puede enseñar la
  corrección de pronunciación, que es lo más vistoso y lo que mejor encaja con
  «usabilidad para el usuario final». Unos audífonos con micro bastan.

---

## 7. Calendario del módulo (6 semanas)

1. Diseño: **crear una compañía ficticia de IA**, nicho, problema, estrategia
   técnica y de negocio, resolución «en papel», usuario final.
2. Dataset (APIs, scraping; **Kaggle no**), EDA, visualización, limpieza,
   ingeniería de variables fase 1.
3. Baseline, hiperparametría, modelos secundarios, diseño de UI, fase 2.
4. Pipeline, inferencia, desarrollo de UI, despliegue local, fase 3.
5. **Despliegue remoto**, mejoras de interfaz, limpieza y documentación,
   redacción del documento, elevator pitch, vídeo tutorial.
6. Demostraciones en vivo.

⚠️ La semana 1 pide una **compañía ficticia de IA**. Conviene comprobar si eso
se entregó y si el documento debe mantener esa ficción.

---

## 8. Lo honesto de LiteraLevel, que hay que saber decir

Un proyecto se defiende mejor si sus límites los cuenta el autor antes que el
evaluador. Estos están medidos:

- **La escala pública es 0–2 y es propia.** El MCER es el ancla con la que se
  entrenó, no un certificado. La app lo dice en pantalla y el documento debe
  decirlo igual.
- **Las etiquetas del catálogo viejo no son fiables**: eran predicciones de un
  modelo anterior sobre las primeras ~190 palabras. Por eso se está midiendo
  todo de nuevo, libro entero.
- **El muestreo está justificado con datos**: 8 ventanas dan 1.784 y el recorrido
  completo 1.743. La app ofrece las dos opciones y dice cuál usó.
- **Spearman 0.91**, orden CEFR estrictamente creciente en validación ciega.
- **No se filtra el catálogo por contenido**, y es una decisión razonada: es una
  plataforma de literatura. Se avisa al lector en la ficha del libro; no se
  esconde nada.

---

## 9. Prioridad si el tiempo aprieta

Por puntos por hora de trabajo:

1. **Publicar modelo y diccionario** (desbloquea 15 pts, y es media hora).
2. **Despliegue permanente** (protege 25 pts).
3. **Notebook limpio** (15 pts, no existe).
4. **Documento + estrategia** (30 pts juntos, comparten material).
5. **Grabar el vídeo** (20 pts, el guion ya está).
6. **Presentación** (10 pts, se deriva del documento).
