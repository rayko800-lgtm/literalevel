# Lectura de profesor

**Qué es esto.** Una lectura de los tres entregables *como los leería quien los
califica*: Mtro. Fernando Barranco, Módulo 5 (Integrador). No se comprueba
ninguna cifra contra el código ni se buscan desajustes entre archivos —eso lo
hacen otros—. Aquí se lee la prosa: qué no se entiende a la primera, dónde el
documento se disculpa hasta ahogar lo que afirma, dónde afirma más de lo que
puede, y qué echará de menos este lector en concreto.

Orden: por cuánto afectan a la nota. Las cinco primeras son las que yo
arreglaría si solo hubiera tiempo para cinco.

Leídos: `entrega/documento.md` (1.364 líneas), `entrega/presentacion.tex`
(12 diapositivas), `entrega/guion_video.md`. Se consultó además
`entrega/estrategia.md` porque el §3 del documento delega en él toda la
estrategia, que es justo lo que este profesor exige.

---

## 1. Las conclusiones no terminan en decisiones. Terminan en métricas y en deudas

`documento.md:1148–1233`. La sección tiene ocho párrafos en negrita. Seis son
metodológicos o de laboratorio: la separación de corpus, el experimento no
controlado, el tamaño del salto del *embedding*, la ley de Zipf, fp16 e int8.
Uno es de producto (`1220`). Y el último cierra así:

> «**Y queda pendiente lo que más pesa.** La aplicación funciona y ya tiene
> dirección fija, pero sobre el hardware más barato: se suspende por
> inactividad y no guarda nada entre reinicios.» (`1227–1229`)

Barranco valora que el proyecto **termine en decisiones de negocio, no en
métricas**. Este cierra en una lista de lo que falta. La última frase que se
lleva el lector es una carencia de infraestructura.

**Propuesta:** mover «Escalar el corpus no siempre mejora nada» (`1205`) y «La
velocidad se ganó sin mover ninguna cifra» (`1211`) al §7, y cerrar con tres
decisiones tomadas y su consecuencia: *no se certifica* (y por eso hay bandas),
*no se filtra el catálogo* (y por eso hay aviso), *se precalcula* (y por eso
medir Gutenberg entero cuesta horas y no una licencia anual).

---

## 2. El caso de uso está recorrido tres veces, con tres lectores distintos

Es lo que este profesor más premia —su «Ejemplo de uso y aplicación»— y es
donde los tres entregables se despegan:

- `documento.md:861` → «Tomemos el caso concreto de un lector cuyo perfil da
  **1,20** sobre 2 (banda intermedia, ancla B2)», que busca «*una novela de
  detectives victoriana*».
- `presentacion.tex:249` → «una lectora de 15 años que el sistema sitúa en
  **0,93**», que busca «algo de misterio, no muy largo» y elige *Sherlock
  Holmes*.
- `guion_video.md:102` → «*una novela de detectives victoriana*», sin nivel.

Y dentro del propio recorrido del documento, el paso 4 mide *Notes from a Dead
House* (`887–890`, media 1,73), un libro muy por encima del 1,20 del lector que
protagoniza el apartado, y la ficha del paso 3 se ilustra con *Alice*, *Pride
and Prejudice* y *Crime and Punishment*. El apartado se llama «Un recorrido
completo, con números reales» y lo que hay es un montaje de mediciones de libros
distintos.

**Propuesta:** un lector, un número, un libro, en los tres entregables. Si es
*Sherlock Holmes* a 0,93, que la curva del paso 4 sea la de *Sherlock Holmes*.

---

## 3. §7.4: las salvedades ahogan el resultado principal

El Cuadro 10 es *el* resultado del trabajo —el orden creciente por nivel MCER—.
Detrás vienen **383 palabras seguidas de advertencias** (`738–770`) sobre cuál
de las cuatro reglas del filtro se desactiva al unir líneas con espacios, y
sobre qué pasaría si no se desactivara:

> «Medido cambiando una cosa y sólo una: con saltos de línea sobreviven **31
> textos en vez de 47**, y A1 se queda con uno solo, con lo que la comprobación
> de orden creciente ya no se puede hacer sobre cinco niveles.» (`744–746`)

