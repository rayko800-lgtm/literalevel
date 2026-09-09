# Guion del vídeo — LiteraLevel (Módulo 5)

**Formato exigido:** MP4, **máximo 5 minutos**, Miguel **hablando a cámara todo el
tiempo** con las diapositivas de fondo. Vale 20 de los 110 puntos.
Recomendación del profesor: grabar con **OBS**.

**Duración objetivo: 4:40.** Los cinco minutos son un tope, no una meta, y pasarse
es el único error irrecuperable de este entregable.

**El texto hablado son 553 palabras —las que van entre comillas angulares, que es lo que se dice en voz alta— y son 3:41 a 150 palabras por minuto.** El minuto largo que
sobra no es un descuido, es el presupuesto para lo que la demo tarda *de verdad*
— esperar a que salga el nivel, a que responda la búsqueda, que suene el audio,
leer la frase en voz alta. Si al ensayar te sale muy corto, no metas más texto:
ve más despacio y deja respirar las pausas.

---

## Por qué está construido así

Sobre el método **ANSVA** de Fernando Miralles, que es la secuencia clásica de
persuasión: **A**tención · **N**ecesidad · **S**atisfacción · **V**isualización ·
**A**cción. No es un adorno: encaja con lo que la rúbrica del módulo 5 premia,
porque el módulo declara que lo que evalúa es *«hacer que esos modelos sean
accesibles y valiosos para un usuario final»*. ANSVA obliga a hablar del usuario
antes que del modelo, que es exactamente el orden que pide Barranco.

> **Nota honesta sobre las fuentes.** ANSVA está verificado y es suyo. Miralles
> enseña además una *«estructura de la sardina»* de la que encontré el nombre
> pero **no su anatomía exacta** en fuentes públicas — está en su libro y su
> curso. No se ha usado, para no inventarla.

Y se cruza con la plantilla de la **presentación modelo del propio profesor**
(`Ejemplopresentacindehallazgos.pdf`): cifras grandes y desnudas en vez de
párrafos, objetivos numerados, métricas sin adornos, y sobre todo su
**«Ejemplo de uso y aplicación»** — tomar *un* caso real y recorrerlo paso a
paso. En su proyecto de Yelp ese recorrido es el corazón de la presentación.
Aquí el caso real es **un libro concreto y una palabra concreta**.

---

## Consejos de entrega, en tres líneas

- **Mira a la cámara, no a la pantalla.** Es lo que la rúbrica exige y lo que
  más se nota. Pon la ventana de OBS justo debajo del objetivo.
- **Las pausas no son huecos, son puntuación.** Después de cada cifra grande,
  callarse un segundo. El silencio es lo que hace que un número suene grande.
- **Ensáyalo dos veces con cronómetro y una tercera grabando.** Nunca a la
  primera: el primer intento siempre sale a 6 minutos.

---

# EL GUION

## A — ATENCIÓN · 0:00 – 0:35

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

## N — NECESIDAD · 0:35 – 1:15

> **En pantalla:** tres cifras grandes, una por línea. Nada más.
> **1.500 millones** de personas estudian inglés · **la lectura extensiva**
> es el método con más respaldo · **0 herramientas** te dicen si *ese* libro
> es para ti.

«La investigación sobre adquisición de segundas lenguas es bastante clara: leer
mucho y a un nivel ligeramente por encima del tuyo es de lo que mejor funciona.

El problema no es encontrar libros. Hay decenas de miles gratis en dominio
público. El problema es **saber cuál**.

Las etiquetas que existen —A1, B2, C1— casi nunca están puestas por nadie que
haya leído el libro. Y un libro no tiene una sola dificultad: cambia de
capítulo a capítulo.»

---

## S — SATISFACCIÓN · 1:15 – 3:20

> **En pantalla:** compartir pantalla y **usar la aplicación de verdad**.
> Nada de capturas. Que se vea el cursor moverse.

