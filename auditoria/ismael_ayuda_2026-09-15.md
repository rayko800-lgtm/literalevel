# «Le falta hacerla más intuitiva»: dónde se pierde alguien que abre la app por primera vez

- **Quién:** entrega-e6 (811c22), por encargo de la Central. Solo análisis: no se tocó código.
- **Por qué:** Ismael, hermano de Miguel, probó la app el 14 y el 15 de septiembre. Nota de voz literal: «cuesta un poquito entenderle… le falta hacerla más intuitiva, o a lo mejor unos cuadros de diálogo que te diga qué hace cada cosa». Esmeralda dio la misma señal con otras palabras (`auditoria/esmeralda_ux_2026-09-15.md`).
- **Sobre qué:** el front publicado `bdfa418` con la API `74f1484`.
- **Cómo:** Chrome a 390 × 844 táctil, en un contexto aislado sin datos previos y **sin cuenta**, como alguien a quien nadie le explicó nada. Recorrí Inicio, Leer, Encontrar, Pronunciar, Tu nivel, Ajustes y Mis palabras, en ese orden, tocando lo que tocaría una persona curiosa. Al acabar, la pestaña quedó cerrada.
- **Límite:** es mi lectura de la pantalla, no la de Ismael. No sé en qué pantallas se atoró él. Conviene preguntárselo en una línea antes de programar.

## 1. Dónde no se sabe qué hacer ni para qué sirve algo

Gravedad para quien llega nuevo: **alta** = probablemente se rinde o no encuentra la función; **media** = duda, pero sigue; **baja** = detalle.

| # | Pantalla y momento | Lo que se ve | Por qué confunde | Gravedad |
|---|---|---|---|---|
| 1 | **Pronunciar → «Entrar»** del aviso ámbar | Se abre *Ajustes* por arriba: Colores, Color del libro, Tamaño de letra… «Tu perfil» queda a 890 px, **fuera de la pantalla** (el panel acaba en 844), y el cursor no va a «Usuario». | Pulsas «Entrar» y sale un panel de colores. Nada indica que hay que bajar cinco secciones. Es el camino para usar la parte de pago. | **alta** |
| 2 | **Todas las pantallas:** el icono de arriba a la derecha | Un icono de controles deslizantes, sin texto. Solo su `aria-label` dice «Ajustes: colores, letra y perfil». | Ahí es donde se entra con usuario, y no hay forma de adivinarlo. | **alta** |
| 3 | **Pronunciar**, al llegar | «La corrección usa OpenAI, así que necesita que entres con tu perfil. Entrar», en ámbar, encima de todo. | Parece que sin cuenta no sirve la pantalla. No dice lo que **sí** funciona sin entrar: grabarte, escucharte y la tabla de sonidos con la boca. La tabla queda debajo de la barra del micrófono y se llama «(AFI)», una sigla que no se explica. | **alta** |
| 4 | **Leer**, primera vez en un libro | Arriba, la barra general y la del libro («Índice» y dos iconos). Luego «CAPÍTULO 2 DE 13» sobre «CHAPTER I», «¿Cómo de difícil es?», el aviso «Toca dos veces una palabra…» y el aviso «Desliza o toca el borde derecho…». Abajo, la barra de páginas y la barra principal. El texto del libro ocupa un tercio de la pantalla. | Dos avisos a la vez, más cuatro franjas de controles. Lo importante, **mantener presionada una palabra**, compite con todo lo demás. | media |
| 5 | **Leer → «¿Cómo de difícil es?»** | «Midiendo… hasta un minuto», y después «Este capítulo: 1,54 · C1». | Sin nivel medido, «1,54» no dice nada: ni sobre cuánto es la escala ni si es mucho para ti. Tampoco dice antes para qué sirve medir. | media |
| 6 | **Leer:** iconos «≣» y «Aa» | Sin texto. Son «Leer seguido, desplazando» y «Tamaño de letra y colores». | «≣» no se entiende; «Aa» se adivina. | baja |
| 7 | **Leer:** «CAPÍTULO 2 DE 13» sobre «CHAPTER I» | La portadilla cuenta como capítulo 1. | Los dos números no coinciden y parece un error. | baja |
| 8 | **Encontrar**, antes de buscar | Pestañas «Resultados · A mi nivel · Mis libros», con «Resultados» marcada y vacía. | «Mis libros» es donde están los que empezaste **y** donde se sube un libro propio: el nombre no lo sugiere. «A mi nivel» sin nivel lleva a «Primero, tu nivel». | media |
| 9 | **Inicio → tarjeta «Mídeme»** | «Seis preguntas cortas, una por pantalla. Desde la primera ya ves una estimación.» | **Ya no es verdad:** desde la pantalla A de *Tu nivel* no hay estimación hasta la sexta. Promete algo que no pasa. | media (texto que contradice la app) |
| 10 | **Mis palabras** | No está en la barra de abajo. Se llega desde *Inicio* («palabras consultadas», solo si ya consultaste alguna) o desde el resultado de *Tu nivel*. | Quien busca sus palabras no sabe que están dentro de «Tu nivel». | media |
| 11 | **Tu nivel**, pregunta 1 | Antetítulo «Seis preguntas para saber qué libros te van», barra «1 de 6», opciones y «Atrás · Siguiente». | Se entiende. Único roce: la opción avanza sola al tocarla, y aun así hay un botón «Siguiente». | baja |

