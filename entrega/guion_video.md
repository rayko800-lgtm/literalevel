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
- **El motor, despierto.** El Space de la API se suspende a las 48 h exactas sin
  visitas: abre la aplicación **la víspera** y, **diez minutos antes de grabar**,
  comprueba que `/api/salud` diga `"buscador_listo": true`. Si no lo dice, espera
  con esa pestaña abierta de uno a minuto y medio, sin recargar en bucle; si a
  los dos minutos no responde, abre la página del Space y mira si pone `Error`.
  La primera búsqueda tras el arranque va más lenta y la siguiente responde en
  unos 0,3 s. El front es estático y se pinta en 0,64 s, pero lo demás espera a
  la API. Las cifras son de arranques por despliegue, no de un despertar desde
  la suspensión, que no se ha medido
  (`auditoria/ronda4_arranque_demo_f4_2026-09-16.md`).
- **Las correcciones, contadas.** «Corrígeme» tiene 10 por hora, por conexión y no
  por cuenta: si ensayas en ráfaga desde la misma red en la hora antes de grabar, te
  quedas sin ellas para la toma. El aviso dice cuándo vuelve la primera, no todas.
- **La boca en 3D.** El front publicado —revisión `f4920fa` del Space, del commit `a656c2e`— lleva la
  cabeza de MakeHuman y la lengua corregida de la rama `boca3d` (75f334a está en
  `master`): comprobado hoy, `boca3d/cara.glb` y `boca3d/lengua.glb` responden
  200 en el Space publicado. **Ábrela una vez antes de grabar**: la cara
  tarda unos 3–4 s la primera vez (depende de la red; medido el 15 de
  septiembre) y menos de 1 s después. Si no carga, basta el corte 2D.
- **El perfil 1,20, receta** (medida por e6 contra el Space y por 4e con la
  fórmula, 15 de septiembre): en *Tu nivel*, «Varias veces por semana» →
  fragmento fácil «Lo entiendo con naturalidad, sin necesidad de releer» → «Sí,
  una novela actual» → fragmento medio «Lo entiendo con naturalidad, sin
  necesidad de releer» → «Los hechos o argumentos principales» → fragmento
  difícil «Entiendo algunas partes, pero necesitaría el diccionario para
  seguirlo». Se guarda solo al contestar la sexta. El titular dirá «Lees en
  inglés a nivel B2», y el 1,20 está en «Ver el detalle». En la sexta no elijas
  «Capto bien la idea»: da 1,46, que es C1.
