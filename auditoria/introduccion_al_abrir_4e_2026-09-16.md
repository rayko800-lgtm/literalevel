# Una introducción al abrir la aplicación: propuesta (4e, 16 sep 2026)

- **Quién la pide:** Miguel, tras probar la app. Encargo de la Central a 4e.
- **Qué es esto:** un diseño de textos y de orden, **sin programar nada**. No se ha tocado
  `front/`, que es de e6. Decide la Central con Miguel.
- **Sobre qué está escrito:** el front publicado hoy, revisión `f4920fa` del Space, del commit
  `a656c2e`. Los textos que se citan son los que sirve esa revisión, leídos del código, no de
  memoria.

## 0. Lo decidido (Central, 16 de septiembre)

Esto ya no es una propuesta: la Central decidió con este informe delante.

1. **El paso 0 entra antes del 20**, en la versión mínima de la sección 5: dentro de la bienvenida
   que ya existe, «Entrar» y «Seguir sin cuenta» del mismo tamaño, «Saltar» intacto, «Entrar» al
   destino de hoy, y diciendo lo que **sí** se puede sin cuenta. Lo programa e6 cuando termine la
   boca 3D y el scroll, que van antes.
2. **«Cómo funciona» no se toca ahora**, y cuando se toque **se pliega, no se quita**. A la cola de
   después de la entrega.
3. **La introducción sale también la primera vez que alguien entra con cuenta**, una sola vez y con
   «Saltar»: quien entra con cuenta es justo quien va a usar la corrección, que es lo que más se
   malentiende.
4. **Los textos nuevos van en español de México**, como el resto de la aplicación.
5. **Quedan descartados** el tour encadenado de globos y los pop-ups que tapen contenido, por los
   motivos de la sección 6.

Lo único que queda por hacer de 4e son las tres líneas de guion que describen la tarjeta como de
tres pasos, **cuando e6 publique y no antes**: escritas hoy, describirían una pantalla que todavía
no existe.

## 1. Lo que pidió Miguel, y lo que ya existe

Pidió cuatro cosas: que la interfaz tiene **demasiada información** y se pierde; una
**introducción al abrir** que pregunte **si ya tienes cuenta** y vaya guiando por las funciones,
como el arranque de una cuenta de Google; la interfaz final **limpia y sin mucho texto**; y
acepta que la ayuda salga en **pop-ups**.

Hoy ya hay tres capas de ayuda, todas de e6 y todas publicadas:

| Capa | Qué es | Dónde |
|---|---|---|
| Bienvenida | Tarjeta de **tres pasos** la primera vez, solo en Inicio, con «Saltar» y recuperable en *Ajustes* → «Ver la bienvenida otra vez» | `compartido/bienvenida.ts` |
| Línea de ayuda | Una frase bajo el título la primera vez, se cierra con ✕ y vuelve con «?» | `pantallas/pronunciar.html`, `pantallas/lector.html` |
| Avisos en su sitio | El del micrófono dentro de la barra; el de «Corrígeme» sin perfil, con su «Entrar» | `pantallas/pronunciar.*` |

**Lo que Miguel pide no existe todavía es una sola cosa: preguntar por la cuenta.** Ninguna de
las tres capas lo hace. Lo demás que pide —guiar y aligerar— se solapa con lo que ya hay, y esa
es la oportunidad: **la introducción no debe añadirse encima del texto fijo, sino permitir
quitarlo**.

## 2. El diagnóstico, con lo que ya está medido

De los recorridos a 390 px de e6 (`auditoria/ismael_ayuda_2026-09-15.md` y
`auditoria/microfono_casos_a_b_2026-09-16.md`):

- Palabras antes de la primera acción útil: **Inicio 27**, **Encontrar 25**, **Pronunciar 46**,
  y **153** antes del Índice en la ficha de un libro.
- Sin cuenta **sí** funcionan: leer, buscar, medir el nivel, grabarse, escucharse, «Otra vez»,
  los 41 sonidos del AFI, «Escuchar y ver» y la boca 3D.
- Sin cuenta **no**: la corrección de pronunciación y la explicación de una palabra en su frase.
  Eso es lo que hay que saber decir en una frase, y hoy no se dice hasta que chocas con ello.

