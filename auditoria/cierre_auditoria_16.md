# Cierre de la auditoría 16 (Fable) — hallazgo por hallazgo

Cerrado el **11 de septiembre de 2026**, de noche, sobre `b6a7c21`. El informe
es [`informe_fable_16.md`](informe_fable_16.md): 0 críticos, 6 serios, 4
menores, 3 notas y **5 mutantes vivos de 21**. El encargo, en
[`encargo_10.md`](encargo_10.md).

**Es la auditoría del día antes de grabar**, y por eso el encargo pedía dos
cosas que las anteriores no pedían: que **ejecutara el recorrido del guion** en
lugar de leerlo, y que **cronometrara cada paso**. Las dos dieron fruto: tres de
los seis serios solo se ven usando la aplicación, y uno de ellos no es un fallo
del código sino del reloj.

**Verificados los seis serios uno por uno antes de tocar nada.** Ninguno se cayó
al comprobarlo. El primero lo reproduje yo en el Space en vivo.

---

## Serios

### S1 · Un recuadro rojo de «Error» al abrir un libro desde el buscador — CERRADO

El peor, porque cae justo en el paso estrella de la demo.

```
Error ×
Value: 1 is not in the list of choices: []
```

**Reproducido por mí en el Space**, con un `MutationObserver` puesto antes de
pulsar: buscar «dostoyevski» → elegir *Crime and Punishment* → «Leerlo ahora».
El libro se abre perfectamente; lo que sale es un recuadro rojo de Gradio
encima.

**Me costó tres diagnósticos, y los dos primeros eran falsos.** Lo supe las dos
veces porque **volví a reproducirlo en el Space con el arreglo puesto** y el
recuadro seguía ahí. Vale la pena dejarlo escrito, porque es la lección de la
casa aplicada a mí: un arreglo que no se vuelve a comprobar contra el fallo
original es una hipótesis, no una corrección. Si me hubiera fiado del primero,
habría dado por cerrado un fallo que iba a salir en cámara.

Lo que lo resolvió no fue leer más código, fue **una prueba A/B**: repetir el
recorrido en una sesión con `localStorage` limpio. Sin marcapáginas previo el
recuadro **no sale**; con un libro ya abierto, **sale siempre**.

La causa, entonces: `_abrir_del_catalogo` es una **generadora**, y su primer
`yield` **vaciaba el desplegable de capítulos** —`gr.update(choices=[],
value=None)`— para enseñar «Descargando de Project Gutenberg…». Si ya hay un
libro abierto —y lo hay siempre que se haya leído algo antes, porque
`_reanudar` lo repinta al cargar la página—, quitarle las opciones a un
componente que conserva su valor hace que Gradio pinte
«Value: 1 is not in the list of choices: []» encima del libro.

Y vaciarlo estaba mal por sí solo, aparte del recuadro: pulsar «Leerlo ahora»
sin haber elegido nada te borraba el índice del libro que estabas leyendo.

Arreglado en tres sitios, que es lo que lo hace robusto en vez de afortunado:

1. **El descargador no toca el desplegable mientras trabaja.** Solo lo cambia
   al final, cuando ya tiene el libro, o al fallar, cuando el lector se vacía
   entero de todas formas.
2. Los dos mandos del capítulo —el desplegable y el índice— usan ahora
   `_indice_de`, que manda **opciones y valor juntos**. Ninguno de los dos
   puede mandar un valor sin sus opciones.
3. `_indice_de` **valida el valor contra ESTE libro**: si el índice no existe en
   él —o llega como `None`, `"3"`, `-1`, `99`, `NaN` o una lista, que Gradio
   sabe mandar—, no se selecciona nada. Mejor sin selección que con una
   selección que no existe. Y las etiquetas se construyen en **un solo sitio**,
   porque los dos mandos son dos vistas del mismo estado.

La prueba vigila las tres: que el descargador no vacíe el desplegable, que
ningún manejador de `cap` ni de `indice` mande un valor suelto, y que los dos
sigan cableados —si no, se cumpliría sola—. Cuatro mutantes, uno por cada
manera de deshacerlo.