**Lo que ya funciona y no hay que tocar:**
- *Inicio* con «¿Por dónde empiezas?», que ofrece «Solo quiero mirar», «Mídeme» y «Pregúntame».
- La frase bajo el título de *Encontrar* y los chips «Prueba con».
- «Todavía no estás leyendo nada» en *Leer* vacío.
- El estado vacío de *Mis palabras*.
- El aviso del lector con ✕, que se guarda como visto.

**Sobre el idioma:** Central pidió los textos en español de México. La app hoy usa formas de España: «te apetece», «móvil», «Mídelo». Las propuestas de abajo ya van en español de México. Cambiar los textos que ya existen es otra decisión de Miguel.

## 2. Dos formas de ayuda

### (A) Bienvenida de 4 pasos, la primera vez

Se abre **solo** en la primera visita a *Inicio*, nunca encima de un enlace directo a un libro o al lector. Se puede saltar desde cualquier paso, y se vuelve a ver desde *Ajustes → «Ver la bienvenida otra vez»*. Se guarda como vista en el navegador, igual que los avisos del lector de hoy, así que funciona sin cuenta.

```
┌──────────────────────────────────┐
│ LiteraLevel                Saltar│
│                                  │
│      [ilustración: un libro]     │
│                                  │
│  Libros en inglés a tu nivel     │
│                                  │
│  Medimos qué tan difícil es cada │
│  capítulo para que elijas uno    │
│  que puedas terminar.            │
│                                  │
│            ● ○ ○ ○               │
│  ┌────────────────────────────┐  │
│  │         Siguiente          │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

| Paso | Título | Texto (una o dos frases) | Botones |
|---|---|---|---|
| 1 | Libros en inglés a tu nivel | Medimos qué tan difícil es cada capítulo para que elijas uno que puedas terminar. | Siguiente · Saltar |
| 2 | Una palabra, en su frase | Mientras lees, mantén presionada una palabra: te decimos qué significa **ahí** y cómo se pronuncia. | Siguiente · Saltar |
| 3 | Practica en voz alta | En *Pronunciar* te grabas leyendo una frase y ves qué sonido corregir y cómo se mueve la boca. | Siguiente · Saltar |
| 4 | ¿Por dónde empiezas? | Mide tu nivel con seis preguntas, o ve directo a un libro. Nada de esto pide cuenta. | **Medir mi nivel** · Solo quiero leer |

**A favor:** cuenta el producto entero de una vez, y el paso 4 lleva a una acción.

**En contra:**
- Añade 4 pantallas antes de tocar nada, y la gente suele saltarlas sin leer.
- Repite lo que *Inicio* ya dice con «¿Por dónde empiezas?».
- **No ayuda en el momento de la duda:** los fallos 1, 3, 5 y 8 de la tabla pasan en otras pantallas, días después.

### (B) Una línea de ayuda por pantalla, con «?»

Es el mismo patrón que ya tiene el lector con «Toca dos veces una palabra…»: un aviso de una frase, con ✕, que se guarda como visto. La **primera vez** que entras en cada pantalla sale debajo del título. Después queda un «?» pequeño junto al título que lo vuelve a abrir. No es un diálogo encima de la pantalla, así que no tapa nada ni pide pulsar para seguir.

```
┌──────────────────────────────────┐
│ [L] LiteraLevel          ⚙ Ajustes│
├──────────────────────────────────┤
│ PRONUNCIAR                       │
│ Lee una frase en voz alta    (?) │
│ ┌──────────────────────────────┐ │
│ │ ✦ Escribe o trae una frase,  │ │
│ │   grábate leyéndola y te digo│ │
│ │   qué sonido corregir. Sin   │ │
│ │   entrar puedes grabarte y   │ │
│ │   escucharte.            ✕   │ │
│ └──────────────────────────────┘ │
│ ① La frase     📖 Una frase de…  │
│ ┌──────────────────────────────┐ │
│ │ Escribe o pega la frase…     │ │
│ └──────────────────────────────┘ │
│              ( 🎤 )              │
├──────────────────────────────────┤
│  Leer  Encontrar Pronunciar Nivel│
└──────────────────────────────────┘
```

Tocar «(?)» después vuelve a abrir el mismo recuadro. El ✕ lo cierra y no vuelve a salir solo.

**Textos (español de México):**

| Pantalla | La línea de ayuda |
|---|---|
| Inicio | Abre un libro, busca uno que se te antoje o mide tu nivel: nada de esto pide cuenta. |
| Leer (lector) | Mantén presionada una palabra para ver qué significa en esta frase; desliza para cambiar de página. *(Junta en una sola línea los dos avisos de hoy.)* |
| Leer → «¿Cómo de difícil es?» | Mide este capítulo de 0 a 2: cuanto más alto, más difícil. Si ya mediste tu nivel, te digo si te queda. |
| Encontrar | Escribe en español qué quieres leer. Si ya mediste tu nivel, primero salen los que te quedan. En «Mis libros» están los que empezaste y los que subas. |
| Pronunciar | Escribe o trae una frase, grábate leyéndola y te digo qué sonido corregir. Sin entrar puedes grabarte, escucharte y ver cómo se dice cada sonido. |
| Tu nivel | Seis preguntas para saber qué libros te quedan. No es un examen ni un certificado. |
| Ajustes | Aquí cambias colores y letra; hasta abajo, en «Tu perfil», entras con tu usuario. |
| Mis palabras | *(No hace falta: la pantalla ya explica qué guarda.)* |

**A favor:**
- Aparece **donde y cuando** surge la duda, y no añade ningún paso: quien ya sabe cierra con ✕ o ni lo ve, porque se guarda en el navegador.
- Reutiliza un patrón que la app ya tiene y que las lectoras ya vieron.

**En contra:**
- No cuenta el producto entero de una vez.
- Son 7 textos que mantener.

### Qué no hay que tapar, con cualquiera de las dos

- **El texto del libro ni el panel de la palabra.** En el lector, nada de diálogos: la línea va en el hueco donde hoy están los avisos.
- **La barra de abajo, el botón del micrófono y la barra de páginas:** son lo que se toca con el pulgar.
- **El buscador de *Encontrar* y las opciones de *Tu nivel*.**
- **Los enlaces directos** a un libro o al lector: la bienvenida (A) no sale ahí, y la línea (B) va debajo del título, nunca encima del contenido.

## 2 bis. La segunda nota de Ismael: el micrófono y la saturación

Nota de voz literal: «entré y ya inicié sesión, pero le pisas al micrófono y no te dice que hables, no se activa la grabación… a lo mejor no tan saturada la página, los textos están largos y tienes que hacerle scroll, y te pierdes, no sabes qué hacer». Según Miguel, usó un teléfono **Android** y abrió el enlace que le mandaron **por WhatsApp**.

### El micrófono: era un fallo, ya arreglado y publicado

**Cómo se probó:** en Chrome a 390 táctil sustituí `navigator.mediaDevices` en la página. Primero sobre el front publicado `bdfa418`, y luego sobre el build local del arreglo. En el celular, la barra del micrófono es fija y empieza en y = 687.

**En `bdfa418`, con la frase escrita y la página arriba del todo:**

| Caso | Qué hacía el código | Qué se veía |
|---|---|---|
| Sin `navigator.mediaDevices` (WebView de WhatsApp, http) | «Este navegador no deja grabar audio…» | **Nada.** El aviso se pintaba en y = 750–849, **debajo de la barra fija**. |
| Permiso negado (NotAllowedError; un WebView lo rechaza sin preguntar) | «No tengo permiso… Actívalo en el candado…» | **Nada**, tapado. En un WebView además no hay candado. |
| Sin micrófono (NotFoundError) | El mismo texto de «no tengo permiso» | **Nada**, y el texto era falso. |
| El permiso no contesta | Nada | **Nada**, ni «pidiendo permiso». |
| Concedido, llegue audio o no | «Grabando… 2 s · pulsa para terminar» | El texto, **tapado por la barra**. Solo el micrófono rojo latiendo decía que grababa. **Nunca decía «habla ahora».** |
| Sin frase | Micrófono desactivado | **Un toque no hacía nada.** |

Lo que contó Ismael encaja con los cuatro primeros casos: toca el micrófono y no pasa nada visible.

**El arreglo** (commit `601788b`, publicado en el Space del front `0cfa382`, visto bueno de 4e) pone una línea de estado **dentro de la barra, encima del micrófono**:

| Caso | Lo que dice ahora |
|---|---|
| WebView de Android («; wv)») o sin `mediaDevices`, **antes de pulsar** | «Para grabar tu voz, abre LiteraLevel en Chrome: toca ⋮ y luego «Abrir en Chrome».» (sin WebView: «Este navegador no puede grabar. Abre LiteraLevel en Chrome o Safari.») |
| Esperando el permiso | «Acepta el permiso del micrófono.», y a los 5 s «¿No ves el permiso? Abre LiteraLevel en Chrome o Safari.» |
| Concedido | «Grabando: habla ahora · N s» |
| Permiso negado | «No hay permiso para el micrófono. Actívalo en los ajustes del sitio y vuelve a intentar.» (en un WebView, el texto de Chrome) |
| Sin micrófono | «No encontramos ningún micrófono. Conecta uno y vuelve a intentar.» |
| Micrófono ocupado | «El micrófono está ocupado por otra app. Ciérrala y vuelve a intentar.» |
| Sin frase | «Primero escribe la frase que vas a leer.» |

**Comprobado:**
- **En Chrome a 390:** la línea se ve entera, sin taparse ni solaparse con el micrófono, en todos los estados, y sin animación. Con el user agent del WebView de WhatsApp, el aviso sale antes de pulsar.
- **Pruebas:** 11 casos en `pronunciar.microfono.spec.ts`, más los mutantes.
- **Aparte:** el menor de 4e va en el commit `e3f80e4`, que sale con la próxima publicación del front. Si alguien sale de la pantalla con el permiso pendiente y lo concede después, las pistas se paran al llegar y no se graba.
- **Sin probar:** un Android de verdad dentro de WhatsApp. Eso lo hace Ismael.
- **Límite:** la detección «; wv)» es solo de Android. En el navegador interno de otras apps en iPhone sale el mensaje general.

### La saturación, pantalla por pantalla a 390

**Cómo se midió:** la zona útil es lo que queda entre la barra de arriba y la de abajo, 712 px; en *Pronunciar*, 622 px, por la barra del micrófono. «Palabras antes» cuenta el texto que hay por encima de la primera acción útil. Todo sin cuenta.

| Pantalla | Primera acción útil | ¿Se ve sin scroll? | Pantallas de scroll hasta ella | Palabras antes | Pantallas en total |
|---|---|---|---|---|---|
| Inicio | «Empezar a leer» | sí | 0 | 27 | 3,2 |
| Leer (vacío) | «Abrir Alicia…» | sí | 0 | 18 | 1,2 |
| **Lector, primera vez** | la primera línea del libro | **a medias** | 0 | — | 1,4 |
| Encontrar | el buscador | sí | 0 | 25 | 1,6 |
| Encontrar con resultados | la primera tarjeta | sí (y = 573) | 0 | 39 | 7,5 |
| **Pronunciar** | la caja de la frase | sí (y = 435) | 0 | **46** | 2,0 |
| **Pronunciar: tabla de sonidos** | «Los sonidos del inglés (AFI)» | **no** (debajo de la barra) | 0,1 | 50 | 2,0 |
| Tu nivel, pregunta 1 | la primera opción | sí | 0 | 15 | 1,4 |
| Tu nivel, resultado | «Ver libros de mi nivel» | sí | 0 | 31 | 1,7 |
| Ficha de un libro | «Empezar a leer» | sí | 0 | 19 | 3,4 |
| **Ficha: Índice** | «Índice · 40 capítulos» | **no** | **1,9** | **153** | 3,4 |
| Mis palabras (vacía) | «Ir a leer» | sí | 0 | 38 | 1,2 |
| **Ajustes → Tu perfil** | «Usuario» | **no**, y «Entrar» no baja hasta ahí | 0,3 dentro del panel, detrás de 16 botones | — | 1,9 del panel |

**Lectura:** en casi todas las pantallas la primera acción se ve sin scroll. La sensación de «saturada» viene de **cuatro sitios**:

1. **El lector la primera vez.** Arriba van la barra y la del libro; luego «CAPÍTULO 2 DE 13», «CHAPTER I», «12 min · 2.184 palabras», «¿Cómo de difícil es?» y el aviso de la palabra; abajo, el aviso de pasar página, la barra de páginas y la barra principal. En la captura, **el texto del libro deja ver unas dos líneas** (de y ≈ 427 a 498) antes del segundo aviso.
2. ***Pronunciar*.** 46 palabras (subtítulo de 19 y aviso ámbar) antes de la caja de la frase, y la tabla de sonidos queda justo debajo de la barra del micrófono.
3. **La ficha de un libro.** El índice queda a casi dos pantallas, detrás de la curva, «Cómo es de leer» y «¿De qué trata?»: 153 palabras.
4. ***Ajustes*.** «Tu perfil» es la sexta sección.

### Qué se acorta o se pliega, con A y con B

Vale con cualquiera de las dos propuestas. Con (B), **la línea de ayuda sustituye al subtítulo largo, no se suma**: el total de palabras baja.

| Pantalla | Hoy | Propuesta (español de México) |
|---|---|---|
| Lector, primera vez | Dos avisos a la vez (palabra y páginas) | **Uno solo:** «Mantén presionada una palabra para ver qué significa; desliza para cambiar de página.» «¿Cómo de difícil es?» y «12 min · 2.184 palabras» pasan al Índice o a la ficha. |
| Pronunciar | Subtítulo de 19 palabras y aviso ámbar de 12 | Subtítulo: «Graba una frase y te digo qué corregir.» Aviso: «Para corregirte necesitas entrar; sin entrar puedes grabarte y escucharte.» La tabla, como enlace pequeño arriba: «Ver los sonidos del inglés». |
| Inicio | «Cómo funciona» (3 bloques) repite las tarjetas de «¿Por dónde empiezas?» | Quitar «Cómo funciona» o plegarlo. Tarjetas de 8 palabras como máximo, sin «Desde la primera ya ves una estimación». |
| Ficha de libro | Índice a 1,9 pantallas | Un «Elegir capítulo» junto a «Empezar a leer». «Cómo es de leer» plegado, como ya está «¿Qué significa cada nivel?». |
| Encontrar | Subtítulo de 22 palabras; pestaña «Mis libros» | «Escribe en español qué quieres leer.» La pestaña, «Mis libros y subir». |
| Ajustes | «Tu perfil» al final | Sin sesión, «Tu perfil» arriba; y «Entrar», desde cualquier pantalla, lleva ahí con el cursor en «Usuario». |

**(A), la bienvenida, no arregla nada de esto:** es una pantalla más antes de las mismas pantallas. Si Miguel la elige, debería ir junto con estos recortes.

## 3. Recomendación

**Recomiendo (B)**, más tres arreglos que no son ayuda sino fallos y valen con cualquiera de las dos:

1. **«Entrar» debe llevar a «Tu perfil».** Hoy abre *Ajustes* por arriba y el formulario queda fuera de la pantalla (fallo 1). Basta con desplazar el panel hasta esa sección y poner el cursor en «Usuario». Es el que más probablemente hizo rendirse a alguien.
2. **El icono de *Ajustes* con texto** («Ajustes», o un «Entrar» visible cuando no hay sesión) (fallo 2).
3. **Corregir la tarjeta «Mídeme» de *Inicio*:** quitar «Desde la primera ya ves una estimación» (fallo 9).

**Por qué (B) y no (A):**
- **No añade pasos a quien ya sabe usarla,** que es el criterio del encargo: (A) pone cuatro pantallas delante; (B), ninguna.
- **Lo que vi pasa en el momento de usar cada pantalla,** no al llegar. *Inicio* ya explica por dónde empezar. Donde falta es en *Pronunciar*, *Leer* y *Encontrar*.
- **Funciona sin cuenta** y cuesta poco: el lector ya tiene el componente y la bandera en el navegador (`literalevel.pista-palabra`).

Si Miguel prefiere (A) por lo que dijo Ismael («unos cuadros de diálogo»), yo la haría **de 3 pasos**, sin el de pronunciar, y **sin quitar (B) en *Pronunciar* y en el lector**, que es donde la bienvenida no llega.

Además, los recortes de la tabla «Qué se acorta o se pliega» (2 bis). Por lo que dijo Ismael, lo más urgente después del micrófono es **el lector la primera vez** (un solo aviso) y ***Pronunciar*** (subtítulo y aviso más cortos).

## Lo que decide Miguel

1. (A), (B) o las dos.
2. Si los tres arreglos (Entrar → Tu perfil, texto en el icono de Ajustes, tarjeta «Mídeme») van ya, aparte de la ayuda.
3. Qué recortes de 2 bis se hacen, y en qué orden.
4. Si los textos de la app pasan a español de México, o solo los nuevos.
5. Si le pregunta a Ismael, cuando pruebe el micrófono arreglado, en qué otra pantalla se atoró, para confirmar que es la misma que señala este informe.
