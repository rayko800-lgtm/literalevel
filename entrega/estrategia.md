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

## 1. La apuesta, en un párrafo

La lectura extensiva es uno de los métodos con más respaldo para aprender una
segunda lengua, y sin embargo casi nadie la practica bien, porque elegir el
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
| Que le propongan algo, no una biblioteca | Un botón de «Sorpréndeme con algo de mi nivel» además de la búsqueda |
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
  cuánto tarda en leerlo **a su ritmo**, cuánto es diálogo y qué palabras se
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
| — | «Ajustar a mi nivel» es abstracto | «Solo libros que pueda leer», con información | Etiqueta reescrita |
| — | «Medir la dificultad de este capítulo» es lenguaje de laboratorio | «¿Cómo de difícil es este capítulo?» | Etiqueta reescrita |
| — | «Vistazo rápido a la dificultad» no dice cuánto tarda | «Vistazo rápido (unos segundos)» | Etiqueta reescrita |
| — | «Analizar el libro entero» no advierte del coste | «Leer el libro entero (tarda más)» | Etiqueta reescrita |
| «No me gustan los colores» | El color es gusto, y el gusto no se discute: se ofrece | **Cinco paletas** con pestaña propia y cambio instantáneo: *hielo* (la original), *amanecer* (clara, crema y naranja), *menta*, *papel* (para leer horas) y *medianoche* | Una prueba automática comprueba las cinco contra el criterio de contraste **WCAG AA (4,5:1)**. Las cinco pasan; la peor mide **9,51** |
| «Todo muy recto, muy marcado» | Esto no es gusto, es diseño, y se corrige para todas las paletas | Esquinas de 14 px, bordes finos, sombras suaves y las opciones de lista como fichas tocables | — |
| «Difícil de usar en celular… casi todo» | En un móvil, el círculo de un botón de radio es un blanco de 12 px | La ficha entera pasa a ser el blanco: **44 px** | — |

*Cuadro 1. Del comentario de una usuaria a un cambio verificable.*

### 3.2 Lo que ya se había corregido antes, por la misma vía

El ciclo de Esmeralda no fue el primero. Probar la aplicación en un teléfono
real —y no en el navegador del escritorio— había descubierto antes fallos que
**ninguna de las 183 pruebas automáticas podía encontrar, porque todos
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

### 3.3 La lección, en una línea

**El valor de una prueba de usuario no está en el promedio de satisfacción, sino
en la frase que duele.** Con n = 1 no se puede estimar nada, pero se pueden
encontrar los fallos que hacen que una persona se culpe a sí misma. Nielsen
(2000) sitúa en cinco usuarios el punto donde se detecta la mayor parte de los
problemas de usabilidad; el accionable A8 lleva la prueba hasta ahí.

---

## 4. Usabilidad del modelo

Un modelo es usable cuando el usuario puede confiar en él sin entenderlo. Eso
se construye con cinco decisiones, todas medidas.

### 4.1 La espera se traslada, no se pide

Medir un libro largo son minutos. Pedirle esos minutos al lector en el momento
en que quiere leer es perderlo. La estrategia es **mover el cómputo antes de la
consulta**: el catálogo se precalcula fuera de línea y, cuando el lector busca,
el trabajo ya está hecho. Los números que hacen viable esa decisión están en el
Cuadro 14 del documento principal: 8,19 ventanas/s en CPU, 112,7 en la GPU
local y **2.022 en una A100**, con lo que los 61.642 libros en inglés de
Project Gutenberg son **entre tres y cinco horas** de cómputo, según el número
medio de ventanas por libro, que todavía no está medido sobre el catálogo.

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
del propio MCER y no tercios de la escala— y la letra MCER
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
servicio externo, la aplicación sigue dando diccionario, fonética, audio de
Wiktionary, buscador y puntuación, porque nada de eso usa red. Solo se apagan
la explicación en contexto y la corrección de pronunciación, y se dice con
palabras que el lector entienda —«se ha agotado el presupuesto mensual de
explicaciones; el diccionario, la fonética y el audio siguen funcionando»— en
lugar del error técnico en crudo.

La regla que verifican las 183 pruebas de robustez es una sola: **ningún
manejador puede lanzar una excepción hacia la interfaz**. Lo que falla vuelve
como texto legible.

### 4.4 Cada número dice de dónde viene