**La consecuencia de diseño:** la pregunta por la cuenta no es burocracia, es la que ordena la
primera visita. Quien entra ve una app completa; quien no, ve una app que hace casi todo y tiene
dos cosas cerradas. Decirlo al principio evita el «pulso y no pasa nada» que ya nos costó una
tanda entera.

## 3. Paso 0: «¿Ya tienes cuenta?»

Va **dentro de la bienvenida que ya existe**, como primer paso, no como pantalla aparte. Se
salta igual, se guarda igual y se recupera igual.

```
┌──────────────────────────────────┐
│ LiteraLevel                Saltar│
│                                  │
│  ¿Ya tienes cuenta?              │
│                                  │
│  Con cuenta te corrijo la        │
│  pronunciación y te explico una  │
│  palabra en su frase. Sin        │
│  cuenta puedes leer, buscar,     │
│  medir tu nivel y grabarte.      │
│                                  │
│  ┌────────────────────────────┐  │
│  │          Entrar            │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │    Seguir sin cuenta       │  │
│  └────────────────────────────┘  │
│            ● ○ ○ ○               │
└──────────────────────────────────┘
```

**Texto, 32 palabras contadas:** «¿Ya tienes cuenta? Con cuenta te corrijo la pronunciación y te
explico una palabra en su frase. Sin cuenta puedes leer, buscar, medir tu nivel y grabarte.»

Tres reglas para que no estorbe:

1. **No bloquea.** «Seguir sin cuenta» es un botón igual de grande que «Entrar», y «Saltar» sigue
   arriba a la derecha. Nadie queda atrapado en la puerta.
2. **«Entrar» lleva a donde ya lleva hoy:** *Ajustes* → «Tu perfil» con el cursor en «Usuario»
   (`nucleo/sesion.ts`, el mismo destino del «Entrar» del aviso ámbar). No se inventa una pantalla
   de registro.
3. **Se dice lo que se gana, no lo que se pierde.** «Sin cuenta puedes…» y no «sin cuenta no
   puedes…».

## 4. Guiar sin llenar de texto: qué se puede quitar

Este es el punto que Miguel pide de verdad —**menos texto fijo, más ayuda cuando hace falta**— y
el único que reduce información en pantalla. Cada fila dice el texto que hay hoy, con su archivo.

| Pantalla | Texto fijo hoy | Si la introducción lo explica | Propuesta |
|---|---|---|---|
| Inicio | Bloque **«Cómo funciona»** con tres apartados: «Sabes cuánto te va a costar», «Lees con red», «Practicas en voz alta» (`pantallas/inicio.ts:115-122`), **76 palabras contadas** | Es **lo mismo** que cuentan los pasos 1-3 de la bienvenida, con otras palabras | **Quitar**, o dejarlo plegado bajo un «Cómo funciona ▸» |
| Inicio | Entradilla «LiteraLevel mide lo difícil que es cada capítulo y te explica cualquier palabra en su frase, sin salir del libro.» (`:23-24`) | El paso 1 de la bienvenida ya lo dice | **Acortar** a media frase, o quitarla si se queda «Cómo funciona» |
| Encontrar | «Descríbelo con tus palabras, en español o en inglés. Si ya sabes tu nivel, primero salen los que te quedan mejor.» (`pantallas/encontrar.ts:23`) | La línea de ayuda con «?» ya cubre la explicación larga | **Acortar** a «Descríbelo con tus palabras.» y dejar el resto en el «?» |
| Pronunciar | «Graba la frase y te digo qué palabras se entendieron, qué sonido se escapa y cómo colocar la boca.» (`pantallas/pronunciar.html:15`) | Ya es la versión corta; la larga vive en el «?» | **Dejar** |
| Lector | El aviso único de la primera vez | Ya se arregló en la tanda 2 | **Dejar** |

