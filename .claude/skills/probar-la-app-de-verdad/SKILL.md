---
name: probar-la-app-de-verdad
description: Probar una aplicación desplegada como la usa una persona, no como la mira una suite de pruebas — el camino que solo existe en producción, lo que nadie encuentra, y el contraste que se mide mal. Úsala antes de dar por buena cualquier interfaz, y siempre que alguien diga «no encontré dónde».
---

# Probar la aplicación de verdad

En un solo día, LiteraLevel pasó **nueve auditorías externas**, tres
verificaciones que ejecutaban código y **209 pruebas automáticas**. Ninguna
encontró estos tres fallos:

1. **La aplicación desplegada no podía puntuar nada.** El fallo central del
   producto, muerto en producción.
2. **La caja para activar las funciones de pago no la encontraba nadie**,
   empezando por el autor.
3. **El texto secundario estaba en 3,2:1**, por debajo de WCAG AA, con todos
   los colores declarados pasando la prueba de contraste.

Los tres los encontró Miguel abriendo la app en su móvil. Esta skill es lo que
se aprendió.

---

## 1. El camino que se despliega no es el camino que se prueba

`Puntuador.__init__` hacía `os.path.isdir(ruta)` y en el Space la ruta era
`MikeMaki1763/literalevel-v4`, un identificador del Hub. La app arrancaba, la
interfaz entera funcionaba —catálogo, lector, diccionario, paletas— y al pedir
una medición devolvía «No encuentro el modelo».

**Por qué ninguna prueba lo vio:** las 209 pruebas, el *smoke* y
`validar_local.py` cargan el modelo **de disco**, porque en la máquina de
desarrollo existe `./modelo_v4`. La rama que usa producción no la ejercita
nada.

**La pregunta que hay que hacerse, y que no es teórica:**

> ¿Qué hace esta aplicación en producción que no haga ninguna prueba?

Casi siempre hay tres respuestas, y las tres muerden:

- **Cargar recursos por una vía distinta** (un repositorio remoto en vez de una
  carpeta, un bucket en vez de un fichero, una variable de entorno en vez de
  un valor por defecto).
- **Correr sin algo que en local sobra**: sin la clave de la API, sin disco
  persistente, sin las 12 CPU de casa.
- **Empezar de cero**: primer visitante, caché vacía, ningún dato de usuario.

Escribe una prueba para cada una, aunque sea fea. Una prueba que instancie el
cargador con el identificador remoto y compruebe que puntúa vale más que veinte
que comprueben lo mismo por el camino cómodo.

---

## 2. Si el autor no lo encuentra, no existe

La caja de activación vivía dentro de un acordeón **cerrado**, dentro de la
pestaña que la necesitaba, que era una de ocho. El razonamiento al ponerla ahí
fue: *«así el usuario la encuentra cuando le hace falta, en vez de ir a
buscarla a un menú»*. Suena bien y es falso: quien no sabe que existe no la
busca donde hace falta, **no la busca en ninguna parte**.

Reglas que salieron de ahí:

- **Lo que abre funciones va arriba y abierto**, antes de cualquier pestaña. Si
  algo condiciona lo que la aplicación puede hacer, no puede estar a dos clics
  de profundidad.
- **Una credencial se entiende o no se usa.** Un código suelto —`QQHT-P5V2-V4DM`—
  no le dice a quien lo recibe si es suyo, para qué sirve ni cuánto le queda.
  Un **usuario y una contraseña** sí, y permiten saludar por el nombre y decir
  los usos restantes.
- **Di siempre qué funciona sin entrar.** Si el 90 % de la aplicación es libre,
  decirlo en la misma caja evita que alguien se marche pensando que necesita
  permiso para todo.
- **Pon el botón de salir.** En un ordenador prestado, importa.

### El contraejemplo que hay que buscar

Cuando termines una pantalla, pregúntate: *si le doy esto a alguien sin
explicarle nada, ¿en cuántos sitios va a mirar antes de rendirse?* Si la
respuesta es «tiene que abrir un desplegable», ya está mal.

---

## 3. El contraste que se declara no es el que se ve

La prueba de contraste comprobaba **40 parejas de colores declarados** y todas
pasaban AA. Y aun así el texto secundario se leía mal en las paletas claras.

El culpable era el CSS:

```css
#ll-cuaderno .ll-d { opacity: .62 }
```

`opacity` **compone el texto contra el fondo**. Ningún color cambia, así que
una prueba que mire los colores no puede verlo. Medido:

| opacity | .60 | .62 | .65 | .70 | .75 |
|---|---|---|---|---|---|
| paleta *menta* | 3,23 | 3,41 | 3,65 | 4,14 | 4,73 |

Con `.62` el texto está en **3,41:1** — por debajo de 4,5 — con todo declarado
correctamente.

