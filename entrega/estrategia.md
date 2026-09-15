# LiteraLevel — Estrategia

**Proyecto integrador — Módulo 5 (Integrador)**
Diplomado en Ciencia de Datos, FES Acatlán (UNAM), Generación 34
Profesor: Mtro. Fernando Barranco Rodríguez
Autor: Miguel Reyes Carrillo
Septiembre de 2026

> Documento complementario de `documento.md`, al que corresponde el apartado 3.
> Aquí se desarrollan las tres piezas que la rúbrica pide de forma explícita:
> **descripción de usuarios**, **usabilidad del modelo** y **accionables
> concretos**. Todas las cifras citadas están medidas; su procedencia se indica
> en cada caso.

---

## El marco: Peldaño, una compañía ficticia

Este trabajo se plantea como el primer producto de **Peldaño**, una compañía
ficticia de inteligencia artificial aplicada a la educación. La ficción es un
requisito del módulo y conviene decir desde el principio **qué es ficticio y qué
no**: la empresa lo es; el modelo, la aplicación desplegada, el corpus, las
métricas y cada cifra de este documento, no. Todo lo que se afirma aquí está
medido, y qué parte se puede además *reproducir* desde el repositorio y cuál no
está dicho sin adornos en el documento principal: el código, la inferencia
desde los pesos públicos y las métricas del entrenamiento del v4 se rehacen
desde el repositorio, con datos públicos; lo único que no se redistribuye es el
corpus de British Council, que se reconstruye con su manifiesto.

El nombre no es decorativo. En adquisición de segundas lenguas, la hipótesis del
*input* comprensible sostiene que se aprende con material que está justo un
escalón por encima de lo que uno ya domina (Krashen, 1985). Ese escalón es el
peldaño, y encontrarlo es exactamente el problema que el lector no puede
resolver solo.

**El nicho.** Peldaño no compite en el mercado general de aprendizaje de
idiomas, que está saturado y lo dominan aplicaciones de repetición espaciada. Se
sitúa en un hueco más estrecho y peor atendido: **la lectura extensiva en inglés
para hispanohablantes que ya tienen base**, entre A2 y B2. Es el tramo donde el
estudiante ya no cabe en el material graduado, todavía no aguanta una novela sin
ayuda, y abandona. El apartado 5 documenta contra quién se compite y dónde se
pierde.

**La propuesta de valor, en una frase.** Convertir una biblioteca gratuita e
inabarcable —Project Gutenberg— en una estantería personal ordenada por lo que
cada lector puede leer hoy.

**Cómo se sostendría.** La pregunta de negocio no es cómo cobrar por el modelo,
que es pequeño y replicable, sino quién paga la parte cara. Medido en este
proyecto: **medir un libro, leerlo, buscar y consultar el diccionario no cuestan
nada** —corren en local sobre datos abiertos—, y solo tres acciones salen a un
servicio externo de pago: explicar una palabra en su frase, resumir un libro y
corregir la pronunciación. Esa separación, que en la aplicación es una puerta de
acceso con cupo por perfil, es también la frontera natural entre un nivel
gratuito y uno de pago, y no hubo que diseñarla: salió de medir qué costaba cada
cosa.

El cliente institucional —el docente de inglés del apartado 2.3— es el que
justificaría una tarifa, porque su necesidad no es leer sino *asignar*: repartir
lecturas de dificultad medida, y medida capítulo a capítulo, sin tener que
leerse cuarenta libros antes. Conviene decir qué es esto y qué no: hoy el
producto **no hace seguimiento de alumnos**, ni puede hacerlo tal como está
construido —los datos de cada lector se guardan separados y no se comparten—, y
la declaración de alcance del documento principal descarta expresamente usar
esta medida para decisiones con consecuencias para el evaluado. El producto que
hay sirve al docente para *elegir textos*; un panel de seguimiento sería otro
producto.

**Lo que Peldaño no promete.** No promete enseñar inglés, ni certificar un
nivel, ni sustituir a un profesor. Mide la dificultad de un texto en una escala
propia de 0 a 2 y la pone al lado del nivel estimado del lector. Las
limitaciones del documento principal enumeran los límites de esa medida, y la
aplicación los dice en pantalla en vez de esconderlos.

---

## 1. La apuesta, en un párrafo

La lectura extensiva es uno de los métodos con más respaldo para aprender una
segunda lengua (Nakanishi, 2015), y sin embargo casi nadie la practica bien, porque elegir el
libro adecuado es un problema que el lector no puede resolver solo. LiteraLevel
convierte una medida continua de dificultad —producida por un modelo que lee el
texto entero, no la portada— en tres decisiones cotidianas: **qué leer ahora**,
**por dónde se va a complicar** y **qué significa esta palabra en esta frase**.
El activo defendible no es el modelo, que es pequeño y replicable: es la cadena
completa desde el corpus hasta el pulgar de una persona de quince años en un
teléfono.

---

## 2. Descripción de usuarios

Tres perfiles, con lo que cada uno necesita y con lo que hoy hace en su lugar.
No son personas inventadas para rellenar: el primero está observado
directamente (apartado 3) y los otros dos se derivan de las peticiones reales
recogidas durante el desarrollo.

### 2.1 Usuaria primaria — la estudiante de preparatoria

**Perfil.** 14 a 18 años. Estudia inglés en la escuela, entiende bastante más
de lo que cree, no sabe qué es el MCER y no le interesa. Entra desde el
teléfono, casi siempre en vertical, y en pantallas de unos 390 px de ancho.
Su tolerancia a la fricción es de segundos.

**Qué necesita.**

| Necesidad | Cómo se atiende |
|---|---|
| Saber por dónde empezar sin sentirse examinada | Seis preguntas sobre hábitos observables —con qué frecuencia lee, si necesita diccionario, si ve series sin subtítulos, si ha terminado un libro entero— y **cero jerga gramatical** |
| Juzgarse ante algo real y no ante una descripción | Tres fragmentos literarios en escalera (*Alice*, Sherlock Holmes, *Frankenstein*), pintados con la tipografía del lector para que se lean como un libro y no como un formulario. Pesan 0,65 en el cálculo del nivel: delante de un texto real la gente se juzga mejor que describiéndose |
| Que le propongan algo, no una biblioteca | La pestaña «A mi nivel» de *Encontrar*, que propone lecturas sin escribir nada |
| Poder usarlo con el pulgar | Objetivos táctiles de 44 px, controles repartidos en filas que caben en 390 px, mandos de navegación también debajo del texto |
| No perderse | Al terminar el cuestionario, un enlace que salta directamente al buscador **con la recomendación ya hecha** |

**Qué hace hoy en su lugar:** elige por portada o por título conocido, abandona
a las tres páginas y concluye que el problema es ella.

### 2.2 Usuario secundario — el adulto autodidacta

**Perfil.** 25 a 55 años. Ya lee en inglés con esfuerzo. Su problema no es
empezar, es **subir de escalón sin abandonar**. Tiene libros a medias y no
recuerda por dónde iba en ninguno.