«Esto es LiteraLevel.

**Uno.** Contesto seis preguntas sobre cómo leo y leo tres fragmentos reales.
En segundos tengo mi nivel. *(mostrar el resultado)*

**Dos.** Le describo en español lo que me apetece leer —*una novela de
detectives victoriana*— y me busca entre los libros que **puedo** leer.
No busca por título: busca por significado.

**Tres.** Abro el libro y aparece su ficha. Cuánto tardo en leerlo *a la
velocidad que le toca a mi nivel*, cuánto es diálogo, qué palabras se repiten. Y esta curva: **la
dificultad capítulo a capítulo**, medida por el modelo leyendo el libro
entero. Aquí se ve que arranca duro y se suelta.

**Cuatro.** *(doble clic en una palabra)* Toco una palabra y me da su
significado **en esta frase**, no en abstracto: la definición del
diccionario, la gramática, la fonética británica y americana, y el audio.

**Cinco.** *(leer una frase en voz alta al micrófono)* Y leo en voz alta. Me
marca en verde lo que sonó bien y en rojo lo que no, palabra por palabra.»

> **En pantalla, al terminar la demo:** las métricas desnudas.
> **distilroberta-base** · Spearman **0,908** interno · orden MCER
> estrictamente creciente en textos externos · escala pública 0–2.

«El modelo es un distilroberta afinado en regresión. Spearman de 0,908 en
validación interna. Y aparte, sobre textos externos con nivel oficial del Marco
Común Europeo, el orden de A1 a C1 sale estrictamente creciente. Lo digo
separado porque son corpus distintos.

Y algo que quiero decir con todas las letras: **no certificamos ningún nivel
del MCER**. La letra que enseñamos es la etiqueta más cercana en una escala
continua. Sirve para elegir qué leer, no para acreditar nada.»

---

## V — VISUALIZACIÓN · 3:20 – 4:10

> **En pantalla:** el catálogo. **61.642** libros en inglés de Project
> Gutenberg, y debajo: *medición en curso; lo que no está medido, se mide al
> abrirlo*.

«Ahora imagina esto a escala.

Project Gutenberg tiene **61.642 libros en inglés** en dominio público, y los
estamos midiendo todos con el modelo leyendo cada libro completo. No una
muestra: el libro entero.

Y seré honesto: la medición está en curso. Lo ya medido se abre al instante; lo
demás lo mide la aplicación al abrirlo. La diferencia es de espera, no de
resultado.

Para el lector eso significa una cosa muy concreta: **deja de abandonar
libros**. Empieza el que le toca, entiende lo que lee, y sigue.»

---

## A — ACCIÓN · 4:10 – 4:40

> **En pantalla:** el enlace de la aplicación, grande. Y debajo, pequeño:
> el repositorio.

«LiteraLevel está funcionando ahora mismo, no es una maqueta. Este es el
enlace; se abre en el móvil y funciona.

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
| ¿Dura menos de 5:00? | cronometrar el ensayo |
| ¿Se te ve la cara **todo** el rato? | requisito explícito de la rúbrica |
| ¿Es MP4? | requisito explícito |
| ¿Se oye el audio de la app en la demo? | comprobar niveles en OBS |
| ¿Funciona el micrófono para la parte de pronunciación? | **hace falta un headset** |
| ¿El enlace del final está vivo? | pegarlo en el móvil y abrirlo |

## Lo que este guion NO hace, a propósito

- **No explica cómo funciona el modelo por dentro.** Eso es el documento y el
  notebook. Un vídeo de cinco minutos que explica arquitecturas no vende nada.
- **No pide disculpas por lo que falta.** Las limitaciones van en el documento,
  donde se leen con calma; en el vídeo restan y no suman.
- **No abre con «Hola, soy Miguel y les voy a presentar…».** Esa frase gasta
  ocho segundos de los primeros diez, que son los que deciden si te siguen
  escuchando.