**La regla:** el contraste se mide sobre el color **compuesto**, no sobre el
declarado. Y como el CSS cambia, la prueba tiene que **leer las opacidades del
propio CSS** en vez de llevarlas escritas:

```python
alfas = {float(x) for x in re.findall(r"opacity:(\.[0-9]+)", css)}
for alfa in alfas:
    visto = componer(texto, fondo, alfa)
    assert ratio(visto, fondo) >= 4.5
```

Lo mismo vale para `rgba()` con alfa, para un `color` heredado que se pinta
sobre un `background` semitransparente, y para el texto sobre un degradado: ahí
hay que medir **el extremo peor del degradado**, no el punto medio.

---

## 4. Conducir la aplicación desplegada desde aquí

Se puede, y hay que hacerlo. Con `chrome-devtools`:

1. `new_page` con la URL del Space.
2. `evaluate_script` con `document.body.innerText` para ver **qué se lee** de
   verdad. Es más barato que un snapshot y contesta la mayoría de las
   preguntas: ¿aparece el botón nuevo?, ¿queda algún rastro del texto viejo?
3. `take_snapshot` cuando necesites **uids** para interactuar.
4. `fill` + `click` para probar el recorrido: primero con datos malos, después
   con los buenos. Comprobar el rechazo importa tanto como comprobar el éxito.
5. `evaluate_script` otra vez para leer el resultado.

Un recorrido de prueba que vale la pena automatizar tras cada despliegue:

- entra con una contraseña mala → tiene que rechazar con un mensaje entendible;
- entra con la buena → tiene que saludar por el nombre;
- ve a la pantalla principal → comprueba el **orden** de los bloques, que es lo
  que decide si algo se encuentra o no.

El orden se lee así, sin snapshot:

```js
const t = document.body.innerText;
['Consultar una palabra', 'Índice'].map(m => [t.indexOf(m), m]).sort()
```

### Pulsar como un dedo, no como un script

El 13 de septiembre, la primera pasada sobre el Space a 390 px dio **dos
resultados falsos**. Decía que ⚙ Ajustes abría, y estaba tapado. Decía que el
menú «…» no llevaba a Pronunciación, y sí llevaba.

- **`element.click()` desde JavaScript atraviesa lo que tapa al elemento.** En
  el Space, la cabecera fija de Hugging Face (`#huggingface-space-header`, la
  insignia con el nombre del Space) ocupa la franja superior de la página. En
  local no existe. Un botón debajo de ella «funciona» por script y no se
  puede pulsar con el dedo. Antes de dar un botón por bueno, mira qué hay de
  verdad en su centro:

  ```js
  const r = boton.getBoundingClientRect();
  document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)
  ```

  Y pulsa con toques reales por el protocolo de depuración:
  `Input.dispatchTouchEvent` (`touchStart` y luego `touchEnd`) en esas
  coordenadas.
- **Gradio guarda una copia invisible de las pestañas para medir cuáles
  caben.** Un `querySelectorAll('button')` filtrado por texto puede devolver
  esa copia, a la altura de la barra, en vez de la opción del desplegable «…».
  Filtra por posición (debajo del botón «…») y por tamaño.
- **Sin `Emulation.setTouchEmulationEnabled` no hay móvil.** Con solo cambiar
  el ancho de la ventana, Chrome sigue diciendo `hover:hover` y
  `pointer:fine`, y las reglas `@media` táctiles no se aplican.
- **Un `Textbox` de Gradio 6 de una línea puede ser un `<textarea>`.** Busca
  por `[placeholder=...]`, sin la etiqueta delante, o la escritura cae en el
  vacío y el «No he podido entrar» parece un fallo del Space.

---

## 5. Lo que hay que comprobar después de cada despliegue

- El Space vuelve a `RUNNING` (la API lo dice) **y** la página responde 200.
- El texto nuevo aparece y **el viejo no**. Buscar solo lo nuevo deja pasar los
  restos.
- El camino de producción funciona de verdad: no que la app arranque, sino que
  **haga lo que existe para hacer**. Arrancar y no poder medir es peor que no
  arrancar, porque parece que va.

---

## 6. Y lo más importante

**Dale la aplicación a una persona y mírala usarla.** Nueve auditorías miraron
el código y los documentos; ninguna podía ver que la caja no se encontraba,
porque en el código está perfectamente visible.

Cuando alguien diga «no encontré dónde», eso **no es una pregunta**: es un
informe de fallo, y el fallo es tuyo.


---

## 7. Arreglar el color del texto sin arreglar el fondo

Esto salió de la corrección de la sección 3, y es la lección más cara del día
porque parecía terminada.

Cuando una interfaz hereda su tema de un framework —Gradio, Bootstrap, lo que
sea— y encima le pones una paleta propia, el navegador acaba mezclando dos
fuentes de verdad. Si redefines solo la mitad, el contraste no mejora: **se
mueve de sitio**.

Medido, después de forzar `--body-text-color` desde la paleta y creer que ya
estaba:

| dónde | contraste | qué era |
|---|---|---|
| casillas de opción | 1,03–1,11:1 | letra de la paleta, relleno del tema |
| casilla **elegida** | 2,12–2,44:1 | mi propia regla `!important` ganándole a la variable del tema |
| pestaña seleccionada | 2,80–2,98:1 | `--color-accent`, que nunca miré |
| gráfica de Plotly | 1,3:1 | una imagen con los colores dentro |

**La regla:** haz la lista de las variables del tema que pintan **superficies
con texto encima** —casillas, entradas, botones secundarios, bloques, tablas,
código, acento— y átalas todas a la paleta, o no ates ninguna. La lista se saca
del navegador, no de la memoria:

```js
const props = new Set();
for (const ss of document.styleSheets)
  for (const r of ss.cssRules || [])
    for (const p of (r.style || [])) if (p.startsWith('--')) props.add(p);
```

Eso devolvió 692 variables y 396 relevantes. Elegir a ojo cuáles importan es
cómo se pasan por alto cuatro.

### Lo que no es CSS

Una gráfica de Plotly, un PNG generado, un PDF: **no leen variables CSS**. Son
imágenes con los colores dentro, y si el tema es elegible, el color tiene que
viajar hasta ahí como un dato.

Y no hay atajo: para pasar AA sobre el fondo más oscuro de la aplicación hacía
falta luminancia ≥ 0,186, y sobre el más claro ≤ 0,174. **Ningún color cumple
las dos.** Cuando alguien proponga «un gris que valga para todos», ese cálculo
de dos líneas cierra la discusión.

En Gradio, el camino es un `gr.State` declarado arriba —donde están los demás
`State`— y rellenado abajo, donde vive el selector; los eventos se cablean en
orden de construcción, así que el componente que aún no existe no se puede
referenciar, pero un `State` sí. Y acuérdate de **repintar** lo ya dibujado al
cambiar de tema: el CSS cambia solo, la imagen no.

---

## 8. Medir demasiado pronto miente

Los primeros barridos de contraste sobre la página desplegada dieron grises que
no pertenecían a ninguna paleta: texto `rgb(162,162,163)` sobre fondo
`rgb(155,157,161)`, 1,06:1. Parecía un fallo grave. Era la página a medio
pintar.

Cambiar de paleta son dos cosas seguidas: una ida y vuelta al servidor que
devuelve el `<style>` nuevo, y una transición CSS de 0,2 s. Si mides antes de
que las dos acaben, mides una mezcla.

**Cómo se distingue un fallo de un artefacto de medición**, sin adivinar:

1. Lee la huella del tema —`getComputedStyle(raiz).getPropertyValue('--mi-texto')`—
   y espera a que **cambie**; eso confirma que el CSS nuevo llegó.
2. Espera además a que la transición termine.
3. Vuelve a medir. Si el fallo desaparece, era el reloj; si sigue, es tuyo.

Y el corolario: **acota la medición a tu propia raíz**. Los primeros informes
señalaban un `/` con 1,41:1 que resultó ser el separador de la cabecera que
inyecta Hugging Face, fuera de `.gradio-container`. Un fallo que no puedes
arreglar y no es tuyo solo gasta el tiempo del siguiente.

---

## 9. Una prueba que pasa no demuestra que cazaría el fallo. Mútala.

Es la lección más cara del 9 de septiembre, y llegó por partida doble.

El cierre del día afirmaba que los tres fallos que encontró Miguel usando la
app «tienen ahora una prueba que los cazaría». Una auditoría lo desmintió con
un `grep`: dos de los tres no la tenían. Se escribieron. Y la siguiente pasada
encontró algo peor: **la prueba del fallo 1 existía, pasaba, y pasaba también
con el código roto.**

El fallo era un guardia en `scoring.Puntuador`:

```python
if not (os.path.isdir(ruta) or _parece_repo_hf(ruta)):   # bueno
if not os.path.isdir(ruta):                              # la regresión
```

La prueba comprobaba `_parece_repo_hf("owner/name") is True` y que una carpeta
inexistente diera el error legible. Las dos cosas siguen siendo verdad con el
guardia roto: medía **el ayudante, no el guardia**. La única aserción que
distingue un código del otro es construir el `Puntuador` con un identificador y
comprobar que **llega a cargar**.

**El procedimiento, que cuesta diez minutos y hay que hacerlo siempre:**

1. Copia el módulo al scratchpad y **mete la regresión a mano** — la línea
   exacta que estaba mal, no una parecida.
2. Ejecuta la prueba contra las dos copias, en subprocesos separados.
3. Exige las dos salidas: `código real -> PASA`, `código mutado -> FALLA`.

Si el mutado también pasa, la prueba es decorativa. Y no vale cargar los dos
módulos en el mismo proceso con `importlib`: `dataclasses` revienta al resolver
tipos de un módulo que ya no está en `sys.modules`. Un subproceso por copia.