En la ficha del libro conviven dos clases de información y **la separación se ve
en pantalla**: lo *contado* sobre el fichero (palabras, tiempo de lectura,
proporción de diálogo, vocabulario) sale solo al abrirlo, es instantáneo y no
necesita red; el *resumen* escrito por un modelo generativo va detrás de un
botón, se guarda en disco y viene marcado como lo que es. **Ninguna cifra de la
ficha la dice un modelo generativo.** En el diccionario, la regla equivalente:
el modelo de lenguaje explica el contexto y la gramática, y tiene prohibido
redefinir la palabra; la definición es siempre la de Wiktionary.

### 4.5 La latencia se reparte para que la pantalla no se quede quieta

De los 28 a 44 segundos de una consulta léxica nueva, **23 a 39 son espera al
servicio externo**; todo el trabajo local —lema, diccionario, desambiguación,
fonética— son **40 milisegundos**. Por eso la ficha se pinta en dos etapas: lo
local aparece al instante y la explicación se añade cuando llega. El trabajo
tarda lo mismo; deja de parecer que la aplicación se colgó. La misma idea
gobierna la curva de dificultad, que se repinta cada pocos capítulos mientras
mide (el repintado cuesta 25 ms, medido) y los recursos pesados, que se cargan
al primer uso y no al arrancar.

---

## 5. Accionables

Diez acciones concretas, ordenadas por puntos de rúbrica protegidos u obtenidos
por hora de trabajo. Cada una lleva coste real y criterio de terminado. No son
«se podría»: son «se hace».

| # | Acción | Por qué | Coste | Terminado cuando |
|---|---|---|---|---|
| **A1** | **Publicar el modelo (328 MB) y el diccionario (243 MB)** como repositorios abiertos, con el guion de subida ya escrito | Desbloquea la reproducibilidad del cuaderno, que hoy no corre en un Colab ajeno. Es el mayor rendimiento por hora de todo el proyecto | ~30 min; gratuito. Requiere un token que solo el autor puede crear | El cuaderno corre de principio a fin en un Colab limpio, sin errores ni advertencias |
| **A2** | **Desplegar en enlace permanente** (Gradio sobre plan de pago personal) | El enlace actual es un túnel temporal que muere al apagar el equipo. Es el mayor riesgo de la entrega, y no es técnico | 9 USD un mes | El enlace se abre desde un móvil ajeno y sobrevive a reiniciar el equipo del autor |
| **A3** | **Terminar la remedición del catálogo** con el modelo v4, libro entero | Sustituye las etiquetas heredadas —predicciones de un modelo v1 sobre las primeras ~190 palabras— por medidas reales. Es la deuda técnica más visible | Entre 3 y 5 h de A100, dentro del crédito disponible; la descarga va ahora en un solo archivo de 11,3 GB | El catálogo publica niveles medidos y el aviso sobre las etiquetas heredadas se retira |
| **A4** | **Montar almacenamiento persistente** para los datos del lector | Un servicio que duerme y despierta con la estantería vacía deja en ridículo «Mis libros». Hoy todo eso vive en disco efímero | 12 USD por TB y mes; el proyecto ocupa 7,4 MB, así que el coste es despreciable | Cerrar y reabrir tras un reinicio conserva libros, avance, cuaderno y perfil |
| **A5** | **Conseguir un micrófono** (auriculares con micro) | El equipo actual no tiene. Sin él no se puede demostrar la corrección de pronunciación, que es la función más vistosa y la que mejor encaja con «usabilidad para el usuario final» | Coste mínimo de hardware | Se graba una frase desde el equipo del autor y la corrección palabra por palabra aparece en pantalla |
| **A6** | **Retirar del catálogo los 1.049 registros no descargables** o marcarlos como fichas informativas sin botón de lectura | Hoy son el 87,6 % del catálogo y no se pueden abrir. Ya no aparecen en el desplegable, pero siguen ocupando el índice | Media jornada | El catálogo lista solo lo que se puede leer, o distingue visualmente ambas cosas sin ambigüedad |
| **A7** | **Calibrar la escala** con una transformación afín de dos parámetros ajustada sobre entrenamiento, sin tocar los pesos | La escala está comprimida y un A2 puntúa cerca de B1. La técnica ya se aplicó con éxito a una variante anterior | Una tarde | Las medias por nivel siguen estrictamente crecientes **y** se acercan a sus anclas |
| **A8** | **Repetir la prueba de usuario con cinco lectores** de perfiles distintos, con guion de tareas y observación en silencio | n = 1 encuentra fallos graves; cinco encuentran la mayoría (Nielsen, 2000) | Cinco sesiones de 20 min | Existe una lista priorizada de hallazgos y las tres primeras correcciones están hechas |
| **A9** | **Instrumentar la métrica que de verdad importa**: proporción de libros empezados que se terminan, con recomendación y sin ella | Todo lo demás son métricas de proceso. Esta es la única que valida la propuesta de valor | Una jornada de instrumentación, respetando el aislamiento por sesión | Hay una cifra base con la que comparar dentro de un mes |
| **A10** | **Ampliar el corpus de anclaje MCER** más allá de los 654 documentos actuales | Es el eslabón más delgado de la cadena de evidencia y el que limita la confianza en la letra que se muestra | Trabajo de corpus, sin coste de cómputo | El corpus de anclaje supera los 1.000 documentos con niveles de fuente institucional |