Y el remate: «los tres textos A1 que sostienen el escalón más débil del Cuadro
10 **no pasan el filtro de la aplicación**» (`765–767`). Al terminar el
apartado, el lector no sabe qué se está afirmando: si el orden de cinco niveles
vale, si vale el de cuatro, o si ninguno. Un documento académico tiene que
sostener lo que mide.

**Propuesta:** afirmar el resultado sobre A2–C1 (44 textos, cuatro niveles,
todos fuera del ruido), decir en una línea que A1 se excluye por tener 3 textos
que la aplicación rechazaría, y bajar toda la forense del filtro a un anexo.
Se pierde un nivel y se gana una afirmación defendible.

---

## 4. Faltan las reglas del juego: cinco conjuntos de evaluación sin mapa

A lo largo del documento circulan **144**, **38**, **47**, **31** y **59**
textos, con Spearman 0,908 / 0,829 / 0,860 / 0,807 / 0,668, y correlaciones
0,879 y 0,765 «antes y después de filtrar» (`430–433`). Cada cifra está bien
explicada donde aparece, pero nunca están todas juntas, y el lector pierde el
hilo ya en `424–433`:

> «el rango evaluable **de esa tanda de análisis** se encoge de cinco niveles a
> cuatro (A2–C1) […] La reproducción local del Cuadro 10 sí conserva los cinco,
> con tres textos en A1, porque filtra con otras reglas.»

**Propuesta:** un «Cuadro 0» al final del §2 con cinco filas —conjunto, n, de
dónde sale, qué mide, dónde se usa— y citarlo por nombre después. Es media
página que hace legible medio documento.

---

## 5. El 0,89 de la comparación competitiva no es del modelo desplegado

`documento.md:989–998` (Cuadro 16) y `presentacion.tex:287–320`. La barra más
larga de la diapositiva 9 se llama **LiteraLevel** y vale 0,89. Pero ese 0,89
sale de `documento.md:584`:

> «El modelo afinado directamente sobre el texto es un **`roberta-base`** […] y
> alcanza además **RMSE 0,560** y **correlación de Pearson 0,89**»

…y tres líneas después el propio documento avisa: «Ese `roberta-base` **no es
el modelo que se despliega**» (`588`). La diapositiva gana la comparación con
un modelo que no se entrega. El descargo del pie («no son comparaciones cara a
cara») advierte de otra cosa: de la partición ajena, no de que el número sea de
otro modelo.

**Propuesta:** etiquetar la barra «`roberta-base` afinado sobre CLEAR
(experimento)» y añadir al pie «el modelo desplegado es otro y no se midió en
este corpus».

---

## 6. La diapositiva 5 pone en el mismo eje tres cifras que el documento prohíbe restar

`presentacion.tex:178–180`: 1,061 (17 variables) · 0,93 (*embedding*) · 0,67
(transformador). En el Cuadro 7 (`documento.md:565–569`) el 1,061 es de la
tanda **recalculada** y los otros dos de la **histórica**, y las conclusiones
dedican un párrafo entero a avisar de esto:

> «porque el cuadro 7 tiene dos tandas y es fácil restar filas que no se pueden
> restar» (`1187–1188`)

Además el título de la diapositiva —«El cuello de botella **era** la
representación»— afirma en indicativo lo que `documento.md:1178–1185` matiza:
«esto no es un experimento controlado y no conviene venderlo como tal».

**Propuesta:** tres barras de la misma tanda, o marcar la primera con un
asterisco y una línea al pie; y titular «Cambiar la representación movió el
resultado; subir la potencia del clasificador, no».

---

## 7. El vídeo promete el resultado que el documento declara no medido

`guion_video.md:149–150`:

> «Para el lector eso significa una cosa muy concreta: **deja de abandonar
> libros**.»

`documento.md:1166–1168`: «no es una demostración de que ayude a elegir mejor
un libro. Ese vínculo queda pendiente». Y el abandono es el punto 6 de trabajo
futuro. Es la única frase del vídeo que un evaluador puede contrastar con el
documento y encontrarla desmentida por el propio autor.

**Propuesta:** «Para que la próxima vez empieces por el libro que te toca, y no
por el que te va a echar.» Promete la elección, que es lo que sí se entrega.

---

## 8. El vídeo enseña un catálogo de 1.197 libros y dice 61.642

