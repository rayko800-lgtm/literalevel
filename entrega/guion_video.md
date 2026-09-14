# Guion del vídeo — LiteraLevel (Módulo 5)

**Formato exigido:** MP4, **máximo 5 minutos**, Miguel **hablando a cámara todo el
tiempo** con las diapositivas de fondo. Vale 20 de los 110 puntos.
Recomendación del profesor: grabar con **OBS**.

**Duración objetivo: 4:40.** Los cinco minutos son un tope, no una meta, y pasarse
es el único error irrecuperable de este entregable.

**El texto hablado son 496 palabras: 3:18 a 150 palabras por minuto y 3:49 a 130.** Lo cuenta `tools/contar_guion.py`, que trae la regla escrita: lo que va entre comillas angulares dentro de las fases ANSVA, descontando las acotaciones entre paréntesis y las notas de producción. Esa cifra se ha publicado mal tres veces por contarla cada vez de una manera; ahora se ejecuta. Lo que falta hasta 4:40 no es un descuido: es el presupuesto para lo que la demo tarda *de verdad*
—esperar a que responda la búsqueda, a que llegue la explicación, que suene el
audio, leer la frase en voz alta—, hasta unos 55 segundos. Si al ensayar te sale
muy corto, no metas más texto: ve más despacio y deja respirar las pausas.

Esta versión fusiona el guion de b9 (698b804) con tres cambios del de Codex
(13281a9): el texto recortado a menos de 500 palabras, la hoja de la palabra
contada en dos tiempos (lo local al instante; la traducción y la explicación
después, con IA) con el perfil 1,20 dicho como preparado para el ejemplo, y la
preparación de la toma (respaldo rotulado, privacidad y ensayo cronometrado).

---

## Por qué está construido así

Sobre el método **ANSVA** de Fernando Miralles, campeón de España de oratoria, que es
la secuencia clásica de
persuasión: **A**tención · **N**ecesidad · **S**atisfacción · **V**isualización ·
**A**cción. No es un adorno: encaja con lo que la rúbrica del módulo 5 premia,
porque el módulo declara que lo que evalúa es *«hacer que esos modelos sean
accesibles y valiosos para un usuario final»*. ANSVA obliga a hablar del usuario
antes que del modelo, que es exactamente el orden que pide Barranco.

> **Nota honesta sobre las fuentes.** ANSVA está verificado y es suyo. Miralles
> enseña además una *«estructura de la sardina»*, y PAS, y ADP, de las que encontré el nombre
> pero **no su anatomía exacta** en fuentes públicas — está en su libro y su
> curso. No se ha usado, para no inventarla.

Y se cruza con la plantilla de la **presentación modelo del propio profesor**
(`Ejemplopresentacindehallazgos.pdf`): cifras grandes y desnudas en vez de
párrafos, objetivos numerados, métricas sin adornos, y sobre todo su
**«Ejemplo de uso y aplicación»** — tomar *un* caso real y recorrerlo paso a
paso. En su proyecto de Yelp ese recorrido es el corazón de la presentación.
Aquí es **el mismo caso que recorren el documento (§8.2) y la diapositiva
«Ejemplo de uso y aplicación»**: un perfil **1,20 sobre 2**, preparado para el
ejemplo, y *Crime and Punishment*. Los tres entregables cuentan el mismo
recorrido, con el mismo perfil y el mismo libro. **La aplicación que se enseña
es el front de Angular** (`mikemaki1763-literalevel-front.static.hf.space`), en
el móvil: es lo que se entrega desde el 13 de septiembre de 2026, a petición
del profesor.

---

## Consejos de entrega, en tres líneas

- **Mira a la cámara, no a la pantalla.** Es lo que la rúbrica exige y lo que
  más se nota. Pon la ventana de OBS justo debajo del objetivo.
- **Las pausas no son huecos, son puntuación.** Después de cada cifra grande,
  callarse un segundo. El silencio es lo que hace que un número suene grande.
- **Ensáyalo dos veces con cronómetro y una tercera grabando.** Nunca a la
  primera: el primer intento siempre sale a 6 minutos.