*Cuadro 2. Accionables, con coste y criterio de terminado.*

**Orden de ejecución si el tiempo aprieta:** A1 → A2 → A5 → A3 → A4. Los tres
primeros son los que protegen o desbloquean más puntos de rúbrica por hora
invertida, y ninguno de ellos es un problema de modelado: son despliegue,
publicación y un micrófono.

---

## 6. Métricas de éxito

| Nivel | Métrica | Estado |
|---|---|---|
| Modelo | Orden estrictamente creciente por nivel MCER en corpus externo | **Cumplido**: 0,5040 · 0,5480 · 0,9276 · 1,2478 · 1,4952 |
| Modelo | Señal por encima de la longitud del texto | **Cumplido**: correlación parcial 0,657 |
| Producto | Un usuario sin formación técnica completa el recorrido | **Cumplido con reservas**: lo completó, y de esa sesión salieron 8 correcciones |
| Producto | Accesibilidad de color | **Cumplido**: las cinco paletas superan WCAG AA; la peor, 9,51 |
| Producto | Robustez | **Cumplido**: 183 pruebas de estrés y 27 pasos de integración, ningún manejador lanza hacia la interfaz |
| Operación | Enlace permanente disponible | **Pendiente** (A2) |
| Operación | Catálogo medido, no heredado | **En curso** (A3) |
| Impacto | Proporción de libros terminados | **Sin instrumentar** (A9) |

*Cuadro 3. Métricas por nivel, con su estado real.*

---

## 7. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El enlace de la demostración muere durante la evaluación | Alto | A2: despliegue permanente, probado desde un dispositivo ajeno antes de la fecha |
| El servicio externo de lenguaje agota su presupuesto en mitad de una demostración | Medio | Ya mitigado: la aplicación degrada con un mensaje legible y conserva diccionario, fonética, audio, buscador y puntuación |
| Que la letra MCER se lea como una certificación | Alto, reputacional | Declaración de alcance en el documento y aviso permanente en pantalla |
| Que la remedición del catálogo no termine a tiempo | Medio | El proceso es reanudable por bloques y los resultados se guardan por lotes; lo medido ya es utilizable aunque falte el resto |
| Sobrecarga del espejo de descarga de Project Gutenberg | Medio, ético | Seis hilos y no treinta, cada uno con su pausa entre peticiones; y el vocabulario se obtuvo del SPGC, no rascando el sitio |
| Contenido inapropiado para una lectora menor de edad | Medio | Decisión razonada de **no filtrar por contenido** y avisar en la ficha; se argumenta en el apartado 8.4 del documento principal |

*Cuadro 4. Riesgos y mitigaciones.*

---

## Referencias

Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of
experiments examining the effects of extrinsic rewards on intrinsic motivation.
*Psychological Bulletin, 125*(6), 627–668.
https://doi.org/10.1037/0033-2909.125.6.627

Krug, S. (2014). *Don't make me think, revisited: A common sense approach to
web usability* (3ª ed.). New Riders.

Nakanishi, T. (2015). A meta-analysis of extensive reading research. *TESOL
Quarterly, 49*(1), 6–37. https://doi.org/10.1002/tesq.157

Nielsen, J. (2000, 18 de marzo). *Why you only need to test with 5 users*.
Nielsen Norman Group.
https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/

World Wide Web Consortium. (2023). *Web Content Accessibility Guidelines (WCAG)
2.2*. W3C. https://www.w3.org/TR/WCAG22/