**Qué necesita.**

- **Continuidad.** «Mis libros» guarda cada libro empezado con su barra de
  avance y el capítulo por el que iba, y lo reabre exactamente ahí. Es la
  petición literal que originó el módulo: *«un apartado con mis libros, los que
  estoy leyendo, que se queden guardados, en qué partes voy»*.
- **Saber a qué se enfrenta antes de comprometerse.** La ficha del libro dice
  cuánto tarda en leerlo **a 180 o 110 palabras por minuto** según le quede por
  debajo o por encima de su nivel, cuánto es diálogo y qué palabras se
  repiten, todo contado sobre el fichero.
- **Vocabulario que persista.** «Mis palabras» guarda cada consulta con su
  frase y su libro, que es la unidad que sirve para recordar. Deliberadamente
  **no hay puntos ni rachas**: la evidencia sobre recompensas externas (Deci,
  Koestner & Ryan, 1999) indica que premiar una actividad que ya gusta la
  deteriora, y leer ya es gratificante.
- **Pronunciación.** Lee bien y suena mal, y nadie se lo corrige. La aplicación
  marca palabra por palabra qué sonó bien y qué no.

### 2.3 Usuario institucional — el docente de inglés

**Perfil.** Da clase a grupos heterogéneos y necesita repartir lecturas
graduadas. No puede leerse cuarenta libros para clasificarlos.

**Qué necesita.**

- Un catálogo **medido**, no etiquetado a ojo, con la dificultad por capítulo
  para poder asignar fragmentos y no obras completas.
- Una declaración honesta de lo que la herramienta no es, para poder usarla sin
  incurrir en una promesa que no puede cumplir: **LiteraLevel no certifica
  ningún nivel del MCER**.
- Reproducibilidad: poder comprobar de dónde salen los números.

Este perfil es el que justifica dos decisiones que a un usuario final le dan
igual: publicar el guion de validación y mantener el aviso de alcance visible.

---

## 3. El ciclo de usuario real: Esmeralda

La única prueba que vale es la que hace alguien que no sabe dónde hay que
pulsar. **Esmeralda, 15 años, estudiante de preparatoria**, prima del autor, fue
la primera persona ajena al proyecto que usó la aplicación. Lo que dijo, sin
edulcorar:

> *«Está bien difícil de usar en celular.»* — ¿Qué parte? — *«Casi todo.»*
>
> *«No me gustan los colores… la página se siente antigua, todo muy recto, muy
> marcado.»*
>
> *«¿Qué es eso de 10?»*
>
> *«O yo soy muy tonta para esto.»*

La cuarta frase es la importante, y es la que ordena todo lo que vino después.
**Cuando un usuario concluye que el tonto es él, el fallo es del diseño.**
Krug (2014) formula la misma idea como regla de producto: si el usuario tiene
que pensar para entender un control, el control está mal. A partir de ahí se
diagnosticó qué producía cada queja y se corrigió.

### 3.1 Diagnóstico y corrección

| Lo que dijo | Diagnóstico | Corrección | Verificación |
|---|---|---|---|
| «¿Qué es eso de 10?» | La etiqueta «Resultados» junto a un número no dice qué cuenta | «¿Cuántos te propongo?», con explicación | Etiqueta reescrita |
| Creyó que «Recomiéndame por nivel» tendría en cuenta sus gustos | La etiqueta prometía más de lo que hacía | «Sorpréndeme con algo de mi nivel» | Etiqueta reescrita |
| — | «Ajustar a mi nivel» es abstracto | «Acercar los resultados a mi nivel · no descarta libros» | Etiqueta reescrita **dos veces**: la primera versión, «Solo libros que pueda leer», prometía un filtro que la búsqueda no hace |
| — | «Medir la dificultad de este capítulo» es lenguaje de laboratorio | «¿Cómo de difícil es este capítulo?» | Etiqueta reescrita |
| — | «Vistazo rápido a la dificultad» no dice cuánto tarda | «Vistazo rápido (unos segundos)» | Etiqueta reescrita |
| — | «Analizar el libro entero» no advierte del coste | «Leer el libro entero (tarda más)» | Etiqueta reescrita |
| «No me gustan los colores» | El color es gusto, y el gusto no se discute: se ofrece | **Cinco paletas** con pestaña propia y cambio instantáneo: *hielo* (la original), *amanecer* (clara, crema y naranja), *menta*, *papel* (para leer horas) y *medianoche* | Una prueba automática comprueba las cinco contra el criterio de contraste **WCAG AA (4,5:1)**. Las cinco pasan en las **ochenta y cinco parejas** de color que se comprueban —diecisiete por paleta, cada una con su umbral: 4,5:1 para el texto normal y 3:1 para el título grande—. La más ajustada del texto normal mide **4,53** y la del título, **3,11** |
| «Todo muy recto, muy marcado» | Esto no es gusto, es diseño, y se corrige para todas las paletas | Esquinas de 14 px, bordes finos, sombras suaves y las opciones de lista como fichas tocables | — |
| «Difícil de usar en celular… casi todo» | En un móvil, el círculo de un botón de radio es un blanco de 12 px | La ficha entera pasa a ser el blanco: **44 px** | — |

*Cuadro 1. Del comentario de una usuaria a un cambio verificable.*

### 3.2 Lo que ya se había corregido antes, por la misma vía

El ciclo de Esmeralda no fue el primero. Probar la aplicación en un teléfono
real —y no en el navegador del escritorio— había descubierto antes fallos que
**ninguna de las 303 pruebas automáticas podía encontrar, porque todos
necesitaban un dedo y una pantalla pequeña**:

- El doble toque para consultar una palabra **no funcionaba en el móvil**: el
  código escuchaba solo el evento del ratón, que iOS no emite al seleccionar
  con el dedo. La instrucción en pantalla prometía algo que el dispositivo no
  hacía.
- Los títulos de la tabla de resultados eran enlaces a `gutenberg.org`, así que
  tocarlos **sacaba al lector fuera de la aplicación**.
- El resultado del nivel se pintaba en la parte superior de la página, fuera de
  la pantalla: la usuaria no se enteraba de que había terminado.
- Al pedir «traer una frase del capítulo» sin frase disponible, el campo se
  vaciaba y **borraba lo que el usuario había escrito**, sin decir nada.
- «Mis libros» mostraba 24 entradas llamadas `vacio.txt`, `falso.txt` y
  similares: la batería de pruebas anotaba sus ficheros de ataque en la
  biblioteca **real** de quien las ejecutara. Los datos personales del usuario
  eran el banco de pruebas.

### 3.3 El segundo ciclo: Laura

El 12 de septiembre de 2026 la probó **Laura**, hermana del autor y
desarrolladora web, sobre la aplicación **desplegada**: primero en la laptop y
después en su teléfono Android. Mandó tres capturas y dos notas de voz, que se
transcribieron y se conservan íntegras en `auditoria/feedback_laura_2026-09-12.md`.
Su crítica es de usuaria y de diseñadora a la vez:

> *«Hago el movimiento de deslizar con el dedo y dos, tres segundos y la página
> se empieza a mover.»*
>
> *«No dejas un espacio entre el cuadro y lo que escribes… se come el palito de
> la P.»*
>
> *«Doy a siguiente capítulo y me deja ahí mismo abajo.»*
>
> *«Lo que pones en los tres circulitos son configuraciones, no son
> funcionalidades.»*
>
> *«No entiendo el sonido W que es diferente a la letra B.»*

| Lo que dijo | Diagnóstico | Corrección | Verificación |
|---|---|---|---|
| Retraso de 2-3 s al deslizar en el teléfono | `backdrop-filter` en más de cien bloques y fondo con `background-attachment: fixed`: repintado completo en cada fotograma | Los dos efectos, solo en dispositivos con ratón | Con emulación táctil quedan desactivados; **falta confirmarlo en un teléfono real** |
| El texto toca el borde redondeado | Los bloques de Markdown de la interfaz de entonces (Gradio) no tienen relleno, pero aquí todos llevan fondo de panel | Relleno interior a los bloques con contenido | Medido y capturado a 390 y 1440 px |
| En modo oscuro no distingue las secciones | Panel al 72 % sobre casi negro y borde al 16 % en *hielo*, la paleta por defecto | Panel y borde más claros en las dos paletas oscuras | Las 85 parejas de contraste WCAG siguen pasando |
| Quiere una barra de navegación con las funciones y los ajustes aparte | *Colores* y *Estado* eran pestañas como leer o pronunciar. **El profesor había dicho lo mismo**: «Colores toma demasiada presencia» | Botón **⚙ Ajustes** en la cabecera; barra de pestañas fija arriba al bajar y centrada en escritorio | Probado en el navegador; a 390 px «Pronunciar» sigue en el menú «…» |
| «Siguiente capítulo» la deja al final | Los botones no movían la página | Al cambiar de capítulo sube al principio del texto | Teléfono: el lector queda justo bajo la barra con el capítulo nuevo |
| Borrar a mano la frase para practicar otra | No había forma de empezar de nuevo | Botón **«Otra frase ↺»** bajo la corrección | Probado en el navegador |
| No entiende «/w/ diferente a la b» y pide «los símbolos» | La explicación comparaba con una letra, no enseñaba el AFI y ni siquiera sabía qué se había oído | Explicación anclada a palabras del español y a lo que se entendió; símbolo AFI; transcripción de la palabra sacada del diccionario local; 41 audios pregrabados, uno por fonema, que no gastan créditos (≈ 0,19 USD una sola vez) | Probada de punta a punta con un audio que dice «fix» por «fox»: ahora culpa a la vocal y no a la /f/. **Los audios aún no los ha escuchado nadie** |
| Captura: «don’t» marcado como «don» y «t» | El apóstrofo tipográfico de los libros partía la contracción | Se normaliza antes de comparar | Dos pruebas nuevas |
| Captura: «Tolstoy, Leo, graf» | El título nobiliario de Gutenberg se tomaba por parte del nombre | El autor corto se queda con apellido y nombre | Prueba nueva |

*Cuadro 1b. El segundo ciclo, de la crítica a la verificación.*

**Dos de las correcciones fallaron la primera vez, y las 306 pruebas
automáticas no lo vieron.** La primera versión del arreglo del lector sacaba la
cabecera del libro letra a letra. La del botón de siguiente capítulo no movía
nada, porque el texto nuevo llega después y los botones que pulsó Laura eran
los de debajo del texto. Las dos se descubrieron midiendo la página en un
navegador controlado a ancho de teléfono. Es la misma lección del apartado 3.2,
repetida.

**Lo que vino después de ese ciclo cambió la interfaz entera.** Ese mismo 12 de
septiembre, en la revisión del avance, el profesor Barranco pidió que la
aplicación entregada no fuera la de Gradio sino un front propio, separado del
motor. La interfaz pasó a Angular sobre una API (apartado 4.6). Las
correcciones del Cuadro 1b se hicieron primero en Gradio, que sigue en marcha
como motor, y las que tocan la pantalla se llevaron al front: los ajustes fuera
de la navegación, el lector que sube al cambiar de capítulo, «Otra frase» y la
ficha de cada sonido.

### 3.4 La lección, en una línea

**El valor de una prueba de usuario no está en el promedio de satisfacción, sino
en la frase que duele.** Con n = 2 no se puede estimar nada, pero se pueden
encontrar los fallos que hacen que una persona se culpe a sí misma, y ya hay
una coincidencia: a las dos lectoras les costó el móvil y a ninguna le gustó la
paleta por defecto. Nielsen (2000) sitúa en cinco usuarios el punto donde se
detecta la mayor parte de los problemas de usabilidad; el accionable A8 lleva la
prueba hasta ahí.

---

## 4. Usabilidad del modelo

Un modelo es usable cuando el usuario puede confiar en él sin entenderlo. Eso
se construye con cinco decisiones, todas medidas, y con la interfaz que las
pone delante del lector (4.6).

### 4.1 La espera se traslada, no se pide

Medir un libro largo son minutos. Pedirle esos minutos al lector en el momento
en que quiere leer es perderlo. La estrategia es **mover el cómputo antes de la
consulta**: el catálogo se precalcula fuera de línea y, cuando el lector busca,
el trabajo ya está hecho. Los números que hacen viable esa decisión están en el
Cuadro 21 del PDF —el 16 de la copia de lectura—: 8,19 ventanas/s en CPU, 112,7 en la GPU
local y **2.022 en una A100**, con lo que los 61.642 libros en inglés de
Project Gutenberg son **unas tres horas** de cómputo puro. De extremo a extremo
son **unas diecisiete**, y la diferencia no la pone la tarjeta sino el disco.
**Y se hizo**: el 12 de septiembre de 2026 quedaron medidos 53.179 libros y
585.111 capítulos, en tandas reanudables que guardaban en Drive y, desde el 12,
en Hugging Face: hasta el 10 de septiembre en una A100 de pago de Colab Pro, y
desde entonces en una T4 gratuita; la última, 9.795 libros, tardó 55 minutos.

Cuando el cómputo sí tiene que ocurrir en vivo, se ofrecen **dos velocidades y
se dice cuál se usó**: un vistazo (30 capítulos repartidos, 2 ventanas de cada
uno) o el libro entero sin muestrear. Y el atajo está cuantificado, no
prometido: 8 ventanas dan **1,784** y el recorrido completo del mismo capítulo,
**1,743**.

### 4.2 La incertidumbre se comunica en bandas

El modelo devuelve un número continuo, pero su escala está comprimida
(`predicho ≈ 0,72 × real + 0,38`). Presentar «1,27 sobre 2» como si fueran dos
decimales de precisión sería mentir con exactitud. La interfaz muestra
**bandas** —básico < 0,6 ≤ intermedio < 1,4 ≤ avanzado, que son los cortes
del propio MCER, y no los 0,8 y 1,6 de antes, que ni siquiera partían el
0–2 en tres partes iguales— y la letra MCER
únicamente como orientación, siempre junto al número y con la tabla de
correspondencia a la vista.