### El caso hermano: una prueba puede medir lo que ya no se pinta

`_contraste_suficiente` mide **variables de la paleta**. Cuando el CSS clava un
color a mano, la prueba sigue en verde midiendo una variable que el navegador
no usa. Así sobrevivieron cuatro colores clavados a un arreglo de contraste que
se dio por cerrado: el resaltado de `::selection` en amarillo (1,20:1 en las
paletas claras, **y seleccionar es cómo se consulta el diccionario**), el canal
de la barra de avance (1,47:1), el borde de la cita del cuaderno (1,23:1) y el
borde del lector. Dos variables —`--ll-seleccion`, `--ll-lector-texto`— estaban
declaradas en las cinco paletas y **no las pintaba nadie**: código muerto que
ninguna prueba podía delatar, porque las pruebas las medían a ellas.

Contra eso hacen falta **dos** pruebas, no una:

- la numérica, sobre las variables compuestas con su alfa;
- una estructural que abra los bloques `<style>` y exija que esas reglas usen
  `var(--ll-…)` y **no contengan ningún color literal**. Quitando primero los
  comentarios del CSS, que citan los colores viejos a propósito.

**Y ojo con el orden de las reglas.** Un `border:1px solid …` abreviado y
posterior reescribe entero el `border-color:var(--ll-borde)` que puso la
paleta. La especificidad no lo explica: es que va después.

### Corolario sobre los regex de las pruebas

`re.findall(r"opacity:(\.[0-9]+)", css)` no ve `opacity: 0.3`, ni `opacity:0`,
ni `opacity:1`, ni `opacity:30%`. Pasaba **por convención de escritura**: con
el mismo color pintado, `opacity:.3` la hacía fallar y `opacity:0.3` no. Lo
mismo con `#[0-9a-fA-F]{6}`, que no ve `#8ce`, ni `rgb()`, ni `hsl()`.

Cada vez que una prueba busque una declaración CSS con un regex, escribe las
formas que **no** cubre y comprueba una a una que las cazaría. Y lee todos los
archivos que llevan CSS, no solo el primero: la prueba de opacidad miraba
`ui.py` y no `paletas.py`.

### El envoltorio que imprime `ok False`

El caso mayor de todo esto no estaba en una prueba, sino en el **envoltorio**
que las ejecuta. `prueba(nombre, fn)` imprimía lo que devolviera `fn`, así que
un `False` salía como `ok False` y la suite terminaba en verde. Treinta y nueve
pruebas devolvían un booleano que nadie aseveraba. Con eso, un banco de
mutaciones demostró que la suite pasaba entera con:

- `_entrar` aceptando **cualquier contraseña**;
- los tres topes por hora apagados;
- la práctica de voz **sin puerta de pago**;
- `_salir` que no olvida la sesión;
- `_dir_lector` devolviendo la misma carpeta a todos los lectores.

Dos cosas que se aprenden aquí y no son obvias:

**1. Prohibir el valor no es la solución.** El arreglo que sugería el auditor
—`assert r is not False` a secas— rompía cinco pruebas legítimas de golpe:
«palabra vacía se rechaza», «sin título se rechaza», «libro que ya no existe se
marca»… En todas ellas `False` **es** el resultado correcto, porque la función
devuelve `False` cuando rechaza. Lo que hay que arreglar es que la prueba
**asevere su expectativa** en vez de devolver el booleano crudo:

```python
prueba("palabra vacia se rechaza",
       lambda: not cuaderno.registrar(palabra="", ...) and "rechazada")
```

Así devuelve una cadena legible cuando acierta y `False` —ahora sí, un fallo—
cuando el rechazo deja de funcionar. La regla en el envoltorio y la aserción en
la prueba son las dos necesarias: sin la primera nadie mira el valor, sin la
segunda la primera dispara sobre inocentes.

**2. Itera lo que devuelva una generadora.** `_medir`, `_consultar` y
`_de_que_trata` lo son, y una `lambda` que las llama sin iterarlas devuelve el
generador **sin ejecutar una sola línea del cuerpo**. La prueba «medir índice
imposible» imprimía `ok <generator object …>` y pasaba igual con un
`IndexError` dentro. Un `if inspect.isgenerator(r): r = list(r)` en el
envoltorio lo arregla para todas a la vez.

### La tercera forma de que una prueba no pruebe nada

Las dos primeras están arriba: devolver un booleano que nadie asevera, y no
iterar una generadora. La tercera la encontró un banco de mutaciones **sobre
pruebas recién escritas para cerrar una auditoría**, y es la más engañosa:

> **El manejador rechaza la entrada antes de llegar al código que quieres
> probar, y tu aserción se cumple sobre el vacío.**

El caso literal. Para comprobar que `_consultar` recorta la oración antes de
mandarla a OpenAI, la prueba pasaba una «palabra» de 300 caracteres y miraba lo
que había recibido un consultor doble:

```python
list(ui._consultar(None, None, None, "x" * 300, largo, "es", None))
assert len(vistas.get("oracion", "")) <= ui.LIMITE_ORACION      # se cumple sola
```

`_consultar` contesta «eso son 300 caracteres seguidos: ninguna palabra inglesa
pasa de 40» y **vuelve sin llamar al consultor**. `vistas` queda vacío,
`len("") <= 400` es cierto, y quitar el recorte del código no rompía la prueba.

Dos costumbres que lo cierran:

- **Asevera que el doble se llamó.** `assert "oracion" in vistas` antes de
  medir lo que vio. Un espía que no registró nada es un espía que no vio nada,
  no una prueba que pasó.
- **Exige el valor exacto, no una cota.** `== LIMITE_ORACION` en vez de
  `<= LIMITE_ORACION`: la cota la cumple el vacío y la igualdad no.

Y lo mismo con los datos de prueba, que fue el otro par de fallos de esa tanda:
una licencia de Gutenberg escrita **en una sola línea** cuando la de verdad son
párrafos —el ayudante que quita la primera línea se la llevaba entera—, y un
epub de prueba cuya portadilla tenía el título sacado del texto legal, así que
caía por una regla vieja y la nueva no hacía falta. **Un dato de prueba
demasiado limpio prueba el camino equivocado.**

### Arreglar algo puede quitar una red que otra cosa usaba

En la misma tanda: `reader` ponía como título del capítulo la cabecera corrida
de Gutenberg («The Project Gutenberg eBook of…»), y eso era un fallo de verdad
—trece capítulos con el mismo nombre—. Al limpiarlo, **tres libros empeoraron**:
su portadilla legal dejaba de tener «Project Gutenberg» en el título, y resulta
que el detector de licencia estaba viviendo de eso sin que nadie lo hubiera
escrito.

No se vio leyendo. Se vio porque antes de dar el arreglo por bueno se midió lo
mismo con el código de antes y con el de después, sobre los nueve libros
cacheados:

```
antes:  P&P 14 de 15   Grimms 62 de 63   W&P 362 de 366   Alicia-il. 1 de 13
tras 1: P&P 15 de 15   Grimms 63 de 63   W&P 363 de 366   Alicia-il. 12 de 13
                       ^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^  la portadilla entro
```

**La costumbre:** cuando arregles algo que otra cosa consultaba, corre la
medición completa con el árbol de antes y con el de después y compara fila por
fila. `git show HEAD:app/x.py > copia/app/x.py` sobre una copia del árbol cuesta
un minuto y es la única forma de ver el daño colateral, porque la prueba nueva
solo mira lo que fuiste a arreglar.

Y el remate: **el primer parche fue un umbral inventado** («es portadilla si le
quedan menos de 1.200 palabras»), y una prueba lo tumbó por llevarse un capítulo
de verdad de mil palabras. El criterio bueno no era una longitud, era una
propiedad: que lo que queda tras quitar la licencia **no sea prosa corrida**. Si
tienes que elegir un número a ojo para que tus cinco casos caigan bien, casi
siempre existe una propiedad que no necesita número.

**Y una advertencia sobre el propio banco de mutaciones:** apunta qué prueba
falla, no solo que la suite falla. En la primera pasada, tres mutantes «se
cazaban»… por una prueba de rutas que fallaba en la copia por un archivo que no
había copiado. El mutante parecía cubierto y no lo estaba. Exige el nombre de
la prueba que salta, y que sea la que te esperas.

---

## 10. El front de Angular publicado: lo que solo se ve en el Space

Aprendido entre el 13 y el 14 de septiembre, publicando el front estático una
docena de veces. Todo esto pasaba las pruebas y el build.

### La meta vacía: el front publicado no llegaba al motor

El build de Angular **minifica** `<meta name="literalevel-api" content="">` a
`<meta name="literalevel-api" content>`, sin valor. El publicador lo leía con
un parser HTML que devuelve `None` para ese atributo y solo escribía la URL
cuando había valor: la meta salió vacía, el front pidió `/api/salud` a **su
propio dominio**, 404, y la pantalla dijo «No consigo hablar con el motor»
mientras el motor respondía 200 a `curl`.

Qué lo destapa y qué hacer siempre tras publicar:

```bash
curl -sL "https://…-front.static.hf.space/index.html?nocache=$RANDOM" \
  | grep -o '<meta[^>]*literalevel-api[^>]*>\|main-[A-Z0-9]*\.js'
```

Tiene que salir el `main-*.js` nuevo **y** `content="https://…"`. Y si la
pantalla dice que no hay motor, antes de culpar al Space mira
`list_network_requests`: si las peticiones van a `…-front.static.hf.space/api/…`,
es la meta. La prueba del publicador tiene que usar **el HTML tal como sale del
build**, no uno escrito a mano con `content=""`.