## Preparación de la toma

- **Ensayo cronometrado, y se corta a 4:40.** Si un ensayo pasa de 4:40, se
  detiene y se recortan acciones (menos toques, menos espera), no palabras
  dichas más deprisa. El MP4 final nunca pasa de 5:00.
- **Privacidad.** Entra antes de grabar y fuera de plano: en la toma no se ven
  la contraseña, el identificador de lector, la consola del navegador, claves
  ni paneles de administración.
- **Grabación de respaldo.** Graba antes el mismo recorrido. Si en directo algo
  falla y se usa, va rotulada en pantalla como **grabación previa**: nunca se
  presenta una reproducción como respuesta en vivo.
- **La boca en 3D, de lejos.** Hasta que el front desplegado lleve los `.glb`
  corregidos (rama `boca3d`, 75f334a), la lengua que carga es la anterior y roza
  los dientes en seis sonidos, entre ellos las dos *th*. Si se abre el 3D, no
  acercar la cámara a la lengua; para enseñar el movimiento basta el corte 2D.

---

# EL GUION

## A — ATENCIÓN · 0:00 – 0:30

> **En pantalla:** portada. Solo el nombre *LiteraLevel* y una frase.
> Sin logotipo animado, sin música.

**Miguel, a cámara:**

«Un hispanohablante que quiere leer en inglés se topa siempre con el mismo
muro. Elige un libro que suena bien, lo abre… y a las tres páginas lo cierra.

No porque no sepa inglés. Porque **eligió mal el libro**.

Nadie le dijo que *Moby Dick* le quedaba grande y que *El sabueso de los
Baskerville* le quedaba justo. Eso es lo que hace LiteraLevel.»

> *Pausa de un segundo antes de pasar de diapositiva.*

---

## N — NECESIDAD · 0:30 – 1:00

> **En pantalla:** tres cifras grandes, una por línea. Nada más.
> **1.500 millones** de personas estudian inglés · **la lectura extensiva**
> es de los métodos con más respaldo · **53.179** libros gratis, medidos.

«La investigación es clara: leer mucho, a un nivel algo por encima del tuyo,
es de lo que mejor funciona.

El problema no es encontrar libros: hay decenas de miles gratis. El problema es
**saber cuál**.

Las etiquetas que existen —A1, B2, C1— casi nunca las pone alguien que haya
leído el libro. Y un libro no tiene una sola dificultad: cambia de capítulo a
capítulo.»

---

## S — SATISFACCIÓN · 1:00 – 3:35

