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