Un fallo real de esta decisión, encontrado y corregido, ilustra el nivel de
cuidado que exige: el redondeo por defecto de Python resuelve los empates hacia
el par, de modo que un 1,00 exacto caía en un nivel y la tabla publicada decía
otro. Un usuario que comparase su cifra con la tabla habría encontrado dos
respuestas para el mismo número. Ahora hay una sola regla, y una prueba fija los
cinco límites.

### 4.3 Nada falla en silencio, y nada se rompe del todo

La regla transversal del sistema es la **degradación elegante**: sin clave de
servicio externo, la aplicación sigue dando diccionario, fonética, buscador
y puntuación, porque nada de eso sale a la red desde el servidor; el audio
de Wiktionary es un enlace a `upload.wikimedia.org` que descarga el navegador del
lector, así que necesita conexión pero no clave. Solo se apagan tres cosas
—la explicación en contexto, la corrección de pronunciación y el resumen de
«¿de qué trata?» de la ficha—, y se dice con
palabras que el lector entienda —«se ha agotado el presupuesto mensual de
explicaciones; el diccionario, la fonética y el audio siguen funcionando»— en
lugar del error técnico en crudo.

La regla de diseño es que los fallos vuelvan como texto legible en vez de
excepciones sin tratar. Las pruebas cubren escenarios concretos; no demuestran
que ningún manejador pueda fallar. El corte de verificación actual se distingue
de las baterías históricas en el apartado 4.6.

### 4.4 Cada número dice de dónde viene

En la ficha del libro conviven dos clases de información y **la separación se ve
en pantalla**: lo *contado* sobre el fichero (palabras, tiempo de lectura,
proporción de diálogo, vocabulario) sale solo al abrirlo, es instantáneo y no
necesita red; el *resumen* escrito por un modelo generativo va detrás de un
botón, se guarda en disco y viene marcado como lo que es. **Ninguna cifra de la
ficha la dice un modelo generativo.** En el diccionario, la regla equivalente:
el modelo de lenguaje explica el contexto y la gramática sin sustituir una
acepción utilizable de Wiktionary. Si no existe, desde el 13 de septiembre puede
proponer una definición marcada como generada por IA, solo con acceso
autorizado. La definición de diccionario y el texto generado no son lo mismo.
Y si la elección entre acepciones es dudosa —menos de 0,05 de afinidad entre las dos más cercanas— y no hay explicación de OpenAI, desde `bf3a9f2` la ficha no afirma una: dice «Puede ser» y enseña la acepción principal de cada entrada del diccionario, si hay al menos dos.

### 4.5 La latencia se reparte para que la pantalla no se quede quieta

En una consulta léxica nueva, casi todo el tiempo es **espera al servicio
externo**: la explicación contextual se midió en **14,9 segundos** con el
esfuerzo de razonamiento `low` que usa la aplicación —eran 67,7 con el esfuerzo
medio de antes—, mientras todo el trabajo local —lema, diccionario,
desambiguación, fonética— son **40 milisegundos**. Por eso la ficha se pinta en dos etapas: lo
local aparece al instante y la explicación se añade cuando llega. El trabajo
tarda lo mismo; deja de parecer que la aplicación se colgó. La misma idea
gobierna la curva de dificultad, que se repinta cada pocos capítulos mientras
mide (el repintado cuesta 25 ms, medido) y los recursos pesados, que se cargan
al primer uso y no al arrancar.

### 4.6 La interfaz entregada: un front de Angular sobre una API

Hasta el 12 de septiembre de 2026 la aplicación era una sola pieza: ocho
pestañas de Gradio que hacían de interfaz y de motor a la vez. En la revisión
del avance de ese día, el profesor Barranco pidió que la entrega fuera un front
propio, separado del motor. Se hizo al día siguiente, y es lo que se entrega:

- **El front** es una aplicación de Angular 22 (componentes independientes, sin
  `zone.js`) publicada como **Space estático** de Hugging Face
  (`MikeMaki1763/literalevel-front`), gratuito y siempre despierto: es HTML, CSS
  y JavaScript ya compilados. Tiene cuatro sitios en vez de ocho pestañas
  —*Leer*, *Encontrar*, *Pronunciar* y *Tu nivel*—, más *Mis palabras*; los
  ajustes (paleta, tamaño de letra, idioma de las explicaciones) y el estado del
  servicio salen de la navegación, que es lo que Laura y el profesor habían
  pedido por separado.
- **La API** es un servicio FastAPI (`app/api.py`, 40 rutas bajo `/api` a fecha de `8ee42f0`, el `app/` que publica el Space en `7c09d90`)
  **montado en el mismo Space de Gradio** que ya existía, con Gradio en la raíz
  como motor y respaldo. **Reutiliza el motor y ayudantes de Gradio**, pero sus
  adaptadores contienen lógica propia: topes, cobro, aislamiento y degradación
  requieren pruebas también en la API. Compartir funciones no basta para
  demostrar equivalencia. El inicio de sesión frena los intentos fallidos en una hora: 15 por IP y,
  desde `514786b`, 20 por usuario, porque la IP sale de una cabecera que puede
  escribir el cliente. Solo cuentan los que fallan, y son valores por defecto
  que se cambian por variable de entorno. Medir tampoco es ilimitado: cada medida ocupa la CPU del único proceso del Space, así que desde el 14 de septiembre hay topes por IP y hora —40 medidas de nivel o de capítulo y 6 curvas nuevas— y como mucho 4 curvas en cola a la vez; lo ya medido no gasta ficha. En el Space, a fecha de `2bb1276`, la séptima curva seguida dio 429 y un libro ya medido siguió respondiendo. La identidad del lector
  viaja en una cabecera (`X-Lector`) y sus datos siguen en el bucket montado en
  `/data`. El primer montaje falló —el proxy de renderizado en servidor de
  Gradio no dejaba pasar `/api`— y el segundo, sin ese proxy, es el que está en
  marcha.
- **Regla de entrega:** una función existe cuando tiene ruta en la API **y**
  pantalla en el front. Lo que solo vive en Gradio no cuenta como entregado.
- **Verificación del 13 de septiembre, corte actualizado el 14:** 32 de 35
  pruebas API pasaron en el entorno aislado; tres quedaron sin validar por
  dependencias NLP ausentes. Pasaron además 7 pruebas de concurrencia de voz,
  10 del despliegue y 11 del pipeline de portadas. No se suman como una prueba
  completa de usuario ni sustituyen la batería histórica del motor.
  El backend publicado `e56cf08` se cotejó por hash y se comprobó salud JSON,
  lectura de Alicia en Angular, diccionario sin perfil y rechazo de voz anónima.
  No se probó OpenAI real ni micrófono físico en ese cierre. Evidencia:
  `auditoria/despliegue_codex_2026-09-13_noche.md`.
  Recuento sin claves del 15 de septiembre sobre `d58b0be`: 52 de 52 pruebas API,
  349 de 349 pruebas extremas, 34 de 34 de corpus y 34 de 34 de lectura natural.