`guion_video.md:141–147`: «Project Gutenberg tiene **61.642 libros en inglés**
[…] y **los estamos midiendo todos** […] Lo ya medido se abre al instante; lo
demás lo mide la aplicación al abrirlo.» En pantalla, mientras tanto, está la
aplicación real: 1.197 libros, de los que **148 se pueden abrir**
(`documento.md:326`). Un espectador que pulse el enlace del final ve otra cosa
de la que oyó.

**Propuesta:** «El catálogo de hoy son 1.197 libros. El objetivo, ya
presupuestado en horas de cómputo, es todo Gutenberg: 61.642.» La cifra grande
sigue estando, y deja de ser una promesa contra la pantalla.

---

## 9. El vídeo dice «leyendo el libro entero» justo donde la app hace un vistazo

`guion_video.md:107–109`: «Y esta curva: **la dificultad capítulo a capítulo**,
medida por el modelo leyendo el libro entero.» Pero el §8.4 del documento
advierte —bien— contra exactamente eso:

> «el resumen declara cuál de los dos se ejecutó, porque un vistazo que
> presumiera de haber leído el libro entero acabaría citado como si lo hubiera
> hecho.» (`documento.md:967–969`)

Si en la demo se ejecuta el vistazo (30 capítulos × 2 ventanas) y la voz dice
«libro entero», el vídeo comete el error que el documento describe.

**Propuesta:** acotación de rodaje —«ejecutar el análisis completo sobre un
libro corto, o decir *en modo vistazo*»— y una frase: «esto es un vistazo; el
análisis completo tarda minutos y da la curva entera».

---

## 10. La limitación 9 contradice la corrección que el §7.4 presume de haber hecho

`documento.md:1074`:

> «Las cifras del apartado 7.4 se reportan tal como constan **en la tarjeta del
> modelo**.»

`documento.md:669–671`: «aquí **no hay ningún archivo que las respalde**, y una
versión anterior de este documento citaba una tarjeta
`metricas_literalevel_v4.json` **inexistente**». Es la única contradicción
interna que encontré leyendo, y es de las caras: el documento dedica un párrafo
a corregir esa cita y luego la reintroduce en la lista de limitaciones, que es
donde el evaluador va a buscar precisamente eso.

**Propuesta:** «Las cifras del apartado 7.4 proceden de la ejecución de
entrenamiento en Google Drive; no hay en el repositorio ningún archivo que las
respalde.»

---

## 11. La frase más difícil del documento está en el apartado que más se lee

`documento.md:872–882`, paso 3 del recorrido: **134 palabras**, tres incisos con
raya, dos cifras entre paréntesis mental y una explicación causal al final:

> «Aparece la ficha, **contada sobre el texto y no sobre metadatos**, aunque no
> toda sobre el libro entero: las palabras y el tiempo de lectura salen del
> fichero completo, y la longitud de frase, el diálogo y el vocabulario se
> calculan sobre una muestra con **tope de 60.000 palabras**, repartido a partes
> iguales entre los capítulos —la variedad léxica, sobre las primeras 20.000 de
> esa muestra—, porque recorrer *Guerra y paz* entero para pintar una ficha
> haría esperar al lector.»

Aquí el lector va siguiendo a una persona que abre un libro; obligarle a
sostener tres alcances de muestreo a la vez lo saca del relato.

**Propuesta:** «Aparece la ficha, contada sobre el texto y no sobre metadatos:
palabras reales, tiempo de lectura, longitud de frase, diálogo, vocabulario y
palabras repetidas.» Y una nota al pie con el muestreo.

---

## 12. El resumen tarda 134 palabras en dar un resultado y ya se está disculpando

`documento.md:40–51`. La frase central lleva un inciso dentro del inciso y una
referencia adelantada a una limitación que está a mil líneas:

> «sobre un corpus externo que no se usó para ajustar los pesos —**aunque sí se
> exploró durante el desarrollo, y eso se detalla en la limitación 6**—, ordena
> los niveles del Marco Común Europeo de forma estrictamente creciente»

y después: «**con una salvedad que conviene leer junto a las cifras**: el
escalón A1–A2 es de 0,052 sobre desviaciones de 0,111 y 0,223, y descansa en
tres textos». Un resumen que se autoenmienda antes de terminar de afirmar
enseña un trabajo inseguro de sí mismo, no uno honesto.

**Propuesta:** afirmación en una frase (el orden crece de A2 a C1 sobre textos
externos con nivel oficial), salvedad en otra frase corta (A1 no se sostiene con
3 textos y no se usa para concluir), y fuera la remisión a la limitación 6.

