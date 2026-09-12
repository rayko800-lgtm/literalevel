# Plan hasta el 3 de octubre de 2026

Escrito el **sábado 12 de septiembre de 2026**, después de que el profesor viera
la aplicación. Quedan **21 días exactos**. La entrega es el **sábado 3 de
octubre**: documento, estrategia, cuadernillo, interfaz, presentación, vídeo y
demo en vivo, todo el mismo día.

---

## 1. Lo que dijo el profesor, traducido

Dijo cinco cosas: migrar a Angular, que la interfaz sea más llamativa y
retenedora, que el formulario es tortuoso, que Colores toma demasiada
presencia, y que sea más orientativa.

**Las cinco son la misma queja: la aplicación te obliga a decidir antes de
saber qué hace.** Hoy lo primero que ves son **ocho pestañas** —Mi nivel,
Buscar lectura, Leer, Pronunciación, Mis libros, Mis palabras, Colores,
Estado—, un formulario y un selector de paletas. Nadie te ha dicho todavía para
qué sirve esto. Un menú te pregunta; una secuencia te lleva.

El arreglo, por tanto, no son cinco arreglos: es **cambiar el menú por un
recorrido**. Y eso vale igual en Gradio que en Angular, así que el diseño se
hace una vez y se implementa dos.

**Esto también es material del documento.** Un apartado corto que diga «la
primera versión era un panel de control y la segunda es un recorrido, y este es
el motivo» vale puntos de interfaz que una captura bonita no da.

---

## 2. Las dos decisiones de arquitectura, resueltas

### 2.1 Angular no puede llevarse el modelo dentro. Ni falta que hace.

`modelo_v4/` son 332 MB, el diccionario Kaikki otros 243, y la aplicación
ocupa **1,05 GB de RSS** medidos con torch, spaCy y MiniLM cargados. Eso no
entra en un front-end ni en una función *serverless* —por eso Vercel estaba
descartado desde antes de que lo descartaras tú—.

Así que la migración solo puede significar una cosa, y es la buena:

    Angular (estático, gratis)  ->  HTTP  ->  Python en el Space (el motor)

**Y esto es una mejora que contar, no una concesión.** Ahora mismo interfaz y
motor son el mismo proceso; separarlos es lo que permite que mañana haya una
app de móvil, o que otro front consuma lo mismo. En el documento se escribe
como decisión de arquitectura, no como parche.

**Dónde vive cada cosa:**

- El motor se queda **donde ya está y ya funciona**: `MikeMaki1763/literalevel`,
  7 USD/mes ya pagados, arranque medido en 32 s.
- La API es un archivo **nuevo**, `app/api.py`, con FastAPI, montada en el
  **mismo proceso** que Gradio (`gr.mount_gradio_app`). Un solo despliegue
  sirve las dos cosas: el plan B en `/` y la API en `/api`. No hay que pagar
  nada más ni administrar un segundo servidor.
- El front de Angular compila a estáticos y va a un **Space de tipo `static`**
  de la misma cuenta. Cero proveedores nuevos, cero cuentas nuevas, y el
  despliegue es el mismo `git push` que ya sabes hacer.

### 2.2 Qué significa exactamente «el código no se toca»

Hay que afinarlo o no se puede trabajar:

| | |
|---|---|
| **Congelado de verdad** | `scoring.py`, `reader.py`, `lexicon.py`, `voz.py`, `perfil.py`, `catalogo.py`, `ficha.py`, el modelo v4. Todo lo que **mide**. Diecisiete auditorías lo avalan y ninguna cifra publicada puede moverse |
| **Es lo que hay que cambiar** | `app/ui.py`, 3.608 líneas. Es la interfaz, y la interfaz es justo lo que el profesor pidió rehacer |
| **Nuevo, no tocado** | `app/api.py` y el proyecto de Angular. Código nuevo que **lee** los módulos congelados sin modificarlos |

Y una regla que no se relaja por ser «solo interfaz»: **cada cambio de `ui.py`
entra en `tools/banco_mutantes.py` con su prueba**. Ese banco tiene 88 mutantes
y es la razón por la que este proyecto sabe que sus pruebas prueban algo. La
auditoría 17 encontró un crítico en una línea de interfaz que llevaba semanas
ahí. No es momento de aflojar.

---

## 3. La interfaz nueva, en concreto

### 3.1 La puerta: tres opciones y nada más

Al abrir, pantalla limpia, el título, una frase de qué es esto, y tres
botones grandes:

| Botón | A dónde lleva |
|---|---|
| **Solo quiero mirar** | Directo a un libro abierto, ya leyéndose. Sin perfil, sin formulario, sin nada. Puedes tocar palabras desde el segundo uno |
| **Mídeme** | El formulario, pero convertido en conversación (§3.2) |
| **Pregúntame** | El buscador: escribe un autor o un título y ve qué pasa |