### Pestañas atrapadas en el build anterior

Una pestaña abierta antes de publicar sigue con el `main-*.js` viejo, que pide
chunks perezosos que ya no existen (o no los pide, y enseña la pantalla vieja).
Dos consecuencias:

- **Para verificar, pestaña nueva** (o `navigate_page` con `ignoreCache`) y
  comprueba en el propio DOM qué `main-*.js` cargó
  (`[...document.scripts].map(s => s.src)`). Si lo que ves no cambió, casi
  seguro estás mirando el build anterior, no un fallo.
- **Para el usuario**: el publicador no borra chunks viejos, `nucleo/version.ts`
  recarga una vez si falla la carga de una ruta, y el `@defer` de la boca 3D
  (que no pasa por el router) tiene su botón «Recargar y reintentar».

### 390 px con emulación táctil, y medir en vez de mirar

`emulate` con `390x844x3,mobile,touch` **antes** de medir: sin táctil no hay
pulsación larga ni el comportamiento de los bordes del lector. Y mide:

- `document.documentElement.scrollWidth` tiene que ser 390. Así salió que la
  ficha se salía 4 px al ensanchar la portada: un chip largo empujaba una
  columna `1fr` (hace falta `minmax(0, 1fr)`).
- Tamaños reales de lo que se pulsa (`getBoundingClientRect().height ≥ 48`) y
  que una barra fija no tape lo que debe verse (la barra de «Escuchar y ver»
  tapaba la boca 3D hasta que se midió dónde quedaba el visor al pulsar).
- Contraste sobre el **color calculado** (`getComputedStyle`), no sobre el
  declarado; y del párrafo de texto de verdad: el primer `p` de la hoja era una
  pista con el color de acento y daba 5,6:1 cuando el texto estaba a 12,6:1.

### Lo que el Space no puede probar: micrófono y OpenAI

En el Space no hay micrófono ni sesión con usos, así que la corrección de voz
no se ve de verdad. Se prueba en local inyectando el resultado en el componente
(`ng.getComponent(el).resultado.set({...})` en modo desarrollo) con **el JSON
real** que manda quien escribió el contrato, no uno inventado: así se vieron
«aquí sin pausa», los arcos de enlace y la leyenda partiéndose en trozos. Y en
automatización, `audio.play()` puede no sonar ni emitir `playing`: comprueba
también el camino de la voz del navegador y el de «sin audio».

### `@defer` que no separa si se reexporta

Con `import { Boca3d } from '../compartido/boca3d'` (un índice que reexporta)
el build dejaba three.js entero, 736 KB, dentro del chunk de Pronunciar: el
`@defer` compila, funciona, y no ahorra nada. Solo separa el componente en su
chunk si se importa **directamente** desde el archivo que lo declara. Y lo
mismo con `viewChild(Boca3d)`: usar la clase como valor la vuelve a meter;
`viewChild<Boca3d>('visor')` con una referencia de plantilla, no. Comprobación:
la tabla de chunks de `ng build` (el de Pronunciar en ~40 KB y uno aparte de
~730 KB) y, en el navegador, que ningún `.glb` ni chunk grande baja hasta
pulsar «Boca en 3D».

### Publicar sin llevarse el trabajo de otros

Varias sesiones comparten el árbol. Dos tropiezos reales: `git stash` guardó
archivos ajenos, y un commit con rutas explícitas se llevó cinco líneas sin
commit de otra sesión que dependían de una función aún no confirmada (HEAD
rompió al medir). Publica desde un worktree limpio de HEAD y, antes de `git
add` de un archivo compartido, mira `git diff -- ruta`.


## Demuestra que la medida no estaba hueca (16 sep)

Medir «sin sesión» tiene una trampa: si la llamada que trae el estado no llega,
la aplicación tampoco cree que estés fuera, y el camino que querías medir **no se
ejecuta**. Entonces el resultado sale «bien» sin haber probado nada.

f4 lo dejó demostrado al revés, sin falsear nada: el aviso que midió lo escribe un
`return` temprano que **solo** se alcanza cuando el estado dice «bloqueada». Si el
estado hubiera quedado nulo, en su lugar habría salido la respuesta del servidor.
Es decir, el propio texto observado prueba que la rama medida es la de verdad.

- Antes de dar por buena una medida de un caso «sin algo», di **qué se habría
  visto si el caso no se hubiera dado**. Si no sabes distinguirlo, la medida no
  vale.
- Y comprueba el estado por lo que hay, no por lo que supones: aquí, `localStorage`
  con solo preferencias, y el identificador del navegador —el que viaja en
  `X-Lector`— que **no** es una sesión.