**Lo que el front añadió a la usabilidad en un día.** Tres cosas, y las tres
salieron de mirar cómo se usa un teléfono:

- **Uso con una sola mano.** Un estudio propio (`investigacion/una_mano.md`)
  fijó diez reglas a partir de la literatura sobre el alcance del pulgar y el
  tamaño de los objetivos; las primeras ya están en el front: en el lector, una
  barra única abajo con capítulo y página anterior y siguiente y el índice, que
  se esconde con la navegación; nada primario en el cuarto superior de la
  pantalla; en *Pronunciar*, una barra de acción fija abajo con el micrófono en
  el centro, que no se mueve entre grabar, parar y corregir.
- **Corrección de pronunciación con fonema determinista.** Con la misma
  grabación, el modelo generativo señalaba un sonido distinto en cada llamada.
  Ahora el fonema que falla sale de **alinear la transcripción de lo que había
  que decir con la de lo que se entendió** —las dos de diccionario: Wiktionary
  y, donde no la trae, CMUdict (Carnegie Mellon University, s. f.), 126.052
  palabras bajo licencia BSD— y el
  consejo de boca, lengua y aire sale de una ficha fija por fonema. Del modelo
  queda el resumen. La selección del fonema es determinista dadas las mismas
  palabras y transcripciones; esto no hace determinista al reconocimiento de voz.
- **Animación del corte de la boca.** Para cada uno de los 41 sonidos del
  inglés americano (y los 44 del británico), un corte sagital animado —labios,
  dientes, paladar, velo, lengua y mandíbula— que va del reposo a la posición
  del sonido y vuelve; y para la palabra entera, la secuencia de sus sonidos a
  partir de su transcripción. Son SVG animados con CSS, sin JavaScript,
  generados una vez en el servidor y servidos por la API; el front los enseña
  en la ficha de cada sonido y en la corrección —primero el sonido que falla y
  después la palabra—, y con «reducir movimiento» del sistema los deja quietos.

**Boca 3D y portadas, a fecha del front `ec957d0` (repositorio `4e6276e`).** La boca 3D ya está publicada: el front sirve `boca3d/cara.glb` y `lengua.glb`, idénticos byte a byte a los del repositorio, con 72 mallas entre los dos y respaldo 2D si no cargan. La piel de la media cabeza sale de la malla base de MakeHuman 1.3.0, publicada bajo CC0 1.0 (no obliga a atribuir; MakeHuman Community, s. f.); paladar, velo, encías, dientes y lengua son modelos propios, y sus 53 poses se validan contra ellos. Es un corte esquemático, no anatomía validada clínicamente. Las portadas publicadas son **tipográficas**: una de 12 familias según los temas del catálogo, con una paleta de cinco colores sacada de la huella del identificador y el título a un contraste de al menos 4,5:1. El lector toma el fondo y el acento de esa paleta, con el texto a 7:1 o más y el acento a 4,5:1 sobre el fondo (sobre el color suave del acento, la pista del lector baja a 4,17:1 en algunos libros en tema claro, como SWV369), y el ajuste «Color del libro en el lector» lo apaga; la prueba del front que fija esos contrastes recorre 12 familias, 200 libros y dos temas (`b2003e5`). El pipeline de portadas FLUX está bloqueado por defecto; no generó imágenes nuevas ni consumió GPU. Sus 1.200 candidatos tienen 746 motivos temáticos y 454 genéricos, pendientes de muestra y revisión visual.

**Lectura natural, medida con diez frases.** En *Pronunciar*, además del sonido que falla, la aplicación mide el ritmo de la lectura y enseña cómo se dice la frase de corrido: énfasis, enlaces entre palabras y reducciones (*want to* → *wanna*). Lo propone un modelo generativo y lo filtra un validador: las reducciones solo salen de una lista cerrada y los enlaces se comprueban con la pronunciación de diccionario. Con diez frases reales del catálogo evaluadas a mano (`auditoria/bateria_lectura_natural_2026-09-14.md`), el modelo propuso 11 reducciones y 29 enlaces; llegaron al lector 2 reducciones y 4 enlaces, **todos correctos**, y las diez versiones naturales quedaron fieles a la frase (8 reconstruidas por el validador). La exhaustividad es baja: se quedan fuera enlaces claros como *an argument*. En esa batería todo lo que llegó al lector era correcto, y eso no es una garantía: desde el 15 de septiembre el validador exige además un verbo detrás de *gonna*, *wanna* o *gotta* (antes aceptaba «I am gonna school» si el modelo lo proponía) y no enlaza a través de un punto. La frase de la demostración, «Don't you want to come with us?», da en el Space a fecha de `7c09d90` las reducciones *doncha* y *wanna*, marcadas como generadas por IA, y ningún enlace.

**Primeros usuarios.** Desde el 14 de septiembre hay cuentas repartidas a los primeros usuarios (`auditoria/feedback_usuarios_2026-09-14.md`), y la primera respuesta ya enseñó un fallo: una lectora B1 buscó libros de amor y encontró pocos. No faltaban en el catálogo; fallaba la búsqueda. En la franja que la aplicación da a un lector B1 (dificultad de 0,35 a 1,25) hay 114 textos libres con *love* o *romance* en el título, frente a 4 libros de Gutenberg; pero la búsqueda devolvía los más parecidos de todo el catálogo, y con «amor» o «Historias de amor» y nivel B1 los 24 primeros eran de Gutenberg, sin ninguno de esos cuentos. Desde el reinicio 25 (15 de septiembre), detrás de esos resultados van hasta 12 textos de la franja del lector que se parecen a lo buscado: con «amor» y nivel B1 se marcan 12, y 8 llevan el amor en el título. En *Encontrar*, contados a mano, unos 7 de los resultados de «Historias de amor» que caen en el nivel del lector o un poco por encima son de amor, en sentido amplio. Recontado el 15 de septiembre con el catálogo que carga la aplicación y con el Space publicado (`auditoria/chips_reinicio25_2026-09-15.md`).
El enlace del lector es https://mikemaki1763-literalevel-front.static.hf.space/ .

---

## 5. Contra quién compite esto

Un proyecto que no sabe contra qué compite no puede decir qué aporta. Esta
sección responde a tres preguntas incómodas: si alguien ya lo hace, si lo hace
mejor, y qué queda entonces para nosotros.

### 5.1 Las tres alternativas reales

**Las fórmulas clásicas** —Flesch, Dale-Chall, ATOS— son gratis, instantáneas e
interpretables al cien por cien, y llevan setenta años en las aulas. Su límite
está medido: alcanzan **Pearson 0,517** contra el juicio humano en el corpus
CLEAR, donde el modelo de este proyecto llega a **0,89**. Cuentan sílabas; no
leen.