Es tu idea, y es la correcta. La razón por la que funciona: **cada puerta
enseña el producto antes de pedir nada**, y las tres desembocan en el lector,
que es lo bueno que tiene esta aplicación.

### 3.2 El formulario deja de ser un formulario

Hoy son varios campos a la vez en una pantalla. Pasa a ser **una pregunta por
pantalla**, con respuestas en botones grandes y una barra de «2 de 5». Cuatro
reglas:

1. **Nunca dos preguntas a la vez.**
2. **Se puede salir en cualquier momento** con lo respondido hasta ahí: con
   dos respuestas ya damos un perfil, más burdo pero útil. Un formulario que
   solo sirve entero es un formulario que se abandona.
3. **Cada respuesta enseña algo.** Después de la primera ya aparece una
   estimación provisional, y se ve moverse con cada respuesta. Eso es lo que
   retiene: ver que tu acción hace algo.
4. **Textos cortos y que suben de nivel**, como dijiste. La primera pregunta se
   entiende sin saber qué es el MCER; el vocabulario técnico aparece más tarde,
   cuando ya te importa.

### 3.3 Colores, a una esquina

Un icono de paleta arriba a la derecha que abre un panel lateral. Las cinco
paletas siguen ahí y las pruebas de contraste siguen midiéndolas —son **85
parejas** y no se tocan—, pero dejan de competir con el contenido. Lo mismo
con **Estado**: sale de la barra de pestañas y pasa a ser una página aparte
con su enlace propio. Es diagnóstico, no es para el lector.

### 3.4 De ocho pestañas a tres sitios

    LEER        el libro, el diccionario, el cuaderno de palabras, la pronunciacion
    ENCONTRAR   el buscador, la ficha, tus libros
    TU NIVEL    el perfil, la curva, tu progreso

Nada desaparece: **Mis palabras** y **Pronunciación** viven donde se usan, que
es dentro del lector, no en una pestaña a la que hay que acordarse de ir.

### 3.5 Más orientativa

Regla única, aplicada en todas las pantallas: **cada una responde en una línea
dónde estás, qué pasa si pulsas y qué viene después.** Y donde algo tarda —la
curva son 134 s en frío, la primera consulta léxica 55 s— se dice qué está
pasando y cuánto queda, en vez de dejar una rueda girando. Un tiempo de espera
explicado deja de ser un fallo y pasa a ser una demostración de que está
trabajando.

---

## 4. Los tres objetivos que añadiste

### 4.1 El corpus que no se puede publicar — resuelto, y sin pedir permiso a nadie

Fui a mirarlo y el problema es más pequeño de lo que parecía. El corpus con
derechos son los **59 PDF de British Council LearnEnglish**, y el detalle que
lo cambia todo es este: **son de descarga pública y gratuita**. Lo que no se
puede es **redistribuirlos**. No es que el profesor no pueda tenerlos: es que
no se los podemos enviar nosotros.

Así que no hay que argumentar nada. Hay que **entregar la receta en vez del
plato**, en tres piezas:

1. **`tools/bajar_corpus_bc.py`** — se baja los 59 PDF de
   learnenglish.britishcouncil.org por URL y **verifica cada uno con su
   SHA-256** contra el manifiesto. El profesor ejecuta un comando y tiene los
   mismos archivos, bit a bit, y `validar_local.py` le reproduce las cifras
   exactas.
2. **`entrega/corpus_externo_rasgos.csv`** — una fila por texto: nombre, nivel
   declarado, número de palabras, número de frases, la salida del modelo y los
   rasgos intermedios. **Con esto se recalculan Spearman, MAE y las medias por
   nivel sin tener el texto.** Un recuento no reconstruye un texto, así que no
   hay nada que redistribuir.
3. **El manifiesto que ya existe**, `entrega/manifiesto_corpus_externo.md`,
   ampliado con los hashes.

**Esto es mejor que darle el zip, y hay que decirlo así en el documento.** Un
zip prueba que las cifras existen; un descargador con hashes prueba que
**cualquiera** las puede rehacer, hoy y dentro de dos años. Es la práctica
estándar en investigación con material con derechos, y en la rúbrica es un
punto de gobierno del dato, no una excusa.

Si aun así te pide los archivos: se los pasas en privado con una nota de
alcance —«para evaluar este trabajo, no se redistribuye»— y ya. Pero que sea
petición suya, no oferta nuestra: la respuesta buena la tiene ya sin pedir
nada.

### 4.2 El catálogo entero, medido por el v4

Estado al 9 de septiembre: **31.974 descargados** de 61.642, **29.875 con
perfil del v4**. Lo que falta **no es medir, es descargar** unos 29.700 libros,
y descargar **no necesita GPU ni unidades**. Medirlos después son ~6 h de T4
gratis a los 84 libros/min medidos.