**Y su gemela: un cero solo vale si la medida puede ver un uno.** Buscando si un
aviso mal escrito salía en la demo, f4 midió diez consultas del guion y no salió
nunca. En vez de reportar el cero, montó un **control positivo**: seis consultas
hechas para forzar el aviso (galimatías y temas lejanos), cada una con y sin
perfil y con cuatro tamaños de lista, 48 peticiones más. Seguía sin salir. Solo
entonces buscó el motivo en el código, y resultó que la rama **es inalcanzable con
la configuración que se entrega**: el umbral que la dispara no lo cambia ningún
llamador ni ninguna variable de entorno.

- Antes de dar un «no pasa nunca», enseña la consulta que **debería** hacerlo
  pasar. Si tampoco pasa, el hallazgo ya no es el aviso: es que la rama está
  muerta, y eso se decide, no se arregla a ciegas.
- Desconfía de una prueba que **fabrica** la cadena que debería producir el
  código: aquí, la suite comprobaba que la interfaz muestra un texto construido a
  mano y nunca ejecutaba la línea que lo genera, así que el fallo de plural no lo
  iba a cazar nadie.

### La prueba que se cree a sí misma

Dos veces el mismo día, y 4e lo juntó: una prueba puede pasar o fallar por una
cadena **que ha escrito la prueba**, no la aplicación.

- `pruebas_extremas.py:5743` comprobaba que la interfaz muestra «Se descartaron 3
  por parecido bajo.» **construyendo ese texto en la prueba**. La línea que lo
  genera de verdad no se ejecutaba nunca, y de hecho es inalcanzable.
- Una prueba nueva del front afirmaba `'1 consulta'` con un espacio que en la
  pantalla **lo pone el CSS**: el número y el sustantivo son dos nodos. Falló, y
  la salida buena no fue retocar la aserción sino **emparejar cifra y sustantivo
  leyendo el DOM**, con lo que además queda fijado que no se despareje.

La pregunta que separa las dos: **¿de dónde sale el texto que estoy comparando?**
Si sale de la prueba, la prueba se está creyendo a sí misma.

**Una aserción que no puede fallar es el mismo fallo sin texto.**
`pruebas_extremas.py:519-521` guardaba la cadena del aviso de tope con una lambda
que devuelve una **tupla**: `lambda: (len(...) > 40, len(...) > 40)`. El
lanzador solo falla con una excepción o con `False` exacto, y una tupla no es
ninguna de las dos, así que imprimía `ok` pasara lo que pasara. Lo tragicómico:
el comentario tres líneas más arriba describe ese mismo fallo —«devolvía una
TUPLA (True, False), que nunca es False»— arreglado en el código y no en la
prueba de al lado. Y f4 lo acotó bien: repasó las 30 lambdas con paréntesis del
archivo y demostró que las otras seis eran booleanos legítimos unidos con `and`,
así que el hallazgo quedó cerrado y no como sospecha.

- **Antes de cambiar una cadena, mira quién la guarda** y comprueba que ese
  guardián puede fallar. Cambiar el texto y dejar la prueba ciega es peor que no
  tocar nada.
- En un lanzador propio, **haz que un resultado que no sea booleano sea un
  fallo**, no un `ok`.
- El 16 de septiembre este patrón apareció **cinco veces en una tarde**, en tres
  sesiones distintas. No es una anécdota: es lo primero que hay que mirar en una
  suite heredada.

**Y el mismo patrón sin texto: una prueba puede medir un lienzo vacío.**
`tools/probar_boca_integrada.mjs` garantiza el encuadre de la cara 3D con
`assert.equal(px.borde, 0)`, leyendo el canvas con `getImageData`. Ejecutando ese
código en el navegador, el canvas **se lee vacío** —un color, cero píxeles
opacos— porque WebGL no conserva el búfer de dibujo. Si en el entorno de pruebas
pasa igual, ese `assert` pasa **sin medir nada**, y es justo la prueba que debía
haber cazado el encuadre cortado que un usuario vio en su móvil. Queda pendiente
de confirmar en Playwright, pero la regla ya vale:

- Cuando una prueba afirma algo sobre **píxeles**, comprueba primero que lee
  píxeles: que haya opacos, que no sean todos del mismo color, que el conteo
  cambie si mueves a propósito lo que mides.
- Una aserción que **no puede fallar** es peor que no tener prueba, porque
  además da tranquilidad.

## Una acción por pasada, si quieres poder atribuir el efecto (16 sep)

Al comprobar que pulsar un botón **ya no** abre un panel, f4 midió en dos pasadas
separadas: una para pulsar el botón y mirar `panelAbierto`, otra para pulsar el
«Entrar» del aviso y ver que entonces sí abre. Si se pulsan los dos en el mismo
guion, un panel abierto al final no se puede atribuir a un clic ni al otro, y la
comprobación no prueba nada.

- **Un clic por pasada**, con el estado leído justo después.
- Para forzar un estado de espera (el texto que cambia a los 5 s), una promesa
  que no se resuelve sirve — y hay que **soltarla al acabar**, o el botón se queda
  bloqueado y la medida siguiente sale mal.