**Lexile** es el competidor comercial serio y hay que reconocerle lo que tiene:
una escala validada durante treinta años, cientos de miles de títulos medidos,
integración con bibliotecas y pruebas oficiales, y algo que aquí solo se
aproxima —una escala común que compara al lector con el texto—. **Su medida la
acepta un colegio; la nuestra no.** Lo que no tiene es precio accesible. Su tarifa
publicada para creadores de contenido (MetaMetrics, 2026) va de **3.824 a 54.636 USD al año** según
el volumen, y los 53.179 libros del catálogo medido caen en el tramo más alto.

Medirlos aquí **sí usó cómputo de pago**, sin cifra en dólares que dar porque no
quedó registrado cuántas unidades se gastaron: hasta el 10 de septiembre de 2026
el cuaderno de Colab corría en una A100 con unidades de la cuenta Colab Pro, y
hasta esa tarde se midieron 27.776 libros (los 29.875 medidos el 10 menos los
2.099 de la primera tanda en T4). Desde entonces se midió en una T4
gratuita, en tandas reanudables —la última, 9.795 libros en 55 minutos—, y los
textos libres en la CPU local. Las «2,8 h de A100» del registro son la estimación
de tarjeta para los 61.642 libros, no horas gastadas. Al ritmo medido en la A100,
61 libros por minuto, los 53.179 habrían sido **unas catorce horas y media de
reloj**. **No es una razón
monetaria estricta** —una licencia anual y unas horas de cómputo no se dividen
la una por la otra— y tampoco son servicios equivalentes: Lexile vende una
escala aceptada por instituciones, no solo un número. Lo que sí se puede
afirmar es que **el coste de procesamiento está en otro orden de magnitud**, y
que eso es lo que hace viable medir un catálogo entero en un trabajo de
estudiante.

**Un LLM con un buen prompt** es la alternativa que todo el mundo propone hoy.
La evidencia publicada apunta a que un codificador afinado le lleva ventaja en
esta tarea: sobre CLEAR, el mejor método *zero-shot* documentado alcanza
**0,725** (Grossman y Chen, 2026; n = 1.890, diez modelos abiertos), y este
proyecto mide **0,89** en el mismo corpus. Kogan et al. (2025) encontraron algo
parecido con el conjunto Ace-CEFR: un BERT afinado de 45,7 millones de
parámetros, con menos error que PaLM 2-L.

**Pero eso no es una comparación cara a cara y no conviene venderla como tal.**
Son dos experimentos distintos sobre el mismo corpus, con particiones y
protocolos que no se han igualado; compartir el nombre del corpus no es
compartir los textos de prueba. Lo que estas referencias justifican es la
*decisión* de afinar un codificador en lugar de escribir un *prompt*. La
comparación bajo el mismo protocolo está sin hacer, y sería un buen trabajo
futuro.

### 5.2 Dónde perdemos, dicho sin adornos

**TeakReader** (TeakReader, s. f.) es el producto que más se nos parece, y va por delante en lo que
importa a un usuario: es una aplicación terminada y publicada en dos tiendas,
mientras que esto vive en un enlace. Da nivel MCER por capítulo —aunque por
conteo de vocabulario, no con un modelo de lenguaje— y su señal está
personalizada a lo que cada lector declara conocer. La nuestra no.

**Las lecturas graduadas de editorial** tienen algo que ningún modelo da: el
nivel se lo puso una persona que leyó la obra entera. El nuestro se lo puso un
modelo con una escala comprimida.

Y frente a **cualquiera de las alternativas**, este proyecto arrastra una
dependencia que ellas no tienen: 654 documentos de anclaje. Ese es el techo real
del modelo, y está dicho en las limitaciones del documento.

### 5.3 Qué queda entonces, y por qué basta

Tres cosas, y solo tres.

**Recorremos el libro entero, capítulo a capítulo.** Lexile da un número por
libro; las fórmulas, uno por fragmento; las lecturas graduadas, una etiqueta de
colección. Aquí se dibuja la curva completa y se ve dónde se pone cuesta arriba
una novela y dónde da respiro. Para decidir si abandonas *Guerra y paz* en el
capítulo veinte, eso es más útil que un número global.

**Está pensado para un hispanohablante que quiere elegir qué leer**, no para un
profesor que quiere clasificar un texto. La interfaz está en español, la
explicación de cada palabra también, y la pregunta que responde no es «¿qué
nivel tiene este texto?» sino «¿puedo leer esto yo, hoy?».

**Es auditable y de acceso gratuito para el lector.** El modelo está publicado,
el código está a la vista y las métricas vienen con su *n* y sus limitaciones.
Conviene precisar qué significa aquí «auditable»: el código, la inferencia desde
los pesos públicos **y** las métricas internas del v4 se pueden rehacer
—recalculadas el 12 de septiembre de 2026, idénticas a cuatro decimales—. Y
«gratuito» se refiere a quien usa la aplicación: alojarla y servirla cuesta
dinero, y ese coste aparece en los accionables A2 y A4.

Las fórmulas clásicas también son gratuitas y reproducibles, así que la ventaja
no es la auditabilidad por sí sola: es tenerla **junto con** un modelo que lee
el texto en lugar de contar sílabas.

### 5.4 La cifra que hay que saber defender

En el corpus de exámenes de British Council, **contar palabras sin modelo alguno
alcanza 0,807 donde el modelo alcanza 0,860**. Es la comparación más
desfavorable del proyecto y conviene llevarla preparada en lugar de esperar a
que alguien la encuentre: en ese corpus la longitud del texto está correlacionada
con el nivel, así que un contador de palabras aprovecha un atajo que en una
biblioteca real no existe. Descontando la longitud, la correlación parcial del
modelo se sostiene en **0,668**. La del contador de palabras no es que sea
peor: es que **no está definida**, porque descontar la longitud de la propia
longitud deja un residuo de varianza cero. Dicho de otro modo, el contador no
aporta nada por encima de la longitud porque es la longitud; el modelo sí.

**Y una cifra que parecía mejor y hubo que retirar.** Sobre UniversalCEFR
(Imperial et al., 2025) el
modelo daba 0,946 y contar palabras 0,663. Pero el v4 se entrenó con uno de sus
dos conjuntos (ELG CEFR English; Breuker, 2023) y el otro está contenido en él, así que era
medir el entrenamiento. Conviene llevarlo preparado igual que el 0,807: a la
pregunta «¿habéis comprobado que la validación no se solapa con el
entrenamiento?» la respuesta es que sí, que se encontró un solapamiento, y que
la cifra se retiró.

**Y la que sí se puede defender, con un corpus que el v4 no vio.** En
OneStopEnglish el modelo llega a 0,800 y contar palabras a 0,692, y descontando
la longitud el modelo conserva 0,688. Conviene no vender de más la cifra más
vistosa de ese corpus: dentro de cada artículo el modelo ordena las tres
versiones en 183 de 185, pero la longitud sola ya acierta 179.