---

## 13. El documento abre con una nota administrativa a la defensiva

`documento.md:9–21`. Lo primero que lee el profesor, antes del resumen, son
trece líneas sobre por qué dos archivos no coinciden:

> «**No es una contradicción**: es que el entregable es el PDF y este `.md` es
> la copia de lectura. Si buscas algo de estrategia y no está aquí, está en el
> PDF o en `estrategia.md`.»

Empezar defendiéndose de una acusación que nadie ha hecho es la peor primera
impresión posible, y además siembra la idea de que hay descuadres.

**Propuesta:** una línea, en cursiva y pequeña: «*Copia de lectura. El
entregable es `documento.pdf`; la numeración de cuadros difiere.*» El resto,
al final.

---

## 14. Siete veces «una versión anterior de este documento» — y una de ellas abre las conclusiones

`documento.md` líneas `145`, `287`, `669`, `726`, `953`, `1041`, `1151`. El
documento narra su propia errata en voz alta. El caso peor es el más visible de
todos, la primera línea de las conclusiones:

> «**Se cumplió el objetivo ordinal, que era el objetivo.** Y conviene separar
> dos cosas que esta frase mezclaba en una versión anterior, porque vienen de
> corpus distintos.» (`1150–1151`)

El lector no vio la versión anterior. Lo único que percibe es que el autor está
discutiendo consigo mismo en el párrafo que debería rematar el trabajo. La nota
global del §9 (`1031–1043`) ya cubre esto muy bien y con dignidad: basta con
ella.

**Propuesta:** conservar la nota del §9 y borrar las siete menciones locales.
En las conclusiones: «Se cumplió el objetivo ordinal, que era el objetivo. Hay
dos resultados y vienen de corpus distintos.»

---

## 15. La estrategia va en el §3, antes de la evidencia que la justifica

En el PDF (`documento.tex:510`) la Estrategia está desarrollada entera como §3,
antes de Datos, EDA y Modelación. Formalmente cumple —está antes de concluir—,
pero el lector se encuentra los accionables, las métricas de éxito y los riesgos
sin saber todavía si el modelo funciona. Y el §11 no vuelve a recogerlos, que es
lo que produce el problema nº 1 de esta lista.

Defendible: da marco de negocio antes que técnica. Pero la plantilla de este
profesor coloca la estrategia **después de los hallazgos**, para que se lea como
consecuencia y no como declaración de intenciones.

**Propuesta mínima (sin mover nada):** cerrar el §3 con una línea —«los
accionables se justifican con lo que se mide en los apartados 5 a 8 y se
recogen en las conclusiones»— y recogerlos de verdad en el §11.

---

## 16. La estrategia está optimizada para puntos de rúbrica, no para el negocio

`estrategia.md:355–380`. Es el entregable donde este profesor busca visión de
negocio, y lo que dice literalmente es:

> «Diez acciones concretas, ordenadas por **puntos de rúbrica protegidos u
> obtenidos por hora de trabajo**.»

Y el A5 es «**Conseguir un micrófono** (auriculares con micro)», justificado
porque «es la función más vistosa y la que mejor encaja con “usabilidad para el
usuario final”». Eso es gestión de la entrega, no estrategia. El A9 —instrumentar
la proporción de libros terminados— sí lo es, y está el noveno.

**Propuesta:** ordenar por valor para el lector (A9, A3, A7, A4…), dejar el
micrófono y el orden por rúbrica en una nota de ejecución aparte, y sustituir la
frase de apertura por «ordenadas por valor entregado al lector por hora de
trabajo».

---

## 17. La presentación no tiene diapositiva de conclusiones, y dos dicen lo mismo

12 diapositivas. La 2 (`presentacion.tex:104–115`) dice «No porque no sepa
inglés. Porque eligió mal el libro» y la 12 (`375–376`) dice «no lo eras. Era el
libro». Es la misma idea, y funciona como marco… pero a cambio no hay ninguna
diapositiva que diga qué se concluye. Un mazo que nunca enuncia sus conclusiones
es un hueco visible en cualquier rúbrica.

**Propuesta:** convertir la 11 («Lo que esto no es») en «Conclusiones» con tres
líneas —el orden se cumple, el cuello de botella era la representación, el valor
está en el recorrido— y dejar el «no certificamos» como una de las tres.

---