**Comprobado en el Space con el caso exacto que fallaba**: con *The Brothers
Karamazov* abierto, buscar «dostoyevski» y abrir *Crime and Punishment*. Sin
recuadro, el libro abre y la cabecera dice «42 capítulos · 203.699 palabras».

### S2 · «40 milisegundos» son en caliente: la primera consulta tarda ~55 s — CERRADO como nota de producción

El auditor lo cronometró: la primera consulta léxica de la sesión tardó **55 s**
(11:40:01 → 11:40:57) y la segunda **11 s**. No es un fallo: es la carga del
SQLite de 243 MB, spaCy y MiniLM, y `AGENTS.md` ya dice que los 40 ms son en
caliente. Lo que faltaba es que **el guion no lo decía**, y quien grabe se
encuentra con cincuenta y cinco segundos de silencio mientras afirma «cuarenta
milisegundos».

No se toca el código: cargar los modelos al arrancar está prohibido a propósito
—la app tiene que abrir rápido—. Lo que se hace es decirlo donde sirve: el guion
lleva ahora una nota de producción de **encender la aplicación y usarla antes de
grabar**.

### S3 · La ficha daba dos tiempos de lectura para el mismo libro y lector — CERRADO

Medido por el auditor sobre *Crime and Punishment* con perfil 1,20:

| | Tiempo que anunciaba |
|---|---|
| Primera apertura, sin la curva calculada | **18 h 52 min a tu ritmo de lectura** |
| Reapertura, con la curva ya medida (1,70) | **30 h 52 min (va por encima de tu nivel)** |

Doce horas de diferencia por el mismo libro y el mismo lector. `_ficha_libro`
decidía `exigente = nivel_libro > p.nivel + 0.15`, y cuando no hay análisis
guardado `nivel_libro` es `None`, así que `exigente` salía `False` **por
ausencia de dato** y se rotulaba «a tu ritmo de lectura»: una afirmación que la
aplicación no podía sostener todavía.

Ahora, con perfil pero sin medir el libro, da **el rango** —«entre 18 h 52 y
30 h 52, según lo que te cueste»—, igual que hace sin perfil. Medido el libro,
se moja: por encima avisa, por debajo da el ritmo cómodo.

### S4 · La pronunciación cobraba el cupo aunque no hubiera clave — CERRADO

El mismo fallo que ya se corrigió en `_consultar` —«con la clave caducada CADA
consulta descontaba un uso»— y que en `_practicar` se quedó sin corregir.
`_consultar` y `_de_que_trata` llaman a `_puede_pagar` **solo si hay clave**;
`_practicar` la llamaba siempre, y encima es la única de las tres que a
propósito no devuelve el uso.

Consecuencia real: un Space con perfiles y sin `OPENAI_API_KEY` —clave caducada
o borrada, que ya ha pasado aquí— descontaba un uso por cada intento de
pronunciación sin que saliera una sola petición. Ahora tiene la misma guardia
que sus dos hermanos y dice por qué.

### S5 · La pestaña pública «Estado» podía filtrar los nombres de usuario — CERRADO

La prueba del diagnóstico comprobaba que no se filtrara la **contraseña** y no
que faltara el **nombre de usuario**, así que invertir el `con_nombre=False` de
`problemas()` sacaba los usuarios configurados a una pestaña pública sin que
fallara nada. Es medio trabajo regalado a quien prueba contraseñas.

La prueba nueva exige las dos direcciones: que el nombre **no** salga en lo
público, y que **sí** salga en el registro del Space —si no, quien edita el
secreto a ciegas no sabría cuál arreglar—.

### S6 · El buscador no lo cubría ninguna prueba — CERRADO

El rescate por parecido ortográfico —lo que hace que «dostoyevski» mal escrito
encuentre a Dostoyevsky, que es **el paso 2 de la demo**— no lo probaba nadie.
Subir `_PARECIDO_NOMBRE` de 0,75 a 0,99 lo apaga y las 296 pruebas seguían en
verde. Igual el umbral de parecido: bajarlo a 0 hace que no se descarte nunca un
resultado flojo y el aviso de «ningún libro supera el umbral» no salga jamás.

La prueba nueva pone el parecido por **tema** a cero, de modo que lo único que
puede encontrar al autor sea el rescate del nombre. Sin eso se cumpliría sola.

---

## Menores