**Y tres bibliotecas infantiles graduadas, que no dicen lo mismo.** En StoryWeaver
el modelo ordena sus cuatro niveles con 0,426 y conserva 0,206 descontando la
longitud, con intervalos que no tocan el cero: es la validación externa más
sólida. En African Storybook la longitud sola predice mejor el nivel (0,81)
porque ese editor gradúa sobre todo por extensión. Y Let's Read no valida: más de
la mitad son traducciones que heredan el nivel del libro original en otro idioma.
Si alguien pregunta «¿y por qué no promediáis las tres?», la respuesta es esa:
cada una mide una cosa distinta, y promediarlas escondería justo lo que se
aprendió. Además, a fecha de `740eb84` (reinicio 21), el catálogo de la aplicación suma 15.367 textos de licencia
libre de esas bibliotecas y de VOA (14.506 de StoryWeaver, de Pratham Books; 328 de Let's Read, de
The Asia Foundation; 280 de African Storybook, de Saide; y 253 de VOA Learning English), con la dificultad que mide el modelo. Un cuento corto medido dentro de un bloque lo dice (`medido_en_bloque`); la atribución que exige su licencia se enseña pero no se puntúa («Doggie is Happy», 0,349 con ella y 0,007 sin ella); el texto servido sale sin páginas repetidas ni U+FEFF sin cambiar lo medido; y al recomendar por nivel ocupan un tercio de las tarjetas, por cercanía al nivel del lector (a fecha de `7c09d90`).

---

## 6. Accionables

Diez acciones concretas, ordenadas por puntos de rúbrica protegidos u obtenidos
por hora de trabajo. Cada una lleva coste real y criterio de terminado. No son
«se podría»: son «se hace».

| # | Acción | Por qué | Coste | Terminado cuando |
|---|---|---|---|---|
| **A1** | **Publicar el modelo y el diccionario** como repositorios abiertos | Desbloquea la reproducibilidad del cuaderno, que antes no corría en un Colab ajeno | ~30 min; gratuito. Requiere un token que solo el autor puede crear | **HECHO a medias**: el modelo (328 MB) está en `MikeMaki1763/literalevel-v4`, público y con la descarga sin credenciales verificada. El diccionario (243 MB) sigue sin publicar |
| **A2** | **Desplegar en enlace permanente** | El enlace anterior era un túnel temporal que moría al apagar el equipo, y era el mayor riesgo de la entrega | **7 USD/mes**: el Space de Gradio que aloja el motor y la API exige cuenta Hugging Face Pro (9 USD de tarifa, 7 con descuento); el hardware `cpu-basic` no añade coste, y el Space estático del front es gratuito | **HECHO**: `MikeMaki1763/literalevel-front` (el front) y `MikeMaki1763/literalevel` (API y motor), públicos y en marcha. El disco persistente es A4 |
| ~~**A3**~~ **HECHO** | **Terminar la remedición del catálogo** con el modelo v4, libro entero | Sustituye las etiquetas heredadas —predicciones de un modelo v1 sobre las primeras ~190 palabras— por medidas reales | T4 gratuita; la descarga por `common-pile/project_gutenberg` (Kandpal et al., 2025; 57.226 textos en 7,7 minutos) y los resultados en Hugging Face, no en Drive, que pedía un permiso en cada sesión | **Cumplido el 12 de septiembre de 2026**: 53.179 libros y 585.111 capítulos medidos, y la aplicación los usa |
| ~~**A4**~~ **HECHO** | **Montar almacenamiento persistente** para los datos del lector | Un servicio que duerme y despierta con la estantería vacía deja en ridículo «Mis libros» | 18 USD por TB y mes en repositorio privado; los datos del lector ocupan **10,9 MB** medidos, así que el coste es despreciable | **Cumplido y verificado**: bucket montado en `/data`, se fijó un perfil, se reinició el Space y el perfil seguía ahí |
| **A5** | **Conseguir un micrófono** (auriculares con micro) | El equipo actual no tiene. Sin él no se puede demostrar la corrección de pronunciación, que es la función más vistosa y la que mejor encaja con «usabilidad para el usuario final» | Coste mínimo de hardware | Se graba una frase desde el equipo del autor y la corrección palabra por palabra aparece en pantalla |
| **A6 · HECHO** | **Sustituir el catálogo heredado** de 1.197 registros | Incluía 1.049 registros sin texto descargable, el 87,6 % de aquella versión, no de la actual | Incluido en A3 | El catálogo medido actual contiene 53.179 IDs de Gutenberg; a fecha de `db366b8` se excluyen al recomendar y al buscar 600 que no son lectura (índices, catálogos, directorios) y, desde `3524357`, 163 textos libres que no son lectura en inglés (relleno o en otra lengua), y por nivel solo se ofrecen obras literarias. Una medida del precálculo se corrige al cargar (`correcciones_catalogo.csv`): PG2242, *A Midsummer Night's Dream* del First Folio, guardó 0,697 y releída por el mismo camino da 1,713 (C1) |
| **A7** | **Calibrar la escala** con una transformación afín de dos parámetros ajustada sobre entrenamiento, sin tocar los pesos | La escala está comprimida y un A2 puntúa cerca de B1. La técnica ya se aplicó con éxito a una variante anterior | Una tarde | Las medias por nivel siguen estrictamente crecientes **y** se acercan a sus anclas |
| **A8** | **Repetir la prueba de usuario con cinco lectores** de perfiles distintos sobre Angular, con guion de tareas y observación en silencio | Los dos ciclos previos encontraron fallos graves; no validan todos los cambios del nuevo front (Nielsen, 2000) | Cinco sesiones de 20 min | Existe una lista priorizada de hallazgos y las tres primeras correcciones están hechas |
| **A9** | **Instrumentar la métrica que de verdad importa**: proporción de libros empezados que se terminan, con recomendación y sin ella | Todo lo demás son métricas de proceso. Esta es la única que valida la propuesta de valor | Una jornada de instrumentación, respetando el aislamiento por sesión | Hay una cifra base con la que comparar dentro de un mes |
| **A10** | **Ampliar el corpus de anclaje MCER** más allá de los 654 documentos actuales | Es el eslabón más delgado de la cadena de evidencia y el que limita la confianza en la letra que se muestra | Trabajo de corpus, sin coste de cómputo | El corpus de anclaje supera los 1.000 documentos con niveles de fuente institucional |

*Cuadro 2. Accionables, con coste y criterio de terminado.*

**Orden de ejecución actualizado:** ensayar la voz con micrófono real (A5),
recorrer Angular con usuarios (A8), grabar el video y comprobar los archivos
de entrega. A2, A3, A4 y la sustitución del catálogo de A6 ya tienen evidencia
de cierre; no se vuelven a presentar como trabajo por empezar. Las mejoras
visuales pendientes no deben desplazar el ensayo de la demo.

---

## 7. Métricas de éxito