> **En pantalla:** el **front de Angular en el móvil** y **usarlo de verdad**.
> Nada de capturas pegadas: que se vea el dedo (o el cursor) moverse. Dos
> maneras de enseñar el móvil en OBS: la pantalla del teléfono duplicada en
> el equipo, o el navegador del equipo con la vista de dispositivo a
> **390 px** de ancho, que es como se probó el front. Miguel sigue a cámara
> todo el rato; la app va en una ventana al lado.
> **Usa el mismo caso que el documento §8.2 y la diapositiva «Ejemplo de uso
> y aplicación»**: perfil **1,20** y *Crime and Punishment* (PG2554). Las
> cifras que se dicen —203.415 palabras, media 1,70— son las que dio la app
> publicada el 12 de septiembre de 2026, con el libro abierto desde el
> buscador (en `.txt`, el mismo texto con el que se midió el catálogo, 836
> ventanas; el documento cita 203.699 y 840 porque aquella medida se hizo
> sobre el EPUB: no mezclar las dos). El motor es el mismo detrás del front,
> así que las cifras no cambian; si la ficha enseña otro valor, **di el que se
> ve**. Y el libro **se abre desde el buscador**: escribe «dostoyevski» en
> *Encontrar* y sale.
>
> **El libro del recorrido tiene que ser uno que el buscador devuelva.** Si
> hay que subirlo a mano, el paso Dos deja de ser cierto delante de cámara.
>
> **Entra antes de grabar, y úsala.** Entrar es *Ajustes → Tu perfil*
> (usuario y contraseña), fuera de plano: sin entrar, la explicación en
> contexto y la corrección de pronunciación no salen, porque son lo que cuesta
> dinero. Y tres cosas de la primera vez, medidas el 11 de septiembre de 2026 y
> que siguen igual, porque el motor es el mismo:
>
> - La **primera consulta léxica de la sesión tarda unos 55 segundos**:
>   carga el diccionario de 243 MB, spaCy y el modelo de similitud. Los
>   **40 milisegundos** que dices a cámara son **en caliente** y cubren **solo
>   lo local**: lema, diccionario, acepción y fonética (§8.2 del documento).
>   **La traducción y el «Aquí significa» salen de la IA** y llegan unos
>   segundos después, en la segunda etapa de la hoja: no los atribuyas al
>   diccionario ni a los 40 ms. **Consulta una palabra cualquiera antes de
>   grabar** y el paso Cuatro va fluido. Si el motor llevaba horas sin
>   visitas, la primera llamada tarda además medio minuto en despertarlo; el
>   front lo dice en pantalla. Despiértalo antes.
> - **Calcula la curva del libro antes.** Queda guardada, así que en la
>   toma sale en segundos en vez de en dos minutos de silencio. Y hasta
>   que no está calculada, la ficha no sabe si el libro te queda por
>   encima y te da el rango en vez del dato.
> - **Con tu perfil puesto, *Crime and Punishment* no sale el primero.**
>   Probado en la app publicada el 12 de septiembre de 2026 con un perfil
>   de 1,34: «dostoyevski» devuelve primero *Best Russian Short Stories* y
>   **el nuestro, segundo**; sin perfil sale tercero, tras *The Idiot* y
>   *The House of the Dead*. Con otro perfil puede moverse un puesto. Está
>   en la lista y se abre bien; **elígelo sin dudar**, que dudar delante de
>   la cámara parece que la app no lo encuentra.
> - **Con perfil 1,20 no esperes capítulos sugeridos para este libro.** Su
>   capítulo más llevadero mide 1,52, por encima de lo que la app ofrece a
>   ese nivel, así que la sugerencia —bien hecha— no sale. Si quieres
>   enseñarla, abre *Alice's Adventures in Wonderland* o *Adventures of
>   Huckleberry Finn*: los dos quedan por encima y tienen capítulos a tu
>   nivel.
>
> **El perfil 1,20 se prepara antes y se dice como preparado.** El
> cuestionario no garantiza ese número: responderlo en directo puede dar otro.
> Deja puesto el perfil de 1,20 y, en el paso Uno, enseña el resultado.
> *Mídeme con un texto*, que nombras, y *Mídeme con un libro que ya leí* están
> en *Tu nivel*, bajo «Afinar»: no las hagas en directo, que el libro tarda en
> medirse.
>
> **Y la palabra del paso Cuatro se elige antes, no en directo.** El
> diccionario solo trae fonética en el 3,1 % de sus entradas —el 58 % de las
> consultas sobre un libro real, §6.4 del documento—, así que la fonética
> depende de la palabra que se toque. Y hay una
> segunda trampa, medida: **las palabras con el contraste británico/
> americano más bonito son las polisémicas, que es justo donde el
> desambiguador flojea**. De las tres apariciones de *clerk* en estos
> capítulos, dos devuelven una acepción eclesiástica —«laico que asiste en
> el oficio anglicano»— y las tres salen marcadas «dudosa».
>
> Así que la palabra del plano está **medida**, no elegida por bonita:
> **poverty**, afinidad **0,505** —por encima del umbral de duda, así que
> sale sin aviso—, acepción correcta, y */ˈpɒvəti/* frente a */ˈpɑːvɚti/*
> se oye. Está en *«He was in terrible poverty, yet he took upon himself
> the payment of his brother's debts»*, y encima es el tema del libro. Si
> quieres otra: **torture** (0,504) o **cruelty** (0,502). En la hoja de la
> palabra se ve **«En español»** (la traducción) y **«Aquí significa»**; la
> marca **IA** solo sale cuando la definición no viene del diccionario, así
> que **para enseñar la marca toca antes una palabra que Wiktionary no
> traiga** (un nombre propio raro del capítulo vale) y vuelve a *poverty*.
>
> Y si alguna vez sale el aviso de **«no estoy seguro de que sea esta
> acepción», dilo en voz alta**: que el modelo avise de que no está seguro
> es de lo mejor que tiene esta aplicación, y es el mismo criterio que la
> banda en vez del decimal.
>
> **La frase del paso Cinco la trae la app** («Una frase de mi libro» en
> *Pronunciar*), así que es del capítulo abierto. La corrección depende de lo
> que se entienda: si la lees perfecta, dirá que se entendió todo y no habrá
> sonido que señalar. Si lees alguna palabra mal a propósito para que salga,
> dilo («la digo mal a propósito»). El botón del sonido **suena** (audio
> pregrabado, sin coste) y «Ver cómo se mueve la boca» abre **primero el
> sonido y después la palabra entera**, animados. Con «Reducir movimiento»
> del sistema salen quietos: tenlo apagado al grabar. Y la boca en 3D, de
> lejos (ver *Preparación de la toma*).
>
> **Planos de pantalla que hacen falta**, en el orden del guion. Son la
> referencia de lo que tiene que verse en cada paso y el plan B si algo
> falla en directo; todos a 390 px de ancho, con perfil 1,20 puesto:
>
> - [CAPTURA: inicio del front en el móvil, con la navegación Leer ·
>   Encontrar · Pronunciar · Tu nivel]
> - [CAPTURA: Ajustes → Tu perfil, formulario Usuario y Contraseña con el
>   botón «Entrar», sin nada escrito]
> - [CAPTURA: Tu nivel, resultado «1,20 de 2 · intermedio» con la escala
>   y la franja de lecturas recomendadas]
> - [CAPTURA: Tu nivel → «Afinar»: «Mídeme con un texto» y «Mídeme con un
>   libro que ya leí»]
> - [CAPTURA: Encontrar con «dostoyevski» escrito y la lista de resultados
>   con el nivel al lado de cada libro, *Crime and Punishment* visible]
> - [CAPTURA: ficha de *Crime and Punishment*: 203.415 palabras, diálogo,
>   vocabulario y la curva medida con la media 1,70 y la línea «tu nivel»]
> - [CAPTURA: lector con la hoja de *poverty*: fonética con audio, «En
>   español» y «Aquí significa»]
> - [CAPTURA: hoja de una palabra que el diccionario no trae, con la marca
>   «IA» en la definición]
> - [CAPTURA: Pronunciar, con la frase del libro escrita y la barra de
>   acción fija abajo: micrófono en el centro y «Corrígeme»]
> - [CAPTURA: la corrección palabra por palabra, el sonido que falla con su
>   botón de audio y «Cómo colocar la boca»]
> - [CAPTURA: «Ver cómo se mueve la boca» abierto: el corte del sonido y
>   el de la palabra entera]
> - [CAPTURA: Mis palabras, con la lista de palabras consultadas y su
>   frase, y «Repasa cinco»]
> - [CAPTURA: para el cierre, la dirección del front grande sobre la
>   portada: `mikemaki1763-literalevel-front.static.hf.space`]

«Esto es LiteraLevel, en el móvil. Este front lo pidió el profesor en la
revisión.

**Uno.** Mido mi nivel con unas preguntas y tres fragmentos reales, o con un texto mío.
Para este ejemplo, un perfil preparado: **1,20 sobre 2**. *(mostrar el resultado)*

**Dos.** Describo en español lo que me apetece leer y busca por significado,
**con mi nivel al lado de cada libro**. Escribo *dostoyevski*, y lo encuentra.

**Tres.** Abro *Crimen y castigo*: **203.415 palabras**, cuánto es diálogo, qué se repite. Y la curva: **la
dificultad capítulo a capítulo**. Media **1,70**. Mi perfil es 1,20: me queda
por encima, y lo sé antes de la primera página.

**Cuatro.** *(tocar* poverty*)* Toco una palabra y en **40 milisegundos**
tengo el diccionario y la fonética. Unos segundos después llega lo que pone
la IA: la traducción y qué significa **en esta frase**. Y si el diccionario no la
trae, la define un modelo y lo marca: **IA**.

**Cinco.** *(leer la frase y pulsar Corrígeme)* Leo en voz alta y pulso
*Corrígeme*: me marca lo que se entendió, me señala **el
sonido** que falla, lo oigo bien dicho y veo **cómo se mueve la boca**.
*(abrir Ver cómo se mueve la boca)*

**Seis.** Lo que consulto se queda en **Mis palabras**, con su frase, para
repasar.»

> **En pantalla, al terminar la demo:** las métricas desnudas.
> **distilroberta-base** · Spearman **0,908** interno · orden MCER
> estrictamente creciente en textos externos · escala pública 0–2.

«Detrás, un distilroberta afinado: Spearman de 0,908 en
validación interna, y en textos externos con nivel oficial, el orden de A1 a
C1 sale estrictamente creciente.

Y lo digo con todas las letras: **no certificamos ningún nivel del MCER**.
Sirve para elegir qué leer, no para acreditar nada.»

---

## V — VISUALIZACIÓN · 3:35 – 4:15

> **En pantalla:** el catálogo. **53.179** libros de Project Gutenberg y
> **585.111** capítulos, y debajo: *medidos enteros por el modelo*.

«Ahora imagina esto a escala.

Hemos medido **53.179 libros** de Project Gutenberg enteros, capítulo a
capítulo: **585.111 capítulos**.

Y eso permite algo que una etiqueta por libro no puede: si un libro te queda
grande, la aplicación te dice **qué capítulos sí están a tu nivel**.

Para el lector eso significa empezar el libro que le toca, entender lo que
lee, **y seguir**.»

---

## A — ACCIÓN · 4:15 – 4:40

> **En pantalla:** el enlace del front, grande:
> `mikemaki1763-literalevel-front.static.hf.space`. Y debajo, pequeño: el
> repositorio y el motor (`huggingface.co/spaces/MikeMaki1763/literalevel`).

«LiteraLevel funciona ahora mismo, no es una maqueta. Este es el enlace; se
abre en el móvil.

Si hablas español y alguna vez abandonaste un libro en inglés pensando que el
problema eras tú —no lo eras. Era el libro.

Pruébalo.»

> *Mantener la mirada un segundo después de la última palabra. No cortar en
> seco: el corte inmediato después de hablar es lo que hace que un vídeo
> parezca casero.*

---

## Comprobación antes de grabar

| | |
|---|---|
| ¿El ensayo completo baja de 4:40? | cronometrarlo; si pasa, recortar acciones |
| ¿Se te ve la cara **todo** el rato? | requisito explícito de la rúbrica |
| ¿Es MP4, y dura menos de 5:00? | reproducirlo entero antes de entregar |
| ¿Se oye el audio de la app en la demo? | comprobar niveles en OBS |
| ¿Funciona el micrófono para la parte de pronunciación? | **hace falta un headset** |
| ¿El enlace del final está vivo? | pegarlo en el móvil y abrirlo |
| ¿El motor está despierto y has entrado? | abrir *Ajustes → Tu perfil* fuera de plano y consultar una palabra antes de grabar |
| ¿No se ve nada privado? | ni contraseña, ni identificador de lector, ni consola, ni claves |
| ¿Hay respaldo grabado? | si se usa, rotulado como **grabación previa** |
| ¿Lo que dices coincide con lo que se ve? | perfil, media de la ficha y palabra, iguales en pantalla |
| ¿«Reducir movimiento» está apagado en el sistema? | si no, la boca sale quieta |

## Lo que este guion NO hace, a propósito

- **No explica cómo funciona el modelo por dentro.** Eso es el documento y el
  notebook. Un vídeo de cinco minutos que explica arquitecturas no vende nada.
- **No pide disculpas por lo que falta.** Las limitaciones van en el documento,
  donde se leen con calma; en el vídeo restan y no suman.
- **No abre con «Hola, soy Miguel y les voy a presentar…».** Esa frase gasta
  ocho segundos de los primeros diez, que son los que deciden si te siguen
  escuchando.