Como esto es tiempo de reloj y no tiempo tuyo, **arranca hoy y corre solo
mientras haces lo demás**. Es lo primero de la lista del día 12.

**Y un aviso que hay que tener presente desde ya**, porque afecta al diseño de
la interfaz que vas a hacer esta semana: los 29.875 ya medidos promedian
**1,75 sobre 2**, con tres cuartas partes en C1 o por encima. Cuando esté el
catálogo entero, es muy probable que confirme que **a un lector de B1 la
literatura del XIX no le ofrece casi nada**.

La respuesta no es tocar el modelo. Es que **la app recomiende capítulos, no
libros**: la curva por capítulo ya está calculada, y en casi cualquier novela
hay capítulos muy por debajo de su media. «Este libro te queda grande, pero
estos tres capítulos no» es una recomendación mejor que un «no hay nada para
ti», y es exactamente el tipo de cosa que solo puede decir un sistema que lee
el libro entero en vez de darle un número. **Eso es interfaz, es lo que
tenemos permitido tocar, y es el mejor argumento del proyecto.**

### 4.3 Más textos graduados

Hoy hay tres fuentes: CLEAR (4.724 extractos), OneStopEnglish (567 textos, 3
niveles) y British Council (59, A1–C1). Cuatro candidatas para ampliar, por
orden de lo que valen **dividido entre lo que cuestan**:

| Candidata | Por qué interesa | Riesgo |
|---|---|---|
| **VOA Learning English** | Tres niveles con vocabulario controlado, miles de artículos, y —si se confirma— **obra del gobierno de EE. UU., o sea dominio público**. Sería un corpus graduado **que sí se puede redistribuir**, y eso resolvería de raíz el problema del §4.1 para el futuro | Hay que verificar la situación legal artículo por artículo, no fiarse |
| **CEFR-SP** (Arase et al., 2022) | Etiquetas MCER explícitas a nivel de frase, en GitHub | Es frase, no texto: sirve para validar, no para entrenar lo mismo |
| **Simple English Wikipedia** alineada | Gratis, enorme, redistribuible | Solo dos niveles, y «simple» no es MCER |
| **RACE** (CMU) | Exámenes de comprensión reales, dos niveles | Requiere aceptar condiciones; puede tardar |

**Dos horas hoy** para comprobar licencia y descarga de las cuatro. Si VOA
sale limpia, son las dos horas mejor invertidas del plan: pasamos de «nuestras
métricas no son reproducibles» a que sí lo sean.

Y una decisión escrita de antemano: **estos corpus entran como validación, no
como reentrenamiento.** El v4 es final. Si un corpus nuevo lo valida, es una
cifra más en el documento; si lo contradice, es una limitación honesta que
también suma. Reentrenar a tres semanas de la entrega sería tirar diecisiete
auditorías a la basura.

---

## 5. El calendario

### Hoy, sábado 12 — las cuatro cosas que desbloquean todo lo demás

- [x] ~~Rotar las nueve contraseñas~~ — **decidido por Miguel el 12 de
      septiembre: no hace falta.** La única que importaba era la de invitado.
- [ ] **Comprar un micrófono.** Unos audífonos con micro valen. **Bloquea los
      20 puntos del vídeo y parte de los 25 de la demo**, y es lo único de la
      lista que no depende de programar.
- [ ] **Arrancar la descarga del catálogo** en Colab con CPU. Corre sola
      varios días mientras haces la interfaz.
- [ ] **Dos horas con los cuatro corpus graduados** (§4.3) y decidir.

### Semana 1 · 13–19 de septiembre — que Gradio deje de ser tortuosa

Esta semana **no es trabajo desechable**. Es (a) el plan B blindado, (b) el
diseño ya validado que Angular copia, y (c) las cinco quejas del profesor
resueltas aunque Angular no llegue.

| Día | Qué |
|---|---|
| Dom 13 | Las tres puertas. Solo eso |
| Lun 14 | El formulario, una pregunta por pantalla |
| Mar 15 | Colores a la esquina · Estado fuera de la barra · ocho pestañas a tres |
| Mié 16 | El lector como pantalla protagonista + los textos orientativos |
| Jue 17 | Pruebas y mutantes de todo lo nuevo · desplegar · **pasada estrecha de auditoría sobre el diff de la semana** |
| Vie 18 | `app/api.py`: los siete endpoints, montados junto a Gradio |
| Sáb 19 | **Grabar el vídeo, toma 1, contra Gradio.** Seguro de 20 puntos |

Los siete endpoints: `/api/salud`, `/api/medir`, `/api/buscar`,
`/api/libro/{id}`, `/api/libro/{id}/capitulo/{n}`, `/api/palabra`,
`/api/curva/{id}`. Ninguno toca los módulos congelados: los llama.

