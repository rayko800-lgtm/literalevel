# Dos cosas que Miguel vio en la app: la boca 3D y la frase de Pronunciar

**Medido el 16 de septiembre de 2026** sobre la **revisión del Space `f4920fa`**
(commit `a656c2e`), a **390 × 844 px**, móvil y táctil, contexto limpio y sin
cuenta. Solo medición y propuestas: **no he tocado nada**.

Captura de prueba: `auditoria/capturas/boca3d_390_f4920fa.png`, tomada **del
propio elemento** (no de la pantalla), así que no depende de coordenadas.

---

## 1. La boca 3D

### Qué NO es

Conviene descartarlo primero, porque la sospecha inicial iba por ahí:

- **No es el contenedor.** El lienzo mide **290 × 420 px** y cabe entero en
  pantalla (de 248 a 668 del viewport). No lo corta nada.
- **No es el lienzo mal dimensionado.** El búfer es 580 × 840 (pixel ratio
  capado a 2) y `redimensionar()` recalcula `aspect` y la matriz de proyección.
- **No es el modelo descentrado.** El centro del dibujo cae en el centro del
  lienzo (desviación horizontal por debajo del 1 %).
- **No es que falte el modelo.** `cara.glb` (3,17 s) y `lengua.glb` (2,99 s)
  cargan, y el lienzo queda marcado `data-cara="blender"` y
  `data-lengua="blender"`.

### Qué es

**El contenido es apaisado y el lienzo es vertical.** La proporción del lienzo
es **0,69** (290 de ancho por 420 de alto), y lo que hay que enseñar —un perfil
de cara— es más ancho que alto. El resultado, que se ve en la captura:

- el perfil **toca el borde izquierdo**: los labios, que son justo lo que hay que
  mirar, quedan al límite del encuadre;
- **sobra banda vacía arriba y abajo**, sin nada que mirar;
- por la derecha, el corte vertical de la nuca **es del modelo, no de la
  cámara**: el `.glb` es media cabeza seccionada, y el plano blanco del cuello
  que Miguel describe es esa sección.

La cámara mira al punto `(0,1 · 0,05 · 0)` —la boca— a una distancia de
`14,5 × 1/aspect` = **21,0**. El 14,5 está calibrado, según el propio comentario
del código, para «un móvil (288 × 420)», que es casi exactamente este lienzo. Es
decir: **está funcionando como se diseñó, y aun así no cabe bien**, porque la
forma del hueco no es la del contenido.

### Propuesta mínima, para antes de la entrega

**No tocar el `.glb`.** Que la cabeza esté seccionada es cosa del modelo, y eso
es Blender: Miguel lo deja para después.

Dos números en `escena.ts`, sin tocar geometría:

1. **Mover el punto al que mira la cámara hacia atrás**, de `x = 0,1` a `x ≈ 0,9`
   cuando la cara está modelada (`vista()`, línea 1061). Ese valor ya existe en
   el código para el caso `cabezaEntera`, así que no es un número inventado:
   desplaza el encuadre y despega los labios del borde izquierdo.
2. **Alejar un poco**: de 14,5 a **16–17,5** para el caso `caraModelada`
   (`distanciaEncuadre()`, línea 1081). 17,5 es, otra vez, el valor que el código
   ya usa para la cabeza entera.

Con eso el perfil deja de tocar el lado y se aprovechan las bandas muertas. Es
un cambio de dos constantes, reversible, y se comprueba con una captura del
elemento antes y después.

### La buena, para después del 20

**Encuadrar por la caja envolvente y no por constantes.** Calcular la `Box3` de
lo visible y derivar distancia y punto de mira para que quepa con un margen
fijo (un 5 %, por ejemplo). Hoy hay tres constantes —13, 14,5 y 17,5— calibradas
a ojo para un tamaño de lienzo concreto; cualquier pantalla distinta vuelve a
descuadrar. Con la caja envolvente, el encuadre es correcto en cualquier móvil y
deja de haber números mágicos.

### Lo que Central preguntaba de los botones

**Siguen donde estaban**, debajo del visor y sin solaparse: «Escuchar y ver» y
«🐢 Despacio» en **636 – 684**, y «Cerrar 3D» en **692 – 740**. Ninguno queda
tapado por la barra del micrófono ni por la navegación inferior.

---

## 2. La frase, en Pronunciar

La queja de Miguel —«tengo que scrollear para buscar el texto»— es **de un
desplazamiento dentro del cuadro de texto**, no de la página. Medido:

- El cuadro de la frase tiene **altura fija de 112 px**, que son **seis líneas**
  de 19 px.
- Lo que cabe, según la frase:

| Frase | Caracteres | Líneas ocultas |
|---|---|---|
| «Don't you want to come with us?» (la del guion) | 31 | **0** |
| Una frase media | 109 | **2** |
| Una oración de libro típica | 180 | **5** |
| Una oración larga | 262 | **8** |

- **Al pulsar el micrófono no pasa nada con la vista:** `scrollY` sigue en 0, la
  frase no se mueve y el cuadro conserva su desplazamiento interno. Para leer el
  final de la frase hay que arrastrar **dentro** de un cuadro de 112 px, que es
  lo más difícil de encontrar de toda la pantalla.
- **La barra de grabación crece al grabar**, de 127 a **159 px** (de 617 a 776),
  y la navegación inferior ocupa otros 67 (777 – 844): **227 px de los 844 están
  ocupados por barras fijas mientras se graba**.
- El bloque de la frase llega hasta 646 y la barra empieza en 617: **la barra
  tapa los últimos 29 px del bloque**.
- Al grabar, **el foco no queda en el cuadro**, así que ni siquiera se puede
  desplazar con el teclado sin volver a tocarlo.

Con la frase del guion (31 caracteres) **esto no se reproduce**: cabe entera. Por
eso no se vio antes. Aparece en cuanto la frase viene de un libro.

### Propuesta mínima, para antes de la entrega

**Que al empezar a grabar la frase se vea entera y sola.** Dos cambios de
presentación, sin lógica nueva:

1. Mientras el estado es «grabando», **el cuadro de texto deja de ser un cuadro
   con desplazamiento y se muestra como texto completo** (altura automática, sin
   recorte): ya no se edita mientras se graba, así que no necesita ser un campo.
2. Y **llevar la vista a la frase** al empezar (`scrollIntoView` del bloque 1),
   para que quede sobre la barra del micrófono.

Con una oración de libro de 180 caracteres, el texto pasaría de 112 px a unos
200: sigue cabiendo entre la cabecera (65) y la barra de grabación (617).

### La buena, para después del 20

**Una pantalla de grabación, no una pantalla de formulario.** Mientras se graba,
lo único que importa es la frase y el contador; el resto —el AFI, el aviso de
OpenAI, el paso 1 con su botón de borrar— sobra y es lo que hace que Miguel diga
«con tanta información me pierdo, no sé dónde estaba». Una vista dedicada, con
la frase grande y centrada, resolvería a la vez el desplazamiento, el foco y las
227 px de barras.

---

## 3. Seis medidas mías que no valían, y por qué

Esto me ha costado seis intentos, y todos fallaron igual: **una condición
demasiado laxa que se cumple sola**. Lo dejo escrito porque el patrón se repite:

1. `svg path` como selector de «la curva»: **todos los iconos** son `svg` con
   `path`.
2. «El capítulo ha cargado» comprobando un texto que **ya estaba en la ficha**.
3. «La bienvenida tarda 34,8 s»: medía **cuándo llegó mi guion**, no cuándo la
   vio el usuario.
4. Recortar la captura de pantalla por las coordenadas del DOM, **con la página
   desplazada 1.411 px**: medí el fondo de la página y lo llamé modelo.
5. Detectar el lienzo «por la región clara más grande»: cazó **la ficha 2D** de
   arriba.
6. Separar modelo y fondo por saturación: **el fondo del lienzo es beige**
   (saturación 14) y con degradado, así que cualquier umbral global miente.

Lo que sí vale, y es lo que sostiene este informe: **las medidas del DOM**
(tamaños, posiciones, líneas ocultas, tiempos) y **una captura del propio
elemento**, que se puede mirar.

### Y una sospecha que conviene comprobar

`tools/probar_boca_integrada.mjs` garantiza el encuadre con
`assert.equal(px.borde, 0)` —«el modelo no toca el borde»—, leyendo el canvas
con `drawImage` + `getImageData`. **Al ejecutar ese mismo código en el navegador,
el canvas se lee vacío**: un solo color y cero píxeles opacos, porque el WebGL no
conserva el búfer. Si en Playwright pasa lo mismo, ese `assert` **está pasando
sin medir nada** y la garantía de encuadre es falsa. No lo he comprobado en
Playwright y no lo doy por cierto: es verificable en diez minutos y merece la
pena antes de fiarse de esa prueba.