- **M1 · Los capítulos de §8.2 estaban en el `.md` y no en el `.tex`.** La app
  enseña «el 19, 1,52» y «el 36, 1,87», el `.md` también, y el PDF se quedó en
  «su capítulo más llevadero y su capítulo más exigente», sin números. Es el
  patrón de siempre: el `.md` corregido y el `.tex` sin corregir. Propagado y
  recompilado.
- **M2 · «clerk» sale con una acepción equivocada.** Cierto, y **peor de lo que
  decía el informe**. Medidas las tres apariciones de *clerk* en los primeros
  capítulos, por el camino de la app y con las frases reales del libro:

  | Frase | Afinidad | Acepción |
  |---|---|---|
  | «tailors, locksmiths, cooks… clerks» | 0,225 | oficinista — **correcta** |
  | «a German clerk in the civil service» | 0,213 | laico anglicano — **mal** |
  | «a retired government clerk» | 0,359 | clérigo — **mal** |

  Dos de tres, y las tres por debajo del umbral de duda (0,40), así que la app
  las marca «dudosa». La palabra del guion no puede ser una que falle dos de
  cada tres veces delante de una cámara.

  Un barrido por las 150 primeras palabras largas de esos capítulos deja nueve
  por encima del umbral. **La del guion pasa a ser `poverty`**: afinidad
  **0,505** —sin aviso de duda—, acepción correcta, */ˈpɒvəti/* frente a
  */ˈpɑːvɚti/* se oye, y es el tema del libro. Se pierde el audio grabado de
  Wiktionary, que `clerk` sí traía; se cambia igual, porque que la definición
  sea correcta importa más que de dónde salga la voz.

  Y hay una lección detrás que el guion ahora dice: **las palabras con el
  contraste británico/americano más bonito son las polisémicas, que es justo
  donde el desambiguador flojea.** Si el aviso de «acepción dudosa» sale en
  cámara, hay que decirlo en voz alta: que el modelo avise de que no está
  seguro es de lo mejor que tiene esta aplicación.
- **M3 y M4 · El separador de miles y el tope de la muestra.** Dos constantes
  que la aplicación enseña por todas partes («1.197», «203.699») y que ninguna
  prueba fijaba: volver a `format(int(n), ",")` daba «1,197» sin romper nada.
  Tres asertos en `pruebas_ficha.py`.

---

## Notas

- **N1 · Los «134 segundos» de la curva no se ven en vivo**, porque el Space la
  sirve desde la caché de `/data` y responde en 6 s. Es bueno para la demo y hay
  que saberlo: si el disco se limpiara, la primera medición serían dos minutos
  de silencio. En la nota de producción del guion.
- **N2 · Con el perfil puesto, *Crime and Punishment* sale el cuarto.**
  «dostoyevski» devuelve *The Idiot*, *Karamázov* y *Notes from the Underground*
  antes, porque la casilla «acercar a mi nivel» sube los B2 y el perfil del
  guion es 1,20. Lo medí yo también, y coincide. No es un fallo —el libro sale y
  se abre— pero hay que elegirlo sin dudar delante de la cámara. En el guion.
- **N3 · `PENDIENTES.md` iba otra vez por detrás**: decía que lo de la auditoría
  15 estaba sin subir cuando ya estaba subido y cotejado. Corregido, y con la
  frase que avisa de que esa línea es justo la que envejece.

Y un hallazgo del auditor **sobre su propio método**, que vale la pena guardar:
`pruebas_voz.py` usaba una ruta fija en el temporal del sistema, así que dos
ejecuciones simultáneas —que es exactamente lo que hace un banco de mutantes—
se pisaban el SQLite y daban un `PermissionError` que no tenía nada que ver con
lo que se medía. Un mutante podía parecer cazado por esa suite cuando lo único
que pasaba era eso. Las tres rutas cuelgan ahora de una carpeta propia por
ejecución.

---

## La comprobación

`pruebas_extremas.py` pasa de **296 a 301**, y `pruebas_ficha.py` suma tres
asertos. Los nueve mutantes de esta auditoría están en
[`tools/banco_mutantes.py`](../tools/banco_mutantes.py) con el prefijo `F16-`,
para que ninguno de estos seis arreglos se pueda deshacer en silencio.