## 18. La presentación no enseña análisis exploratorio

Salto de la 3 («Los datos, en cifras») a la 4 («Objetivos») y de ahí a
«Hallazgo 1», que es una comparación de modelos. La 6 (longitud contra nivel) es
bivariado de facto pero no se presenta como tal. Este profesor organiza el EDA en
univariado / bivariado / multivariado y lo va a buscar.

**Propuesta:** renombrar la 6 como «Bivariado · nivel y longitud van juntos» y
añadir al pie de la 3 dos hallazgos univariados con cifra desnuda: el 60,4 % del
catálogo heredado etiquetado A1, y las 2.838 millones de palabras del SPGC que
confirman Zipf. Cabe sin añadir diapositiva.

---

## 19. En la diapositiva 8, el descargo va arriba y ocupa cuatro líneas

`presentacion.tex:248–252`. Lo primero que se proyecta en la diapositiva del
caso de uso es:

> «Los pasos y lo que produce cada uno son los de la aplicación; el nombre y el
> perfil ilustran, no son una sesión registrada. La única prueba de usuario real
> del proyecto es la de Esmeralda, $n=1$, y está en el documento.»

Es correcto decirlo. No es correcto que sea el titular de la diapositiva que
Barranco más va a mirar.

**Propuesta:** al pie, en `\footnotesize`: «Recorrido ilustrativo. La prueba de
usuario real (n = 1) está en el documento.»

---

## 20. La cifra «3–5 h» viaja sola, y el propio documento dice que el cuello de botella es otro

`documento.md:947–960`. En el mismo párrafo conviven «entre 3 y 5 horas de
A100» y:

> «El cuello de botella real resultó no ser el modelo sino la descarga: en
> serie, a 0,3 libros/s, los libros tardarían 57 horas en bajar.»

El resumen (`61–63`) y el vídeo se quedan solo con la primera. La diapositiva 10
sí acota bien («la descarga va aparte»), y ese es el modelo a seguir.

**Propuesta:** en el resumen, «entre tres y cinco horas de cómputo en una A100,
más la descarga, que es el cuello de botella real». Y partir ese párrafo en dos:
uno de cómputo, otro de descarga.

---

## 21. El lector maneja cuatro modelos sin que nadie se los presente

Por el documento circulan v1, v2, v4, `roberta-base`, `distilroberta-base` y
`all-MiniLM-L6-v2`. El §7.3 compara «v1 y v2» (`609–610`) sin haber dicho antes
qué son, y el §7.4 introduce v4 como «el modelo en producción» sin relacionarlo
con los anteriores. Cuando en el Cuadro 8 aparece un **−0,239** para v1 en
British Council, el lector no sabe si eso descalifica algo que sí se usa.

**Propuesta:** tres líneas al abrir el §7: «v1: afinado sobre `BT_easiness`, es
el que etiquetó el catálogo heredado. v2: afinado sobre material graduado,
descartado. v4: `distilroberta` anclado al MCER, es el desplegado.»

---

## 22. §7.5: el argumento bueno está enterrado dentro de un inciso

`documento.md:785–789`, 115 palabras con raya dentro de raya:

> «Lo que sostiene al modelo es la tercera fila: **aporta señal por encima de la
> longitud**, que es precisamente lo que un contador de palabras no puede hacer
> —y conviene decirlo con precisión: no es que su correlación parcial sea peor,
> es que **no está definida**, porque descontar la longitud de la propia
> longitud deja un residuo de varianza cero—.»

El remate («no está definida») es el mejor argumento del apartado y va escondido
dentro de un guion largo.

**Propuesta:** «El modelo conserva 0,668 al descontar la longitud. Para el
contador de palabras esa correlación ni siquiera existe: descontar la longitud
de sí misma no deja nada que correlacionar.»

---

## 23. §8.3: 232 palabras para concluir que ninguna cifra se mueve

`documento.md:928–945`. La viñeta del *padding* incluye un texto de prueba, la
ventana más corta (258 *tokens*), un texto artificial hipotético de 250
monosílabos que daría 252, 300 ventanas idénticas, 112 ventanas de *Alicia*, 103
coincidencias exactas y una diferencia de 4,8 × 10⁻⁷. Y termina donde podía
haber empezado: «Las cifras del catálogo se guardan con tres decimales, así que
una diferencia de ese tamaño no puede mover ninguna».