- **La primera vez salen tres ayudas.** En un navegador limpio, al abrir Inicio
  sale la bienvenida («1 de 4» y, debajo, «¿Ya tienes cuenta?»): pulsa «Saltar»,
  arriba a la derecha de la tarjeta, antes de grabar; al entrar con tu cuenta sale
  una vez más, con lo que gasta usos, y se salta igual. Al abrir el lector sale
  arriba «Mantén presionada una palabra para ver qué significa; desliza para
  cambiar de página.», y en *Pronunciar*, en lugar del subtítulo, «Escribe o trae
  una frase, grábate leyéndola y te digo qué sonido corregir…». Ciérralas con ✕
  antes de grabar (vuelven con «?»).

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
> es de los métodos con más respaldo · **68.546** libros y textos gratis, medidos.

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
> ve**. Y el libro **se abre desde el buscador**: escribe «Crimen y castigo de
> Dostoyevski» en *Encontrar* y sale.
>
> **El libro del recorrido tiene que ser uno que el buscador devuelva.** Si
> hay que subirlo a mano, el paso Dos deja de ser cierto delante de cámara.
>
> **Entra antes de grabar, y úsala.** Entrar es *Ajustes → Tu perfil*
> (usuario y contraseña), fuera de plano: sin entrar, la explicación en
> contexto y la corrección de pronunciación no salen, porque son lo que cuesta
> dinero. Y tres cosas de la primera vez, medidas el 11 de septiembre de 2026 (la
> primera, otra vez el 15, en el ensayo de e6):
>
> - La **primera consulta léxica tarda unos 1,0 s** —el panel a 0,47 s, y la IPA
>   y el diccionario a 1,02 s—, medido el 16 de septiembre sobre la revisión
>   `f4920fa` del Space, del commit `a656c2e`. Las cifras viejas eran de cuando el
>   servidor cargaba en frío el diccionario de 243 MB, spaCy y el modelo de
>   similitud: 3,8 s el 15 de septiembre y unos 55 s el 11. **En caliente se ven
>   0,3–0,4 s**, y a cámara dices «al instante».
>   **La traducción y el «Aquí significa» salen de la IA** y llegan unos
>   segundos después, en la segunda etapa de la hoja: no los atribuyas al
>   diccionario. Eso es lo único que puede tardar aquí, **pide cuenta y sigue sin
>   medirse**; la consulta en sí ya no hay que calentarla. Si el motor llevaba horas sin
>   visitas, la primera llamada tarda además medio minuto en despertarlo; el
>   front lo dice en pantalla. Despiértalo antes.
> - **Calcula la curva del libro antes.** Queda guardada, así que en la
>   toma sale en segundos en vez de en dos minutos de silencio. Y hasta
>   que no está calculada, la ficha no sabe si el libro te queda por
>   encima y te da el rango en vez del dato.
> - **Con tu perfil puesto, *Crime and Punishment* sale el primero y en el
>   bloque de otros niveles.** Todo Dostoievski queda a más de 0,45 de un
>   perfil de 1,20, así que *Encontrar* enseña primero el aviso «De «Crimen y
>   castigo de Dostoyevski» no hay libros en tu nivel ni un poco por encima
>   entre los resultados. Estos son los de otros niveles.» y debajo, en **De
>   otros niveles**, **el nuestro, primero**, y detrás *Best Russian Short
>   Stories* y *The Brothers Karamazov* (ensayo del 15 de septiembre de 2026
>   sobre los reinicios 28 y 30b, a 390 px: el libro a 679 px, sin pulsar nada). El aviso es lo esperado: no lo leas
>   como un fallo. Sin perfil también sale el primero; con un perfil de 1,34
>   pasa a «Un poco por encima», segundo. **No escribas solo «dostoyevski»**:
>   con el perfil de 1,20, «En tu nivel» se llena de cuentos que no son suyos y
>   el libro queda detrás de «Ver también». Está en la lista y se abre bien;
>   **elígelo sin dudar**, que dudar delante de la cámara parece que la app no
>   lo encuentra.
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
> Afinar con un texto, que nombras, y con un libro que ya leíste están al
> final del resultado de *Tu nivel*, en «¿No te convence? Afínalo con un libro
> que ya leíste · con un texto»: no las hagas en directo, que el libro tarda en
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
> the payment of his brother's debts»*, y encima es el tema del libro. Está en
> **«Antes del primer capítulo»**: ábrelo desde el Índice, porque «Empezar a
> leer» lleva al capítulo 2. En la ficha, el Índice queda unas 2 pantallas
> más abajo; o usa «Índice» arriba del lector. Si
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
> *Pronunciar*), así que es del capítulo abierto. Ese botón **solo aparece si
> vienes de un libro**: en *Pronunciar* en frío no está, y hay que escribir la
> frase a mano. La corrección depende de lo
> que se entienda: si la lees perfecta, dirá que se entendió todo y no habrá
> sonido que señalar. Si lees alguna palabra mal a propósito para que salga,
> dilo («la digo mal a propósito»). El botón del sonido **suena** (audio
> pregrabado, sin coste) y «Cómo se mueve la boca», abierto ya en la primera
> palabra a practicar, enseña **primero el sonido y después la palabra
> entera**, animados. Con «Reducir movimiento»
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
> - [CAPTURA: Tu nivel, resultado «Lees en inglés a nivel B2» con la barra
>   A1–C2 y «Ver el detalle» abierto: «1,20 de 2 · Intermedio» y la franja]
> - [CAPTURA: el pie del resultado de Tu nivel: «¿No te convence? Afínalo con
>   un libro que ya leíste · con un texto · volver a medirme»]
> - [CAPTURA: Encontrar con «Crimen y castigo de Dostoyevski» escrito, el
>   aviso de otros niveles y *Crime and Punishment* el primero, con su nivel al
>   lado]
> - [CAPTURA: ficha de *Crime and Punishment*: 203.415 palabras, diálogo,
>   vocabulario y la curva medida con la media 1,70 y la línea «tu nivel»]
> - [CAPTURA: lector con la hoja de *poverty*: fonética británica y
>   americana, el botón de la voz del navegador («Sin grabación para esta
>   palabra»), «En español» y «Aquí significa»]
> - [CAPTURA: hoja de una palabra que el diccionario no trae, con la marca
>   «IA» en la definición]
> - [CAPTURA: Pronunciar, con la frase del libro escrita y la barra de
>   acción fija abajo: micrófono en el centro y «Corrígeme»]
> - [CAPTURA: la corrección palabra por palabra, el sonido que falla con su
>   botón de audio y «Cómo colocar la boca»]
> - [CAPTURA: «Practica esta palabra» con «Cómo se mueve la boca» abierto:
>   el corte del sonido y el de la palabra entera, con «Escuchar y ver» y
>   «🐢 Despacio»]
> - [CAPTURA: Mis palabras, con la lista de palabras consultadas y su
>   frase, y «Repasa cinco». La tarjeta de *poverty* dice «cap. 1» aunque es
>   del prefacio: no leerlo en voz alta]
> - [CAPTURA: para el cierre, la dirección del front grande sobre la
>   portada: `mikemaki1763-literalevel-front.static.hf.space`]

«Esto es LiteraLevel, en el móvil. Este front lo pidió el profesor en la
revisión.

**Uno.** Mido mi nivel con tres preguntas y tres fragmentos reales, o con un texto mío.
Para este ejemplo, un perfil preparado: **1,20 sobre 2**. *(mostrar el resultado)*

**Dos.** Describo en español lo que me apetece leer y busca por significado,
**con mi nivel al lado de cada libro**. Escribo *Crimen y castigo de Dostoyevski*, y
lo encuentra.

**Tres.** Abro *Crimen y castigo*: **203.415 palabras**, cuánto es diálogo, qué se repite. Y la curva: **la
dificultad capítulo a capítulo**. Media **1,70**. Mi perfil es 1,20: me queda
por encima, y lo sé antes de la primera página.

**Cuatro.** *(mantener presionada* poverty*)* Mantengo el dedo sobre una palabra y **al instante**
tengo el diccionario y la fonética. Unos segundos después llega lo que pone
la IA: la traducción y qué significa **en esta frase**. Y si el diccionario no la
trae, la define un modelo y lo marca: **IA**.

**Cinco.** *(leer la frase y pulsar Corrígeme)* Leo en voz alta y pulso
*Corrígeme*: me marca lo que se entendió, me señala **el
sonido** que falla, lo oigo bien dicho y veo **cómo se mueve la boca**.
*(pulsar Escuchar y ver en Practica esta palabra)*

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
| ¿El motor está despierto y has entrado? | abrir *Ajustes → Tu perfil* fuera de plano; lo que se calienta es el buscador con una búsqueda, no la palabra |
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