## Cada publicación se comprueba contra la anterior (16 sep)

Tres publicaciones del front en una tarde. 4e verificó cada una sobre **lo
servido**, no sobre el repositorio: recorrió el grafo desde `index.html`, y
además de mirar lo nuevo comprobó que **las frases de la tanda anterior seguían
ahí y las viejas seguían a cero**. Un despliegue puede deshacer el anterior sin
que nadie lo note, y el repositorio del Space acumula chunks huérfanos que no
carga nadie: de 402 `.js`, solo 14 eran alcanzables, y 76 de los huérfanos
contenían todavía el texto retirado. Quien audite a `grep` los encontrará y
parecerá que no se corrigió; la respuesta es la lista de alcanzables.

## Una afirmación del documento tiene que poder verse en pantalla (16 sep)

El documento decía que sin clave de OpenAI la aplicación sigue funcionando en
todo lo que no sale a la red. En *Pronunciar* eso era verdad a medias: el botón
de corrección estaba apagado y no explicaba por qué, así que el usuario no tenía
forma de saber qué seguía funcionando. Con el texto nuevo —«La corrección no está
disponible en este servidor. Grabarte y escucharte, sí.»— la pantalla y el
documento dicen lo mismo.

- Al revisar un entregable, coge sus afirmaciones de cara al usuario y pregunta
  **dónde se ve eso en la aplicación**. Si no se ve en ningún sitio, o falta una
  frase en pantalla o sobra una en el documento.
- Y al arreglar, comprueba que el arreglo no reintroduce el fallo que presume de
  resolver: aquí, el aviso nuevo quedaba tapado por el panel que se abría solo.

## Antes de buscar el fallo, comprueba si había sesión (16 sep)

Ismael tocó el micrófono en su Android y «no pasó nada». Se investigó como fallo
del micrófono, se midió un aviso que no se veía (abajo), se escribió en el
documento que la causa era el navegador interno de WhatsApp… y el 16 de
septiembre Miguel contó que **Ismael no había iniciado sesión**, así que esas
funciones no estaban disponibles para él. La causa se escribió antes de medirla,
el mismo error que con el caso de Esmeralda.

- **Lo primero que se pregunta ante «pulsé y no pasó nada»:** si había cuenta,
  en qué pantalla estaba y qué decía la app en ese momento. Sin eso, cualquier
  hipótesis técnica es una historia.
- **Una función que pide cuenta y no lo dice se ve igual que un fallo.** Prueba
  cada pantalla **sin sesión** y mira si la app explica qué hay que hacer, donde
  la persona está mirando. Comprueba también qué devuelve la API sin
  credenciales: un error técnico que el front no puede traducir es el mismo
  fallo, un piso más abajo.
- Lo que se midió sigue siendo cierto y útil, pero como hallazgo propio, no como
  causa del caso.

**Y comprueba de quién es la nota de voz.** Horas después, Miguel mandó ese mismo
audio diciendo «según yo este es de Laura». Era la misma grabación archivada como
de Ismael, y empieza «entré y **ya me inicié sesión**»: justo lo contrario de la
explicación que se acababa de escribir. Dos reglas de ahí:

- **Una nota de voz reenviada no trae remitente.** Antes de citarla en un
  entregable, pregunta de quién es; si no está confirmado, escribe «uno de los
  lectores» y sigue adelante, que no cuesta nada.
- **Una sola nota puede llevar dos quejas.** Al des-atribuirla hay que
  des-atribuirlas todas, no solo la que se estaba investigando: aquí, el
  micrófono **y** la saturación de la página, que era una de las razones escritas
  para una tanda de cambios.

## Un aviso que existe en el DOM puede no verse (Pronunciar, 15 sep)

Al investigar aquello se midió esto, que es un fallo real por sí mismo. El
código sí escribía un aviso («Este navegador no deja grabar audio»), pero a 390 px se pintaba en
y = 750-849, **debajo de la barra fija del micrófono**, que empieza en y = 687.
Lo mismo pasaba con «No tengo permiso…» y hasta con «Grabando…». Ninguna
prueba lo vio porque todas miraban que el texto estuviera en la página, no que
se viera.

- Para cada estado de una pantalla con barra fija (esperando permiso, grabando,
  cada error), comprueba con `getBoundingClientRect()` que el texto queda por
  encima de la barra, no solo que exista.
- **Los enlaces que se mandan por WhatsApp** se abren en Android dentro de su
  navegador interno (WebView, «; wv)» en el user agent), donde
  `navigator.mediaDevices` no existe o `getUserMedia` falla sin preguntar. Hay
  que probar ese caso borrando `navigator.mediaDevices` en la página, y la app
  tiene que decir **antes de pulsar** cómo abrirla en Chrome.
- A quien reciba el enlace, dile que lo abra en Chrome (Android) o Safari
  (iPhone), no dentro de WhatsApp.