| Nivel | Métrica | Estado |
|---|---|---|
| Modelo | Orden estrictamente creciente por nivel MCER en corpus externo | **Cumplido**: 0,5040 · 0,5561 · 0,9276 · 1,2414 · 1,4952 |
| Modelo | Señal por encima de la longitud del texto | **Cumplido**: correlación parcial 0,668 |
| Producto | Un usuario sin formación técnica completa el recorrido | **Cumplido con reservas, sobre la interfaz anterior**: lo completó en Gradio, y de esa sesión salieron las nueve correcciones del Cuadro 1 —seis de ellas etiquetas—; sobre el front de Angular, pendiente (A8) |
| Producto | Accesibilidad de color | **Cumplido**: las ochenta y cinco parejas de color de las cinco paletas superan WCAG AA; las más ajustadas, 4,53 (texto) y 3,11 (título) |
| Producto | Robustez | **Parcial**: recuento sin claves del 15 de septiembre —API 52 de 52, extremas 349 de 349, lectura natural 34 de 34, voz concurrente 10 de 10 y corpus 34 de 34—; no equivalen a una prueba completa de usuario |
| Operación | Enlace permanente disponible | **Cumplido**: el front en `MikeMaki1763/literalevel-front` y la API con el motor en `MikeMaki1763/literalevel`, los dos en Hugging Face Spaces, públicos y en marcha, con los datos del lector en un bucket montado en `/data` |
| Operación | Catálogo medido, no heredado | **Cumplido** el 12 de septiembre de 2026: 53.179 libros y 585.111 capítulos medidos por el v4 (A3) |
| Impacto | Proporción de libros terminados | **Sin instrumentar** (A9) |

*Cuadro 3. Métricas por nivel, con su estado real.*

---

## 8. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El enlace de la demostración muere durante la evaluación | Alto | A2: despliegue permanente, probado desde un dispositivo ajeno antes de la fecha |
| El servicio externo de lenguaje agota su presupuesto en mitad de una demostración | Medio | Ya mitigado: la aplicación degrada con un mensaje legible y conserva diccionario, fonética, audio, buscador y puntuación |
| Que la letra MCER se lea como una certificación | Alto, reputacional | Declaración de alcance en el documento y aviso permanente en pantalla |
| Que la remedición del catálogo no termine a tiempo | ~~Medio~~ **Resuelto** | Terminada el 12 de septiembre de 2026: sin Drive, con los resultados en Hugging Face tras cada lote, 0 errores y ningún libro medido dos veces |
| Sobrecarga del espejo de descarga de Project Gutenberg | Medio, ético | Seis hilos y no treinta, cada uno con su pausa entre peticiones; y el vocabulario se obtuvo del SPGC, no rascando el sitio |
| Contenido inapropiado para una lectora menor de edad | Medio | Decisión razonada de **no filtrar por contenido** y avisar en la ficha (una lista curada: 2 títulos a fecha de `db366b8`, que no encabezan la recomendación por nivel y no se quitan); se argumenta en el apartado 8.4 del documento principal |

*Cuadro 4. Riesgos y mitigaciones.*

---

## Referencias

Breuker, M. (2023). CEFR labelling and assessment services. En G. Rehm (Ed.),
*European Language Grid* (pp. 277–282). Springer.
https://doi.org/10.1007/978-3-031-17258-8_16

Carnegie Mellon University. (s. f.). *The CMU Pronouncing Dictionary*
[Conjunto de datos]. https://github.com/cmusphinx/cmudict

Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of
experiments examining the effects of extrinsic rewards on intrinsic motivation.
*Psychological Bulletin, 125*(6), 627–668.
https://doi.org/10.1037/0033-2909.125.6.627

Grossman, R., & Chen, Y. (2026). *Zero-shot large language models for automatic
readability assessment* (arXiv:2604.24470). arXiv.
https://arxiv.org/abs/2604.24470

Imperial, J. M., Barayan, A., Stodden, R., Wilkens, R., Muñoz Sánchez, R., Gao,
L., Torgbi, M., Knight, D., Forey, G., Jablonkai, R. R., Kochmar, E., Reynolds,
R. J., Ribeiro, E., Saggion, H., Volodina, E., Vajjala, S., François, T.,
Alva-Manchego, F., & Tayyar Madabushi, H. (2025). UniversalCEFR: Enabling open
multilingual research on language proficiency assessment. En *Proceedings of the
2025 Conference on Empirical Methods in Natural Language Processing* (pp.
9703–9755). Association for Computational Linguistics.
https://doi.org/10.18653/v1/2025.emnlp-main.491

Kandpal, N., Lester, B., Raffel, C., Majstorovic, S., Biderman, S., Abbasi, B.,
Soldaini, L., Shippole, E., Cooper, A. F., Skowron, A., Kirchenbauer, J.,
Longpre, S., Sutawika, L., Albalak, A., Xu, Z., Penedo, G., Ben Allal, L.,
Bakouch, E., Pressman, J. D., … Murray, T. (2025). *The Common Pile v0.1: An 8TB
dataset of public domain and openly licensed text* (arXiv:2506.05209). arXiv.
https://arxiv.org/abs/2506.05209

Kogan, D., Schumacher, M., Nguyen, S., Suzuki, M., Smith, M., Bellows, C. S., &
Bernstein, J. (2025). *Ace-CEFR: A dataset for automated evaluation of the
linguistic difficulty of conversational texts for LLM applications*
(arXiv:2506.14046). arXiv. https://arxiv.org/abs/2506.14046

Krashen, S. D. (1985). *The input hypothesis: Issues and implications*.
Longman.

Krug, S. (2014). *Don't make me think, revisited: A common sense approach to
web usability* (3ª ed.). New Riders.

MakeHuman Community. (s. f.). *License*.
https://static.makehumancommunity.org/about/license.html

MetaMetrics. (2026). *Lexile® Text Analyzer content creator annual tiered pricing
program*. https://www2.metametricsinc.com/content-creator-annual-pricing

Nakanishi, T. (2015). A meta-analysis of extensive reading research. *TESOL
Quarterly, 49*(1), 6–37. https://doi.org/10.1002/tesq.157

Nielsen, J. (2000, 18 de marzo). *Why you only need to test with 5 users*.
Nielsen Norman Group.
https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/

Pratham Books. (s. f.). *StoryWeaver* [Biblioteca digital].
https://storyweaver.org.in

Saide. (s. f.). *African Storybook* [Biblioteca digital].
https://www.africanstorybook.org

TeakReader. (s. f.). *English reading level checker for books*.
https://teakreader.com/english-reading-level-checker-for-books

The Asia Foundation. (s. f.). *Let's Read* [Biblioteca digital].
https://www.letsreadasia.org

Voice of America. (s. f.). *VOA Learning English*.
https://learningenglish.voanews.com

World Wide Web Consortium. (2023). *Web Content Accessibility Guidelines (WCAG)
2.2*. W3C. https://www.w3.org/TR/WCAG22/