**Cuenta de lo que se ahorra, separando dos cosas que se confunden con facilidad.** Las **27
palabras antes de la primera acción** de Inicio son el antetítulo, el titular y la entradilla, que
van **encima** de «Empezar a leer»; quitar «Cómo funciona» **no las toca**, porque ese bloque va
más abajo. Lo que ese bloque acorta es **la página**: 76 palabras de las 3,2 pantallas que mide
hoy. Las 27 solo bajan **acortando la entradilla**, de 20 palabras a unas 8, y entonces quedan en
unas 15. En *Encontrar* las dos cosas sí coinciden, porque el subtítulo es justo el texto de antes
de la primera acción: de **25 palabras a unas 6**. Nada de esto toca el lector ni *Pronunciar*,
que son los que el guion enseña.

## 5. Dos versiones

### Mínima — cabe antes del 20

**Solo el paso 0, dentro de la bienvenida.** Ni una pantalla más se toca.

- **Qué cambia:** un paso nuevo en `compartido/bienvenida.ts`, con sus dos botones; el contador
  pasa de «1 de 3» a «1 de 4».
- **Coste:** un paso, dos botones y su prueba. Es la misma forma que los tres pasos que ya
  existen.
- **Riesgo a tres días de grabar: bajo, pero no cero.** El guion manda pulsar «Saltar» antes de
  compartir pantalla, así que la demo no lo ve. **Pero hay que tocar tres líneas de guion**, que
  hoy dicen «una tarjeta de tres pasos («1 de 3»…)»: `guion_demo_en_vivo.md:140`,
  `guion_video.md:99` y `guion_video.tex:265`. Eso lo hago yo en un commit pequeño, con los PDF.
- **Lo que NO invalida:** ni el cronómetro (`auditoria/cronometro_demo_2026-09-16.md`) ni el
  ensayo del guion, porque ninguna medida de píxeles ni de tiempo es de la bienvenida: todas
  empiezan con ella saltada.

### Completa — después del 20

Los recortes de la sección 4, más el paso 0.

- **Qué cambia:** `inicio.ts` (quitar o plegar «Cómo funciona», acortar la entradilla),
  `encontrar.ts` (subtítulo corto), y la ayuda larga que se va al «?».
- **Riesgo si se hace antes de grabar: alto, y por eso no.** Mueve el contenido de Inicio y de
  *Encontrar*, que son los pasos 1 y 2 de la demo; **invalida las medidas de píxeles del ensayo**
  (los 679 px del paso 3, las «2 pantallas» del Índice) y obliga a volver a cronometrar. A tres
  días de grabar, cambiar la pantalla por la que empieza la demo es el peor sitio donde tocar.

## 6. Lo descartado, y por qué

**Las dos cosas de esta sección están descartadas por decisión de la Central (16 de septiembre),
no son una recomendación de quien escribe.** Se dejan con su motivo para que, si alguien las vuelve
a proponer después del 20, discuta el motivo y no la conclusión.

- **Un tour encadenado con globos sobre cada control**, tipo *coach marks*. Es lo que más se
  parece a «como una cuenta de Google», y es justo lo que Ismael pedía; pero son cuatro o cinco
  pantallas más antes de tocar nada, y e6 ya midió que los fallos de Ismael pasaban **dentro** de
  cada pantalla, no al llegar. Después del 20, si se hace, que sea con la regla de una frase por
  control y salida en cualquier momento.
- **Pop-ups que tapen el contenido.** Miguel los acepta, pero el fallo que acabamos de arreglar
  —el panel de *Ajustes* abriéndose encima del propio aviso— salió exactamente de eso. Si se usan,
  que no cubran el texto del libro, la barra del micrófono ni la caja de la frase.

## 7. Lo que queda abierto

Las cuatro preguntas que traía esta sección están contestadas en la sección 0. Queda esto:

1. **e6 programa el paso 0**, después de la boca 3D y del scroll, que van antes.
2. **4e actualiza las tres líneas de guion** que describen la tarjeta como de tres pasos
   (`guion_demo_en_vivo.md:140`, `guion_video.md:99`, `guion_video.tex:265`), **cuando e6
   publique**, en un commit pequeño con los PDF.
3. **Después de la entrega:** plegar «Cómo funciona» y los recortes de la sección 4, que mueven
   Inicio y *Encontrar* y obligan a recronometrar la demo.