**Propuesta:** dos frases —«Agrupar ventanas en lotes distintos cambia como
mucho 4,8 × 10⁻⁷ cuando el lote mezcla capítulos de longitudes distintas; el
catálogo guarda tres decimales, así que no mueve ninguna cifra publicada»— y el
detalle al anexo.

---

## 24. El bloque de demo del vídeo no cabe en su ventana

`guion_video.md:92`, «S — SATISFACCIÓN · 1:15 – 3:20»: 2 minutos 5 segundos para
cinco pasos, tres de ellos con espera real —el nivel, la búsqueda, la curva— y
uno con lectura en voz alta al micrófono. El propio documento mide 12,7 s para
un vistazo (`853`) y 86 s para el recorrido completo de un libro (`888`). A eso
hay que sumarle el riesgo del arranque en frío: la limitación 12 (`1104–1108`)
mide **31–32 s** si el Space lleva 48 h sin visitas.

**Propuesta:** añadir a la lista de comprobación previa dos líneas —«abrir la
aplicación 10 minutos antes de grabar» y «ejecutar la curva una vez antes de
grabar: la segunda tarda 0,02 s porque queda en caché»— y elegir un libro corto
para el paso 3.

---

## 25. El mismo objeto con dos nombres: «cuaderno» y «cuadernillo»

Cuatro veces cada uno (`documento.md`, p. ej. `357`, `458`, `505`, `1090`,
`1190`). En un documento que distingue con tanto cuidado entre tandas, corpus y
filtros, llamar de dos maneras al entregable hace dudar de si son dos cosas.

**Propuesta:** «cuaderno» en todas.

---

# Lo que está bien escrito, y conviene no tocarlo

Esto también orienta, y en este documento hay bastante:

- **El Cuadro 5 (`documento.md:483–495`) es la mejor página del trabajo.** Cada
  transformación con su columna de «Evidencia / consecuencia», y evidencias que
  son historias reales: el filtro que estaba muerto en producción, la carta de
  menú de 432 palabras puntuada como prosa, las 2.900 palabras de licencia
  dentro del capítulo XII de *Alice*. Eso es exactamente «no se transforma sin
  medir qué se rompió», demostrado en vez de proclamado.

- **El Cuadro 13 con las hipótesis rechazadas** (`822–837`). Int8, fp16,
  `inference_mode`, el esfuerzo de razonamiento mínimo: cada rechazo con su
  número y su motivo. Reportar lo que no funcionó, con cifra, es raro en
  trabajos de estudiante y aquí está hecho sin coquetería.

- **Publicar el *baseline* de contar palabras antes de que lo pregunten**
  (`415–422`, Cuadro 12, y la diapositiva 6 entera). «Se enseña porque es la
  comparación más desfavorable del proyecto, y ocultarla sería el peor error
  posible» (`presentacion.tex:210–211`) es la mejor frase de la presentación.

- **La Declaración de alcance** (`1237–1258`). Limpia, sin una sola salvedad de
  más, y dice qué no se debe hacer con la herramienta en frases que se entienden
  a la primera. Es el registro que le falta a los apartados 7.4 y 8.3.

- **El §4.3, problema por problema.** El menú de restaurante en A1, el enlace de
  `SWgdlgdl201` al libro equivocado, la portadilla de *War and Peace* saliendo
  como «capítulo más fácil». Se recuerdan, que es lo que hace que un evaluador
  crea que hubo trabajo de datos de verdad.

- **La diapositiva 1 y la 2.** «¿Está este libro en inglés a tu nivel de
  lectura?» explica el proyecto en diez segundos, y el arranque —«lo abre… y a
  las tres páginas lo cierra»— es mejor que cualquier definición.

- **El guion no abre con «Hola, soy Miguel».** Y lo justifica
  (`guion_video.md:190–192`). El bloque A entero, tal cual, se queda.

---

## Si solo hay tiempo para tres cosas

1. **Reescribir el §11** para que termine en decisiones (obs. 1). Es donde este
   profesor pone la nota de cierre.
2. **Unificar el caso de uso** en los tres entregables (obs. 2) y desatascar el
   §7.4 (obs. 3).
3. **Arreglar las tres frases del vídeo** que prometen de más (obs. 7, 8, 9).
   Son tres líneas de texto y quitan la única grieta que un evaluador puede
   comprobar en cinco minutos.