Lo del jueves 17 no es opcional. La lección de la auditoría 17, textual: *una
pasada estrecha sobre un diff pequeño encontró un crítico que una auditoría
completa del día anterior no vio*. Una semana de cambios en `ui.py` es
exactamente ese diff.

### Semana 2 · 20–26 de septiembre — Angular

Aprendes Angular con la API ya viva, que es la única forma de aprenderlo
rápido: cada día una pantalla que funciona de verdad.

| Día | Qué |
|---|---|
| Dom 20 | Angular desde cero: instalar, `ng new`, componentes, servicios, rutas. Día de aprendizaje puro |
| Lun 21 | Las tres puertas |
| Mar 22 | El formulario y el perfil |
| Mié 23 | El buscador y la ficha del libro |
| Jue 24 | **El lector y el diccionario** — es el paso estrella del vídeo, y el que más tiene que lucir |
| Vie 25 | Desplegar el front · CORS · estados de carga y de Space dormido |
| **Sáb 26** | **La puerta. Go / no-go.** |

**El criterio del 26, escrito hoy para no discutirlo con uno mismo ese día:**
los cinco pasos del guion del vídeo se hacen de principio a fin en Angular, en
un navegador limpio, sin abrir Gradio ni una vez. Si sí → Angular es la
entrega. Si no → **Angular se presenta como prototipo funcional con su código y
su arquitectura, y la demo en vivo se hace en Gradio.**

Esa segunda salida no es un fracaso y conviene tenerlo claro desde ahora: el
profesor recomendó Angular a alguien que le dijo que no sabía nada, y llegar en
dos semanas a una API separada y un front que consume su propia arquitectura
es la respuesta a lo que pidió. Lo que sería un fracaso es enseñar un Angular a
medias el día de la demo, que son **25 puntos**.

### Semana 3 · 27 de septiembre – 2 de octubre — los entregables

| Día | Qué |
|---|---|
| Dom 27 | Si el catálogo no ha entrado antes, entra hoy como tarde · recomendación por capítulo a escala de catálogo (§4.2) |
| Lun 28 | Documento: apartado de arquitectura nueva, corpus reproducible, catálogo completo, corpus graduados nuevos |
| Mar 29 | Cuadernillo y estrategia al día con las cifras nuevas |
| Mié 30 | Presentación |
| Jue 1 oct | **Grabar el vídeo definitivo** y montarlo |
| Vie 2 oct | Congelar: recompilar PDF, verificar hashes, **ensayar la demo tres veces con cronómetro**, revocar el token de Hugging Face |
| **Sáb 3 oct** | Entregar |

Sobre el miércoles 30: el ejemplo que subió el profesor son **40
diapositivas** y las nuestras son **13**. No hay que llegar a 40, pero 13 para
un proyecto de este tamaño se queda corto, y es un entregable de 10 puntos que
cuesta una tarde subir.

---

## 6. Los riesgos, y qué se hace con cada uno

| Riesgo | Qué lo tapa |
|---|---|
| **Angular no llega** | Gradio queda entregable el 17 de septiembre. La puerta del 26 decide con una semana de margen, no la víspera |
| **El vídeo son 20 puntos y depende de un micrófono** | Comprarlo hoy. Toma 1 grabada el 19 aunque luego se regrabe |
| **El Space duerme y la demo arranca en frío delante del profesor** | El front avisa mientras despierta; y la aplicación se enciende y se usa **antes** de la demo. Ya está en las notas del guion: primera consulta léxica 55 s, curva 134 s si no está en caché |
| **Rehacer `ui.py` rompe algo que diecisiete auditorías dejaron sano** | Cada cambio con su mutante, y la pasada estrecha del 17 sobre el diff completo de la semana |
| **El catálogo entero dice que no hay nada para un B1** | Ya está previsto: recomendar capítulos (§4.2). Y si sale así, es un hallazgo del proyecto, no un fallo |

---

## 7. Lo que no vamos a hacer, y por qué

- **Reentrenar el modelo.** El v4 es final. Ninguna cifra publicada se mueve.
- **Tocar los módulos que miden.** Solo `ui.py`, `api.py` y Angular.
- ~~Cambiar `catalogo_recomendaciones.csv` antes del 27.~~ **Decidido por
  Miguel el 12 de septiembre de 2026: el catálogo medido entra en la app en
  cuanto esté medido.** El precio, asumido con los ojos abiertos: cambia lo que
  recomienda el buscador, así que las notas del guion del vídeo y las pruebas
  que dependen del catálogo viejo se vuelven a medir ese mismo día.
- **Vercel.** Descartado por ti y, además, imposible: 332 MB de modelo contra
  ~250 MB de límite por función.
- **Entregar el corpus con derechos.** Se entrega el descargador, los hashes y
  los rasgos, que es más y es limpio.
